"""Configuração comum dos testes: banco de teste separado, fakes e cliente da API.

Os imports de app ficam dentro das fixtures. Assim, os testes que não usam a API
(chunking, notas, embeddings, geração) continuam rodando sem .env.
"""

import os

import pytest

# Precisa vir antes de qualquer import de app: o settings é criado na importação,
# e a variável de ambiente vale mais que o .env. Os testes nunca usam o banco aed.
os.environ["POSTGRES_DB"] = "aed_teste"

DIMENSAO = 384
# Cada palavra-chave liga um eixo do vetor falso. Textos com a mesma palavra ficam
# perto, e a ordem da busca fica previsível nos testes.
PALAVRAS_CHAVE = ["pilha", "fila", "vetor", "ponteiro"]


class ModeloFalso:
    """Imita o SentenceTransformer sem baixar nada."""

    def get_embedding_dimension(self) -> int:
        return DIMENSAO

    def encode(self, textos: list[str]) -> list[list[float]]:
        vetores = []
        for texto in textos:
            vetor = [0.0] * DIMENSAO
            vetor[-1] = 0.01  # nunca um vetor só de zeros (o cosseno não é definido)
            for eixo, palavra in enumerate(PALAVRAS_CHAVE):
                vetor[eixo] = float(texto.lower().count(palavra))
            vetores.append(vetor)
        return vetores


class LLMFalso:
    """Guarda a pergunta e o contexto recebidos e devolve uma resposta fixa."""

    def __init__(self):
        self.chamadas: list[tuple[str, list[dict]]] = []

    def gerar_resposta(self, pergunta: str, contexto: list[dict]) -> str:
        self.chamadas.append((pergunta, contexto))
        return "Resposta falsa [1]."


@pytest.fixture
def fakes(monkeypatch):
    """Troca o modelo de embedding e o LLM por versões falsas."""
    from app import busca, main

    modelo = ModeloFalso()
    llm = LLMFalso()
    monkeypatch.setattr(busca, "modelo_configurado", lambda: modelo)
    monkeypatch.setattr(main, "provedor_configurado", lambda: llm)
    return {"modelo": modelo, "llm": llm}


@pytest.fixture
def banco_limpo():
    """Garante que o banco é o de teste, que ele responde e que as tabelas estão vazias."""
    from app import db
    from app.config import settings

    if not settings.postgres_db.endswith("_teste"):
        raise RuntimeError(
            f"Os testes de integração apagam as tabelas e só rodam num banco *_teste, "
            f"mas o banco configurado é {settings.postgres_db!r}."
        )
    if not db.banco_responde():
        mensagem = (
            f"O banco {settings.postgres_db} não responde em "
            f"{settings.postgres_host}:{settings.postgres_port}. Suba o Postgres "
            "(docker compose up -d) e crie o banco de teste (veja o CLAUDE.md)."
        )
        if os.environ.get("CI") == "true":
            pytest.fail(mensagem)  # no CI, banco fora do ar é erro, não pode passar despercebido
        pytest.skip(mensagem)

    with db.conectar() as conexao:
        conexao.run("TRUNCATE chunks, documentos RESTART IDENTITY")
    yield
    with db.conectar() as conexao:
        conexao.run("TRUNCATE chunks, documentos RESTART IDENTITY")


@pytest.fixture
def cliente(fakes):
    """Cliente da API com os fakes no lugar do modelo e do LLM."""
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as cliente:
        yield cliente

"""Testes da API que não precisam do banco no ar: serviços fora do ar e validação.

O banco é "desligado" apontando a porta para um lugar onde não há Postgres.
"""

import pytest

from app.embeddings import ErroModeloEmbedding

NOTA = "---\ntitulo: Teste\nlinguagem: C\n---\n# Teste\n\n## Seção\nTexto da seção.\n"


@pytest.fixture
def banco_desligado(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "postgres_host", "127.0.0.1")
    monkeypatch.setattr(settings, "postgres_port", 1)  # nenhuma conexão aceita aqui


@pytest.mark.parametrize(
    "metodo, rota, argumentos",
    [
        ("get", "/documentos", {}),
        ("post", "/documentos", {"files": {"arquivo": ("teste.md", NOTA.encode(), "text/markdown")}}),
        ("post", "/embeddings", {}),
        ("get", "/busca", {"params": {"pergunta": "pilha"}}),
        ("post", "/perguntas", {"json": {"pergunta": "pilha"}}),
    ],
    ids=["listar", "enviar", "embeddings", "busca", "perguntas"],
)
def test_banco_fora_do_ar_da_503_com_mensagem(cliente, banco_desligado, metodo, rota, argumentos):
    resposta = getattr(cliente, metodo)(rota, **argumentos)

    assert resposta.status_code == 503
    assert "Não foi possível conectar ao banco em 127.0.0.1:1" in resposta.json()["detail"]


def test_saude_com_o_banco_fora_do_ar(cliente, banco_desligado):
    resposta = cliente.get("/saude")

    assert resposta.status_code == 503
    assert resposta.json() == {"api": "ok", "banco": "fora do ar"}


def test_modelo_de_embedding_indisponivel_da_503(cliente, monkeypatch):
    from app import busca

    def modelo_que_falha():
        raise ErroModeloEmbedding("Não foi possível carregar o modelo de embedding X.")

    monkeypatch.setattr(busca, "modelo_configurado", modelo_que_falha)

    resposta = cliente.get("/busca", params={"pergunta": "pilha"})

    assert resposta.status_code == 503
    assert "modelo de embedding" in resposta.json()["detail"]


def test_pergunta_longa_demais_da_422(cliente):
    longa = "a" * 501

    assert cliente.post("/perguntas", json={"pergunta": longa}).status_code == 422
    assert cliente.get("/busca", params={"pergunta": longa}).status_code == 422


def test_pergunta_no_limite_passa_da_validacao(cliente, banco_desligado):
    # 500 caracteres passam na validação e chegam ao banco (que aqui está fora do ar).
    resposta = cliente.post("/perguntas", json={"pergunta": "a" * 500})

    assert resposta.status_code == 503

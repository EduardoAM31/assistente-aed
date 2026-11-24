"""Testes de integração das rotas, com o Postgres de verdade (banco aed_teste).

O modelo de embedding e o LLM são falsos (veja o conftest.py): nada é baixado e
o Ollama não é chamado.
"""

import pytest

pytestmark = [pytest.mark.integracao, pytest.mark.usefixtures("banco_limpo")]

NOTA_PILHA = """---
titulo: Pilha de teste
linguagem: C
topicos:
  - pilha
---

# Pilha de teste

## O que é uma pilha
A pilha guarda elementos, e a pilha devolve primeiro o último que entrou.

## Como usar a pilha
Para usar a pilha, empilhe e desempilhe pelo topo da pilha.
"""

NOTA_FILA = """---
titulo: Fila de teste
linguagem: C
topicos:
  - fila
---

# Fila de teste

## O que é uma fila
A fila devolve primeiro o elemento que entrou primeiro na fila.
"""


def enviar(cliente, nome: str, conteudo: str | bytes):
    dados = conteudo.encode("utf-8") if isinstance(conteudo, str) else conteudo
    return cliente.post("/documentos", files={"arquivo": (nome, dados, "text/markdown")})


def consultar(sql: str) -> list:
    from app import db

    with db.conectar() as conexao:
        return conexao.run(sql)


def preparar_busca(cliente) -> None:
    """Duas notas no banco (3 chunks), todas com embedding."""
    assert enviar(cliente, "pilha.md", NOTA_PILHA).status_code == 201
    assert enviar(cliente, "fila.md", NOTA_FILA).status_code == 201
    assert cliente.post("/embeddings").json()["gerados"] == 3


def test_saude_com_o_banco_no_ar(cliente):
    resposta = cliente.get("/saude")

    assert resposta.status_code == 200
    assert resposta.json() == {"api": "ok", "banco": "ok"}


def test_nota_nova_201_e_reenvio_200_sem_duplicar(cliente):
    primeira = enviar(cliente, "pilha.md", NOTA_PILHA)
    segunda = enviar(cliente, "pilha.md", NOTA_PILHA)

    assert primeira.status_code == 201
    assert segunda.status_code == 200
    assert primeira.json()["id"] == segunda.json()["id"]
    assert segunda.json()["quantidade_chunks"] == 2
    assert consultar("SELECT count(*) FROM documentos") == [[1]]
    assert consultar("SELECT count(*) FROM chunks") == [[2]]


def test_listar_documentos(cliente):
    enviar(cliente, "pilha.md", NOTA_PILHA)
    enviar(cliente, "fila.md", NOTA_FILA)

    documentos = cliente.get("/documentos").json()

    assert [(d["nome_arquivo"], d["quantidade_chunks"]) for d in documentos] == [
        ("fila.md", 1),
        ("pilha.md", 2),
    ]


@pytest.mark.parametrize(
    "nome, conteudo, trecho_da_mensagem",
    [
        ("pilha.txt", NOTA_PILHA, "extensão .md"),
        ("pilha.md", "---\ntitulo: Olá\nlinguagem: C\n---\n# Olá\n".encode("latin-1"), "UTF-8"),
        ("pilha.md", "# Nota sem cabeçalho\n\n## Seção\nTexto.\n", "cabeçalho YAML"),
    ],
    ids=["extensao", "utf8", "sem-frontmatter"],
)
def test_nota_invalida_da_422_com_mensagem(cliente, nome, conteudo, trecho_da_mensagem):
    resposta = enviar(cliente, nome, conteudo)

    assert resposta.status_code == 422
    assert trecho_da_mensagem in resposta.json()["detail"]
    assert consultar("SELECT count(*) FROM documentos") == [[0]]


def test_reenvio_apaga_os_vetores_da_nota(cliente):
    enviar(cliente, "pilha.md", NOTA_PILHA)
    cliente.post("/embeddings")
    assert consultar("SELECT count(*) FROM chunks WHERE embedding IS NULL") == [[0]]

    enviar(cliente, "pilha.md", NOTA_PILHA)

    assert consultar("SELECT count(*) FROM chunks WHERE embedding IS NULL") == [[2]]


def test_embeddings_gera_uma_vez_e_refazer_recalcula_todos(cliente):
    enviar(cliente, "pilha.md", NOTA_PILHA)
    enviar(cliente, "fila.md", NOTA_FILA)

    assert cliente.post("/embeddings").json()["gerados"] == 3
    assert cliente.post("/embeddings").json()["gerados"] == 0
    assert cliente.post("/embeddings", params={"refazer": "true"}).json()["gerados"] == 3
    assert consultar("SELECT count(*) FROM chunks WHERE embedding IS NULL") == [[0]]


def test_busca_ordena_pela_distancia(cliente):
    preparar_busca(cliente)

    resultados = cliente.get("/busca", params={"pergunta": "o que é uma pilha?"}).json()

    assert len(resultados) == 3  # BUSCA_K do .env
    assert [r["nome_arquivo"] for r in resultados] == ["pilha.md", "pilha.md", "fila.md"]
    distancias = [r["distancia"] for r in resultados]
    assert distancias == sorted(distancias)
    assert set(resultados[0]) == {"nome_arquivo", "titulo", "secao", "distancia", "texto"}


def test_busca_respeita_o_k(cliente):
    preparar_busca(cliente)

    resultados = cliente.get("/busca", params={"pergunta": "fila", "k": 1}).json()

    assert [r["nome_arquivo"] for r in resultados] == ["fila.md"]


@pytest.mark.parametrize("parametros", [{"pergunta": "pilha", "k": 0}, {"pergunta": ""}])
def test_busca_com_parametros_invalidos_da_422(cliente, parametros):
    assert cliente.get("/busca", params=parametros).status_code == 422


def test_perguntas_sem_embeddings_da_409(cliente):
    enviar(cliente, "pilha.md", NOTA_PILHA)

    resposta = cliente.post("/perguntas", json={"pergunta": "o que é uma pilha?"})

    assert resposta.status_code == 409
    assert "POST /embeddings" in resposta.json()["detail"]


def test_perguntas_devolve_a_resposta_e_as_fontes_da_busca(cliente, fakes):
    preparar_busca(cliente)

    resposta = cliente.post("/perguntas", json={"pergunta": "  o que é uma pilha?  "})

    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["resposta"] == "Resposta falsa [1]."
    # As fontes não repetem (nota, seção) e seguem a ordem da busca.
    assert [(f["nome_arquivo"], f["secao"]) for f in dados["fontes"]] == [
        ("pilha.md", "O que é uma pilha"),
        ("pilha.md", "Como usar a pilha"),
        ("fila.md", "O que é uma fila"),
    ]
    # O LLM recebeu a pergunta sem os espaços das pontas e os 3 chunks da busca.
    [(pergunta, contexto)] = fakes["llm"].chamadas
    assert pergunta == "o que é uma pilha?"
    assert [c["secao"] for c in contexto] == [f["secao"] for f in dados["fontes"]]


def test_perguntas_da_503_quando_o_provedor_falha(cliente, monkeypatch):
    from app import main
    from app.geracao.base import ErroProvedorLLM

    class LLMForaDoAr:
        def gerar_resposta(self, pergunta, contexto):
            raise ErroProvedorLLM("Não foi possível conectar ao Ollama em http://teste.")

    preparar_busca(cliente)
    monkeypatch.setattr(main, "provedor_configurado", lambda: LLMForaDoAr())

    resposta = cliente.post("/perguntas", json={"pergunta": "pilha"})

    assert resposta.status_code == 503
    assert "conectar ao Ollama" in resposta.json()["detail"]


@pytest.mark.parametrize("pergunta", ["", "   "], ids=["vazia", "so-espacos"])
def test_perguntas_com_pergunta_vazia_da_422(cliente, pergunta):
    assert cliente.post("/perguntas", json={"pergunta": pergunta}).status_code == 422

"""Testes do prompt e da lista de fontes. Não usam o Ollama nem o banco."""

from app.geracao.base import INSTRUCOES, listar_fontes, montar_mensagens


def chunk(nome_arquivo: str, secao: str, texto: str) -> dict:
    return {
        "nome_arquivo": nome_arquivo,
        "titulo": f"Título de {nome_arquivo}",
        "secao": secao,
        "texto": texto,
        "distancia": 0.3,
    }


CONTEXTO = [
    chunk("vetores.md", "Seção A", "# Vetores\n## Seção A\n\nprimeiro trecho"),
    chunk("vetores.md", "Seção A", "# Vetores\n## Seção A\n\nsegundo trecho"),
    chunk("strings.md", "Seção B", "# Strings\n## Seção B\n\nterceiro trecho"),
]


def test_mensagens_tem_system_com_as_instrucoes_e_user_com_a_pergunta():
    mensagens = montar_mensagens("Por que o índice começa em 0?", CONTEXTO)

    assert [m["role"] for m in mensagens] == ["system", "user"]
    assert mensagens[0]["content"] == INSTRUCOES
    assert mensagens[1]["content"].endswith("Pergunta: Por que o índice começa em 0?")


def test_instrucoes_tem_as_regras_do_estilo_das_respostas():
    for regra in ("português", "no máximo 4 frases", "um exemplo curto", "[1]", "não sabe"):
        assert regra in INSTRUCOES


def test_trechos_vao_numerados_e_na_ordem_sem_perder_nenhum():
    usuario = montar_mensagens("pergunta", CONTEXTO)[1]["content"]

    posicoes = [usuario.index(f"[{n}] # ") for n in (1, 2, 3)]
    assert posicoes == sorted(posicoes)
    for c in CONTEXTO:
        assert c["texto"] in usuario
    assert "[4]" not in usuario


def test_fontes_sem_repeticao_e_na_ordem():
    assert listar_fontes(CONTEXTO) == [
        {"nome_arquivo": "vetores.md", "titulo": "Título de vetores.md", "secao": "Seção A"},
        {"nome_arquivo": "strings.md", "titulo": "Título de strings.md", "secao": "Seção B"},
    ]


def test_mesma_secao_em_notas_diferentes_conta_como_fontes_diferentes():
    contexto = [chunk("a.md", "Introdução", "x"), chunk("b.md", "Introdução", "y")]

    assert [f["nome_arquivo"] for f in listar_fontes(contexto)] == ["a.md", "b.md"]

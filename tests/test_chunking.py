"""Testes unitários do chunking. Não usam o banco nem o .env."""

from pathlib import Path

import pytest

from app.chunking import dividir_em_chunks
from app.notas import ler_nota

PASTA_CORPUS = Path(__file__).resolve().parent.parent / "corpus"
TITULO = "Vetores em C"


def palavras(n: int, inicio: int = 1) -> str:
    """Gera um texto com n palavras numeradas: 'p1 p2 p3 ...'."""
    return " ".join(f"p{i}" for i in range(inicio, inicio + n))


def corpo_com_secao(texto: str, titulo_secao: str = "Seção A") -> str:
    return f"# {TITULO}\n\nIntrodução antes das seções.\n\n## {titulo_secao}\n\n{texto}\n"


def sem_prefixo(chunk_texto: str) -> str:
    """Tira as duas linhas de título e a linha em branco do começo do chunk."""
    return chunk_texto.split("\n\n", 1)[1]


def test_secao_curta_vira_um_chunk():
    chunks = dividir_em_chunks(corpo_com_secao(palavras(10)), TITULO, 150, 25)

    assert len(chunks) == 1
    assert chunks[0].secao == "Seção A"
    assert sem_prefixo(chunks[0].texto) == palavras(10)


def test_secao_longa_quebra_com_overlap():
    chunks = dividir_em_chunks(corpo_com_secao(palavras(25)), TITULO, 10, 2)

    # Passo de 10 - 2 = 8 palavras: janelas p1-p10, p9-p18, p17-p25.
    assert [sem_prefixo(c.texto) for c in chunks] == [
        palavras(10, inicio=1),
        palavras(10, inicio=9),
        palavras(9, inicio=17),
    ]
    assert all(c.secao == "Seção A" for c in chunks)


def test_ultima_janela_com_poucas_palavras_novas_estende_a_anterior():
    # 12 palavras, max 10, overlap 2: a segunda janela seria p9-p12, com só 2
    # palavras novas (p11 e p12). Em vez disso, a primeira vai até p12.
    chunks = dividir_em_chunks(corpo_com_secao(palavras(12)), TITULO, 10, 2)

    assert [sem_prefixo(c.texto) for c in chunks] == [palavras(12)]


def test_ultima_janela_com_mais_palavras_novas_que_o_overlap_e_mantida():
    # 13 palavras, max 10, overlap 2: a segunda janela (p9-p13) traz 3 palavras novas.
    chunks = dividir_em_chunks(corpo_com_secao(palavras(13)), TITULO, 10, 2)

    assert [sem_prefixo(c.texto) for c in chunks] == [
        palavras(10, inicio=1),
        palavras(5, inicio=9),
    ]


def test_secao_do_tamanho_exato_do_limite_nao_quebra():
    chunks = dividir_em_chunks(corpo_com_secao(palavras(10)), TITULO, 10, 2)

    assert len(chunks) == 1


def test_limite_zero_nao_quebra_nada():
    chunks = dividir_em_chunks(corpo_com_secao(palavras(500)), TITULO, 0, 0)

    assert len(chunks) == 1
    assert sem_prefixo(chunks[0].texto) == palavras(500)


def test_prefixo_com_os_titulos_aparece_em_todo_chunk():
    corpo = (
        f"# {TITULO}\n\n## Seção A\n\n{palavras(30)}\n\n## Seção B\n\n{palavras(5)}\n"
    )
    chunks = dividir_em_chunks(corpo, TITULO, 10, 2)

    assert len(chunks) == 5  # 4 da seção A e 1 da seção B
    for chunk in chunks:
        assert chunk.texto.startswith(f"# {TITULO}\n## {chunk.secao}\n\n")


def test_texto_antes_da_primeira_secao_nao_vira_chunk():
    chunks = dividir_em_chunks(corpo_com_secao(palavras(5)), TITULO, 150, 25)

    assert len(chunks) == 1
    assert "Introdução antes das seções" not in chunks[0].texto


def test_secao_vazia_nao_gera_chunk():
    corpo = f"# {TITULO}\n\n## Seção vazia\n\n\n## Seção B\n\n{palavras(5)}\n"
    chunks = dividir_em_chunks(corpo, TITULO, 150, 25)

    assert [c.secao for c in chunks] == ["Seção B"]


def test_linha_com_hashes_dentro_de_codigo_nao_abre_secao():
    codigo = "```c\n## isto não é título\nint x = 0;\n```"
    chunks = dividir_em_chunks(corpo_com_secao(codigo), TITULO, 150, 25)

    assert len(chunks) == 1
    assert "## isto não é título" in chunks[0].texto


def test_quebra_mantem_as_quebras_de_linha_do_codigo():
    codigo = "```c\nint main(void) {\n    return 0;\n}\n```"
    texto = palavras(8) + "\n\n" + codigo
    chunks = dividir_em_chunks(corpo_com_secao(texto), TITULO, 10, 2)

    assert "{\n    return 0;\n}" in chunks[-1].texto


@pytest.mark.parametrize("max_palavras, overlap", [(-1, 0), (10, -1), (10, 10), (10, 15)])
def test_parametros_invalidos(max_palavras: int, overlap: int):
    with pytest.raises(ValueError):
        dividir_em_chunks(corpo_com_secao(palavras(5)), TITULO, max_palavras, overlap)


@pytest.mark.parametrize("max_palavras, overlap", [(80, 15), (150, 25), (0, 0)])
@pytest.mark.parametrize("caminho", sorted(PASTA_CORPUS.glob("*.md")), ids=lambda c: c.name)
def test_notas_do_corpus_passam_pelo_chunker(caminho: Path, max_palavras: int, overlap: int):
    metadados, corpo = ler_nota(caminho.read_text(encoding="utf-8"))
    chunks = dividir_em_chunks(corpo, metadados["titulo"], max_palavras, overlap)

    assert len(chunks) >= 3  # toda nota tem de 3 a 5 seções
    for chunk in chunks:
        assert chunk.texto.startswith(f"# {metadados['titulo']}\n## {chunk.secao}\n\n")

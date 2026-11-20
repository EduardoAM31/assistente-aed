"""Testes unitários do ler_nota. Não usam o banco."""

from pathlib import Path

import pytest

from app.notas import NotaInvalida, ler_nota

PASTA_CORPUS = Path(__file__).resolve().parent.parent / "corpus"

NOTA_VALIDA = """---
titulo: Vetores em C
linguagem: C
topicos:
  - vetores
---

# Vetores em C

## O que é um vetor em C
Texto da seção.
"""


def test_nota_valida_separa_metadados_e_corpo():
    metadados, corpo = ler_nota(NOTA_VALIDA)

    assert metadados["titulo"] == "Vetores em C"
    assert metadados["linguagem"] == "C"
    assert metadados["topicos"] == ["vetores"]
    assert corpo.startswith("# Vetores em C")
    assert "---" not in corpo


def test_nota_com_quebras_de_linha_do_windows():
    metadados, corpo = ler_nota(NOTA_VALIDA.replace("\n", "\r\n"))

    assert metadados["titulo"] == "Vetores em C"
    assert corpo.startswith("# Vetores em C")


def test_nota_sem_frontmatter():
    with pytest.raises(NotaInvalida, match="cabeçalho YAML"):
        ler_nota("# Vetores em C\n\nTexto sem cabeçalho.\n")


def test_nota_com_frontmatter_sem_fechamento():
    with pytest.raises(NotaInvalida, match="não foi fechado"):
        ler_nota("---\ntitulo: Vetores em C\nlinguagem: C\n# Vetores em C\n")


def test_nota_sem_titulo():
    with pytest.raises(NotaInvalida, match="titulo"):
        ler_nota("---\nlinguagem: C\n---\n# Vetores em C\n")


def test_nota_com_linguagem_invalida():
    with pytest.raises(NotaInvalida, match="'C' ou 'C\\+\\+'"):
        ler_nota("---\ntitulo: Listas em Python\nlinguagem: Python\n---\n# Listas\n")


@pytest.mark.parametrize("caminho", sorted(PASTA_CORPUS.glob("*.md")), ids=lambda c: c.name)
def test_notas_do_corpus_sao_validas(caminho: Path):
    metadados, corpo = ler_nota(caminho.read_text(encoding="utf-8"))

    assert metadados["titulo"]
    assert corpo.startswith("# ")

"""Testes das funções puras do avaliacao/avaliar.py: sem banco e sem modelo."""

import json
from datetime import datetime

import pytest

from avaliacao.avaliar import (
    ErroAvaliacao,
    acertou,
    calcular_recall,
    conferir_rotulos,
    contar_chunks_esperados,
    distancia_cosseno,
    ler_perguntas,
    nome_do_resultado,
    secoes_do_corpus,
)

NOTA = """---
titulo: Pilha
linguagem: C
topicos: [pilha]
---
# Pilha

## O que é uma pilha
Uma pilha guarda elementos e tira sempre o último que entrou.

## Pilha vazia
Tirar de uma pilha vazia é um erro que o programa precisa tratar.
"""


def jsonl(*linhas: dict) -> str:
    return "\n".join(json.dumps(linha, ensure_ascii=False) for linha in linhas)


def principal(id: int, secao: str = "O que é uma pilha") -> dict:
    return {"id": id, "pergunta": f"pergunta {id}", "nota": "pilha.md", "secao": secao}


def resultado(nota: str, secao: str, distancia: float = 0.1) -> dict:
    return {"nome_arquivo": nota, "secao": secao, "distancia": distancia}


# --- ler_perguntas -----------------------------------------------------------


def test_ler_perguntas_aceita_os_tres_tipos_e_ignora_linhas_vazias():
    texto = jsonl(
        principal(1),
        {"id": 2, "pergunta": "fora do corpus", "sem_resposta": True},
        {**principal(3), "variante_de": 1},
    )
    perguntas = ler_perguntas(texto + "\n\n")
    assert [p["id"] for p in perguntas] == [1, 2, 3]


def test_ler_perguntas_aponta_a_linha_com_json_invalido():
    texto = jsonl(principal(1)) + '\n{"id": 2, "pergunta": "sem fechar"'
    with pytest.raises(ErroAvaliacao, match="Linha 2"):
        ler_perguntas(texto)


def test_ler_perguntas_recusa_id_repetido():
    with pytest.raises(ErroAvaliacao, match="id 1 aparece mais de uma vez"):
        ler_perguntas(jsonl(principal(1), principal(1)))


def test_ler_perguntas_exige_rotulo_ou_sem_resposta():
    with pytest.raises(ErroAvaliacao, match="precisa de nota e secao"):
        ler_perguntas(jsonl({"id": 1, "pergunta": "sem rótulo", "nota": "pilha.md", "secao": ""}))


def test_ler_perguntas_exige_id_inteiro_e_pergunta():
    with pytest.raises(ErroAvaliacao, match="id inteiro"):
        ler_perguntas(jsonl({"id": "1", "pergunta": "x", "sem_resposta": True}))


@pytest.mark.parametrize(
    "variante_de",
    [99, 2, 3],  # não existe, é sem resposta, é outra variante
)
def test_ler_perguntas_recusa_variante_sem_principal_valida(variante_de):
    texto = jsonl(
        principal(1),
        {"id": 2, "pergunta": "fora", "sem_resposta": True},
        {**principal(3), "variante_de": 1},
        {**principal(4), "variante_de": variante_de},
    )
    with pytest.raises(ErroAvaliacao, match="id 4"):
        ler_perguntas(texto)


def test_ler_perguntas_recusa_variante_com_rotulo_diferente_da_principal():
    texto = jsonl(principal(1), {**principal(2, secao="Pilha vazia"), "variante_de": 1})
    with pytest.raises(ErroAvaliacao, match="mesma nota e seção"):
        ler_perguntas(texto)


# --- secoes_do_corpus e conferir_rotulos --------------------------------------


@pytest.fixture
def corpus(tmp_path):
    (tmp_path / "pilha.md").write_text(NOTA, encoding="utf-8")
    return tmp_path


def test_secoes_do_corpus_le_os_titulos_de_cada_nota(corpus):
    assert secoes_do_corpus(corpus) == {"pilha.md": ["O que é uma pilha", "Pilha vazia"]}


def test_conferir_rotulos_aceita_rotulos_certos_e_ignora_sem_resposta(corpus):
    perguntas = [principal(1), {"id": 2, "pergunta": "fora", "sem_resposta": True}]
    assert conferir_rotulos(perguntas, secoes_do_corpus(corpus)) == []


def test_conferir_rotulos_mostra_as_secoes_da_nota_quando_o_titulo_nao_existe(corpus):
    [problema] = conferir_rotulos([principal(1, secao="O que e uma pilha")], secoes_do_corpus(corpus))
    assert "id 1" in problema
    assert "- O que é uma pilha" in problema and "- Pilha vazia" in problema


def test_conferir_rotulos_avisa_nota_inexistente(corpus):
    pergunta = {**principal(1), "nota": "fila.md"}
    [problema] = conferir_rotulos([pergunta], secoes_do_corpus(corpus))
    assert "'fila.md' não existe" in problema and "pilha.md" in problema


# --- acertou e calcular_recall ------------------------------------------------


def test_acertou_em_qualquer_uma_das_posicoes():
    resultados = [
        resultado("fila.md", "O que é uma fila"),
        resultado("pilha.md", "Pilha vazia"),
        resultado("pilha.md", "O que é uma pilha"),
    ]
    assert acertou(principal(1), resultados)


def test_mesma_nota_com_outra_secao_nao_e_acerto():
    assert not acertou(principal(1), [resultado("pilha.md", "Pilha vazia")])


def test_calcular_recall_conta_acertos_e_lista_os_erros():
    perguntas = [principal(1), principal(2), principal(3), principal(4)]
    certo = [resultado("pilha.md", "O que é uma pilha")]
    errado = [resultado("fila.md", "O que é uma fila", 0.4321)]
    resultados_por_id = {1: certo, 2: certo, 3: certo, 4: errado}

    grupo = calcular_recall(perguntas, resultados_por_id)

    assert grupo["perguntas"] == 4
    assert grupo["acertos"] == 3
    assert grupo["recall"] == 0.75
    [erro] = grupo["erros"]
    assert erro["id"] == 4
    assert erro["esperado"] == {"nota": "pilha.md", "secao": "O que é uma pilha"}
    assert erro["vieram"] == [{"nota": "fila.md", "secao": "O que é uma fila", "distancia": 0.4321}]


def test_calcular_recall_sem_perguntas_fica_none():
    assert calcular_recall([], {})["recall"] is None


# --- funções auxiliares -------------------------------------------------------


def test_contar_chunks_esperados_segue_o_chunking(corpus):
    assert contar_chunks_esperados(corpus, 0, 0) == 2  # sem limite: um chunk por seção
    assert contar_chunks_esperados(corpus, 5, 1) > 2  # seções de mais de 5 palavras se dividem


def test_distancia_cosseno():
    assert distancia_cosseno([1.0, 2.0], [2.0, 4.0]) == pytest.approx(0.0)  # mesma direção
    assert distancia_cosseno([1.0, 0.0], [0.0, 1.0]) == pytest.approx(1.0)  # perpendiculares


def test_nome_do_resultado():
    data = datetime(2026, 11, 25, 14, 30)
    modelo = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    assert nome_do_resultado(data, modelo, 60, 10) == (
        "2026-11-25_1430_paraphrase-multilingual-MiniLM-L12-v2_60-10.json"
    )
    assert nome_do_resultado(data, "intfloat/multilingual-e5-small", 0, 0).endswith(
        "_multilingual-e5-small_sem-limite.json"
    )

"""Testes de app/embeddings.py com um modelo falso. Nenhum modelo é baixado."""

import subprocess
import sys
from pathlib import Path

import pytest

from app.embeddings import (
    DIMENSAO_ESPERADA,
    conferir_dimensao,
    gerar_vetores,
    vetor_para_texto,
)


class ModeloFalso:
    """Imita o SentenceTransformer: guarda os textos recebidos e devolve vetores fixos."""

    def __init__(self, dimensao: int = DIMENSAO_ESPERADA):
        self.dimensao = dimensao
        self.textos_recebidos: list[str] = []

    def get_embedding_dimension(self) -> int:
        return self.dimensao

    def encode(self, textos: list[str]) -> list[list[float]]:
        self.textos_recebidos.extend(textos)
        return [[float(i)] * self.dimensao for i in range(len(textos))]


def test_prefixo_e_colocado_na_frente_de_cada_texto():
    modelo = ModeloFalso()
    gerar_vetores(modelo, ["texto um", "texto dois"], "passage: ")

    assert modelo.textos_recebidos == ["passage: texto um", "passage: texto dois"]


def test_prefixo_vazio_nao_muda_o_texto():
    modelo = ModeloFalso()
    gerar_vetores(modelo, ["texto um"], "")

    assert modelo.textos_recebidos == ["texto um"]


def test_gera_um_vetor_de_floats_por_texto():
    vetores = gerar_vetores(ModeloFalso(), ["a", "b", "c"], "")

    assert len(vetores) == 3
    assert all(len(v) == DIMENSAO_ESPERADA for v in vetores)
    assert all(isinstance(x, float) for v in vetores for x in v)


def test_vetor_para_texto_no_formato_do_pgvector():
    assert vetor_para_texto([0.5, -1.0, 2.25]) == "[0.5,-1.0,2.25]"


def test_vetor_para_texto_preserva_os_valores():
    vetor = [0.1, -0.000012345, 3.0e-8]
    texto = vetor_para_texto(vetor)

    assert [float(x) for x in texto.strip("[]").split(",")] == vetor


def test_dimensao_certa_passa():
    conferir_dimensao(ModeloFalso(384), "modelo-de-teste")


def test_dimensao_errada_da_erro_claro():
    with pytest.raises(ValueError, match="768 dimensões.*vector\\(384\\)"):
        conferir_dimensao(ModeloFalso(768), "modelo-de-teste")


def test_importar_embeddings_nao_carrega_o_torch():
    # O torch só deve ser importado ao carregar o modelo de verdade. A checagem roda
    # num Python novo, porque outro teste pode ter importado o torch neste processo.
    raiz = Path(__file__).resolve().parent.parent
    resultado = subprocess.run(
        [sys.executable, "-c", "import sys, app.embeddings; print('torch' in sys.modules)"],
        cwd=raiz,
        capture_output=True,
        text=True,
    )

    assert resultado.returncode == 0, resultado.stderr
    assert resultado.stdout.strip() == "False"

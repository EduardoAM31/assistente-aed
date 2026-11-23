"""Testes da escolha do provedor, com uma configuração falsa (sem .env)."""

from types import SimpleNamespace

import pytest

from app.geracao import criar_provedor
from app.geracao.ollama import ProvedorOllama


def config_falsa(provedor: str) -> SimpleNamespace:
    return SimpleNamespace(
        llm_provedor=provedor,
        ollama_url="http://ollama-falso:11434",
        llm_model="modelo-falso",
        llm_num_predict=256,
        llm_temperature=0.1,
        ollama_num_ctx=4096,
        llm_timeout=5,
    )


def test_ollama_cria_o_provedor_ollama_com_a_configuracao():
    provedor = criar_provedor(config_falsa("ollama"))

    assert isinstance(provedor, ProvedorOllama)
    assert provedor.modelo == "modelo-falso"
    assert provedor.opcoes == {"num_predict": 256, "temperature": 0.1, "num_ctx": 4096}


@pytest.mark.parametrize("nome", ["huggingface", "Ollama", ""])
def test_provedor_invalido_da_erro_claro(nome: str):
    with pytest.raises(ValueError, match="LLM_PROVEDOR=.*não é válido"):
        criar_provedor(config_falsa(nome))

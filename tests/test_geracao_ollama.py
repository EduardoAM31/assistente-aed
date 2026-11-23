"""Testes do ProvedorOllama com um transporte falso do httpx. Não chamam o Ollama."""

import json
import logging

import httpx
import pytest

from app.geracao.base import ErroProvedorLLM, montar_mensagens
from app.geracao.ollama import ProvedorOllama

CONTEXTO = [
    {
        "nome_arquivo": "indice-zero.md",
        "titulo": "Índice zero",
        "secao": "Seção A",
        "texto": "# Índice zero\n## Seção A\n\ntexto do trecho",
    }
]


def criar_provedor(responder) -> ProvedorOllama:
    """responder recebe o httpx.Request e devolve um httpx.Response (ou levanta erro)."""
    return ProvedorOllama(
        url="http://ollama-falso:11434",
        modelo="modelo-falso",
        num_predict=256,
        temperature=0.1,
        num_ctx=4096,
        timeout=5,
        transporte=httpx.MockTransport(responder),
    )


def resposta_ok(conteudo: str = "  Resposta curta [1].  ", done_reason: str = "stop"):
    return httpx.Response(
        200,
        json={"message": {"role": "assistant", "content": conteudo}, "done_reason": done_reason},
    )


def test_envia_o_corpo_certo_para_o_api_chat():
    pedidos = []

    def responder(request: httpx.Request) -> httpx.Response:
        pedidos.append(request)
        return resposta_ok()

    criar_provedor(responder).gerar_resposta("Por que começa em 0?", CONTEXTO)

    [pedido] = pedidos
    corpo = json.loads(pedido.content)
    assert pedido.method == "POST"
    assert str(pedido.url) == "http://ollama-falso:11434/api/chat"
    assert corpo["model"] == "modelo-falso"
    assert corpo["stream"] is False
    assert corpo["options"] == {"num_predict": 256, "temperature": 0.1, "num_ctx": 4096}
    assert corpo["messages"] == montar_mensagens("Por que começa em 0?", CONTEXTO)


def test_devolve_o_texto_da_resposta_sem_espacos_nas_pontas():
    resposta = criar_provedor(lambda request: resposta_ok()).gerar_resposta("p", CONTEXTO)

    assert resposta == "Resposta curta [1]."


def test_ollama_fora_do_ar_da_erro_claro():
    def responder(request):
        raise httpx.ConnectError("conexão recusada", request=request)

    with pytest.raises(ErroProvedorLLM, match="conectar ao Ollama em http://ollama-falso:11434"):
        criar_provedor(responder).gerar_resposta("p", CONTEXTO)


def test_timeout_da_erro_claro():
    def responder(request):
        raise httpx.ReadTimeout("demorou", request=request)

    with pytest.raises(ErroProvedorLLM, match="não respondeu em 5 s"):
        criar_provedor(responder).gerar_resposta("p", CONTEXTO)


def test_erro_http_do_ollama_da_erro_claro():
    def responder(request):
        return httpx.Response(404, json={"error": "model 'modelo-falso' not found"})

    with pytest.raises(ErroProvedorLLM, match="erro 404.*not found"):
        criar_provedor(responder).gerar_resposta("p", CONTEXTO)


def test_resposta_cortada_gera_aviso_no_log(caplog):
    provedor = criar_provedor(lambda request: resposta_ok(done_reason="length"))

    with caplog.at_level(logging.WARNING):
        provedor.gerar_resposta("p", CONTEXTO)

    assert "cortada" in caplog.text

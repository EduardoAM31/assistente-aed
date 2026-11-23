"""Provedor de LLM que usa o Ollama rodando localmente (API /api/chat)."""

import logging

import httpx

from app.geracao.base import ErroProvedorLLM, montar_mensagens

logger = logging.getLogger(__name__)


class ProvedorOllama:
    def __init__(
        self,
        url: str,
        modelo: str,
        num_predict: int,
        temperature: float,
        num_ctx: int,
        timeout: float,
        transporte: httpx.BaseTransport | None = None,
    ):
        """transporte só é usado nos testes, para trocar a rede por respostas falsas."""
        self.url = url
        self.modelo = modelo
        self.timeout = timeout
        self.opcoes = {
            "num_predict": num_predict,  # limite de tokens da resposta
            "temperature": temperature,  # baixa: respostas mais previsíveis
            "num_ctx": num_ctx,  # contexto fixo, para o uso de VRAM ser previsível
        }
        self.cliente = httpx.Client(base_url=url, timeout=timeout, transport=transporte)

    def gerar_resposta(self, pergunta: str, contexto: list[dict]) -> str:
        corpo = {
            "model": self.modelo,
            "messages": montar_mensagens(pergunta, contexto),
            "stream": False,  # a resposta vem inteira, num JSON só
            "options": self.opcoes,
        }
        try:
            resposta = self.cliente.post("/api/chat", json=corpo)
            resposta.raise_for_status()
        except httpx.TimeoutException as erro:
            raise ErroProvedorLLM(
                f"O Ollama não respondeu em {self.timeout:g} s. Confira se ele está "
                f"rodando em {self.url} ou aumente o LLM_TIMEOUT no .env."
            ) from erro
        except httpx.TransportError as erro:
            raise ErroProvedorLLM(
                f"Não foi possível conectar ao Ollama em {self.url}. "
                "Confira se ele está rodando (OLLAMA_URL no .env)."
            ) from erro
        except httpx.HTTPStatusError as erro:
            raise ErroProvedorLLM(
                f"O Ollama respondeu com erro {erro.response.status_code}: "
                f"{erro.response.text}. Confira se o modelo {self.modelo} foi baixado "
                "(ollama pull)."
            ) from erro

        dados = resposta.json()
        if dados.get("done_reason") == "length":
            # A resposta bateu no num_predict e foi cortada no meio.
            logger.warning(
                "Resposta cortada pelo limite de %s tokens (LLM_NUM_PREDICT).",
                self.opcoes["num_predict"],
            )
        return dados["message"]["content"].strip()

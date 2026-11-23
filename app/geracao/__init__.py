"""Escolha do provedor de LLM a partir da configuração (LLM_PROVEDOR no .env)."""

from app.geracao.base import ProvedorLLM
from app.geracao.ollama import ProvedorOllama

PROVEDORES_VALIDOS = ("ollama",)


def criar_provedor(config) -> ProvedorLLM:
    """Cria o provedor indicado em config.llm_provedor.

    config é o settings do app/config.py. Ele vem por parâmetro, e não por import,
    para os testes passarem uma configuração falsa sem precisar do .env.
    """
    if config.llm_provedor == "ollama":
        return ProvedorOllama(
            url=config.ollama_url,
            modelo=config.llm_model,
            num_predict=config.llm_num_predict,
            temperature=config.llm_temperature,
            num_ctx=config.ollama_num_ctx,
            timeout=config.llm_timeout,
        )
    # O provedor Hugging Face fica para depois: a interface já está pronta para ele.
    raise ValueError(
        f"LLM_PROVEDOR={config.llm_provedor!r} não é válido. "
        f"Valores aceitos por enquanto: {', '.join(PROVEDORES_VALIDOS)}."
    )

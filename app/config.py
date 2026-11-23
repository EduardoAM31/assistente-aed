"""Configuração do projeto, lida das variáveis de ambiente e do arquivo .env."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# O .env fica na raiz do projeto, um nível acima da pasta app/.
ARQUIVO_ENV = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    # extra="ignore": o .env tem variáveis de outras etapas (como as do Ollama).
    model_config = SettingsConfigDict(env_file=ARQUIVO_ENV, extra="ignore")

    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: int

    # Chunking (etapa 4). CHUNK_MAX_PALAVRAS=0 significa "sem limite".
    chunk_max_palavras: int
    chunk_overlap_palavras: int

    # Embeddings e busca (etapa 5). Os prefixos podem ficar vazios (MiniLM).
    embedding_modelo: str
    embedding_prefixo_documento: str
    embedding_prefixo_pergunta: str
    embedding_dispositivo: str
    busca_k: int

    # Geração (etapa 6). Por enquanto, LLM_PROVEDOR só aceita "ollama".
    llm_provedor: str
    llm_model: str
    llm_num_predict: int
    llm_temperature: float
    llm_timeout: float  # segundos
    ollama_url: str
    ollama_num_ctx: int


settings = Settings()

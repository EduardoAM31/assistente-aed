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


settings = Settings()

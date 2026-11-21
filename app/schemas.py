"""Modelos Pydantic das respostas da API."""

from pydantic import BaseModel


class SaudeSaida(BaseModel):
    api: str
    banco: str


class DocumentoSaida(BaseModel):
    id: int
    nome_arquivo: str
    titulo: str
    linguagem: str
    quantidade_chunks: int

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


class EmbeddingsSaida(BaseModel):
    modelo: str
    gerados: int


class ResultadoBusca(BaseModel):
    nome_arquivo: str
    titulo: str
    secao: str
    distancia: float  # distância de cosseno: 0 é igual, quanto maior, mais longe
    texto: str

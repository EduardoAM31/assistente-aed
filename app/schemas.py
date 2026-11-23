"""Modelos Pydantic das entradas e das respostas da API."""

from typing import Annotated

from pydantic import BaseModel, StringConstraints


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


class PerguntaEntrada(BaseModel):
    # strip_whitespace tira os espaços das pontas: uma pergunta só com espaços dá 422.
    pergunta: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Fonte(BaseModel):
    nome_arquivo: str
    titulo: str
    secao: str


class RespostaSaida(BaseModel):
    resposta: str
    # Os trechos que o modelo recebeu, sem repetir (nota, seção). Vêm do código, e não
    # do texto do modelo, e não provam qual trecho ele usou.
    fontes: list[Fonte]

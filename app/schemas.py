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


# Uma pergunta de iniciante cabe com folga em 500 caracteres. O limite evita que um
# prompt maior que OLLAMA_NUM_CTX faça o Ollama cortar o começo, onde estão as instruções.
TAMANHO_MAXIMO_PERGUNTA = 500


class PerguntaEntrada(BaseModel):
    # strip_whitespace tira os espaços das pontas: uma pergunta só com espaços dá 422.
    pergunta: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True, min_length=1, max_length=TAMANHO_MAXIMO_PERGUNTA
        ),
    ]


class Fonte(BaseModel):
    nome_arquivo: str
    titulo: str
    secao: str


class RespostaSaida(BaseModel):
    resposta: str
    # Os trechos que o modelo recebeu, sem repetir (nota, seção). Vêm do código, e não
    # do texto do modelo, e não provam qual trecho ele usou.
    fontes: list[Fonte]

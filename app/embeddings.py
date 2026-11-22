"""Geração de embeddings com sentence-transformers.

As funções recebem o modelo e o prefixo como parâmetros, em vez de lerem o .env.
Assim, os testes passam um modelo falso e nenhum modelo de verdade é baixado.
"""

from functools import lru_cache

# Tamanho da coluna chunks.embedding, que é vector(384) no sql/init.sql.
DIMENSAO_ESPERADA = 384


@lru_cache(maxsize=1)
def carregar_modelo(nome: str, dispositivo: str):
    """Carrega o modelo uma vez só e reaproveita nas próximas chamadas.

    O lru_cache guarda o resultado: chamar de novo com o mesmo nome e dispositivo
    devolve o mesmo modelo, sem carregar outra vez. Na primeira vez, o modelo é
    baixado do Hugging Face e fica no cache do disco.
    """
    # Import aqui dentro: o torch só é carregado quando um embedding é pedido,
    # e não ao subir a API (a RAM é de 8 GB).
    from sentence_transformers import SentenceTransformer

    modelo = SentenceTransformer(nome, device=dispositivo)
    conferir_dimensao(modelo, nome)
    return modelo


def conferir_dimensao(modelo, nome: str) -> None:
    """Levanta erro se o modelo não gera vetores do tamanho da coluna do banco."""
    dimensao = modelo.get_embedding_dimension()
    if dimensao != DIMENSAO_ESPERADA:
        raise ValueError(
            f"O modelo {nome} gera vetores de {dimensao} dimensões, mas a coluna "
            f"chunks.embedding é vector({DIMENSAO_ESPERADA}). Troque o modelo no "
            f".env ou mude a dimensão no sql/init.sql."
        )


def gerar_vetores(modelo, textos: list[str], prefixo: str) -> list[list[float]]:
    """Calcula um vetor para cada texto, colocando o prefixo do modelo na frente.

    O prefixo é "passage: " ou "query: " no e5 e vazio no MiniLM.
    """
    vetores = modelo.encode([prefixo + texto for texto in textos])
    return [[float(x) for x in vetor] for vetor in vetores]


def vetor_para_texto(vetor: list[float]) -> str:
    """Escreve o vetor no formato que o pgvector entende: '[0.1,0.2,...]'."""
    return "[" + ",".join(repr(x) for x in vetor) + "]"

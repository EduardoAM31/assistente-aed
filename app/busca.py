"""Busca dos chunks mais próximos de uma pergunta, e geração dos vetores dos chunks."""

from app import db, embeddings
from app.config import settings


def modelo_configurado():
    """O modelo de embedding escolhido no .env, carregado uma vez só."""
    return embeddings.carregar_modelo(
        settings.embedding_modelo, settings.embedding_dispositivo
    )


def gerar_embeddings_dos_chunks(refazer: bool) -> int:
    """Calcula e grava os vetores dos chunks. Devolve quantos foram gerados."""
    chunks = db.listar_chunks_para_embedding(refazer)
    if not chunks:
        return 0  # nada a fazer, nem precisa carregar o modelo

    vetores = embeddings.gerar_vetores(
        modelo_configurado(),
        [chunk["texto"] for chunk in chunks],
        settings.embedding_prefixo_documento,
    )
    db.gravar_embeddings(
        [
            (chunk["id"], embeddings.vetor_para_texto(vetor))
            for chunk, vetor in zip(chunks, vetores)
        ]
    )
    return len(chunks)


def buscar(pergunta: str, k: int) -> list[dict]:
    """Transforma a pergunta em vetor e devolve os k chunks mais próximos."""
    [vetor] = embeddings.gerar_vetores(
        modelo_configurado(), [pergunta], settings.embedding_prefixo_pergunta
    )
    return db.buscar_chunks(embeddings.vetor_para_texto(vetor), k)

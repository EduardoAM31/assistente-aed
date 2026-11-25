"""Reindexa o banco com a configuração do .env: reenvia as notas e refaz os vetores.

Serve para a etapa 11: a cada combinação de modelo e chunking, troque o .env inteiro
(modelo, os 2 prefixos e o chunking), rode este script e depois o avaliar.py.

Rode na raiz do projeto, com o venv ativo e o banco no ar (docker compose up -d db):
    python -m scripts.reindexar

Não precisa da API: faz o mesmo caminho da rota POST /documentos (ler_nota,
dividir_em_chunks, db.salvar_documento) para cada nota do corpus/, e depois o do
POST /embeddings?refazer=true. Escreve no banco do .env (o aed).
"""

import time
from pathlib import Path

from app import busca, db
from app.chunking import dividir_em_chunks
from app.config import settings
from app.notas import ler_nota

PASTA_CORPUS = Path(__file__).resolve().parent.parent / "corpus"


def reenviar_notas(pasta: Path) -> tuple[int, int]:
    """Grava cada nota da pasta com o chunking do .env. Devolve (notas, chunks).

    Cada nota é substituída numa transação: os chunks antigos dela são apagados,
    e os novos ficam sem vetor até o gerar_embeddings_dos_chunks.
    """
    notas = chunks = 0
    for caminho in sorted(pasta.glob("*.md")):
        # Lê os bytes e decodifica como a rota faz com o arquivo enviado.
        metadados, corpo = ler_nota(caminho.read_bytes().decode("utf-8-sig"))
        partes = dividir_em_chunks(
            corpo,
            metadados["titulo"],
            settings.chunk_max_palavras,
            settings.chunk_overlap_palavras,
        )
        db.salvar_documento(
            caminho.name, metadados["titulo"], metadados["linguagem"], corpo, partes
        )
        notas += 1
        chunks += len(partes)
    return notas, chunks


def main() -> None:
    chunking = (
        "sem limite"
        if settings.chunk_max_palavras == 0
        else f"{settings.chunk_max_palavras}/{settings.chunk_overlap_palavras}"
    )
    print(f"Banco: {settings.postgres_db} em {settings.postgres_host}:{settings.postgres_port}")
    print(f"Modelo: {settings.embedding_modelo}")
    print(
        f"Prefixos: documento {settings.embedding_prefixo_documento!r}, "
        f"pergunta {settings.embedding_prefixo_pergunta!r}"
    )
    print(f"Chunking: {chunking}")

    notas, chunks = reenviar_notas(PASTA_CORPUS)
    print(f"Notas reenviadas: {notas}, com {chunks} chunks")

    inicio = time.perf_counter()
    gerados = busca.gerar_embeddings_dos_chunks(refazer=True)
    print(f"Vetores gerados: {gerados} em {time.perf_counter() - inicio:.0f} s (contando o carregamento do modelo)")

    # Uma nota que saiu do corpus/ continuaria no banco e entraria na busca.
    documentos = len(db.listar_documentos())
    if documentos != notas:
        print(
            f"AVISO: o banco tem {documentos} notas, mas o corpus tem {notas}. "
            "Alguma nota do banco não está mais no corpus."
        )


if __name__ == "__main__":
    main()

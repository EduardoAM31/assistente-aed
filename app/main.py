"""API do assistente de AED. Rodar com: uvicorn app.main:app --reload"""

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Response, UploadFile, status

from app import busca, db
from app.chunking import dividir_em_chunks
from app.config import settings
from app.notas import NotaInvalida, ler_nota
from app.schemas import DocumentoSaida, EmbeddingsSaida, ResultadoBusca, SaudeSaida

app = FastAPI(title="Assistente AED")


@app.get("/saude", response_model=SaudeSaida)
def saude(response: Response) -> SaudeSaida:
    """Diz se a API está no ar e se o banco responde."""
    if db.banco_responde():
        return SaudeSaida(api="ok", banco="ok")
    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return SaudeSaida(api="ok", banco="fora do ar")


@app.post(
    "/documentos",
    response_model=DocumentoSaida,
    status_code=status.HTTP_201_CREATED,
)
def enviar_documento(arquivo: UploadFile, response: Response) -> dict:
    """Recebe uma nota .md, divide em chunks e grava tudo no banco.

    Responde 201 quando a nota é nova e 200 quando atualiza uma nota com o mesmo nome.
    """
    # Path(...).name descarta pastas que venham no nome do arquivo enviado.
    nome_arquivo = Path(arquivo.filename or "").name
    if Path(nome_arquivo).suffix.lower() != ".md":
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "Envie um arquivo com extensão .md."
        )

    try:
        # utf-8-sig também aceita o BOM que alguns editores do Windows colocam.
        texto = arquivo.file.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "O arquivo precisa estar em UTF-8."
        )

    try:
        metadados, corpo = ler_nota(texto)
    except NotaInvalida as erro:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(erro))

    try:
        chunks = dividir_em_chunks(
            corpo,
            metadados["titulo"],
            settings.chunk_max_palavras,
            settings.chunk_overlap_palavras,
        )
    except ValueError as erro:
        # Parâmetros de chunking errados no .env são erro de configuração do servidor.
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(erro))

    documento, criado = db.salvar_documento(
        nome_arquivo, metadados["titulo"], metadados["linguagem"], corpo, chunks
    )
    if not criado:
        response.status_code = status.HTTP_200_OK
    return documento


@app.get("/documentos", response_model=list[DocumentoSaida])
def listar_documentos() -> list[dict]:
    """Lista as notas gravadas no banco."""
    return db.listar_documentos()


@app.post("/embeddings", response_model=EmbeddingsSaida)
def gerar_embeddings(refazer: bool = False) -> EmbeddingsSaida:
    """Calcula os vetores dos chunks que estão sem embedding.

    Com refazer=true, recalcula todos. Use isso ao trocar o modelo no .env, para não
    misturar vetores de modelos diferentes. Reenviar uma nota apaga os vetores dela,
    então esta rota precisa rodar de novo depois do reenvio.
    """
    try:
        gerados = busca.gerar_embeddings_dos_chunks(refazer)
    except ValueError as erro:
        # Por exemplo, um modelo no .env com dimensão diferente de 384.
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(erro))
    return EmbeddingsSaida(modelo=settings.embedding_modelo, gerados=gerados)


@app.get("/busca", response_model=list[ResultadoBusca])
def buscar(
    pergunta: str = Query(min_length=1),
    k: int | None = Query(default=None, ge=1),
) -> list[dict]:
    """Rota de depuração: mostra os k chunks mais próximos da pergunta.

    distancia é a distância de cosseno do pgvector (0 é igual; quanto maior, mais
    longe). Sem k, usa o BUSCA_K do .env.
    """
    try:
        return busca.buscar(pergunta, k or settings.busca_k)
    except ValueError as erro:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(erro))

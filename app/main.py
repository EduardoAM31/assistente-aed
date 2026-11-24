"""API do assistente de AED. Rodar com: uvicorn app.main:app --reload"""

from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request, Response, UploadFile, status
from fastapi.responses import JSONResponse
from pg8000.exceptions import InterfaceError

from app import busca, db
from app.chunking import dividir_em_chunks
from app.config import settings
from app.embeddings import ErroModeloEmbedding
from app.geracao import criar_provedor
from app.geracao.base import ErroProvedorLLM, ProvedorLLM, listar_fontes
from app.notas import NotaInvalida, ler_nota
from app.schemas import (
    TAMANHO_MAXIMO_PERGUNTA,
    DocumentoSaida,
    EmbeddingsSaida,
    PerguntaEntrada,
    RespostaSaida,
    ResultadoBusca,
    SaudeSaida,
)

app = FastAPI(title="Assistente AED")


# Tratamentos únicos para serviços fora do ar, em vez de um try/except em cada rota.
@app.exception_handler(InterfaceError)
async def banco_fora_do_ar(request: Request, erro: InterfaceError) -> JSONResponse:
    """O pg8000 levanta InterfaceError quando não consegue conectar no Postgres."""
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": (
                f"Não foi possível conectar ao banco em {settings.postgres_host}:"
                f"{settings.postgres_port}. Confira se o Postgres está rodando "
                "(docker compose up -d)."
            )
        },
    )


@app.exception_handler(ErroModeloEmbedding)
async def modelo_indisponivel(request: Request, erro: ErroModeloEmbedding) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"detail": str(erro)}
    )


@lru_cache(maxsize=1)
def provedor_configurado() -> ProvedorLLM:
    """O provedor de LLM do .env, criado uma vez só (reaproveita a conexão HTTP)."""
    return criar_provedor(settings)


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
    pergunta: str = Query(min_length=1, max_length=TAMANHO_MAXIMO_PERGUNTA),
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


@app.post("/perguntas", response_model=RespostaSaida)
def responder_pergunta(entrada: PerguntaEntrada) -> dict:
    """Busca os trechos mais próximos da pergunta e pede a resposta ao LLM.

    As fontes são os trechos consultados (sem repetir nota e seção), e não uma
    citação extraída do texto do modelo.
    """
    try:
        contexto = busca.buscar(entrada.pergunta, settings.busca_k)
    except ValueError as erro:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(erro))
    if not contexto:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Nenhum chunk tem embedding ainda. Rode POST /embeddings antes de perguntar.",
        )

    try:
        provedor = provedor_configurado()
    except ValueError as erro:
        # LLM_PROVEDOR inválido no .env é erro de configuração do servidor.
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(erro))

    try:
        resposta = provedor.gerar_resposta(entrada.pergunta, contexto)
    except ErroProvedorLLM as erro:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(erro))

    return {"resposta": resposta, "fontes": listar_fontes(contexto)}

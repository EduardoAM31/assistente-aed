"""Calcula o recall@3 da busca com as perguntas de avaliacao/perguntas.jsonl.

Rode na raiz do projeto, com o venv ativo e o banco no ar (docker compose up -d db):
    python -m avaliacao.avaliar

Não precisa da API nem do Ollama: chama busca.buscar direto, a mesma função que a
rota GET /busca usa. Usa o banco do .env (o aed), nunca o aed_teste.

Uma pergunta acerta quando algum dos 3 primeiros chunks vem da nota e da seção do
rótulo. As principais e as variantes com erro de digitação são medidas à parte, e
as "sem resposta no corpus" ficam fora do cálculo.
"""

import json
import math
import sys
from datetime import datetime
from pathlib import Path

from app.chunking import dividir_em_chunks, separar_secoes
from app.notas import ler_nota

PASTA_AVALIACAO = Path(__file__).resolve().parent
ARQUIVO_PERGUNTAS = PASTA_AVALIACAO / "perguntas.jsonl"
PASTA_RESULTADOS = PASTA_AVALIACAO / "resultados"
PASTA_CORPUS = PASTA_AVALIACAO.parent / "corpus"

K = 3  # é o recall@3: fixo aqui, e não o BUSCA_K do .env, que é o da API
# Conferência do modelo: quantos chunks recalcular e a distância máxima aceita.
# Com o mesmo modelo, a distância fica perto de 0 (só arredondamento).
AMOSTRA_VETORES = 5
DISTANCIA_MAXIMA = 0.01


class ErroAvaliacao(Exception):
    """O perguntas.jsonl tem algum problema que impede a medição."""


# ---------------------------------------------------------------------------
# Funções puras: não usam banco nem modelo, e por isso são testadas sem eles.
# ---------------------------------------------------------------------------


def ler_perguntas(texto: str) -> list[dict]:
    """Lê o JSONL (uma pergunta por linha) e confere a estrutura de cada linha.

    Cada linha tem id e pergunta, e mais: nota e secao (pergunta com resposta), ou
    "sem_resposta": true. Uma variante com erro de digitação tem também variante_de,
    com o id da principal, e o mesmo rótulo dela.
    """
    perguntas = []
    for numero, linha in enumerate(texto.splitlines(), start=1):
        if not linha.strip():
            continue
        try:
            pergunta = json.loads(linha)
        except json.JSONDecodeError as erro:
            raise ErroAvaliacao(f"Linha {numero}: JSON inválido ({erro.msg}).") from erro
        if not isinstance(pergunta.get("id"), int) or not pergunta.get("pergunta"):
            raise ErroAvaliacao(f"Linha {numero}: precisa de um id inteiro e da pergunta.")
        if not pergunta.get("sem_resposta") and not (pergunta.get("nota") and pergunta.get("secao")):
            raise ErroAvaliacao(
                f"Linha {numero} (id {pergunta['id']}): precisa de nota e secao, "
                'ou de "sem_resposta": true.'
            )
        perguntas.append(pergunta)

    por_id: dict[int, dict] = {}
    for pergunta in perguntas:
        if pergunta["id"] in por_id:
            raise ErroAvaliacao(f"O id {pergunta['id']} aparece mais de uma vez.")
        por_id[pergunta["id"]] = pergunta

    for pergunta in perguntas:
        if "variante_de" not in pergunta:
            continue
        principal = por_id.get(pergunta["variante_de"])
        if principal is None or "variante_de" in principal or principal.get("sem_resposta"):
            raise ErroAvaliacao(
                f"id {pergunta['id']}: variante_de = {pergunta['variante_de']} precisa "
                "apontar para uma pergunta principal com resposta."
            )
        if (pergunta.get("nota"), pergunta.get("secao")) != (principal["nota"], principal["secao"]):
            raise ErroAvaliacao(
                f"id {pergunta['id']}: a variante precisa ter a mesma nota e seção da "
                f"principal (id {principal['id']})."
            )
    return perguntas


def secoes_do_corpus(pasta: Path) -> dict[str, list[str]]:
    """Os títulos das seções ## de cada nota, pelo nome do arquivo."""
    secoes = {}
    for caminho in sorted(pasta.glob("*.md")):
        _, corpo = ler_nota(caminho.read_text(encoding="utf-8-sig"))
        secoes[caminho.name] = [titulo for titulo, _ in separar_secoes(corpo)]
    return secoes


def conferir_rotulos(perguntas: list[dict], secoes: dict[str, list[str]]) -> list[str]:
    """Os rótulos que não existem no corpus, com os títulos certos para corrigir."""
    problemas = []
    for pergunta in perguntas:
        if pergunta.get("sem_resposta"):
            continue
        nota, secao = pergunta["nota"], pergunta["secao"]
        if nota not in secoes:
            problemas.append(
                f"id {pergunta['id']}: a nota {nota!r} não existe. "
                f"Notas do corpus: {', '.join(secoes)}"
            )
        elif secao not in secoes[nota]:
            titulos = "\n".join(f"      - {titulo}" for titulo in secoes[nota])
            problemas.append(
                f"id {pergunta['id']}: a seção {secao!r} não existe em {nota}. "
                f"Seções da nota:\n{titulos}"
            )
    return problemas


def acertou(pergunta: dict, resultados: list[dict]) -> bool:
    """Acerto: algum chunk dos resultados vem da nota e da seção do rótulo."""
    return any(
        r["nome_arquivo"] == pergunta["nota"] and r["secao"] == pergunta["secao"]
        for r in resultados
    )


def calcular_recall(perguntas: list[dict], resultados_por_id: dict[int, list[dict]]) -> dict:
    """Acertos e recall de um grupo de perguntas, com a lista das que erraram.

    O recall fica None quando o grupo está vazio (não há o que medir).
    """
    erros = []
    for pergunta in perguntas:
        resultados = resultados_por_id[pergunta["id"]]
        if not acertou(pergunta, resultados):
            erros.append(
                {
                    "id": pergunta["id"],
                    "pergunta": pergunta["pergunta"],
                    "esperado": {"nota": pergunta["nota"], "secao": pergunta["secao"]},
                    "vieram": [resumir_resultado(r) for r in resultados],
                }
            )
    total = len(perguntas)
    acertos = total - len(erros)
    return {
        "perguntas": total,
        "acertos": acertos,
        "recall": acertos / total if total else None,
        "erros": erros,
    }


def resumir_resultado(resultado: dict) -> dict:
    """Só o que interessa de um chunk devolvido pela busca."""
    return {
        "nota": resultado["nome_arquivo"],
        "secao": resultado["secao"],
        "distancia": round(float(resultado["distancia"]), 4),
    }


def contar_chunks_esperados(pasta: Path, max_palavras: int, overlap_palavras: int) -> int:
    """Quantos chunks o chunking gera para o corpus, sem olhar o banco."""
    total = 0
    for caminho in sorted(pasta.glob("*.md")):
        metadados, corpo = ler_nota(caminho.read_text(encoding="utf-8-sig"))
        total += len(dividir_em_chunks(corpo, metadados["titulo"], max_palavras, overlap_palavras))
    return total


def distancia_cosseno(a: list[float], b: list[float]) -> float:
    """1 - cosseno do ângulo entre os vetores, a mesma conta do <=> do pgvector."""
    produto = sum(x * y for x, y in zip(a, b))
    normas = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return 1 - produto / normas


def nome_do_resultado(data: datetime, modelo: str, max_palavras: int, overlap_palavras: int) -> str:
    """Ex.: 2026-11-25_1430_paraphrase-multilingual-MiniLM-L12-v2_60-10.json"""
    chunking = "sem-limite" if max_palavras == 0 else f"{max_palavras}-{overlap_palavras}"
    modelo_curto = modelo.split("/")[-1]  # tira o "sentence-transformers/" ou "intfloat/"
    return f"{data:%Y-%m-%d_%H%M}_{modelo_curto}_{chunking}.json"


def formatar_recall(grupo: dict) -> str:
    if grupo["recall"] is None:
        return "sem perguntas"
    return f"{grupo['recall']:.1%} ({grupo['acertos']} de {grupo['perguntas']})"


# ---------------------------------------------------------------------------
# A rodada: usa o banco e o modelo do .env.
# ---------------------------------------------------------------------------


def conferir_banco(settings, db, embeddings, carregar_modelo) -> list[str]:
    """Avisos de que os vetores do banco podem não ser do modelo e do chunking do .env.

    O banco não guarda com qual modelo nem com qual chunking os vetores foram gerados.
    Sem estes avisos, uma mudança no .env sem reenviar as notas daria um recall
    errado, sem erro nenhum.
    """
    avisos = []
    contagem = db.contar_chunks()
    esperados = contar_chunks_esperados(
        PASTA_CORPUS, settings.chunk_max_palavras, settings.chunk_overlap_palavras
    )
    print(f"Chunks no banco: {contagem['total']} ({contagem['com_vetor']} com vetor)")
    print(f"Chunks que o chunking do .env gera para o corpus: {esperados}")

    if contagem["total"] != esperados:
        avisos.append(
            f"O banco tem {contagem['total']} chunks, mas o chunking do .env gera "
            f"{esperados}. Reenvie as notas (POST /documentos) e refaça os vetores."
        )
    if contagem["com_vetor"] != contagem["total"]:
        avisos.append(
            f"{contagem['total'] - contagem['com_vetor']} chunks estão sem vetor e ficam "
            "fora da busca. Rode POST /embeddings."
        )

    amostra = db.amostrar_chunks_com_vetor(AMOSTRA_VETORES)
    if amostra:
        recalculados = embeddings.gerar_vetores(
            carregar_modelo(), [c["texto"] for c in amostra], settings.embedding_prefixo_documento
        )
        maior = max(
            distancia_cosseno(json.loads(c["embedding"]), vetor)
            for c, vetor in zip(amostra, recalculados)
        )
        print(
            f"Maior distância entre o vetor guardado e o recalculado agora "
            f"({len(amostra)} chunks): {maior:.6f}"
        )
        if maior > DISTANCIA_MAXIMA:
            avisos.append(
                f"O vetor guardado de um chunk está a {maior:.4f} do recalculado com o "
                "modelo do .env: os vetores do banco devem ser de outro modelo ou "
                "prefixo. Rode POST /embeddings?refazer=true."
            )
    return avisos


def main() -> None:
    # Imports aqui dentro: o settings exige o .env, e o busca carrega o torch.
    # Assim, os testes das funções puras acima rodam sem nada disso.
    from pg8000.exceptions import InterfaceError

    from app import busca, db, embeddings
    from app.config import settings

    try:
        perguntas = ler_perguntas(ARQUIVO_PERGUNTAS.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        sys.exit(f"Não achei {ARQUIVO_PERGUNTAS}.")
    except ErroAvaliacao as erro:
        sys.exit(f"Problema no perguntas.jsonl: {erro}")

    problemas = conferir_rotulos(perguntas, secoes_do_corpus(PASTA_CORPUS))
    if problemas:
        print("Rótulos que não existem no corpus (corrija antes de medir):")
        for problema in problemas:
            print(f"  - {problema}")
        sys.exit(1)

    principais = [p for p in perguntas if not p.get("sem_resposta") and "variante_de" not in p]
    variantes = [p for p in perguntas if "variante_de" in p]
    sem_resposta = [p for p in perguntas if p.get("sem_resposta")]

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
    print(f"Chunking: {chunking}   k: {K}")
    print(
        f"Perguntas: {len(principais)} principais, {len(variantes)} variantes, "
        f"{len(sem_resposta)} sem resposta no corpus"
    )

    try:
        # O modelo só é carregado depois de o banco responder: com o banco fora do ar,
        # o erro aparece na hora, sem esperar o modelo carregar.
        avisos = conferir_banco(settings, db, embeddings, busca.modelo_configurado)
        resultados_por_id = {p["id"]: busca.buscar(p["pergunta"], K) for p in perguntas}
    except InterfaceError:
        sys.exit(
            f"Não foi possível conectar ao banco em {settings.postgres_host}:"
            f"{settings.postgres_port}. Suba o Postgres: docker compose up -d db"
        )
    except embeddings.ErroModeloEmbedding as erro:
        sys.exit(str(erro))

    for aviso in avisos:
        print(f"AVISO: {aviso}")

    resultado_principais = calcular_recall(principais, resultados_por_id)
    resultado_variantes = calcular_recall(variantes, resultados_por_id)

    print(f"\nrecall@{K} das principais: {formatar_recall(resultado_principais)}")
    print(f"recall@{K} das variantes com erro de digitação: {formatar_recall(resultado_variantes)}")

    for titulo, grupo in [("principais", resultado_principais), ("variantes", resultado_variantes)]:
        if grupo["erros"]:
            print(f"\nErros nas {titulo}:")
        for erro in grupo["erros"]:
            print(f"  [{erro['id']}] {erro['pergunta']}")
            print(f"      esperado: {erro['esperado']['nota']} > {erro['esperado']['secao']}")
            for veio in erro["vieram"]:
                print(f"      veio:     {veio['nota']} > {veio['secao']} ({veio['distancia']})")

    # As sem resposta não entram no recall. O que veio fica registrado para ver,
    # depois, se a distância ajuda a perceber que o corpus não cobre a pergunta.
    lista_sem_resposta = [
        {
            "id": p["id"],
            "pergunta": p["pergunta"],
            "vieram": [resumir_resultado(r) for r in resultados_por_id[p["id"]]],
        }
        for p in sem_resposta
    ]
    if lista_sem_resposta:
        print("\nSem resposta no corpus (fora do cálculo):")
    for item in lista_sem_resposta:
        primeiro = item["vieram"][0] if item["vieram"] else None
        detalhe = f"{primeiro['nota']} > {primeiro['secao']} ({primeiro['distancia']})" if primeiro else "nada"
        print(f"  [{item['id']}] {item['pergunta']}")
        print(f"      mais perto: {detalhe}")

    agora = datetime.now()
    rodada = {
        "data": agora.isoformat(timespec="seconds"),
        "modelo": settings.embedding_modelo,
        "prefixo_documento": settings.embedding_prefixo_documento,
        "prefixo_pergunta": settings.embedding_prefixo_pergunta,
        "chunk_max_palavras": settings.chunk_max_palavras,
        "chunk_overlap_palavras": settings.chunk_overlap_palavras,
        "k": K,
        "avisos": avisos,
        "principais": resultado_principais,
        "variantes": resultado_variantes,
        "sem_resposta": lista_sem_resposta,
    }
    PASTA_RESULTADOS.mkdir(exist_ok=True)
    arquivo = PASTA_RESULTADOS / nome_do_resultado(
        agora, settings.embedding_modelo, settings.chunk_max_palavras, settings.chunk_overlap_palavras
    )
    # newline="\n": no Windows, o write_text trocaria cada \n por \r\n.
    arquivo.write_text(
        json.dumps(rodada, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"\nResultado gravado em {arquivo.relative_to(PASTA_AVALIACAO.parent)}")


if __name__ == "__main__":
    main()

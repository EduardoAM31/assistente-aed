"""Conta os tokens de cada chunk do corpus, para cada configuração de chunking.

Serve para escolher os tamanhos de chunk do experimento da etapa 11 e para refazer
a medição quando o corpus mudar (por exemplo, depois da parte 2, na etapa 7).

Rode na raiz do projeto:
    python -m scripts.contar_tokens

O modelo, o prefixo de documento e o dispositivo vêm do .env, como na API. Para
medir o e5, troque EMBEDDING_MODELO e EMBEDDING_PREFIXO_DOCUMENTO no .env.
"""

from pathlib import Path

from sentence_transformers import SentenceTransformer

from app.chunking import dividir_em_chunks
from app.config import settings
from app.notas import ler_nota

PASTA_CORPUS = Path(__file__).resolve().parent.parent / "corpus"
# (máximo de palavras, overlap). O par (0, 0) significa "sem limite".
CONFIGURACOES = [(40, 8), (60, 10), (80, 15), (100, 15), (120, 20), (150, 25), (0, 0)]

modelo = SentenceTransformer(settings.embedding_modelo, device=settings.embedding_dispositivo)
limite = modelo.max_seq_length
tokenizador = modelo.tokenizer
# O e5 espera "passage: " no começo de cada chunk, e esse prefixo também gasta tokens.
prefixo = settings.embedding_prefixo_documento

notas = []
for caminho in sorted(PASTA_CORPUS.glob("*.md")):
    metadados, corpo = ler_nota(caminho.read_text(encoding="utf-8"))
    notas.append((metadados["titulo"], corpo))

print(f"Modelo: {settings.embedding_modelo} (prefixo de documento: {prefixo!r})")
print(f"Limite do modelo: {limite} tokens. Notas lidas: {len(notas)}")
print(f"{'config':>10} {'chunks':>7} {'min':>5} {'mediana':>8} {'max':>5} {'acima do limite':>16}")

for max_palavras, overlap in CONFIGURACOES:
    tokens_por_chunk = []
    for titulo, corpo in notas:
        for chunk in dividir_em_chunks(corpo, titulo, max_palavras, overlap):
            # O texto do chunk já inclui o prefixo "# nota" e "## seção".
            # O tokenizador também soma os tokens especiais de início e fim, como o modelo faz.
            tokens_por_chunk.append(len(tokenizador(prefixo + chunk.texto)["input_ids"]))
    tokens_por_chunk.sort()
    n = len(tokens_por_chunk)
    mediana = tokens_por_chunk[n // 2]  # o elemento do meio da lista ordenada
    acima = sum(1 for t in tokens_por_chunk if t > limite)
    nome = "sem limite" if max_palavras == 0 else f"{max_palavras}/{overlap}"
    print(f"{nome:>10} {n:>7} {tokens_por_chunk[0]:>5} {mediana:>8} {tokens_por_chunk[-1]:>5} {acima:>9} ({acima / n:.0%})")

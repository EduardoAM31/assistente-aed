"""Divisão das notas em chunks. Função pura: não acessa banco nem configuração.

Regras (decididas na etapa 4):
1. Cada seção "##" é cortada separadamente. O texto antes da primeira "##"
   (o título "#" da nota) não vira chunk, e uma seção vazia também não.
2. Uma seção que cabe no limite de palavras vira um chunk só, sem overlap.
3. Uma seção maior que o limite é quebrada em janelas de até max_palavras.
   Cada janela repete as últimas overlap_palavras da anterior, para uma ideia
   que fica na fronteira entre dois chunks não se perder. Se a última janela
   traria no máximo overlap_palavras palavras novas, a janela anterior é
   estendida até o fim da seção (e pode passar de max_palavras em até
   overlap_palavras palavras).
4. max_palavras = 0 significa "sem limite": cada seção vira um chunk.
5. Todo chunk começa com o título da nota e o da seção. Esse prefixo não
   conta no limite de palavras.
"""

import re
from typing import NamedTuple

# Uma "palavra" é qualquer sequência de caracteres sem espaço.
PALAVRA = re.compile(r"\S+")


class Chunk(NamedTuple):
    secao: str  # título da seção "##", que é o rótulo usado na avaliação
    texto: str  # prefixo com os títulos + trecho da seção


def separar_secoes(corpo: str) -> list[tuple[str, str]]:
    """Devolve a lista de (título da seção, texto da seção) do corpo da nota."""
    secoes: list[tuple[str, list[str]]] = []
    dentro_de_codigo = False

    for linha in corpo.splitlines():
        # Uma linha "## ..." dentro de um bloco de código não é título de seção.
        if linha.lstrip().startswith("```"):
            dentro_de_codigo = not dentro_de_codigo

        if not dentro_de_codigo and linha.startswith("## "):
            secoes.append((linha[3:].strip(), []))
        elif secoes:
            secoes[-1][1].append(linha)
        # Linhas antes da primeira "##" são ignoradas.

    return [(titulo, "\n".join(linhas).strip()) for titulo, linhas in secoes]


def quebrar_texto(texto: str, max_palavras: int, overlap_palavras: int) -> list[str]:
    """Quebra o texto em janelas de até max_palavras, com overlap entre elas.

    As janelas são recortadas do texto original, então as quebras de linha e a
    indentação dos exemplos de código são mantidas.
    """
    palavras = list(PALAVRA.finditer(texto))
    if max_palavras == 0 or len(palavras) <= max_palavras:
        return [texto]

    passo = max_palavras - overlap_palavras
    janelas = []
    inicio = 0
    while True:
        fim = min(inicio + max_palavras, len(palavras))
        # Se sobram no máximo overlap_palavras palavras depois desta janela, a próxima
        # seria quase só repetição. Então esta janela vai até o fim da seção.
        if len(palavras) - fim <= overlap_palavras:
            fim = len(palavras)
        janelas.append(texto[palavras[inicio].start() : palavras[fim - 1].end()])
        if fim == len(palavras):
            break
        inicio += passo
    return janelas


def dividir_em_chunks(
    corpo: str, titulo_nota: str, max_palavras: int, overlap_palavras: int
) -> list[Chunk]:
    """Divide o corpo de uma nota em chunks, seguindo as regras do topo do arquivo."""
    if max_palavras < 0 or overlap_palavras < 0:
        raise ValueError("max_palavras e overlap_palavras não podem ser negativos.")
    if max_palavras > 0 and overlap_palavras >= max_palavras:
        raise ValueError("overlap_palavras precisa ser menor que max_palavras.")

    chunks = []
    for titulo_secao, texto_secao in separar_secoes(corpo):
        if not texto_secao:
            continue  # seção vazia não gera chunk
        prefixo = f"# {titulo_nota}\n## {titulo_secao}\n\n"
        for trecho in quebrar_texto(texto_secao, max_palavras, overlap_palavras):
            chunks.append(Chunk(secao=titulo_secao, texto=prefixo + trecho))
    return chunks

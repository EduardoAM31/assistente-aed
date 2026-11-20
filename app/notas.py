"""Leitura das notas do corpus: separa o cabeçalho YAML (frontmatter) do corpo."""

import yaml

LINGUAGENS_VALIDAS = ("C", "C++")


class NotaInvalida(ValueError):
    """A nota não segue o formato do corpus. A mensagem diz o que corrigir."""


def ler_nota(texto: str) -> tuple[dict, str]:
    """Separa o frontmatter do corpo da nota e valida os metadados obrigatórios.

    A nota começa com um bloco YAML entre duas linhas "---":

        ---
        titulo: Por que o índice de vetores em C começa em 0
        linguagem: C
        ---
        # Título da nota ...
    """
    # splitlines() aceita tanto \n (Linux) quanto \r\n (Windows).
    linhas = texto.splitlines()

    if not linhas or linhas[0].strip() != "---":
        raise NotaInvalida(
            "A nota precisa começar com um cabeçalho YAML entre duas linhas '---'."
        )

    fim = None
    for i in range(1, len(linhas)):
        if linhas[i].strip() == "---":
            fim = i
            break
    if fim is None:
        raise NotaInvalida("O cabeçalho YAML não foi fechado com uma linha '---'.")

    try:
        metadados = yaml.safe_load("\n".join(linhas[1:fim]))
    except yaml.YAMLError as erro:
        raise NotaInvalida(f"O cabeçalho YAML tem um erro de sintaxe: {erro}") from erro

    if not isinstance(metadados, dict):
        raise NotaInvalida("O cabeçalho YAML precisa ter campos no formato 'nome: valor'.")

    titulo = metadados.get("titulo")
    if not isinstance(titulo, str) or not titulo.strip():
        raise NotaInvalida("O cabeçalho YAML precisa do campo 'titulo', com um texto.")

    linguagem = metadados.get("linguagem")
    if linguagem not in LINGUAGENS_VALIDAS:
        raise NotaInvalida(
            f"O campo 'linguagem' precisa ser 'C' ou 'C++', mas veio {linguagem!r}."
        )

    corpo = "\n".join(linhas[fim + 1 :]).strip()
    return metadados, corpo

"""Interface dos provedores de LLM e o prompt, que é o mesmo para todos eles."""

from typing import Protocol

INSTRUCOES = (
    "Você é um monitor de Algoritmos e Estruturas de Dados e ajuda iniciantes. "
    "Responda em português, em no máximo 4 frases, sem repetir a pergunta. "
    "Use somente as informações dos trechos numerados abaixo, sem acrescentar nada "
    "que não esteja neles, e cite o número do trecho, como [1]. "
    "Se precisar de código, mostre no máximo um exemplo curto, de até 6 linhas, "
    "baseado nos trechos. Se os trechos não responderem a pergunta, responda apenas: "
    '"Não sei responder isso com base nas notas."'
)


class ErroProvedorLLM(Exception):
    """O provedor está fora do ar, demorou demais ou respondeu com erro."""


class ProvedorLLM(Protocol):
    """Qualquer objeto com este método serve como provedor (inclusive os falsos dos testes)."""

    def gerar_resposta(self, pergunta: str, contexto: list[dict]) -> str:
        """Responde a pergunta usando os chunks do contexto."""
        ...


def montar_mensagens(pergunta: str, contexto: list[dict]) -> list[dict[str, str]]:
    """Monta as mensagens do chat: as instruções (system) e os trechos com a pergunta (user).

    Cada chunk já começa com "# <nota>" e "## <seção>", então o título e a seção
    aparecem dentro do próprio trecho.
    """
    trechos = "\n\n".join(
        f"[{numero}] {chunk['texto']}" for numero, chunk in enumerate(contexto, start=1)
    )
    return [
        {"role": "system", "content": INSTRUCOES},
        {"role": "user", "content": f"Trechos:\n\n{trechos}\n\nPergunta: {pergunta}"},
    ]


def listar_fontes(contexto: list[dict]) -> list[dict[str, str]]:
    """Lista (nota, seção) dos chunks consultados, sem repetir e mantendo a ordem.

    A lista mostra os trechos que o modelo recebeu, e não prova qual deles ele usou.
    """
    fontes = []
    vistas = set()
    for chunk in contexto:
        chave = (chunk["nome_arquivo"], chunk["secao"])
        if chave not in vistas:
            vistas.add(chave)
            fontes.append(
                {
                    "nome_arquivo": chunk["nome_arquivo"],
                    "titulo": chunk["titulo"],
                    "secao": chunk["secao"],
                }
            )
    return fontes

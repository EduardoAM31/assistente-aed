"""Acesso ao banco com pg8000 e SQL escrito à mão.

O pg8000 é um driver de PostgreSQL escrito só em Python, sem bibliotecas nativas.
Usamos a interface "native" dele: cada comando roda e é confirmado na hora
(autocommit), e os parâmetros entram no SQL pelo nome, como :nome_arquivo.
"""

import pg8000.native
from pg8000.exceptions import DatabaseError, InterfaceError

from app.config import settings


def conectar() -> pg8000.native.Connection:
    """Abre uma conexão nova com os dados do .env."""
    return pg8000.native.Connection(
        user=settings.postgres_user,
        password=settings.postgres_password,
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=settings.postgres_db,
    )


def _como_dicionarios(conexao: pg8000.native.Connection, linhas: list) -> list[dict]:
    """O pg8000 devolve cada linha como lista; aqui viram dicionários {coluna: valor}."""
    nomes = [coluna["name"] for coluna in conexao.columns]
    return [dict(zip(nomes, linha)) for linha in linhas]


def banco_responde() -> bool:
    """Testa se o banco aceita conexões e responde a uma consulta simples."""
    try:
        with conectar() as conexao:
            conexao.run("SELECT 1")
        return True
    except (InterfaceError, DatabaseError):
        return False


def salvar_documento(
    nome_arquivo: str, titulo: str, linguagem: str, conteudo: str
) -> tuple[dict, bool]:
    """Grava a nota ou atualiza a que tem o mesmo nome de arquivo.

    Devolve o documento gravado e True se ele foi criado (False se foi atualizado).
    """
    # O "with" fecha a conexão no fim do bloco.
    with conectar() as conexao:
        existente = conexao.run(
            "SELECT id FROM documentos WHERE nome_arquivo = :nome_arquivo",
            nome_arquivo=nome_arquivo,
        )

        linhas = conexao.run(
            """
            INSERT INTO documentos (nome_arquivo, titulo, linguagem, conteudo)
            VALUES (:nome_arquivo, :titulo, :linguagem, :conteudo)
            ON CONFLICT (nome_arquivo) DO UPDATE
                SET titulo    = EXCLUDED.titulo,
                    linguagem = EXCLUDED.linguagem,
                    conteudo  = EXCLUDED.conteudo
            RETURNING id, nome_arquivo, titulo, linguagem
            """,
            nome_arquivo=nome_arquivo,
            titulo=titulo,
            linguagem=linguagem,
            conteudo=conteudo,
        )
        documento = _como_dicionarios(conexao, linhas)[0]

    return documento, not existente


def listar_documentos() -> list[dict]:
    """Lista as notas gravadas, em ordem de nome de arquivo."""
    with conectar() as conexao:
        linhas = conexao.run(
            """
            SELECT id, nome_arquivo, titulo, linguagem
            FROM documentos
            ORDER BY nome_arquivo
            """
        )
        return _como_dicionarios(conexao, linhas)

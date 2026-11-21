"""Acesso ao banco com pg8000 e SQL escrito à mão.

O pg8000 é um driver de PostgreSQL escrito só em Python, sem bibliotecas nativas.
Usamos a interface "native" dele: cada comando roda e é confirmado na hora
(autocommit), e os parâmetros entram no SQL pelo nome, como :nome_arquivo.
"""

import pg8000.native
from pg8000.exceptions import DatabaseError, InterfaceError

from app.chunking import Chunk
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
    nome_arquivo: str, titulo: str, linguagem: str, conteudo: str, chunks: list[Chunk]
) -> tuple[dict, bool]:
    """Grava a nota e os chunks dela, ou atualiza a nota com o mesmo nome de arquivo.

    Tudo roda numa transação só: se algo falhar no meio, nada é gravado.
    Devolve o documento gravado e True se ele foi criado (False se foi atualizado).
    """
    # O "with" fecha a conexão no fim do bloco.
    with conectar() as conexao:
        conexao.run("START TRANSACTION")
        try:
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

            # No reenvio, o documento mantém o mesmo id, então o ON DELETE CASCADE
            # não age: os chunks antigos precisam ser apagados aqui.
            conexao.run(
                "DELETE FROM chunks WHERE documento_id = :documento_id",
                documento_id=documento["id"],
            )
            for ordem, chunk in enumerate(chunks):
                conexao.run(
                    """
                    INSERT INTO chunks (documento_id, ordem, secao, texto)
                    VALUES (:documento_id, :ordem, :secao, :texto)
                    """,
                    documento_id=documento["id"],
                    ordem=ordem,
                    secao=chunk.secao,
                    texto=chunk.texto,
                )

            conexao.run("COMMIT")
        except Exception:
            conexao.run("ROLLBACK")
            raise

    documento["quantidade_chunks"] = len(chunks)
    return documento, not existente


def listar_documentos() -> list[dict]:
    """Lista as notas gravadas, em ordem de nome de arquivo, com o número de chunks."""
    with conectar() as conexao:
        linhas = conexao.run(
            """
            SELECT d.id, d.nome_arquivo, d.titulo, d.linguagem,
                   count(c.id) AS quantidade_chunks
            FROM documentos d
            LEFT JOIN chunks c ON c.documento_id = d.id
            GROUP BY d.id
            ORDER BY d.nome_arquivo
            """
        )
        return _como_dicionarios(conexao, linhas)

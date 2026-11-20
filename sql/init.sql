CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documentos (
    id           SERIAL PRIMARY KEY,
    nome_arquivo TEXT NOT NULL UNIQUE,
    titulo       TEXT NOT NULL,
    linguagem    TEXT NOT NULL,
    conteudo     TEXT NOT NULL,
    criado_em    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chunks (
    id           SERIAL PRIMARY KEY,
    documento_id INTEGER NOT NULL REFERENCES documentos(id) ON DELETE CASCADE,
    ordem        INTEGER NOT NULL,
    secao        TEXT NOT NULL,
    texto        TEXT NOT NULL,
    embedding    vector(384),
    UNIQUE (documento_id, ordem)
);

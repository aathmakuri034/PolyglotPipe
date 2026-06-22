CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id           BIGSERIAL PRIMARY KEY,
    source_path  TEXT      NOT NULL,
    source_lang  TEXT      NOT NULL,
    target_lang  TEXT      NOT NULL,
    media_type   TEXT      NOT NULL CHECK (media_type IN ('audio','pdf','image','text')),
    timestamp    TEXT,
    confidence   REAL      NOT NULL,
    chunk_index  INTEGER   NOT NULL,
    content      TEXT      NOT NULL,
    embedding    vector(384),
    content_tsv  tsvector  GENERATED ALWAYS AS (to_tsvector('simple', content)) STORED,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (source_path, chunk_index)
);

CREATE INDEX IF NOT EXISTS docs_embedding_hnsw
    ON documents USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64)
    WHERE embedding IS NOT NULL;

CREATE INDEX IF NOT EXISTS docs_tsv_gin     ON documents USING gin (content_tsv);
CREATE INDEX IF NOT EXISTS docs_source_path ON documents (source_path);
CREATE INDEX IF NOT EXISTS docs_lang_media  ON documents (source_lang, media_type);

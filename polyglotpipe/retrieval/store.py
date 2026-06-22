from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Sequence

import numpy as np
import psycopg
from langchain_core.documents import Document
from numpy.typing import NDArray
from pgvector.psycopg import register_vector_async
from psycopg_pool import AsyncConnectionPool

from polyglotpipe.retrieval.config import Settings
from polyglotpipe.retrieval.embedder import Embedder
from polyglotpipe.retrieval.exceptions import StoreError
from polyglotpipe.retrieval.types import RetrievedChunk, SearchFilters

SCHEMA_PATH = Path(__file__).parent / "schema.sql"

_INSERT_SQL = """
INSERT INTO documents (
    source_path, source_lang, target_lang, media_type,
    timestamp, confidence, chunk_index, content, embedding
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (source_path, chunk_index) DO UPDATE SET
    content = EXCLUDED.content,
    embedding = EXCLUDED.embedding,
    confidence = EXCLUDED.confidence
RETURNING id
"""

_SELECT_COLS = (
    "id, content, source_path, source_lang, target_lang, "
    "media_type, timestamp, chunk_index"
)


class VectorStore(ABC):
    @abstractmethod
    async def add_documents(self, docs: Sequence[Document]) -> list[int]: ...
    @abstractmethod
    async def search_dense(
        self, query_embedding: NDArray[np.float32], top_k: int,
        filters: SearchFilters | None,
    ) -> list[RetrievedChunk]: ...
    @abstractmethod
    async def search_lexical(
        self, query: str, top_k: int, filters: SearchFilters | None,
    ) -> list[RetrievedChunk]: ...


class PgVectorStore(VectorStore):
    def __init__(self, settings: Settings, embedder: Embedder) -> None:
        self._settings = settings
        self._embedder = embedder
        self._pool: AsyncConnectionPool | None = None  # type: ignore[type-arg]

    async def setup(self) -> None:
        self._pool = AsyncConnectionPool(
            conninfo=str(self._settings.database_url),
            min_size=self._settings.pool_min_size,
            max_size=self._settings.pool_max_size,
            configure=register_vector_async,
            open=False,
        )
        await self._pool.open()

    async def aclose(self) -> None:
        if self._pool is not None:
            await self._pool.close()

    @property
    def _p(self) -> AsyncConnectionPool:  # type: ignore[type-arg]
        if self._pool is None:
            raise StoreError("setup() not called")
        return self._pool

    async def add_documents(self, docs: Sequence[Document]) -> list[int]:
        if not docs:
            return []
        batch_size = self._settings.embed_batch_size
        ids: list[int] = []
        for start in range(0, len(docs), batch_size):
            batch = docs[start : start + batch_size]
            embeddings = self._embedder.embed([d.page_content for d in batch])
            ids.extend(await self._insert_batch(batch, embeddings))
        return ids

    async def _insert_batch(
        self, batch: Sequence[Document], embeddings: NDArray[np.float32],
    ) -> list[int]:
        rows: list[int] = []
        try:
            async with self._p.connection() as conn:
                async with conn.transaction():
                    for doc, vec in zip(batch, embeddings, strict=True):
                        meta = doc.metadata
                        result = await conn.execute(
                            _INSERT_SQL,
                            (
                                meta["source_path"], meta["source_lang"],
                                meta["target_lang"], meta["media_type"],
                                meta.get("timestamp"), meta["confidence"],
                                meta["chunk_index"], doc.page_content, vec,
                            ),
                        )
                        row = await result.fetchone()
                        assert row is not None
                        rows.append(int(row[0]))
        except psycopg.Error as exc:
            raise StoreError(f"add_documents failed: {exc}") from exc
        return rows

    async def search_dense(
        self, query_embedding: NDArray[np.float32], top_k: int,
        filters: SearchFilters | None,
    ) -> list[RetrievedChunk]:
        where_sql, params = (filters or SearchFilters()).to_sql()
        sql = (
            f"SELECT {_SELECT_COLS}, 1 - (embedding <=> %s) AS score "
            f"FROM documents "
            f"WHERE embedding IS NOT NULL AND {where_sql} "
            f"ORDER BY embedding <=> %s LIMIT %s"
        )
        try:
            async with self._p.connection() as conn:
                await conn.execute(
                    "SET LOCAL hnsw.ef_search = %s",
                    (self._settings.hnsw_ef_search,),
                )
                cur = await conn.execute(
                    sql, [query_embedding, *params, query_embedding, top_k]
                )
                rows = await cur.fetchall()
        except psycopg.Error as exc:
            raise StoreError(f"search_dense failed: {exc}") from exc
        return [_row_to_chunk(row) for row in rows]

    async def search_lexical(
        self, query: str, top_k: int, filters: SearchFilters | None,
    ) -> list[RetrievedChunk]:
        where_sql, params = (filters or SearchFilters()).to_sql()
        sql = (
            f"SELECT {_SELECT_COLS}, "
            f"  ts_rank_cd(content_tsv, plainto_tsquery('simple', %s)) AS score "
            f"FROM documents "
            f"WHERE content_tsv @@ plainto_tsquery('simple', %s) AND {where_sql} "
            f"ORDER BY score DESC LIMIT %s"
        )
        try:
            async with self._p.connection() as conn:
                cur = await conn.execute(sql, [query, query, *params, top_k])
                rows = await cur.fetchall()
        except psycopg.Error as exc:
            raise StoreError(f"search_lexical failed: {exc}") from exc
        return [_row_to_chunk(row) for row in rows]


def _row_to_chunk(row: tuple[object, ...]) -> RetrievedChunk:
    return RetrievedChunk(
        id=int(row[0]), content=str(row[1]), source_path=str(row[2]),  # type: ignore[arg-type]
        source_lang=str(row[3]), target_lang=str(row[4]),
        media_type=str(row[5]),
        timestamp=None if row[6] is None else str(row[6]),
        chunk_index=int(row[7]), score=float(row[8]),  # type: ignore[arg-type]
    )

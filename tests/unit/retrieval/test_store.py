from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import psycopg
import pytest
from langchain_core.documents import Document

from polyglotpipe.retrieval.config import Settings
from polyglotpipe.retrieval.exceptions import StoreError
from polyglotpipe.retrieval.store import PgVectorStore, _row_to_chunk
from polyglotpipe.retrieval.types import SearchFilters


class _AsyncCM:
    """Minimal async context manager yielding a fixed value (mocks pool/transaction)."""

    def __init__(self, value: Any) -> None:
        self._value = value

    async def __aenter__(self) -> Any:
        return self._value

    async def __aexit__(self, *exc: object) -> bool:
        return False


def _settings() -> Settings:
    return Settings(database_url="postgresql://x:y@localhost/z")  # type: ignore[call-arg]


def _embedder() -> MagicMock:
    emb = MagicMock()
    emb.embed.return_value = np.ones((1, 384), dtype=np.float32)
    return emb


def _doc(path: str = "/a.pdf", content: str = "hello") -> Document:
    return Document(
        page_content=content,
        metadata={
            "source_path": path,
            "source_lang": "en",
            "target_lang": "en",
            "media_type": "pdf",
            "confidence": 0.9,
            "chunk_index": 0,
        },
    )


def _row(rid: int = 1, content: str = "hello", ts: str | None = None) -> tuple[Any, ...]:
    # Column order matches store._SELECT_COLS plus the trailing score column.
    return (rid, content, "/a.pdf", "en", "en", "pdf", ts, 0, 0.5)


def _store_with_pool(conn: MagicMock, embedder: MagicMock | None = None) -> PgVectorStore:
    store = PgVectorStore(_settings(), _embedder() if embedder is None else embedder)
    pool = MagicMock()
    pool.connection = MagicMock(return_value=_AsyncCM(conn))
    store._pool = pool
    return store


# --- guard / empty paths ---


async def test_search_lexical_without_setup_raises_store_error() -> None:
    store = PgVectorStore(_settings(), _embedder())
    with pytest.raises(StoreError, match="setup"):
        await store.search_lexical("q", top_k=5, filters=None)


async def test_add_documents_empty_returns_empty_list() -> None:
    store = PgVectorStore(_settings(), _embedder())
    assert await store.add_documents([]) == []


# --- add_documents ---


async def test_add_documents_inserts_and_returns_ids() -> None:
    conn = MagicMock()
    conn.transaction = MagicMock(return_value=_AsyncCM(None))
    result = MagicMock()
    result.fetchone = AsyncMock(return_value=(7,))
    conn.execute = AsyncMock(return_value=result)
    store = _store_with_pool(conn)

    ids = await store.add_documents([_doc()])

    assert ids == [7]
    conn.execute.assert_awaited_once()


async def test_add_documents_wraps_psycopg_error() -> None:
    conn = MagicMock()
    conn.transaction = MagicMock(return_value=_AsyncCM(None))
    conn.execute = AsyncMock(side_effect=psycopg.OperationalError("boom"))
    store = _store_with_pool(conn)

    with pytest.raises(StoreError, match="add_documents failed"):
        await store.add_documents([_doc()])


# --- search_dense ---


async def test_search_dense_sets_ef_and_maps_rows() -> None:
    conn = MagicMock()
    cur = MagicMock()
    cur.fetchall = AsyncMock(return_value=[_row(1), _row(2)])
    # First execute = "SET LOCAL ..." (return ignored), second = SELECT returning cursor.
    conn.execute = AsyncMock(side_effect=[MagicMock(), cur])
    store = _store_with_pool(conn)

    results = await store.search_dense(
        np.ones(384, dtype=np.float32), top_k=2, filters=SearchFilters(media_type="pdf")
    )

    assert [r.id for r in results] == [1, 2]
    assert conn.execute.await_count == 2


async def test_search_dense_wraps_psycopg_error() -> None:
    conn = MagicMock()
    conn.execute = AsyncMock(side_effect=psycopg.OperationalError("boom"))
    store = _store_with_pool(conn)

    with pytest.raises(StoreError, match="search_dense failed"):
        await store.search_dense(np.ones(384, dtype=np.float32), top_k=2, filters=None)


# --- search_lexical ---


async def test_search_lexical_maps_rows() -> None:
    conn = MagicMock()
    cur = MagicMock()
    cur.fetchall = AsyncMock(return_value=[_row(3, "revenue")])
    conn.execute = AsyncMock(return_value=cur)
    store = _store_with_pool(conn)

    results = await store.search_lexical("revenue", top_k=5, filters=None)

    assert [r.id for r in results] == [3]


async def test_search_lexical_wraps_psycopg_error() -> None:
    conn = MagicMock()
    conn.execute = AsyncMock(side_effect=psycopg.OperationalError("boom"))
    store = _store_with_pool(conn)

    with pytest.raises(StoreError, match="search_lexical failed"):
        await store.search_lexical("q", top_k=5, filters=None)


# --- _row_to_chunk ---


def test_row_to_chunk_maps_all_fields_with_timestamp() -> None:
    chunk = _row_to_chunk(_row(9, "body", ts="00:01:02"))
    assert (chunk.id, chunk.content, chunk.timestamp, chunk.score) == (9, "body", "00:01:02", 0.5)


def test_row_to_chunk_null_timestamp() -> None:
    assert _row_to_chunk(_row(9, "body", ts=None)).timestamp is None

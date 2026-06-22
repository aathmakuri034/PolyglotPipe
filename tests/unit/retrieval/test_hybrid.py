from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest

from polyglotpipe.retrieval.config import Settings
from polyglotpipe.retrieval.hybrid import HybridRetriever
from polyglotpipe.retrieval.types import RetrievedChunk

pytestmark = pytest.mark.asyncio


def _chunk(cid: int) -> RetrievedChunk:
    return RetrievedChunk(
        id=cid, content=f"c{cid}", source_path=f"/{cid}.pdf",
        source_lang="en", target_lang="en", media_type="pdf",
        chunk_index=0, score=0.0,
    )


def _settings() -> Settings:
    return Settings(database_url="postgresql://x:y@localhost/z")  # type: ignore[arg-type]


async def test_rrf_prefers_items_ranked_well_in_both_lists() -> None:
    store = MagicMock()
    store.search_dense = AsyncMock(return_value=[_chunk(1), _chunk(2), _chunk(3)])
    store.search_lexical = AsyncMock(return_value=[_chunk(2), _chunk(4), _chunk(1)])
    embedder = MagicMock()
    embedder.embed.return_value = np.zeros((1, 384), dtype=np.float32)

    retriever = HybridRetriever(store, embedder, _settings())
    results = await retriever.retrieve("q", top_k=4)

    # id=1 appears at rank 1 (dense) + rank 3 (lex) → highest fused score
    # id=2 appears at rank 2 (dense) + rank 1 (lex) → second
    assert [r.id for r in results[:2]] == [2, 1] or [r.id for r in results[:2]] == [1, 2]
    assert {r.id for r in results} == {1, 2, 3, 4}


async def test_only_dense_results_returns_dense_order() -> None:
    store = MagicMock()
    store.search_dense = AsyncMock(return_value=[_chunk(1), _chunk(2)])
    store.search_lexical = AsyncMock(return_value=[])
    embedder = MagicMock()
    embedder.embed.return_value = np.zeros((1, 384), dtype=np.float32)

    retriever = HybridRetriever(store, embedder, _settings())
    results = await retriever.retrieve("q", top_k=2)

    assert [r.id for r in results] == [1, 2]


async def test_empty_results() -> None:
    store = MagicMock()
    store.search_dense = AsyncMock(return_value=[])
    store.search_lexical = AsyncMock(return_value=[])
    embedder = MagicMock()
    embedder.embed.return_value = np.zeros((1, 384), dtype=np.float32)

    retriever = HybridRetriever(store, embedder, _settings())
    assert await retriever.retrieve("q") == []

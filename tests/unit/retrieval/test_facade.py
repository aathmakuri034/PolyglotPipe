from unittest.mock import AsyncMock, MagicMock

import pytest

from polyglotpipe.retrieval import Retriever
from polyglotpipe.retrieval.types import RetrievedChunk

pytestmark = pytest.mark.asyncio


def _chunk(cid: int) -> RetrievedChunk:
    return RetrievedChunk(
        id=cid,
        content=f"c{cid}",
        source_path=f"/{cid}.pdf",
        source_lang="en",
        target_lang="en",
        media_type="pdf",
        chunk_index=0,
        score=0.5,
    )


async def test_retrieve_without_reranker_truncates_to_top_k() -> None:
    hybrid = MagicMock()
    hybrid.retrieve = AsyncMock(return_value=[_chunk(1), _chunk(2), _chunk(3)])
    retriever = Retriever(hybrid, reranker=None)
    results = await retriever.retrieve("q", top_k=2)
    assert [r.id for r in results] == [1, 2]


async def test_retrieve_with_reranker_reorders() -> None:
    hybrid = MagicMock()
    hybrid.retrieve = AsyncMock(return_value=[_chunk(1), _chunk(2), _chunk(3)])
    reranker = MagicMock()
    reranker.rerank.return_value = [_chunk(3), _chunk(1)]
    retriever = Retriever(hybrid, reranker=reranker)
    results = await retriever.retrieve("q", top_k=2)
    assert [r.id for r in results] == [3, 1]
    reranker.rerank.assert_called_once_with("q", [_chunk(1), _chunk(2), _chunk(3)], top_k=2)


async def test_rerank_false_skips_reranker_even_if_present() -> None:
    hybrid = MagicMock()
    hybrid.retrieve = AsyncMock(return_value=[_chunk(1), _chunk(2)])
    reranker = MagicMock()
    retriever = Retriever(hybrid, reranker=reranker)
    await retriever.retrieve("q", top_k=2, rerank=False)
    reranker.rerank.assert_not_called()

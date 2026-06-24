from __future__ import annotations

import hashlib
import time

import structlog

from polyglotpipe.retrieval.config import Settings
from polyglotpipe.retrieval.embedder import Embedder
from polyglotpipe.retrieval.exceptions import (
    EmbeddingError,
    RerankerError,
    RetrievalError,
    StoreError,
)
from polyglotpipe.retrieval.hybrid import HybridRetriever
from polyglotpipe.retrieval.reranker import BgeReranker
from polyglotpipe.retrieval.store import PgVectorStore, VectorStore
from polyglotpipe.retrieval.types import RetrievedChunk, SearchFilters

__all__ = [
    "BgeReranker",
    "Embedder",
    "EmbeddingError",
    "HybridRetriever",
    "PgVectorStore",
    "RerankerError",
    "RetrievalError",
    "RetrievedChunk",
    "Retriever",
    "SearchFilters",
    "Settings",
    "StoreError",
    "VectorStore",
]

_log = structlog.get_logger(__name__)


class Retriever:
    """Facade: hybrid retrieve → rerank, with one structured log event per call."""

    def __init__(
        self,
        hybrid: HybridRetriever,
        reranker: BgeReranker | None = None,
    ) -> None:
        self._hybrid = hybrid
        self._reranker = reranker

    async def warmup(self) -> None:
        self._hybrid._embedder.warmup()
        if self._reranker is not None:
            self._reranker.warmup()

    async def retrieve(
        self,
        query: str,
        *,
        top_k: int = 5,
        filters: SearchFilters | None = None,
        rerank: bool = True,
    ) -> list[RetrievedChunk]:
        t0 = time.perf_counter()
        candidates = await self._hybrid.retrieve(query, filters=filters)
        t_hybrid = time.perf_counter()

        results = candidates[:top_k]
        if rerank and self._reranker is not None and candidates:
            results = self._reranker.rerank(query, candidates, top_k=top_k)
        t_end = time.perf_counter()

        _log.info(
            "retrieve.complete",
            query_hash=hashlib.sha256(query.encode()).hexdigest()[:12],
            hybrid_ms=round((t_hybrid - t0) * 1000, 2),
            rerank_ms=round((t_end - t_hybrid) * 1000, 2),
            n_candidates=len(candidates),
            n_returned=len(results),
            rerank=rerank and self._reranker is not None,
            filters=(filters.model_dump(exclude_none=True) if filters else {}),
        )
        return results

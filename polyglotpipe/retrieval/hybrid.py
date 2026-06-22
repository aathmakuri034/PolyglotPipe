from __future__ import annotations

import asyncio
from collections import defaultdict

from polyglotpipe.retrieval.config import Settings
from polyglotpipe.retrieval.embedder import Embedder
from polyglotpipe.retrieval.store import VectorStore
from polyglotpipe.retrieval.types import RetrievedChunk, SearchFilters


class HybridRetriever:
    """Parallel dense + lexical search fused via Reciprocal Rank Fusion."""

    def __init__(
        self,
        store: VectorStore,
        embedder: Embedder,
        settings: Settings,
    ) -> None:
        self._store = store
        self._embedder = embedder
        self._rrf_k = settings.rrf_k
        self._fusion_top_k = settings.fusion_top_k

    async def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        filters: SearchFilters | None = None,
    ) -> list[RetrievedChunk]:
        top_k = top_k or self._fusion_top_k
        query_vec = self._embedder.embed([query])[0]
        dense, lexical = await asyncio.gather(
            self._store.search_dense(query_vec, top_k, filters),
            self._store.search_lexical(query, top_k, filters),
        )
        return self._fuse(dense, lexical, top_k)

    def _fuse(
        self,
        dense: list[RetrievedChunk],
        lexical: list[RetrievedChunk],
        top_k: int,
    ) -> list[RetrievedChunk]:
        scores: dict[int, float] = defaultdict(float)
        chunks: dict[int, RetrievedChunk] = {}
        for ranking in (dense, lexical):
            for rank, chunk in enumerate(ranking, start=1):
                scores[chunk.id] += 1.0 / (self._rrf_k + rank)
                chunks.setdefault(chunk.id, chunk)
        ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:top_k]
        return [chunks[cid].model_copy(update={"score": score}) for cid, score in ordered]

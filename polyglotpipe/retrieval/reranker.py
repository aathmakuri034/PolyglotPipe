from __future__ import annotations

from typing import TYPE_CHECKING

from polyglotpipe.retrieval.config import Settings
from polyglotpipe.retrieval.exceptions import RerankerError
from polyglotpipe.retrieval.types import RetrievedChunk

if TYPE_CHECKING:
    from sentence_transformers import CrossEncoder


class BgeReranker:
    def __init__(self, settings: Settings, device: str = "cpu") -> None:
        self._model_name = settings.reranker_model
        self._batch_size = settings.rerank_batch_size
        self._device = device
        self._model: CrossEncoder | None = None

    def warmup(self) -> None:
        if self._model is None:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self._model_name, device=self._device)

    def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        if not chunks:
            return []
        self.warmup()
        assert self._model is not None
        pairs = [(query, c.content) for c in chunks]
        try:
            scores = self._model.predict(pairs, batch_size=self._batch_size)  # type: ignore[arg-type]
        except Exception as exc:
            raise RerankerError(f"rerank failed: {exc}") from exc
        ranked = sorted(zip(chunks, scores, strict=True), key=lambda x: x[1], reverse=True)
        return [c.model_copy(update={"score": float(s)}) for c, s in ranked[:top_k]]

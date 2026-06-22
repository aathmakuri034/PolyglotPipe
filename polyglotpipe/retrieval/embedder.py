from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from polyglotpipe.retrieval.config import Settings
from polyglotpipe.retrieval.exceptions import EmbeddingError

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


class Embedder:
    """Wraps a SentenceTransformer; lazy-loads on first use."""

    def __init__(self, settings: Settings) -> None:
        self._model_name = settings.embedding_model
        self._batch_size = settings.embed_batch_size
        self._model: SentenceTransformer | None = None

    def warmup(self) -> None:
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)

    def embed(self, texts: list[str]) -> NDArray[np.float32]:
        if not texts:
            return np.empty((0, 384), dtype=np.float32)
        self.warmup()
        assert self._model is not None
        try:
            vectors = self._model.encode(
                texts,
                batch_size=self._batch_size,
                normalize_embeddings=True,
                convert_to_numpy=True,
            )
        except Exception as exc:
            raise EmbeddingError(f"embed failed: {exc}") from exc
        return np.asarray(vectors, dtype=np.float32)

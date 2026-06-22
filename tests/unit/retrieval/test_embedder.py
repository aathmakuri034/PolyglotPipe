from unittest.mock import MagicMock

import numpy as np

from polyglotpipe.retrieval.config import Settings
from polyglotpipe.retrieval.embedder import Embedder


def _settings() -> Settings:
    return Settings(database_url="postgresql://x:y@localhost/z")  # type: ignore[arg-type]


def test_empty_input_returns_empty_array() -> None:
    embedder = Embedder(_settings())
    out = embedder.embed([])
    assert out.shape == (0, 384)
    assert out.dtype == np.float32


def test_embed_calls_model_and_returns_array(monkeypatch: object) -> None:
    embedder = Embedder(_settings())
    fake_model = MagicMock()
    fake_model.encode.return_value = np.ones((2, 384), dtype=np.float32)
    embedder._model = fake_model

    out = embedder.embed(["hello", "world"])

    fake_model.encode.assert_called_once()
    assert out.shape == (2, 384)
    kwargs = fake_model.encode.call_args.kwargs
    assert kwargs["normalize_embeddings"] is True
    assert kwargs["batch_size"] == 64

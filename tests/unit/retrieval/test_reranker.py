from unittest.mock import MagicMock

from polyglotpipe.retrieval.config import Settings
from polyglotpipe.retrieval.reranker import BgeReranker
from polyglotpipe.retrieval.types import RetrievedChunk


def _chunk(cid: int, content: str) -> RetrievedChunk:
    return RetrievedChunk(
        id=cid,
        content=content,
        source_path=f"/{cid}.pdf",
        source_lang="en",
        target_lang="en",
        media_type="pdf",
        chunk_index=0,
        score=0.0,
    )


def _settings() -> Settings:
    return Settings(database_url="postgresql://x:y@localhost/z")  # type: ignore[arg-type]


def test_empty_chunks_returns_empty() -> None:
    reranker = BgeReranker(_settings())
    assert reranker.rerank("q", [], top_k=5) == []


def test_rerank_reorders_by_model_score() -> None:
    reranker = BgeReranker(_settings())
    fake = MagicMock()
    fake.predict.return_value = [0.1, 0.9, 0.5]
    reranker._model = fake

    chunks = [_chunk(1, "a"), _chunk(2, "b"), _chunk(3, "c")]
    result = reranker.rerank("query", chunks, top_k=2)

    assert [r.id for r in result] == [2, 3]
    assert result[0].score == 0.9
    fake.predict.assert_called_once()
    assert fake.predict.call_args.kwargs["batch_size"] == 16

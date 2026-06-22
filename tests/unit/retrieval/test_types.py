import pytest
from pydantic import ValidationError

from polyglotpipe.retrieval.types import RetrievedChunk, SearchFilters


def _chunk(**overrides: object) -> RetrievedChunk:
    base = dict(
        id=1, content="hi", source_path="/a.pdf", source_lang="en",
        target_lang="en", media_type="pdf", chunk_index=0, score=0.5,
    )
    base.update(overrides)
    return RetrievedChunk(**base)  # type: ignore[arg-type]


def test_retrieved_chunk_is_frozen() -> None:
    chunk = _chunk()
    with pytest.raises(ValidationError):
        chunk.score = 0.9  # type: ignore[misc]


def test_search_filters_empty_returns_true() -> None:
    sql, params = SearchFilters().to_sql()
    assert sql == "TRUE"
    assert params == []


def test_search_filters_multiple() -> None:
    sql, params = SearchFilters(media_type="pdf", source_lang="de").to_sql()
    assert sql == "media_type = %s AND source_lang = %s"
    assert params == ["pdf", "de"]

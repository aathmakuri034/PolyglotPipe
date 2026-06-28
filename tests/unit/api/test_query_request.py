from __future__ import annotations

import pytest
from pydantic import ValidationError

from polyglotpipe.api.models import QueryFilters, QueryRequest


def test_minimal_query_uses_defaults() -> None:
    r = QueryRequest(query="how did Q3 revenue change?")
    assert r.target_lang == "en"
    assert r.top_k == 5
    assert r.rerank is True
    assert r.filters is None


def test_strips_and_rejects_whitespace_only() -> None:
    with pytest.raises(ValidationError):
        QueryRequest(query="   ")


def test_query_length_cap() -> None:
    QueryRequest(query="x" * 4000)
    with pytest.raises(ValidationError):
        QueryRequest(query="x" * 4001)


def test_top_k_lower_bound() -> None:
    with pytest.raises(ValidationError):
        QueryRequest(query="q", top_k=0)


def test_top_k_upper_bound() -> None:
    with pytest.raises(ValidationError):
        QueryRequest(query="q", top_k=51)


def test_filters_passes_through() -> None:
    r = QueryRequest(
        query="q",
        filters=QueryFilters(media_type="audio", source_lang="ja"),
    )
    assert r.filters is not None
    assert r.filters.media_type == "audio"
    assert r.filters.source_lang == "ja"


def test_filters_extra_forbidden() -> None:
    with pytest.raises(ValidationError):
        QueryFilters(media_type="audio", note="hello")  # type: ignore[call-arg]


def test_request_extra_forbidden() -> None:
    with pytest.raises(ValidationError):
        QueryRequest(query="q", debug=True)  # type: ignore[call-arg]


def test_frozen() -> None:
    r = QueryRequest(query="q")
    with pytest.raises(ValidationError):
        r.top_k = 10  # type: ignore[misc]


def test_target_lang_validated() -> None:
    QueryRequest(query="q", target_lang="zh-Hans")
    with pytest.raises(ValidationError):
        QueryRequest(query="q", target_lang="english")

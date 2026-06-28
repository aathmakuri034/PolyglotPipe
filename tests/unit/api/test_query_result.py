from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from polyglotpipe.api.models import (
    Citation,
    QueryLatency,
    QueryResult,
    QueryUsage,
)


def _citation(**overrides: Any) -> Citation:
    base: dict[str, Any] = dict(
        source_path="/data/a.pdf",
        source_lang="en",
        media_type="pdf",
        chunk_index=0,
        content="excerpt text",
        relevance_score=0.87,
    )
    base.update(overrides)
    return Citation(**base)


def _latency() -> QueryLatency:
    return QueryLatency(hybrid_ms=12.0, rerank_ms=80.0, generate_ms=300.0, total_ms=395.0)


def _usage() -> QueryUsage:
    return QueryUsage(prompt_tokens=200, completion_tokens=50, cost_usd=0.0001)


def _result(**overrides: Any) -> QueryResult:
    base: dict[str, Any] = dict(
        answer="Revenue grew 12 percent in Q3.",
        target_lang="en",
        citations=[_citation()],
        detected_source_langs=["en"],
        latency=_latency(),
        usage=_usage(),
        request_id="01HG2X9K7N",
    )
    base.update(overrides)
    return QueryResult(**base)


def test_citation_minimum_ok() -> None:
    c = _citation()
    assert c.timestamp is None


def test_citation_negative_chunk_index_rejected() -> None:
    with pytest.raises(ValidationError):
        _citation(chunk_index=-1)


def test_citation_empty_content_rejected() -> None:
    with pytest.raises(ValidationError):
        _citation(content="")


def test_citation_empty_source_path_rejected() -> None:
    with pytest.raises(ValidationError):
        _citation(source_path="")


def test_result_defaults_empty_lists() -> None:
    r = QueryResult(
        answer="ok",
        target_lang="en",
        latency=QueryLatency(hybrid_ms=0, rerank_ms=0, generate_ms=0, total_ms=0),
        usage=QueryUsage(prompt_tokens=0, completion_tokens=0),
        request_id="r1",
    )
    assert r.citations == []
    assert r.detected_source_langs == []
    assert r.usage.embed_tokens == 0
    assert r.usage.cost_usd == 0.0


def test_usage_rejects_negative_tokens() -> None:
    with pytest.raises(ValidationError):
        QueryUsage(prompt_tokens=-1, completion_tokens=0)


def test_latency_rejects_negative_ms() -> None:
    with pytest.raises(ValidationError):
        QueryLatency(hybrid_ms=-1.0, rerank_ms=0, generate_ms=0, total_ms=0)


def test_result_frozen() -> None:
    r = _result()
    with pytest.raises(ValidationError):
        r.answer = "..."  # type: ignore[misc]


def test_result_extra_forbidden() -> None:
    with pytest.raises(ValidationError):
        QueryResult(
            answer="x",
            target_lang="en",
            request_id="r",
            latency=_latency(),
            usage=_usage(),
            note="oops",  # type: ignore[call-arg]
        )


def test_request_id_length() -> None:
    with pytest.raises(ValidationError):
        _result(request_id="")
    with pytest.raises(ValidationError):
        _result(request_id="x" * 65)

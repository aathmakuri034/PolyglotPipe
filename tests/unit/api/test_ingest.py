from __future__ import annotations

import pytest
from pydantic import ValidationError

from polyglotpipe.api.models import (
    IngestRequest,
    IngestResponse,
    IngestStats,
    IngestStatus,
)


def test_request_defaults() -> None:
    r = IngestRequest(path="/data/media")
    assert r.target_lang == "en"
    assert r.recursive is True
    assert r.resume_id is None


def test_request_empty_path_rejected() -> None:
    with pytest.raises(ValidationError):
        IngestRequest(path="")


def test_request_invalid_target_lang_rejected() -> None:
    with pytest.raises(ValidationError):
        IngestRequest(path="/x", target_lang="english")


def test_status_enum_values() -> None:
    assert IngestStatus.SUCCEEDED.value == "succeeded"
    assert IngestStatus("queued") is IngestStatus.QUEUED


def test_stats_defaults_are_zero() -> None:
    s = IngestStats()
    assert s.audio == 0
    assert s.chunks_inserted == 0


def test_stats_no_negative_counts() -> None:
    with pytest.raises(ValidationError):
        IngestStats(pdf=-1)


def test_response_round_trip_via_dict() -> None:
    r = IngestResponse(
        run_id="run_01HG",
        status=IngestStatus.RUNNING,
        stats=IngestStats(pdf=3, chunks_inserted=42),
        started_at="2026-06-26T12:00:00Z",
    )
    assert IngestResponse.model_validate(r.model_dump()) == r


def test_response_frozen() -> None:
    r = IngestResponse(
        run_id="run_01",
        status=IngestStatus.SUCCEEDED,
        stats=IngestStats(),
        started_at="2026-06-26T12:00:00Z",
    )
    with pytest.raises(ValidationError):
        r.status = IngestStatus.FAILED  # type: ignore[misc]

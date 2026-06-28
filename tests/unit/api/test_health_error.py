from __future__ import annotations

import pytest
from pydantic import ValidationError

from polyglotpipe.api.models import (
    ComponentHealth,
    ErrorCode,
    ErrorResponse,
    HealthResponse,
)


def test_health_ok_with_components() -> None:
    h = HealthResponse(
        ok=True,
        version="0.0.1",
        components=[
            ComponentHealth(name="postgres", ok=True),
            ComponentHealth(name="gemini", ok=True, detail="15 RPM available"),
        ],
    )
    assert h.components[1].detail == "15 RPM available"


def test_health_empty_components_default() -> None:
    h = HealthResponse(ok=False, version="0.0.1")
    assert h.components == []


def test_health_blank_version_rejected() -> None:
    with pytest.raises(ValidationError):
        HealthResponse(ok=True, version="")


def test_error_codes_have_expected_values() -> None:
    assert ErrorCode.RATE_LIMITED.value == "rate_limited"
    assert ErrorCode("upstream_gemini") is ErrorCode.UPSTREAM_GEMINI


def test_error_message_required_non_empty() -> None:
    with pytest.raises(ValidationError):
        ErrorResponse(code=ErrorCode.INTERNAL, message="")


def test_error_details_optional() -> None:
    e = ErrorResponse(code=ErrorCode.VALIDATION, message="bad input")
    assert e.details is None
    assert e.request_id is None


def test_error_with_details_and_request_id() -> None:
    e = ErrorResponse(
        code=ErrorCode.UPSTREAM_GEMINI,
        message="429 from Gemini",
        details={"retry_after_s": 30},
        request_id="01HG2X9K7N",
    )
    assert e.details == {"retry_after_s": 30}


def test_error_request_id_length() -> None:
    with pytest.raises(ValidationError):
        ErrorResponse(code=ErrorCode.INTERNAL, message="boom", request_id="x" * 65)


def test_error_frozen() -> None:
    e = ErrorResponse(code=ErrorCode.INTERNAL, message="boom")
    with pytest.raises(ValidationError):
        e.message = "..."  # type: ignore[misc]

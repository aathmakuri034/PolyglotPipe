from __future__ import annotations

import pytest
from langchain_core.documents import Document
from pydantic import ValidationError

from polyglotpipe.api.models import DocumentMetadata


def _valid(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = dict(
        source_path="/data/a.pdf",
        source_lang="en",
        target_lang="en",
        media_type="pdf",
        confidence=0.9,
        chunk_index=0,
    )
    base.update(overrides)
    return base


def test_minimal_valid_payload() -> None:
    md = DocumentMetadata(**_valid())  # type: ignore[arg-type]
    assert md.timestamp is None
    assert md.media_type == "pdf"


def test_frozen() -> None:
    md = DocumentMetadata(**_valid())  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        md.confidence = 0.5  # type: ignore[misc]


def test_extra_field_forbidden() -> None:
    with pytest.raises(ValidationError):
        DocumentMetadata(**_valid(unknown_key="x"))  # type: ignore[arg-type]


def test_invalid_media_type() -> None:
    with pytest.raises(ValidationError):
        DocumentMetadata(**_valid(media_type="video"))  # type: ignore[arg-type]


def test_negative_chunk_index() -> None:
    with pytest.raises(ValidationError):
        DocumentMetadata(**_valid(chunk_index=-1))  # type: ignore[arg-type]


def test_confidence_out_of_range() -> None:
    with pytest.raises(ValidationError):
        DocumentMetadata(**_valid(confidence=1.1))  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        DocumentMetadata(**_valid(confidence=-0.01))  # type: ignore[arg-type]


def test_lang_code_accepts_simple_and_compound() -> None:
    DocumentMetadata(**_valid(source_lang="en", target_lang="zh-Hans"))  # type: ignore[arg-type]
    DocumentMetadata(**_valid(source_lang="pt-BR"))  # type: ignore[arg-type]


def test_lang_code_rejects_uppercase_primary() -> None:
    with pytest.raises(ValidationError):
        DocumentMetadata(**_valid(source_lang="EN"))  # type: ignore[arg-type]


def test_lang_code_rejects_garbage() -> None:
    with pytest.raises(ValidationError):
        DocumentMetadata(**_valid(target_lang="not a lang"))  # type: ignore[arg-type]


def test_empty_source_path_rejected() -> None:
    with pytest.raises(ValidationError):
        DocumentMetadata(**_valid(source_path=""))  # type: ignore[arg-type]


def test_timestamp_max_length() -> None:
    with pytest.raises(ValidationError):
        DocumentMetadata(**_valid(timestamp="x" * 33))  # type: ignore[arg-type]


def test_round_trip_through_langchain_document() -> None:
    md = DocumentMetadata(**_valid(timestamp="00:01:23.450", media_type="audio"))  # type: ignore[arg-type]
    doc = Document(page_content="hello", metadata=md.model_dump())
    parsed = DocumentMetadata(**doc.metadata)
    assert parsed == md

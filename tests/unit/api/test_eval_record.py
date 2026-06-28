from __future__ import annotations

import json
from typing import Any

import pytest
from pydantic import ValidationError

from polyglotpipe.api.models import EvalRecord


def _record(**overrides: Any) -> EvalRecord:
    base: dict[str, Any] = dict(
        question="What was Q3 revenue growth?",
        ground_truth="12 percent",
        contexts=["Revenue grew 12 percent in Q3 according to the filing."],
        source_lang="en",
        target_lang="en",
        media_type="pdf",
        source_path="/eval/q3.pdf",
        dataset_id="compliance-en-v1",
    )
    base.update(overrides)
    return EvalRecord(**base)


def test_minimal_record_ok() -> None:
    r = _record()
    assert r.answer is None


def test_contexts_must_be_non_empty_list() -> None:
    with pytest.raises(ValidationError):
        _record(contexts=[])


def test_contexts_individual_items_non_empty() -> None:
    with pytest.raises(ValidationError):
        _record(contexts=[""])


def test_question_strip_and_min_length() -> None:
    with pytest.raises(ValidationError):
        _record(question="   ")


def test_dataset_id_max_length() -> None:
    with pytest.raises(ValidationError):
        _record(dataset_id="x" * 65)


def test_jsonl_round_trip_no_newline() -> None:
    r = _record(answer="Twelve percent.")
    line = r.to_jsonl()
    assert "\n" not in line
    assert json.loads(line)["question"] == r.question
    assert EvalRecord.from_jsonl(line) == r


def test_jsonl_round_trip_unicode() -> None:
    r = _record(
        question="Wie war das Umsatzwachstum in Q3?",
        ground_truth="zwölf Prozent",
        source_lang="de",
    )
    assert EvalRecord.from_jsonl(r.to_jsonl()) == r


def test_extra_forbidden() -> None:
    with pytest.raises(ValidationError):
        _record(notes="oops")


def test_frozen() -> None:
    r = _record()
    with pytest.raises(ValidationError):
        r.answer = "x"  # type: ignore[misc]

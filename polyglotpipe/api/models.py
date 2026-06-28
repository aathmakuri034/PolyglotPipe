from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

# --- Shared primitives ---------------------------------------------------

MediaType = Literal["audio", "pdf", "image", "text"]
"""Allowed media types. Mirrors the CHECK constraint on
``documents.media_type`` in ``polyglotpipe/retrieval/schema.sql``.
"""

LangCode = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=2,
        max_length=12,
        pattern=r"^[a-z]{2,3}(-[A-Z][a-z]{3})?(-[A-Z]{2})?$",
    ),
]
"""BCP 47 language tag. Primary subtag is ISO 639-1 (2-letter, lowercase)
or ISO 639-2 (3-letter); optional script (e.g. ``Hans``) and region
(e.g. ``DE``) subtags. Examples: ``en``, ``de``, ``zh-Hans``, ``pt-BR``."""


# --- Locked contract #1: Document metadata -------------------------------


class DocumentMetadata(BaseModel):
    """Schema for the ``metadata`` dict on every
    ``langchain_core.documents.Document`` flowing through the pipeline.

    Mirrors the columns of ``polyglotpipe.retrieval.schema.documents`` so
    that ``DocumentMetadata(...).model_dump()`` can be handed straight to
    ``PgVectorStore.add_documents`` without an adapter layer.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    source_path: Annotated[str, StringConstraints(min_length=1)] = Field(
        ...,
        description="Absolute or repo-relative path to the original media file.",
    )
    source_lang: LangCode = Field(
        ...,
        description="Detected language of the source content.",
    )
    target_lang: LangCode = Field(
        ...,
        description=(
            "Language the content was (or will be) translated into. "
            "Equal to ``source_lang`` if no translation step ran."
        ),
    )
    media_type: MediaType = Field(
        ...,
        description="Original media type of the source file.",
    )
    timestamp: str | None = Field(
        default=None,
        max_length=32,
        description=(
            "Provenance pointer inside the source — e.g. ``00:01:23.450`` for "
            "audio/video, ``p12`` for pdf pages. ``None`` for image/text."
        ),
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "Pipeline confidence in this chunk on [0,1] "
            "(e.g. Whisper avg_logprob rescaled, OCR mean conf)."
        ),
    )
    chunk_index: int = Field(
        ...,
        ge=0,
        description="0-based index of this chunk within ``source_path``.",
    )

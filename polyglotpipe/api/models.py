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


# --- Locked contract #2a: QueryRequest -----------------------------------


class QueryFilters(BaseModel):
    """Optional narrowing of the corpus before retrieval. All set fields
    are combined with AND. Mirrors ``polyglotpipe.retrieval.SearchFilters``
    but lives in the public API layer so the retrieval module stays an
    implementation detail."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    media_type: MediaType | None = None
    source_lang: LangCode | None = None
    source_path: Annotated[str, StringConstraints(min_length=1)] | None = None


class QueryRequest(BaseModel):
    """Body of ``POST /query`` and the input to ``graph.pipeline.run``.

    The query string may be in any of the 15+ supported languages; the
    answer is generated in ``target_lang`` (defaults to English).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    query: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=4000),
    ] = Field(..., description="User question; may be in any supported language.")
    target_lang: LangCode = Field(
        default="en",
        description="Language of the generated answer.",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Number of citations to return.",
    )
    rerank: bool = Field(
        default=True,
        description="If True, apply the BGE cross-encoder reranker after RRF fusion.",
    )
    filters: QueryFilters | None = None


# --- Locked contract #2b: QueryResult ------------------------------------


class Citation(BaseModel):
    """One retrieved chunk surfaced to the caller for citation grounding."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    source_path: Annotated[str, StringConstraints(min_length=1)]
    source_lang: LangCode
    media_type: MediaType
    chunk_index: int = Field(..., ge=0)
    timestamp: str | None = Field(default=None, max_length=32)
    content: Annotated[str, StringConstraints(min_length=1)] = Field(
        ...,
        description="The cited text, post-translation if applicable.",
    )
    relevance_score: float = Field(
        ...,
        description="Final score from rerank (BGE) or RRF fusion if rerank=False.",
    )


class QueryLatency(BaseModel):
    """Per-query latency breakdown in milliseconds. Mirrors the fields of
    the structlog ``retrieve.complete`` event emitted by ``Retriever``."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    hybrid_ms: float = Field(..., ge=0.0)
    rerank_ms: float = Field(..., ge=0.0)
    generate_ms: float = Field(..., ge=0.0)
    total_ms: float = Field(..., ge=0.0)


class QueryUsage(BaseModel):
    """Per-query resource usage. Feeds ``observability.cost_tracker`` and
    Prometheus metrics."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    prompt_tokens: int = Field(..., ge=0)
    completion_tokens: int = Field(..., ge=0)
    embed_tokens: int = Field(default=0, ge=0)
    cost_usd: float = Field(default=0.0, ge=0.0)


class QueryResult(BaseModel):
    """Body of ``POST /query`` response."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    answer: Annotated[str, StringConstraints(min_length=0)] = Field(
        ...,
        description=(
            "Generated answer in ``target_lang``. May be empty when no citations were found."
        ),
    )
    target_lang: LangCode
    citations: list[Citation] = Field(default_factory=list)
    detected_source_langs: list[LangCode] = Field(
        default_factory=list,
        description="Distinct ``source_lang`` values across the citations.",
    )
    latency: QueryLatency
    usage: QueryUsage
    request_id: Annotated[str, StringConstraints(min_length=1, max_length=64)] = Field(
        ...,
        description="Opaque trace id (e.g. ULID) for log correlation.",
    )


# --- Locked contract #3: Eval-dataset JSONL ------------------------------


class EvalRecord(BaseModel):
    """One row of the eval JSONL dataset consumed by ``eval/harness.py``.

    The field layout mirrors RAGAS's expected dataframe columns
    (``question``, ``ground_truth``, ``contexts``, ``answer``) plus the
    language and provenance fields needed for the cross-lingual chrF++
    translation-quality benchmark and per-slice reporting.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    question: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=4000),
    ]
    ground_truth: Annotated[str, StringConstraints(min_length=1)]
    contexts: list[Annotated[str, StringConstraints(min_length=1)]] = Field(
        ...,
        min_length=1,
        description="Gold context passages used to compute context_precision.",
    )
    answer: str | None = Field(
        default=None,
        description=(
            "Optional generated answer captured during a previous run "
            "(used for replay / regression diffs)."
        ),
    )
    source_lang: LangCode
    target_lang: LangCode
    media_type: MediaType
    source_path: Annotated[str, StringConstraints(min_length=1)]
    dataset_id: Annotated[str, StringConstraints(min_length=1, max_length=64)] = Field(
        ...,
        description="Identifies the eval slice (e.g. ``compliance-de-v1``).",
    )

    def to_jsonl(self) -> str:
        """Serialize to a single JSON line (no trailing newline)."""
        return self.model_dump_json()

    @classmethod
    def from_jsonl(cls, line: str) -> EvalRecord:
        """Parse a single JSONL line."""
        return cls.model_validate_json(line)

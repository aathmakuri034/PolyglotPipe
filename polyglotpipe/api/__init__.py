"""Public API contracts shared between Engineer A (chains/graph/providers)
and Engineer B (retrieval/api/eval/observability).

See docs/plans/api-models.md for the design and Contributions.md for the
approval rules around shared files.
"""

from polyglotpipe.api.models import (
    Citation,
    ComponentHealth,
    DocumentMetadata,
    ErrorCode,
    ErrorResponse,
    EvalRecord,
    HealthResponse,
    IngestRequest,
    IngestResponse,
    IngestStats,
    IngestStatus,
    LangCode,
    MediaType,
    QueryFilters,
    QueryLatency,
    QueryRequest,
    QueryResult,
    QueryUsage,
)

__all__ = [
    "Citation",
    "ComponentHealth",
    "DocumentMetadata",
    "ErrorCode",
    "ErrorResponse",
    "EvalRecord",
    "HealthResponse",
    "IngestRequest",
    "IngestResponse",
    "IngestStats",
    "IngestStatus",
    "LangCode",
    "MediaType",
    "QueryFilters",
    "QueryLatency",
    "QueryRequest",
    "QueryResult",
    "QueryUsage",
]

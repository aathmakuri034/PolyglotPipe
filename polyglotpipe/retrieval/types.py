from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field  # noqa: F401


class RetrievedChunk(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: int
    content: str
    source_path: str
    source_lang: str
    target_lang: str
    media_type: str
    timestamp: str | None = None
    chunk_index: int
    score: float


class SearchFilters(BaseModel):
    media_type: str | None = None
    source_lang: str | None = None
    target_lang: str | None = None
    source_path: str | None = None

    def to_sql(self) -> tuple[str, list[object]]:
        clauses: list[str] = []
        params: list[object] = []
        for column in ("media_type", "source_lang", "target_lang", "source_path"):
            value = getattr(self, column)
            if value is not None:
                clauses.append(f"{column} = %s")
                params.append(value)
        sql = " AND ".join(clauses) if clauses else "TRUE"
        return sql, params

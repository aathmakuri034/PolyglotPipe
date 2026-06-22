from __future__ import annotations

import os
from collections.abc import AsyncIterator
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import psycopg
import pytest
import pytest_asyncio

from polyglotpipe.retrieval.config import Settings
from polyglotpipe.retrieval.embedder import Embedder
from polyglotpipe.retrieval.store import SCHEMA_PATH, PgVectorStore


def _require_dsn() -> str:
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        pytest.skip("DATABASE_URL not set — skipping integration tests")
    return dsn


@pytest.fixture(scope="session")
def pg_dsn() -> str:
    dsn = _require_dsn()
    # Apply schema once per session (all statements are idempotent IF NOT EXISTS).
    with psycopg.connect(dsn) as conn:
        conn.execute(Path(SCHEMA_PATH).read_text())
        conn.commit()
    return dsn


@pytest_asyncio.fixture
async def store(pg_dsn: str, monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[PgVectorStore]:
    # Truncate between tests so each one starts with a clean documents table.
    with psycopg.connect(pg_dsn) as conn:
        conn.execute("TRUNCATE TABLE documents RESTART IDENTITY CASCADE")
        conn.commit()

    monkeypatch.setenv("DATABASE_URL", pg_dsn)
    settings = Settings()  # type: ignore[call-arg]

    embedder = Embedder(settings)
    fake = MagicMock()
    fake.encode.side_effect = lambda texts, **_: np.tile(
        np.linspace(0, 1, 384, dtype=np.float32), (len(texts), 1)
    )
    embedder._model = fake

    s = PgVectorStore(settings, embedder)
    await s.setup()
    yield s
    await s.aclose()

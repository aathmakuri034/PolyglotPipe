from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest
import pytest_asyncio
from testcontainers.postgres import PostgresContainer

from polyglotpipe.retrieval.config import Settings
from polyglotpipe.retrieval.embedder import Embedder
from polyglotpipe.retrieval.store import SCHEMA_PATH, PgVectorStore

PGVECTOR_IMAGE = "pgvector/pgvector:pg16"


@pytest.fixture(scope="session")
def pg_dsn() -> AsyncIterator[str]:
    with PostgresContainer(PGVECTOR_IMAGE) as pg:
        yield pg.get_connection_url().replace("postgresql+psycopg2", "postgresql")


@pytest_asyncio.fixture
async def store(pg_dsn: str, monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[PgVectorStore]:
    import psycopg
    with psycopg.connect(pg_dsn) as conn:
        conn.execute(Path(SCHEMA_PATH).read_text())
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

"""Apply retrieval schema to the database pointed to by DATABASE_URL."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "polyglotpipe" / "retrieval" / "schema.sql"
MIN_PGVECTOR = (0, 5, 0)


def _check_pgvector_version(conn: psycopg.Connection[tuple[str, ...]]) -> None:
    row = conn.execute(
        "SELECT extversion FROM pg_extension WHERE extname = 'vector'"
    ).fetchone()
    if row is None:
        return  # extension created below; version checked next run
    version = tuple(int(p) for p in row[0].split("."))
    if version < MIN_PGVECTOR:
        raise SystemExit(f"pgvector >= {MIN_PGVECTOR} required, found {version}")


def main() -> None:
    load_dotenv()
    dsn = os.environ["DATABASE_URL"]
    sql = SCHEMA_PATH.read_text()
    with psycopg.connect(dsn) as conn:
        _check_pgvector_version(conn)
        conn.execute(sql)
        conn.commit()
        _check_pgvector_version(conn)
    print("schema applied", file=sys.stderr)


if __name__ == "__main__":
    main()

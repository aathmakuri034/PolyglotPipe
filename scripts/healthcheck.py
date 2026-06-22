"""Verify dev environment: DB reachable, pgvector installed, schema present."""
from __future__ import annotations

import os
import sys

import psycopg
from dotenv import load_dotenv


def main() -> None:
    load_dotenv()
    dsn = os.environ["DATABASE_URL"]
    with psycopg.connect(dsn) as conn:
        ext = conn.execute(
            "SELECT extversion FROM pg_extension WHERE extname = 'vector'"
        ).fetchone()
        if ext is None:
            raise SystemExit("pgvector extension not installed")
        tbl = conn.execute(
            "SELECT to_regclass('public.documents')"
        ).fetchone()
        if tbl is None or tbl[0] is None:
            raise SystemExit("documents table missing; run scripts/init_db.py")
    print(f"ok: pgvector={ext[0]}, documents table present", file=sys.stderr)


if __name__ == "__main__":
    main()

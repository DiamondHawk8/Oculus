"""

Supports:
    SQLite (default – zero-config, file-based)
    PostgreSQL (when `backend="postgres"` or env var DB_BACKEND = "postgres")

env vars are postgres only:
----------------------
DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
"""
from __future__ import annotations

import os
import sqlite3
import logging
from typing import Sequence, Tuple, Optional

try:
    import psycopg2
except ModuleNotFoundError:
    psycopg2 = None

logger = logging.getLogger(__name__)


def get_db_connection(*, db_path: Optional[str | os.PathLike] = None, backend: Optional[str] = None, ) \
        -> "sqlite3.Connection | psycopg2.extensions.connection":
    """
    If backend is None, fall back to DB_BACKEND env-var or sqlite.
    """
    backend = backend or os.getenv("DB_BACKEND", "sqlite").lower()

    if backend == "postgres":
        if psycopg2 is None:
            raise RuntimeError("psycopg2 not installed; cannot use PostgreSQL")

        logger.info("Connecting to PostgreSQL…")
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "oculus_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "secret"),
        )
        conn.autocommit = False
        return conn

    # ---- SQLite (default) ----
    logger.info("Connecting to SQLite…")
    sqlite_path = str(db_path or "oculus.db")
    conn = sqlite3.connect(sqlite_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def generate_insert_sql(
        table: str,
        columns: Sequence[str],
        values: Sequence,
        *,
        backend: str = "sqlite",
) -> Tuple[str, Tuple]:
    """
    Produce an INSERT … VALUES statement + param tuple for either backend.
    """
    if not table or not columns or len(columns) != len(values):
        raise ValueError("table, columns, and values must be non-empty & aligned")

    cols = f"({', '.join(columns)})"
    placeholder = "%s" if backend == "postgres" else "?"
    placeholders = ", ".join([placeholder] * len(values))
    sql = f"INSERT INTO {table} {cols} VALUES ({placeholders});"
    return sql, tuple(values)

from __future__ import annotations

import logging
import os
import sqlite3
from typing import Optional, Sequence, Tuple

from infrastructure.sqlite.schema import SCHEMA_VERSION, ensure_schema

try:
    import psycopg2
except ModuleNotFoundError:
    psycopg2 = None

logger = logging.getLogger(__name__)

__all__ = ["SCHEMA_VERSION", "ensure_schema", "get_db_connection", "generate_insert_sql"]

def get_db_connection(
        *,
        db_path: Optional[str | os.PathLike] = None,
        backend: Optional[str] = None,
        initialize_schema: bool = True,
) -> "sqlite3.Connection | psycopg2.extensions.connection":
    """Open the selected backend, defaulting to SQLite."""
    backend = backend or os.getenv("DB_BACKEND", "sqlite").lower()

    if backend == "postgres":
        if psycopg2 is None:
            logger.error("psycopg2 not installed; cannot use PostgreSQL")
            raise RuntimeError("psycopg2 not installed; cannot use PostgreSQL")

        logger.info("Connecting to PostgreSQL...")
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "oculus_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "secret"),
        )
        conn.autocommit = False

        # TODO, make schema creation postgres compatible
        # PostgreSQL remains experimental; its schema needs a separate dialect.
        return conn

    logger.info("Connecting to SQLite")
    sqlite_path = str(db_path or "oculus.db")
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        if initialize_schema:
            # Startup creates fresh catalogs and validates existing ones only
            ensure_schema(conn)
    except BaseException:
        conn.close()
        raise
    return conn


def generate_insert_sql(
        table: str,
        columns: Sequence[str],
        values: Sequence,
        *,
        backend: str = "sqlite",
) -> Tuple[str, Tuple]:
    """Produce an INSERT statement and parameter tuple for either backend."""
    logger.debug("Generating insert sql for %s", table)
    if not table or not columns or len(columns) != len(values):
        raise ValueError("table, columns, and values must be non-empty & aligned")

    cols = f"({', '.join(columns)})"
    placeholder = "%s" if backend == "postgres" else "?"
    placeholders = ", ".join([placeholder] * len(values))
    sql = f"INSERT INTO {table} {cols} VALUES ({placeholders});"
    return sql, tuple(values)

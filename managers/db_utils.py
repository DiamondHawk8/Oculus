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


def _ensure_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    # check does media exist
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='media';")
    if cur.fetchone():
        logger.debug("Schema exists")
        return

    # Otherwise, create the schema
    logger.debug("No media entries found, creating schema")
    cur.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE media (
            id     INTEGER PRIMARY KEY,
            path   TEXT UNIQUE,
            added  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_dir BOOLEAN DEFAULT 0,
            byte_size INTEGER DEFAULT 0
        );

        CREATE TABLE variants (
            base_id    INTEGER,
            variant_id INTEGER UNIQUE,
            rank       INTEGER DEFAULT 0,
            FOREIGN KEY(base_id)    REFERENCES media(id) ON DELETE CASCADE,
            FOREIGN KEY(variant_id) REFERENCES media(id) ON DELETE CASCADE
        );

        CREATE TABLE presets (
            id        INTEGER PRIMARY KEY,
            media_id  INTEGER,
            name      TEXT,
            zoom      REAL,
            pan_x     INTEGER,
            pan_y     INTEGER,
            FOREIGN KEY(media_id) REFERENCES media(id) ON DELETE CASCADE
        );

        CREATE TABLE attributes (
            media_id  INTEGER PRIMARY KEY,
            favorite  BOOLEAN DEFAULT 0,
            weight    REAL    DEFAULT 1.0,
            FOREIGN KEY(media_id) REFERENCES media(id) ON DELETE CASCADE
        );

        CREATE TABLE tags (
            media_id  INTEGER,
            tag       TEXT,
            FOREIGN KEY(media_id) REFERENCES media(id) ON DELETE CASCADE,
            UNIQUE(media_id, tag)
        );

        CREATE INDEX idx_tags_tag ON tags(tag);
        """
    )
    conn.commit()


def get_db_connection(*, db_path: Optional[str | os.PathLike] = None, backend: Optional[str] = None, ) \
        -> "sqlite3.Connection | psycopg2.extensions.connection":
    """
    If backend is None, fall back to DB_BACKEND env-var or sqlite.
    """
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
        # _ensure_schema(conn)
        return conn

    # ---- SQLite (default) ----
    logger.info("Connecting to SQLite")
    sqlite_path = str(db_path or "oculus.db")
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    _ensure_schema(conn)
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
    logger.debug(f"Generating insert sql for {table}")
    logger.debug(f"Args:\n Columns: {columns}\nValues: {values}\nBackend: {backend}")
    if not table or not columns or len(columns) != len(values):
        logger.error("Columns and values must have the same length")
        raise ValueError("table, columns, and values must be non-empty & aligned")

    cols = f"({', '.join(columns)})"
    placeholder = "%s" if backend == "postgres" else "?"
    placeholders = ", ".join([placeholder] * len(values))
    sql = f"INSERT INTO {table} {cols} VALUES ({placeholders});"
    return sql, tuple(values)

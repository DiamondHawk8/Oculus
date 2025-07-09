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
    """
    Create the base schema on a brand-new DB, or upgrade an
    existing DB by adding any missing tables / indexes.
    """
    cur = conn.cursor()

    # Does the core 'media' table exist?
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='media';")
    media_exists = bool(cur.fetchone())

    if not media_exists:
        logger.debug("Fresh database – creating core schema")
        cur.executescript(
            """
            PRAGMA foreign_keys = ON;

            CREATE TABLE media (
                id        INTEGER PRIMARY KEY,
                path      TEXT UNIQUE,
                added     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_dir    BOOLEAN DEFAULT 0,
                byte_size INTEGER DEFAULT 0,
                favorite  INTEGER NOT NULL DEFAULT 0,
                weight    REAL,
                artist    TEXT,
                type      TEXT    NOT NULL
                            
            );

            CREATE TABLE IF NOT EXISTS presets (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id    TEXT    NOT NULL,          -- same for all copies of one preset
                name        TEXT    NOT NULL,
                media_id    INTEGER,                   -- NULL = folder default
                zoom        REAL    NOT NULL,
                pan_x       INTEGER NOT NULL,
                pan_y       INTEGER NOT NULL,
                is_default  INTEGER NOT NULL DEFAULT 0,
                hotkey      TEXT,                      -- e.g. "Ctrl+2"
            
                FOREIGN KEY (media_id) REFERENCES media(id) ON DELETE CASCADE,
                UNIQUE (media_id, name),               -- keep names unique per image
                CHECK (is_default IN (0,1))
            );
            CREATE INDEX IF NOT EXISTS idx_presets_group ON presets(group_id);

            CREATE TABLE tags (
                media_id  INTEGER,
                tag       TEXT,
                FOREIGN KEY(media_id) REFERENCES media(id) ON DELETE CASCADE,
                UNIQUE(media_id, tag)
            );

            CREATE INDEX idx_tags_tag ON tags(tag);
            
            CREATE TABLE comments (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                media_id  INTEGER NOT NULL,
                created   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                text      TEXT NOT NULL,
                FOREIGN KEY (media_id) REFERENCES media(id) ON DELETE CASCADE
            );
            
            CREATE INDEX IF NOT EXISTS idx_comments_media ON comments(media_id);
            """

        )
        conn.commit()
        logger.debug("Core schema created")

    # ALWAYS ensure variants table/indexes exist (upgrade path)
    ensure_variants_schema(conn)
    logger.debug("Schema verified / upgraded")


def ensure_variants_schema(conn) -> None:
    cur = conn.cursor()

    # main table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS variants (
            base_id     INTEGER NOT NULL,
            variant_id  INTEGER NOT NULL UNIQUE,
            rank        INTEGER DEFAULT 0,
            FOREIGN KEY(base_id)    REFERENCES media(id)  ON DELETE CASCADE,
            FOREIGN KEY(variant_id) REFERENCES media(id)  ON DELETE CASCADE
        )
    """)

    # lookup indexes
    cur.execute("CREATE INDEX IF NOT EXISTS idx_variants_base  ON variants(base_id)")
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_variants_rank ON variants(base_id, rank)")

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

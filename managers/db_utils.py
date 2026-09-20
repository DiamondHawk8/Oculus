from __future__ import annotations

import logging
import os
import sqlite3
from typing import Optional, Sequence, Tuple

try:
    import psycopg2
except ModuleNotFoundError:
    psycopg2 = None

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 3

# ALTER TABLE accepts only one column at a time. Keeping the definitions here
_MEDIA_COLUMNS = {
    "added": "TIMESTAMP",
    "is_dir": "BOOLEAN DEFAULT 0",
    "byte_size": "INTEGER DEFAULT 0",
    "favorite": "INTEGER NOT NULL DEFAULT 0",
    "weight": "REAL",
    "artist": "TEXT",
    "type": "TEXT NOT NULL DEFAULT 'image'",
    "device": "TEXT",
    "inode": "TEXT",
    "mtime": "INTEGER",
}


def ensure_schema(conn: sqlite3.Connection) -> None:
    """Create a fresh schema or repair an older, partially upgraded schema."""
    cur = conn.cursor()

    # These statements run on every connection intentionally, IF NOT EXISTS prevents overhead
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS media (
            id        INTEGER PRIMARY KEY,
            path      TEXT UNIQUE,
            added     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_dir    BOOLEAN DEFAULT 0,
            byte_size INTEGER DEFAULT 0,
            favorite  INTEGER NOT NULL DEFAULT 0,
            weight    REAL,
            artist    TEXT,
            type      TEXT NOT NULL,
            device    TEXT,
            inode     TEXT,
            mtime     INTEGER
        );

        CREATE TABLE IF NOT EXISTS presets (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id    TEXT NOT NULL,
            name        TEXT NOT NULL,
            media_id    INTEGER,
            zoom        REAL NOT NULL,
            pan_x       INTEGER NOT NULL,
            pan_y       INTEGER NOT NULL,
            is_default  INTEGER NOT NULL DEFAULT 0,
            hotkey      TEXT,
            FOREIGN KEY (media_id) REFERENCES media(id) ON DELETE CASCADE,
            UNIQUE (media_id, name),
            CHECK (is_default IN (0,1))
        );

        CREATE TABLE IF NOT EXISTS tags (
            media_id INTEGER,
            tag      TEXT,
            FOREIGN KEY(media_id) REFERENCES media(id) ON DELETE CASCADE,
            UNIQUE(media_id, tag)
        );

        CREATE TABLE IF NOT EXISTS comments (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            media_id INTEGER NOT NULL,
            created  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            text     TEXT NOT NULL,
            seq      INTEGER,
            FOREIGN KEY (media_id) REFERENCES media(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS bookmarks (
            path    TEXT NOT NULL,
            time_ms INTEGER NOT NULL,
            PRIMARY KEY (path, time_ms)
        );

        CREATE INDEX IF NOT EXISTS idx_presets_group ON presets(group_id);
        CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag);
        CREATE INDEX IF NOT EXISTS idx_comments_media ON comments(media_id);
        """
    )

    existing_columns = {
        row["name"] if isinstance(row, sqlite3.Row) else row[1]
        for row in cur.execute("PRAGMA table_info(media)")
    }
    for name, definition in _MEDIA_COLUMNS.items():
        if name not in existing_columns:
            logger.info("Adding missing media.%s column", name)
            cur.execute(f"ALTER TABLE media ADD COLUMN {name} {definition}")

    ensure_variants_schema(conn, commit=False)
    cur.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    conn.commit()
    logger.debug("Schema verified at version %d", SCHEMA_VERSION)


def ensure_variants_schema(conn, *, commit: bool = True) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS variants (
            base_id     INTEGER NOT NULL,
            variant_id  INTEGER NOT NULL UNIQUE,
            rank        INTEGER DEFAULT 0,
            FOREIGN KEY(base_id)    REFERENCES media(id) ON DELETE CASCADE,
            FOREIGN KEY(variant_id) REFERENCES media(id) ON DELETE CASCADE
        )
        """
    )
    cur.execute("CREATE INDEX IF NOT EXISTS idx_variants_base ON variants(base_id)")
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_variants_rank ON variants(base_id, rank)")
    if commit:
        conn.commit()


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
    if initialize_schema:
        ensure_schema(conn)
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

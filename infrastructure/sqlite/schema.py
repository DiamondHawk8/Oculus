"""The current catalog schema"""

import sqlite3

SCHEMA_VERSION = 4


class SchemaError(RuntimeError):
    """The selected catalog cannot be used by the current application."""


# Execute statements individually
TABLES = (
    """CREATE TABLE IF NOT EXISTS media (
        id INTEGER PRIMARY KEY,
        path TEXT UNIQUE,
        added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_dir BOOLEAN DEFAULT 0,
        byte_size INTEGER DEFAULT 0,
        favorite INTEGER NOT NULL DEFAULT 0,
        weight REAL,
        artist TEXT,
        type TEXT NOT NULL,
        device TEXT,
        inode TEXT,
        mtime INTEGER
    )""",
    """CREATE TABLE IF NOT EXISTS presets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id TEXT NOT NULL,
        name TEXT NOT NULL,
        media_id INTEGER,
        zoom REAL NOT NULL,
        pan_x INTEGER NOT NULL,
        pan_y INTEGER NOT NULL,
        is_default INTEGER NOT NULL DEFAULT 0,
        hotkey TEXT,
        FOREIGN KEY (media_id) REFERENCES media(id) ON DELETE CASCADE,
        UNIQUE (media_id, name),
        CHECK (is_default IN (0,1))
    )""",
    """CREATE TABLE IF NOT EXISTS tags (
        media_id INTEGER,
        tag TEXT,
        FOREIGN KEY (media_id) REFERENCES media(id) ON DELETE CASCADE,
        UNIQUE (media_id, tag)
    )""",
    """CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        media_id INTEGER NOT NULL,
        created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        text TEXT NOT NULL,
        seq INTEGER,
        FOREIGN KEY (media_id) REFERENCES media(id) ON DELETE CASCADE
    )""",
    """CREATE TABLE IF NOT EXISTS bookmarks (
        path TEXT NOT NULL,
        time_ms INTEGER NOT NULL,
        PRIMARY KEY (path, time_ms)
    )""",
    """CREATE TABLE IF NOT EXISTS variants (
        base_id INTEGER NOT NULL,
        variant_id INTEGER NOT NULL UNIQUE,
        rank INTEGER DEFAULT 0,
        FOREIGN KEY (base_id) REFERENCES media(id) ON DELETE CASCADE,
        FOREIGN KEY (variant_id) REFERENCES media(id) ON DELETE CASCADE
    )""",
)

INDEXES = (
    "CREATE INDEX IF NOT EXISTS idx_presets_group ON presets(group_id)",
    "CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag)",
    "CREATE INDEX IF NOT EXISTS idx_comments_media ON comments(media_id)",
    "CREATE INDEX IF NOT EXISTS idx_variants_base ON variants(base_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_variants_rank ON variants(base_id, rank)",
)

REQUIRED_COLUMNS = {
    "media": {"id", "path", "added", "is_dir", "byte_size", "favorite",
              "weight", "artist", "type", "device", "inode", "mtime"},
    "presets": {"id", "group_id", "name", "media_id", "zoom", "pan_x",
                "pan_y", "is_default", "hotkey"},
    "tags": {"media_id", "tag"},
    "comments": {"id", "media_id", "created", "text", "seq"},
    "bookmarks": {"path", "time_ms"},
    "variants": {"base_id", "variant_id", "rank"},
}


def columns(conn: sqlite3.Connection, table: str) -> set[str]:
    # Table names originate only from the constant schema definitions above.
    return {row[1] for row in conn.execute(f'PRAGMA table_info("{table}")')}


def validate_columns(conn: sqlite3.Connection) -> None:
    for table, required in REQUIRED_COLUMNS.items():
        missing = required - columns(conn, table)
        if missing:
            raise SchemaError(f"Catalog table {table} is missing: {', '.join(sorted(missing))}.")


def validate_schema(conn: sqlite3.Connection) -> None:
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    if version != SCHEMA_VERSION:
        instruction = (
            "Close Oculus and run the one-off converter described in README: "
            "python -m infrastructure.sqlite.migrations --database PATH"
            if version == 3 else "Check that you selected the intended database and code checkout."
        )
        raise SchemaError(
            f"Catalog version {version}; this application expects {SCHEMA_VERSION}. "
            f"Startup does not upgrade existing databases. {instruction}"
        )
    # Earlier refactor builds may have left a schema_migrations table. It is
    # harmless extra data: no longer create it, require it, or delete it.
    validate_columns(conn)


def _is_empty(conn: sqlite3.Connection) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE name NOT GLOB 'sqlite_*' LIMIT 1"
    ).fetchone() is None and conn.execute("PRAGMA user_version").fetchone()[0] == 0


def ensure_schema(conn: sqlite3.Connection) -> None:
    """Create a fresh catalog, or validate an existing one without altering it."""
    if conn.in_transaction:
        raise SchemaError("Schema initialization requires no pending transaction.")
    if not _is_empty(conn):
        validate_schema(conn)
        return

    # Only initialization owns a write transaction. Never repair or convert an existing catalog as a side effect of
    # launching
    conn.execute("BEGIN IMMEDIATE")
    try:
        if _is_empty(conn):
            for statement in (*TABLES, *INDEXES):
                conn.execute(statement)
            conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        validate_schema(conn)
        conn.execute("COMMIT")
    except BaseException:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise

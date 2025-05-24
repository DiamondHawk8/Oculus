import logging
from pathlib import Path
from typing import List, Iterable, Tuple, Sequence

from managers.db_utils import get_db_connection, generate_insert_sql

logger = logging.getLogger(__name__)


class TagManager:
    """Lightweight DB wrapper for media + tag storage."""
    _CREATE_MEDIA_TABLE = """
        CREATE TABLE IF NOT EXISTS media (
            id     INTEGER PRIMARY KEY AUTOINCREMENT,
            path   TEXT UNIQUE,
            sha256 TEXT,
            added  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """

    _CREATE_TAG_TABLE = """
        CREATE TABLE IF NOT EXISTS tags (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            media_id INTEGER REFERENCES media(id) ON DELETE CASCADE,
            tag      TEXT NOT NULL
        );
    """

    _CREATE_FTS = """
        CREATE VIRTUAL TABLE IF NOT EXISTS fts_media
        USING fts5(path, content='media', content_rowid='id');
    """

    def __init__(self, db_path: str | Path | None = None, *, backend: str = "sqlite") -> None:
        self.backend = backend.lower()
        self.conn = get_db_connection(db_path=db_path, backend=self.backend)
        self.cur = self.conn.cursor()

        self._init_schema()

    def add_tag(self, media_id: int, tags: Iterable[str]) -> None:
        """
        Insert one or many tag strings for media_id*
        Ignores duplicates at the DB level (TODO UNIQUE not enforced yet)
        """
        for tag in tags:
            sql, params = generate_insert_sql(
                "tags", ("media_id", "tag"), (media_id, tag), backend=self.backend
            )
            self.cur.execute(sql, params)
        self.conn.commit()

    def delete_tag(self, *,ids: Sequence[int] | None = None, media_id: int | None = None,
                   tags: Sequence[str] | None = None) -> None:
        """
        Delete tags by row ids OR  by *(media_id, tags)* combination.
        Passing both ids and (media_id, tags) will not work
        """
        if ids:
            self.cur.executemany(
                "DELETE FROM tags WHERE id = ?;" if self.backend == "sqlite"
                else "DELETE FROM tags WHERE id = %s;",
                [(i,) for i in ids],
            )
        elif media_id is not None and tags:
            placeholder = "?" if self.backend == "sqlite" else "%s"
            sql = (
                f"DELETE FROM tags WHERE media_id = {placeholder} AND tag = {placeholder};"
            )
            params = [(media_id, tag) for tag in tags]
            self.cur.executemany(sql, params)
        else:
            raise ValueError("Specify either ids or (media_id + tags)")

        self.conn.commit()

    def get_tags(self, media_id: int) -> List[Tuple[int, str]]:
        """
        Return list of (tag_id, tag_string) for the given media_id
        """
        placeholder = "?" if self.backend == "sqlite" else "%s"
        sql = f"SELECT id, tag FROM tags WHERE media_id = {placeholder};"
        self.cur.execute(sql, (media_id,))
        return self.cur.fetchall()


    def _init_schema(self) -> None:
        """Create core tables; add FTS table only on SQLite. TODO add fts later"""
        self.cur.execute(self._CREATE_MEDIA_TABLE)
        self.cur.execute(self._CREATE_TAG_TABLE)

    def add_media(self, path: str) -> int:
        """
        Insert path into the media table if it is not already present.
        Returns the media.id
        """
        ph = "%s" if self.backend == "postgres" else "?"
        sql = f"""INSERT INTO media (path)
                  VALUES ({ph})
                  ON CONFLICT(path) DO NOTHING;"""

        self.cur.execute(sql, (path,))
        self.conn.commit()

        # fetch id
        self.cur.execute(f"SELECT id FROM media WHERE path = {ph};", (path,))
        return self.cur.fetchone()[0]

    def all_paths(self) -> list[str]:
        self.cur.execute("SELECT path FROM media ORDER BY added;")
        return [row[0] for row in self.cur.fetchall()]

"""        if self.backend == "sqlite":
            try:
                self.cur.execute(self._CREATE_FTS)
            except Exception as exc:  # pragma: no cover
                logger.warning("FTS5 unavailable – continuing without it (%s)", exc)

        self.conn.commit()
"""
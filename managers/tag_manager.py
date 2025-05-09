import sqlite3
from pathlib import Path
from typing import Iterable
import db_utils

class TagManager:

    # --- SQL strings (D-3) ---
    _CREATE_MEDIA_TABLE = """
        CREATE TABLE IF NOT EXISTS media (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            path    TEXT UNIQUE,
            sha256  TEXT,
            added   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """

    _CREATE_TAG_TABLE = """
        CREATE TABLE IF NOT EXISTS tags (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            media_id INTEGER REFERENCES media(id) ON DELETE CASCADE,
            tag     TEXT
        );
    """

    _CREATE_FTS = """
        CREATE VIRTUAL TABLE IF NOT EXISTS fts_media
        USING fts5(path, content='media', content_rowid='id');
    """

    def __init__(self, db_path: str | Path | None = None, backend='sqlite') -> None:
        self.backend = backend
        self.connection = db_utils.get_db_connection(db_path=db_path, backend=backend)
        self.cursor = self.connection.cursor()

        self.cursor.execute(TagManager._CREATE_MEDIA_TABLE)
        self.cursor.execute(TagManager._CREATE_TAG_TABLE)
        self.cursor.execute(TagManager._CREATE_FTS)
        pass
    # add_tag, get_tags, etc. will remain no-ops until explicitly requested.

    def add_tag(self, media_id, tags: list):
        for tag in tags:
            command, values = db_utils.generate_insert_sql('tags', ['media_id', 'tag'], [str(media_id), str(tag)], self.backend)
            self.cursor.execute(command, values)
        self.connection.commit()

    def delete_tag(self, media_id, tags, ids=None):
        if ids:
            for id in ids:
                command = f"DELETE FROM tags WHERE id={id}"
        else:
            for tag in tags:
                command = f"DELETE FROM tags WHERE tag={tag} AND media_id={media_id};"
        self.connection.commit()

    def get_tags(self, media_id: int) -> list:

        command = f"SELECT id, tag FROM tags WHERE media_id = {media_id};"
        self.cursor.execute(command)
        return [(row[0], row[1]) for row in self.cursor.fetchall()]
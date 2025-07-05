from __future__ import annotations
import os, time, uuid
from pathlib import Path
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}

class MediaDAO:
    """
    Pure synchronous DB helper, no QT/Pyside
    """

    def __init__(self, conn):
        self.conn = conn
        self.cur = conn.cursor()

    # ---------- Core Operations ----------

    def insert_media(self, path: str) -> int:
        p = Path(path)
        is_dir = int(p.is_dir())
        size = 0 if is_dir else p.stat().st_size

        ftype = (
            "gif" if p.suffix.lower() == ".gif"
            else "video" if p.suffix.lower() in (".mp4", ".mkv", ".webm", ".mov")
            else "image" if not is_dir
            else "dir"
        )

        self.cur.execute(
            """
            INSERT INTO media(path, added, is_dir, byte_size, type)
            VALUES (?,?,?,?,?)
            ON CONFLICT(path) DO NOTHING
            """,
            (str(p), int(time.time()), is_dir, size, ftype),
        )
        if self.cur.rowcount:
            return self.cur.lastrowid
        row = self.cur.execute(
            "SELECT id FROM media WHERE path=?", (str(p),)
        ).fetchone()
        return row["id"]

    def set_attr(self, media_id: int, **kwargs):
        if not kwargs:
            return
        cols = ", ".join(f"{k}=?" for k in kwargs)
        self.cur.execute(f"UPDATE media SET {cols} WHERE id=?", (*kwargs.values(), media_id))

    def get_attr(self, media_id: int) -> Dict[str, Any]:
        row = self.cur.execute(
            "SELECT favorite, weight, artist FROM media WHERE id=?", (media_id,)
        ).fetchone()
        return dict(row) if row else {}

    # ---------- variants ----------
    def add_variant(self, base_id: int, variant_id: int, rank: int):
        self.cur.execute(
            "INSERT OR IGNORE INTO variants(base_id, variant_id, rank) VALUES (?,?,?)",
            (base_id, variant_id, rank)
        )

    def stack_ids_for_base(self, base_id: int) -> List[int]:
        rows = self.cur.execute(
            "SELECT variant_id FROM variants WHERE base_id=? ORDER BY rank",
            (base_id,)
        ).fetchall()
        return [base_id] + [r['variant_id'] for r in rows]
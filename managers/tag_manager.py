from typing import Iterable, List, Dict, Any
from .base import BaseManager


class TagManager(BaseManager):
    def set_tags(self, media_id: int, tags: Iterable[str], *, overwrite=False):
        if overwrite:
            self.execute("DELETE FROM tags WHERE media_id=?", (media_id,))
        rows = [(media_id, t.strip().lower()) for t in tags if t.strip()]
        if rows:
            self.cur.executemany("INSERT OR IGNORE INTO tags(media_id, tag) VALUES (?,?)", rows)
            self.conn.commit()

    def get_tags(self, media_id: int) -> List[str]:
        rows = self.fetchall("SELECT tag FROM tags WHERE media_id=?", (media_id,))
        return [r["tag"] for r in rows]

    def get_attr(self, media_id: int) -> Dict[str, Any]:
        row = self.fetchone("SELECT * FROM attributes WHERE media_id=?", (media_id,))
        return dict(row) if row else {}

    def set_attr(self, media_id: int, **kwargs):
        cols = ", ".join(kwargs)
        marks = ", ".join("?" * len(kwargs))
        sql = (
                f"INSERT INTO attributes(media_id, {cols}) VALUES ({','.join(['?'] * (len(kwargs) + 1))}) "
                f"ON CONFLICT(media_id) DO UPDATE SET " +
                ", ".join(f"{k}=excluded.{k}" for k in kwargs)
        )
        self.execute(sql, (media_id, *kwargs.values()))

    def save_preset(self, media_id: int, name: str, zoom: float, pan_x: int, pan_y: int):
        self.execute(
            "INSERT OR REPLACE INTO presets(media_id,name,zoom,pan_x,pan_y) VALUES (?,?,?,?,?)",
            (media_id, name, zoom, pan_x, pan_y)
        )

    def list_presets(self, media_id: int):
        rows = self.fetchall("SELECT * FROM presets WHERE media_id=?", (media_id,))
        return [dict(r) for r in rows]

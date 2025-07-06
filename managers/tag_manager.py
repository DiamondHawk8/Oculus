from typing import Iterable, List, Dict, Any
import logging

from .base import BaseManager

logger = logging.getLogger(__name__)


class TagManager(BaseManager):
    def set_tags(self, media_id: int, tags: Iterable[str], *, overwrite=False):
        logger.info(f"Setting tags for media with id {media_id} to {tags}")
        if overwrite:
            logger.warning("Overwriting existing tags")
            self.execute("DELETE FROM tags WHERE media_id=?", (media_id,))
        rows = [(media_id, t.strip().lower()) for t in tags if t.strip()]
        if rows:
            self.cur.executemany("INSERT OR IGNORE INTO tags(media_id, tag) VALUES (?,?)", rows)
            self.conn.commit()

    def get_tags(self, media_id: int) -> List[str]:
        logger.info(f"Getting tags for media with id {media_id}")
        rows = self.fetchall("SELECT tag FROM tags WHERE media_id=?", (media_id,))
        return [r["tag"] for r in rows]

    def delete_tags(self, media_id: int, tags: Iterable[str]):
        """
        Remove the given tags from a single media row.
        :param media_id:
        :param tags:
        :return:
        """
        rows = [(media_id, t.strip().lower()) for t in tags if t.strip()]
        if not rows:
            return
        self.cur.executemany(
            "DELETE FROM tags WHERE media_id=? AND tag=?", rows
        )
        self.conn.commit()

    def get_attr(self, media_id: int) -> Dict[str, Any]:
        logger.info(f"Getting attributes for media with id {media_id}")
        row = self.fetchone("SELECT * FROM attributes WHERE media_id=?", (media_id,))
        return dict(row) if row else {}

    def set_attr(self, media_id: int, **kwargs):
        logger.info(f"Setting attributes for media with id {media_id}")
        cols = ", ".join(kwargs)
        sql = (
                f"INSERT INTO attributes(media_id, {cols}) VALUES ({','.join(['?'] * (len(kwargs) + 1))}) "
                f"ON CONFLICT(media_id) DO UPDATE SET " +
                ", ".join(f"{k}=excluded.{k}" for k in kwargs)
        )
        self.execute(sql, (media_id, *kwargs.values()))

    def save_preset(self, group_id, media_id: int, name: str, zoom: float, pan_x: int, pan_y: int):
        logger.debug(f"Creating new preset for media with id {media_id}")
        logger.debug(f"Preset args:\ngroup_id: {group_id}\nname: {name}\nzoom: {zoom}\npan_x: {pan_x}\npan_y: {pan_y}")
        self.execute(
            "INSERT OR REPLACE INTO presets(group_id,media_id,name,zoom,pan_x,pan_y) VALUES (?,?,?,?,?,?)",
            (group_id, media_id, name, zoom, pan_x, pan_y)
        )

    def list_presets(self, media_id: int):
        logger.info(f"Listing presets for media with id {media_id}")
        rows = self.fetchall("SELECT * FROM presets WHERE media_id=?", (media_id,))
        return [dict(r) for r in rows]

    def distinct_tags(self):
        rows = self.fetchall("SELECT DISTINCT tag FROM tags", ())
        return [r["tag"] for r in rows]

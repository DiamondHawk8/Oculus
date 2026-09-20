from __future__ import annotations

import logging
import os
import re
import time
from pathlib import Path
from typing import List, Dict, Any

from controllers.utils.path_utils import natural_key
from .base import BaseManager

logger = logging.getLogger(__name__)

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}

_SORT_SQL = {
    ("name", True): "ORDER BY LOWER(path)         ASC",
    ("name", False): "ORDER BY LOWER(path)         DESC",
    ("date", True): "ORDER BY added               ASC",
    ("date", False): "ORDER BY added               DESC",
    ("size", True): "ORDER BY byte_size           ASC",
    ("size", False): "ORDER BY byte_size           DESC",
    ("weight", True): "ORDER BY COALESCE(weight,1) ASC",
    ("weight", False): "ORDER BY COALESCE(weight,1) DESC",
}

_VARIANT_RE = re.compile(r"^(.*)_v(\d+)$", re.I)  # captures (stem, index)


class MediaDAO(BaseManager):
    """
    Pure synchronous DB helper, no QT/Pyside
    """

    def __init__(self, conn):
        super().__init__(conn)
        self.conn = conn
        self.cur = conn.cursor()

    # ---------- Core Operations ----------

    @staticmethod
    def file_identity(st: os.stat_result) -> tuple[str, str]:
        # Windows may expose a 128-bit file ID in st_ino. A non-numeric prefix
        # prevents SQLite INTEGER affinity from coercing it to a lossy REAL.
        return f"d:{st.st_dev}", f"i:{st.st_ino}"

    def insert_media(
            self,
            path: str,
            st: os.stat_result | None = None,
            *,
            commit: bool = True,
    ) -> int:
        p = Path(path)
        st = st or p.stat()
        is_dir = int(p.is_dir())
        size = 0 if is_dir else st.st_size
        device, inode = self.file_identity(st)
        mtime = int(st.st_mtime)
        ftype = (
            "gif" if p.suffix.lower() == ".gif" else
            "video" if p.suffix.lower() in (".mp4", ".mkv", ".webm", ".mov", ".avi") else
            "image" if not is_dir else
            "dir"
        )

        try:
            # noinspection SqlResolve -- device is added by the runtime schema migration.
            self.cur.execute(
                """
                INSERT INTO media(path, added, is_dir, byte_size,
                                  type, device, inode, mtime)
                VALUES (?,?,?,?,?,?,?,?)
                ON CONFLICT(path) DO NOTHING
                """,
                (str(p), int(time.time()), is_dir, size, ftype, device, inode, mtime),
            )
            if self.cur.rowcount:
                media_id = self.cur.lastrowid
                if media_id is None:
                    raise RuntimeError("SQLite did not return an id for inserted media")
                if commit:
                    self.conn.commit()
                return int(media_id)

            # Refresh identity data for rows created before device tracking was
            # introduced, without treating the existing path as a new import.
            # noinspection SqlResolve -- device is added by the runtime schema migration.
            self.cur.execute(
                """UPDATE media
                   SET is_dir=?, byte_size=?, type=?, device=?, inode=?, mtime=?
                   WHERE path=?""",
                (is_dir, size, ftype, device, inode, mtime, str(p)),
            )
            if commit:
                self.conn.commit()
        except Exception:
            if commit:
                self.conn.rollback()
            raise

        row = self.cur.execute(
            "SELECT id FROM media WHERE path = ?", (str(p),)
        ).fetchone()
        return row["id"] if row else 0

    def update_media_path(
            self,
            mid: int,
            new_path: str,
            mtime: int,
            *,
            commit: bool = True,
    ) -> None:
        try:
            self.cur.execute(
                "UPDATE media SET path = ?, mtime = ? WHERE id = ?",
                (new_path, mtime, mid),
            )
            if commit:
                self.conn.commit()
        except Exception:
            if commit:
                self.conn.rollback()
            raise

    def fetch_many_file_identities(
            self,
            identities: list[tuple[str, str]],
    ) -> dict[tuple[str, str], list[tuple[int, str]]]:
        """Return every row for each ``(device, inode)`` identity."""
        if not identities:
            return {}
        result: dict[tuple[str, str], list[tuple[int, str]]] = {}
        unique = list(dict.fromkeys(identities))
        for start in range(0, len(unique), 400):
            chunk = unique[start:start + 400]
            clauses = " OR ".join("(device=? AND inode=?)" for _ in chunk)
            params = tuple(value for identity in chunk for value in identity)
            rows = self.cur.execute(
                f"SELECT id, path, device, inode FROM media WHERE {clauses}",
                params,
            ).fetchall()
            for row in rows:
                key = (row["device"], row["inode"])
                result.setdefault(key, []).append((row["id"], row["path"]))
        return result

    def fetch_many_paths(self, paths: list[str]) -> dict[str, int]:
        result: dict[str, int] = {}
        for start in range(0, len(paths), 900):
            chunk = paths[start:start + 900]
            if not chunk:
                continue
            placeholders = ",".join("?" for _ in chunk)
            rows = self.cur.execute(
                f"SELECT id, path FROM media WHERE path IN ({placeholders})",
                chunk,
            ).fetchall()
            result.update((row["path"], row["id"]) for row in rows)
        return result

    def set_attr(self, media_id: int, **kwargs):
        logger.debug(f"Setting attributes for {media_id} with args {kwargs}")
        if not kwargs:
            return
        allowed = {"favorite", "weight", "artist"}
        invalid = set(kwargs) - allowed
        if invalid:
            raise ValueError(f"Unsupported media attributes: {sorted(invalid)}")
        cols = ", ".join(f"{k}=?" for k in kwargs)
        with self.conn:
            self.cur.execute(f"UPDATE media SET {cols} WHERE id=?", (*kwargs.values(), media_id))

    def get_attr(self, media_id: int) -> Dict[str, Any]:
        logger.debug(f"Getting attributes for {media_id}")
        row = self.cur.execute(
            "SELECT favorite, weight, artist FROM media WHERE id=?", (media_id,)
        ).fetchone()
        return dict(row) if row else {}

    # ------------------------------ Variants ------------------------------
    def add_variant(self, base_id: int, variant_id: int, rank: int):
        logger.debug(f"Adding variant {variant_id} to {base_id}, with rank {rank}")
        with self.conn:
            self.cur.execute(
                "INSERT OR IGNORE INTO variants(base_id, variant_id, rank) VALUES (?,?,?)",
                (base_id, variant_id, rank)
            )

    def is_variant(self, path: str) -> bool:
        row = self.fetchone("SELECT id FROM media WHERE path=?", (path,))
        if not row:
            return False
        media_id = row["id"]
        # variant if it appears in variants.variant_id and NOT as base_id
        return bool(self.fetchone(
            "SELECT 1 FROM variants WHERE variant_id=? LIMIT 1", (media_id,))
        )

    def is_stacked(self, media_id: int) -> bool:
        row = self.fetchone(
            "SELECT 1 FROM variants WHERE base_id=? OR variant_id=? LIMIT 1",
            (media_id, media_id)
        )
        return row is not None

    def is_stacked_base(self, media_id: int) -> bool:
        row = self.fetchone("SELECT 1 FROM variants WHERE base_id=? LIMIT 1", (media_id,))
        return row is not None

    def detect_and_stack(self, media_id: int, path: str) -> None:
        p = Path(path)
        m = _VARIANT_RE.match(p.stem)

        # add variant file first
        if m:
            base_stem, idx = m.groups()
            base_path = str(p.with_name(base_stem + p.suffix))
            row = self.fetchone("SELECT id FROM media WHERE path=?", (base_path,))
            if row:
                self.add_variant(row["id"], media_id, int(idx))
            return

        # Search the exact parent without SQL wildcards, filenames can
        # contain '%' and '_' and should not alter matching semantics
        base_stem = p.stem
        parent_prefix = str(p.parent) + os.sep
        rows = self.fetchall(
            "SELECT id, path FROM media WHERE substr(path, 1, ?) = ?",
            (len(parent_prefix), parent_prefix),
        )
        for v_id, v_path in rows:
            m2 = _VARIANT_RE.match(Path(v_path).stem)
            if m2 and Path(v_path).parent == p.parent and Path(v_path).suffix.lower() == p.suffix.lower():
                candidate_base, idx2 = m2.groups()
                if candidate_base.casefold() != base_stem.casefold():
                    continue
                self.add_variant(media_id, v_id, int(idx2))

    def stack_ids_for_base(self, base_id: int) -> List[int]:
        logger.debug(f"Getting base ids for {base_id}")
        rows = self.cur.execute(
            "SELECT variant_id FROM variants WHERE base_id=? ORDER BY rank",
            (base_id,)
        ).fetchall()
        return [base_id] + [r['variant_id'] for r in rows]

    def stack_paths(self, path: str) -> List[str]:
        row = self.fetchone("SELECT id FROM media WHERE path=?", (path,))
        if not row:
            return [path]

        media_id = row["id"]

        # Is this the base?
        if self.fetchone("SELECT 1 FROM variants WHERE base_id=? LIMIT 1", (media_id,)):
            ids = self.stack_ids_for_base(media_id)
        else:
            # it might be a variant -> find its base
            row2 = self.fetchone("SELECT base_id FROM variants WHERE variant_id=?", (media_id,))
            if not row2:
                return [path]  # not stacked
            ids = self.stack_ids_for_base(row2["base_id"])

        # map ids -> paths
        rows = self.fetchall(
            f"SELECT id, path FROM media WHERE id IN ({','.join('?' * len(ids))})",
            tuple(ids)
        )
        id_to_path = {r['id']: r['path'] for r in rows}
        return [id_to_path[i] for i in ids if i in id_to_path]

    # ------------------------------ Sorting Queries ------------------------------
    def get_sorted_paths(self, sort_key: str, ascending: bool = True) -> list[str]:
        logger.debug(f"Obtaining sorted paths with args: sort_key: {sort_key}, ascending: {ascending}")
        clause = _SORT_SQL.get((sort_key, ascending))
        if clause is None:
            clause = _SORT_SQL[("name", True)]

        sql = f"SELECT path FROM media WHERE is_dir=0 {clause};"
        self.cur.execute(sql)
        return [r["path"] for r in self.cur.fetchall()]

    def order_subset(self, subset: list[str], sort_key: str, asc: bool) -> list[str]:
        if not subset:
            return []

        if sort_key == "name":
            return sorted(subset, key=natural_key, reverse=not asc)

        value_sql = {
            "date": "CASE WHEN typeof(added) IN ('integer', 'real') "
                    "THEN added ELSE COALESCE(strftime('%s', added), 0) END",
            "size": "COALESCE(byte_size, 0)",
            "weight": "COALESCE(weight, 1)",
        }.get(sort_key, "LOWER(path)")
        values: dict[str, object] = {}
        for i in range(0, len(subset), 900):
            chunk = subset[i:i + 900]
            ph = ", ".join("?" for _ in chunk)
            sql = f"SELECT path, {value_sql} AS sort_value FROM media WHERE path IN ({ph});"
            self.cur.execute(sql, chunk)
            values.update((row["path"], row["sort_value"]) for row in self.cur.fetchall())

        ordered = sorted(values, key=lambda path: (values[path], path.lower()), reverse=not asc)
        missing = [p for p in subset if p not in values]
        return ordered + missing

    # ------------------------------ Universal Helpers ------------------------------
    def all_paths(self, *, files_only: bool = True) -> list[str]:
        logger.debug(f"Obtaining all paths, files_only: {files_only}")
        if files_only:
            self.cur.execute("SELECT path FROM media WHERE is_dir = 0")
        else:
            self.cur.execute("SELECT path FROM media")
        return [row["path"] for row in self.cur.fetchall()]

    def folder_paths(self) -> list[str]:
        logger.info("Obtaining folder paths")
        self.cur.execute("SELECT path FROM media WHERE is_dir = 1")
        return [r["path"] for r in self.cur.fetchall()]

    def paths_in_folder(self, folder: str | Path) -> list[str]:
        """Return media whose immediate parent is exactly ``folder``."""
        folder = Path(folder)
        prefix = str(folder) + os.sep
        rows = self.fetchall(
            "SELECT path FROM media WHERE is_dir=0 AND substr(path, 1, ?) = ?",
            (len(prefix), prefix),
        )
        return [row["path"] for row in rows if Path(row["path"]).parent == folder]

    def root_folders(self) -> list[str]:
        self.cur.execute("SELECT path FROM media WHERE is_dir=1")
        all_folders = [row["path"] for row in self.cur.fetchall()]
        folder_set = set(all_folders)
        roots = [
            p for p in all_folders
            if str(Path(p).parent) not in folder_set
        ]
        return sorted(roots)

    def path_for_id(self, media_id: int) -> str | None:
        """
        Return absolute path string for a given media_id (or None if missing).
        :param media_id:
        :return:
        """
        row = self.fetchone("SELECT path FROM media WHERE id=?", (media_id,))
        return row["path"] if row else None

    def folder_for_id(self, media_id: int) -> Path | None:
        p = self.path_for_id(media_id)
        return Path(p).parent if p else None

    # ------------------------------ Presets ------------------------------

    def list_presets_in_group(self, group_id: str):
        return self.fetchall(
            """
            SELECT p.*, m.path
            FROM   presets p
            LEFT   JOIN media m ON m.id = p.media_id
            WHERE  p.group_id = ?
            """,
            (group_id,),
        )

    def list_presets_for_media(self, media_id: int) -> list[dict]:
        return self.fetchall(
            """
            SELECT p.id, p.group_id, p.name, p.media_id,
                   p.zoom, p.pan_x, p.pan_y,
                   p.is_default, p.hotkey,
                   m.path                         -- ← NEW
            FROM   presets p
            LEFT   JOIN media m ON m.id = p.media_id
            WHERE  p.media_id = ?
               OR  (p.media_id IS NULL AND m.id = ?)
            """,
            (media_id, media_id),
        )

    # ------------------------------ Comments ------------------------------

    def add_comment(self, media_id: int, text: str, seq: int) -> int:
        with self.conn:
            self.cur.execute(
                "INSERT INTO comments(media_id, text, seq) VALUES (?,?,?)",
                (media_id, text.strip(), seq)
            )
        return self.cur.lastrowid

    def list_comments(self, media_id: int) -> list[dict]:
        with self.conn:
            self.cur.execute(
                "SELECT id, created, text, seq FROM comments "
                "WHERE media_id=? ORDER BY seq", (media_id,)
            )
        return [dict(r) for r in self.cur.fetchall()]

    def delete_comment(self, comment_id: int) -> None:
        with self.conn:
            self.cur.execute("DELETE FROM comments WHERE id=?", (comment_id,))

    def update_comment(self, comment_id: int, text: str) -> None:
        with self.conn:
            self.cur.execute(
                "UPDATE comments SET text=? WHERE id=?", (text, comment_id)
            )

    def update_comment_sequence(self, media_id: int, ordered_ids: list[int]):
        cases = " ".join("WHEN ? THEN ?" for _ in ordered_ids)
        ids = ", ".join("?" for _ in ordered_ids)
        case_params = tuple(
            value for idx, comment_id in enumerate(ordered_ids) for value in (comment_id, idx)
        )

        sql = (
            "UPDATE comments "
            f"SET seq = CASE id {cases} END "
            f"WHERE id IN ({ids}) AND media_id=?"
        )
        with self.conn:
            self.cur.execute(sql, (*case_params, *ordered_ids, media_id))

    def bookmarks_for_path(self, path: str) -> list[int]:
        rows = self.cur.execute(
            "SELECT time_ms FROM bookmarks WHERE path = ? ORDER BY time_ms", (path,)
        ).fetchall()
        return [r["time_ms"] for r in rows]

    def add_bookmark(self, path: str, ms: int) -> None:
        with self.conn:
            self.cur.execute(
                "INSERT OR IGNORE INTO bookmarks(path, time_ms) VALUES (?, ?)",
                (path, ms),
            )

    def delete_bookmark(self, path: str, ms: int) -> None:
        with self.conn:
            self.cur.execute(
                "DELETE FROM bookmarks WHERE path = ? AND time_ms = ?",
                (path, ms),
            )

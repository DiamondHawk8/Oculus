from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
import os
from collections import deque, OrderedDict
from typing import Callable

from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool, Qt, QMetaObject, Slot, QTimer, Q_ARG
from PySide6.QtGui import QPixmap

from .base import BaseManager

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}
_CACHE_CAPACITY = 512
_THUMB_CACHE: "OrderedDict[tuple[str, int], QPixmap]" = OrderedDict()

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


class MediaManager(BaseManager, QObject):
    """
    Thread-aware loader for image assets, currently only processes images
    """

    scan_finished = Signal(list)
    thumb_ready = Signal(str, object)
    _scan_done = Signal(object)

    def __init__(self, conn, thumb_size: int = 256, parent=None):
        BaseManager.__init__(self, conn)
        QObject.__init__(self, parent)

        self.thumb_size = thumb_size
        self.pool = QThreadPool.globalInstance()

        self._scan_done.connect(self._process_scan_result)

    def scan_folder(self, folder: str | Path) -> None:
        """
        This method returns immediately; results are delivered via scan_finished
        """
        folder = Path(folder).expanduser().resolve()
        task = _ScanTask(folder, self)
        self.pool.start(task)

    def thumb(self, path: str | Path) -> None:
        """
        Ensure a thumbnail for path is available and emit thumb_ready.
        """
        path = str(path)
        cached = _thumbnail_cache_get(path, self.thumb_size)
        if cached is not None:
            self.thumb_ready.emit(path, cached)
            return
        task = _ThumbTask(path, self.thumb_size, self._on_thumb_complete)
        self.pool.start(task)

    # DB helpers (sync)
    def add_media(self, path: str, *, is_dir: bool, size: int = 0) -> int:
        self.execute(
            "INSERT OR IGNORE INTO media(path, is_dir, byte_size) VALUES (?,?,?)",
            (path, int(is_dir), size),
        )
        row = self.fetchone("SELECT id FROM media WHERE path=?", (path,))
        return row["id"]

    # task callbacks (GUI thread)
    def _on_scan_complete(self, paths: list[str]) -> None:
        for p in paths:
            self.add_media(p, is_dir=False)
        self.scan_finished.emit(paths)

    def _on_thumb_complete(self, path: str, pix: QPixmap) -> None:
        _thumbnail_cache_set(path, self.thumb_size, pix)
        self.thumb_ready.emit(path, pix)

    def walk_tree(self, root: str | Path) -> dict[str, tuple[list[str], list[str]]]:
        root = Path(root).expanduser().resolve()
        tree: dict[str, tuple[list[str], list[str]]] = {}
        q: deque[Path] = deque([root])
        while q:
            folder = q.popleft()
            sub, imgs = [], []
            for child in folder.iterdir():
                if child.is_dir():
                    sub.append(str(child))
                    q.append(child)
                elif child.suffix.lower() in IMAGE_EXT:
                    imgs.append(str(child))
            tree[str(folder)] = (sub, imgs)
        return tree

    def all_paths(self, *, files_only: bool = True) -> list[str]:
        """
        Return every path currently in the DB (files by default).
        :param files_only: If false, function will also return directory paths
        :return: 
        """
        if files_only:
            self.cur.execute("SELECT path FROM media WHERE is_dir = 0")
        else:
            self.cur.execute("SELECT path FROM media")
        return [row["path"] for row in self.cur.fetchall()]

    @Slot(object)
    def _process_scan_result(self, items):
        seen_dirs = set()
        for p, sz in items:

            self.add_media(p, is_dir=False, size=sz)
            parent = str(Path(p).parent)

            if parent not in seen_dirs:
                self.add_media(parent, is_dir=True)
                seen_dirs.add(parent)

        self.scan_finished.emit([p for p, _ in items])

    def folder_paths(self) -> list[str]:
        self.cur.execute("SELECT path FROM media WHERE is_dir = 1")
        return [r["path"] for r in self.cur.fetchall()]

    def root_folders(self) -> list[str]:
        """Folders whose parent directory is NOT itself recorded"""
        self.cur.execute("SELECT path FROM media WHERE is_dir=1")
        all_folders = [row["path"] for row in self.cur.fetchall()]
        folder_set = set(all_folders)
        roots = [
            p for p in all_folders
            if str(Path(p).parent) not in folder_set
        ]
        return sorted(roots)

    def get_sorted_paths(self, sort_key: str, ascending: bool = True) -> list[str]:
        """
        :param sort_key: Key to sort by
        :param ascending: Return sort in ascending order
        :return:
        """

        clause = _SORT_SQL.get((sort_key, ascending))
        if clause is None:
            clause = _SORT_SQL[("name", True)]

        sql = f"SELECT path FROM media WHERE is_dir=0 {clause};"
        self.cur.execute(sql)
        return [r["path"] for r in self.cur.fetchall()]

    def order_subset(self, subset: list[str], sort_key: str, asc: bool) -> list[str]:
        """
        Return subset of paths ordered by the same criteria
        used in get_sorted_paths(). Items not found in the DB are appended unchanged
        """
        if not subset:
            return []

        clause = _SORT_SQL.get((sort_key, asc), _SORT_SQL[("name", True)])

        # Build parameter list for SQL IN
        ph = ", ".join("?" for _ in subset)

        sql = f"""
            SELECT path FROM media
            WHERE path IN ({ph})
            {clause};
        """
        self.cur.execute(sql, subset)
        ordered = [row["path"] for row in self.cur.fetchall()]

        # Any paths missing from DB or filtered out are appended in original order
        missing = [p for p in subset if p not in ordered]
        return ordered + missing


# Thread tasks
class _ScanTask(QRunnable):
    def __init__(self, folder: Path, mgr: "MediaManager"):
        super().__init__()
        self.folder = folder
        self.mgr = mgr
        self.setAutoDelete(True)

    def run(self):
        out = []
        for root, _, files in os.walk(self.folder):
            for fn in files:
                if Path(fn).suffix.lower() in IMAGE_EXT:
                    p = Path(root) / fn
                    out.append((str(p), p.stat().st_size))
        self.mgr._scan_done.emit(out)  # queued to GUI thread


class _ThumbTask(QRunnable):
    def __init__(self, path: str, size: int, cb: Callable[[str, QPixmap], None]):
        super().__init__()
        self.p = path
        self.s = size
        self.cb = cb
        self.setAutoDelete(True)

    def run(self):
        pix = _generate_thumb(self.p, self.s)
        if not pix.isNull():
            self.cb(self.p, pix)


def _generate_thumb(path: str, size: int) -> QPixmap:
    pix = QPixmap(path)
    return pix.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation) if not pix.isNull() else QPixmap()


def _thumbnail_cache_get(p: str, s: int) -> QPixmap | None:
    key = (p, s)
    pix = _THUMB_CACHE.get(key)
    if pix:
        _THUMB_CACHE.move_to_end(key)
    return pix


def _thumbnail_cache_set(p: str, s: int, pix: QPixmap):
    key = (p, s)
    _THUMB_CACHE[key] = pix
    _THUMB_CACHE.move_to_end(key)
    if len(_THUMB_CACHE) > _CACHE_CAPACITY:
        _THUMB_CACHE.popitem(last=False)

from __future__ import annotations

import json
import logging
import os
import sqlite3
import time
import uuid
from collections import deque, OrderedDict
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool, Qt, Slot
from PySide6.QtGui import QPixmap

from .base import BaseManager

from widgets.collision_dialog import CollisionDialog

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

_BACKUP_DIR = Path.home() / "OculusBackups"
_BACKUP_DIR.mkdir(exist_ok=True)

logger = logging.getLogger(__name__)


def _log_rename(old_path: str, new_path: str):
    log_file = _BACKUP_DIR / "rename_log.json"
    entry = {
        "timestamp": time.time(),
        "old": old_path,
        "new": new_path,
    }
    try:
        data = json.loads(log_file.read_text()) if log_file.exists() else []
    except json.JSONDecodeError:
        logger.error("Error decoding file name log file")
        data = []
    data.append(entry)
    log_file.write_text(json.dumps(data, indent=2))


class MediaManager(BaseManager, QObject):
    """
    Thread-aware loader for image assets, currently only processes images
    """

    scan_finished = Signal(list)
    thumb_ready = Signal(str, object)
    _scan_done = Signal(object)
    renamed = Signal(str, str)

    def __init__(self, conn, undo_manager, thumb_size: int = 256, parent=None):
        BaseManager.__init__(self, conn)
        QObject.__init__(self, parent)

        self.undo_manager = undo_manager

        self.thumb_size = thumb_size
        self.pool = QThreadPool.globalInstance()

        self._scan_done.connect(self._process_scan_result)

        logger.info("Media manager initialized")

    # DB helpers (sync)
    def add_media(self, path: str, *, is_dir: bool, size: int = 0) -> int:
        self.execute(
            "INSERT OR IGNORE INTO media(path, is_dir, byte_size) VALUES (?,?,?)",
            (path, int(is_dir), size),
        )
        row = self.fetchone("SELECT id FROM media WHERE path=?", (path,))
        return row["id"]

    def rename_media(self, old_abs: str, new_abs: str) -> bool:
        """
        Rename on disk and update DB. Returns False if the destination already exists or any error occurs.
        :param old_abs: Old absolute path of media
        :param new_abs: New absolute path of media
        :return: True if operation was successful, False otherwise
        """
        logger.info(f"Attempting to rename {old_abs} to {new_abs}")

        old_path = Path(old_abs).expanduser().resolve()
        new_path = Path(new_abs).expanduser().resolve()

        # collision check
        if new_path.exists():
            choice = CollisionDialog.ask(str(old_path), str(new_path))
            if choice in ("cancel", "skip"):
                return False
            if choice == "auto":
                new_path = self._unique_path(new_path)
            elif choice == "overwrite":
                return self._safe_overwrite(old_path, new_path)

        row = self.fetchone("SELECT 1 FROM media WHERE path=?", (str(new_path),))
        if row:
            return False

        # perform rename on disk
        try:
            old_path.rename(new_path)
        except OSError as exc:
            logger.error(f"Rename failed on disk: {exc}")
            return False

        # update DB row
        self.execute("UPDATE media SET path=? WHERE path=?", (str(new_path), str(old_path)))

        _log_rename(str(old_path), str(new_path))

        if self.undo_manager:
            self.undo_manager.push(str(old_path), str(new_path))

        self.renamed.emit(str(old_path), str(new_path))

        return True

    def scan_folder(self, folder: str | Path) -> None:
        """
        This method returns immediately; results are delivered via scan_finished
        """

        logger.info(f"Attempting to scan folder {folder}")

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

    # ---------------------------- db backup management methods

    def _safe_overwrite(self, old_path: Path, new_path: Path) -> bool:
        """
        1. Move destination file → backup.
        2. Move source file     → destination.
        3. Update DB rows inside ONE transaction.
        4. Push UndoEntry with backup so it can be fully restored.
        Signals emitted for both moves so all views update instantly.
        """
        logger = logging.getLogger(__name__)
        backup_path = self._backup_path(new_path)

        try:
            # -- A: FILE SYSTEM -------------------------------------------------
            # move dest → backup  (may not exist ; catch FileNotFound)
            if new_path.exists():
                new_path.replace(backup_path)
                # UI: dest has disappeared (new → backup)
                self.renamed.emit(str(new_path), str(backup_path))

            # move src → dest
            old_path.replace(new_path)
            # UI: src now at dest
            self.renamed.emit(str(old_path), str(new_path))

            # -- B: DATABASE (single atomic scope) -----------------------------
            with self.conn:
                # If dest record existed, migrate it to backup_path
                self.execute(
                    "UPDATE media SET path=? WHERE path=?",
                    (str(backup_path), str(new_path))
                )
                # Update source record to new_path
                self.execute(
                    "UPDATE media SET path=? WHERE path=?",
                    (str(new_path), str(old_path))
                )

            # -- C: Logging & undo ---------------------------------------------
            _log_rename(str(old_path), str(new_path))
            if self.undo_manager:
                self.undo_manager.push(str(old_path), str(new_path),
                                   backup=str(backup_path))
            return True

        except Exception as exc:
            logger.error("Safe overwrite failed: %s", exc)
            # Best-effort roll-back (optional: add more elaborate recovery)
            return False

    def _backup_path(self, original: Path) -> Path:
        bk_dir = Path.home() / "OculusBackups" / "overwritten"
        bk_dir.mkdir(parents=True, exist_ok=True)
        return bk_dir / f"{uuid.uuid4()}{original.suffix}"

    def restore_overwrite(self, entry: "UndoEntry") -> bool:
        """
        Revert a safe overwrite recorded in UndoEntry:
            new_path -> old_path
            backup -> new_path
            DB rows adjusted
        :param entry:
        :return:
        """
        old_path = Path(entry.old)
        new_path = Path(entry.new)
        backup = Path(entry.backup)

        try:
            # -- A: FILE SYSTEM
            # Move current file back to old_path
            new_path.replace(old_path)
            self.renamed.emit(str(new_path), str(old_path))

            # Restore backup → new_path
            backup.replace(new_path)
            self.renamed.emit(str(backup), str(new_path))

            # B: DATABASE
            with self.conn:
                # Row that represents current file -> old_path
                self.execute(
                    "UPDATE media SET path=? WHERE path=?",
                    (str(old_path), str(new_path))
                )
                # Row for backup file -> new_path
                self.execute(
                    "UPDATE media SET path=? WHERE path=?",
                    (str(new_path), str(backup))
                )

            return True

        except Exception as exc:
            logger.error("Undo overwrite failed: %s", exc)
            return False

    # ----------------------------- task callbacks (GUI thread)
    def _on_scan_complete(self, paths: list[str]) -> None:
        logger.info("Scan complete")
        for p in paths:
            self.add_media(p, is_dir=False)
        self.scan_finished.emit(paths)

    def _on_thumb_complete(self, path: str, pix: QPixmap) -> None:
        _thumbnail_cache_set(path, self.thumb_size, pix)
        self.thumb_ready.emit(path, pix)

    # ----------------------------- Path Getters

    def all_paths(self, *, files_only: bool = True) -> list[str]:
        """
        Return every path currently in the DB (files by default).
        :param files_only: If false, function will also return directory paths
        :return:
        """
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

    # ----------------------------- Sorting

    def get_sorted_paths(self, sort_key: str, ascending: bool = True) -> list[str]:
        """
        :param sort_key: Key to sort by
        :param ascending: Return sort in ascending order
        :return:
        """
        logger.debug(f"Obtaining sorted paths with args: sort_key: {sort_key}, ascending: {ascending}")
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

    # ----------------------------- Misc
    @Slot(object)
    def _process_scan_result(self, items):
        logger.info("Processing scan result")
        seen_dirs = set()
        for p, sz in items:

            self.add_media(p, is_dir=False, size=sz)
            parent = str(Path(p).parent)

            if parent not in seen_dirs:
                self.add_media(parent, is_dir=True)
                seen_dirs.add(parent)

        self.scan_finished.emit([p for p, _ in items])

    def walk_tree(self, root: str | Path) -> dict[str, tuple[list[str], list[str]]]:
        logger.info("Walking tree")
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

    def _unique_path(self, base: Path) -> Path:
        """
        Return a non-existent path by appending _1, _2 etc.
        e.g. pics/cat.png  ->  pics/cat_1.png
        :param base:
        :return:
        """
        stem, suffix = base.stem, base.suffix
        parent = base.parent

        counter = 1
        while True:
            candidate = parent / f"{stem}_{counter}{suffix}"
            if not candidate.exists():
                return candidate
            counter += 1


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

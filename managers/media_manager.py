# TODO reorganize this file
from __future__ import annotations

import json
import logging
import os
import time
import uuid
from collections import deque, OrderedDict
from pathlib import Path
from typing import Callable, List

from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool, Qt, Slot
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont

from workers.scan_worker import ScanWorker, ScanResult
from workers.thumb_worker import ThumbWorker
from .base import BaseManager

from widgets.collision_dialog import CollisionDialog
from .dao import MediaDAO

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}
_CACHE_CAPACITY = 512
_THUMB_CACHE: "OrderedDict[tuple[str, int], QPixmap]" = OrderedDict()

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


def decorate_stack_badge(base: QPixmap) -> QPixmap:
    """
    Paint a small purple 'S' badge in the bottom right corner
    :param base:
    :return: New QPixmap (leaves original untouched)
    """
    badge = max(12, base.width() // 6)  # scale with thumb
    result = QPixmap(base)  # shallow copy
    painter = QPainter(result)

    # circle
    radius = badge // 2
    x = base.width() - badge - 2
    y = base.height() - badge - 2
    painter.setBrush(QColor("#5e5eff"))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(x, y, badge, badge)

    # white 'S'
    painter.setPen(Qt.white)
    f = QFont()
    f.setBold(True)
    f.setPixelSize(badge - 4)
    painter.setFont(f)
    painter.drawText(x, y, badge, badge, Qt.AlignCenter, "S")

    painter.end()
    return result


class MediaManager(BaseManager, QObject):
    """
    Thread-aware loader for image assets, currently only processes images
    """

    scan_finished = Signal(list)
    thumb_ready = Signal(str, object)
    renamed = Signal(str, str)

    def __init__(self, conn, undo_manager, thumb_size: int = 256, parent=None):
        BaseManager.__init__(self, conn)
        QObject.__init__(self, parent)

        self.dao = MediaDAO(conn)
        self.undo_manager = undo_manager

        self.thumb_size = thumb_size
        self.pool = QThreadPool.globalInstance()

        logger.info("Media manager initialized")

    # DB helpers (sync)
    def add_media(self, path: str) -> int:
        """
        Adds the given path to database
        """
        return self.dao.insert_media(path)

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
        Begin an async scan; results arrive in _on_scan_completed().
        :param folder:
        :return:
        """
        root = Path(folder).expanduser().resolve()
        logger.info("Scanning folder %s", root)

        worker = ScanWorker(root, self.dao)  # dao does the inserts
        worker.finished.connect(self._on_scan_completed)
        self.pool.start(worker)

    def thumb(self, path: str | Path) -> None:
        path = str(path)

        # cache hit
        cached = _thumbnail_cache_get(path, self.thumb_size)
        if cached is not None:
            self.thumb_ready.emit(path, cached)
            return

        # decide badge in the GUI thread
        row = self.dao.fetchone(
            "SELECT id FROM media WHERE path=?", (path,)
        )
        decorate = bool(row and self.dao.is_stacked_base(row["id"]))

        # worker callback does NO DB access
        def _emit(p: str, pix: QPixmap):
            if decorate:
                pix = decorate_stack_badge(pix)
            _thumbnail_cache_set(p, self.thumb_size, pix)
            self.thumb_ready.emit(p, pix)  # Qt queues to GUI thread

        self.pool.start(ThumbWorker(path, self.thumb_size, _emit))

    # ---------------------------- db backup management methods

    def _safe_overwrite(self, old_path: Path, new_path: Path) -> bool:
        """
        1. Move destination file -> backup.
        2. Move source file -> destination.
        3. Update DB rows inside ONE transaction.
        4. Push UndoEntry with backup so it can be fully restored.
        Signals emitted for both moves so all views update instantly.
        """
        logger = logging.getLogger(__name__)
        backup_path = self._backup_path(new_path)

        try:
            # -- A: FILE SYSTEM
            # move dest -> backup  (may not exist ; catch FileNotFound)
            if new_path.exists():
                new_path.replace(backup_path)
                # UI: dest has disappeared (new -> backup)
                self.renamed.emit(str(new_path), str(backup_path))

            # move src -> dest
            old_path.replace(new_path)
            # UI: src now at dest
            self.renamed.emit(str(old_path), str(new_path))

            # -- B: DATABASE (single atomic scope)
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

            # -- C: Logging & undo
            _log_rename(str(old_path), str(new_path))
            if self.undo_manager:
                self.undo_manager.push(str(old_path), str(new_path),
                                       backup=str(backup_path))
            return True

        except Exception as exc:
            logger.error("Safe overwrite failed: %s", exc)
            # Best-effort roll-back (TODO add more elaborate recovery)
            return False

    def _backup_path(self, original: Path) -> Path:
        bk_dir = Path.home() / "OculusBackups" / "overwritten"
        bk_dir.mkdir(parents=True, exist_ok=True)
        return bk_dir / f"{uuid.uuid4()}{original.suffix}"

    def restore_overwrite(self, entry) -> bool:
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

            # Restore backup -> new_path
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

    def _on_thumb_complete(self, path: str, pix: QPixmap, decorate: bool) -> None:
        """
        Receive raw pixmap from worker, decorate if stacked, then cache and emit.
        :param path: Path to media
        :param pix: pixmap representing the media's thumbnail
        :return: None
        """
        if decorate:
            pix = decorate_stack_badge(pix)

        _thumbnail_cache_set(path, self.thumb_size, pix)
        # Emit is thread-safe; Qt delivers to UI thread
        self.thumb_ready.emit(path, pix)

    # ----------------------------- Path Getters

    def all_paths(self, *, files_only: bool = True) -> list[str]:
        """
        Return every path currently in the DB (files by default).
        :param files_only: If false, function will also return directory paths
        :return:
        """
        return self.dao.all_paths(files_only=files_only)

    def folder_paths(self) -> list[str]:
        return self.dao.folder_paths()

    def root_folders(self) -> list[str]:
        """
        Folders whose parent directory is NOT itself recorded
        :return:
        """
        return self.dao.root_folders()

    # ----------------------------- Sorting

    def get_sorted_paths(self, sort_key: str, ascending: bool = True) -> list[str]:
        """
        :param sort_key: Key to sort by
        :param ascending: Return sort in ascending order
        :return:
        """
        return self.dao.get_sorted_paths(sort_key, ascending)

    def order_subset(self, subset: list[str], sort_key: str, asc: bool) -> list[str]:
        """
        Return subset of paths ordered by the same criteria
        used in get_sorted_paths(). Items not found in the DB are appended unchanged
        """
        return self.dao.order_subset(subset, sort_key, asc)

    # ----------------------------- Variant Management

    def add_variant(self, base_id: int, variant_id: int, rank: int) -> None:
        """
        Insert variant with explicit rank (_vN suffix), if the rank exists, skip (prevents duplicates).
        """
        self.dao.add_variant(base_id, variant_id, rank)

    def is_variant(self, path: str) -> bool:
        """
        True if this path is NOT the base but belongs to a stack.
        :param path:
        :return:
        """
        return self.dao.is_variant(path)

    def _is_stacked(self, media_id: int) -> bool:
        """
        Return True if this media_id has at least one variant.
        :param media_id: media to check
        :return: boolean representing if this media_id has at least one variant.
        """
        return self.dao.is_stacked(media_id)

    def _is_stacked_base(self, media_id: int) -> bool:
        """
        True if this media_id is the base (rank 0) of a stack.
        :param media_id:
        :return:
        """
        return self.dao.is_stacked_base(media_id)

    def detect_and_stack(self, media_id: int, path: str) -> None:
        """
        Auto-stack when filename ends with _vN before the extension. Base file must exist without the suffix.
        :param media_id:
        :param path:
        :return:
        """
        self.dao.detect_and_stack(media_id, path)

    def _stack_ids_for_base(self, base_id: int) -> List[int]:
        return self.dao.stack_ids_for_base(base_id)

    def stack_paths(self, path: str) -> List[str]:
        """
        :param path: Media to check
        :return: An ordered list [base, v1, v2, ...] for any path. If the file isn’t stacked, returns [path].
        """
        return self.dao.stack_paths(path)

    # ----------------------------- Misc
    @Slot(object)
    def _process_scan_result(self, items):
        logger.info("Processing scan result")
        seen_dirs = set()
        for p, sz in items:

            # add (or fetch) media row and capture its id
            media_id = self.add_media(p)

            # auto-detect variant relationship, if any
            self.detect_and_stack(media_id, str(p))

            # Ensure parent folder exists in DB
            parent = str(Path(p).parent)
            if parent not in seen_dirs:
                self.add_media(parent)
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

    def get_attr(self, media_id: int) -> dict:
        """
        Return favorite, weight, artist as a dict.
        """
        return self.dao.get_attr(media_id)

    def set_attr(self, media_id: int, **kwargs):
        """
        Update one or more scalar attributes for the given media_id.
        Example: set_attr(5, favorite=1, weight=0.8, artist='John')
        """
        self.dao.set_attr(media_id, **kwargs)


# Thread tasks
@Slot(object)
def _on_scan_completed(self, result: ScanResult):
    logger.info("Scan finished: added %d, skipped %d (%.1fs)",
                result.added, result.skipped, result.duration)
    self.scan_finished.emit(result)


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

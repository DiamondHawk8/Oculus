from __future__ import annotations

import logging
from collections import deque
from pathlib import Path
from typing import List

from PySide6.QtCore import QObject, Signal, QThreadPool, Qt
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont

from services.comment_service import CommentService
from services.rename_service import RenameService
from services.variant_service import VariantService
from services.import_service import ImportService

from workers.thumb_worker import ThumbWorker

from .dao import MediaDAO
from .utils.thumb_cache import ThumbCache

MEDIA_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".mp4", ".mkv", ".webm", ".mov", ".avi"}
logger = logging.getLogger(__name__)


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


class MediaManager(QObject):
    """
    Thread-aware loader for image assets, currently only processes images
    """

    scan_finished = Signal(list)
    thumb_ready = Signal(str, object)
    renamed = Signal(str, str)
    import_finished = Signal(object)

    def __init__(self, conn, undo_manager, thumb_size: int = 256, parent=None):
        QObject.__init__(self, parent)

        self.dao = MediaDAO(conn)
        self.variants = VariantService(self.dao)
        self.comments = CommentService(self.dao)
        self.pool = QThreadPool.globalInstance()

        self.importer = ImportService(self.dao, self.variants, self.pool)
        self.rename_service = RenameService(self.dao)
        undo_manager.set_rename_service(self.rename_service)
        self.rename_service.attach_undo_manager(undo_manager)

        self.undo_manager = undo_manager

        self.importer.import_completed.connect(self.import_finished)
        self.rename_service.renamed.connect(self.renamed)

        self.thumb_size = thumb_size
        self.cache = ThumbCache(capacity=512)

        logger.info("Media manager initialized")

    def add_media(self, path: str, st) -> int:
        """
        Adds the given path to database
        """
        return self.dao.insert_media(path, st)

    def update_media_path(self, mid: int, new_path: str, mtime: int) -> None:
        self.dao.update_media_path(mid, new_path, mtime)

    def fetch_many_inodes(self, inodes: list[int]) -> dict[int, tuple[int, str]]:
        """
        Return {inode: (id, path)} for any rows whose inode is in inodes.
        """
        return self.dao.fetch_many_inodes(inodes)

    def get_media_id(self, path: str) -> int | None:
        row = self.dao.fetchone("SELECT id FROM media WHERE path=?", (path,))
        return row["id"] if row else None

    def scan_folder(self, folder: str | Path) -> None:
        """
        Begin an async scan; results arrive in _on_scan_completed().
        :param folder:
        :return:
        """
        self.importer.scan(Path(folder))

    # ----------------------------- Path Getters -----------------------------

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

    def path_for_id(self, media_id: int) -> str | None:
        return self.dao.path_for_id(media_id)

    def folder_for_id(self, media_id: int) -> Path | None:
        return self.dao.folder_for_id(media_id)

    # ----------------------------- Sorting -----------------------------

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

    # ----------------------------- Variant Management -----------------------------

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

    def is_stacked(self, media_id: int) -> bool:
        """
        Return True if this media_id has at least one variant.
        :param media_id: media to check
        :return: boolean representing if this media_id has at least one variant.
        """
        return self.dao.is_stacked(media_id)

    def is_stacked_base(self, media_id: int) -> bool:
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
        return self.variants.stack_paths(path)

    # ----------------------------- Renaming logic -----------------------------

    def rename_media(self, old_abs: str, new_abs: str) -> bool:
        return self.rename_service.rename(old_abs, new_abs)

    def overwrite_media(self, old_abs: str, new_abs: str) -> bool:
        return self.rename_service.overwrite(old_abs, new_abs)

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
                elif child.suffix.lower() in MEDIA_EXT:
                    imgs.append(str(child))
            tree[str(folder)] = (sub, imgs)
        return tree

    # ----------------------------- Preset Management -----------------------------
    def list_presets_for_media(self, media_id: int):
        return self.dao.list_presets_for_media(media_id)

    def list_presets_in_group(self, group_id: str):
        return self.dao.list_presets_in_group(group_id)

    def update_preset_transform(self, group_id: str, zoom: float, pan_x: int, pan_y: int):
        self.dao.execute(
            "UPDATE presets SET zoom=?, pan_x=?, pan_y=? WHERE group_id=?",
            (zoom, pan_x, pan_y, group_id)
        )

    def rename_preset_group(self, group_id: str, new_name: str):
        self.dao.execute(
            "UPDATE presets SET name=? WHERE group_id=?", (new_name, group_id)
        )

    def preset_name_exists(self, media_id: int, new_name: str, exclude_gid: str):
        return self.dao.fetchone(
            """SELECT 1 FROM presets
               WHERE name=? AND group_id<>? AND media_id IS NOT NULL""",
            (new_name, exclude_gid)
        ) is not None

    def set_default_preset(self, media_id: int | None, group_id: str):
        self.dao.execute("UPDATE presets SET is_default=0 WHERE media_id IS ?", (media_id,))
        self.dao.execute("UPDATE presets SET is_default=1 WHERE group_id=?", (group_id,))

    def update_hotkey(self, group_id: str, hotkey: str | None):
        self.dao.execute("UPDATE presets SET hotkey=? WHERE group_id=?", (hotkey, group_id))

    def hotkey_clash(self, media_id: int, group_id: str, hotkey: str):
        return self.dao.fetchone(
            """SELECT 1 FROM presets
               WHERE hotkey=? AND media_id=? AND group_id<>?""",
            (hotkey, media_id, group_id)
        ) is not None

    # ----------------------------- Other metadata logic -----------------------------

    def default_view_state(self, media_id: int):
        return self.dao.fetchone(
            "SELECT zoom, pan_x, pan_y FROM presets "
            "WHERE media_id=? AND is_default=1", (media_id,)
        )

    def preset_shortcuts(self, media_id: int):
        return self.dao.fetchall(
            "SELECT zoom, pan_x, pan_y, hotkey FROM presets "
            "WHERE media_id=? AND hotkey IS NOT NULL", (media_id,)
        )

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

    def thumb(self, path: str | Path) -> None:
        path = str(path)
        cached = self.cache.get(path, self.thumb_size)
        if cached is not None:
            self.thumb_ready.emit(path, cached)
            return

        row = self.dao.fetchone("SELECT id FROM media WHERE path=?", (path,))
        decorate = bool(row and self.is_stacked_base(row["id"]))

        # worker callback does NO DB access
        def _emit(p: str, pix: QPixmap):
            if decorate:
                pix = decorate_stack_badge(pix)
            self.cache.set(p, self.thumb_size, pix)
            self.thumb_ready.emit(p, pix)  # Qt queues to GUI thread

        self.pool.start(ThumbWorker(path, self.thumb_size, _emit))

    # ----------------------------- Bookmarks -----------------------------

    def bookmarks_for_path(self, path: str) -> list[int]:
        return self.dao.bookmarks_for_path(path)

    def add_bookmark(self, path: str, ms: int) -> None:
        self.dao.add_bookmark(path, ms)

    def delete_bookmark(self, path: str, ms: int) -> None:
        self.dao.delete_bookmark(path, ms)

    # Temp saving method
    def export_bookmarks_json(self, outfile: str) -> None:
        import json
        rows = self.dao.cur.execute("SELECT path, time_ms FROM bookmarks").fetchall()
        data: dict[str, list[int]] = {}
        for r in rows:
            data.setdefault(r["path"], []).append(r["time_ms"])
        with open(outfile, "w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2)

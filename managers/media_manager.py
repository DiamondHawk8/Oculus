from __future__ import annotations

import os
from pathlib import Path
from collections import deque
from typing import Iterable, Callable, List, Sequence

from functools import lru_cache

from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool, Qt, QMetaObject
from PySide6.QtGui import QPixmap

from collections import OrderedDict


class MediaManager(QObject):
    """
    Thread-aware loader for image assets, currently only processes images
    """

    scan_finished = Signal(list)  # list[str]
    thumb_ready = Signal(str, object)  # (path, QPixmap)

    IMAGE_SUFFIXES: Sequence[str] = (".png", ".jpg", ".jpeg", ".bmp", ".gif")

    def __init__(self, thumb_size: int = 256, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._pool: QThreadPool = QThreadPool.globalInstance()
        self._thumb_size = thumb_size

    def scan_folder(self, folder: str | Path) -> None:
        """
        This method returns immediately; results are delivered via scan_finished
        """
        folder = Path(folder).expanduser().resolve()
        task = _ScanTask(folder, self._on_scan_complete)
        self._pool.start(task)

    def thumb(self, path: str | Path) -> None:
        """
        Ensure a thumbnail for *path* is available and emit *thumb_ready*.
        """
        path_str = str(path)

        # Fast path – already cached
        cached = _thumbnail_cache_get(path_str, self._thumb_size)
        if cached is not None:
            self.thumb_ready.emit(path_str, cached)
            return

        # Slow path – go off-thread
        task = _ThumbTask(path_str, self._thumb_size, self._on_thumb_complete)
        self._pool.start(task)

    def _on_scan_complete(self, paths: list[str]) -> None:
        # Emit directly: Qt will queue to the main thread because MediaManager
        # lives in the GUI thread and this call originates in a worker thread.
        self.scan_finished.emit(paths)

    def _on_thumb_complete(self, path: str, pix: QPixmap) -> None:
        _thumbnail_cache_set(path, self._thumb_size, pix)
        self.thumb_ready.emit(path, pix)

    def walk_tree(self, root: str | Path) -> dict[str, tuple[list[str], list[str]]]:
        """
        Return an adjacency map of the folder hierarchy.

        Dict key: absolute folder path
        Value tuple: (subfolders[abs], image_files[abs])

        Debug
        """
        root = Path(root).expanduser().resolve()
        tree: dict[str, tuple[list[str], list[str]]] = {}

        q: deque[Path] = deque([root])
        while q:
            folder = q.popleft()
            subdirs, images = [], []
            for child in folder.iterdir():
                if child.is_dir():
                    subdirs.append(str(child))
                    q.append(child)       # breadth-first
                elif child.suffix.lower() in {".jpg", ".png", ".gif", ".bmp"}:
                    images.append(str(child))
            tree[str(folder)] = (subdirs, images)
        return tree


class _ScanTask(QRunnable):
    """QRunnable that walks folder and reports image paths via callback"""

    def __init__(self, folder: Path, callback: Callable[[List[str]], None]) -> None:
        super().__init__()
        self.folder = folder
        self.callback = callback
        self.setAutoDelete(True)

    def run(self) -> None:  # executes in worker thread
        paths: List[str] = []
        for root, _, files in os.walk(self.folder):
            for fn in files:
                if fn.lower().endswith(MediaManager.IMAGE_SUFFIXES):
                    paths.append(str(Path(root) / fn))
        self.callback(paths)


class _ThumbTask(QRunnable):
    """deliver a thumbnail, executed off the GUI thread."""

    def __init__(self, path: str, size: int, callback: Callable[[str, QPixmap], None], ) -> None:
        super().__init__()
        self._path = path
        self._size = size
        self._callback = callback
        self.setAutoDelete(True)

    def run(self) -> None:
        pix = _generate_thumbnail(self._path, self._size)
        if not pix.isNull():
            self._callback(self._path, pix)


# ------------ Can be adjusted

_CACHE_CAPACITY = 512
_THUMB_CACHE: "OrderedDict[tuple[str, int], QPixmap]" = OrderedDict()


def _thumbnail_cache_get(path: str, size: int) -> QPixmap | None:
    key = (path, size)
    pix = _THUMB_CACHE.get(key)
    if pix is not None:
        # Move to end -> marks as recently used
        _THUMB_CACHE.move_to_end(key)
    return pix


def _thumbnail_cache_set(path: str, size: int, pix: QPixmap) -> None:
    key = (path, size)
    _THUMB_CACHE[key] = pix
    _THUMB_CACHE.move_to_end(key)
    if len(_THUMB_CACHE) > _CACHE_CAPACITY:
        _THUMB_CACHE.popitem(last=False)  # discard oldest


def _generate_thumbnail(path: str, size: int) -> QPixmap:
    pix = QPixmap(path)
    if pix.isNull():
        return QPixmap()
    return pix.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

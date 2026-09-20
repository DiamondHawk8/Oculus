import os
import time
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QRunnable, Signal, QObject

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".mp4", ".mkv", ".webm", ".mov", ".avi"}


@dataclass(frozen=True)
class ScannedFile:
    path: str
    stat: os.stat_result


@dataclass(frozen=True)
class ScanResult:
    root: Path
    files: list[ScannedFile]
    duration: float


class ScanWorker(QRunnable, QObject):
    finished = Signal(object)

    def __init__(self, root: Path):
        QRunnable.__init__(self)
        QObject.__init__(self)
        self.root = root
        self.setAutoDelete(True)

    def run(self):
        start = time.time()
        found: list[ScannedFile] = []
        for dirpath, _, files in os.walk(self.root):
            for fn in files:
                if Path(fn).suffix.lower() in IMAGE_EXT:
                    path = str(Path(dirpath) / fn)
                    try:
                        # Stat on the worker thread; large network collections
                        # should not perform this I/O after returning to the UI.
                        found.append(ScannedFile(path, os.stat(path, follow_symlinks=False)))
                    except OSError:
                        continue
        self.finished.emit(
            ScanResult(self.root, found, time.time() - start)
        )

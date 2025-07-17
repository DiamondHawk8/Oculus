import os
import time
from pathlib import Path

from PySide6.QtCore import QRunnable, Signal, QObject

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".mp4", ".mkv", ".mov", ".avi"}


class ScanResult:
    def __init__(self, root: Path, files: list[str], duration: float):
        self.root = root
        self.files = files
        self.duration = duration


class ScanWorker(QRunnable, QObject):
    finished = Signal(object)

    def __init__(self, root: Path):
        QRunnable.__init__(self)
        QObject.__init__(self)
        self.root = root
        self.setAutoDelete(True)

    def run(self):
        start = time.time()
        found = []
        for dirpath, _, files in os.walk(self.root):
            for fn in files:
                print(fn)
                if Path(fn).suffix.lower() in IMAGE_EXT:
                    print(str(Path(dirpath) / fn))
                    found.append(str(Path(dirpath) / fn))
        self.finished.emit(
            ScanResult(self.root, found, time.time() - start)
        )

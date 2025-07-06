from __future__ import annotations

import os
import time
from pathlib import Path

from PySide6.QtCore import QRunnable, Signal, QObject

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}


class ScanResult:
    def __init__(self, root: Path, added: int, skipped: int, duration: float):
        self.root = root
        self.added = added
        self.skipped = skipped
        self.duration = duration


class ScanWorker(QRunnable, QObject):
    finished = Signal(object)

    def __init__(self, root: Path, dao):
        QRunnable.__init__(self)
        QObject.__init__(self)
        self.root = root
        self.dao = dao
        self.setAutoDelete(True)

    def run(self):
        start = time.time()
        added = skipped = 0

        for dirpath, _, files in os.walk(self.root):
            for fn in files:
                if Path(fn).suffix.lower() in IMAGE_EXT:
                    full = str(Path(dirpath) / fn)
                    mid = self.dao.insert_media(full)
                    if mid:
                        added += 1
                    else:
                        skipped += 1

        self.finished.emit(
            ScanResult(self.root, added, skipped, time.time() - start)
        )

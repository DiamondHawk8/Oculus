from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPixmap, QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QStackedLayout,
    QWidget,
)



class MediaRenderer(QWidget):

    supports_presets = True

    # --- mandatory API -----------------------------------------------------
    def load(self, path: str):
        raise NotImplementedError

    def zoom(self, factor: float, anchor: Optional[QPoint] = None):
        raise NotImplementedError

    def fit_to(self):
        raise NotImplementedError

    def move_to(self, dx: int, dy: int):
        raise NotImplementedError


class ImageRenderer(MediaRenderer):
    """Temporary static‑image renderer with **no** zoom/pan yet.

    It simply shows the image inside an internal QLabel, scaled to fit the
    widget whilst preserving aspect ratio.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignCenter)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._label, 1)

    # ------------------------------------------------------------------ API
    def load(self, path: str):
        pix = QPixmap(path)
        self._label.setPixmap(pix)
        self._label.adjustSize()

    def zoom(self, factor: float, anchor: Optional[QPoint] = None):
        pass  # not implemented yet

    def fit_to(self):
        pass  # not implemented yet

    def move_to(self, dx: int, dy: int):
        pass  # not implemented yet

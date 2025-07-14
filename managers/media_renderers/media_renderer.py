
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


# MediaViewerDialog - replacement for the old ImageViewerDialog



class MediaViewerDialog(QDialog):

    # ------------------------------------------------------------------ ctor
    def __init__(
        self,
        paths: List[str],
        cur_idx: int,
        media_manager,
        tag_manager,
        stack: Optional[List[str]] = None,
        selected_path: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Media Viewer")
        self.setWindowFlag(Qt.Window)
        self.resize(900, 600)

        # --- data -------------------------------------------------------
        self._paths: List[str] = paths
        self._idx: int = cur_idx
        self._stack: List[str] = stack or []
        self._media_manager = media_manager
        self._tag_manager = tag_manager

        self._current_path: str = selected_path or self._paths[self._idx]

        # --- UI ---------------------------------------------------------
        self._renderer = ImageRenderer(self)
        self._stacked = QStackedLayout()
        self._stacked.addWidget(self._renderer)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addLayout(self._stacked, 1)

        # Initial render
        self._show_current()

        self.show()

    def load_new_stack(
        self,
        paths: List[str],
        cur_idx: int,
        stack: Optional[List[str]] = None,
    ) -> None:
        self._paths = paths
        self._idx = cur_idx
        self._stack = stack or []
        self._show_current()
        self.raise_()
        self.activateWindow()

    # ------------------------------------------------------------------ internals
    def _show_current(self):
        if not self._paths:
            return
        self._current_path = self._paths[self._idx]
        self._renderer.load(self._current_path)

    def _step(self, delta: int):
        if not self._paths:
            return
        self._idx = (self._idx + delta) % len(self._paths)
        self._show_current()

    # ------------------------------------------------------------------ events
    def keyPressEvent(self, ev: QKeyEvent):
        if ev.key() == Qt.Key_Right:
            self._step(+1)
            return
        if ev.key() == Qt.Key_Left:
            self._step(-1)
            return
        if ev.key() == Qt.Key_Escape:
            self.close()
            return
        super().keyPressEvent(ev)

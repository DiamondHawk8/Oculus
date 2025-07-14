from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QStackedLayout,
    QWidget,
)

from widgets.media_renderers.media_renderer import ImageRenderer
# type: ignore


class MediaViewerDialog(QDialog):

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
        self.resize(900, 600)

        # --- navigation data
        self._paths = paths[:]
        self._idx = cur_idx
        self._stack = stack or []
        self._media_manager = media_manager
        self._tag_manager = tag_manager

        self._current_path = selected_path or self._paths[self._idx]

        # --- UI
        self._renderer = ImageRenderer(self)
        self._stacked = QStackedLayout()
        self._stacked.addWidget(self._renderer)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addLayout(self._stacked, 1)

        # first display
        self._show_current()
        self.show()

    # public API
    def load_new_stack(
        self,
        paths: List[str],
        cur_idx: int,
        stack: Optional[List[str]] = None,
    ) -> None:
        self._paths = paths[:]
        self._idx = cur_idx
        self._stack = stack or []
        self._show_current()
        self.raise_()
        self.activateWindow()

    # helpers
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

    # events
    def keyPressEvent(self, ev: QKeyEvent):
        match ev.key():
            case Qt.Key_Right:
                self._step(+1)
            case Qt.Key_Left:
                self._step(-1)
            case Qt.Key_Escape:
                self.close()
            case _:
                super().keyPressEvent(ev)

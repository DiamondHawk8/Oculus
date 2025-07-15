from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QStackedLayout,
    QWidget, QApplication,
)

from widgets.media_renderers.media_renderer import ImageRenderer

BACKDROP_CSS = "background-color: rgba(0, 0, 0, 180);"  # 70 % black


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

        # ----- Window aesthetics
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")

        # Auto‑size to screen
        scr = self.screen() or QApplication.primaryScreen()
        self.resize(scr.availableGeometry().size())

        # navigation data
        self._paths = paths[:]
        self._idx = cur_idx % len(self._paths) if self._paths else 0
        self._stack = stack or []
        self._media_manager = media_manager
        self._tag_manager = tag_manager
        self._variant_pos: dict[str, int] = {}

        self._current_path = selected_path or self._paths[self._idx]

        # --- UI
        self._renderer = ImageRenderer(self)
        self._stacked = QStackedLayout()
        self._stacked.addWidget(self._renderer)

        # Backdrop widget fills entire dialog area with dark css
        self._backdrop = QWidget(self)
        self._backdrop.setStyleSheet(BACKDROP_CSS)

        lay = QHBoxLayout(self._backdrop)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addLayout(self._stacked, 1)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._backdrop, 1)

        # first display
        self._show_current()
        self.show()

    # public API
    def load_new_stack(self, paths: List[str], cur_idx: int, stack: Optional[List[str]] = None,) -> None:
        self._paths = paths[:]
        self._idx = cur_idx % len(self._paths) if self._paths else 0
        self._stack = stack or []
        self._variant_pos.clear()
        self._show_current()
        self.raise_()
        self.activateWindow()

    # helpers
    def _show_current(self):
        if not self._paths:
            return

        self._current_path = self._paths[self._idx]
        self._renderer.load(self._current_path)

        # If the current path belongs to the known stack, remember index
        if self._stack and self._current_path in self._stack:
            self._variant_pos[self._stack[0]] = self._stack.index(self._current_path)

    def _step(self, delta: int):
        if not self._paths:
            return
        self._idx = (self._idx + delta) % len(self._paths)
        self._show_current()

    def _cycle_variant(self, delta: int):
        if not self._stack or self._current_path not in self._stack:
            return  # nothing to cycle
        root = self._stack[0]
        pos = self._variant_pos.get(root, 0)
        pos = (pos + delta) % len(self._stack)
        self._variant_pos[root] = pos
        self._current_path = self._stack[pos]
        self._renderer.load(self._current_path)

    # events
    def keyPressEvent(self, ev: QKeyEvent):
        match ev.key():
            case Qt.Key_Right:
                self._step(+1)
            case Qt.Key_Left:
                self._step(-1)
            case Qt.Key_Down:
                self._cycle_variant(+1)
            case Qt.Key_Up:
                self._cycle_variant(-1)
            case Qt.Key_Escape:
                self.close()
            case _:
                super().keyPressEvent(ev)

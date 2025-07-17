from typing import List, Optional

from PySide6.QtCore import Qt, QPoint, QTimer
from PySide6.QtGui import QKeyEvent, QShortcut, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QStackedLayout,
    QWidget,
)

from widgets.media_renderers.media_renderer import ImageRenderer
from widgets.metadata_dialog import MetadataDialog

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

        # ----- Window aesthetics ------------------------------------------------------
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")

        scr = self.screen() or QApplication.primaryScreen()
        self.resize(scr.availableGeometry().size())
        self.showFullScreen()

        # navigation data
        self._paths = paths[:]
        self._idx = cur_idx % len(self._paths) if self._paths else 0
        self._stack = stack or []
        self._media_manager = media_manager
        self._tag_manager = tag_manager
        self._variant_pos: dict[str, int] = {}

        # Track which media have already had their default preset applied
        self._applied_default: set[int] = set()
        self._dyn_presets: List[QShortcut] = []

        self._current_path = selected_path or self._paths[self._idx]
        if self._stack and self._current_path in self._stack:
            self._variant_pos[self._stack[0]] = self._stack.index(self._current_path)

        # --- UI ------------------------------------------------------
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

        QShortcut(QKeySequence("Ctrl+P"), self).activated.connect(
            lambda: self._open_metadata_dialog()
        )

        # first display
        self._show_current()

    # public API
    def load_new_stack(
            self,
            paths: List[str],
            cur_idx: int,
            stack: Optional[List[str]] = None,
    ) -> None:
        self._paths = paths[:]
        self._idx = cur_idx % len(self._paths) if self._paths else 0
        self._stack = stack or []
        self._variant_pos.clear()
        self._show_current()
        self.raise_()
        self.activateWindow()

    # helpers
    def _refresh_stack_for_current(self):
        """
        Update self._stack from media_manager if possible.
        :return:
        """
        if hasattr(self._media_manager, "stack_paths"):
            new_stack = self._media_manager.stack_paths(self._current_path)
            if new_stack:
                self._stack = new_stack

    def _show_current(self):
        if not self._paths:
            return

        self._current_path = self._paths[self._idx]
        self._renderer.load(self._current_path)
        self._refresh_stack_for_current()

        # If the current path belongs to the known stack, remember index
        if self._stack and self._current_path in self._stack:
            self._variant_pos[self._stack[0]] = self._stack.index(self._current_path)

        # Apply default preset + build shortcuts
        media_id = self._media_manager.get_media_id(self._current_path) if hasattr(self._media_manager,
                                                                                   "get_media_id") else None
        if media_id:
            if media_id not in self._applied_default:
                #  delay default preset until all resize events are done
                QTimer.singleShot(
                    0,
                    lambda mid=media_id: self._apply_default_preset(mid),
                )
            self._create_dynamic_shortcuts(media_id)

    def _apply_view_state(self, zoom: float, pan: QPoint):
        """
        Apply absolute zoom and pan from a zoom, (x, y) format
        :param zoom:
        :param pan:
        :return:
        """
        if zoom and zoom != self._renderer._scale:
            self._renderer.zoom(zoom / self._renderer._scale)
        self._renderer.move_to(pan.x(), pan.y())

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

    # ------- Preset helpers --------------------------------------
    def _apply_default_preset(self, media_id: int):
        if media_id in self._applied_default:
            return

        row = self._media_manager.default_view_state(media_id)
        if row:
            self._apply_view_state(
                row["zoom"],
                QPoint(row["pan_x"], row["pan_y"]),
            )
        self._applied_default.add(media_id)
        self._renderer.print_offset()

    def _clear_dynamic_shortcuts(self):
        for sc in self._dyn_presets:
            sc.setParent(None)
        self._dyn_presets.clear()

    def _create_dynamic_shortcuts(self, media_id: int):
        self._clear_dynamic_shortcuts()
        for r in self._media_manager.preset_shortcuts(media_id) or []:
            seq = QKeySequence(r["hotkey"])
            if seq.isEmpty():
                continue
            sc = QShortcut(seq, self)  # bind to dialog, not renderer
            sc.activated.connect(
                lambda z=r["zoom"], x=r["pan_x"], y=r["pan_y"]:
                self._apply_view_state(z, QPoint(x, y))
            )
            self._dyn_presets.append(sc)

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

    def _open_metadata_dialog(self):
        self._renderer.print_offset()
        if not self._paths:
            return
        z = self._renderer._scale
        pos = self._renderer._offset.toPoint()
        dlg = MetadataDialog(
            [self._current_path],
            self._media_manager,
            self._tag_manager,
            parent=self.window(),
            default_transform=(z, pos.x(), pos.y()),
            viewer=self,
        )
        dlg.exec()

    def refresh(self):
        self._show_current()


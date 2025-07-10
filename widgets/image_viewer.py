from pathlib import Path

from PySide6.QtCore import Qt, QSize, QPoint, QEvent
from PySide6.QtGui import QPixmap, QShortcut, QKeySequence
from PySide6.QtWidgets import QDialog, QLabel, QWidget

from widgets.comments_panel import CommentsPanel
from widgets.metadata_dialog import MetadataDialog
import logging

logger = logging.getLogger(__name__)


class ImageViewerDialog(QDialog):
    BACKDROP_CSS = "background-color: rgba(0, 0, 0, 180);"  # 70 % black

    def __init__(self, paths, cur_idx, media_manager, tag_manager, stack, selected_path=None, parent=None):
        super().__init__(parent)

        self._paths = list(paths)
        self._idx = cur_idx
        self._media_manager = media_manager
        self._tag_manager = tag_manager
        self._stack = stack

        self._view_states: dict[str, tuple[float, QPoint]] = {}
        self._variant_pos: dict[str, int] = {}
        self._scale = 1.0  # 1.0 = fit-to-window
        self._fit_scale = 1.0  # how much to scale to fit dialog
        self._fit_to_win = True  # start in fit mode
        self._pix: QPixmap | None = None
        self._dragging = False
        self._last_pos = QPoint()

        self._drag_start_cursor = QPoint()
        self._drag_start_label = QPoint()

        # Window setup
        self.setWindowFlag(Qt.FramelessWindowHint, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # ---- backdrop ---------------------------------------------------
        # fills entire dialog
        self._backdrop = QWidget(self)
        self._backdrop.setStyleSheet(self.BACKDROP_CSS)
        # push it behind everything
        self._backdrop.lower()

        # ---- image label -----------------------------------------------
        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setStyleSheet("background: transparent;")
        # needed for panning
        self._label.setMouseTracking(True)
        self._label.installEventFilter(self)

        self._meta_shortcut = QShortcut(QKeySequence("Ctrl+P"), self._label)
        self._meta_shortcut.activated.connect(self._open_metadata_dialog)

        # ---- comments --------------------------------------------------
        self.comments_panel = CommentsPanel(media_manager.comments, self)
        self.comments_panel.hide()

        # ---- load & show -----------------------------------------------
        self.showFullScreen()

        first_path = selected_path or self._paths[self._idx]
        self._current_path = first_path
        # If variant, save the position
        if first_path in stack and first_path != stack[0]:
            self._variant_pos[stack[0]] = stack.index(first_path)

        self._load_image(first_path)

        # Temp nudge work around
        QShortcut(QKeySequence("Alt+A"), self).activated.connect(
            lambda: self._nudge(Qt.Key_Left)
        )
        QShortcut(QKeySequence("Alt+D"), self).activated.connect(
            lambda: self._nudge(Qt.Key_Right)
        )
        QShortcut(QKeySequence("Ctrl+/"), self).activated.connect(
            lambda: self._toggle_comments()
        )
        QShortcut(QKeySequence("Ctrl+Shift+/"), self).activated.connect(
            lambda: self.comments_panel.toggle_input()
        )

    def current_media_id(self) -> int | None:
        """
        Return DB id of the image currently displayed.
        :return:
        """
        return self._media_manager.get_media_id(self._current_path)

    def _load_image(self, path: str):
        """
        Load image from given path. Displays white, if not found
        :param path: path to image
        :return:
        """
        logger.info(f"Loading image from {path}")
        pix = QPixmap(path)
        if pix.isNull():
            logger.error("Could not load image %s", path)
            self._label.setText(f"Could not load\n{Path(path).name}")
            self._label.setStyleSheet("color:white; background:transparent;")
            self._pix = None
            return

        self._pix = pix
        self._current_path = path

        # Check session cache
        if self._current_path in self._view_states:
            self._scale, saved_pos = self._view_states[path]
            self._fit_to_win = False
            self._recompute_fit_scale()  # still needed for bounds
            self._update_scaled()
            self._label.move(saved_pos)  # restore pan
            return
        # Otherwise Apply default if it exists
        else:
            logger.debug("Applying default preset")
            mid = self._media_manager.get_media_id(self._current_path)
            row = self._media_manager.default_view_state(mid) if mid else None
            if row:
                self.apply_view_state(row["zoom"], QPoint(row["pan_x"], row["pan_y"]))
            else:
                # Fallback apply nothing
                self._recompute_fit_scale()
                self._scale = self._fit_scale
                self._update_scaled()
                self._center_label()
            self._create_shortcuts()

    def _create_shortcuts(self):
        # Create shortcuts for presets that have defined such
        for sc in getattr(self, "_dyn_presets", []):
            sc.setParent(None)
        self._dyn_presets = []

        mid = self._media_manager.get_media_id(self._current_path)
        rows = self._media_manager.preset_shortcuts(mid) if mid else []
        for r in rows:
            seq = QKeySequence(r["hotkey"])
            if seq.isEmpty():
                continue
            sc = QShortcut(seq, self)
            sc.activated.connect(lambda z=r["zoom"], x=r["pan_x"], y=r["pan_y"]:
                                 self.apply_view_state(z, QPoint(x, y)))
            self._dyn_presets.append(sc)

    def _recompute_fit_scale(self):
        if not self._pix:
            self._fit_scale = 1.0
            return
        self._fit_scale = min(
            self.width() / self._pix.width(),
            self.height() / self._pix.height()
        )

    def _update_scaled(self):
        logger.debug("Updating scale of current image")
        if not self._pix:
            logger.warning("Failed to scale current image, no pix set")
            return

        if self._fit_to_win:
            self._scale = self._fit_scale  # always track fit exactly

        target_w = self._pix.width() * self._scale
        target_h = self._pix.height() * self._scale
        target = QSize(int(target_w), int(target_h))

        scaled = self._pix.scaled(target, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self._label.setPixmap(scaled)
        self._label.resize(scaled.size())

        # if the image now fits entirely inside the window, center it
        if scaled.width() <= self.width() and scaled.height() <= self.height():
            self._center_label()
        else:
            # otherwise keep current pos but clamp to new bounds
            self._move_label(self._label.pos())

    def resizeEvent(self, ev):
        self._backdrop.setGeometry(self.rect())
        self._recompute_fit_scale()
        self._update_scaled()
        panel_w = self.comments_panel.width()
        self.comments_panel.setFixedHeight(self.height())
        self.comments_panel.move(self.width() - panel_w, 0)
        super().resizeEvent(ev)

    def mouseDoubleClickEvent(self, event):
        """
        Handles mouse double click; fitting media to screen size
        :param event:
        :return:
        """
        if event.button() == Qt.LeftButton:
            self._fit_to_win = not self._fit_to_win
            if self._fit_to_win:
                self._scale = 1.0
            self._update_scaled()

    def keyPressEvent(self, event):
        key = event.key()
        mods = event.modifiers()

        # ---------- Immediate actions ----------
        if key == Qt.Key_Escape:
            self.close()
            return

        if mods & Qt.AltModifier and key == Qt.Key_H:
            self._center_horiz()
            return
        if mods & Qt.AltModifier and key == Qt.Key_V:
            self._center_vert()
            return

        # ---------- Fine zoom / nudge first ----------
        if mods & Qt.AltModifier:
            if key == Qt.Key_Plus:
                self._zoom(1.01)  # +1 %
                return
            if key == Qt.Key_Minus:
                self._zoom(0.99)  # −1 %
                return
            if key in (Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down):
                self._nudge(key)  # 1-pixel pan
                return

        # ---------- Pixel-zoom ----------
        if key == Qt.Key_Plus:
            self._zoom_by_pixels(+1)
            return
        if key == Qt.Key_Minus:
            self._zoom_by_pixels(-1)
            return

        # ---------- Fit / coarse zoom ----------
        if key == Qt.Key_0:
            self._fit_to_win = True
            self._update_scaled()
            return
        if key in (Qt.Key_Plus, Qt.Key_Equal):
            self._zoom(1.25)
            return
        if key == Qt.Key_Minus:
            self._zoom(0.8)
            return

        # ---------- Variant cycling ----------
        if key == Qt.Key_Down:
            self._cycle_variant(-1)
            return
        if key == Qt.Key_Up:
            self._cycle_variant(+1)
            return

        # ---------- Gallery navigation ----------
        if key == Qt.Key_Right:
            self._step(+1)
            return
        if key == Qt.Key_Left:
            self._step(-1)
            return

        # Fallback: default handling
        super().keyPressEvent(event)

    def _step(self, delta: int):
        self._save_current_state()
        new_idx = self._idx + delta
        if 0 <= new_idx < len(self._paths):
            self._idx = new_idx

            # refresh current stack for this new gallery item
            self._stack = self._media_manager.stack_paths(self._paths[new_idx])
            base = self._stack[0]

            # pick stored variant if we have one, else base (index 0)
            next_idx = self._variant_pos.get(base, 0)
            next_idx = min(next_idx, len(self._stack) - 1)
            self._current_path = self._stack[next_idx]
            self._load_image(self._current_path)

    def _cycle_variant(self, delta: int):
        """
        Swap to another variant of the current media.
        :param delta:
        :return:
        """
        if len(self._stack) <= 1:
            logger.debug("No detected variants for current media")
            return

        self._save_current_state()

        base = self._stack[0]
        cur_idx = self._stack.index(self._current_path)
        next_idx = (cur_idx + delta) % len(self._stack)
        next_path = self._stack[next_idx]

        # remember position for this stack
        self._variant_pos[base] = next_idx

        # load new variant
        self._current_path = next_path
        self._load_image(next_path)

        # If this variant is visible in the gallery list, update self._idx so Left/Right stay in sync
        if next_path in self._paths:
            self._idx = self._paths.index(next_path)

    def wheelEvent(self, event):
        delta = event.angleDelta()

        if event.modifiers() & Qt.AltModifier:
            # 1 % per wheel‐step. 120: +1 %; −120: −1 %
            sign = 1 if delta.x() > 0 else -1
            factor = 1.0 + 0.01 * sign
        else:
            factor = 1.25 if delta.y() > 0 else 0.8

        self._zoom(factor)

    def _zoom(self, factor: float):
        if not self._pix:
            return

        # Leaving fit-to-window for the first time
        if self._fit_to_win:
            self._fit_to_win = False

        self._scale = max(0.05, min(self._scale * factor, 16.0))
        self._dragging = False
        self._update_scaled()

    def _center_label(self):
        x = (self.width() - self._label.width()) // 2
        y = (self.height() - self._label.height()) // 2
        self._label.move(max(0, x), max(0, y))

    def _move_label(self, new_pos: QPoint):
        """
        Clamp label so at least one edge stays visible.
        :param new_pos:
        :return:
        """
        self._label.move(new_pos)

    def get_view_state(self) -> tuple[float, QPoint]:
        """
        Return (scale, top-left label pos) for saving as a preset. Scale is absolute (not relative to fit-scale).
        :return:
        """
        return self._scale, self._label.pos()

    # Panning logic
    def eventFilter(self, obj, event):
        if obj is self._label:
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                if not self._fit_to_win:
                    self._dragging = True
                    self._drag_start_cursor = event.globalPos()
                    self._drag_start_label = self._label.pos()
                    return True

            elif event.type() == QEvent.MouseMove and self._dragging:
                delta = event.globalPos() - self._drag_start_cursor
                self._move_label(self._drag_start_label + delta)
                return True

            elif event.type() == QEvent.MouseButtonRelease and self._dragging:
                self._dragging = False
                return True

        return super().eventFilter(obj, event)

    def _zoom_by_pixels(self, px: int):
        """
        Add or subtract exactly 1 output pixel in image width.
        :param px: pixel amount to zoom
        :return:
        """
        if not self._pix:
            return
        cur_out_w = self._pix.width() * self._scale
        new_scale = (cur_out_w + px) / self._pix.width()
        self._scale = max(0.05, min(new_scale, 16.0))
        self._fit_to_win = False
        self._update_scaled()

    # ----------------------------------------------------------
    def _nudge(self, key: int):
        """
        Arrow-key pan by one pixel with ALT.
        :param key:
        :return:
        """
        offset = {
            Qt.Key_Left: QPoint(-1, 0),
            Qt.Key_Right: QPoint(1, 0),
            Qt.Key_Up: QPoint(0, -1),
            Qt.Key_Down: QPoint(0, 1),
        }[key]
        self._label.move(self._label.pos() + offset)

    def _save_current_state(self):
        """
        Remember current image’s zoom & pan for this session.
        :return:
        """
        if self._pix:
            self._view_states[self._current_path] = (
                self._scale,
                self._label.pos()
            )

    def _center_horiz(self):
        self._label.move((self.width() - self._label.width()) // 2,
                         self._label.y())

    def _center_vert(self):
        self._label.move(self._label.x(),
                         (self.height() - self._label.height()) // 2)

    def apply_view_state(self, scale: float, pos: QPoint):
        logger.debug(f"Applying view state with {scale}, and {str(pos.x()), str(pos.y())}")
        self._fit_to_win = False
        self._scale = max(0.05, min(scale, 16.0))
        self._update_scaled()
        self._label.move(pos)

    def load_new_stack(self, paths, cur_idx, stack):
        self._paths = list(paths)
        self._stack = stack
        self._idx = cur_idx
        self._load_image(paths[cur_idx])

    def _open_metadata_dialog(self):
        """
        Launch the metadata dialog for the image currently displayed.
        The only path that is provided to metadata dialog is the currently viewed image
        :return:
        """
        if not self._paths:
            logger.warning("No media paths detected, canceling metadata dialog execution")
            return

        z = self._scale
        pos = self._label.pos()
        dlg = MetadataDialog(
            [self._paths[self._idx]],  # single image
            self._media_manager,
            self._tag_manager,
            parent=self.window(),  # modal over main window
            default_transform=(z, pos.x(), pos.y()),  # (zoom, panX, panY)
            viewer=self
        )
        logger.debug(f"New metadata dialog opened with {z, pos.x(), pos.y()} for {self._paths[self._idx]}")
        dlg.exec()

    def refresh(self):
        """
        Re-runs the load image method, first saving the state of the currently viewed media
        :return:
        """
        self._save_current_state()
        self._load_image(self._current_path)
        self._create_shortcuts()

    def _toggle_comments(self):
        print("test")
        if self.comments_panel.isVisible():
            self.comments_panel.hide()
        else:
            mid = self.current_media_id()
            if mid is not None:
                self.comments_panel.load_comments(mid)
            self.comments_panel.show()

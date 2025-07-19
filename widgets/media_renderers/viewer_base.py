from typing import List, Optional
from dataclasses import dataclass
import logging

from PySide6.QtCore import Qt, QPoint, QTimer, QPointF, QUrl
from PySide6.QtGui import QKeyEvent, QShortcut, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QStackedLayout,
    QWidget,
)

from widgets.comments_panel import CommentsPanel
from widgets.media_renderers.media_renderer import ImageRenderer, GifRenderer, MediaRenderer, VideoRenderer
from widgets.metadata_dialog import MetadataDialog

BACKDROP_CSS = "background-color: rgba(0, 0, 0, 180);"  # 70 % black

logger = logging.getLogger(__name__)

COMMENTS_PANEL_MIN_W = 260
COMMENTS_PANEL_W_FRAC = 0.30          # 30 % of viewer width


@dataclass
class ViewerContext:
    path: str
    media_id: int | None
    media_type: str  # 'image' | 'gif' | 'video'
    gif_frame: int | None  # None unless GifRenderer + paused
    gif_paused: bool | None
    timestamp: int | None  #


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
        self._view_state_cache: dict[str, tuple] = {}

        self._current_path = selected_path or self._paths[self._idx]
        self._media_id = self._media_manager.get_media_id(self._current_path)
        if self._stack and self._current_path in self._stack:
            self._variant_pos[self._stack[0]] = self._stack.index(self._current_path)

        # --- Comments ------------------------------------------------------
        self.comments_panel = CommentsPanel(media_manager.comments, self)
        self.comments_panel.hide()
        self.comments_panel.editingBegan.connect(lambda: None)
        self.comments_panel.editingEnded.connect(self.setFocus)

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

        QShortcut(QKeySequence("Ctrl+/"), self).activated.connect(
            lambda: self._toggle_comments()
        )
        QShortcut(QKeySequence("Ctrl+Shift+/"), self).activated.connect(
            lambda: self.comments_panel.toggle_input()
        )
        QShortcut(QKeySequence("Ctrl+P"), self).activated.connect(
            lambda: self._open_metadata_dialog()
        )

        self.ctx = ViewerContext(self._current_path, self._media_id, "image", None, None, None)

        # first display
        self._show_current()

        logger.info("MediaViewerDialog Initialized")

    # public API

    def current_context(self) -> ViewerContext:  # used by MetadataDialog
        return self.ctx

    def _update_context(self) -> None:
        if self._renderer is not None:
            if isinstance(self._renderer, ImageRenderer):
                self.ctx = ViewerContext(self._current_path, self._media_id, "image", None, None, None)
            elif isinstance(self._renderer, GifRenderer):
                paused, cur_frame = self._renderer.current_state()
                self.ctx = ViewerContext(self._current_path, self._media_id, "gif", cur_frame, paused, None)
            else:
                # TODO add timestamp logic
                self.ctx = ViewerContext(self._current_path, self._media_id, "video", None, None, None)

        else:
            logger.critical(f"Renderer improperly set for {self}")

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
    def _select_renderer_class(self, path: str):
        low = path.lower()
        if low.endswith((".mp4", ".mkv", ".mov", ".avi")):
            self.comments_panel.hide()
            return VideoRenderer
        if low.endswith((".gif", ".webp")):
            return GifRenderer
        return ImageRenderer

    def _replace_renderer(self, new_renderer: QWidget):
        self._stacked.removeWidget(self._renderer)
        self._renderer.deleteLater()
        self._renderer = new_renderer
        self._stacked.addWidget(self._renderer)
        if isinstance(new_renderer, VideoRenderer):
            new_renderer._ui.playBtn.setCheckable(True)
            new_renderer._ui.playBtn.clicked.connect(new_renderer.toggle_play)

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
        self._media_id = self._media_manager.get_media_id(self._current_path)

        if self._media_id is None:
            return

        cls_needed = self._select_renderer_class(self._current_path)
        if not isinstance(self._renderer, cls_needed):
            self._replace_renderer(cls_needed(self))

        self._current_path = self._paths[self._idx]
        self._refresh_stack_for_current()

        if self._stack:
            root = self._stack[0]
            desired_pos = self._variant_pos.get(root, 0)
            desired_path = self._stack[desired_pos]
            if desired_path != self._current_path:
                self._current_path = desired_path

        self._renderer.load(self._current_path)

        # If the current path belongs to the known stack, remember index
        if self._stack and self._current_path in self._stack:
            self._variant_pos[self._stack[0]] = self._stack.index(self._current_path)

        # Load comments
        if self.comments_panel.isVisible():
            self.comments_panel.load_comments(self._media_id)

        # restore cached state from this dialog session
        cached = self._view_state_cache.get(self._current_path)
        if cached:
            zoom, pan, extra = cached
            if zoom and pan:
                self._apply_view_state(zoom, QPointF(pan.x(), pan.y()))
            if extra and hasattr(self._renderer, "restore_state"):
                # extra may be a tuple or dict depending on renderer
                if isinstance(extra, dict):
                    self._renderer.restore_state(**extra)
                else:
                    # expected (paused, frame_or_pos)
                    self._renderer.restore_state(*extra)
        elif self._media_id not in self._applied_default:
            #  delay default preset until all resize events are done
            QTimer.singleShot(
                0,
                lambda mid=self._media_id: self._apply_default_preset(mid),
            )
        self._create_dynamic_shortcuts(self._media_id)

        # Update context
        self._update_context()

    def _apply_view_state(self, zoom, offset):

        # ensure current renderer actually has _scale/_offset
        if not hasattr(self._renderer, "_scale") or not hasattr(self._renderer, "move_to"):
            return

        if zoom != self._renderer._scale:
            self._renderer.zoom(zoom / self._renderer._scale)
        self._renderer.move_to(offset.x(), offset.y())

    def _stash_current_view_state(self) -> None:
        """
        Cache zoom/pan (if supported) plus renderer-specific extras.
        :return:
        """
        if not self._current_path:
            return

        # Detect whether the renderer exposes scale/offset attributes
        zoom = getattr(self._renderer, "_scale", None)
        offset = getattr(self._renderer, "_offset", None)  # QPointF or None

        # Renderer-specific state (gif: (paused, frame); video: (paused, pos))
        extra = ()
        if hasattr(self._renderer, "current_state"):
            extra = self._renderer.current_state()

        self._view_state_cache[self._current_path] = (zoom, offset, extra)
    def _step(self, delta: int):
        if not self._paths:
            return
        self._stash_current_view_state()
        self._idx = (self._idx + delta) % len(self._paths)
        self._show_current()

    def _cycle_variant(self, delta: int):
        if not self._stack or self._current_path not in self._stack:
            return
        self._stash_current_view_state()

        root = self._stack[0]
        pos = (self._variant_pos.get(root, 0) + delta) % len(self._stack)
        self._variant_pos[root] = pos
        new_path = self._stack[pos]

        if self._current_path in self._paths:
            self._idx = self._paths.index(self._current_path)
        self._show_current()

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

    # --- Comment Helpers --------------------------------------
    def _toggle_comments(self):

        # Do not allow comments panel on video
        if isinstance(self._renderer, VideoRenderer):
            return

        if self.comments_panel.isVisible():
            self.comments_panel.hide()
        else:
            mid = self._media_manager.get_media_id(self._current_path)
            if mid:
                self.comments_panel.load_comments(mid)
            self.comments_panel.show()
            self._position_comments_panel()
        self.setFocus()

    def _position_comments_panel(self) -> None:
        if self.comments_panel.isHidden():
            return
        w = max(COMMENTS_PANEL_MIN_W, int(self.width() * COMMENTS_PANEL_W_FRAC))
        self.comments_panel.setGeometry(
            self.width() - w,  # x: flush right
            0,  # y: top-aligned
            w,  # dynamic width
            self.height(),  # full height so input box sticks to bottom
        )
        self.comments_panel.raise_()

    # events

    def resizeEvent(self, ev):  # noqa: N802
        self._position_comments_panel()
        super().resizeEvent(ev)

    def keyPressEvent(self, ev: QKeyEvent):  # noqa: N802
        key = ev.key()
        if key in (Qt.Key_D,):
            self._renderer.nudge(+1, 0)
            return
        if key in (Qt.Key_A,):
            self._renderer.nudge(-1, 0)
            return
        if key in (Qt.Key_S,):
            self._renderer.nudge(0, +1)
            return
        if key in (Qt.Key_W,):
            self._renderer.nudge(0, -1)
            return
        if key == Qt.Key_H:
            self._renderer.center_axis(horizontal=True)
            return
        if key == Qt.Key_V:
            self._renderer.center_axis(horizontal=False)
            return
        if ev.key() == Qt.Key_Space and hasattr(self._renderer, "toggle_play"):
            self._renderer.toggle_play()
            return
        if key == Qt.Key_Comma and isinstance(self._renderer, GifRenderer):
            self._renderer.step_frame(-1)
            return  # previous frame
        if key == Qt.Key_Period and isinstance(self._renderer, GifRenderer):
            self._renderer.step_frame(+1)
            return  # next frame
        match key:
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

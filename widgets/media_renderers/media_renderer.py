from typing import Optional

from PySide6.QtCore import Qt, QPoint, QPointF, QRectF, QUrl, Signal, QTimer
from PySide6.QtGui import QPixmap, QWheelEvent, QMouseEvent, QPainter, QMovie, QKeySequence, QShortcut
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QApplication,
    QWidget, QHBoxLayout, QVBoxLayout, QStackedLayout, QSizePolicy, QSlider, QAbstractSlider,
)

from ui.ui_video_controls import Ui_VideoControls


class MediaRenderer(QWidget):
    supports_presets = True

    # --- mandatory API
    def load(self, path: str):
        raise NotImplementedError

    def zoom(self, factor: float, anchor: Optional[QPoint] = None):
        raise NotImplementedError

    def fit_to(self):
        raise NotImplementedError

    def move_to(self, dx: int, dy: int):
        raise NotImplementedError


class ImageRenderer(MediaRenderer):
    _MIN_SCALE = 0.05
    _MAX_SCALE = 50.0

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)

        self._pixmap: QPixmap | None = None
        self._scale: float = 1.0
        self._offset: QPointF = QPointF(0, 0)  # top‑left of image in widget

        # drag state
        self._dragging = False
        self._drag_start_cursor: QPoint = QPoint()
        self._drag_start_offset: QPointF = QPointF()

    # ------------------------------------------------------------------ API
    def load(self, path: str):
        self._pixmap = QPixmap(path)
        self.fit_to()
        self.update()

    def zoom(self, factor: float, anchor: Optional[QPoint] = None):
        if not self._pixmap:
            return
        if anchor is None:
            anchor = QPoint(self.width() // 2, self.height() // 2)

        old_scale = self._scale
        new_scale = max(self._MIN_SCALE, min(self._scale * factor, self._MAX_SCALE))
        if new_scale == old_scale:
            return

        # Work in floating-point space to dodge PySide operator issues
        anchor_f = QPointF(anchor)
        diff = anchor_f - self._offset
        img_coord = QPointF(diff.x() / old_scale, diff.y() / old_scale)

        self._scale = new_scale
        self._offset = anchor_f - QPointF(img_coord.x() * new_scale, img_coord.y() * new_scale)
        self.update()

    def fit_to(self):
        if not self._pixmap:
            return
        vp = self.rect()
        if vp.isEmpty():
            return
        img_w = self._pixmap.width()
        img_h = self._pixmap.height()
        if img_w == 0 or img_h == 0:
            return
        scale_w = vp.width() / img_w
        scale_h = vp.height() / img_h
        self._scale = min(scale_w, scale_h)
        # Center
        self._offset = QPointF(
            (vp.width() - img_w * self._scale) / 2,
            (vp.height() - img_h * self._scale) / 2,
        )
        self.update()

    def move_to(self, dx: int, dy: int):
        self._offset = QPointF(dx, dy)
        self.update()

    def nudge(self, dx: int, dy: int):
        """
        Pan by a small delta in widget space
        :param dx:
        :param dy:
        :return:
        """
        self._offset += QPointF(dx, dy)
        self.update()

    def center_axis(self, horizontal: bool = True):
        if not self._pixmap:
            return
        vp = self.rect()
        if horizontal:
            self._offset.setX((vp.width() - self._pixmap.width() * self._scale) / 2)
        else:
            self._offset.setY((vp.height() - self._pixmap.height() * self._scale) / 2)
        self.update()

    # ------------------------------------------------------------------ events
    def wheelEvent(self, ev: QWheelEvent):  # noqa: N802
        mod = QApplication.keyboardModifiers()
        angle = ev.angleDelta().y()
        if mod & Qt.ControlModifier:
            base = 1.05 if not (mod & Qt.ShiftModifier) else 1.01
        else:
            base = 1.15
        factor = base if angle > 0 else 1 / base
        self.zoom(factor, ev.position().toPoint())

    def mousePressEvent(self, ev: QMouseEvent):  # noqa: N802
        if ev.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_start_cursor = ev.globalPosition().toPoint()
            self._drag_start_offset = QPointF(self._offset)
            self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev: QMouseEvent):
        if self._dragging:
            delta = ev.globalPosition().toPoint() - self._drag_start_cursor
            self._offset = self._drag_start_offset + QPointF(delta)
            self.update()
        super().mouseMoveEvent(ev)

    def mouseReleaseEvent(self, ev: QMouseEvent):
        if ev.button() == Qt.LeftButton and self._dragging:
            self._dragging = False
            self.setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(ev)

    def resizeEvent(self, ev):  # noqa: N802, D401
        # Preserve center on resize
        if self._pixmap:
            self.fit_to()
        super().resizeEvent(ev)

    def paintEvent(self, ev):
        if not self._pixmap:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        target = QRectF(
            self._offset.x(),
            self._offset.y(),
            self._pixmap.width() * self._scale,
            self._pixmap.height() * self._scale,
        )
        painter.drawPixmap(target, self._pixmap, self._pixmap.rect())


class GifRenderer(ImageRenderer):
    supports_presets = True

    def __init__(self, parent: QWidget | None = None):
        self._paused = False  # remember play state
        self._cur_frame = 0  # remember frame index
        super().__init__(parent)
        self._movie: QMovie | None = None

    def load(self, path: str):
        if self._movie:
            self._movie.frameChanged.disconnect()
            self._movie.stop()
        self._movie = QMovie(path)
        self._movie.setCacheMode(QMovie.CacheAll)
        self._movie.frameChanged.connect(self._on_frame_changed)
        self._on_frame_changed(self._cur_frame)  # set first frame into _pixmap
        self._movie.start()
        self.fit_to()

    # --- helper -----------------------------------------------------------
    def _on_frame_changed(self, i: int):
        self._cur_frame = i
        self._pixmap = self._movie.currentPixmap()
        self.update()

    def current_state(self):
        return self._paused, self._cur_frame

    def restore_state(self, paused: bool, frame: int):
        if self._movie:
            self._movie.jumpToFrame(frame)
            self._movie.setPaused(paused)
            self._paused = paused
            self._cur_frame = frame

    def toggle_play(self):
        if self._movie:
            self._paused = not self._paused
            self._movie.setPaused(self._paused)

    def step_frame(self, delta: int):
        if self._movie and self._paused:
            self._movie.jumpToFrame((self._cur_frame + delta) % self._movie.frameCount())


class VideoRenderer(MediaRenderer):
    supports_presets = False  # skip image presets
    request_fullscreen_toggle = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # ----- core widgets -------------------------------------------------
        self._src_path = None
        self._player = QMediaPlayer(self)
        self._player.playbackStateChanged.connect(self._on_state_changed)
        self._player.mediaStatusChanged.connect(self._on_media_status)
        self._player.positionChanged.connect(self._update_time_label)
        self._player.durationChanged.connect(self._update_time_label)
        self._audio = QAudioOutput(self)
        self._player.setAudioOutput(self._audio)
        self._pending_restore = None  # type: tuple[bool, int] | None
        self._player.mediaStatusChanged.connect(self._maybe_apply_pending)

        self._video = QVideoWidget(self)
        self._video.setFocusPolicy(Qt.NoFocus)

        # ----- controls -------------------------------------
        self._controls = QWidget(self)
        self._ui = Ui_VideoControls()
        self._ui.setupUi(self._controls)

        for w in (
                self._ui.playBtn, self._ui.volBtn, self._ui.fsBtn,
                self._ui.posSlider, self._ui.volSlider
        ):
            w.setFocusPolicy(Qt.NoFocus)

        old = self._ui.posSlider
        self._ui.posSlider = BookmarkSlider(Qt.Horizontal, self._controls)
        self._ui.posSlider.setRange(old.minimum(), old.maximum())

        layout = self._ui.horizontalLayout
        idx = layout.indexOf(old)
        layout.removeWidget(old)
        old.deleteLater()
        layout.insertWidget(idx, self._ui.posSlider, 1)

        self._ui.playBtn.setCheckable(True)
        self._ui.playBtn.clicked.connect(self.toggle_play)
        self._ui.volBtn.setCheckable(True)
        self._update_mute_icon(False)
        self._ui.volBtn.toggled.connect(self._audio.setMuted)
        self._audio.mutedChanged.connect(self._update_mute_icon)

        # Stretch controls full-width
        self._controls.setSizePolicy(
            QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        )
        self._controls.setMinimumHeight(self._controls.sizeHint().height())

        # ----- single-container vertical layout ----------------------------
        container = QWidget(self)  # native parent for both
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self._video, 1)  # stretch to fill
        lay.addWidget(self._controls, 0)  # stick to bottom

        # make renderer’s own layout just hold that container
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(container)

        # ----- connect player ----------------------------------------------
        self._player.setVideoOutput(self._video)

        self._ui.posSlider.sliderMoved.connect(
            lambda v: self._player.setPosition(v)
        )

        # Keyboard triggers (←/→, PgUp/Dn) without loop
        self._ui.posSlider.actionTriggered.connect(
            lambda action: self._player.setPosition(self._ui.posSlider.value())
            if action in (
                QAbstractSlider.SliderSingleStepAdd,
                QAbstractSlider.SliderSingleStepSub,
                QAbstractSlider.SliderPageStepAdd,
                QAbstractSlider.SliderPageStepSub,
            ) else None
        )

        self._player.positionChanged.connect(
            lambda ms: self._ui.posSlider.setValue(ms)
        )
        self._player.durationChanged.connect(
            lambda ms: self._ui.posSlider.setMaximum(max(1, ms))
        )

        self._ui.posSlider.setSingleStep(100)  # 0.1 s per left/right key press
        self._ui.posSlider.setPageStep(500)  # 0.5 s per PgUp/PgDn (optional)

        # buttons / sliders
        self._ui.playBtn.clicked.connect(self.toggle_play)

        self._ui.volSlider.valueChanged.connect(lambda v: self._audio.setVolume(v / 100))
        self._ui.fsBtn.clicked.connect(self.request_fullscreen_toggle.emit)

        self._paused = False  # remember play state
        self._last_pos = 0  # remember position

    def _mgr(self):
        """climb two levels to viewer, then grab media_manager."""
        parent = self.parent()
        parent = parent.parent()
        return getattr(parent, "_media_manager", None)

    def load(self, path: str):
        self._src_path = path
        self._player.setSource(QUrl.fromLocalFile(path))

        # ensure widget is ready
        if self._video.size().isEmpty():
            # force layout to run once and give the widget a size
            self.layout().activate()
            if self._video.size().isEmpty():
                # minimum safety fallback
                self._video.resize(16, 16)

        mgr = self._mgr()
        if mgr:
            self.set_bookmarks(mgr.bookmarks_for_path(path))

    # stubs to satisfy interface ------------------------------------------
    def zoom(self, *a, **k):
        pass

    def fit_to(self):
        pass

    def move_to(self, *a, **k):
        pass

    # video helpers --------------------------------------------------------
    def toggle_play(self):
        dur = self._player.duration()
        at_end = dur > 0 and self._player.position() >= dur - 50  # 50 ms tolerance

        if at_end:
            self._player.setPosition(0)

        if self._player.playbackState() == QMediaPlayer.PlayingState:
            self._player.pause()
        else:
            self._player.play()

    def stop(self) -> None:
        """Fully stop playback so audio and decoding cease."""
        self._player.stop()

    def toggle_bar(self):
        self._controls.setVisible(not self._controls.isVisible())

    def seek_seconds(self, delta: int):
        new_ms = max(0, self._player.position() + delta * 1000)
        self._player.setPosition(new_ms)
        self._last_pos = new_ms

    def adjust_volume(self, delta: int):
        cur = int(self._audio.volume() * 100)
        self._audio.setVolume(max(0, min(100, cur + delta)) / 100)

    def _update_play_icon(self, playing: bool) -> None:
        """
        Sync the playBtn check-state and tooltip with the player state.
        """
        self._ui.playBtn.blockSignals(True)
        self._ui.playBtn.setChecked(playing)
        self._ui.playBtn.setToolTip("Pause" if playing else "Play")
        self._ui.playBtn.blockSignals(False)

    def _update_mute_icon(self, muted: bool) -> None:
        """Keep icon/tooltip aligned with audio mute state."""
        self._ui.volBtn.blockSignals(True)
        self._ui.volBtn.setChecked(muted)
        self._ui.volBtn.setToolTip("Unmute" if muted else "Mute")
        self._ui.volBtn.blockSignals(False)

    def add_bookmark(self) -> None:
        """Store current position (ms) and refresh ticks."""
        pos = self._player.position()
        ticks = set(self._ui.posSlider.bookmarks) | {pos}
        self.set_bookmarks(list(ticks))
        mgr = self._mgr()
        if mgr:
            mgr.add_bookmark(self._src_path, pos)

    def delete_nearest_bookmark(self) -> None:
        """Remove tick nearest to current position (1 s tolerance)."""
        ticks = set(self._ui.posSlider.bookmarks)
        if not ticks:
            return
        cur = self._player.position()
        nearest = min(ticks, key=lambda t: abs(t - cur))
        if abs(nearest - cur) > 1000:
            return
        ticks.remove(nearest)
        self.set_bookmarks(list(ticks))

        mgr = self._mgr()
        if mgr:
            mgr.delete_bookmark(self._src_path, nearest)

    def set_bookmarks(self, seconds: list[float] | list[int]) -> None:
        """
        Accepts seconds (float/int) or milliseconds (int) and updates ticks.
        """
        seq = list(seconds)  # <-- handles set, tuple, etc.
        if not seq:
            ms_list = []
        elif isinstance(seq[0], float):
            ms_list = [int(s * 1000) for s in seq]
        else:
            ms_list = [int(s) for s in seq]

        self._ui.posSlider.set_bookmarks(sorted(ms_list))

    def focusNextPrevChild(self, _next: bool) -> bool:  # noqa: D401
        """Disable Tab/Shift-Tab focus traversal so viewer retains focus."""
        return False


    def skip_bookmark(self, direction: int) -> None:
        """
        Jump to the next (direction=+1) or previous (direction=-1) bookmark.
        Wraps at ends.
        """
        ticks = self._ui.posSlider.bookmarks
        if not ticks:
            return
        cur = self._player.position()
        if direction > 0:
            nxt = next((t for t in ticks if t > cur + 500), ticks[0])
        else:
            nxt = next((t for t in reversed(ticks) if t < cur - 500), ticks[-1])
        self._player.setPosition(nxt)

    def _on_state_changed(self, state):  # slot for playbackStateChanged
        self._update_play_icon(state == QMediaPlayer.PlayingState)

    def _on_media_status(self, status):  # slot for mediaStatusChanged
        if status == QMediaPlayer.EndOfMedia:
            # Seek to first frame and stay paused so user sees poster frame
            self._player.pause()
            self._player.setPosition(0)

    def current_state(self):
        return {
            "paused": self._player.playbackState() != QMediaPlayer.PlayingState,
            "pos": self._player.position(),
        }

    def restore_state(self, paused: bool, pos: int):
        """
        Defer the seek until media is ready; then play/pause as requested.
        """
        if self._player.mediaStatus() in (QMediaPlayer.LoadedMedia,
                                          QMediaPlayer.BufferedMedia):
            self._apply_restore(paused, pos)
        else:
            # save for later
            self._pending_restore = (paused, pos)

    def _maybe_apply_pending(self, status):
        if status in (QMediaPlayer.LoadedMedia, QMediaPlayer.BufferedMedia):
            if self._pending_restore:
                paused, pos = self._pending_restore
                self._apply_restore(paused, pos)
                self._pending_restore = None

    def _apply_restore(self, paused: bool, pos: int):
        self._player.setPosition(pos)
        if paused:
            self._player.pause()
        else:
            self._player.play()

    def _update_time_label(self, *_):
        cur = self._player.position()
        dur = max(self._player.duration(), 1)
        self._ui.timeLbl.setText(f"{_fmt_ms(cur)} / {_fmt_ms(dur)}")


class ClickableSlider(QSlider):
    def mousePressEvent(self, ev: QMouseEvent):
        if ev.button() == Qt.LeftButton:
            frac = ev.position().x() / self.width()
            val = self.minimum() + frac * (self.maximum() - self.minimum())
            self.setValue(int(val))
            self.sliderMoved.emit(int(val))
            ev.accept()
        super().mousePressEvent(ev)


class BookmarkSlider(ClickableSlider):
    """Slider that can paint bookmark ticks."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.bookmarks: list[int] = []  # milliseconds

    def set_bookmarks(self, ms_list: list[int]) -> None:
        self.bookmarks = sorted(ms_list)
        self.update()

    def paintEvent(self, ev):
        super().paintEvent(ev)
        if not self.bookmarks or self.maximum() == self.minimum():
            return

        from PySide6.QtGui import QPainter, QColor, QPen
        p = QPainter(self)
        pen = QPen(QColor("red"))
        pen.setWidth(3)  # thicker
        p.setPen(pen)

        full = self.maximum() - self.minimum()
        h = self.height()
        tick_h = int(h * 0.4)  # 40 % height

        for ms in self.bookmarks:
            x = int((ms - self.minimum()) / full * self.width())
            y0 = (h - tick_h) // 2  # vertically centered stub
            p.drawLine(x, y0, x, y0 + tick_h)


def _fmt_ms(ms: int) -> str:
    sec = ms // 1000
    return f"{sec // 60:02d}:{sec % 60:02d}"

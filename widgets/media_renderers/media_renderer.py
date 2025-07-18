from typing import Optional

from PySide6.QtCore import Qt, QPoint, QPointF, QRectF, QUrl, Signal
from PySide6.QtGui import QPixmap, QWheelEvent, QMouseEvent, QPainter, QMovie
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QApplication,
    QWidget, QHBoxLayout, QVBoxLayout, QStackedLayout, QSizePolicy,
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
        self._player = QMediaPlayer(self)
        self._audio = QAudioOutput(self)
        self._player.setAudioOutput(self._audio)

        self._video = QVideoWidget(self)

        # ----- controls -------------------------------------
        self._controls = QWidget(self)
        self._ui = Ui_VideoControls()
        self._ui.setupUi(self._controls)

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

        self._player.positionChanged.connect(
            lambda ms: self._ui.posSlider.setValue(ms // 1000)
        )
        self._player.durationChanged.connect(
            lambda ms: self._ui.posSlider.setMaximum(max(1, ms // 1000))
        )

        # buttons / sliders
        self._ui.playBtn.clicked.connect(self.toggle_play)
        self._ui.posSlider.sliderMoved.connect(
            lambda v: self._player.setPosition(v * 1000)
        )
        self._ui.volSlider.valueChanged.connect(lambda v: self._audio.setVolume(v / 100))
        self._ui.fsBtn.clicked.connect(self.request_fullscreen_toggle.emit)

        self._paused = False  # remember play state
        self._last_pos = 0  # remember position

    # mandatory API --------------------------------------------------------
    def load(self, path: str):
        self._player.setSource(QUrl.fromLocalFile(path))
        self._player.play()

    # stubs to satisfy interface ------------------------------------------
    def zoom(self, *a, **k):
        pass

    def fit_to(self):
        pass

    def move_to(self, *a, **k):
        pass

    # video helpers --------------------------------------------------------
    def toggle_play(self):
        if self._player.playbackState() == QMediaPlayer.PlayingState:
            self._player.pause()
            self._paused = True
            self._ui.playBtn.setChecked(False)  # update icon state
        else:
            self._player.play()
            self._paused = False
            self._ui.playBtn.setChecked(True)

    def seek_seconds(self, delta: int):
        new_ms = max(0, self._player.position() + delta * 1000)
        self._player.setPosition(new_ms)
        self._last_pos = new_ms

    def adjust_volume(self, delta: int):
        cur = int(self._audio.volume() * 100)
        self._audio.setVolume(max(0, min(100, cur + delta)) / 100)

    def current_state(self):
        return self._paused, self._last_pos

    def restore_state(self, paused: bool, pos: int):
        self._player.setPosition(pos)
        self._player.setPaused(paused)
        self._paused, self._last_pos = paused, pos

    def enterEvent(self, _):
        self._controls.show()

    def leaveEvent(self, _):
        self._controls.hide()

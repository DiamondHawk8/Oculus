from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, QPoint, QPointF, QRectF
from PySide6.QtGui import QPixmap, QKeyEvent, QWheelEvent, QMouseEvent, QPainter
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

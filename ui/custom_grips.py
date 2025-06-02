from PySide6.QtCore import Qt, QRect, QSize
from PySide6.QtGui  import QCursor, QMouseEvent
from PySide6.QtWidgets import QWidget, QFrame, QHBoxLayout, QSizeGrip


GRIP = 5


class CustomGrip(QWidget):

    def __init__(self, parent, position: Qt.Edge, *, disable_color: bool = False):
        super().__init__(parent)
        self.parent = parent
        self._pos   = position
        self._init_ui(disable_color)

    def _init_ui(self, disable_color: bool) -> None:
        if self._pos == Qt.TopEdge:
            self._build_top(disable_color)
        elif self._pos == Qt.BottomEdge:
            self._build_bottom(disable_color)
        elif self._pos == Qt.LeftEdge:
            self._build_left(disable_color)
        elif self._pos == Qt.RightEdge:
            self._build_right(disable_color)

        if disable_color:
            self.setStyleSheet("background: transparent;")
            self._clear_child_styles(self)

    def _build_top(self, disable: bool):
        self.setGeometry(0, 0, self.parent.width(), GRIP)
        self.setMaximumHeight(GRIP)

        bar = _make_bar(self, Qt.SizeVerCursor, disable)
        bar.mouseMoveEvent = self._resize_top
        # corners
        QSizeGrip(_make_corner(self, Qt.SizeFDiagCursor, disable, left=True))
        QSizeGrip(_make_corner(self, Qt.SizeBDiagCursor, disable, left=False))

    def _build_bottom(self, disable: bool):
        self.setGeometry(0, self.parent.height() - GRIP, self.parent.width(), GRIP)
        self.setMaximumHeight(GRIP)

        bar = _make_bar(self, Qt.SizeVerCursor, disable)
        bar.mouseMoveEvent = self._resize_bottom
        QSizeGrip(_make_corner(self, Qt.SizeBDiagCursor, disable, left=True))
        QSizeGrip(_make_corner(self, Qt.SizeFDiagCursor, disable, left=False))

    def _build_left(self, disable: bool):
        self.setGeometry(0, GRIP, GRIP, self.parent.height() - 2 * GRIP)
        self.setMaximumWidth(GRIP)

        bar = _make_bar(self, Qt.SizeHorCursor, disable, vertical=True)
        bar.mouseMoveEvent = self._resize_left

    def _build_right(self, disable: bool):
        self.setGeometry(self.parent.width() - GRIP, GRIP, GRIP,
                         self.parent.height() - 2 * GRIP)
        self.setMaximumWidth(GRIP)

        bar = _make_bar(self, Qt.SizeHorCursor, disable, vertical=True)
        bar.mouseMoveEvent = self._resize_right

    def _resize_top(self, e: QMouseEvent):
        dy     = e.pos().y()
        height = max(self.parent.minimumHeight(), self.parent.height() - dy)
        geo    = self.parent.geometry()
        geo.setTop(geo.bottom() - height)
        self.parent.setGeometry(geo); e.accept()

    def _resize_bottom(self, e: QMouseEvent):
        dy = e.pos().y()
        height = max(self.parent.minimumHeight(), self.parent.height() + dy)
        self.parent.resize(self.parent.width(), height); e.accept()

    def _resize_left(self, e: QMouseEvent):
        dx   = e.pos().x()
        width = max(self.parent.minimumWidth(), self.parent.width() - dx)
        geo   = self.parent.geometry()
        geo.setLeft(geo.right() - width)
        self.parent.setGeometry(geo); e.accept()

    def _resize_right(self, e: QMouseEvent):
        dx = e.pos().x()
        width = max(self.parent.minimumWidth(), self.parent.width() + dx)
        self.parent.resize(width, self.parent.height()); e.accept()


    @staticmethod
    def _clear_child_styles(w: QWidget):
        for child in w.findChildren(QWidget):
            child.setStyleSheet("background: transparent")

    # keep layout in sync when window resizes
    def resizeEvent(self, _):
        if self._pos == Qt.TopEdge:
            self.setGeometry(0, 0, self.parent.width(), GRIP)
        elif self._pos == Qt.BottomEdge:
            self.setGeometry(0, self.parent.height() - GRIP, self.parent.width(), GRIP)
        elif self._pos == Qt.LeftEdge:
            self.setGeometry(0, GRIP, GRIP, self.parent.height() - 2 * GRIP)
        elif self._pos == Qt.RightEdge:
            self.setGeometry(self.parent.width() - GRIP, GRIP,
                              GRIP, self.parent.height() - 2 * GRIP)


def _make_bar(parent: QWidget, cursor, disable: bool,
              vertical: bool = False) -> QFrame:
    bar = QFrame(parent)
    if vertical:
        bar.setGeometry(QRect(0, 0, GRIP, parent.height()))
    else:
        bar.setGeometry(QRect(0, 0, parent.width(), GRIP))
    bar.setCursor(QCursor(cursor))
    if not disable:
        bar.setStyleSheet("background: rgba(255,255,255,25);")
    return bar


def _make_corner(parent: QWidget, cursor, disable: bool, *, left: bool) -> QFrame:
    corner = QFrame(parent)
    corner.setCursor(QCursor(cursor))
    corner.resize(GRIP, GRIP)
    if not disable:
        corner.setStyleSheet("background: rgba(255,255,255,25);")
    if left:
        corner.move(0, 0)
    else:
        if parent.width() > parent.height():
            corner.move(parent.width() - GRIP, 0)
        else:
            corner.move(0, parent.height() - GRIP)
    return corner

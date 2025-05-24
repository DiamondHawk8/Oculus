from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

class CustomGrip(QWidget):
    def __init__(self, parent, position, disable_color = False):

        # SETUP UI
        QWidget.__init__(self)
        self.parent = parent
        self.setParent(parent)
        self.wi = Widgets()

        # SHOW TOP GRIP
        if position == Qt.TopEdge:
            self._init_top_grip(disable_color)

        # SHOW BOTTOM GRIP
        elif position == Qt.BottomEdge:
            self._init_bottom_grip(disable_color)

        # SHOW LEFT GRIP
        elif position == Qt.LeftEdge:
            self._init_left_grip(disable_color)

        # RESIZE RIGHT
        elif position == Qt.RightEdge:
            self._init_right_grip(disable_color)

    def _init_top_grip(self, disable_color: bool = False):
        self.wi.top(self)
        self.setGeometry(0, 0, self.parent.width(), 10)
        self.setMaximumHeight(10)

        QSizeGrip(self.wi.top_left)
        QSizeGrip(self.wi.top_right)

        self.wi.top.mouseMoveEvent = self._resize_top

        if disable_color:
            self._set_transparent_styles([
                self.wi.top_left,
                self.wi.top_right,
                self.wi.top
            ])

    def _resize_top(self, event: QMouseEvent):
        delta = event.pos()
        height = max(self.parent.minimumHeight(), self.parent.height() - delta.y())
        geo = self.parent.geometry()
        geo.setTop(geo.bottom() - height)
        self.parent.setGeometry(geo)
        event.accept()

    def _init_bottom_grip(self, disable_color: bool = False):
        self.wi.bottom(self)
        self.setGeometry(0, self.parent.height() - 10, self.parent.width(), 10)
        self.setMaximumHeight(10)

        QSizeGrip(self.wi.bottom_left)
        QSizeGrip(self.wi.bottom_right)

        self.wi.bottom.mouseMoveEvent = self._resize_bottom

        if disable_color:
            self._set_transparent_styles([
                self.wi.bottom_left,
                self.wi.bottom_right,
                self.wi.bottom
            ])

    def _resize_bottom(self, event: QMouseEvent):
        delta = event.pos()
        height = max(self.parent.minimumHeight(), self.parent.height() + delta.y())
        self.parent.resize(self.parent.width(), height)
        event.accept()

    def _init_left_grip(self, disable_color: bool = False):
        self.wi.left(self)
        self.setGeometry(0, 10, 10, self.parent.height())
        self.setMaximumWidth(10)

        self.wi.leftgrip.mouseMoveEvent = self._resize_left

        if disable_color:
            self._set_transparent_styles([self.wi.leftgrip])

    def _resize_left(self, event: QMouseEvent):
        delta = event.pos()
        width = max(self.parent.minimumWidth(), self.parent.width() - delta.x())
        geo = self.parent.geometry()
        geo.setLeft(geo.right() - width)
        self.parent.setGeometry(geo)
        event.accept()

    def _init_right_grip(self, disable_color: bool = False):
        self.wi.right(self)
        self.setGeometry(self.parent.width() - 10, 10, 10, self.parent.height())
        self.setMaximumWidth(10)

        self.wi.rightgrip.mouseMoveEvent = self._resize_right

        if disable_color:
            self._set_transparent_styles([self.wi.rightgrip])

    def _resize_right(self, event: QMouseEvent):
        delta = event.pos()
        width = max(self.parent.minimumWidth(), self.parent.width() + delta.x())
        self.parent.resize(width, self.parent.height())
        event.accept()

    def _set_transparent_styles(self, widgets: list[QWidget]):
        for widget in widgets:
            widget.setStyleSheet("background: transparent")

    def mouseReleaseEvent(self, event):
        self.mousePos = None

    def resizeEvent(self, event):
        w, h = self.width(), self.height()
        if hasattr(self.wi, "container_top"):  # top grip
            self.wi.container_top.setGeometry(0, 0, w, 10)

        elif hasattr(self.wi, "container_bottom"):  # bottom grip
            self.wi.container_bottom.setGeometry(0, 0, w, 10)

        elif hasattr(self.wi, "leftgrip"):  # left grip
            self.wi.leftgrip.setGeometry(0, 0, 10, h)

        elif hasattr(self.wi, "rightgrip"):  # right grip
            self.wi.rightgrip.setGeometry(0, 0, 10, h)



class Widgets(object):
    def top(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        self.container_top = QFrame(Form)
        self.container_top.setObjectName(u"container_top")
        self.container_top.setGeometry(QRect(0, 0, 500, 10))
        self.container_top.setMinimumSize(QSize(0, 10))
        self.container_top.setMaximumSize(QSize(16777215, 10))
        self.container_top.setFrameShape(QFrame.NoFrame)
        self.container_top.setFrameShadow(QFrame.Raised)
        self.top_layout = QHBoxLayout(self.container_top)
        self.top_layout.setSpacing(0)
        self.top_layout.setObjectName(u"top_layout")
        self.top_layout.setContentsMargins(0, 0, 0, 0)
        self.top_left = QFrame(self.container_top)
        self.top_left.setObjectName(u"top_left")
        self.top_left.setMinimumSize(QSize(10, 10))
        self.top_left.setMaximumSize(QSize(10, 10))
        self.top_left.setCursor(QCursor(Qt.SizeFDiagCursor))
        self.top_left.setStyleSheet(u"background-color: rgb(33, 37, 43);")
        self.top_left.setFrameShape(QFrame.NoFrame)
        self.top_left.setFrameShadow(QFrame.Raised)
        self.top_layout.addWidget(self.top_left)
        self.top = QFrame(self.container_top)
        self.top.setObjectName(u"top")
        self.top.setCursor(QCursor(Qt.SizeVerCursor))
        self.top.setStyleSheet(u"background-color: rgb(85, 255, 255);")
        self.top.setFrameShape(QFrame.NoFrame)
        self.top.setFrameShadow(QFrame.Raised)
        self.top_layout.addWidget(self.top)
        self.top_right = QFrame(self.container_top)
        self.top_right.setObjectName(u"top_right")
        self.top_right.setMinimumSize(QSize(10, 10))
        self.top_right.setMaximumSize(QSize(10, 10))
        self.top_right.setCursor(QCursor(Qt.SizeBDiagCursor))
        self.top_right.setStyleSheet(u"background-color: rgb(33, 37, 43);")
        self.top_right.setFrameShape(QFrame.NoFrame)
        self.top_right.setFrameShadow(QFrame.Raised)
        self.top_layout.addWidget(self.top_right)

    def bottom(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        self.container_bottom = QFrame(Form)
        self.container_bottom.setObjectName(u"container_bottom")
        self.container_bottom.setGeometry(QRect(0, 0, 500, 10))
        self.container_bottom.setMinimumSize(QSize(0, 10))
        self.container_bottom.setMaximumSize(QSize(16777215, 10))
        self.container_bottom.setFrameShape(QFrame.NoFrame)
        self.container_bottom.setFrameShadow(QFrame.Raised)
        self.bottom_layout = QHBoxLayout(self.container_bottom)
        self.bottom_layout.setSpacing(0)
        self.bottom_layout.setObjectName(u"bottom_layout")
        self.bottom_layout.setContentsMargins(0, 0, 0, 0)
        self.bottom_left = QFrame(self.container_bottom)
        self.bottom_left.setObjectName(u"bottom_left")
        self.bottom_left.setMinimumSize(QSize(10, 10))
        self.bottom_left.setMaximumSize(QSize(10, 10))
        self.bottom_left.setCursor(QCursor(Qt.SizeBDiagCursor))
        self.bottom_left.setStyleSheet(u"background-color: rgb(33, 37, 43);")
        self.bottom_left.setFrameShape(QFrame.NoFrame)
        self.bottom_left.setFrameShadow(QFrame.Raised)
        self.bottom_layout.addWidget(self.bottom_left)
        self.bottom = QFrame(self.container_bottom)
        self.bottom.setObjectName(u"bottom")
        self.bottom.setCursor(QCursor(Qt.SizeVerCursor))
        self.bottom.setStyleSheet(u"background-color: rgb(85, 170, 0);")
        self.bottom.setFrameShape(QFrame.NoFrame)
        self.bottom.setFrameShadow(QFrame.Raised)
        self.bottom_layout.addWidget(self.bottom)
        self.bottom_right = QFrame(self.container_bottom)
        self.bottom_right.setObjectName(u"bottom_right")
        self.bottom_right.setMinimumSize(QSize(10, 10))
        self.bottom_right.setMaximumSize(QSize(10, 10))
        self.bottom_right.setCursor(QCursor(Qt.SizeFDiagCursor))
        self.bottom_right.setStyleSheet(u"background-color: rgb(33, 37, 43);")
        self.bottom_right.setFrameShape(QFrame.NoFrame)
        self.bottom_right.setFrameShadow(QFrame.Raised)
        self.bottom_layout.addWidget(self.bottom_right)

    def left(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        self.leftgrip = QFrame(Form)
        self.leftgrip.setObjectName(u"left")
        self.leftgrip.setGeometry(QRect(0, 10, 10, 480))
        self.leftgrip.setMinimumSize(QSize(10, 0))
        self.leftgrip.setCursor(QCursor(Qt.SizeHorCursor))
        self.leftgrip.setStyleSheet(u"background-color: rgb(255, 121, 198);")
        self.leftgrip.setFrameShape(QFrame.NoFrame)
        self.leftgrip.setFrameShadow(QFrame.Raised)

    def right(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        self.rightgrip = QFrame(Form)
        self.rightgrip.setObjectName(u"right")
        self.rightgrip.setGeometry(QRect(0, 0, 10, 500))
        self.rightgrip.setMinimumSize(QSize(10, 0))
        self.rightgrip.setCursor(QCursor(Qt.SizeHorCursor))
        self.rightgrip.setStyleSheet(u"background-color: rgb(255, 0, 127);")
        self.rightgrip.setFrameShape(QFrame.NoFrame)
        self.rightgrip.setFrameShadow(QFrame.Raised)

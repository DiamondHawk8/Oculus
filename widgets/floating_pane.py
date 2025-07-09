from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QFrame

from ui.ui_floating_pane import Ui_FloatingPane


class FloatingPane(QFrame, Ui_FloatingPane):
    """
    A Draggable, collapsible wrapper
    """
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Tool | Qt.FramelessWindowHint)
        self.setupUi(self)  # loads btnToggle & body frame
        self._drag: QPoint | None = None

        self.btnToggle.clicked.connect(self._toggle)

    def setContent(self, w):
        self.body.layout().addWidget(w)

    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self._drag = ev.globalPos() - self.pos()

    def mouseMoveEvent(self, ev):
        if self._drag:
            self.move(ev.globalPos() - self._drag)

    def mouseReleaseEvent(self, *_):
        self._drag = None

    def _toggle(self):
        hide = self.body.isVisible()
        self.body.setVisible(not hide)
        self.btnToggle.setText("⮞" if hide else "⮜")
        self.adjustSize()

from PySide6.QtCore import QSize, QPoint, Qt
from PySide6.QtWidgets import QWidget


class MediaRenderer(QWidget):
    """Abstract base for all renderers"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    def load(self, path: str):
        raise NotImplementedError

    def zoom(self, factor: float):
        raise NotImplementedError

    def fit_to(self, size: QSize):
        raise NotImplementedError

    def move_to(self, pos: QPoint):
        raise NotImplementedError
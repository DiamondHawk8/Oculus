from abc import ABC, abstractmethod
from pathlib import Path
from PySide6.QtCore import QSize, QPoint, Qt
from PySide6.QtWidgets import QWidget


class MediaRenderer(QWidget, ABC):
    """Abstract base for all renderers"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    @abstractmethod
    def load(self, path: str):
        pass

    @abstractmethod
    def zoom(self, factor: float):
        pass

    @abstractmethod
    def fit_to(self, size: QSize):
        pass

    @abstractmethod
    def pan(self, delta: QPoint):
        pass

    @abstractmethod
    def reset_view(self):
        pass

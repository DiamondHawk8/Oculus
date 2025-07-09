from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget


class TagPane(QWidget):
    tagsChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def load(self, media_ids: list[int]):
        pass

    def save(self):
        pass

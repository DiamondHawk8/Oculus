from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget


class TagsPane(QWidget):
    tagsChanged = Signal(list, list, list)

    def load(self, media_ids: list[int]):
        pass

    def save(self):
        pass

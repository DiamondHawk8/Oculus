from PySide6.QtCore import QObject, Signal

class MetadataPresenter(QObject):
    tagsChanged = Signal()
    attributesChanged = Signal()
    presetsChanged = Signal()

    def __init__(self, backend, parent=None):
        super().__init__(parent)
        self.backend = backend

    def save_tags(self, *args, **kwargs):
        pass
    def save_attributes(self, *args, **kwargs):
        pass
    def save_preset(self, *args, **kwargs):
        pass
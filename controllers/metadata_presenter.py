from PySide6.QtCore import QObject, Signal

class MetadataPresenter(QObject):
    tagsChanged = Signal()
    attributesChanged = Signal()
    presetsChanged = Signal()

    def __init__(self, backend, parent=None):
        super().__init__(parent)
        self.backend = backend

    def id_for_path(self, path: str) -> int:
        return self.backend.id_for_path(path)

    def target_media_ids(self, paths, scope, include_variants):
        return self.backend.target_media_ids(paths, scope, include_variants)
    def save_tags(self, *args, **kwargs):
        pass
    def save_attributes(self, *args, **kwargs):
        pass
    def save_preset(self, *args, **kwargs):
        pass
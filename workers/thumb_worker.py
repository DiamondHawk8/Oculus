from PySide6.QtCore import QRunnable
from PySide6.QtGui import QPixmap, Qt


def _generate_thumb(path: str, size: int) -> QPixmap:
    pix = QPixmap(path)
    return pix.scaled(size, size, Qt.KeepAspectRatio,
                      Qt.SmoothTransformation) if not pix.isNull() else QPixmap()


class ThumbWorker(QRunnable):
    def __init__(self, path: str, size: int, cb):
        super().__init__()
        self.path, self.size, self.cb = path, size, cb
        self.setAutoDelete(True)

    def run(self):
        pix = _generate_thumb(self.path, self.size)
        if not pix.isNull():
            self.cb(self.path, pix)

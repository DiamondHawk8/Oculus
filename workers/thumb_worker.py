from pathlib import Path
import cv2

from PySide6.QtCore import QRunnable, Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QApplication

VIDEO_SUFFIXES = {".mp4", ".mkv", ".webm", ".mov", ".avi"}


# ------------------------------------------------------------------ helpers
def _generate_thumb(path: str, size: int) -> QImage:

    suffix = Path(path).suffix.lower()

    # ----- images & GIFs --------------------------------------------------
    if suffix not in VIDEO_SUFFIXES:
        img = QImage(path)
        if img.isNull():
            return QImage()
        return img.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    # ----- videos ---------------------------------------------------------
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        return QImage()

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(fps) * 3)    # seek ~3 s in
    ok, frame = cap.read()
    cap.release()
    if not ok:
        return QImage()

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w, _ = frame_rgb.shape
    img = QImage(frame_rgb.data, w, h, QImage.Format_RGB888)
    return img.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)


class ThumbWorker(QRunnable):
    """
    Runs off-thread: builds QImage, then posts a Pixmap-ready callback
    back to the GUI thread.
    """
    def __init__(self, path: str, size: int, cb):
        super().__init__()
        self.path, self.size, self.cb = path, size, cb
        self.setAutoDelete(True)

    def run(self):
        img = _generate_thumb(self.path, self.size)
        if img.isNull():
            return

        # schedule on the GUI thread (via QApplication's thread)
        QTimer.singleShot(
            0,
            QApplication.instance(),  # receiver to main thread
            lambda p=self.path, im=img:  # lambda runs in GUI thread
            self.cb(p, QPixmap.fromImage(im))
        )

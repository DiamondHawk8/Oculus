from pathlib import Path

import cv2

from PySide6.QtCore import QRunnable
from PySide6.QtGui import QPixmap, Qt, QImage

VIDEO_SUFFIXES = {".mp4", ".mkv", ".webm", ".mov", ".avi"}


def _generate_thumb(path: str, size: int) -> QPixmap:
    suffix = Path(path).suffix.lower()

    #  image & gif
    if suffix not in VIDEO_SUFFIXES:
        pix = QPixmap(path)
        return (
            pix.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            if not pix.isNull()
            else QPixmap()
        )

    #  video thumbnail
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        return QPixmap()

    # grab frame ~1 s in (or frame 0 if shorter)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(fps) * 30)  # seek to ~30 sec
    success, frame = cap.read()
    cap.release()

    if not success:
        return QPixmap()

    # BGR -> RGB, ndarray -> QImage -> QPixmap
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w, _ = frame_rgb.shape
    qimg = QImage(frame_rgb.data, w, h, QImage.Format_RGB888)
    pix = QPixmap.fromImage(qimg)
    return pix.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)


class ThumbWorker(QRunnable):
    def __init__(self, path: str, size: int, cb):
        super().__init__()
        self.path, self.size, self.cb = path, size, cb
        self.setAutoDelete(True)

    def run(self):
        pix = _generate_thumb(self.path, self.size)
        if not pix.isNull():
            self.cb(self.path, pix)

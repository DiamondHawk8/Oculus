from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QApplication, QWidget


class ImageViewerDialog(QDialog):
    """Fullscreen viewer with translucent backdrop and Esc to close."""

    BACKDROP_CSS = "background-color: rgba(0, 0, 0, 180);"   # 70 % black

    def __init__(self, paths: list[str], cur_idx: int, parent=None):
        super().__init__(parent)

        self._paths = list(paths)
        self._idx = cur_idx

        # Window setup
        self.setWindowFlag(Qt.FramelessWindowHint, True)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setModal(True)

        # ---- backdrop ---------------------------------------------------
        # fills entire dialog
        self._backdrop = QWidget(self)
        self._backdrop.setStyleSheet(self.BACKDROP_CSS)
        # push it behind everything
        self._backdrop.lower()

        # ---- image label -----------------------------------------------
        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setStyleSheet("background: transparent;")

        # ---- layout -----------------------------------------------------
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._label)

        # ---- load & show -----------------------------------------------
        self._load_image(self._paths[self._idx])

        self.showFullScreen()

    def _load_image(self, path: str):
        """
        Load image from given path. Displays white, if not found
        :param path: path to image
        :return:
        """
        pix = QPixmap(path)
        if pix.isNull():
            self._label.setText(f"Could not load {Path(path).name}")
            self._label.setStyleSheet("color:white;background:black;")
        else:
            self._label.setPixmap(pix)

    def _update_scaled(self):
        if self._pix.isNull():
            return
        scaled = self._pix.scaled(
            self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self._label.setPixmap(scaled)

    def resizeEvent(self, ev):
        self._backdrop.setGeometry(self.rect())   # keep backdrop full-size
        self._update_scaled()
        super().resizeEvent(ev)

    def keyPressEvent(self, event):
        """
        Method that will close the viewer on esc being pressed
        :param event:
        :return: None
        """
        if event.key() == Qt.Key_Escape:
            self.close()

        elif event.key() == Qt.Key_Right:
            # Next
            self._step(+1)
        elif event.key() == Qt.Key_Left:
            # Previous
            self._step(-1)
        else:
            super().keyPressEvent(event)

    def _step(self, delta: int):
        new_idx = self._idx + delta
        if 0 <= new_idx < len(self._paths):
            self._idx = new_idx
            self._load_image(self._paths[new_idx])

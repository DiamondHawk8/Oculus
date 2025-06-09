from pathlib import Path

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QApplication, QWidget


class ImageViewerDialog(QDialog):
    """Fullscreen viewer with translucent backdrop and Esc to close."""

    BACKDROP_CSS = "background-color: rgba(0, 0, 0, 180);"   # 70 % black

    def __init__(self, paths: list[str], cur_idx: int, parent=None):
        super().__init__(parent)

        self._paths = list(paths)
        self._idx = cur_idx

        self._scale = 1.0  # 1.0 = fit-to-window
        self._fit_to_win = True  # start in fit mode
        self._pix: QPixmap | None = None

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
            self._label.setText(f"Could not load\n{Path(path).name}")
            self._label.setStyleSheet("color:white; background:transparent;")
            self._pix = None
        else:
            self._pix = pix
            self._update_scaled()

    def _update_scaled(self):
        if self._pix.isNull():
            return

        if self._fit_to_win:
            target = self.size()
        else:
            w = self._pix.width() * self._scale
            h = self._pix.height() * self._scale
            target = QSize(int(w), int(h))

        scaled = self._pix.scaled(target, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self._label.setPixmap(scaled)
        self._label.adjustSize()

    def resizeEvent(self, ev):
        self._backdrop.setGeometry(self.rect())   # keep backdrop full-size
        self._update_scaled()
        super().resizeEvent(ev)

    def mouseDoubleClickEvent(self, event):
        """
        Handles mouse double click; fitting media to screen size
        :param event:
        :return:
        """
        if event.button() == Qt.LeftButton:
            self._fit_to_win = not self._fit_to_win
            if self._fit_to_win:
                self._scale = 1.0
            self._update_scaled()

    def keyPressEvent(self, event):
        """
        Handles the following key events: cycling media, zooming media, fitting media to window
        :param event:
        :return:
        """
        if event.key() == Qt.Key_Escape:
            self.close()

        elif event.key() == Qt.Key_Right:
            # Next
            self._step(+1)

        elif event.key() == Qt.Key_Left:
            # Previous
            self._step(-1)

        elif event.key() in (Qt.Key_Plus, Qt.Key_Equal):
            self._zoom(1.25)

        elif event.key() == Qt.Key_Minus:
            self._zoom(0.8)

        elif event.key() == Qt.Key_0:  # fit-to-window reset
            self._fit_to_win = True
            self._update_scaled()

        else:
            super().keyPressEvent(event)

    def _step(self, delta: int):
        new_idx = self._idx + delta
        if 0 <= new_idx < len(self._paths):
            self._idx = new_idx
            self._load_image(self._paths[new_idx])

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        self._zoom(1.25 if delta > 0 else 0.8)

    def _zoom(self, factor: float):
        self._fit_to_win = False
        self._scale = max(0.1, min(self._scale * factor, 16.0))
        self._update_scaled()

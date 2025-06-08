from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QApplication


class ImageViewerDialog(QDialog):
    """
    Modal, borderless fullscreen viewer.
    """

    BACKDROP = "background-color: rgba(255, 0, 0, 0.5);"   # translucent blur

    def __init__(self, img_path: str, parent=None):
        super().__init__(parent)

        # Ensure widget stays on top
        self.setWindowFlag(Qt.FramelessWindowHint, True)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.setModal(True)

        # Create translucent blur for background
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet(self.BACKDROP)

        # Layout
        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._label)

        # Generate the scaled image with the appropriate args
        self._pix = QPixmap(img_path)
        if self._pix.isNull():
            self._label.setText(f"Could not load\n{Path(img_path).name}")
            self._label.setStyleSheet("color:white;")
        else:
            self._update_scaled()

        self.showFullScreen()

    def load_image(self, path: str):
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
        """Keeps aspect ratio; no cropping."""
        if self._pix.isNull():
            return
        scaled = self._pix.scaled(
            self.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self._label.setPixmap(scaled)

    # re-scale on every window size change
    def resizeEvent(self, ev):
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
        else:
            super().keyPressEvent(event)

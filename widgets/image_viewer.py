from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QApplication


class ImageViewerDialog(QDialog):
    """
    Modal, borderless fullscreen viewer.
    """

    def __init__(self, img_path: str, parent=None):
        super().__init__(parent)

        # Ensure widget stays on top
        self.setWindowFlag(Qt.FramelessWindowHint, True)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.showFullScreen()

        # Layout
        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setStyleSheet("background-color: black;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._label)

        # Load and show image
        self.load_image(img_path)
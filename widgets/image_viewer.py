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

    def load_image(self, path: str):
        """
        Load image from given path. Displays white, if not found
        :param path: path to image
        :return:
        """
        pix = QPixmap(path)
        if pix.isNull():
            self._label.setText(f"Could not load {Path(path).name}")
            self._label.setStyleSheet("color: white;")
        else:
            self._pix = pix
            self._show_scaled()

    # ------------------------------------------------------------------ #
    def _show_scaled(self):
        """
        Scale current image
        :return: None
        """
        if hasattr(self, "_pix"):
            scaled = self._pix.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self._label.setPixmap(scaled)

    def resizeEvent(self, event):
        """
        Scale image properly during resizing
        :param event:
        :return: None
        """
        self._show_scaled()
        super().resizeEvent(event)

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

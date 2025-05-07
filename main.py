import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from ui.ui_main import Ui_MainWindow  # From main.ui
from ui.custom_grips import CustomGrip  # Your refactored grips

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Make the window frameless and translucent
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(400, 300)

        # Set icon (optional, from PyDracula or your own)
        self.setWindowIcon(QIcon(":/icons/icon.ico"))

        # Load custom grips
        self.top_grip = CustomGrip(self, Qt.TopEdge)
        self.bottom_grip = CustomGrip(self, Qt.BottomEdge)
        self.left_grip = CustomGrip(self, Qt.LeftEdge)
        self.right_grip = CustomGrip(self, Qt.RightEdge)

        self.ui.title_bar.mouseMoveEvent = self.moveWindow

    def resizeEvent(self, event):
        """Ensure grips stay positioned on window resize."""
        self.top_grip.setGeometry(0, 0, self.width(), 10)
        self.bottom_grip.setGeometry(0, self.height() - 10, self.width(), 10)
        self.left_grip.setGeometry(0, 10, 10, self.height() - 20)
        self.right_grip.setGeometry(self.width() - 10, 10, 10, self.height() - 20)
        super().resizeEvent(event)

    def moveWindow(self, event):
        """Allow dragging the window by the title bar."""
        if event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.globalPosition().toPoint() - self.dragPos)
            self.dragPos = event.globalPosition().toPoint()
            event.accept()

    def mousePressEvent(self, event):
        self.dragPos = event.globalPosition().toPoint()
        super().mousePressEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    with open("themes/py_dracula_dark.qss", "r") as f:
        style = f.read()
        app.setStyleSheet(style)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

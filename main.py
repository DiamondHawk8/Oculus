from pathlib import Path
import sys
import logging

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog
from PySide6.QtCore import Qt
from PySide6.QtCore import QStringListModel, QSize

from ui.custom_grips import CustomGrip
from ui.ui_main import Ui_MainWindow

from managers.media_manager import MediaManager
from managers.search_manager import SearchManager
from managers.tag_manager import TagManager
from managers.keybind_manager import KeybindManager

from controllers.gallery_controller import GalleryController
from controllers.import_controller import ImportController
from controllers.search_controller import SearchController
from controllers.tab_controller import TabController

ACTIVE_BACKEND = "sqlite"
GALLERY_PAGE_INDEX = 0
WIDGET_PAGE_INDEX = 1
IMPORT_PAGE_INDEX = 2
SEARCH_PAGE_INDEX = 3

class MainWindow(QMainWindow):

    def __init__(self) -> None:
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        # Make borderless

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Create grips for window
        self._grips = [
            CustomGrip(self, Qt.LeftEdge, disable_color=True),
            CustomGrip(self, Qt.RightEdge, disable_color=True),
            CustomGrip(self, Qt.TopEdge, disable_color=True),
            CustomGrip(self, Qt.BottomEdge, disable_color=True),
        ]

        # backend managers
        self.tags = TagManager("oculus.db", backend=ACTIVE_BACKEND)
        self.media = MediaManager(parent=self)
        self.search = SearchManager(Path("oculus.db"), backend=ACTIVE_BACKEND)

        # Other Managers
        self.keybinds = KeybindManager(self)

        # Logic Controllers
        self.gallery_controller = GalleryController(self.ui, self.media, self.tags)
        self.search_controller = SearchController(self.ui, self.media, self.search)
        self.import_controller = ImportController(self, self.ui, self.media, self.tags, self.gallery_controller)

        self.tab_controller = TabController(
            tab_widget=self.ui.centralTabs,
            keybinds=self.keybinds,
        )

        # Persist if roots exist
        roots = self.tags.all_roots()
        if roots:
            self.gallery_controller.open_folder(roots[-1])  # show most recent import
        else:
            self.gallery_controller.populate_gallery([])  # empty state

        # Connect window buttons
        self.ui.closeAppBtn.clicked.connect(self.close)
        self.ui.minimizeAppBtn.clicked.connect(self.showMinimized)

        def _toggle_max_restore():
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()

        self.ui.maximizeRestoreAppBtn.clicked.connect(_toggle_max_restore)

        # Connect page buttons
        self.ui.btn_home.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(GALLERY_PAGE_INDEX))
        self.ui.btn_adv.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(WIDGET_PAGE_INDEX))
        self.ui.btn_import.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(IMPORT_PAGE_INDEX))
        self.ui.btn_search.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(SEARCH_PAGE_INDEX))


    # Glue edges
    def resizeEvent(self, event):
        super().resizeEvent(event)
        g = 10
        w, h = self.width(), self.height()

        self._grips[0].setGeometry(0, g, g, h - 2 * g)
        self._grips[1].setGeometry(w - g, g, g, h - 2 * g)
        self._grips[2].setGeometry(0, 0, w, g)
        self._grips[3].setGeometry(0, h - g, w, g)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

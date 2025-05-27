from pathlib import Path
import sys
import logging

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QListWidget
from PySide6.QtCore import Qt, QPoint, QFile, QTextStream
from PySide6.QtCore import QStringListModel, QSize

from ui.custom_grips import CustomGrip
from ui.ui_main import Ui_MainWindow
from managers.media_manager import MediaManager
from managers.search_manager import SearchManager
from managers.tag_manager import TagManager

from controllers.gallery_controller import GalleryController

ACTIVE_BACKEND = "sqlite"
GALLERY_PAGE_INDEX = 0
WIDGET_PAGE_INDEX = 1
IMPORT_PAGE_INDEX = 2
SEARCH_PAGE_INDEX = 3

import controllers.view_utils as view_utils

SIZE_PRESETS = {
    "Small": (64, QSize(82, 82)),
    "Medium": (96, QSize(118, 118)),
    "Large": (128, QSize(150, 150)),
    "XL": (192, QSize(216, 216)),
}


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

        # Logic Managers
        self.gallery_controller = GalleryController(self.ui, self.media, self.tags)

        # Connect Import page
        self.ui.chooseBtn.clicked.connect(self._choose_folder)
        self.media.scan_finished.connect(self._on_scan_finished)

        # Connect Search page
        self.ui.searchBtn.clicked.connect(self._exec_search)
        self.ui.searchEdit.returnPressed.connect(self._exec_search)
        self._search_items: dict[str, int] = {}

        # search results widgets
        self._results_model = QStringListModel()

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


        # Apply search page appearance options functionality
        self._search_grid = True  # default Search = grid
        self._search_preset = "Medium"
        view_utils.apply_view(self.ui.resultsList,
                              grid=self._search_grid,
                              preset=self._search_preset)

        # toggle button
        self.ui.btn_search_view.toggled.connect(self._toggle_search_view)

        # size combo
        self.ui.cmb_search_size.addItems(SIZE_PRESETS.keys())
        self.ui.cmb_search_size.setCurrentText(self._search_preset)
        self.ui.cmb_search_size.currentTextChanged.connect(self._change_search_size)


        # LEAVE HERE FOR NOW SO THAT SEARCH CAN WORK
        self.media.thumb_ready.connect(self._on_thumb_ready)

    # Import page slots
    def _choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choose image folder")
        if folder:
            self.ui.importStatus.setText("Scanning…")
            self.media.scan_folder(folder)

    def _on_scan_finished(self, paths: list[str]) -> None:

        # persist paths into DB so SearchManager can find them
        for p in paths:
            self.tags.add_media(p)

        self.ui.importStatus.setText(f"Found {len(paths)} files")
        self.gallery_controller.populate_gallery(paths)
        self.ui.stackedWidget.setCurrentWidget(self.ui.gallery_page)

    def _on_thumb_ready(self, path: str, pix) -> None:
        icon = QIcon(pix)

        # Search update
        idx = self._search_items.get(path)
        if idx is not None:
            self.ui.resultsList.item(idx).setIcon(icon)

    def _exec_search(self) -> None:
        term = self.ui.searchEdit.text().strip()
        if not term:
            return

        paths = (self.search.tag_search(term)
                 if any(sym in term for sym in "|,()")
                 else self.search.simple_search(term))

        rlist = self.ui.resultsList  # a QListWidget
        rlist.clear()
        self._search_items.clear()

        for p in paths:
            row = rlist.count()
            rlist.addItem(Path(p).name)
            self._search_items[p] = row
            self.media.thumb(p)  # async thumb request

        self.ui.stackedWidget.setCurrentIndex(SEARCH_PAGE_INDEX)

    # Search view functions

    def _toggle_search_view(self, checked: bool):
        self._search_grid = checked
        view_utils.apply_view(self.ui.resultsList,
                         grid=checked,
                         preset=self._search_preset)
        # Set scrolling speeds
        self.ui.resultsList.verticalScrollBar().setSingleStep(300)

    def _change_search_size(self, preset: str):
        self._search_preset = preset
        view_utils.apply_view(self.ui.resultsList,
                         grid=self._search_grid,
                         preset=preset)

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

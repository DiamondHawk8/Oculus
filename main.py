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

ACTIVE_BACKEND = "sqlite"
GALLERY_PAGE_INDEX = 0
WIDGET_PAGE_INDEX = 1
IMPORT_PAGE_INDEX = 2
SEARCH_PAGE_INDEX = 3

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


        self.tags = TagManager("oculus.db", backend=ACTIVE_BACKEND)
        self.search = SearchManager("oculus.db", backend=ACTIVE_BACKEND)

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
        self.media = MediaManager(parent=self)
        self.search = SearchManager(Path("oculus.db"), backend=ACTIVE_BACKEND)

        # Connect Import page
        self.ui.chooseBtn.clicked.connect(self._choose_folder)
        self.media.scan_finished.connect(self._on_scan_finished)

        # connect Gallery page
        # storage: path is QListWidgetItem (inserted on scan)
        self._gallery_items: dict[str, int] = {}
        self.media.thumb_ready.connect(self._on_thumb_ready)

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

        cached_paths = self.tags.all_paths()
        if cached_paths:
            self._populate_gallery(cached_paths)

        # Apply gallery page appeareance options functionality
        self._gallery_grid = True  # default mode
        self._gallery_preset = "Medium"
        self._apply_view(self.ui.galleryList,
                         grid=self._gallery_grid,
                         preset=self._gallery_preset)

        # toggle button
        self.ui.btn_gallery_view.toggled.connect(self._toggle_gallery_view)

        # combo
        self.ui.cmb_gallery_size.addItems(SIZE_PRESETS.keys())
        self.ui.cmb_gallery_size.setCurrentText(self._gallery_preset)
        self.ui.cmb_gallery_size.currentTextChanged.connect(self._change_gallery_size)

        # Apply search page appeareance options functionality
        self._search_grid = True  # default Search = grid
        self._search_preset = "Medium"
        self._apply_view(self.ui.resultsList,
                         grid=self._search_grid,
                         preset=self._search_preset)

        # toggle button
        self.ui.btn_search_view.setCheckable(True)
        self.ui.btn_search_view.setChecked(self._search_grid)
        self.ui.btn_search_view.toggled.connect(self._toggle_search_view)

        # size combo
        self.ui.cmb_search_size.addItems(SIZE_PRESETS.keys())
        self.ui.cmb_search_size.setCurrentText(self._search_preset)
        self.ui.cmb_search_size.currentTextChanged.connect(self._change_search_size)


        # Set scrolling sppeds
        self.ui.galleryList.verticalScrollBar().setSingleStep(30)
        self.ui.resultsList.verticalScrollBar().setSingleStep(30)


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
        self._populate_gallery(paths)
        self.ui.stackedWidget.setCurrentWidget(self.ui.gallery_page)

    # Gallery helpers
    # ----------------
    def _populate_gallery(self, paths: list[str]) -> None:
        glist = self.ui.galleryList
        glist.clear()
        self._gallery_items.clear()

        for p in paths:
            row = glist.count()
            item = glist.addItem(str(Path(p).name))
            self._gallery_items[p] = row
            # request thumb : will arrive async
            self.media.thumb(p)

    def _on_thumb_ready(self, path: str, pix) -> None:
        icon = QIcon(pix)

        # Gallery update
        idx = self._gallery_items.get(path)
        if idx is not None:
            self.ui.galleryList.item(idx).setIcon(icon)

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

    def _apply_view(self, widget: QListWidget, *, grid: bool, preset: str):
        print("applying view")
        icon, cell = SIZE_PRESETS[preset]
        if grid:
            print("applying grid")
            widget.setViewMode(QListWidget.IconMode)
            widget.setFlow(QListWidget.LeftToRight)
            widget.setWrapping(True)
            widget.setResizeMode(QListWidget.Adjust)
            widget.setIconSize(QSize(icon, icon))
            widget.setGridSize(cell)
        else:
            print("applying list")
            widget.setViewMode(QListWidget.ListMode)
            widget.setFlow(QListWidget.TopToBottom)
            widget.setWrapping(False)
            widget.setIconSize(QSize(32, 32))
            widget.setGridSize(QSize())  # resets grid

    # Gallery and search view functions
    def _toggle_gallery_view(self, checked: bool):
        self._gallery_grid = checked
        self._apply_view(self.ui.galleryList,
                         grid=checked,
                         preset=self._gallery_preset)

    def _change_gallery_size(self, preset: str):
        self._gallery_preset = preset
        self._apply_view(self.ui.galleryList,
                         grid=self._gallery_grid,
                         preset=preset)


    def _toggle_search_view(self, checked: bool):
        self._search_grid = checked
        self._apply_view(self.ui.resultsList,
                         grid=checked,
                         preset=self._search_preset)

    def _change_search_size(self, preset: str):
        self._search_preset = preset
        self._apply_view(self.ui.resultsList,
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

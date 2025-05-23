from pathlib import Path
import sys
import logging

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog
from PySide6.QtCore import Qt, QPoint, QFile, QTextStream
from PySide6.QtCore import QStringListModel

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


class MainWindow(QMainWindow):

    def __init__(self) -> None:
        super().__init__()

        self.tags = TagManager("oculus.db", backend=ACTIVE_BACKEND)
        self.search = SearchManager("oculus.db", backend=ACTIVE_BACKEND)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

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

        # search results widgets
        self._results_model = QStringListModel()
        self.ui.resultsList.setModel(self._results_model)

        # Connect page buttons
        self.ui.btn_home.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(GALLERY_PAGE_INDEX))
        self.ui.btn_adv.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(WIDGET_PAGE_INDEX))
        self.ui.btn_import.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(IMPORT_PAGE_INDEX))
        self.ui.btn_search.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(SEARCH_PAGE_INDEX))

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
        idx = self._gallery_items.get(path)
        if idx is None:
            return
        item = self.ui.galleryList.item(idx)
        item.setIcon(QIcon(pix))


    def _exec_search(self) -> None:
        term = self.ui.searchEdit.text().strip()
        if not term:
            return

        # Decide which search
        paths = (self.search.tag_search(term)
                 if any(sym in term for sym in "|,()")
                 else self.search.simple_search(term))

        # Update QListView via its model
        self._results_model.setStringList([Path(p).name for p in paths])

        # Warm the cache
        for p in paths:
            self.media.thumb(p)

        self.ui.stackedWidget.setCurrentIndex(SEARCH_PAGE_INDEX)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

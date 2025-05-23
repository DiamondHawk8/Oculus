from pathlib import Path
import sys
import logging

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog
from PySide6.QtCore import Qt, QPoint, QFile, QTextStream

from ui.custom_grips import CustomGrip
from ui.ui_main import Ui_MainWindow
from managers.media_manager import MediaManager
from managers.search_manager import SearchManager

ACTIVE_BACKEND = "sqlite"


class MainWindow(QMainWindow):

    def __init__(self) -> None:
        super().__init__()
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

    # Import page slots
    def _choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choose image folder")
        if folder:
            self.ui.import_page.importStatus.setText("Scanning…")
            self.media.scan_folder(folder)

    def _on_scan_finished(self, paths: list[str]) -> None:
        self.ui.import_page.importStatus.setText(f"Found {len(paths)} files")
        self._populate_gallery(paths)
        self.ui.pages.setCurrentWidget(self.ui.gallery_page)

    # Gallery helpers
    # ----------------
    def _populate_gallery(self, paths: list[str]) -> None:
        glist = self.ui.gallery_page.galleryList
        glist.clear()
        self._gallery_items.clear()

        for p in paths:
            row = glist.count()
            item = glist.addItem(str(Path(p).name))
            self._gallery_items[p] = row
            # request thumb → will arrive async
            self.media.thumb(p)

    def _on_thumb_ready(self, path: str, pix) -> None:
        """Update QListWidgetItem icon when thumbnail arrives."""
        idx = self._gallery_items.get(path)
        if idx is None:
            return
        item = self.ui.gallery_page.galleryList.item(idx)
        item.setIcon(pix)

    def _exec_search(self) -> None:
        term = self.ui.searchEdit.text().strip()
        if not term:
            return
        # OR / , / () => tag expression
        if any(sym in term for sym in "|,()"):
            paths = self.search.tag_search(term)
        else:
            paths = self.search.simple_search(term)

        rlist = self.ui.search_page.resultsList
        rlist.clear()
        for p in paths:
            rlist.addItem(str(Path(p).name))
            self.media.thumb(p)  # cache

        self.ui.pages.setCurrentWidget(self.ui.search_page)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

from pathlib import Path

from PySide6.QtCore import QStringListModel

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon

import controllers.view_utils as view_utils


SIZE_PRESETS = {
    "Small": (64, QSize(82, 82)),
    "Medium": (96, QSize(118, 118)),
    "Large": (128, QSize(150, 150)),
    "XL": (192, QSize(216, 216)),
}

GALLERY_PAGE_INDEX = 0
WIDGET_PAGE_INDEX = 1
IMPORT_PAGE_INDEX = 2
SEARCH_PAGE_INDEX = 3

class SearchController:
    def __init__(self, ui, media_manager, search_manager):
        self.ui = ui
        self.media_manager = media_manager
        self.search_manager = search_manager

        self._search_items: dict[str, int] = {}

        # Apply search defaults
        self._search_grid = True
        self._search_preset = "Medium"
        view_utils.apply_view(self.ui.resultsList,
                              grid=self._search_grid,
                              preset=self._search_preset)

        # Connect Search bar
        self.ui.searchBtn.clicked.connect(self._exec_search)
        self.ui.searchEdit.returnPressed.connect(self._exec_search)

        # Search Results widgets
        self._results_model = QStringListModel()

        # Connect thumbnail method to media signals
        self.media_manager.thumb_ready.connect(self._on_thumb_ready)

        # toggle button
        self.ui.btn_search_view.toggled.connect(self.toggle_view)

        # size combo
        self.ui.cmb_search_size.addItems(SIZE_PRESETS.keys())
        self.ui.cmb_search_size.setCurrentText(self._search_preset)
        self.ui.cmb_search_size.currentTextChanged.connect(self.change_size)

    def _exec_search(self) -> None:
        term = self.ui.searchEdit.text().strip()
        if not term:
            return

        paths = (self.search_manager.tag_search(term)
                 if any(sym in term for sym in "|,()")
                 else self.search_manager.simple_search(term))

        rlist = self.ui.resultsList  # a QListWidget
        rlist.clear()
        self._search_items.clear()

        for p in paths:
            row = rlist.count()
            rlist.addItem(Path(p).name)
            self._search_items[p] = row
            self.media_manager.thumb(p)  # async thumb request

        self.ui.stackedWidget.setCurrentIndex(SEARCH_PAGE_INDEX)

    def _on_thumb_ready(self, path: str, pix) -> None:
        icon = QIcon(pix)

        # Search update
        idx = self._search_items.get(path)
        if idx is not None:
            self.ui.resultsList.item(idx).setIcon(icon)

    def toggle_view(self, checked):
        self._search_grid = checked
        view_utils.apply_view(self.ui.resultsList,
                              grid=checked,
                              preset=self._search_preset)
        # Set scrolling speeds
        self.ui.resultsList.verticalScrollBar().setSingleStep(300)
    def change_size(self, preset):
        self._search_preset = preset
        view_utils.apply_view(self.ui.resultsList,
                              grid=self._search_grid,
                              preset=preset)
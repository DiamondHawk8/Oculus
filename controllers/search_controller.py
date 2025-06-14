from pathlib import Path
import logging

from PySide6.QtCore import QSize, QModelIndex
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QStyle

import controllers.view_utils as view_utils
from models.thumbnail_model import ThumbnailListModel

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

_SORT_KEYS = {
    0: "name",
    1: "date",
    2: "size",
    3: "weight",
}

# TODO allow folders showing in search to be toggled
SHOW_FOLDERS = True

class SearchController:
    def __init__(self, ui, media_manager, search_manager):
        self.ui = ui
        self.media_manager = media_manager
        self.search_manager = search_manager

        self._search_items: dict[str, int] = {}
        self._result_paths: list[str] = []

        self._model = ThumbnailListModel()
        self.ui.resultsList.setModel(self._model)

        self._folder_icon = QApplication.style().standardIcon(QStyle.SP_DirIcon)

        # Apply search defaults
        self._search_grid = True
        self._search_preset = "Medium"
        view_utils.apply_view(self.ui.resultsList,
                              grid=self._search_grid,
                              preset=self._search_preset)

        # Connect Search bar
        self.ui.searchBtn.clicked.connect(self._exec_search)
        self.ui.searchEdit.returnPressed.connect(self._exec_search)

        # Connect thumbnail method to media signals
        self.media_manager.thumb_ready.connect(self._on_thumb_ready)

        # toggle button
        self.ui.btn_search_view.toggled.connect(self.toggle_view)

        # size combo
        self.ui.cmb_search_size.addItems(SIZE_PRESETS.keys())
        self.ui.cmb_search_size.setCurrentText(self._search_preset)
        self.ui.cmb_search_size.currentTextChanged.connect(self.change_size)

        # Sort hooks
        self.ui.cmb_search_sortKey.currentIndexChanged.connect(self._apply_sort)
        self.ui.btn_search_sortDir.toggled.connect(self._apply_sort)

    def _exec_search(self) -> None:
        term = self.ui.searchEdit.text().strip()

        if not term:
            # if blank query, return all media
            self._result_paths = self.media_manager.all_paths(files_only=False)
            self._apply_sort()

        paths = (
            self.search_manager.tag_search(term)
            if any(sym in term for sym in "|,()")
            else self.search_manager.simple_search(term)
        )

        self._result_paths = paths
        self._apply_sort()

        self.ui.stackedWidget.setCurrentIndex(SEARCH_PAGE_INDEX)

    def _apply_sort(self):
        if not self._result_paths:
            return

        key = _SORT_KEYS.get(self.ui.cmb_search_sortKey.currentIndex(), "name")
        asc = not self.ui.btn_search_sortDir.isChecked()
        ordered = self.media_manager.order_subset(self._result_paths, key, asc)

        # repopulate model
        self._model.set_paths(ordered)
        self._search_items = {p: i for i, p in enumerate(ordered)}

        for p in ordered:
            if Path(p).is_dir():
                self._model.update_icon(p, self._folder_icon)
            else:
                self.media_manager.thumb(p)

    def _on_thumb_ready(self, path: str, pix: QPixmap) -> None:
        icon = QIcon(pix)

        # Search update
        if path in self._search_items:
            self._model.update_icon(path, icon)

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

    def _on_item_activated(self, index: QModelIndex):
        """
        self.tab_controller.open_in_new_tab(
            new_gallery_page_for(folder_path), Path(folder_path).name
        )
        """
        pass

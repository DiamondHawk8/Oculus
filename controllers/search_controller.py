from pathlib import Path

from PySide6.QtCore import QSize, QModelIndex
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QListView

import controllers.view_utils as view_utils
from models.thumbnail_model import ThumbnailListModel

SIZE_PRESETS = {
    "Small":  (64,  QSize(82,  82)),
    "Medium": (96,  QSize(118, 118)),
    "Large":  (128, QSize(150, 150)),
    "XL":     (192, QSize(216, 216)),
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

        self._model = ThumbnailListModel()
        self.ui.resultsList.setModel(self._model)

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

    def _exec_search(self) -> None:
        term = self.ui.searchEdit.text().strip()
        if not term:
            return

        paths = (
            self.search_manager.tag_search(term)
            if any(sym in term for sym in "|,()")
            else self.search_manager.simple_search(term)
        )

        self._model.set_paths(paths)
        self._search_items = {p: i for i, p in enumerate(paths)}

        for p in paths:
            self.media_manager.thumb(p)

        self.ui.stackedWidget.setCurrentIndex(SEARCH_PAGE_INDEX)

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
        # TODO allow searched files' folder to be added to gallery tab
        """
        self.tab_controller.open_in_new_tab(
            new_gallery_page_for(folder_path), Path(folder_path).name
        )
        """
        pass


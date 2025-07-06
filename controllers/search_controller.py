from pathlib import Path
import logging

from PySide6.QtCore import QSize, QModelIndex, Qt, QEvent, QObject
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QStyle

import controllers.utils.view_utils as view_utils
from controllers.utils.state_utils import ViewerState
from models.thumbnail_model import ThumbnailListModel

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

logger = logging.getLogger(__name__)


class SearchController(QObject):
    def __init__(self, ui, media_manager, tag_manager, search_manager, tab_controller, host_widget, gallery_controller):
        super().__init__()

        self.ui = ui
        self.media_manager = media_manager
        self.tag_manager = tag_manager
        self.search_manager = search_manager
        self.tab_controller = tab_controller
        self.gallery_controller = gallery_controller

        self._search_items: dict[str, int] = {}
        self._result_paths: list[str] = []

        self.viewer = ViewerState()
        self._host_widget = host_widget

        self._model = ThumbnailListModel()
        self.ui.resultsList.setModel(self._model)

        self._folder_icon = QApplication.style().standardIcon(QStyle.SP_DirIcon)

        # Apply search defaults
        self._search_grid = True
        self._search_preset = "Medium"
        view_utils.apply_gallery_view(self.ui.resultsList, grid=self._search_grid, preset=self._search_preset)

        # Connect Search bar
        self.ui.searchBtn.clicked.connect(self._exec_search)
        self.ui.searchEdit.returnPressed.connect(self._exec_search)

        # Connect thumbnail method to media signals
        self.media_manager.thumb_ready.connect(self._on_thumb_ready)

        # toggle button
        self.ui.btn_search_view.toggled.connect(self._toggle_view)

        # size combo
        self.ui.cmb_gallery_size.addItems(view_utils.icon_preset.__globals__["_SIZE_PRESETS"].keys())
        self.ui.cmb_search_size.setCurrentText(self._search_preset)
        self.ui.cmb_search_size.currentTextChanged.connect(self.change_size)

        # Media activation hook
        self.ui.resultsList.activated.connect(self._on_item_activated)
        self.ui.resultsList.viewport().installEventFilter(self)

        # Sort hooks
        self.ui.cmb_search_sortKey.currentIndexChanged.connect(self._apply_sort)
        self.ui.btn_search_sortDir.toggled.connect(self._apply_sort)

        logger.info("Search setup complete")

    def _exec_search(self) -> None:
        logger.info("Search started")
        term = self.ui.searchEdit.text().strip()
        logger.debug(f"Search query: {term}")

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
        logger.info("Sort started")
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
        logger.debug(f"Thumbnail read at path: {path}")
        icon = QIcon(pix)

        # Search update
        if path in self._search_items:
            self._model.update_icon(path, icon)

    def _toggle_view(self, checked):
        logger.info("_toggle_view called")
        self._search_grid = checked
        view_utils.apply_gallery_view(self.ui.resultsList, grid=checked, preset=self._search_preset)
        # Set scrolling speeds
        self.ui.resultsList.verticalScrollBar().setSingleStep(300)

    def change_size(self, preset):
        logger.info("_change_size called")
        self._search_preset = preset
        view_utils.apply_gallery_view(self.ui.resultsList, grid=self._search_grid, preset=preset)

    def _open_viewer(self, index: QModelIndex):
        path = self._model.data(index, Qt.UserRole)
        stack = self.media_manager.stack_paths(path)

        # navigation list -> skip any file that is a variant
        paths = [p for p in self._model.get_paths()
                 if Path(p).is_file() and not self.media_manager.is_variant(p)]
        cur_idx = paths.index(stack[0])  # base index

        # open viewer at base, but pass full stack so Up/Down still work
        if self.viewer.callback:
            self.viewer.open_via_callback(paths, cur_idx, stack,
                                          self._host_widget, self.media_manager)
        else:
            self.viewer.open(self._model, index, self.media_manager,
                             self.tag_manager, self._host_widget)

    def set_viewer_callback(self, fn):
        self.viewer.callback = fn

    def _on_item_activated(self, index: QModelIndex):
        if not index.isValid():
            return
        abs_path = self._model.data(index, Qt.UserRole)

        if Path(abs_path).is_dir():
            # tell the existing GalleryController to switch folders
            self.gallery_controller.open_folder(abs_path)
            # bring Gallery page to front
            # TODO Allow for auto switching to gallery to be optional
            self.ui.stackedWidget.setCurrentIndex(GALLERY_PAGE_INDEX)
        else:
            self._open_viewer(index)

    def eventFilter(self, obj, event):
        if (obj is self.ui.resultsList.viewport()
                and event.type() == QEvent.MouseButtonRelease
                and event.button() == Qt.MiddleButton):

            idx = self.ui.resultsList.indexAt(event.pos())
            if not idx.isValid():
                return True  # swallow event

            abs_path = self._model.data(idx, Qt.UserRole)
            target_folder = abs_path if Path(abs_path).is_dir() else str(Path(abs_path).parent)

            self.tab_controller.open_folder_tab(
                root_path=target_folder,
                title=Path(target_folder).name,
                switch=True
            )
            # TODO Allow for auto switching to gallery to be optional
            self.ui.stackedWidget.setCurrentIndex(GALLERY_PAGE_INDEX)
            return True

        return super().eventFilter(obj, event)

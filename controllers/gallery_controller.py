from pathlib import Path

from PySide6.QtCore import Qt, QSize, QModelIndex, QEvent
from PySide6.QtGui import QIcon, QKeySequence, QAction
from PySide6.QtWidgets import QListView, QMenu

import controllers.view_utils as view_utils
from controllers import tab_controller
from models.thumbnail_model import ThumbnailListModel

from PySide6.QtWidgets import QApplication, QStyle

SIZE_PRESETS = {
    "Small": (64, QSize(82, 82)),
    "Medium": (96, QSize(118, 118)),
    "Large": (128, QSize(150, 150)),
    "XL": (192, QSize(216, 216)),
}


class GalleryController:
    def __init__(self, ui, media_manager, tag_manager, tab_controller):
        self.ui = ui
        self.media_manager = media_manager
        self.tag_manager = tag_manager
        self.tab_controller = tab_controller

        # model & view
        self._model = ThumbnailListModel()
        self.ui.galleryList.setViewMode(QListView.IconMode)
        self.ui.galleryList.setResizeMode(QListView.Adjust)
        self.ui.galleryList.setModel(self._model)

        self._gallery_items: dict[str, int] = {}

        # Apply gallery defaults
        self._gallery_grid = True  # default mode
        self._gallery_preset = "Medium"
        view_utils.apply_view(self.ui.galleryList,
                              grid=self._gallery_grid,
                              preset=self._gallery_preset)

        # Create folder icon
        self._folder_icon = QApplication.style().standardIcon(QStyle.SP_DirIcon)

        # Create navigation structs
        self._history: list[str] = []
        self._cursor: int = -1

        idx = self.tab_controller.open_in_new_tab(self.ui.tabRoot, "Root", switch=True)
        # self.open_folder(root_path) is still called from ImportController once scanning finishes

        # Signals

        self.ui.galleryList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.galleryList.customContextMenuRequested.connect(self._show_ctx_menu)

        # Connect event driven functionality
        self.ui.galleryList.viewport().installEventFilter(self)

        # Hook Back/Forward buttons
        self.ui.btn_back.clicked.connect(self.go_back)
        if hasattr(self.ui, "btn_forward"):
            self.ui.btn_forward.clicked.connect(self.go_forward)

        # Connect double-click / Enter activation
        self.ui.galleryList.doubleClicked.connect(self._on_item_activated)
        self.ui.galleryList.activated.connect(self._on_item_activated)

        # Connect thumbnail method to media signals
        self.media_manager.thumb_ready.connect(self._on_thumb_ready)

        # Connect button to toggle between list and grid view
        self.ui.btn_gallery_view.toggled.connect(self._toggle_view)

        # Register keyboard shortcuts (inside Gallery only)
        self._add_shortcut("Alt+Left", self.go_back)
        self._add_shortcut("Alt+Right", self.go_forward)

        # Obtain any existing media paths
        cached_paths = self.tag_manager.all_paths()
        if cached_paths:
            self.populate_gallery(cached_paths)

        # TODO derive size preset dynamically
        # Connect dropdown to select icon sizes
        self.ui.cmb_gallery_size.addItems(SIZE_PRESETS.keys())
        self.ui.cmb_gallery_size.setCurrentText(self._gallery_preset)
        self.ui.cmb_gallery_size.currentTextChanged.connect(self._change_size)

    # push a folder’s contents into the model
    def _push_page(self, folder_abspath: str):
        """
        Refresh view with contents of folder_abspath
        Folders first (α-sorted) then image files (α-sorted).
        """
        folder = Path(folder_abspath)
        if not folder.is_dir():
            return

        subdirs = [
            str(p) for p in folder.iterdir() if p.is_dir()
        ]
        images = [
            str(p) for p in folder.iterdir()
            if p.is_file() and p.suffix.lower() in {".jpg", ".png", ".gif", ".bmp"}
        ]

        #   Folders first, then files – each group sorted case-insensitively
        paths = sorted(subdirs, key=str.lower) + sorted(images, key=str.lower)
        self.populate_gallery(paths)

    # ---------------------------- Nav methods ----------------------------

    def open_folder(self, folder_abspath: str):
        """
        Method that is called when a folder is opened to properly display contents and preserve hierarchy
        :param folder_abspath: The absolute path to the folder
        :return: None
        """

        if self._cursor >= 0 and self._history[self._cursor] == folder_abspath:
            return  # same folder; ignore

        # prune forward history if branched
        self._history = self._history[: self._cursor + 1]
        self._history.append(folder_abspath)
        self._cursor += 1
        self._push_page(folder_abspath)

        # enable/disable nav buttons
        self.ui.btn_back.setEnabled(self._cursor > 0)
        if hasattr(self.ui, "btn_forward"):
            self.ui.btn_forward.setEnabled(False)

    def _on_item_activated(self, index: QModelIndex):
        """
        Method that determines what should be done when an item is activated (usually via clicking)
        :param index: The item that is being activated
        :return: None
        """
        # Obtain
        path = self._model.data(index, Qt.UserRole)

        # If item does not contain any usable data
        if not path:
            return

        # If the item is recognized as a folder, call the open folder method on the path
        if Path(path).is_dir():
            self.open_folder(path)

        # Otherwise, its media, and it will be opened accordingly
        else:
            self._open_viewer(path)  # TODO hook to ImageViewerDialog

    def go_back(self):
        """
        Method to navigate to previously accessed directory in gallery
        :return: None
        """
        if self._cursor <= 0:
            return
        self._cursor -= 1
        self._push_page(self._history[self._cursor])
        self.ui.btn_back.setEnabled(self._cursor > 0)
        if hasattr(self.ui, "btn_forward"):
            self.ui.btn_forward.setEnabled(True)

    def go_forward(self):
        """
        Method to navigate to previously accessed directory in gallery
        :return: None
        """
        if self._cursor + 1 >= len(self._history):
            return
        self._cursor += 1
        self._push_page(self._history[self._cursor])
        self.ui.btn_back.setEnabled(True)
        if hasattr(self.ui, "btn_forward"):
            self.ui.btn_forward.setEnabled(self._cursor + 1 < len(self._history))

    # ---------------------------- Thumbnail methods ----------------------------
    def populate_gallery(self, paths: list[str]) -> None:
        """
        Method that takes in a list of paths, and creates the gallery data structures accordingly
        :param paths:
        :return:
        """
        self._model.set_paths(paths)
        self._gallery_items = {p: i for i, p in enumerate(paths)}

        for p in paths:
            if Path(p).is_file():
                self.media_manager.thumb(p)
            # If is folder
            else:
                self._model.update_icon(p, self._folder_icon)

    def _on_thumb_ready(self, path: str, pix) -> None:
        icon = QIcon(pix)
        self._model.update_icon(path, icon)

    # ---------------------------- Appearance methods ----------------------------

    def _toggle_view(self, checked):
        self._gallery_grid = checked
        view_utils.apply_view(self.ui.galleryList,
                              grid=checked,
                              preset=self._gallery_preset)
        self.ui.galleryList.verticalScrollBar().setSingleStep(300)

    def _change_size(self, preset):
        self._gallery_preset = preset
        view_utils.apply_view(self.ui.galleryList,
                              grid=self._gallery_grid,
                              preset=preset)

    # ---------------------------- Other methods ----------------------------

    # helper for local shortcuts (keeps them limited to gallery page)
    def _add_shortcut(self, keyseq: str, slot):
        act = QAction(self.ui.gallery_page)
        act.setShortcut(QKeySequence(keyseq))
        act.triggered.connect(slot)
        self.ui.gallery_page.addAction(act)

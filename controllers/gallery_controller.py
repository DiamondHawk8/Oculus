from pathlib import Path

from PySide6.QtCore import Qt, QSize, QModelIndex, QEvent, QObject
from PySide6.QtGui import QIcon, QKeySequence, QAction
from PySide6.QtWidgets import QListView, QMenu, QWidget, QApplication, QStyle

import controllers.view_utils as view_utils

from models.thumbnail_model import ThumbnailListModel

from ui.ui_gallery_tab import Ui_Form

from widgets.image_viewer import ImageViewerDialog

import logging

SIZE_PRESETS = {
    "Small": (64, QSize(82, 82)),
    "Medium": (96, QSize(118, 118)),
    "Large": (128, QSize(150, 150)),
    "XL": (192, QSize(216, 216)),
}

_SORT_KEYS = {
    0: "name",
    1: "date",
    2: "size",
}

logger = logging.getLogger(__name__)


class GalleryController:
    def __init__(self, ui, media_manager, tag_manager, tab_controller, host_widget):
        super().__init__()

        self.ui = ui
        self.media_manager = media_manager
        self.tag_manager = tag_manager
        self.tab_controller = tab_controller
        # Attribute used to differentiate between the root gallery page and other opened tabs
        self._host_widget = host_widget

        # View dialog opened for any given gallery
        self._viewer = None
        self._viewer_open = False

        # model & view
        self._model = ThumbnailListModel()
        self.ui.galleryList.setViewMode(QListView.IconMode)
        self.ui.galleryList.setResizeMode(QListView.Adjust)
        self.ui.galleryList.setModel(self._model)

        self._gallery_items: dict[str, int] = {}

        # Apply gallery defaults
        self._gallery_grid = True  # default mode
        self._gallery_preset = "Medium"
        logger.debug("Applying gallery view")
        view_utils.apply_view(self.ui.galleryList,
                              grid=self._gallery_grid,
                              preset=self._gallery_preset)

        # Create folder icon
        self._folder_icon = QApplication.style().standardIcon(QStyle.SP_DirIcon)

        # Create navigation structs
        self._history: list[str] = []
        self._cursor: int = -1

        # Signals
        self._mid_filter = _MiddleClickFilter(self.ui.galleryList, self._open_in_new_tab)
        self.ui.galleryList.viewport().installEventFilter(self._mid_filter)

        self.ui.galleryList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.galleryList.customContextMenuRequested.connect(self._show_ctx_menu)

        # Hook Back/Forward buttons
        ui.btn_back.clicked.connect(lambda: self._navigate(-1))
        if hasattr(ui, "btn_forward"):
            ui.btn_forward.clicked.connect(lambda: self._navigate(+1))
        # Hook keyboard
        self._add_shortcut("Alt+Left", lambda: self._navigate(-1))
        self._add_shortcut("Alt+Right", lambda: self._navigate(+1))

        # Connect double-click / Enter activation
        self.ui.galleryList.activated.connect(self._on_item_activated)

        # Connect thumbnail method to media signals
        self.media_manager.thumb_ready.connect(self._on_thumb_ready)

        # Connect button to toggle between list and grid view
        self.ui.btn_gallery_view.toggled.connect(self._toggle_view)

        # Connect sorting functionality
        self.ui.cmb_gallery_sortKey.currentIndexChanged.connect(self._apply_sort)
        self.ui.btn_gallery_sortDir.toggled.connect(self._apply_sort)
        self._apply_sort()  # initial sort

        # Obtain any existing media paths
        cached_paths = self.media_manager.folder_paths()
        if cached_paths:
            self.populate_gallery(cached_paths)

        # TODO derive size preset dynamically
        # Connect dropdown to select icon sizes
        self.ui.cmb_gallery_size.addItems(SIZE_PRESETS.keys())
        self.ui.cmb_gallery_size.setCurrentText(self._gallery_preset)
        self.ui.cmb_gallery_size.currentTextChanged.connect(self._change_size)

        logger.info("Gallery setup complete")

    def _push_page(self, folder_abspath: str):
        """
        Refresh view with contents of folder_abspath
        Folders first then image files.
        """

        logger.debug(f"_push_page called with folder abspath: {folder_abspath}")

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

        paths = sorted(subdirs, key=str.lower) + sorted(images, key=str.lower)
        logger.debug(f"Populating gallery with paths:\n{paths}")
        self.populate_gallery(paths)

    # ---------------------------- Nav methods ----------------------------

    def open_folder(self, folder_abspath: str):
        """
        Method that is called when a folder is opened to properly display contents and preserve hierarchy
        :param folder_abspath: The absolute path to the folder
        :return: None
        """

        logger.debug(f"open_folder called with folder abspath: {folder_abspath}")

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

        logger.debug(f"on_item_activated called with index: {index}")

        # Obtain
        path = self._model.data(index, Qt.UserRole)

        logger.debug(f"path: {path}")

        # If item does not contain any usable data
        if not path:
            logger.warning(f"Item at {path} does not exist")
            return

        # If the item is recognized as a folder, call the open folder method on the path
        if Path(path).is_dir():
            self.open_folder(path)

        # Otherwise, its media, and it will be opened accordingly
        else:
            self._open_viewer(index)

    def _navigate(self, delta: int) -> None:
        logger.debug(f"navigate {delta}")
        nxt = self._cursor + delta
        if 0 <= nxt < len(self._history):
            self._cursor = nxt
            self._push_page(self._history[self._cursor])
            self._update_nav_buttons()

    def _update_nav_buttons(self) -> None:
        logger.debug("_update_nav_buttons called")
        self.ui.btn_back.setEnabled(self._cursor > 0)
        if hasattr(self.ui, "btn_forward"):
            self.ui.btn_forward.setEnabled(self._cursor + 1 < len(self._history))

    # ---------------------------- Thumbnail methods ----------------------------
    def populate_gallery(self, paths: list[str]) -> None:
        """
        Method that takes in a list of paths, and creates the gallery data structures accordingly
        :param paths:
        :return:
        """
        logger.info("populate_gallery called")
        logger.debug(f"populate_gallery called with paths: {paths}")
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
        logger.info("toggle_view called")
        self._gallery_grid = checked
        view_utils.apply_view(self.ui.galleryList,
                              grid=checked,
                              preset=self._gallery_preset)
        self.ui.galleryList.verticalScrollBar().setSingleStep(300)

    def _change_size(self, preset):
        logger.info("_change_size called")
        self._gallery_preset = preset
        view_utils.apply_view(self.ui.galleryList,
                              grid=self._gallery_grid,
                              preset=preset)

    def _apply_sort(self):
        logger.info("_apply_sort called")
        # Determine key + direction
        key = _SORT_KEYS.get(self.ui.cmb_gallery_sortKey.currentIndex(), "name")
        asc = not self.ui.btn_gallery_sortDir.isChecked()
        logger.debug(f"_apply_sort key: {key}, asc: {asc}")

        # Split current view into dirs vs. files
        current_paths = self._model.get_paths()  # whatever is shown now
        dirs = [p for p in current_paths if Path(p).is_dir()]
        files = [p for p in current_paths if Path(p).is_file()]
        logger.debug(f"_apply_sort dirs: {dirs}, files: {files}")

        # Sort only the file slice
        ordered_files = self.media_manager.order_subset(files, key, asc)
        logger.debug(f"_apply_sort ordered_files: {ordered_files}")

        # Combine folders first (unsorted), then ordered files
        self.populate_gallery(dirs + ordered_files)

    # ---------------------------- Other methods ----------------------------

    def _show_ctx_menu(self, pos):
        logger.debug(f"_show_ctx_menu called, context menu opening at {pos}")
        idx = self.ui.galleryList.indexAt(pos)
        if not idx.isValid():
            return
        menu = QMenu(self.ui.galleryList)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #444;
            }
            QMenu::item:selected {
                background-color: #3c3f41;
            }
        """)
        act_new = menu.addAction("Open in New Tab")
        if menu.exec(self.ui.galleryList.mapToGlobal(pos)) == act_new:
            self._open_in_new_tab(idx)

    def eventFilter(self, obj, event):
        # If MMB on the gallery list
        if obj is self.ui.galleryList.viewport() and event.type() == QEvent.MouseButtonRelease:
            if event.button() == Qt.MiddleButton:
                # If the index is valid, open a new tab for it
                idx = self.ui.galleryList.indexAt(event.pos())
                logger.debug(f"MMB pressed at {event.pos()}, index: {idx}")
                if idx.isValid():
                    self._open_in_new_tab(idx)
                    return True
        return super().eventFilter(obj, event)

    def _open_in_new_tab(self, index: QModelIndex) -> None:
        logger.info("_open_in_new_tab called")
        logger.debug(f"_open_in_new_tab index: {index}")
        path = self._model.data(index, Qt.UserRole)
        if not path:
            logger.warning(f"Item at {path} does not exist")
            return

        # Clone a fresh tab page containing a QListView & toolbar
        page_widget, page_ui = self._build_gallery_tab()
        clone_controller = GalleryController(
            ui=page_ui,
            media_manager=self.media_manager,
            tag_manager=self.tag_manager,
            tab_controller=self.tab_controller,
            host_widget=page_widget
        )
        logger.debug(f"New gallery instance created: {clone_controller}")

        # Point it at the folder (or file's parent) that was clicked
        target = path if Path(path).is_dir() else str(Path(path).parent)
        logger.debug(f"New gallery target path: {target}")
        clone_controller.open_folder(target)

        # Hand it to TabController
        tab_title = Path(target).name or "Root"
        self.tab_controller.open_in_new_tab(page_widget, tab_title)

    # helper for local shortcuts (keeps them limited to gallery page)
    def _add_shortcut(self, keyseq: str, slot):
        # ensure that shortcuts are attached to gallery page itself rather than any of the tabs
        act = QAction(self._host_widget)
        act.setShortcut(QKeySequence(keyseq))
        act.triggered.connect(slot)
        act.setShortcutContext(Qt.ApplicationShortcut)
        self._host_widget.addAction(act)

    def _build_gallery_tab(self) -> tuple[QWidget, Ui_Form]:
        """
        Creates a blank Gallery tab page (ListView + buttons already laid out
        in Designer as Ui_GalleryTab) and return (widget, ui_object)
        :return: None
        """
        logger.debug("_build_gallery_tab called")
        widget = QWidget()
        ui_local = Ui_Form()
        ui_local.setupUi(widget)
        logger.debug(f"Newly built gallery tab data {widget, ui_local}")
        return widget, ui_local

    def _open_viewer(self, index: QModelIndex):
        logger.info("Opening media viewer")
        logger.debug(f"_open_viewer called with index: {index}")
        if self._viewer_open:
            logger.warning("Viewer instance is already open")
            return

        path = self._model.data(index, Qt.UserRole)
        if not path or not Path(path).is_file():
            logger.warning(f"Item at {path} does not exist")
            return

        # assemble the current list of file paths in display order
        paths = [p for p in self._model.get_paths() if Path(p).is_file()]
        cur_idx = paths.index(path)

        self._viewer_open = True
        logger.debug(f"Attempting to create ImageViewerDialog with args: \n"
                     f"path: {paths}, cur_idx: {cur_idx}, parent: {self._host_widget}")
        dlg = ImageViewerDialog(paths, cur_idx, parent=self._host_widget)

        # set viewer open state to false upon operation complete
        dlg.finished.connect(lambda *_: setattr(self, "_viewer_open", False))
        dlg.exec()


class _MiddleClickFilter(QObject):
    """Intercepts middle-button releases on a view's viewport"""

    def __init__(self, view, callback):
        super().__init__(view)
        self._view = view
        self._callback = callback
        logger.debug("Middle-click filter initialized")

    def eventFilter(self, obj, event):
        if obj is self._view.viewport() and event.type() == QEvent.MouseButtonRelease:
            if event.button() == Qt.MiddleButton:
                logger.debug(f"Middle-click clicked on {obj}")
                idx = self._view.indexAt(event.pos())
                if idx.isValid():
                    self._callback(idx)
                    return True
        return False

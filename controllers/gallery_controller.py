from pathlib import Path

from PySide6.QtCore import Qt, QSize, QModelIndex, QEvent, QObject
from PySide6.QtGui import QIcon, QKeySequence, QAction
from PySide6.QtWidgets import QListView, QMenu, QWidget, QApplication, QStyle, QMessageBox

import controllers.view_utils as view_utils

from models.thumbnail_model import ThumbnailListModel

from ui.ui_gallery_tab import Ui_Form

from widgets.rename_dialog import RenameDialog

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
        self.media_manager.renamed.connect(self._on_renamed)

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

        self._current_folder: str | None = None

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

        self._current_folder = folder_abspath

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
        rename_act = menu.addAction("Rename")

        chosen = menu.exec(self.ui.galleryList.mapToGlobal(pos))

        if chosen == act_new:
            self._open_in_new_tab(idx)
        elif chosen == rename_act:
            self._on_rename_triggered()

    def _on_rename_triggered(self):
        logger.info("Renaming media")
        idx = self.ui.galleryList.currentIndex()
        if not idx.isValid():
            return

        old_path = self._model.data(idx, Qt.UserRole)

        dlg = RenameDialog(old_path, parent=self.ui.gallery_page)
        if not (dlg.exec() and dlg.result_path):
            return

        new_path = dlg.result_path
        if not self.media_manager.rename_media(old_path, new_path):
            QMessageBox.warning(self.ui.gallery_page, "Rename failed",
                                "A file or folder with that name already exists.")
            return

        self._on_renamed(old_path, new_path)

    def _on_renamed(self, old_path: str, new_path: str) -> None:
        """
        Update UI/data when any rename (including Undo) occurs.
        :param old_path:
        :param new_path:
        :return:
        """

        if old_path not in self._gallery_items:
            return  # this tab doesn't show that item

        row = self._gallery_items.pop(old_path)
        self._gallery_items[new_path] = row

        self._model.update_display(old_path, Path(new_path).name, new_user_role=new_path)

        self.media_manager.thumb(new_path)  # enqueue new thumb
        self._apply_sort()

        logger.debug(f"{old_path} -> {new_path}")



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
        """
        Called on middle-click from inside Gallery. Code path is identical to Search’s middle-click.
        :param index:
        :return:
        """
        if not index.isValid():
            return

        abs_path = self._model.data(index, Qt.UserRole)
        target = abs_path if Path(abs_path).is_dir() else str(Path(abs_path).parent)

        self.tab_controller.open_folder_tab(
            root_path=target,
            title=Path(target).name or "Root",
            switch=True
        )

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
        view_utils.open_image_viewer(
            self._model,
            index,
            host_widget=self._host_widget,
            flag_container=self,
            flag_attr="_viewer_open",
        )


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

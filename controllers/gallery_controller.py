from dataclasses import field, dataclass
from pathlib import Path
from typing import Dict, Set

from PySide6.QtCore import Qt, QModelIndex, QEvent, QObject
from PySide6.QtGui import QIcon, QKeySequence, QAction
from PySide6.QtWidgets import QListView, QMenu, QWidget, QApplication, QStyle, QAbstractItemView

from controllers.utils import view_utils
from controllers.utils import path_utils
from controllers.utils.gallery_history import GalleryHistory
from controllers.utils.state_utils import GalleryState, ViewerState

from models.thumbnail_model import ThumbnailListModel

from ui.ui_gallery_tab import Ui_Form
from widgets.image_viewer import ImageViewerDialog
from widgets.metadata_dialog import MetadataDialog

from widgets.rename_dialog import RenameDialog

import logging


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
        self.viewer = ViewerState()

        # model & view
        self._model = ThumbnailListModel()
        self.ui.galleryList.setViewMode(QListView.IconMode)
        self.ui.galleryList.setResizeMode(QListView.Adjust)
        self.ui.galleryList.setModel(self._model)

        # State control
        self.state = GalleryState()
        self.state.row_map = []
        self.state.current_folder = None

        self.history = GalleryHistory()

        # Apply gallery defaults
        self._gallery_grid = True
        self._gallery_preset = "Medium"
        view_utils.apply_gallery_view(self.ui.galleryList, grid=self._gallery_grid, preset=self._gallery_preset)

        # Create folder icon
        self._folder_icon = QApplication.style().standardIcon(QStyle.SP_DirIcon)

        # Signals
        self._mid_filter = _MiddleClickFilter(self.ui.galleryList, self._open_in_new_tab)
        self.ui.galleryList.viewport().installEventFilter(self._mid_filter)

        self.ui.galleryList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.galleryList.customContextMenuRequested.connect(self._show_ctx_menu)

        # Allow for advanced selection
        self.ui.galleryList.setSelectionMode(QAbstractItemView.ExtendedSelection)

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

        # TODO derive size preset dynamically
        # Connect dropdown to select icon sizes
        self.ui.cmb_gallery_size.addItems(view_utils.icon_preset.__globals__["_SIZE_PRESETS"].keys())
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

        paths = (
                sorted(path_utils.list_subdirs(folder), key=lambda x: x.lower()) +
                sorted(path_utils.list_images(folder), key=lambda x: x.lower())
        )

        self.populate_gallery(paths)
        self._apply_sort()

    # ---------------------------- Nav methods ----------------------------

    def open_folder(self, folder_abspath: str):
        """
        Method that is called when a folder is opened to properly display contents and preserve hierarchy
        :param folder_abspath: The absolute path to the folder
        :return: None
        """

        logger.debug(f"open_folder called with folder abspath: {folder_abspath}")

        self.state.current_folder = folder_abspath

        if not self.history.push(folder_abspath):
            return

        self._push_page(folder_abspath)

        # enable/disable nav buttons
        self.ui.btn_back.setEnabled(self.history.can_go_back())
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
        new_folder = self.history.step(delta)
        if new_folder:
            self._push_page(new_folder)
            self._update_nav_buttons()

    def _update_nav_buttons(self) -> None:
        logger.debug("_update_nav_buttons called")
        self.ui.btn_back.setEnabled(self.history.can_go_back())
        if hasattr(self.ui, "btn_forward"):
            self.ui.btn_forward.setEnabled(self.history.can_go_forward())

    # ---------------------------- Thumbnail methods ----------------------------
    def populate_gallery(self, paths: list[str]) -> None:
        """
        Method that takes in a list of paths, and creates the gallery data structures accordingly
        :param paths:
        :return:
        """
        logger.info("populate_gallery called")
        logger.debug(f"populate_gallery called with paths: {paths}")
        self._set_paths_filtered(paths)

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
        view_utils.apply_gallery_view(self.ui.galleryList, grid=checked, preset=self._gallery_preset)

    def _change_size(self, preset):
        logger.info("_change_size called")
        self._gallery_preset = preset
        view_utils.apply_gallery_view(self.ui.galleryList, grid=self._gallery_grid, preset=preset)

    def _apply_sort(self):
        logger.info("_apply_sort called")

        # Determine key + direction
        key = _SORT_KEYS.get(self.ui.cmb_gallery_sortKey.currentIndex(), "name")
        asc = not self.ui.btn_gallery_sortDir.isChecked()
        logger.debug(f"_apply_sort key: {key}, asc: {asc}")

        # Split current view into dirs and files
        current_paths = self._model.get_paths()
        dirs, files = path_utils.split_dirs_files(current_paths)

        # Exclude the current root folder from being displayed as an entry
        dirs = [p for p in dirs if p != self.state.current_folder]
        logger.debug(f"_apply_sort dirs: {dirs}, files: {files}")

        # Order the files slice
        ordered_files = self.media_manager.order_subset(files, key, asc)
        logger.debug(f"_apply_sort ordered_files: {ordered_files}")

        # Display: folders first, then sorted files
        self.populate_gallery(dirs + ordered_files)

    def _set_paths_filtered(self, paths: list[str]) -> None:
        """
        Push paths to the model, hiding variants unless expanded.
        :param paths:
        :return:
        """
        shown: list[str] = []
        for p in paths:
            if self.media_manager.is_variant(p):
                base = self.media_manager.stack_paths(p)[0]
                if self.state.expanded_bases:
                    continue  # collapsed -> hide
            shown.append(p)

        self._model.set_paths(shown)
        self.state.row_map = {p: i for i, p in enumerate(shown)}
        logger.debug(f"_set_paths_filtered called, new gallery items: {self.state.row_map}")

    # ---------------------------- Other methods ----------------------------

    def _show_ctx_menu(self, pos):
        logger.debug(f"_show_ctx_menu called, context menu opening at {pos}")

        # Which item was right-clicked?
        idx = self.ui.galleryList.indexAt(pos)
        if not idx.isValid():
            return

        abs_path = self._model.data(idx, Qt.UserRole)  # absolute path of given row

        # ---------- build menu -------------------------------------------------
        menu = QMenu(self.ui.galleryList)
        menu.setStyleSheet("""
            QMenu { background:#2b2b2b; color:white; border:1px solid #444; }
            QMenu::item:selected { background:#3c3f41; }
        """)

        # Expand / Collapse variants  (only if this row is a stack base)
        base_path = self.media_manager.stack_paths(abs_path)[0]
        base_id_row = self.media_manager.fetchone(
            "SELECT id FROM media WHERE path=?", (base_path,))
        if base_id_row and self.media_manager._is_stacked_base(base_id_row["id"]):

            if self.state.is_expanded(base_path):
                txt = "Expand variants"
            else:
                txt = "Collapse variants"

            act_toggle = menu.addAction(txt)  # keep reference
        else:
            act_toggle = "Not a base stack"

        # Existing actions
        act_new = menu.addAction("Open in New Tab")
        rename_act = menu.addAction("Rename")
        edit_act = menu.addAction("Edit metadata")

        # ---------- execute menu
        chosen = menu.exec(self.ui.galleryList.mapToGlobal(pos))

        # Variant toggle selected?
        if chosen == act_toggle:
            self._toggle_stack(base_path)
            return  # done

        if chosen == act_new:
            self._open_in_new_tab(idx)
        elif chosen == rename_act:
            self._on_rename_triggered()
        if chosen == edit_act:
            sel_paths = self.get_selected_paths()
            dlg = MetadataDialog(sel_paths, self.media_manager, self.tag_manager, self._host_widget)
            dlg.exec()
            return

    def _toggle_stack(self, base_path: str) -> None:
        """
        Expand or collapse a given stack
        :param base_path:
        :return:
        """
        if self.state.is_expanded(base_path):
            logger.debug(f"Removing {base_path} from state.expanded_bases")
            self.state.expanded_bases.remove(base_path)
        else:
            logger.debug(f"Adding {base_path} to state.expanded_bases")
            self.state.expanded_bases.add(base_path)

        self._reload_gallery()

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
            """
            QMessageBox.warning(self.ui.gallery_page, "Rename failed",
                                "A file or folder with that name already exists.")
            """
            return

        self._on_renamed(old_path, new_path)

    def _on_renamed(self, old_path: str, new_path: str) -> None:
        """
        Refresh gallery rows whenever MediaManager emits renamed(old, new).
        """
        root_dir = Path(self.state.current_folder)
        new_parent = Path(new_path).parent
        old_in_view = old_path in self.state.row_map

        # Rename stays within this folder
        if old_in_view and new_parent == root_dir:
            row = self.state.row_map.pop(old_path)
            self.state.row_map[new_path] = row
            self._model.update_display(old_path,
                                       Path(new_path).name,
                                       new_user_role=new_path)
            self.media_manager.thumb(new_path)
            self._apply_sort()
            return

        # File moved out of this folder, therefore drop the row
        if old_in_view and new_parent != root_dir:
            row = self.state.row_map.pop(old_path)
            self._model.removeRow(row)
            self._apply_sort()
            return

        # File moved into this folder (wasn't visible before)
        if not old_in_view and new_parent == root_dir:
            row = self._model.add_path(new_path)  # your helper to append
            self.state.row_map[new_path] = row
            self.media_manager.thumb(new_path)
            self._apply_sort()

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

    def _reload_gallery(self) -> None:
        """
        Refresh list from scratch, then apply the hide/expand filter.
        :return:
        """
        logger.debug("_reload_gallery called")
        key = _SORT_KEYS.get(self.ui.cmb_gallery_sortKey.currentIndex(), "name")
        asc = not self.ui.btn_gallery_sortDir.isChecked()

        all_paths = self.media_manager.get_sorted_paths(key, asc)
        self._set_paths_filtered(all_paths)
        self.populate_gallery(all_paths)

    def get_selected_paths(self) -> list[str]:
        """
        Return a list of absolute paths for all currently-selected thumbnails in the gallery QListView.
        :return:
        """
        indexes = self.ui.galleryList.selectedIndexes()
        if not indexes:
            return []

        return [self._model.data(idx, Qt.UserRole) for idx in indexes]

    def set_viewer_callback(self, fn):
        self.viewer.callback = fn

    def _open_viewer(self, index: QModelIndex):
        """

        :param index:
        :return:
        """
        path = self._model.data(index, Qt.UserRole)
        stack = self.media_manager.stack_paths(path)
        paths = [p for p in self._model.get_paths() if Path(p).is_file()]
        cur_idx = paths.index(path)

        if self.viewer.callback:
            self.viewer.open_via_callback(paths, cur_idx, stack, self._host_widget, self.media_manager)
        else:
            self.viewer.open(self._model, index, self.media_manager, self._host_widget)


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

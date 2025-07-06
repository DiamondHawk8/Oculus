from pathlib import Path

from PySide6.QtCore import Qt, QModelIndex, QEvent, QObject
from PySide6.QtGui import QIcon, QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QListView, QMenu, QWidget, QApplication,
    QStyle, QAbstractItemView, QDialog
)

from controllers.utils import view_utils, path_utils
from controllers.utils.gallery_history import GalleryHistory
from controllers.utils.state_utils import GalleryState, ViewerState
from models.thumbnail_model import ThumbnailListModel

from ui.ui_gallery_tab import Ui_Form
from widgets.metadata_dialog import MetadataDialog
from widgets.rename_dialog import RenameDialog

import logging

_SORT_KEYS = {0: "name", 1: "date", 2: "size"}

logger = logging.getLogger(__name__)


class GalleryController:
    def __init__(self, ui, media_manager, tag_manager, tab_controller, host_widget):
        super().__init__()

        self.ui = ui
        self.media_manager = media_manager
        self.tag_manager = tag_manager
        self.tab_controller = tab_controller
        self._host_widget = host_widget  # differentiate root vs tabs

        self.media_manager.renamed.connect(self._on_renamed)

        # ---------- model / view ----------
        self._model = ThumbnailListModel()
        self.ui.galleryList.setViewMode(QListView.IconMode)
        self.ui.galleryList.setResizeMode(QListView.Adjust)
        self.ui.galleryList.setModel(self._model)

        # ---------- state objects ----------
        self.state = GalleryState()
        self.history = GalleryHistory()
        self.viewer = ViewerState()

        # ---------- gallery defaults ----------
        self._gallery_grid = True
        self._gallery_preset = "Medium"
        view_utils.apply_gallery_view(
            self.ui.galleryList,
            grid=self._gallery_grid,
            preset=self._gallery_preset,
        )

        # ---------- icons & helpers ----------
        self._folder_icon = QApplication.style().standardIcon(QStyle.SP_DirIcon)
        self._mid_filter = _MiddleClickFilter(self.ui.galleryList, self._open_in_new_tab)
        self.ui.galleryList.viewport().installEventFilter(self._mid_filter)

        # ---------- selection & context ----------
        self.ui.galleryList.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.ui.galleryList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.galleryList.customContextMenuRequested.connect(self._show_ctx_menu)

        # ---------- navigation ----------
        ui.btn_back.clicked.connect(lambda: self._navigate(-1))
        if hasattr(ui, "btn_forward"):
            ui.btn_forward.clicked.connect(lambda: self._navigate(+1))
        self._add_shortcut("Alt+Left", lambda: self._navigate(-1))
        self._add_shortcut("Alt+Right", lambda: self._navigate(+1))

        # ---------- activation ----------
        self.ui.galleryList.activated.connect(self._on_item_activated)
        self.media_manager.thumb_ready.connect(self._on_thumb_ready)

        # ---------- view / sort controls ----------
        self.ui.btn_gallery_view.toggled.connect(self._toggle_view)
        self.ui.cmb_gallery_sortKey.currentIndexChanged.connect(self._apply_sort)
        self.ui.btn_gallery_sortDir.toggled.connect(self._apply_sort)

        # ---------- size combo ----------
        # TODO derive sizes dynamically
        self.ui.cmb_gallery_size.addItems(view_utils.icon_preset.__globals__["_SIZE_PRESETS"].keys())
        self.ui.cmb_gallery_size.setCurrentText(self._gallery_preset)
        self.ui.cmb_gallery_size.currentTextChanged.connect(self._change_size)

        # ---------- other keybinds ----------
        self._meta_shortcut = QShortcut(QKeySequence("Ctrl+P"), self.ui.galleryList)
        self._meta_shortcut.activated.connect(self._open_metadata_dialog)

        logger.info("Gallery setup complete")

    # ----------------------------- Navigation / History -----------------------------

    def _push_page(self, folder_abspath: str):
        """
        Refresh view with contents of folder_abspath. Folders first then image files.
        :param folder_abspath: Absolute path of folder to display contents of
        :return: None
        """
        logger.debug(f"_push_page called with folder abspath: {folder_abspath}")
        folder = Path(folder_abspath)
        if not folder.is_dir():
            return

        raw_paths = path_utils.list_subdirs(folder) + path_utils.list_images(folder)
        sorted_paths = self._get_sorted_paths(raw_paths)
        self.populate_gallery(sorted_paths)

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
        self.ui.btn_back.setEnabled(self.history.can_go_back())
        if hasattr(self.ui, "btn_forward"):
            self.ui.btn_forward.setEnabled(False)

    def _navigate(self, delta: int) -> None:
        logger.debug(f"navigate {delta}")
        new_folder = self.history.step(delta)
        if new_folder:
            self.state.current_folder = new_folder
            self._push_page(new_folder)
            self._update_nav_buttons()

    def _update_nav_buttons(self) -> None:
        logger.debug("_update_nav_buttons called")
        self.ui.btn_back.setEnabled(self.history.can_go_back())
        if hasattr(self.ui, "btn_forward"):
            self.ui.btn_forward.setEnabled(self.history.can_go_forward())

    def _on_item_activated(self, index: QModelIndex):
        """
        Method that determines what should be done when an item is activated (usually via clicking)
        :param index: The item that is being activated
        :return: None
        """
        logger.debug(f"on_item_activated called with index: {index}")
        path = self._model.data(index, Qt.UserRole)
        if not path:  # If item does not contain any usable data
            logger.warning(f"Item at {index.row()} has no path")
            return
        # If the item is recognized as a folder, call the open folder method on the path
        if Path(path).is_dir():
            self.open_folder(path)
        # Otherwise, its media, and it will be opened accordingly
        else:
            self._open_viewer(index)

    # ----------------------------- Sorting & appearance -----------------------------

    def _toggle_view(self, checked):
        logger.info("toggle_view called")
        self._gallery_grid = checked
        view_utils.apply_gallery_view(self.ui.galleryList, grid=checked, preset=self._gallery_preset)

    def _change_size(self, preset):
        logger.info("_change_size called")
        self._gallery_preset = preset
        view_utils.apply_gallery_view(self.ui.galleryList, grid=self._gallery_grid, preset=preset)

    def _get_sorted_paths(self, paths: list[str]) -> list[str]:
        """
        Sort a mixed list of file and folder paths using current sort settings. Excludes root folder.
        :param paths: list of paths to be sorted
        :return:
        """
        key = _SORT_KEYS.get(self.ui.cmb_gallery_sortKey.currentIndex(), "name")
        asc = not self.ui.btn_gallery_sortDir.isChecked()
        dirs, files = path_utils.split_dirs_files(paths)
        dirs = [p for p in dirs if p != self.state.current_folder]
        ordered_files = self.media_manager.order_subset(files, key, asc)
        return dirs + ordered_files

    def _apply_sort(self):
        logger.info("_apply_sort called")
        if not self._model.rowCount():
            logger.warning("Model is empty; nothing to sort")
            return

        sorted_paths = self._get_sorted_paths(self._model.get_paths())
        self.populate_gallery(sorted_paths)

    # ----------------------------- Gallery population & thumbnails -----------------------------
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
                if base not in self.state.expanded_bases:
                    continue  # collapsed -> hide
            shown.append(p)

        self._model.set_paths(shown)
        self.state.row_map = {p: i for i, p in enumerate(shown)}
        logger.debug(f"_set_paths_filtered called, new gallery items: {self.state.row_map}")

    def _on_thumb_ready(self, path: str, pix) -> None:
        icon = QIcon(pix)
        self._model.update_icon(path, icon)

    # ---------------------------- Variant-stack handling ----------------------------

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

    def _reload_gallery(self) -> None:
        logger.debug("_reload_gallery called")

        if not self.state.current_folder:
            logger.warning("No current folder set. Aborting reload.")
            return

        self._push_page(self.state.current_folder)

    # ---------------------------- Context-menu & actions ----------------------------

    def _show_ctx_menu(self, pos):
        logger.debug(f"_show_ctx_menu called, context menu opening at {pos}")
        idx = self.ui.galleryList.indexAt(pos)  # Item that was right-clicked
        if not idx.isValid():
            return

        abs_path = self._model.data(idx, Qt.UserRole)  # absolute path of given row
        menu = QMenu(self.ui.galleryList)
        menu.setStyleSheet("""
            QMenu { background:#2b2b2b; color:white; border:1px solid #444; }
            QMenu::item:selected { background:#3c3f41; }
        """)

        # Variant stack actions
        base_path = self.media_manager.stack_paths(abs_path)[0]
        base_row = self.media_manager.fetchone("SELECT id FROM media WHERE path=?", (base_path,))
        if base_row and self.media_manager._is_stacked_base(base_row["id"]):
            txt = "Collapse variants" if self.state.is_expanded(base_path) else "Expand variants"
            act_toggle = menu.addAction(txt)
        else:
            act_toggle = None

        act_new = menu.addAction("Open in New Tab")
        rename_act = menu.addAction("Rename")
        edit_act = menu.addAction("Edit metadata")

        chosen = menu.exec(self.ui.galleryList.mapToGlobal(pos))

        if chosen == act_toggle:
            self._toggle_stack(base_path)
        elif chosen == act_new:
            self._open_in_new_tab(idx)
        elif chosen == rename_act:
            self._on_rename_triggered()
        elif chosen == edit_act:
            sel = self.get_selected_paths()
            MetadataDialog(sel, self.media_manager, self.tag_manager, self._host_widget).exec()

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
        if self.media_manager.rename_media(old_path, new_path):
            self._on_renamed(old_path, new_path)

    def _on_renamed(self, old_path: str, new_path: str) -> None:
        """
        Refresh gallery rows whenever MediaManager emits renamed(old, new).
        :param old_path: original gallery path
        :param new_path: new gallery path
        :return:
        """
        root_dir = Path(self.state.current_folder)
        new_parent = Path(new_path).parent
        old_in_view = old_path in self.state.row_map

        # Rename stays within this folder
        if old_in_view and new_parent == root_dir:
            row = self.state.row_map.pop(old_path)
            self.state.row_map[new_path] = row
            self._model.update_display(old_path, Path(new_path).name, new_user_role=new_path)
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
            row = self._model.add_path(new_path)
            self.state.row_map[new_path] = row
            self.media_manager.thumb(new_path)
            self._apply_sort()

    # ---------------------------- Viewer integration & tab helpers ----------------------------

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
            self.viewer.open(self._model, index, self.media_manager, self.tag_manager, self._host_widget)

    def set_viewer_callback(self, fn):
        self.viewer.callback = fn

    def _open_in_new_tab(self, index: QModelIndex) -> None:
        """
        Called on middle-click from inside Gallery. Code path is identical to Search's middle-click.
        :param index:
        :return:
        """
        if not index.isValid():
            return

        abs_path = self._model.data(index, Qt.UserRole)
        target = abs_path if Path(abs_path).is_dir() else str(Path(abs_path).parent)

        # TODO Allow switch parameter to be changed
        self.tab_controller.open_folder_tab(
            root_path=target,
            title=Path(target).name or "Root",
            switch=True
        )

    def _open_metadata_dialog(self):
        sel = self.get_selected_paths()
        if not sel:
            return
        dlg = MetadataDialog(sel, self.media_manager, self.tag_manager, parent=self._host_widget)
        dlg.exec()

    # ---------------------------- Utility / helpers ----------------------------
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

    def get_selected_paths(self) -> list[str]:
        """
        Return a list of absolute paths for all currently-selected thumbnails in the gallery QListView.
        :return:
        """
        indexes = self.ui.galleryList.selectedIndexes()
        if not indexes:
            return []
        return [self._model.data(idx, Qt.UserRole) for idx in indexes]


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

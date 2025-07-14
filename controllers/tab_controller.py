from collections import deque
import logging
from pathlib import Path

import PySide6
from PySide6.QtCore import QObject, QTimer, Qt, QEvent
from PySide6.QtWidgets import QTabWidget, QWidget

from managers.keybind_manager import KeybindManager
from managers.media_manager import MediaManager
from widgets.media_renderer import MediaViewerDialog
from managers.tag_manager import TagManager
from ui.ui_gallery_tab import Ui_Form
from controllers.gallery_controller import GalleryController

# how many tabs Ctrl+Shift+T can restore, higher values may lead to decreased performance
MAX_CLOSED_STACK = 15

logger = logging.getLogger(__name__)


class TabController(QObject):
    def __init__(self, tab_widget: QTabWidget,
                 media_manager: MediaManager,
                 tag_manager: TagManager,
                 keybinds: KeybindManager,
                 parent: QObject | None = None):
        super().__init__(parent)

        self.media_manager = media_manager
        self.tag_manager = tag_manager
        self._viewers: dict[QWidget, MediaViewerDialog] = {}

        self._tabs = tab_widget
        self._closed: deque = deque(maxlen=MAX_CLOSED_STACK)

        # wire TabWidget signals
        self._tabs.setTabsClosable(True)
        self._tabs.tabCloseRequested.connect(self._close_index)
        self._tabs.currentChanged.connect(self._on_tab_changed)

        # register global shortcuts
        keybinds.register("Ctrl+W", self.close_current)
        keybinds.register("Ctrl+Shift+T", self.restore_last)
        keybinds.register("Ctrl+Tab", lambda: self._cycle(+1))
        keybinds.register("Ctrl+Shift+Tab", lambda: self._cycle(-1))

        # Allow for tabs to be closed via MMB
        self._tabs.tabBar().installEventFilter(self)

        self._home_page = self._tabs.widget(0)

        # Remove close tab button for home tab
        self._tabs.tabBar().setTabButton(0, PySide6.QtWidgets.QTabBar.ButtonPosition.RightSide, None)

        logger.info("Tab setup complete")

    def open_in_new_tab(self, widget: QWidget, title: str, switch: bool = False) -> int:
        """
        Adds given widget to nav structs
        :param widget: Widget to add
        :param title: Title of the tab
        :param switch: If True, when tab is added, it will open automatically
        :return: Index of tab
        """
        logger.info("Opening in new tab")
        logger.debug(f"Args: widget: {widget} title: {title} switch: {switch}")
        idx = self._tabs.addTab(widget, title)
        if switch:
            self._tabs.setCurrentIndex(idx)
        return idx

    def open_folder_tab(self, root_path: str, title: str | None = None, *, switch: bool = True) -> int:
        """
        Build a new Gallery page rooted at root_path and add it as a tab.
        Returns the tab index.
        :param root_path:
        :param title:
        :param switch:
        :return:
        """
        logger.info(f"Opening in new tab from {root_path}")
        logger.debug(f"Args: title: {title} switch: {switch}")
        tab_page = QWidget()
        ui = Ui_Form()
        ui.setupUi(tab_page)

        clone_controller = GalleryController(
            ui,
            media_manager=self.media_manager,
            tag_manager=self.tag_manager,
            tab_controller=self,
            host_widget=tab_page
        )

        clone_controller.open_folder(root_path)

        tab_idx = self.open_in_new_tab(tab_page, title or Path(root_path).name, switch=switch)

        return tab_idx

    def _on_tab_changed(self, idx: int):
        active_page = self._tabs.widget(idx)

        # Hide every viewer except the one for the active page
        for page, viewer in list(self._viewers.items()):
            if viewer is None:
                continue
            if page is active_page:
                if viewer:
                    viewer.show()
                    viewer.raise_()
            else:
                viewer.hide()

    def close_current(self) -> None:
        logger.debug("Closing current tab")
        idx = self._tabs.currentIndex()
        if idx != -1:
            self._close_index(idx)

    def restore_last(self) -> None:
        logger.debug("Restoring last tab")
        if not self._closed:
            return
        widget, title, cur_idx = self._closed.pop()
        new_idx = self._tabs.insertTab(cur_idx, widget, title)
        self._tabs.setCurrentIndex(new_idx)

    def _close_index(self, idx: int) -> None:
        """
        Helper method to preserve tab indexes and contents
        :param idx: tab to be closed
        :return: None
        """
        logger.debug(f"New closed index: {idx}")

        page = self._tabs.widget(idx)
        if page is self._home_page:
            logger.debug("Ignoring attempt to close home page")
            return
        viewer = self._viewers.pop(page, None)
        if viewer:
            viewer.close()

        widget = self._tabs.widget(idx)
        title = self._tabs.tabText(idx)
        self._tabs.removeTab(idx)

        # Keep widget alive so state isn't lost
        self._closed.append((widget, title, idx))

    def _cycle(self, step: int) -> None:
        logger.debug(f"Cycling tabs with step: {step}")
        count = self._tabs.count()
        if count == 0:
            return
        cur = self._tabs.currentIndex()
        new = (cur + step) % count

        # Skip homepage during cycling
        if self._tabs.widget(new) is self._home_page:
            new = (new + step) % count
        self._tabs.setCurrentIndex(new)

        # Highlight tab that was switched to
        tabbar = self._tabs.tabBar()
        tabbar.setTabTextColor(new, Qt.red)
        QTimer.singleShot(150, lambda: tabbar.setTabTextColor(new, Qt.black))

    def register_gallery(self, host_page: QWidget, controller) -> None:
        """
        Called by each GalleryController exactly once. Creates (or reuses) a persistent viewer bound to host_page.
        """
        def _open_viewer(paths, cur_idx, stack):
            viewer = self._viewers.get(host_page)
            if viewer is None:
                viewer = MediaViewerDialog(
                    paths, cur_idx,
                    self.media_manager, self.tag_manager, stack,
                    parent=self._tabs
                )
                viewer.destroyed.connect(lambda: self._viewers.pop(host_page, None))
                self._viewers[host_page] = viewer
            else:
                viewer.load_new_stack(paths, cur_idx, stack)
                viewer.show()
                viewer.raise_()

        controller.set_viewer_callback(_open_viewer)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonRelease:
            if event.button() == Qt.MiddleButton:
                pos = event.position().toPoint()
                idx = self._tabs.tabBar().tabAt(pos)
                if idx != -1:
                    self._close_index(idx)
        return super().eventFilter(obj, event)

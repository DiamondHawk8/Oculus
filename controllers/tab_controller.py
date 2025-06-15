from collections import deque
import logging
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, Qt, QEvent
from PySide6.QtWidgets import QTabWidget, QWidget

from managers.keybind_manager import KeybindManager
from managers.media_manager import MediaManager
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

        self._tabs = tab_widget
        self._closed: deque = deque(maxlen=MAX_CLOSED_STACK)

        # wire TabWidget signals
        self._tabs.setTabsClosable(True)
        self._tabs.tabCloseRequested.connect(self._close_index)

        # register global shortcuts
        keybinds.register("Ctrl+W", self.close_current)
        keybinds.register("Ctrl+Shift+T", self.restore_last)
        keybinds.register("Ctrl+Tab", lambda: self._cycle(+1))
        keybinds.register("Ctrl+Shift+Tab", lambda: self._cycle(-1))

        # Allow for tabs to be closed via MMB
        self._tabs.tabBar().installEventFilter(self)

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

    def open_folder_tab(self, root_path: str, title: str | None = None,
                        *, switch: bool = True) -> int:
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
        logger.debug(f"New gallery instance created: {clone_controller}")

        clone_controller.open_folder(root_path)

        # Drop it in the QTabWidget
        return self.open_in_new_tab(
            tab_page,
            title or Path(root_path).name,
            switch=switch
        )

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
        self._tabs.setCurrentIndex(new)

        # Highlight tab that was switched to
        tabbar = self._tabs.tabBar()
        tabbar.setTabTextColor(new, Qt.red)
        QTimer.singleShot(150, lambda: tabbar.setTabTextColor(new, Qt.black))

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonRelease:
            if event.button() == Qt.MiddleButton:
                pos = event.position().toPoint()
                idx = self._tabs.tabBar().tabAt(pos)
                if idx != -1:
                    self._close_index(idx)
        return super().eventFilter(obj, event)

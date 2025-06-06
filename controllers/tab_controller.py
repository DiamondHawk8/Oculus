from collections import deque
from typing import Callable

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QTabWidget, QWidget

from managers.keybind_manager import KeybindManager

# how many tabs Ctrl+Shift+T can restore, higher values may lead to decreased performance
MAX_CLOSED_STACK = 15


class TabController(QObject):
    def __init__(self,
                 tab_widget: QTabWidget,
                 keybinds: KeybindManager,
                 parent: QObject | None = None):
        super().__init__(parent)

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

    def open_in_new_tab(self,
                        widget: QWidget,
                        title: str,
                        switch: bool = True) -> int:
        """Add widget as a new tab; return its index."""
        idx = self._tabs.addTab(widget, title)
        if switch:
            self._tabs.setCurrentIndex(idx)
        return idx

    def close_current(self) -> None:
        idx = self._tabs.currentIndex()
        if idx != -1:
            self._close_index(idx)

    def restore_last(self) -> None:
        if not self._closed:
            return
        widget, title, cur_idx = self._closed.pop()
        new_idx = self._tabs.insertTab(cur_idx, widget, title)
        self._tabs.setCurrentIndex(new_idx)

    def _close_index(self, idx: int) -> None:
        widget = self._tabs.widget(idx)
        title = self._tabs.tabText(idx)
        self._tabs.removeTab(idx)
        # keep widget alive so state isn’t lost
        self._closed.append((widget, title, idx))

    def _cycle(self, step: int) -> None:
        count = self._tabs.count()
        if count == 0:
            return
        cur = self._tabs.currentIndex()
        self._tabs.setCurrentIndex((cur + step) % count)


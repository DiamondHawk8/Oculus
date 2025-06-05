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


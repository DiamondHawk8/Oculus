from typing import Callable
from PySide6.QtCore import QObject, Qt
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtWidgets import QWidget


class KeybindManager(QObject):
    """
    Keeps one QShortcut per key-sequence, regardless of how many widgets call register().
    Shortcuts are bound to the root window, so they work on every page/tab without duplication.
    """

    def __init__(self, root_widget: QWidget, parent: QObject | None = None):
        super().__init__(parent)

        # QMainWindow
        self._root = root_widget
        self._shortcuts: dict[str, QShortcut] = {}

    def register(self, sequence: str | QKeySequence, slot: Callable) -> None:
        """
        Attach slot to sequence (e.g. Ctrl+W).  Idempotent.
        :param sequence: key sequence to register
        :param slot: Called when sequence is used
        :return: None
        """
        key = str(sequence)
        if key not in self._shortcuts:
            sc = QShortcut(QKeySequence(sequence), self._root)
            sc.setContext(Qt.ApplicationShortcut)  # works across tabs
            self._shortcuts[key] = sc
        self._shortcuts[key].activated.connect(slot)

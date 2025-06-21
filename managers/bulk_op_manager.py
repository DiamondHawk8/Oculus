from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import List, Iterable

from PySide6.QtCore import QObject, Signal


class OpStatus(Enum):
    PENDING = auto()
    SKIPPED = auto()
    DONE = auto()
    ERROR = auto()
    CONFLICT = auto()


@dataclass
class MoveQueueItem:
    old_path: str
    new_path: str
    status: OpStatus = field(default=OpStatus.PENDING)
    error: str | None = None


class BulkOpManager(QObject):
    """
    Holds a list of MoveQueueItem objects. Emits signals so UI widgets can stay in sync.
    """
    queue_changed = Signal()  # anything mutated
    item_updated = Signal(int)  # index that changed

    def __init__(self, media_mgr, undo_mgr, parent=None):
        super().__init__(parent)
        self.media = media_mgr
        self.undo = undo_mgr
        self._items: List[MoveQueueItem] = []

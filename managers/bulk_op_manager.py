from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import List, Iterable

from PySide6.QtCore import QObject, Signal

import logging

logger = logging.getLogger(__name__)

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

        logger.info("Bulk op manager initialized")

    def add(self, old_path: str, new_path: str) -> None:
        """
        Add a pending move/rename to the queue, currently supports rename operations
        :param old_path:
        :param new_path:
        :return:
        """
        self._items.append(MoveQueueItem(old_path, new_path))
        self.queue_changed.emit()

    def clear(self) -> None:
        self._items.clear()
        self.queue_changed.emit()

    def items(self) -> Iterable[MoveQueueItem]:
        return self._items

    def commit_all(self) -> None:
        """
        Execute all pending items in order. Skipped/conflict items are ignored.
        :return:
        """
        for idx, itm in enumerate(self._items):
            if itm.status is not OpStatus.PENDING:
                continue

            # collision check
            if Path(itm.new_path).exists():
                itm.status = OpStatus.CONFLICT
                self.item_updated.emit(idx)
                continue

            ok = self.media.rename_media(itm.old_path, itm.new_path)
            itm.status = OpStatus.DONE if ok else OpStatus.ERROR
            itm.error = None if ok else "rename_media failed"
            self.item_updated.emit(idx)

        self.queue_changed.emit()

    def revert_all(self) -> None:
        """
        Revert all pending items in order.
        :return:
        """
        logger.info("Reverting all pending items")
        self.clear()

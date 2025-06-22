from __future__ import annotations

import dataclasses
import json
import logging
import time
from collections import deque
from pathlib import Path
from typing import Deque
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class UndoEntry:
    old: str
    new: str
    backup: str | None = None


class UndoManager:
    """
    LIFO stack of successful rename operations. TODO expand to other tasks/operations
    """

    _LOG_PATH = Path.home() / "OculusBackups" / "rename_log.json"
    _MAX = 1024  # keep last 1024 renames

    def __init__(self) -> None:
        self._history: Deque[UndoEntry] = deque(maxlen=self._MAX)
        self._LOG_PATH.parent.mkdir(exist_ok=True)

        if self._LOG_PATH.exists():
            try:
                data = json.loads(self._LOG_PATH.read_text())
                self._history.extend(UndoEntry(**d) for d in data)
            except Exception:
                # corrupt log -> wipe history
                self._history.clear()
                self._LOG_PATH.unlink(missing_ok=True)

            logger.info("UndoManager initialized")

    def push(self, old_path: str, new_path: str, *, backup: str | None = None) -> None:
        """
        Record a successful rename
        :param backup:
        :param old_path:
        :param new_path:
        :return:
        """
        self._history.append(UndoEntry(old_path, new_path, backup))
        self._dump()

    def undo_last(self, media_mgr) -> bool:
        """
        Revert the most-recent operation.
        :param media_mgr: Media manager to allow for db operations to be reversed
        :return:
        """
        if not self._history:
            return False

        entry = self._history.pop()
        ok = (
            media_mgr.restore_overwrite(entry)
            if entry.backup
            else media_mgr.rename_media(entry.new, entry.old)
        )
        self._dump()
        return ok

    def _dump(self) -> None:
        data = [
            {"timestamp": time.time(), "old": o, "new": n}
            for o, n in self._history
        ]
        self._LOG_PATH.write_text(json.dumps(data, indent=2))

    def can_undo(self) -> bool:
        """
        Checks to see if there is an operation that can be reversed
        :return: True if self._history is not empty else False
        """
        return bool(self._history)

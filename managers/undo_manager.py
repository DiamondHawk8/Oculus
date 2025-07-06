from __future__ import annotations

import dataclasses
import json
import logging
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
    LIFO stack of reversible operations.
    """

    _LOG_PATH = Path.home() / "OculusBackups" / "rename_log.json"
    _MAX = 1024  # keep last 1024 renames

    def __init__(self) -> None:
        self.rename = None
        self._history: Deque[UndoEntry] = deque(maxlen=1024)
        self._log_path = Path.home() / "OculusBackups" / "rename_log.json"
        self._log_path.parent.mkdir(exist_ok=True)
        self._load()

        logger.info("UndoManager initialized")

    def set_rename_service(self, service):
        self.rename = service

    def push(self, entry: UndoEntry):
        """
        Store a successful operation.
        :param entry:
        :return:
        """
        self._history.append(entry)
        self._dump()

    def undo_last(self) -> bool:
        """
        Undo the most recent operation in the stack.
        :return:
        """
        if not self._history:
            return False
        entry = self._history.pop()
        ok = self.rename.undo(entry)  # RenameService handles logic
        self._dump()
        return ok

    def _dump(self):
        self._log_path.write_text(
            json.dumps([dataclasses.asdict(e) for e in self._history], indent=2)
        )

    def can_undo(self) -> bool:
        """
        Checks to see if there is an operation that can be reversed
        :return: True if self._history is not empty else False
        """
        return bool(self._history)

    def _load(self):
        if not self._log_path.exists():
            return
        try:
            data = json.loads(self._log_path.read_text())
            self._history.extend(UndoEntry(**d) for d in data)
        except Exception:
            self._history.clear()
            self._log_path.unlink(missing_ok=True)

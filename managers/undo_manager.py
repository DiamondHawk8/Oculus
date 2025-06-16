from __future__ import annotations

from pathlib import Path
from collections import deque
import json, time
import logging

logger = logging.getLogger(__name__)
class UndoManager:
    """
    LIFO stack of successful rename operations. TODO expand to other tasks/operations
    """

    _LOG_PATH = Path.home() / "OculusBackups" / "rename_log.json"
    _MAX = 1024 # keep last 1024 renames

    def __init__(self) -> None:
        self._history: deque[tuple[str, str]] = deque(maxlen=self._MAX)
        self._LOG_PATH.parent.mkdir(exist_ok=True)

        # warm-start from previous session
        if self._LOG_PATH.exists():
            try:
                data = json.loads(self._LOG_PATH.read_text())
                self._history.extend((d["old"], d["new"]) for d in data if {"old", "new"} <= d.keys())
            except Exception:
                logger.error("Error in reading log file", exc_info=True)
                self._history.clear()

            logger.info("UndoManager initialized")

    def push(self, old_path: str, new_path: str) -> None:
        """
        Record a successful rename
        :param old_path:
        :param new_path:
        :return:
        """
        self._history.append((old_path, new_path))
        self._dump()

    def undo_last_(self):
        pass

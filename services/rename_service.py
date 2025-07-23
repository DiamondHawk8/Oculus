from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from widgets.collision_dialog import CollisionDialog

_BACKUP_DIR = Path.home() / "OculusBackups" / "overwritten"
_BACKUP_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)


def unique_path(base: Path) -> Path:
    stem, suffix = base.stem, base.suffix
    parent = base.parent
    counter = 1
    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


@dataclass
class RenameEntry:
    def __init__(self, old: str, new: str, backup: str | None = None):
        self.old, self.new, self.backup = old, new, backup


class RenameService(QObject):
    renamed = Signal(str, str)  # emits (oldPath, newPath)

    def __init__(self, dao, parent=None):
        super().__init__(parent)
        self.dao = dao
        self.undo_manager = None

    def attach_undo_manager(self, undo_mgr):
        self.undo_manager = undo_mgr

    def move_many(self, src_paths: list[str], dest_folder: str) -> bool:
        """
        Move each path into dest_folder. Uses existing rename()/overwrite()
        logic so collision dialogs, DB updates and undo all work.
        Returns True if at least one file was moved.
        :param src_paths:
        :param dest_folder:
        :return:
        """
        dest_folder = Path(dest_folder).expanduser().resolve()
        moved_any = False

        for src in src_paths:
            src_path = Path(src).expanduser().resolve()

            # skip if already in that folder
            if src_path.parent == dest_folder:
                continue

            target = dest_folder / src_path.name
            # reuse rename(); it shows CollisionDialog and pushes undo entries
            if self.rename(str(src_path), str(target)):
                moved_any = True

        return moved_any

    # ------------------------------------------------------------------
    def rename(self, old_abs: str, new_abs: str) -> bool:
        old_path = Path(old_abs).expanduser().resolve()
        new_path = Path(new_abs).expanduser().resolve()

        if new_path.exists():
            choice = CollisionDialog.ask(str(old_path), str(new_path))
            if choice in ("cancel", "skip"):
                return False
            if choice == "auto":
                new_path = unique_path(new_path)
            elif choice == "overwrite":
                return self.overwrite(str(old_path), str(new_path))

        try:
            old_path.rename(new_path)
        except OSError as exc:
            logger.error("Rename failed on disk: %s", exc)
            return False

        with self.dao.conn:
            self.dao.cur.execute(
                "UPDATE media SET path=? WHERE path=?", (str(new_path), str(old_path))
            )

        self._log_rename(old_path, new_path)
        if self.undo_manager:
            self.undo_manager.push(RenameEntry(str(old_path), str(new_path)))

        self.renamed.emit(str(old_path), str(new_path))
        return True

    # ------------------------------------------------------------------
    def overwrite(self, old_abs: str, new_abs: str) -> bool:
        old_path = Path(old_abs).expanduser().resolve()
        new_path = Path(new_abs).expanduser().resolve()
        backup = self._backup_path(new_path)

        try:
            if new_path.exists():
                new_path.replace(backup)
                self.renamed.emit(str(new_path), str(backup))

            old_path.replace(new_path)
            self.renamed.emit(str(old_path), str(new_path))

            with self.dao.conn:
                self.dao.cur.execute(
                    "UPDATE media SET path=? WHERE path=?",
                    (str(backup), str(new_path))
                )
                self.dao.cur.execute(
                    "UPDATE media SET path=? WHERE path=?",
                    (str(new_path), str(old_path))
                )

            self._log_rename(old_path, new_path)
            if self.undo_manager:
                self.undo_manager.push(RenameEntry(str(old_path), str(new_path), str(backup)))
            return True

        except Exception as exc:
            logger.error("Safe-overwrite failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    def undo(self, entry: RenameEntry) -> bool:
        old_path, new_path = Path(entry.old), Path(entry.new)
        backup = Path(entry.backup) if entry.backup else None

        try:
            new_path.replace(old_path)
            self.renamed.emit(str(new_path), str(old_path))

            if backup and backup.exists():
                backup.replace(new_path)
                self.renamed.emit(str(backup), str(new_path))

            with self.dao.conn:
                self.dao.cur.execute("UPDATE media SET path=? WHERE path=?", (str(old_path), str(new_path)))
                if backup:
                    self.dao.cur.execute("UPDATE media SET path=? WHERE path=?", (str(new_path), str(backup)))
            return True

        except Exception as exc:
            logger.error("Undo rename failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    @staticmethod
    def _backup_path(original: Path) -> Path:
        return _BACKUP_DIR / f"{uuid.uuid4()}{original.suffix}"

    @staticmethod
    def _log_rename(old_path: Path, new_path: Path):
        log_file = _BACKUP_DIR.parent / "rename_log.json"
        entry = {"timestamp": time.time(), "old": str(old_path), "new": str(new_path)}
        try:
            data = json.loads(log_file.read_text()) if log_file.exists() else []
        except json.JSONDecodeError:
            data = []
        data.append(entry)
        log_file.write_text(json.dumps(data, indent=2))

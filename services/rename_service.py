from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from widgets.collision_dialog import CollisionDialog

_DEFAULT_BACKUP_DIR = Path.home() / "OculusBackups" / "overwritten"

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

    def __init__(self, dao, backup_dir: str | Path | None = None, parent=None):
        super().__init__(parent)
        self.dao = dao
        self.undo_manager = None
        self.backup_dir = Path(backup_dir) if backup_dir else _DEFAULT_BACKUP_DIR
        self.backup_dir.mkdir(parents=True, exist_ok=True)

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

        moved = False
        try:
            old_path.rename(new_path)
            moved = True
            with self.dao.conn:
                self.dao.cur.execute(
                    "UPDATE media SET path=? WHERE path=?", (str(new_path), str(old_path))
                )
                if self.dao.cur.rowcount != 1:
                    raise RuntimeError(f"No database row found for {old_path}")
        except Exception as exc:
            logger.error("Rename failed: %s", exc)
            if moved:
                self._restore_path(new_path, old_path)
            return False

        self._log_rename(old_path, new_path)
        if self.undo_manager:
            self._push_undo(RenameEntry(str(old_path), str(new_path)))

        self.renamed.emit(str(old_path), str(new_path))
        return True

    # ------------------------------------------------------------------
    def overwrite(self, old_abs: str, new_abs: str) -> bool:
        old_path = Path(old_abs).expanduser().resolve()
        new_path = Path(new_abs).expanduser().resolve()
        backup = self._backup_path(new_path)
        destination_backed_up = False
        source_moved = False

        try:
            if new_path.exists():
                new_path.replace(backup)
                destination_backed_up = True

            old_path.replace(new_path)
            source_moved = True

            with self.dao.conn:
                if destination_backed_up:
                    self.dao.cur.execute(
                        "UPDATE media SET path=? WHERE path=?",
                        (str(backup), str(new_path))
                    )
                self.dao.cur.execute(
                    "UPDATE media SET path=? WHERE path=?",
                    (str(new_path), str(old_path))
                )
                if self.dao.cur.rowcount != 1:
                    raise RuntimeError(f"No database row found for {old_path}")

            self._log_rename(old_path, new_path)
            if self.undo_manager:
                backup_value = str(backup) if destination_backed_up else None
                self._push_undo(RenameEntry(str(old_path), str(new_path), backup_value))
            if destination_backed_up:
                self.renamed.emit(str(new_path), str(backup))
            self.renamed.emit(str(old_path), str(new_path))
            return True

        except Exception as exc:
            logger.error("Safe-overwrite failed: %s", exc)
            # Compensate in reverse order so the caller sees the pre-operation
            # filesystem whenever the database transaction cannot complete.
            if source_moved:
                self._restore_path(new_path, old_path)
            if destination_backed_up:
                self._restore_path(backup, new_path)
            return False

    # ------------------------------------------------------------------
    def undo(self, entry: RenameEntry) -> bool:
        old_path, new_path = Path(entry.old), Path(entry.new)
        backup = Path(entry.backup) if entry.backup else None

        source_restored = False
        backup_restored = False
        try:
            new_path.replace(old_path)
            source_restored = True

            if backup and backup.exists():
                backup.replace(new_path)
                backup_restored = True

            with self.dao.conn:
                self.dao.cur.execute("UPDATE media SET path=? WHERE path=?", (str(old_path), str(new_path)))
                if backup:
                    self.dao.cur.execute("UPDATE media SET path=? WHERE path=?", (str(new_path), str(backup)))
            self.renamed.emit(str(new_path), str(old_path))
            if backup_restored and backup is not None:
                self.renamed.emit(str(backup), str(new_path))
            return True

        except Exception as exc:
            logger.error("Undo rename failed: %s", exc)
            if backup_restored and backup is not None:
                self._restore_path(new_path, backup)
            if source_restored:
                self._restore_path(old_path, new_path)
            return False

    # ------------------------------------------------------------------
    def _backup_path(self, original: Path) -> Path:
        return self.backup_dir / f"{uuid.uuid4()}{original.suffix}"

    @staticmethod
    def _restore_path(source: Path, destination: Path) -> None:
        try:
            if source.exists():
                source.replace(destination)
        except OSError:
            logger.exception("Could not restore %s to %s", source, destination)

    def _push_undo(self, entry: RenameEntry) -> None:
        try:
            self.undo_manager.push(entry)
        except OSError:
            # A failed audit/undo write must not reverse an otherwise complete
            # filesystem and database operation.
            logger.exception("Rename succeeded, but its undo record could not be saved")

    def _log_rename(self, old_path: Path, new_path: Path):
        log_file = self.backup_dir.parent / "rename_log.json"
        entry = {"timestamp": time.time(), "old": str(old_path), "new": str(new_path)}
        try:
            data = json.loads(log_file.read_text()) if log_file.exists() else []
            data.append(entry)
            log_file.write_text(json.dumps(data, indent=2))
        except (OSError, json.JSONDecodeError, TypeError):
            logger.exception("Rename succeeded, but its audit log could not be saved")

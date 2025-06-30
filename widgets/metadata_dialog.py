from pathlib import Path
from typing import List

from PySide6.QtCore import QStringListModel, Qt, QPoint
from PySide6.QtWidgets import QDialog, QMessageBox, QCompleter, QAbstractItemView, QTableWidgetItem
from ui.ui_metadata_dialog import Ui_MetadataDialog
import logging

logger = logging.getLogger(__name__)


class MetadataDialog(QDialog):
    """
    Unified dialog for Tags, Attributes, and Presets.
    """

    def __init__(self, media_paths: List[str], media_manager, tag_manager, parent=None):
        """
        :param media_paths: The thumbnail paths currently selected, if len==1 it's the single file dialog
        :param media_manager: Needed for TagManager, Attribute table etc
        """
        super().__init__(parent)
        self.ui = Ui_MetadataDialog()
        self.ui.setupUi(self)

        self._paths = media_paths
        self._media = media_manager
        self._tags = tag_manager

        self._copy_buffer: List[str] | None = None

        # Default
        self.ui.radSelected.setChecked(True)

        # populate file list
        for p in self._paths:
            self.ui.listFiles.addItem(Path(p).name)
        self.ui.listFiles.setSelectionMode(QAbstractItemView.ExtendedSelection)


        self.ui.listFiles.setCurrentRow(0)
        self.ui.listFiles.currentRowChanged.connect(self._on_file_change)

        self._load_tags_for_row(0)
        self._populate_presets(self._id_for_path(self._paths[0]))

        # Obtain tags for auto-completion
        rows = self._tags.fetchall("SELECT DISTINCT tag FROM tags", ())
        model = QStringListModel([r["tag"] for r in rows])
        self.ui.editTag.setCompleter(QCompleter(model, self))

        # Tagging buttons
        self.ui.btnAddTag.clicked.connect(self._add_tag)
        self.ui.btnRemoveTag.clicked.connect(self._remove_selected)
        self.ui.btnCopyTags.clicked.connect(self._copy_tags)
        self.ui.btnPasteTags.clicked.connect(self._paste_tags)

        # Preset Buttons
        self.ui.btnSavePreset.clicked.connect(self._save_preset)
        self.ui.btnLoadPreset.clicked.connect(self._load_selected_preset)
        self.ui.btnDeletePreset.clicked.connect(self._delete_selected_preset)

    # -------------------- Tagging ------------------

    def _add_tag(self):
        """
        Add given tags
        :return:
        """
        tag = self.ui.editTag.text().strip().lower()
        if not tag:
            return
        if not self.ui.listTags.findItems(tag, Qt.MatchFixedString):
            self.ui.listTags.addItem(tag)
            self.ui.editTag.clear()

    def _remove_selected(self):
        """
        Remove selected tags
        :return: None
        """
        for item in self.ui.listTags.selectedItems():
            self.ui.listTags.takeItem(self.ui.listTags.row(item))

    def accept(self) -> None:
        """
        Apply tag changes to selected scope, then close dialog.
        :return: None
        """
        ids = self._target_media_ids()
        if not ids:
            return  # invalid scope already logged

        # gather tags from UI
        tags = [
            self.ui.listTags.item(i).text()
            for i in range(self.ui.listTags.count())
        ]

        # set tags for each media_id
        for mid in ids:
            self._tags.set_tags(mid, tags, overwrite=True)

        super().accept()

    def _ids_with_variants(self, path: str, include: bool) -> list[int]:
        """
        Return media IDs for path (and its variants if include=True)
        :param path:
        :param include:
        :return:
        """
        base_and_variants = (self._media.stack_paths(path) if include else [path])
        return [self._id_for_path(p) for p in base_and_variants]

    # -------------------------- Misc ------------------------
    def selected_scope(self) -> str:
        """
        Method for obtaining the user defined scope of metadata dialog.
        """
        if self.ui.radThis.isChecked():
            return "this"
        if self.ui.radFolder.isChecked():
            return "folder"
        if self.ui.radSelected.isChecked():
            return "selected"
        return "invalid"

    def _id_for_path(self, p: str) -> int:
        row = self._media.fetchone("SELECT id FROM media WHERE path=?", (p,))
        return row["id"] if row else -1

    def _copy_tags(self):
        self._copy_buffer = [
            self.ui.listTags.item(i).text()
            for i in range(self.ui.listTags.count())
        ]

    def _paste_tags(self):
        if not self._copy_buffer:
            QMessageBox.information(
                self, "Nothing copied", "Copy a tag list first.")
            return
        existing = {self.ui.listTags.item(i).text()
                    for i in range(self.ui.listTags.count())}
        for t in self._copy_buffer:
            if t not in existing:
                self.ui.listTags.addItem(t)

    def _load_tags_for_row(self, row: int):
        """
        Fill listTags with tags for file at row
        :param row:
        :return:
        """
        self.ui.listTags.clear()
        if row < 0 or row >= len(self._paths):
            return
        mid = self._id_for_path(self._paths[row])
        for t in self._tags.get_tags(mid):
            self.ui.listTags.addItem(t)

    def _on_file_change(self, row: int):
        self._load_tags_for_row(row)
        self._populate_presets(self._id_for_path(self._paths[row]))

    # -------------------- Presets --------------

    def _populate_presets(self, media_id: int):
        self.ui.tblPresets.setRowCount(0)
        rows = self._media.fetchall(
            "SELECT id, name, media_id FROM presets WHERE media_id IS NULL OR media_id=?",
            (media_id,)
        )
        for r in rows:
            row = self.ui.tblPresets.rowCount()
            self.ui.tblPresets.insertRow(row)
            self.ui.tblPresets.setItem(row, 0, QTableWidgetItem(r["name"]))
            scope = "Folder default" if r["media_id"] is None else "This file"
            self.ui.tblPresets.setItem(row, 1, QTableWidgetItem(scope))
            self.ui.tblPresets.setRowHeight(row, 20)  # tidy
            self.ui.tblPresets.item(row, 0).setData(Qt.UserRole, r["id"])

    def _current_view_state(self) -> tuple[float, int, int]:
        viewer = self.parent()._viewer if hasattr(self.parent(), "_viewer") else None
        if viewer:
            scale, pos = viewer.get_view_state()
            return scale, pos.x(), pos.y()
        return 1.0, 0, 0

    def _save_preset(self) -> None:
        """
        Save the current view-state as a preset for all target media_ids.
        """
        name = self.ui.editPresetName.text().strip()
        if not name:
            QMessageBox.warning(self, "Preset name", "Enter a preset name.")
            return

        scale, px, py = self._current_view_state()
        ids = self._target_media_ids()
        if not ids:
            QMessageBox.warning(self, "Scope", "No files selected to save preset.")
            return

        # use TagManager.save_preset for INSERT OR REPLACE semantics
        for mid in ids:
            self._tags.save_preset(mid, name, scale, px, py)

        # refresh UI for the first target
        self.ui.editPresetName.clear()
        self._populate_presets(ids[0])

    def _load_selected_preset(self):
        items = self.ui.tblPresets.selectedItems()
        if not items:
            return
        preset_id = items[0].data(Qt.UserRole)
        p = self._media.fetchone(
            "SELECT zoom, pan_x, pan_y FROM presets WHERE id=?", (preset_id,))
        viewer = self.parent()._viewer if hasattr(self.parent(), "_viewer") else None
        if viewer and p:
            viewer.apply_view_state(p["zoom"], QPoint(p["pan_x"], p["pan_y"]))

    def _delete_selected_preset(self):
        items = self.ui.tblPresets.selectedItems()
        if not items:
            return
        preset_id = items[0].data(Qt.UserRole)
        self._media.execute("DELETE FROM presets WHERE id=?", (preset_id,))
        self._populate_presets(self._id_for_path(self._paths[0]))

    def _target_media_ids(self) -> list[int]:
        """
        Return the list of media_ids to operate on, based on the selected scope
        radio button and the 'apply to variants' checkbox.
        :return:
        """
        scope = self.selected_scope()
        include_variants = self.ui.chkVariants.isChecked()

        if scope == "invalid":
            logger.error("invalid scope")
            return []

        ids: list[int] = []

        # 'This file'
        if scope == "this":
            ids.extend(self._ids_with_variants(self._paths[0], include_variants))

        # 'Selected files'
        elif scope == "selected":
            for p in self._paths:
                ids.extend(self._ids_with_variants(p, include_variants))

        # 'Folder'
        elif scope == "folder":
            folder = str(Path(self._paths[0]).parent)
            rows = self._media.fetchall(
                "SELECT path FROM media WHERE path LIKE ?", (f"{folder}%",)
            )
            for r in rows:
                ids.extend(self._ids_with_variants(r["path"], include_variants))

        # dedupe while preserving order
        return list(dict.fromkeys(ids))

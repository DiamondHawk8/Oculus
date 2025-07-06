import uuid
from pathlib import Path
from typing import List

from PySide6.QtCore import QStringListModel, Qt, QPoint
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QDialog, QMessageBox, QCompleter, QAbstractItemView, QTableWidgetItem, QLineEdit, \
    QRadioButton
from ui.ui_metadata_dialog import Ui_MetadataDialog
import logging

logger = logging.getLogger(__name__)


class MetadataDialog(QDialog):

    def __init__(self, media_paths: List[str], media_manager, tag_manager, parent=None,
                 default_transform: tuple[float, int, int] | None = None, viewer=None, ):
        """
        Unified dialog for Tags, Attributes, and Presets.
        :param media_paths: Path scope of the dialog. Media that is not provided cannot be altered
        :param media_manager: Used for handling db changes
        :param tag_manager: Used for handling db changes
        :param parent:
        :param default_transform: Optional parameter to autofill data to dialog widgets
        :param viewer: Optional viewer so that metadata changes can be immediately be applied in current viewer session
        """
        super().__init__(parent)
        self.ui = Ui_MetadataDialog()
        self.ui.setupUi(self)

        self._paths = media_paths
        self._media = media_manager
        self._tags = tag_manager
        self._viewer = viewer

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
        self._load_attributes(0)

        model = QStringListModel(self._tags.distinct_tags())
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

        # Value inline editing
        self.ui.tblPresets.cellChanged.connect(self._on_transform_edited)
        self.ui.tblPresets.cellChanged.connect(self._on_name_edited)

        # Preset Values
        if default_transform:
            z, px, py = default_transform
            self.ui.spinZoom.setValue(z)
            self.ui.spinPanX.setValue(px)
            self.ui.spinPanY.setValue(py)

    # -------------------- Helpers ------------------

    def accept(self) -> None:
        """
        Apply tag changes to selected scope, then close dialog.
        :return: None
        """
        # Apply tag changes
        self._save_tags()
        # Load any media again to ensure that preset changes are properly reflected
        if self._viewer:
            self._viewer.refresh()

        self._save_attributes()

        super().accept()

    def selected_scope(self) -> str:
        """
        Method for obtaining the user defined scope of metadata dialog.
        :return:
        """
        if self.ui.radThis.isChecked():
            return "this"
        if self.ui.radFolder.isChecked():
            return "folder"
        if self.ui.radSelected.isChecked():
            return "selected"
        return "invalid"

    def _id_for_path(self, p: str) -> int:
        mid = self._media.get_media_id(p)
        return mid if mid is not None else -1

    def _current_view_state(self):
        z = self.ui.spinZoom.value()
        px = self.ui.spinPanX.value()
        py = self.ui.spinPanY.value()
        return z, px, py

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

    def _save_tags(self):
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
            self._tags.set_tags(mid, tags, overwrite=False)

    def _ids_with_variants(self, path: str, include: bool) -> list[int]:
        """
        Return media IDs for path (and its variants if include=True)
        :param path:
        :param include:
        :return:
        """
        base_and_variants = (self._media.stack_paths(path) if include else [path])
        return [self._id_for_path(p) for p in base_and_variants]

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
        self._load_attributes(row)

    # -------------------- Presets --------------

    def _populate_presets(self, media_id: int):
        """
        Refresh the presets table for the given media_id,
        :param media_id:
        :return:
        """
        tbl = self.ui.tblPresets
        tbl.blockSignals(True)  # suppress cellChanged during fill
        tbl.setRowCount(0)

        folder = Path(self._paths[0]).parent
        rows = self._media.list_presets_for_media(media_id)

        for r in rows:
            row_idx = tbl.rowCount()
            tbl.insertRow(row_idx)

            #  column 0: Name (+ hidden data)
            name_item = QTableWidgetItem(r["name"])
            name_item.setData(Qt.UserRole, r["id"])  # preset id
            name_item.setData(Qt.UserRole + 1, r["group_id"])  # group id
            tbl.setItem(row_idx, 0, name_item)

            #  column 1: Scope listing
            if r["media_id"] is None:  # folder-default: all files in folder
                folder_rows = self._media.dao.fetchall(
                    "SELECT path FROM media WHERE path LIKE ?", (f"{folder}%/",)
                )
                all_names = [Path(fr["path"]).name for fr in folder_rows]
            else:  # file-specific: every row in group
                linked_rows = self._media.list_presets_in_group(r["group_id"])
                all_names = [Path(lr["path"]).name for lr in linked_rows]

            display = ", ".join(all_names[:5])
            if len(all_names) > 5:
                display += f", … ({len(all_names)} total)"
            scope_item = QTableWidgetItem(display)
            scope_item.setToolTip("\n".join(all_names))
            scope_item.setFlags(scope_item.flags() & ~Qt.ItemIsEditable)
            tbl.setItem(row_idx, 1, scope_item)

            #  column 2: Transform string
            transform = f"{r['zoom']:.2f}x, {r['pan_x']}, {r['pan_y']}"
            tbl.setItem(row_idx, 2, QTableWidgetItem(transform))

            #  column 3: Default radio
            radio = QRadioButton()
            radio.setChecked(bool(r["is_default"]))
            radio.toggled.connect(
                lambda checked, gid=r["group_id"], mid=r["media_id"]:
                self._on_default_toggled(gid, mid, checked)
            )
            tbl.setCellWidget(row_idx, 3, radio)

            #  column 4: Hotkey edit
            edit = QLineEdit(r["hotkey"] or "")
            edit.setPlaceholderText("Ctrl+1 ...")
            edit.setFixedWidth(80)
            edit.setStyleSheet("background-color: black; color: white;")
            edit.editingFinished.connect(
                lambda e=edit, gid=r["group_id"]: self._on_hotkey_edited(gid, e)
            )
            tbl.setCellWidget(row_idx, 4, edit)

            tbl.setRowHeight(row_idx, 20)

        tbl.blockSignals(False)  # re-enable after table is filled

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

        gid = str(uuid.uuid4())

        for mid in ids:
            self._tags.save_preset(gid, mid, name, scale, px, py)

        # refresh UI for the first target
        self.ui.editPresetName.clear()
        self._populate_presets(ids[0])

    def _load_selected_preset(self):
        items = self.ui.tblPresets.selectedItems()
        if not items:
            return
        preset_id = items[0].data(Qt.UserRole)
        p = self._media.dao.fetchone(
            "SELECT zoom, pan_x, pan_y FROM presets WHERE id=?", (preset_id,)
        )
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
            rows = self._media.dao.fetchall(
                "SELECT path FROM media WHERE path LIKE ?", (f"{folder}%",)
            )
            for r in rows:
                path = r["path"]
                if include_variants:
                    ids.extend(self._ids_with_variants(path, True))
                else:
                    if not self._media.is_variant(path):
                        ids.append(self._id_for_path(path))

        # dedupe while preserving order
        logger.debug(f"Scope of media identified as {ids}")
        return list(dict.fromkeys(ids))

    def _load_attributes(self, row: int):
        if row < 0 or row >= len(self._paths):
            return
        mid = self._id_for_path(self._paths[row])
        attr = self._media.get_attr(mid)  # favorite, weight, artist
        self.ui.chkFavorite.setChecked(bool(attr.get("favorite", 0)))
        self.ui.spinWeight.setValue(attr.get("weight") or 0.0)
        self.ui.editArtist.setText(attr.get("artist") or "")

    def _save_attributes(self):
        """Push current widget values to every media_id in the chosen scope."""
        ids = self._target_media_ids()
        vals = dict(
            favorite=int(self.ui.chkFavorite.isChecked()),
            weight=self.ui.spinWeight.value(),
            artist=self.ui.editArtist.text().strip() or None
        )
        for mid in ids:
            self._media.set_attr(mid, **vals)

    def _reset_attribute_widgets(self):
        """Convenience reset when no file is selected."""
        self.ui.chkFavorite.setChecked(False)
        self.ui.spinWeight.setValue(0.0)
        self.ui.editArtist.clear()

    def _on_transform_edited(self, row: int, col: int):
        """
        Helper function for allowing user editing of the transformations column
        :param row:
        :param col:
        :return:
        """
        logger.debug(f"Transformation values edited for row {row}, col {col}")
        if col != 2:  # column 2 = Properties
            return

        txt = self.ui.tblPresets.item(row, 2).text()
        name = self.ui.tblPresets.item(row, 0).text()
        try:
            zoom_s, pan_x_s, pan_y_s = [s.strip(" x") for s in txt.split(",")]
            zoom = float(zoom_s)
            pan_x = int(pan_x_s)
            pan_y = int(pan_y_s)
        except (ValueError, IndexError):
            QMessageBox.warning(self, "Invalid format", "Use format like: 1.25x, 20, -15")
            return

        # Find related rows
        gid = self.ui.tblPresets.item(row, 0).data(Qt.UserRole + 1)

        self._media.update_preset_transform(gid, zoom, pan_x, pan_y)

    def _on_name_edited(self, row: int, col: int) -> None:
        if col != 0:  # only column 0 is Name
            return

        new_name = self.ui.tblPresets.item(row, 0).text().strip()
        if not new_name:
            QMessageBox.warning(self, "Rename", "Name cannot be blank.")
            self._populate_presets(self._id_for_path(self._paths[0]))
            return

        gid = self.ui.tblPresets.item(row, 0).data(Qt.UserRole + 1)  # group_id
        first_mid = self._id_for_path(self._paths[0])  # media scope

        # uniqueness check
        if self._media.preset_name_exists(first_mid, new_name, gid):
            QMessageBox.warning(
                self, "Rename", "A preset with that name already exists."
            )
            self._populate_presets(first_mid)
            return

        # rename entire preset group
        self._media.rename_preset_group(gid, new_name)

    def _on_default_toggled(self, group_id: str, media_id: int | None, checked: bool):
        logger.debug(f"Default toggled to {checked} for group id {group_id}, media id {media_id}")
        # ignore un-check events
        if not checked:
            return

        # One default per media (NULL = folder default group)
        self._media.set_default_preset(media_id, group_id)

    def _on_hotkey_edited(self, group_id: str, line: QLineEdit) -> None:
        logger.debug("Hotkey edited")
        text = line.text().strip()

        # validate key sequence
        if text and QKeySequence(text).isEmpty():
            QMessageBox.warning(self, "Hotkey", "Invalid key sequence.")
            line.setText("")
            text = ""

        first_mid = self._id_for_path(self._paths[0])  # media scope

        # clash check
        if text and self._media.hotkey_clash(first_mid, group_id, text):
            QMessageBox.warning(
                self, "Hotkey", "That key is already bound for this media."
            )
            line.setText("")
            return
        self._media.update_hotkey(group_id, text or None)

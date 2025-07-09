from pathlib import Path
import uuid
from typing import Callable, List

from PySide6.QtCore import Qt, QPoint, Signal, QObject
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
     QMessageBox, QTableWidgetItem, QRadioButton, QLineEdit, QAbstractItemView
)

class PresetPane(QObject):
    presetsChanged = Signal()

    def __init__(
        self,
        tbl_presets,  # QTableWidget
        edit_name,  # QLineEdit
        btn_save, btn_load, btn_delete,  # QPushButtons
        spin_zoom, spin_px, spin_py,  # QDoubleSpinBox / QSpinBox
        media_manager,
        tag_manager,
        target_ids_fn: Callable[[], list[int]],  # dialog._target_media_ids
        current_scope_fn: Callable[[], str],  # dialog.selected_scope
        parent=None
    ):
        super().__init__(parent)
        self.tbl = tbl_presets
        self.editName = edit_name
        self.spinZ, self.spinPX, self.spinPY = spin_zoom, spin_px, spin_py
        self._media = media_manager
        self._tags = tag_manager
        self._target_ids = target_ids_fn
        self._scope = current_scope_fn

        # table setup
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl.cellChanged.connect(self._on_cell_changed)

        # buttons
        btn_save.clicked.connect(self._save_preset)
        btn_load.clicked.connect(self._load_selected)
        btn_delete.clicked.connect(self._delete_selected)

    # ---------- public API ---------- #
    def load(self, media_id: int, folder_path: Path):
        """
        Refresh table for given media.
        :param media_id:
        :param folder_path:
        :return:
        """
        self._populate_presets(media_id, folder_path)

    # ---------- internal helpers ---------- #
    def _current_view_state(self):
        return self.spinZ.value(), self.spinPX.value(), self.spinPY.value()

    # ---- populate ----
    def _populate_presets(self, media_id: int, folder: Path):
        tbl = self.tbl
        tbl.blockSignals(True)
        tbl.setRowCount(0)

        rows = self._media.list_presets_for_media(media_id)
        for r in rows:
            row = tbl.rowCount()
            tbl.insertRow(row)

            # col 0 Name
            name_item = QTableWidgetItem(r["name"])
            name_item.setData(Qt.UserRole, r["id"])  # preset id
            name_item.setData(Qt.UserRole+1, r["group_id"])  # group id
            tbl.setItem(row, 0, name_item)

            # col 1 Scope list
            if r["media_id"] is None:  # folder default
                folder_rows = self._media.dao.fetchall(
                    "SELECT path FROM media WHERE path LIKE ?", (f"{folder}%",)
                )
                names = [Path(fr["path"]).name for fr in folder_rows]
            else:  # file-specific group
                linked = self._media.list_presets_in_group(r["group_id"])
                names = [Path(lr["path"]).name for lr in linked]
            display = ", ".join(names[:5]) + (f", ... ({len(names)} total)" if len(names) > 5 else "")
            scope_item = QTableWidgetItem(display)
            scope_item.setToolTip("\n".join(names))
            scope_item.setFlags(scope_item.flags() & ~Qt.ItemIsEditable)
            tbl.setItem(row, 1, scope_item)

            # col 2 Transform
            tbl.setItem(row, 2, QTableWidgetItem(f"{r['zoom']:.2f}x, {r['pan_x']}, {r['pan_y']}"))

            # col 3 Default radio
            radio = QRadioButton()
            radio.setChecked(bool(r["is_default"]))
            radio.toggled.connect(
                lambda checked, gid=r["group_id"], mid=r["media_id"]:
                self._on_default_toggled(gid, mid, checked)
            )
            tbl.setCellWidget(row, 3, radio)

            # col 4 Hotkey
            edit = QLineEdit(r["hotkey"] or "")
            edit.setPlaceholderText("Ctrl+1 …")
            edit.setFixedWidth(80)
            edit.editingFinished.connect(
                lambda e=edit, gid=r["group_id"]: self._on_hotkey_edited(gid, e)
            )
            tbl.setCellWidget(row, 4, edit)

            tbl.setRowHeight(row, 20)

        tbl.blockSignals(False)

    # ---- buttons ----

    def _save_preset(self):
        name = self.editName.text().strip()
        if not name:
            QMessageBox.warning(None, "Preset name", "Enter a preset name.")
            return

        scale, px, py = self._current_view_state()
        ids = self._target_ids()
        if not ids:
            QMessageBox.warning(None, "Scope", "No files selected.")
            return

        gid = str(uuid.uuid4())
        for mid in ids:
            self._tags.save_preset(gid, mid, name, scale, px, py)

        self.editName.clear()
        folder = self._media.folder_for_id(ids[0]) or Path(".")
        self._populate_presets(ids[0], folder)
        self.presetsChanged.emit()

    def _load_selected(self):
        items = self.tbl.selectedItems()
        if not items:
            return
        preset_id = items[0].data(Qt.UserRole)
        p = self._media.dao.fetchone(
            "SELECT zoom, pan_x, pan_y FROM presets WHERE id=?", (preset_id,)
        )
        # viewer is handled by dialog; emit signal if needed
        if p:
            self.presetsChanged.emit()  # dialog can catch and apply

    def _delete_selected(self):
        items = self.tbl.selectedItems()
        if not items:
            return
        preset_id = items[0].data(Qt.UserRole)
        self._media.dao.execute("DELETE FROM presets WHERE id=?", (preset_id,))
        self.presetsChanged.emit()

    # ---- inline edits ----
    def _on_cell_changed(self, row: int, col: int):
        if col == 2:
            self._on_transform_edited(row)
        elif col == 0:
            self._on_name_edited(row)

    def _on_transform_edited(self, row: int):
        txt = self.tbl.item(row, 2).text()
        try:
            zoom_s, pan_x_s, pan_y_s = [s.strip(" x") for s in txt.split(",")]
            zoom, pan_x, pan_y = float(zoom_s), int(pan_x_s), int(pan_y_s)
        except (ValueError, IndexError):
            QMessageBox.warning(None, "Invalid format", "Use: 1.25x, 20, -15")
            return
        gid = self.tbl.item(row, 0).data(Qt.UserRole+1)
        self._media.update_preset_transform(gid, zoom, pan_x, pan_y)

    def _on_name_edited(self, row: int):
        new_name = self.tbl.item(row, 0).text().strip()
        if not new_name:
            QMessageBox.warning(None, "Rename", "Name cannot be blank.")
            self.presetsChanged.emit()
            return
        gid = self.tbl.item(row, 0).data(Qt.UserRole+1)
        first_mid = self._target_ids()[0]
        if self._media.preset_name_exists(first_mid, new_name, gid):
            QMessageBox.warning(None, "Rename", "Name already exists.")
            self.presetsChanged.emit()
            return
        self._media.rename_preset_group(gid, new_name)

    def _on_default_toggled(self, group_id: str, media_id: int | None, checked: bool):
        if checked:
            self._media.set_default_preset(media_id, group_id)

    def _on_hotkey_edited(self, group_id: str, line: QLineEdit):
        text = line.text().strip()
        if text and QKeySequence(text).isEmpty():
            QMessageBox.warning(None, "Hotkey", "Invalid sequence.")
            line.setText("")
            return
        first_mid = self._target_ids()[0]
        if text and self._media.hotkey_clash(first_mid, group_id, text):
            QMessageBox.warning(None, "Hotkey", "Key already bound.")
            line.setText("")
            return
        self._media.update_hotkey(group_id, text or None)

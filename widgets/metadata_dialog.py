from pathlib import Path

from PySide6.QtCore import QStringListModel, Qt
from PySide6.QtWidgets import QDialog, QMessageBox, QCompleter
from ui.ui_metadata_dialog import Ui_MetadataDialog
import re

_RANGE_RE = re.compile(r"^\s*(-?\d+)\s*,\s*(-?\d+)\s*$")  # "-1,2" etc.


class MetadataDialog(QDialog):
    """
    Unified dialog for Tags, Attributes, and Presets.
    """

    def __init__(self, media_paths: list[str], media_manager, tag_manager, parent=None):
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

        # Default
        self.ui.radThis.setChecked(True)

        # Obtain all tags for auto-completion
        all_tags = self._tags.fetchall("SELECT DISTINCT tag FROM tags", ())
        model = QStringListModel([r['tag'] for r in all_tags])
        self.ui.editTag.setCompleter(QCompleter(model, self))

        # Populate listTags with first file in provided paths
        first_id = self._id_for_path(self._paths[0])
        for t in self._tags.get_tags(first_id):
            self.ui.listTags.addItem(t)

        self.ui.btnAddTag.clicked.connect(self._add_tag)
        self.ui.btnRemoveTag.clicked.connect(self._remove_selected)

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
        scope, rng = self.selected_scope()
        if scope == "invalid":
            return  # keep dialog open

        # Build final tag list from UI
        tags = [self.ui.listTags.item(i).text() for i in range(self.ui.listTags.count())]

        # Determine which media_id rows to update
        ids: list[int] = []
        if scope == "this":
            ids = [self._id_for_path(self._paths[0])]

        elif scope == "selected":
            ids = [self._id_for_path(p) for p in self._paths]

        elif scope == "stack":
            base, *variants = self._media.stack_paths(self._paths[0])
            ids = [self._id_for_path(p) for p in [base, *variants]]

        elif scope == "folder":
            folder = str(Path(self._paths[0]).parent)
            rows = self._media.fetchall(
                "SELECT id FROM media WHERE path LIKE ?", (f"{folder}%",))
            ids = [r["id"] for r in rows]


        for mid in ids:
            self._tags.set_tags(mid, tags, overwrite=True)

        super().accept()

    # -------------------------- Misc ------------------------
    def selected_scope(self) -> tuple[str, tuple[int, int] | None]:
        """
        Method for obtaining the user defined scope of metadata dialog.
        :return: ("this" | "folder" | "selected" | "stack" | "range", (start_offset, end_offset) or None)
        """
        if self.ui.radThis.isChecked():
            return "this", None
        if self.ui.radFolder.isChecked():
            return "folder", None
        if self.ui.radSelected.isChecked():
            return "selected", None
        if self.ui.radStack.isChecked():
            return "stack", None

        return "invalid", None

    def _id_for_path(self, p: str) -> int:
        row = self._media.fetchone("SELECT id FROM media WHERE path=?", (p,))
        return row["id"] if row else -1

from pathlib import Path

from PySide6.QtCore import QStringListModel, Qt
from PySide6.QtWidgets import QDialog, QMessageBox, QCompleter
from ui.ui_metadata_dialog import Ui_MetadataDialog
import logging

logger = logging.getLogger(__name__)


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
        self.ui.radSelected.setChecked(True)

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

        scope = self.selected_scope()

        if scope == "invalid":
            logger.error("invalid scope")
            return  # keep dialog open

        # Build final tag list from UI
        tags = [self.ui.listTags.item(i).text() for i in range(self.ui.listTags.count())]

        # Determine which media_id rows to update
        ids: list[int] = []

        include_variants = self.ui.chkVariants.isChecked()

        if scope == "this":
            ids.extend(self._ids_with_variants(self._paths[0], include_variants))

        elif scope == "selected":
            for p in self._paths:
                ids.extend(self._ids_with_variants(p, include_variants))

        elif scope == "folder":
            folder = str(Path(self._paths[0]).parent)
            rows = self._media.fetchall(
                "SELECT path FROM media WHERE path LIKE ?", (f"{folder}%",))
            for r in rows:
                ids.extend(self._ids_with_variants(r["path"], include_variants))

        # remove duplicates while preserving order
        ids = list(dict.fromkeys(ids))

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

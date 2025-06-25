from PySide6.QtWidgets import QDialog, QMessageBox
from ui.ui_metadata_dialog import Ui_MetadataDialog
import re

_RANGE_RE = re.compile(r"^\s*(-?\d+)\s*,\s*(-?\d+)\s*$")  # "-1,2" etc.

class MetadataDialog(QDialog):
    """
    Unified dialog for Tags, Attributes, and Presets.
    """

    def __init__(self, media_paths: list[str], media_manager, parent=None):
        """
        :param media_paths: The thumbnail paths currently selected, if len==1 it's the single file dialog
        :param media_manager: Needed for TagManager, Attribute table etc
        """
        super().__init__(parent)
        self.ui = Ui_MetadataDialog()
        self.ui.setupUi(self)

        self._paths = media_paths
        self._media = media_manager

        # Default
        self.ui.radThis.setChecked(True)

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
        # custom range
        txt = self.ui.editRange.text()
        m = _RANGE_RE.match(txt)
        if not m:
            QMessageBox.warning(self, "Invalid range", "Please enter as: -N, +M  (e.g. -1,2)")
            return "invalid", None
        return "range", (int(m.group(1)), int(m.group(2)))

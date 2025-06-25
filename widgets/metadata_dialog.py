from PySide6.QtWidgets import QDialog
from ui.ui_metadata_dialog import Ui_MetadataDialog


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

        # TODO populate tabs with real data

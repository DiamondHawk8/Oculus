from pathlib import Path
from typing import List

from PySide6.QtCore import QStringListModel
from PySide6.QtWidgets import QDialog, QCompleter, QAbstractItemView

from managers.metadata_backend import MetadataBackend
from ui.ui_metadata_dialog import Ui_MetadataDialog
import logging

from widgets.metadata_panes.attr_pane import AttrPane
from widgets.metadata_panes.preset_pane import PresetPane
from widgets.metadata_panes.tag_pane import TagPane

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

        # ----- backend ----- #
        self.backend = MetadataBackend(media_manager)

        # ----- references ----- #
        self._paths = media_paths
        self._media = media_manager
        self._tags = tag_manager
        self._viewer = viewer

        # ----- inject panes ----- #
        self._copy_buffer: List[str] | None = None

        self.tagPane = TagPane(
            list_tags=self.ui.listTags,
            list_pending=self.ui.listPending,
            edit_tag=self.ui.editTag,
            btn_add=self.ui.btnAddTag,
            btn_remove=self.ui.btnRemoveTag,
            btn_copy=self.ui.btnCopyTags,
            btn_paste=self.ui.btnPasteTags,
            tag_manager=tag_manager,
            copy_buffer=self._copy_buffer,
            parent=self
        )
        self.tagPane.tagsChanged.connect(
            lambda: self.tagPane.load(self._id_for_path(self._paths[0]))
        )

        self.presetPane = PresetPane(
            tbl_presets=self.ui.tblPresets,
            edit_name=self.ui.editPresetName,
            btn_save=self.ui.btnSavePreset,
            btn_load=self.ui.btnLoadPreset,
            btn_delete=self.ui.btnDeletePreset,
            spin_zoom=self.ui.spinZoom,
            spin_px=self.ui.spinPanX,
            spin_py=self.ui.spinPanY,
            media_manager=media_manager,
            tag_manager=tag_manager,
            target_ids_fn=self._target_media_ids,
            current_scope_fn=self.selected_scope,
            parent=self
        )
        self.presetPane.presetsChanged.connect(
            lambda: self.presetPane.load(
                self._id_for_path(self._paths[0]),
                Path(self._paths[0]).parent
            )
        )
        self.attrPane = AttrPane(
            chk_favorite=self.ui.chkFavorite,
            spin_weight=self.ui.spinWeight,
            edit_artist=self.ui.editArtist,
            media_manager=media_manager,
            parent=self
        )

        # Default
        self.ui.radSelected.setChecked(True)

        # populate file list
        for p in self._paths:
            self.ui.listFiles.addItem(Path(p).name)
        self.ui.listFiles.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.ui.listFiles.setCurrentRow(0)
        self.ui.listFiles.currentRowChanged.connect(self._on_file_change)

        self.ui.listFiles.setCurrentRow(0)
        self._on_file_change(0)

        model = QStringListModel(self._tags.distinct_tags())
        self.ui.editTag.setCompleter(QCompleter(model, self))

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
        ids = self._target_media_ids()

        # Apply tag and attr changes
        self.tagPane.save(ids, replace_mode=self.ui.chkReplace.isChecked())
        self.attrPane.save(ids)

        # Load any media again to ensure that preset changes are properly reflected
        if self._viewer:
            self._viewer.refresh()

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
        return self.backend.id_for_path(p)

    def _current_view_state(self):
        z = self.ui.spinZoom.value()
        px = self.ui.spinPanX.value()
        py = self.ui.spinPanY.value()
        return z, px, py

    def _on_file_change(self, row: int):
        """
        Refresh per-file panels whenever the selection in listFiles changes.
        :param row:
        :return:
        """
        mid = self._id_for_path(self._paths[row])
        self.tagPane.load(mid)

        self.presetPane.load(mid, Path(self._paths[0]).parent)

        if self.selected_scope() == "this":
            self.attrPane.load(mid)
        else:
            self.attrPane.reset()

    def _target_media_ids(self) -> list[int]:
        include = self.ui.chkVariants.isChecked()
        return self.backend.target_media_ids(self._paths, self.selected_scope(), include)

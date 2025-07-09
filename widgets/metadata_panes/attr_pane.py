from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QCheckBox, QDoubleSpinBox, QLineEdit


class AttrPane(QObject):
    attributesChanged = Signal()

    def __init__(
            self,
            chk_favorite: QCheckBox,
            spin_weight: QDoubleSpinBox,
            edit_artist: QLineEdit,
            media_manager,
            parent=None,
    ):
        super().__init__(parent)
        self.chkFav = chk_favorite
        self.spinWeight = spin_weight
        self.editArtist = edit_artist
        self._media = media_manager

    # ---------- public API ---------- #
    def load(self, media_id: int | None):
        if media_id is None:
            self.reset()
            return
        attr = self._media.get_attr(media_id)
        self.chkFav.setChecked(bool(attr.get("favorite", 0)))
        self.spinWeight.setValue(attr.get("weight") or 0.0)
        self.editArtist.setText(attr.get("artist") or "")

    def save(self, media_ids: list[int]):
        """Push current widget values to all target media_ids."""
        vals = dict(
            favorite=int(self.chkFav.isChecked()),
            weight=self.spinWeight.value(),
            artist=self.editArtist.text().strip() or None,
        )
        for mid in media_ids:
            self._media.set_attr(mid, **vals)
        if media_ids:
            self.attributesChanged.emit()

    def reset(self):
        self.chkFav.setChecked(False)
        self.spinWeight.setValue(0.0)
        self.editArtist.clear()

from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon

import controllers.view_utils as view_utils

SIZE_PRESETS = {
    "Small": (64, QSize(82, 82)),
    "Medium": (96, QSize(118, 118)),
    "Large": (128, QSize(150, 150)),
    "XL": (192, QSize(216, 216)),
}


class GalleryController:
    def __init__(self, ui, media_manager, tag_manager):
        self.ui = ui
        self.media_manager = media_manager
        self.tag_manager = tag_manager

        self._gallery_items: dict[str, int] = {}
        self.media_manager.thumb_ready.connect(self._on_thumb_ready)

        cached_paths = self.tag_manager.all_paths()
        if cached_paths:
            self.populate_gallery(cached_paths)

        # Apply gallery page appearance options functionality
        self._gallery_grid = True  # default mode
        self._gallery_preset = "Medium"
        view_utils.apply_view(self.ui.galleryList,
                              grid=self._gallery_grid,
                              preset=self._gallery_preset)

        # Connect button to toggle between list and grid view
        self.ui.btn_gallery_view.toggled.connect(self._toggle_view)

        # TODO derive size preset dynamically
        # Connect dropdown to select icon sizes
        self.ui.cmb_gallery_size.addItems(SIZE_PRESETS.keys())
        self.ui.cmb_gallery_size.setCurrentText(self._gallery_preset)
        self.ui.cmb_gallery_size.currentTextChanged.connect(self._change_size)

    def populate_gallery(self, paths: list[str]) -> None:
        glist = self.ui.galleryList
        glist.clear()
        self._gallery_items.clear()

        for p in paths:
            row = glist.count()
            item = glist.addItem(str(Path(p).name))
            self._gallery_items[p] = row
            # request thumb : will arrive async
            self.media_manager.thumb(p)

    def _on_thumb_ready(self, path: str, pix) -> None:
        icon = QIcon(pix)

        # Gallery update
        idx = self._gallery_items.get(path)
        if idx is not None:
            self.ui.galleryList.item(idx).setIcon(icon)

    def _toggle_view(self, checked):
        self._gallery_grid = checked
        view_utils.apply_view(self.ui.galleryList,
                              grid=checked,
                              preset=self._gallery_preset)
        self.ui.galleryList.verticalScrollBar().setSingleStep(300)

    def _change_size(self, preset):
        self._gallery_preset = preset
        view_utils.apply_view(self.ui.galleryList,
                              grid=self._gallery_grid,
                              preset=preset)

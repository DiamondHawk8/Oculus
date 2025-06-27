from pathlib import Path
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QListWidget, QListView
import logging

from widgets.image_viewer import ImageViewerDialog

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Gallery icon-size presets (cell size only)
_SIZE_PRESETS = {
    "Small": (64, QSize(82, 82)),
    "Medium": (96, QSize(118, 118)),
    "Large": (128, QSize(150, 150)),
    "XL": (192, QSize(216, 216)),
}


def icon_preset(name: str) -> (int, QSize):
    """
    Return a QSize for grid/list cell based on preset name.
    :param name:
    :return:
    """
    return _SIZE_PRESETS.get(name, _SIZE_PRESETS["Medium"])


def apply_gallery_view(view: QListView | QListWidget, *, grid: bool, preset: str):
    """
    Apply view-mode + icon size to a QListView/Widget that shows thumbnails.
    :param view:
    :param grid:
    :param preset:
    :return:
    """
    icon, cell = icon_preset(preset)

    if grid:
        logger.debug(f"Applying grid view to {view}")
        view.setViewMode(QListView.IconMode)
        view.setFlow(QListView.LeftToRight)
        view.setWrapping(True)
        view.setResizeMode(QListView.Adjust)
        view.setIconSize(QSize(icon, icon))
        view.setGridSize(cell)
    else:
        logger.debug(f"Applying list view to {view}")
        view.setViewMode(QListView.ListMode)
        view.setFlow(QListView.TopToBottom)
        view.setWrapping(False)
        view.setIconSize(QSize(icon, icon))
        view.setGridSize(QSize())  # reset grid

    # consistent scroll speed
    view.verticalScrollBar().setSingleStep(300)

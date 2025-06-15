from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QListWidget

import logging

from widgets.image_viewer import ImageViewerDialog

logger = logging.getLogger(__name__)

SIZE_PRESETS = {
    "Small": (64, QSize(82, 82)),
    "Medium": (96, QSize(118, 118)),
    "Large": (128, QSize(150, 150)),
    "XL": (192, QSize(216, 216)),
}


def apply_view(widget: QListWidget, *, grid: bool, preset: str):
    logger.info("applying view")
    icon, cell = SIZE_PRESETS[preset]
    if grid:
        logger.debug(f"Applying grid view to {widget}")
        widget.setViewMode(QListWidget.IconMode)
        widget.setFlow(QListWidget.LeftToRight)
        widget.setWrapping(True)
        widget.setResizeMode(QListWidget.Adjust)
        widget.setIconSize(QSize(icon, icon))
        widget.setGridSize(cell)
    else:
        logger.debug(f"Applying list view to {widget}")
        widget.setViewMode(QListWidget.ListMode)
        widget.setFlow(QListWidget.TopToBottom)
        widget.setWrapping(False)
        widget.setIconSize(QSize(32, 32))
        widget.setGridSize(QSize())  # resets grid

def open_image_viewer(model, index, host_widget, flag_container, flag_attr: str):
    """
    Shared helper to open ImageViewerDialog and toggle a boolean flag so multiple instances aren't opened.
    :param model:
    :param index:
    :param host_widget:
    :param flag_container:
    :param flag_attr:
    :return:
    """
    logger.info("Opening media viewer")
    logger.debug(f"open_image_viewer args: index: {index}, host_widget: {host_widget}, flag_container: {flag_container}"
                 f", flag_attr: {flag_attr}")
    if getattr(flag_container, flag_attr):
        return  # viewer already open

    abs_path = model.data(index, Qt.UserRole)
    if not abs_path or not Path(abs_path).is_file():
        return

    # order only the files currently visible in the model
    paths = [p for p in model.get_paths() if Path(p).is_file()]
    cur_idx = paths.index(abs_path)

    setattr(flag_container, flag_attr, True)
    dlg = ImageViewerDialog(paths, cur_idx, parent=host_widget)
    dlg.finished.connect(lambda *_: setattr(flag_container, flag_attr, False))
    dlg.exec()

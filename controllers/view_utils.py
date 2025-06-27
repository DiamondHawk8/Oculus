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


def open_image_viewer(model, index, media_manager, host_widget, flag_container, flag_attr: str):
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

    stack = media_manager.stack_paths(abs_path)  # [base, v1, v2]  or [abs_path]
    paths = [p for p in model.get_paths() if Path(p).is_file()]

    cur_idx = paths.index(abs_path)

    setattr(flag_container, flag_attr, True)
    dlg = ImageViewerDialog(paths, cur_idx, media_manager, stack, parent=host_widget)
    dlg.finished.connect(lambda *_: setattr(flag_container, flag_attr, False))
    dlg.exec()

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QListWidget

SIZE_PRESETS = {
    "Small": (64, QSize(82, 82)),
    "Medium": (96, QSize(118, 118)),
    "Large": (128, QSize(150, 150)),
    "XL": (192, QSize(216, 216)),
}


def apply_view(widget: QListWidget, *, grid: bool, preset: str):
    print("applying view")
    icon, cell = SIZE_PRESETS[preset]
    if grid:
        print("applying grid")
        widget.setViewMode(QListWidget.IconMode)
        widget.setFlow(QListWidget.LeftToRight)
        widget.setWrapping(True)
        widget.setResizeMode(QListWidget.Adjust)
        widget.setIconSize(QSize(icon, icon))
        widget.setGridSize(cell)
    else:
        print("applying list")
        widget.setViewMode(QListWidget.ListMode)
        widget.setFlow(QListWidget.TopToBottom)
        widget.setWrapping(False)
        widget.setIconSize(QSize(32, 32))
        widget.setGridSize(QSize())  # resets grid

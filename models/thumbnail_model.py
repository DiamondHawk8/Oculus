from pathlib import Path
from typing import List, Dict

from PySide6.QtCore import Qt, QAbstractListModel, QModelIndex
from PySide6.QtGui import QIcon


class ThumbnailListModel(QAbstractListModel):

    def __init__(self, paths: List[str] | None = None, parent=None) -> None:
        super().__init__(parent)
        self._paths: List[str] = paths or []
        self._icons: Dict[str, QIcon] = {}

    def set_paths(self, paths: List[str]) -> None:
        """Reset list with a new ordered set of absolute paths."""
        self.beginResetModel()
        self._paths = paths
        self._icons.clear()
        self.endResetModel()

    def update_icon(self, path: str, icon: QIcon) -> None:
        """
        Called by the controller when a thumbnail is generated.
        Emits dataChanged so the view repaints only that row.
        """
        if path not in self._icons:
            try:
                row = self._paths.index(path)
            except ValueError:
                return  # path not in current view
            self._icons[path] = icon
            idx = self.index(row)
            self.dataChanged.emit(idx, idx, [Qt.DecorationRole])

    def path_at(self, row: int) -> str:
        #  accessor for controllers
        return self._paths[row]

    # noqa: N802 (Qt naming)
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._paths)

    # noqa: N802 (Qt naming)
    def data(self, index: QModelIndex, role: int):
        if not index.isValid():
            return None
        path = self._paths[index.row()]

        if role == Qt.DisplayRole:
            return Path(path).name

        if role == Qt.DecorationRole:
            return self._icons.get(path)

        if role == Qt.UserRole:
            return path

        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:  # noqa: N802
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

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

    def add_path(self, path: str) -> int:
        """
        Append a new absolute path to the model and return its row index.
        If the path already exists, nothing is done and its current row is returned.
        :param path:
        :return:
        """
        if path in self._paths:
            return self._paths.index(path)

        row = len(self._paths)
        self.beginInsertRows(QModelIndex(), row, row)
        self._paths.append(path)
        self.endInsertRows()
        return row

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

    def update_display(self, old_path: str, new_name: str, *, new_user_role: str):
        """
        Change the display label (and role data) for one row.
        :param old_path:
        :param new_name:
        :param new_user_role:
        :return:
        """
        try:
            idx = self._paths.index(old_path)
        except ValueError:
            return
        self._paths[idx] = new_user_role  # replace stored path
        model_idx = self.index(idx)
        self.dataChanged.emit(model_idx, model_idx, [Qt.DisplayRole, Qt.UserRole])

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

    def get_paths(self) -> List[str]:
        return self._paths

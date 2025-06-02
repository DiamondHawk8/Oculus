from pathlib import Path
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem


class FolderTreeWidget(QTreeWidget):
    """
    Expandable tree that shows folders to be used for debugging after an import scan completes.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)

    def load_tree(self, tree: dict[str, tuple[list[str], list[str]]], root: str):
        self.clear()
        root_item = QTreeWidgetItem([Path(root).name])
        self.addTopLevelItem(root_item)
        self._build_nodes(root_item, root, tree)
        self.expandAll()

    def _build_nodes(self, parent_item: QTreeWidgetItem, folder: str,
                     tree: dict[str, tuple[list[str], list[str]]]):
        for sub in tree.get(folder, ([], []))[0]:
            child_item = QTreeWidgetItem([Path(sub).name])
            parent_item.addChild(child_item)
            self._build_nodes(child_item, sub, tree)

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

    def load_folders(self, folders, root: Path) -> None:
        """Render the importer's bounded, parent-before-child directory preview."""
        self.clear()
        if not folders:
            return
        root_item = QTreeWidgetItem([root.name or str(root)])
        self.addTopLevelItem(root_item)
        nodes = {root: root_item}
        for folder in sorted(folders, key=lambda path: (str(path).casefold(), str(path))):
            if folder == root:
                continue
            parent_item = nodes.get(folder.parent)
            if parent_item is not None:
                item = QTreeWidgetItem([folder.name])
                parent_item.addChild(item)
                nodes[folder] = item
        self.expandAll()

    def _build_nodes(self, parent_item: QTreeWidgetItem, folder: str,
                     tree: dict[str, tuple[list[str], list[str]]]):
        subfolders = tree.get(folder, ([], []))[0]
        for sub in sorted(subfolders, key=lambda path: (Path(path).name.casefold(), Path(path).name)):
            child_item = QTreeWidgetItem([Path(sub).name])
            parent_item.addChild(child_item)
            self._build_nodes(child_item, sub, tree)

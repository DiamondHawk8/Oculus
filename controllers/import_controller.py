from pathlib import Path
import logging

from PySide6.QtWidgets import QFileDialog

from widgets.folder_tree_widget import FolderTreeWidget

logger = logging.getLogger(__name__)


class ImportController:
    def __init__(self, parent_window, ui, media_manager, tag_manager, gallery_controller):

        # Utilized for generating dialogues
        self.parent_window = parent_window

        # Used for tracking chosen import folder for debug
        self._import_root = None

        self.ui = ui
        self.media_manager = media_manager
        self.tag_manager = tag_manager
        self.gallery_controller = gallery_controller

        # Connect Import page
        self.ui.chooseBtn.clicked.connect(self._choose_folder)
        self.media_manager.scan_finished.connect(self.handle_scan_finished)

        tree = FolderTreeWidget(ui.import_page)
        parent_layout = ui.debugFolderTree.parentWidget().layout()  # ← fixed line
        parent_layout.replaceWidget(ui.debugFolderTree, tree)
        ui.debugFolderTree.deleteLater()
        ui.debugFolderTree = tree

        logger.info("Import setup complete")

    def _choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self.parent_window, "Choose image folder")
        if folder:
            self._import_root = folder
            # TODO allow for more advanced scanning text
            self.ui.importStatus.setText("Scanning…")
            self.media_manager.scan_folder(folder)

    def handle_scan_finished(self, paths):
        """
        Receives scanned paths from MediaManager. Updates DB.
        Then calls _on_scan_complete() to allow the caller to handle UI updates.
        """
        logger.info("Attempting to add paths to database")

        # persist paths into DB so SearchManager can find them
        print(paths)
        for p in paths:
            media_id = self.media_manager.add_media(p, is_dir=False)

        self.ui.importStatus.setText(f"Found {len(paths)} files")

        if self._import_root:
            # Create path of imported data from selected folder
            root_path = str(Path(self._import_root).expanduser().resolve())

            # Create debug tree from rootpath
            tree_data = self.media_manager.walk_tree(root_path)
            self.ui.debugFolderTree.load_tree(tree_data, root_path)

            # TODO Streamline process
            self.gallery_controller.open_folder(root_path)


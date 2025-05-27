from PySide6.QtWidgets import QFileDialog


class ImportController:
    def __init__(self, parent_window, ui, media_manager, tag_manager, on_scan_complete):

        # Utilized for generating dialogues
        self.parent_window = parent_window

        self.ui = ui
        self.media_manager = media_manager
        self.tag_manager = tag_manager
        self.on_scan_complete = on_scan_complete

        # Connect Import page
        self.ui.chooseBtn.clicked.connect(self._choose_folder)
        self.media_manager.scan_finished.connect(self.handle_scan_finished)

    def _choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self.parent_window, "Choose image folder")
        if folder:
            self.ui.importStatus.setText("Scanning…")
            self.media_manager.scan_folder(folder)

    def handle_scan_finished(self, paths):
        """
        Receives scanned paths from MediaManager. Updates DB.
        Then calls _on_scan_complete() to allow the caller to handle UI updates.
        """

        # persist paths into DB so SearchManager can find them
        for p in paths:
            self.tag_manager.add_media(p)

        self.ui.importStatus.setText(f"Found {len(paths)} files")

        if self.on_scan_complete:
            self.on_scan_complete(paths)

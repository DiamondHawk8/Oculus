import logging

from PySide6.QtWidgets import QFileDialog, QPushButton

from application.indexing import ImportProgress, ImportSummary
from widgets.folder_tree_widget import FolderTreeWidget

logger = logging.getLogger(__name__)


class ImportController:
    def __init__(self, parent_window, ui, media_manager, tag_manager, gallery_controller):
        self.parent_window = parent_window
        self.ui = ui
        self.media_manager = media_manager
        self.tag_manager = tag_manager
        self.gallery_controller = gallery_controller
        self._job_id = None
        self._completed_root = None
        self._choose_text = ui.chooseBtn.text()
        self.ui.chooseBtn.clicked.connect(self._choose_folder)
        media_manager.import_finished.connect(self.handle_scan_finished)
        media_manager.import_progress.connect(self.handle_progress)

        tree = FolderTreeWidget(ui.import_page)
        parent_layout = ui.debugFolderTree.parentWidget().layout()
        parent_layout.replaceWidget(ui.debugFolderTree, tree)
        ui.debugFolderTree.deleteLater()
        ui.debugFolderTree = tree
        self._open_button = QPushButton("Open imported folder", ui.import_page)
        self._open_button.setEnabled(False)
        self._open_button.clicked.connect(self._open_imported_folder)
        parent_layout.addWidget(self._open_button, 4, 1)
        self.ui.importStatus.setWordWrap(True)

    def _choose_folder(self) -> None:
        if self.media_manager.importer.busy:
            self.media_manager.cancel_import()
            self.ui.chooseBtn.setEnabled(False)
            self.ui.importStatus.setText("Cancelling; committed batches will be kept...")
            return
        folder = QFileDialog.getExistingDirectory(self.parent_window, "Choose media folder")
        if folder:
            try:
                self._job_id = self.media_manager.scan_folder(folder)
            except (RuntimeError, ValueError) as error:
                self.ui.importStatus.setText(str(error))
                return
            self.ui.debugFolderTree.clear()
            self._open_button.setEnabled(False)
            self.ui.chooseBtn.setText("Cancel import")
            self.ui.importStatus.setText("Preparing import...")

    def handle_progress(self, progress: ImportProgress) -> None:
        if progress.job_id != self._job_id:
            return
        self.ui.importStatus.setText(
            f"{progress.phase.capitalize()} · Added {progress.added} · "
            f"Existing {progress.skipped} · Errors {progress.errors}"
        )

    def handle_scan_finished(self, summary: ImportSummary) -> None:
        if summary.job_id != self._job_id:
            return
        self._job_id = None
        self.ui.chooseBtn.setText(self._choose_text)
        self.ui.chooseBtn.setEnabled(True)
        details = summary.error or ""
        if not details and summary.issues:
            first = summary.issues[0]
            details = f"{first.path}: {first.message}"
        preview_note = (
            f" · Folder preview limited to {len(summary.folder_preview)}"
            if summary.directories > len(summary.folder_preview) else ""
        )
        self.ui.importStatus.setText(
            f"{summary.status.capitalize()} · Added {summary.added} · Existing {summary.skipped} "
            f"(moved {summary.moved}) · Errors {summary.errors} · {summary.duration:.1f}s"
            f"{preview_note}" + (f" · {details}" if details else "")
        )
        # The worker's capped preview replaces the second recursive walk and
        # avoids creating a widget for every directory in a large collection.
        self.ui.debugFolderTree.load_folders(summary.folder_preview, summary.root)
        self._completed_root = summary.root if summary.directories else None
        self._open_button.setEnabled(self._completed_root is not None)
        # Gallery paging is the next chunk. Do not auto-open an arbitrarily large
        # folder here: that legacy path requests all thumbnails synchronously.

    def _open_imported_folder(self) -> None:
        if self._completed_root is not None:
            self.gallery_controller.open_folder(str(self._completed_root))
            self.ui.stackedWidget.setCurrentWidget(self.ui.gallery_page)

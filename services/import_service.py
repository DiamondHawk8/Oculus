from pathlib import Path
from PySide6.QtCore import QObject, Signal, QThreadPool
from workers.scan_worker import ScanWorker, ScanResult
from managers.dao import MediaDAO
from services.variant_service import VariantService
import logging

logger = logging.getLogger(__name__)


class ImportSummary:
    def __init__(self, root, added, skipped, duration):
        self.root, self.added, self.skipped, self.duration = root, added, skipped, duration


class ImportService(QObject):
    """
    Walks folders, inserts media rows, stacks variants.
    """

    import_completed = Signal(object)  # emits ScanResult

    def __init__(self, dao: MediaDAO, variants: VariantService,
                 pool: QThreadPool, parent=None):
        super().__init__(parent)
        self.dao = dao
        self.variants = variants
        self.pool = pool

    def scan(self, root: Path):
        logger.info("Scanning folder %s", root)
        worker = ScanWorker(root)
        worker.finished.connect(self._on_scan_done)
        self.pool.start(worker)

    # ----------------------------------------------------------

    def _on_scan_done(self, result: ScanResult):
        """
        Second pass: auto-stack new files.
        :param result:
        :return:
        """
        added = skipped = 0
        for p in result.files:
            mid = self.dao.insert_media(p)
            if mid:
                added += 1
                self.variants.detect_and_stack(mid, p)
            else:
                skipped += 1

        self.import_completed.emit(
            ImportSummary(result.root, added, skipped, result.duration)
        )

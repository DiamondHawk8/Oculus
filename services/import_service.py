from pathlib import Path
from PySide6.QtCore import QObject, Signal, QThreadPool
from workers.scan_worker import ScanWorker, ScanResult
from managers.dao import MediaDAO
from services.variant_service import VariantService
import logging

logger = logging.getLogger(__name__)


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
        worker = ScanWorker(root, self.dao)  # inserts rows via DAO
        worker.finished.connect(self._on_scan_done)
        self.pool.start(worker)

    # ----------------------------------------------------------

    def _on_scan_done(self, result: ScanResult):
        """
        Second pass: auto-stack new files.
        :param result:
        :return:
        """
        for rowid in self.dao.cur.execute(
                "SELECT id, path FROM media WHERE added >= ?",
                (result.root.stat().st_mtime,),  # rough heuristic
        ):
            self.variants.detect_and_stack(rowid["id"], rowid["path"])

        self.import_completed.emit(result)

import os
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
        added = skipped = 0
        newly_added: list[tuple[int, str]] = []
        parents: set[Path] = set()

        # pre-fetch existing inodes for all scanned files
        stats = {p: os.stat(p, follow_symlinks=False) for p in result.files}
        inode_map = self.dao.fetch_many_inodes([st.st_ino for st in stats.values()])

        with self.dao.conn:  # single transaction, rolls back on error
            for path, st in stats.items():
                inode = st.st_ino
                rec = inode_map.get(inode)

                # exact match -> skip
                if rec and rec[1] == path:
                    skipped += 1
                    continue

                # inode known but path moved -> update
                if rec:
                    self.dao.update_media_path(rec[0], path, int(st.st_mtime))
                    skipped += 1
                    continue

                # brand-new file -> insert
                mid = self.dao.insert_media(path, st)
                newly_added.append((mid, path))
                added += 1

                parents.add(Path(path).parent)

            # ensure all parent folders exist in DB
            for folder in parents:
                self.dao.insert_media(str(folder))

            # Ensure import root itself is included
            self.dao.insert_media(str(result.root))

        # second pass: stack only the new ones
        for mid, p in newly_added:
            self.variants.detect_and_stack(mid, p)

        self.import_completed.emit(
            ImportSummary(result.root, added, skipped, result.duration)
        )

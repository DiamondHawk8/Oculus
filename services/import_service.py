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

        stats = {item.path: item.stat for item in result.files}
        identity_map = self.dao.fetch_many_file_identities(
            [self.dao.file_identity(st) for st in stats.values()]
        )
        path_map = self.dao.fetch_many_paths(list(stats))

        with self.dao.conn:  # single transaction, rolls back on error
            for path, st in stats.items():
                identity = self.dao.file_identity(st)
                candidates = identity_map.get(identity, [])
                # Keep parent folders discoverable even when an existing
                # inode was moved into a previously unindexed directory.
                parents.add(Path(path).parent)

                # Exact paths may come from databases created before device
                # tracking; insert_media refreshes their stored identity.
                if path in path_map:
                    self.dao.insert_media(path, st, commit=False)
                    skipped += 1
                    continue

                # A surviving old path indicates a hard link, not a move. Only
                # reuse an identity when exactly one former path disappeared.
                missing_candidates = [rec for rec in candidates if not Path(rec[1]).exists()]
                if len(missing_candidates) == 1:
                    self.dao.update_media_path(
                        missing_candidates[0][0], path, int(st.st_mtime), commit=False
                    )
                    skipped += 1
                    continue

                # brand-new file -> insert
                mid = self.dao.insert_media(path, st, commit=False)
                newly_added.append((mid, path))
                added += 1

            # ensure all parent folders exist in DB
            for folder in parents:
                self.dao.insert_media(str(folder), commit=False)

            # Ensure import root itself is included
            if result.root.is_dir():
                self.dao.insert_media(str(result.root), commit=False)

        # second pass: stack only the new ones
        for mid, p in newly_added:
            self.variants.detect_and_stack(mid, p)

        self.import_completed.emit(
            ImportSummary(result.root, added, skipped, result.duration)
        )

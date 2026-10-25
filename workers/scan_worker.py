"""Qt adapter for one indexing job; its SQLite connection lives on the worker."""

from __future__ import annotations

import logging
import sqlite3
import time
from contextlib import closing
from pathlib import Path
from threading import Event, Lock

from PySide6.QtCore import QObject, QRunnable, Signal

from application.indexing import BATCH_SIZE, ImportProgress, ImportSummary, run_indexing
from infrastructure.filesystem.scanner import scan_batches
from infrastructure.sqlite.index_repository import SQLiteIndexRepository
from infrastructure.sqlite.schema import validate_schema

logger = logging.getLogger(__name__)


class JobProgress:
    """One coalesced snapshot, not an unbounded queue of GUI progress events."""

    def __init__(self, initial: ImportProgress):
        self._latest = initial
        self._lock = Lock()

    def publish(self, progress: ImportProgress) -> None:
        with self._lock:
            self._latest = progress

    def latest(self) -> ImportProgress:
        with self._lock:
            return self._latest


class ScanSignals(QObject):
    finished = Signal(object)


class ScanWorker(QRunnable):
    def __init__(self, database: Path, root: Path, job_id: str,
                 cancel: Event, progress: JobProgress, signals: ScanSignals,
                 *, batch_size: int = BATCH_SIZE):
        super().__init__()
        self.database, self.root, self.job_id = database, root, job_id
        self.cancel, self.progress, self.signals = cancel, progress, signals
        self.batch_size = batch_size
        self.setAutoDelete(True)

    def run(self) -> None:
        started = time.monotonic()
        try:
            # Open/validate/close on this thread. Never pass the GUI connection
            # across threads or turn off sqlite3's thread-affinity protection.
            with closing(sqlite3.connect(
                    self.database.as_uri() + "?mode=rw", uri=True, timeout=0.1,
            )) as conn:
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA foreign_keys=ON")
                validate_schema(conn)
                repository = SQLiteIndexRepository(conn)
                with closing(scan_batches(self.root, self.cancel, batch_size=self.batch_size)) as batches:
                    summary = run_indexing(self.job_id, self.root, batches, repository,
                                           self.cancel, self.progress.publish)
        except Exception as error:
            logger.exception("Unable to run index job %s", self.job_id)
            summary = ImportSummary(
                self.job_id, self.root, duration=time.monotonic() - started,
                phase="finished", status="cancelled" if self.cancel.is_set() else "failed",
                errors=0 if self.cancel.is_set() else 1,
                error=None if self.cancel.is_set() else str(error),
            )
        # Every terminal signal is emitted after the worker's DB handle closes.
        self.signals.finished.emit(summary)

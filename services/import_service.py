"""GUI-thread lifecycle adapter; indexing and database work happen in ScanWorker."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from threading import Event
from uuid import uuid4

from PySide6.QtCore import QObject, QThreadPool, QTimer, Qt, Signal, Slot

from application.indexing import BATCH_SIZE, ImportProgress, ImportSummary
from workers.scan_worker import JobProgress, ScanSignals, ScanWorker

__all__ = ["ImportService", "ImportSummary"]


class ImportService(QObject):
    import_completed = Signal(object)
    progress_changed = Signal(object)

    def __init__(self, database: Path | None, parent=None, *, batch_size: int = BATCH_SIZE):
        super().__init__(parent)
        if not 1 <= batch_size <= BATCH_SIZE:
            raise ValueError(f"batch_size must be between 1 and {BATCH_SIZE}")
        self.database, self.batch_size = database, batch_size
        # Imports do not compete with the unbounded legacy thumbnail pool.
        # Only one import is accepted at a time; there is no pending-job queue.
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(1)
        self._worker = None
        self._cancel = Event()
        self._progress = None
        self._last_progress = None
        self._job_id = None
        self._closing = False
        self._timer = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._poll_progress)

    @property
    def busy(self) -> bool:
        return self._worker is not None

    def scan(self, root: Path) -> str:
        if self._closing:
            raise RuntimeError("Imports are shutting down")
        if self.busy:
            raise RuntimeError("An import is already running; cancel it or wait for completion")
        if self.database is None:
            raise ValueError("Background indexing requires a file-backed SQLite catalog")
        self._job_id = uuid4().hex
        root = root.expanduser().absolute()
        self._cancel = Event()
        self._progress = JobProgress(ImportProgress(self._job_id, root))
        self._last_progress = None
        signals = ScanSignals(self)
        signals.finished.connect(self._on_done, Qt.ConnectionType.QueuedConnection)
        self._worker = ScanWorker(self.database, root, self._job_id, self._cancel,
                                  self._progress, signals, batch_size=self.batch_size)
        self.pool.start(self._worker)
        self._timer.start()
        return self._job_id

    def cancel(self) -> None:
        if self.busy:
            self._cancel.set()

    def shutdown(self) -> bool:
        """Request cancellation; return immediately with whether workers have exited."""
        self._closing = True
        self.cancel()
        self._timer.stop()
        # The window retries close through its event loop, never a blocking join.
        return self.pool.waitForDone(0)

    @Slot()
    def _poll_progress(self) -> None:
        if self._progress is None or self._closing:
            return
        progress = self._progress.latest()
        if self._cancel.is_set():
            progress = replace(progress, phase="cancelling")
        if progress != self._last_progress:
            self._last_progress = progress
            self.progress_changed.emit(progress)

    @Slot(object)
    def _on_done(self, summary: ImportSummary) -> None:
        if summary.job_id != self._job_id:
            return  # Ignore late results belonging to a different UI session.
        self._timer.stop()
        self._worker.signals.deleteLater()
        self._worker = None
        self._progress = None
        self._job_id = None
        if not self._closing:
            self.progress_changed.emit(summary)
            self.import_completed.emit(summary)

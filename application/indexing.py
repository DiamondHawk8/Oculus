"""Bounded indexing orchestration and immutable messages for the UI adapter."""

from __future__ import annotations

import logging
import os
import stat
import time
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from threading import Event
from typing import Callable, Iterable, Protocol, Sequence

logger = logging.getLogger(__name__)
BATCH_SIZE = 256
PREVIEW_LIMIT = 200
ISSUE_LIMIT = 20


class IndexCancelled(Exception):
    """Cooperative cancellation; previously committed batches remain valid."""


def check_cancelled(cancel: Event) -> None:
    if cancel.is_set():
        raise IndexCancelled()


@dataclass(frozen=True)
class ScannedEntry:
    path: Path
    stat: os.stat_result

    @property
    def is_dir(self) -> bool:
        return stat.S_ISDIR(self.stat.st_mode)


@dataclass(frozen=True)
class ScanIssue:
    path: Path
    message: str
    fatal: bool = False


@dataclass(frozen=True)
class DirectoryComplete:
    path: Path


ScanRecord = ScannedEntry | ScanIssue | DirectoryComplete


@dataclass(frozen=True)
class BatchCounts:
    added: int = 0
    skipped: int = 0  # Includes refreshed paths and confidently recognized moves.
    moved: int = 0
    directories: int = 0


@dataclass(frozen=True)
class ImportProgress:
    job_id: str
    root: Path
    added: int = 0
    skipped: int = 0
    moved: int = 0
    directories: int = 0
    errors: int = 0
    duration: float = 0
    phase: str = "preparing"
    first_commit_seconds: float | None = None


@dataclass(frozen=True)
class ImportSummary(ImportProgress):
    status: str = "completed"  # completed, partial, cancelled, failed
    error: str | None = None
    issues: tuple[ScanIssue, ...] = ()
    folder_preview: tuple[Path, ...] = ()


class IndexRepository(Protocol):
    def prepare(self, cancel: Event) -> None: ...
    def write_batch(self, entries: Sequence[ScannedEntry], cancel: Event) -> BatchCounts: ...
    def reconcile_folder(self, folder: Path, cancel: Event) -> None: ...


def run_indexing(
        job_id: str, root: Path, batches: Iterable[tuple[ScanRecord, ...]],
        repository: IndexRepository, cancel: Event,
        publish: Callable[[ImportProgress], None],
) -> ImportSummary:
    started = time.monotonic()
    progress = ImportProgress(job_id, root)
    issues: list[ScanIssue] = []
    folders: list[Path] = []
    status, error = "completed", None
    error_counted = False

    def report(**changes) -> None:
        nonlocal progress
        progress = replace(progress, duration=time.monotonic() - started, **changes)
        publish(progress)

    try:
        publish(progress)
        check_cancelled(cancel)
        repository.prepare(cancel)
        for batch in batches:
            check_cancelled(cancel)
            entries = [record for record in batch if isinstance(record, ScannedEntry)]
            for record in batch:
                if isinstance(record, ScanIssue):
                    logger.warning("Indexing %s: %s", record.path, record.message)
                    if len(issues) < ISSUE_LIMIT:
                        issues.append(record)
                    report(errors=progress.errors + 1)
                    if record.fatal:
                        error_counted = True
                        raise OSError(f"{record.path}: {record.message}")
            if entries:
                counts = repository.write_batch(entries, cancel)
                # Publish only committed counts, never rolled-back/in-flight work.
                report(added=progress.added + counts.added,
                       skipped=progress.skipped + counts.skipped,
                       moved=progress.moved + counts.moved,
                       directories=progress.directories + counts.directories,
                       phase="scanning",
                       first_commit_seconds=(progress.first_commit_seconds
                                             if progress.first_commit_seconds is not None
                                             else time.monotonic() - started))
                for entry in entries:
                    if entry.is_dir and len(folders) < PREVIEW_LIMIT:
                        folders.append(entry.path)
            for record in batch:
                if isinstance(record, DirectoryComplete):
                    report(phase="stacking")
                    repository.reconcile_folder(record.path, cancel)
        check_cancelled(cancel)
        if progress.errors:
            status = "partial"
    except IndexCancelled:
        status = "cancelled"
    except Exception as exc:
        if cancel.is_set():
            status = "cancelled"
        else:
            logger.exception("Index job %s failed", job_id)
            status, error = "failed", str(exc)
            if not error_counted:
                report(errors=progress.errors + 1)
    report(phase="finished")
    return ImportSummary(**asdict(progress), status=status, error=error,
                         issues=tuple(issues), folder_preview=tuple(folders))

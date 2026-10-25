"""Lazy, cancellable depth-first discovery with bounded result batches."""

from __future__ import annotations

import os
import stat
from pathlib import Path
from threading import Event
from typing import Iterator

from application.indexing import (
    BATCH_SIZE, DirectoryComplete, ScannedEntry, ScanIssue, ScanRecord, check_cancelled,
)
from domain.media import MEDIA_EXTENSIONS


def _records(root: Path, cancel: Event) -> Iterator[ScanRecord]:
    stack = []
    try:
        check_cancelled(cancel)
        try:
            root_stat = root.stat()
            if not stat.S_ISDIR(root_stat.st_mode):
                raise NotADirectoryError(str(root))
            iterator = os.scandir(root)
        except OSError as error:
            yield ScanIssue(root, str(error), fatal=True)
            return
        stack.append((root, iterator))
        yield ScannedEntry(root, root_stat)
        while stack:
            check_cancelled(cancel)
            folder, iterator = stack[-1]
            try:
                entry = next(iterator)
            except StopIteration:
                iterator.close()
                stack.pop()
                yield DirectoryComplete(folder)
                continue
            except OSError as error:
                iterator.close()
                stack.pop()
                yield ScanIssue(folder, str(error))
                continue
            path = Path(entry.path)
            try:
                # Do not follow child symlinks/junctions into cycles or outside
                # the selected tree. An explicitly selected root may be a link.
                if entry.is_symlink():
                    continue
                if not entry.is_dir(follow_symlinks=False) and path.suffix.lower() not in MEDIA_EXTENSIONS:
                    continue
                # DirEntry.stat() reports zero device/inode/link counts on
                # Windows. Use os.stat so move/hard-link checks retain real IDs.
                st = os.stat(path, follow_symlinks=False)
                if stat.S_ISDIR(st.st_mode):
                    if getattr(st, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                        continue
                    child_iterator = os.scandir(path)
                    stack.append((path, child_iterator))
                    yield ScannedEntry(path, st)
                elif stat.S_ISREG(st.st_mode) and path.suffix.lower() in MEDIA_EXTENSIONS:
                    yield ScannedEntry(path, st)
            except OSError as error:
                yield ScanIssue(path, str(error))
    finally:
        # Iterator handles are proportional to depth, not the number of files.
        # This also runs on cancellation, database failure, or generator.close().
        for _, iterator in reversed(stack):
            iterator.close()


def scan_batches(root: Path, cancel: Event, *, batch_size: int = BATCH_SIZE) -> Iterator[tuple[ScanRecord, ...]]:
    if not 1 <= batch_size <= BATCH_SIZE:
        raise ValueError(f"batch_size must be between 1 and {BATCH_SIZE}")
    records = _records(root, cancel)
    batch: list[ScanRecord] = []
    try:
        for record in records:
            check_cancelled(cancel)
            batch.append(record)
            if len(batch) == batch_size:
                yield tuple(batch)
                batch.clear()
        if batch:
            check_cancelled(cancel)
            yield tuple(batch)
    finally:
        records.close()

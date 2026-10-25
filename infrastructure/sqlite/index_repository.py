"""Worker-owned catalog writes"""

from __future__ import annotations

import os
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from threading import Event
from typing import Sequence

from application.indexing import BATCH_SIZE, BatchCounts, ScannedEntry, check_cancelled
from domain.media import file_identity, media_kind, variant_key


class SQLiteIndexRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def prepare(self, cancel: Event) -> None:
        check_cancelled(cancel)
        self.conn.set_progress_handler(lambda: int(cancel.is_set()), 1000)
        # Temporary, indexed job state replaces unbounded Python path/identity
        # maps and quadratic per-base variant searches. Nothing changes the
        # persistent schema; SQLite can spill this state to its temporary file.
        self.conn.execute("PRAGMA temp_store=FILE")
        self.conn.execute("PRAGMA temp.cache_size=-2048")
        self.conn.execute("""CREATE TEMP TABLE index_identity (
            id INTEGER PRIMARY KEY, path TEXT, device TEXT, inode TEXT,
            mtime INTEGER, byte_size INTEGER, is_dir INTEGER
        )""")
        self.conn.execute("""INSERT INTO index_identity
            SELECT id,path,device,inode,mtime,byte_size,is_dir FROM media""")
        self.conn.execute("CREATE INDEX temp.idx_identity_key ON index_identity(device,inode)")
        self.conn.execute("""CREATE TEMP TABLE index_seen (
            path TEXT PRIMARY KEY, media_id INTEGER, folder TEXT,
            base_key TEXT, variant_rank INTEGER
        )""")
        self.conn.execute("CREATE INDEX temp.idx_seen_family ON index_seen(folder,base_key,variant_rank)")
        self.conn.execute("CREATE INDEX temp.idx_seen_id ON index_seen(media_id)")
        self.conn.commit()

    @contextmanager
    def _transaction(self, cancel: Event):
        deadline = time.monotonic() + 2.0
        while True:
            check_cancelled(cancel)
            try:
                self.conn.execute("BEGIN IMMEDIATE")
                break
            except sqlite3.OperationalError as error:
                code = getattr(error, "sqlite_errorcode", 0) & 0xff
                if code not in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED) or time.monotonic() >= deadline:
                    raise
                # Cancellation can interrupt the wait; no endless retry queue.
                cancel.wait(0.05)
        try:
            yield
            check_cancelled(cancel)
            self.conn.commit()
        except BaseException:
            self.conn.rollback()
            raise

    def _move_candidate(self, entry: ScannedEntry):
        st = entry.stat
        if entry.is_dir or not st.st_ino or st.st_nlink != 1:
            return None
        if self.conn.execute("SELECT 1 FROM media WHERE path=?", (str(entry.path),)).fetchone():
            return None
        candidates = self.conn.execute(
            "SELECT * FROM index_identity WHERE device=? AND inode=? AND is_dir=0 LIMIT 2",
            file_identity(st),
        ).fetchall()
        if len(candidates) != 1:
            return None  # Multiple former paths are ambiguous, not proof of a move.
        row = candidates[0]
        if row["byte_size"] != st.st_size or row["mtime"] != int(st.st_mtime):
            return None  # Inode reuse or changed content must not steal metadata.
        if self.conn.execute("SELECT 1 FROM index_seen WHERE media_id=?", (row["id"],)).fetchone():
            return None
        if os.path.normcase(row["path"]) == os.path.normcase(str(entry.path)):
            # A case-only rename on Windows still resolves at the old spelling;
            # it is the same location, not a second hard-link identity.
            return row
        try:
            os.stat(row["path"], follow_symlinks=False)
        except FileNotFoundError:
            try:
                # An offline/renamed parent cannot establish that a file moved.
                # This intentionally prefers retaining the old row to guessing.
                parent_stat = Path(row["path"]).parent.stat()
                return row if parent_stat.st_dev == st.st_dev else None
            except OSError:
                return None
        except OSError:
            pass
        return None

    def write_batch(self, entries: Sequence[ScannedEntry], cancel: Event) -> BatchCounts:
        if len(entries) > BATCH_SIZE:
            raise ValueError("Indexing batch exceeds its configured bound")
        # Missing-path probes can block on filesystem I/O. Finish them before
        # reserving SQLite's writer so legacy UI metadata writers are not held up.
        candidates = []
        for entry in entries:
            check_cancelled(cancel)
            candidates.append(self._move_candidate(entry))
        added = skipped = moved = directories = 0
        with self._transaction(cancel):
            for entry, candidate in zip(entries, candidates):
                check_cancelled(cancel)
                path, st = str(entry.path), entry.stat
                row = self.conn.execute("SELECT id FROM media WHERE path=?", (path,)).fetchone()
                mid = row["id"] if row else None
                if mid is None and candidate is not None:
                    # Recheck the snapshot under the write lock. A concurrent
                    # rename or an earlier entry in this batch may have claimed it.
                    updated = self.conn.execute(
                        """UPDATE media SET path=? WHERE id=? AND path=? AND device=?
                           AND inode=? AND mtime=? AND byte_size=? AND is_dir=0""",
                        (path, candidate["id"], candidate["path"], candidate["device"],
                         candidate["inode"], candidate["mtime"], candidate["byte_size"]),
                    ).rowcount
                    if updated:
                        mid = candidate["id"]
                        moved += 1
                        # Comments/presets reference the unchanged media ID;
                        # bookmarks still use paths until their later refactor.
                        self.conn.execute(
                            "INSERT OR IGNORE INTO bookmarks(path,time_ms) "
                            "SELECT ?,time_ms FROM bookmarks WHERE path=?", (path, candidate["path"]),
                        )
                        self.conn.execute("DELETE FROM bookmarks WHERE path=?", (candidate["path"],))
                is_dir = int(entry.is_dir)
                device, inode = file_identity(st)
                size = 0 if is_dir else st.st_size
                values = (is_dir, size, media_kind(entry.path, bool(is_dir)), device, inode, int(st.st_mtime))
                if mid is None:
                    cursor = self.conn.execute(
                        "INSERT INTO media(path,added,is_dir,byte_size,type,device,inode,mtime) "
                        "VALUES (?,?,?,?,?,?,?,?)", (path, int(time.time()), *values),
                    )
                    mid = cursor.lastrowid
                    added += not is_dir
                else:
                    self.conn.execute(
                        "UPDATE media SET is_dir=?,byte_size=?,type=?,device=?,inode=?,mtime=? WHERE id=?",
                        (*values, mid),
                    )
                    skipped += not is_dir
                directories += is_dir
                self.conn.execute(
                    "INSERT OR REPLACE INTO index_identity VALUES (?,?,?,?,?,?,?)",
                    (mid, path, device, inode, int(st.st_mtime), size, is_dir),
                )
                if not is_dir:
                    key, rank = variant_key(entry.path)
                    self.conn.execute(
                        "INSERT OR REPLACE INTO index_seen VALUES (?,?,?,?,?)",
                        (path, mid, str(entry.path.parent), key, rank),
                    )
        return BatchCounts(added, skipped, moved, directories)

    def reconcile_folder(self, folder: Path, cancel: Event) -> None:
        # All observed names in this directory are now staged, irrespective of
        # enumeration order or batch boundaries. Existing/manual stacks survive.
        cursor = self.conn.execute(
            """SELECT b.media_id,v.media_id,v.variant_rank FROM index_seen v
               JOIN index_seen b ON b.folder=v.folder AND b.base_key=v.base_key
                                    AND b.variant_rank IS NULL
               WHERE v.folder=? AND v.variant_rank IS NOT NULL
                 AND NOT EXISTS (
                     SELECT 1 FROM index_seen other WHERE other.folder=b.folder
                     AND other.base_key=b.base_key AND other.variant_rank IS NULL
                     AND other.media_id<>b.media_id)
               ORDER BY v.media_id""", (str(folder),),
        )
        try:
            while True:
                check_cancelled(cancel)
                rows = cursor.fetchmany(BATCH_SIZE)
                if not rows:
                    break
                with self._transaction(cancel):
                    self.conn.executemany(
                        "INSERT OR IGNORE INTO variants(base_id,variant_id,rank) VALUES (?,?,?)", rows,
                    )
        finally:
            cursor.close()

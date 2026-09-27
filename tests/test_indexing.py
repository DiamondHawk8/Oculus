"""Indexing regression tests: real temporary files/catalogs, no configured data."""

from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from threading import Event
from unittest.mock import patch

from application.indexing import (
    BATCH_SIZE, ISSUE_LIMIT, PREVIEW_LIMIT, DirectoryComplete, IndexCancelled,
    ScanIssue, ScannedEntry, run_indexing,
)
from infrastructure.filesystem.scanner import scan_batches
from infrastructure.sqlite.index_repository import SQLiteIndexRepository
from managers.dao import MediaDAO
from managers.db_utils import get_db_connection


class IndexingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.folder = self.root / "media"
        self.folder.mkdir()
        self.database = self.root / "catalog.db"
        self.conn = get_db_connection(db_path=self.database, backend="sqlite")
        self.dao = MediaDAO(self.conn)

    def tearDown(self):
        self.conn.close()
        self.temporary.cleanup()

    def file(self, name, content=b"test") -> Path:
        path = self.folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def index(self, *, root=None, cancel=None, publish=None, batch_size=BATCH_SIZE, batches=None):
        root = self.folder if root is None else root
        cancel = Event() if cancel is None else cancel
        with closing(sqlite3.connect(self.database, timeout=0.01)) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys=ON")
            repository = SQLiteIndexRepository(conn)
            if batches is not None:
                return run_indexing("test", root, batches, repository, cancel, publish or (lambda _: None))
            with closing(scan_batches(root, cancel, batch_size=batch_size)) as stream:
                return run_indexing("test", root, stream, repository, cancel, publish or (lambda _: None))

    def test_scanner_is_bounded_and_includes_empty_directories(self):
        for i in range(600):
            self.file(f"{i}.png")
        self.file("ignored.txt")
        (self.folder / "empty").mkdir()
        batches = list(scan_batches(self.folder, Event(), batch_size=17))
        self.assertLessEqual(max(map(len, batches)), 17)
        entries = [item for batch in batches for item in batch if isinstance(item, ScannedEntry)]
        self.assertEqual(sum(not item.is_dir for item in entries), 600)
        self.assertEqual(sum(item.is_dir for item in entries), 2)
        completed = [item.path for batch in batches for item in batch if isinstance(item, DirectoryComplete)]
        self.assertEqual(set(completed), {self.folder, self.folder / "empty"})

    def test_scanner_cancellation_closes_open_directory_handles(self):
        self.file("sub/image.png")
        cancel = Event()
        handles = []
        real_scandir = os.scandir

        class TrackedIterator:
            def __init__(self, path):
                self.inner = real_scandir(path)
                self.closed = False
                handles.append(self)

            def __next__(self):
                return next(self.inner)

            def close(self):
                self.closed = True
                self.inner.close()

        with patch("infrastructure.filesystem.scanner.os.scandir", side_effect=TrackedIterator):
            stream = scan_batches(self.folder, cancel, batch_size=1)
            next(stream)
            cancel.set()
            with self.assertRaises(IndexCancelled):
                next(stream)
        self.assertTrue(handles)
        self.assertTrue(all(handle.closed for handle in handles))

    def test_discovery_retains_real_filesystem_identity_on_windows(self):
        path = self.file("identity.png")
        found = [record for batch in scan_batches(self.folder, Event()) for record in batch
                 if isinstance(record, ScannedEntry) and record.path == path][0]
        expected = path.stat()
        self.assertEqual((found.stat.st_dev, found.stat.st_ino, found.stat.st_nlink),
                         (expected.st_dev, expected.st_ino, expected.st_nlink))

    def test_symlink_entries_are_not_followed(self):
        class LinkedEntry:
            path = str(self.folder / "loop")

            @staticmethod
            def is_symlink():
                return True

            @staticmethod
            def stat(**_):
                raise AssertionError("symlink should not be traversed")

        class FakeIterator:
            def __init__(self):
                self.entries = iter([LinkedEntry()])

            def __next__(self):
                return next(self.entries)

            def close(self):
                pass

        with patch("infrastructure.filesystem.scanner.os.scandir", return_value=FakeIterator()) as scan:
            batches = list(scan_batches(self.folder, Event()))
        self.assertEqual(scan.call_count, 1)
        self.assertEqual(sum(isinstance(item, ScannedEntry) for batch in batches for item in batch), 1)

    def test_each_committed_batch_is_visible_before_completion(self):
        for i in range(7):
            self.file(f"{i}.png")
        observed = []

        def observe(progress):
            if progress.added:
                count = self.conn.execute("SELECT count(*) FROM media WHERE is_dir=0").fetchone()[0]
                observed.append((progress.added, count))

        summary = self.index(batch_size=2, publish=observe)
        self.assertEqual(summary.status, "completed")
        self.assertEqual(summary.added, 7)
        self.assertTrue(any(0 < count < 7 for _, count in observed))
        self.assertTrue(all(added == count for added, count in observed))
        self.assertIsNotNone(summary.first_commit_seconds)

    def test_rescan_keeps_ids_comments_presets_and_attributes(self):
        image = self.file("image.png")
        mid = self.dao.insert_media(str(image))
        self.conn.execute("INSERT INTO comments(media_id,text,seq) VALUES (?, 'my note', 8)", (mid,))
        self.conn.execute("INSERT INTO presets(group_id,name,media_id,zoom,pan_x,pan_y,is_default,hotkey) "
                          "VALUES ('g','crop',?,1.75,-5,9,1,'Ctrl+2')", (mid,))
        self.conn.execute("UPDATE media SET favorite=1,artist='Artist',weight=0.7 WHERE id=?", (mid,))
        self.conn.commit()
        before = {table: [tuple(row) for row in self.conn.execute(f"SELECT * FROM {table}")]
                  for table in ("comments", "presets")}
        image.write_bytes(b"larger content")
        summary = self.index()
        self.assertEqual((summary.added, summary.skipped), (0, 1))
        row = self.conn.execute("SELECT id,byte_size,favorite,artist,weight FROM media WHERE path=?",
                                (str(image),)).fetchone()
        self.assertEqual(tuple(row), (mid, len(b"larger content"), 1, "Artist", 0.7))
        for table, expected in before.items():
            self.assertEqual([tuple(row) for row in self.conn.execute(f"SELECT * FROM {table}")], expected)

    def test_external_move_reuses_id_and_moves_path_based_bookmarks(self):
        old = self.file("old.png")
        mid = self.dao.insert_media(str(old))
        self.dao.add_comment(mid, "keep", 1)
        self.dao.add_bookmark(str(old), 500)
        new = self.folder / "new.png"
        old.rename(new)
        summary = self.index()
        self.assertEqual((summary.added, summary.skipped, summary.moved), (0, 1, 1))
        self.assertEqual(self.dao.path_for_id(mid), str(new))
        self.assertEqual(self.dao.list_comments(mid)[0]["text"], "keep")
        self.assertEqual(self.dao.bookmarks_for_path(str(new)), [500])
        self.assertEqual(self.dao.bookmarks_for_path(str(old)), [])

    def test_hardlinks_do_not_steal_the_original_media_id(self):
        original = self.file("original.png")
        mid = self.dao.insert_media(str(original))
        alias = self.folder / "alias.png"
        os.link(original, alias)
        self.index(batch_size=1)
        alias_id = self.conn.execute("SELECT id FROM media WHERE path=?", (str(alias),)).fetchone()[0]
        self.assertNotEqual(alias_id, mid)
        self.assertEqual(self.dao.path_for_id(mid), str(original))

    @unittest.skipUnless(os.name == "nt", "Windows case-insensitive paths")
    def test_case_only_external_rename_preserves_id(self):
        old = self.file("lower.png")
        mid = self.dao.insert_media(str(old))
        renamed = self.folder / "LOWER.png"
        old.rename(renamed)
        summary = self.index()
        self.assertEqual((summary.added, summary.moved), (0, 1))
        self.assertEqual(self.dao.path_for_id(mid), str(renamed))

    def test_two_hardlinks_after_old_name_disappears_are_not_claimed_as_one_move(self):
        original = self.file("original.png")
        mid = self.dao.insert_media(str(original))
        self.dao.add_comment(mid, "do not assign arbitrarily", 1)
        first, second = self.folder / "first.png", self.folder / "second.png"
        original.rename(first)
        os.link(first, second)
        summary = self.index(batch_size=1)
        self.assertEqual((summary.added, summary.moved), (2, 0))
        self.assertEqual(self.dao.path_for_id(mid), str(original))
        self.assertEqual(self.dao.list_comments(mid)[0]["text"], "do not assign arbitrarily")

    def test_changed_content_and_missing_parent_are_not_assumed_to_be_moves(self):
        old = self.file("before.png")
        mid = self.dao.insert_media(str(old))
        new = self.folder / "after.png"
        old.rename(new)
        new.write_bytes(b"changed contents")
        self.assertEqual(self.index().moved, 0)
        self.assertEqual(self.dao.path_for_id(mid), str(old))
        nested = self.file("old-dir/moved.png")
        nested_mid = self.dao.insert_media(str(nested))
        nested.rename(self.folder / "moved.png")
        nested.parent.rmdir()
        self.assertEqual(self.index().moved, 0)
        self.assertEqual(self.dao.path_for_id(nested_mid), str(nested))

    def test_ambiguous_legacy_identities_do_not_reassign_metadata(self):
        old = self.file("old.png")
        other = self.file("other.png")
        old_id, other_id = self.dao.insert_media(str(old)), self.dao.insert_media(str(other))
        device, inode = self.dao.file_identity(old.stat())
        self.conn.execute("UPDATE media SET device=?,inode=? WHERE id=?", (device, inode, other_id))
        self.conn.commit()
        other.unlink()
        old.rename(self.folder / "new.png")
        summary = self.index()
        self.assertEqual((summary.added, summary.moved), (1, 0))
        self.assertEqual(self.dao.path_for_id(old_id), str(old))
        self.assertEqual(self.dao.path_for_id(other_id), str(other))

    def test_variant_before_base_across_batches_and_directories(self):
        variant = self.file("photo_v1.PNG")
        base = self.file("photo.png")
        unrelated = self.file("nested/photo_v2.png")
        batches = [(ScannedEntry(self.folder, self.folder.stat()),),
                   (ScannedEntry(variant, variant.stat()),),
                   (ScannedEntry(unrelated, unrelated.stat()),),
                   (ScannedEntry(base, base.stat()),), (DirectoryComplete(self.folder),)]
        summary = self.index(batches=batches)
        self.assertEqual(summary.status, "completed")
        self.assertEqual(self.dao.stack_paths(str(base)), [str(base), str(variant)])
        self.assertFalse(self.dao.is_variant(str(unrelated)))
        # A completed rescan also repairs stacks left unfinished by cancellation.
        self.conn.execute("DELETE FROM variants")
        self.conn.commit()
        self.index(batch_size=1)
        self.assertEqual(self.dao.stack_paths(str(base)), [str(base), str(variant)])

    def test_existing_manual_stack_is_not_overwritten(self):
        base = self.file("base.png")
        auto_variant = self.file("base_v1.png")
        manual = self.file("manual.png")
        base_id = self.dao.insert_media(str(base))
        variant_id = self.dao.insert_media(str(auto_variant))
        manual_id = self.dao.insert_media(str(manual))
        self.dao.add_variant(manual_id, variant_id, 7)
        self.index(batch_size=1)
        self.assertEqual(tuple(self.conn.execute("SELECT base_id,variant_id,rank FROM variants").fetchone()),
                         (manual_id, variant_id, 7))
        self.assertFalse(self.dao.is_stacked_base(base_id))

    def test_large_variant_family_is_linked_in_multiple_transactions(self):
        base = self.file("photo.png")
        for rank in range(1, BATCH_SIZE + 4):
            self.file(f"photo_v{rank}.png")
        summary = self.index()
        self.assertEqual(summary.status, "completed")
        self.assertEqual(len(self.dao.stack_paths(str(base))), BATCH_SIZE + 4)

    def test_cancellation_retains_committed_work_and_retry_finishes(self):
        for i in range(8):
            self.file(f"{i}.png")
        cancel = Event()

        def cancel_after_batch(progress):
            if progress.added >= 2:
                cancel.set()

        summary = self.index(cancel=cancel, publish=cancel_after_batch, batch_size=2)
        self.assertEqual(summary.status, "cancelled")
        self.assertTrue(0 < summary.added < 8)
        count = self.conn.execute("SELECT count(*) FROM media WHERE is_dir=0").fetchone()[0]
        self.assertEqual(count, summary.added)
        retry = self.index(batch_size=2)
        self.assertEqual(retry.status, "completed")
        self.assertEqual(retry.added + retry.skipped, 8)

    def test_failed_batch_rolls_back_and_reports_only_previous_commits(self):
        good = self.file("good.png")
        earlier = self.file("earlier-in-bad-batch.png")
        bad = self.file("bad.png")
        self.conn.execute("""CREATE TRIGGER fail_import BEFORE INSERT ON media
            WHEN NEW.path LIKE '%bad.png' BEGIN SELECT RAISE(ABORT,'injected write failure'); END""")
        self.conn.commit()
        batches = [(ScannedEntry(good, good.stat()),),
                   (ScannedEntry(earlier, earlier.stat()), ScannedEntry(bad, bad.stat()))]
        with self.assertLogs("application.indexing", level="ERROR"):
            summary = self.index(batches=batches)
        self.assertEqual(summary.status, "failed")
        self.assertEqual(summary.added, 1)
        self.assertEqual(self.dao.all_paths(), [str(good)])

    def test_cancellation_inside_batch_rolls_back_that_batch(self):
        first, second = self.file("first.png"), self.file("second.png")
        cancel = Event()
        original = SQLiteIndexRepository.write_batch

        def interrupt_insert(repository, entries, token):
            def trace(sql):
                if sql.startswith("INSERT INTO media("):
                    cancel.set()
            repository.conn.set_trace_callback(trace)
            try:
                return original(repository, entries, token)
            finally:
                repository.conn.set_trace_callback(None)

        with patch.object(SQLiteIndexRepository, "write_batch", interrupt_insert):
            summary = self.index(cancel=cancel, batches=[
                (ScannedEntry(first, first.stat()), ScannedEntry(second, second.stat()))
            ])
        self.assertEqual(summary.status, "cancelled")
        self.assertEqual(summary.added, 0)
        self.assertEqual(self.dao.all_paths(), [])

    def test_unreadable_subdirectory_reports_partial_and_retains_existing_rows(self):
        hidden = self.file("blocked/hidden.png")
        mid = self.dao.insert_media(str(hidden))
        good = self.file("good.png")
        real_scandir = os.scandir

        def deny_directory(path):
            if Path(path) == hidden.parent:
                raise PermissionError("test permission failure")
            return real_scandir(path)

        with patch("infrastructure.filesystem.scanner.os.scandir", side_effect=deny_directory):
            with self.assertLogs("application.indexing", level="WARNING"):
                summary = self.index()
        self.assertEqual((summary.status, summary.errors, summary.added), ("partial", 1, 1))
        self.assertEqual(self.dao.path_for_id(mid), str(hidden))
        self.assertIn(str(good), self.dao.all_paths())

    def test_missing_root_is_a_failure_not_an_empty_success(self):
        existing = self.file("keep.png")
        mid = self.dao.insert_media(str(existing))
        with self.assertLogs("application.indexing", level="WARNING"):
            summary = self.index(root=self.root / "offline")
        self.assertEqual(summary.status, "failed")
        self.assertEqual(summary.added, 0)
        self.assertEqual(self.dao.path_for_id(mid), str(existing))

    def test_pre_cancelled_job_writes_nothing(self):
        self.file("untouched.png")
        cancel = Event()
        cancel.set()
        summary = self.index(cancel=cancel)
        self.assertEqual(summary.status, "cancelled")
        self.assertEqual(self.dao.all_paths(files_only=False), [])

    def test_successful_empty_scan_does_not_delete_missing_media_metadata(self):
        missing = self.file("missing.png")
        mid = self.dao.insert_media(str(missing))
        self.dao.add_comment(mid, "retain even when unavailable", 1)
        missing.unlink()
        summary = self.index()
        self.assertEqual((summary.status, summary.added), ("completed", 0))
        self.assertEqual(self.dao.path_for_id(mid), str(missing))
        self.assertEqual(self.dao.list_comments(mid)[0]["text"], "retain even when unavailable")

    def test_error_and_folder_previews_are_capped(self):
        for i in range(PREVIEW_LIMIT + 5):
            (self.folder / str(i)).mkdir()
        summary = self.index()
        self.assertEqual(len(summary.folder_preview), PREVIEW_LIMIT)
        self.assertEqual(summary.directories, PREVIEW_LIMIT + 6)
        batches = [(ScanIssue(self.folder / str(i), "unreadable"),) for i in range(ISSUE_LIMIT + 5)]
        with self.assertLogs("application.indexing", level="WARNING"):
            summary = self.index(batches=batches)
        self.assertEqual(summary.status, "partial")
        self.assertEqual(summary.errors, ISSUE_LIMIT + 5)
        self.assertEqual(len(summary.issues), ISSUE_LIMIT)

    def test_persistent_schema_and_version_do_not_change(self):
        self.file("image.png")
        before = list(self.conn.execute("SELECT sql FROM sqlite_master ORDER BY name"))
        self.index()
        self.assertEqual(list(self.conn.execute("SELECT sql FROM sqlite_master ORDER BY name")), before)
        self.assertEqual(self.conn.execute("PRAGMA user_version").fetchone()[0], 4)


if __name__ == "__main__":
    unittest.main()

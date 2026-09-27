"""Qt lifecycle tests, with offscreen widgets and disposable SQLite catalogs."""

from __future__ import annotations

import os
import sqlite3
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from application.indexing import ImportProgress, ImportSummary
from infrastructure.sqlite.index_repository import SQLiteIndexRepository
from managers.db_utils import get_db_connection
from services.import_service import ImportService
from utils.config import AppConfig
from workers.scan_worker import JobProgress


class ImportServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.database = self.root / "catalog.db"
        self.folder = self.root / "media"
        self.folder.mkdir()
        for i in range(12):
            (self.folder / f"{i}.png").write_bytes(b"test")
        self.conn = get_db_connection(db_path=self.database, backend="sqlite")
        self.service = ImportService(self.database, batch_size=2)
        self.summaries = []
        self.service.import_completed.connect(self.summaries.append)

    def tearDown(self):
        self.service.shutdown()
        self.assertTrue(self.service.pool.waitForDone(3000))
        self.app.processEvents()
        self.service.deleteLater()
        self.app.processEvents()
        self.conn.close()
        self.temporary.cleanup()

    def wait_for(self, predicate, timeout=5):
        deadline = time.monotonic() + timeout
        while not predicate() and time.monotonic() < deadline:
            QTest.qWait(10)
        self.assertTrue(predicate(), "Timed out waiting for Qt/background work")

    def test_sql_runs_off_gui_thread_and_terminal_signal_returns_to_gui(self):
        gui_thread = threading.get_ident()
        sql_threads = []
        callback_threads = []
        original = SQLiteIndexRepository.prepare

        def capture_prepare(repository, cancel):
            sql_threads.append(threading.get_ident())
            return original(repository, cancel)

        self.service.import_completed.connect(lambda _: callback_threads.append(threading.get_ident()))
        with patch.object(SQLiteIndexRepository, "prepare", capture_prepare):
            job_id = self.service.scan(self.folder)
            self.wait_for(lambda: bool(self.summaries))
        self.assertNotEqual(sql_threads, [gui_thread])
        self.assertEqual(len(sql_threads), 1)
        self.assertEqual(callback_threads, [gui_thread])
        self.assertEqual(self.summaries[0].job_id, job_id)
        self.assertEqual(self.summaries[0].status, "completed")
        # The original connection remains owned and usable by this GUI thread.
        self.assertEqual(self.conn.execute("SELECT count(*) FROM media WHERE is_dir=0").fetchone()[0], 12)

    def test_gui_heartbeat_and_cancellation_during_slow_batches(self):
        ticks = []
        progress = []
        timer = QTimer()
        timer.setInterval(5)
        timer.timeout.connect(lambda: ticks.append(time.monotonic()))
        self.service.progress_changed.connect(progress.append)
        original = SQLiteIndexRepository.write_batch

        def slow_batch(repository, entries, cancel):
            cancel.wait(0.04)
            return original(repository, entries, cancel)

        timer.start()
        try:
            with patch.object(SQLiteIndexRepository, "write_batch", slow_batch):
                self.service.scan(self.folder)
                self.wait_for(lambda: bool(progress) and progress[-1].added > 0)
                self.service.cancel()
                self.wait_for(lambda: bool(self.summaries))
        finally:
            timer.stop()
        self.assertGreaterEqual(len(ticks), 3)
        self.assertEqual(self.summaries[0].status, "cancelled")
        self.assertLess(self.summaries[0].added, 12)
        self.assertGreater(self.summaries[0].added, 0)

    def test_progress_is_coalesced_to_one_snapshot(self):
        state = JobProgress(ImportProgress("id", self.folder))
        for i in range(10000):
            state.publish(ImportProgress("id", self.folder, added=i))
        self.assertEqual(state.latest().added, 9999)
        self.assertEqual(set(vars(state)), {"_latest", "_lock"})

    def test_busy_imports_are_rejected_and_later_imports_get_a_new_id(self):
        first = self.service.scan(self.folder)
        with self.assertRaisesRegex(RuntimeError, "already running"):
            self.service.scan(self.folder)
        self.wait_for(lambda: len(self.summaries) == 1)
        second = self.service.scan(self.folder)
        self.assertNotEqual(first, second)
        self.wait_for(lambda: len(self.summaries) == 2)
        self.assertEqual((self.summaries[1].added, self.summaries[1].skipped), (0, 12))

    def test_cancellation_while_another_connection_holds_writer_lock(self):
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            self.service.scan(self.folder)
            QTest.qWait(150)
            self.service.cancel()
            self.wait_for(lambda: bool(self.summaries))
        finally:
            self.conn.rollback()
        self.assertEqual(self.summaries[0].status, "cancelled")
        self.assertEqual(self.summaries[0].added, 0)

    def test_shutdown_is_nonblocking_and_suppresses_late_ui_callbacks(self):
        entered = threading.Event()
        release = threading.Event()
        original = SQLiteIndexRepository.prepare

        def paused_prepare(repository, cancel):
            entered.set()
            release.wait(2)
            return original(repository, cancel)

        with patch.object(SQLiteIndexRepository, "prepare", paused_prepare):
            self.service.scan(self.folder)
            self.wait_for(entered.is_set)
            try:
                self.assertFalse(self.service.shutdown())
                with self.assertRaisesRegex(RuntimeError, "shutting down"):
                    self.service.scan(self.folder)
            finally:
                release.set()
            self.wait_for(lambda: self.service.pool.waitForDone(0))
            self.app.processEvents()
        self.assertEqual(self.summaries, [])

    def test_missing_database_fails_without_creating_a_replacement(self):
        self.service.database = self.root / "nonexistent.db"
        with self.assertLogs("workers.scan_worker", level="ERROR"):
            self.service.scan(self.folder)
            self.wait_for(lambda: bool(self.summaries))
        self.assertEqual(self.summaries[0].status, "failed")
        self.assertFalse(self.service.database.exists())

    def test_memory_only_catalog_is_rejected_without_starting_a_worker(self):
        self.service.database = None
        with self.assertRaisesRegex(ValueError, "file-backed"):
            self.service.scan(self.folder)
        self.assertFalse(self.service.busy)

    def make_window(self):
        from main import MainWindow

        config = AppConfig(database_path=self.database, log_path=self.root / "app.log",
                           backup_dir=self.root / "backups", operation_backup_dir=self.root / "operations",
                           collection_root=None, backup_on_startup=False,
                           migrate_drive_comments=False, migration_root=None)
        window = MainWindow(config)
        self.addCleanup(window.close)
        return window

    def test_controller_does_not_rewalk_tree_or_auto_load_all_thumbnails(self):
        window = self.make_window()
        controller = window.import_controller
        with patch("controllers.import_controller.QFileDialog.getExistingDirectory", return_value=str(self.folder)):
            with patch.object(window.media, "walk_tree") as walk, \
                 patch.object(window.gallery_controller, "open_folder") as open_folder:
                controller._choose_folder()
                self.wait_for(lambda: controller._job_id is None)
                walk.assert_not_called()
                open_folder.assert_not_called()
                self.assertTrue(controller._open_button.isEnabled())
                self.assertEqual(window.ui.debugFolderTree.topLevelItemCount(), 1)
                controller._open_imported_folder()
                open_folder.assert_called_once_with(str(self.folder))
        window.close()

    def test_controller_ignores_results_from_another_job(self):
        window = self.make_window()
        controller = window.import_controller
        controller._job_id = "current"
        window.ui.importStatus.setText("current status")
        controller.handle_progress(ImportProgress("stale", self.folder, added=999))
        controller.handle_scan_finished(ImportSummary("stale", self.folder))
        self.assertEqual(window.ui.importStatus.text(), "current status")
        self.assertEqual(controller._job_id, "current")
        window.close()

    def test_window_closes_only_after_worker_connection_is_released(self):
        window = self.make_window()
        window.show()
        entered, release = threading.Event(), threading.Event()
        original = SQLiteIndexRepository.prepare

        def paused_prepare(repository, cancel):
            entered.set()
            release.wait(2)
            return original(repository, cancel)

        with patch.object(SQLiteIndexRepository, "prepare", paused_prepare):
            window.media.scan_folder(self.folder)
            self.wait_for(entered.is_set)
            try:
                self.assertFalse(window.close())
                self.assertEqual(window.conn.execute("SELECT 1").fetchone()[0], 1)
            finally:
                release.set()
            self.wait_for(lambda: not window.isVisible())
        with self.assertRaises(sqlite3.ProgrammingError):
            window.conn.execute("SELECT 1")


if __name__ == "__main__":
    unittest.main()

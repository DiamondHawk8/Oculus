"""Current-schema startup and explicit conversion tests use disposable catalogs."""

from __future__ import annotations

import io
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from infrastructure.sqlite import migrations, schema
from infrastructure.sqlite.migrations import ConversionError, convert_catalog
from infrastructure.sqlite.schema import SCHEMA_VERSION, SchemaError
from managers.dao import MediaDAO
from managers.db_utils import ensure_schema, get_db_connection


FIXTURE = Path(__file__).parent / "fixtures" / "legacy_v3.sql"
DATA_TABLES = ("media", "comments", "presets", "tags", "variants", "bookmarks",
               "sqlite_sequence", "extension_notes")


def dump(conn: sqlite3.Connection) -> list[str]:
    return list(conn.iterdump())


def rows(conn: sqlite3.Connection) -> dict[str, list[tuple]]:
    return {table: [tuple(row) for row in conn.execute(f"SELECT * FROM {table} ORDER BY rowid")]
            for table in DATA_TABLES}


class CatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.addCleanup(self.temporary.cleanup)
        self.path = self.root / "catalog.db"
        self.backups = self.root / "recovery"

    def connect(self, path: Path | None = None) -> sqlite3.Connection:
        conn = sqlite3.connect(path if path is not None else self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        self.addCleanup(conn.close)
        return conn

    def legacy(self) -> sqlite3.Connection:
        conn = self.connect()
        conn.executescript(FIXTURE.read_text(encoding="utf-8"))
        return conn

    def test_startup_creates_current_schema_without_history_or_backups(self) -> None:
        conn = get_db_connection(db_path=self.path, backend="sqlite")
        self.addCleanup(conn.close)
        self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], SCHEMA_VERSION)
        self.assertIsNone(conn.execute(
            "SELECT 1 FROM sqlite_master WHERE name='schema_migrations'"
        ).fetchone())
        self.assertFalse((self.root / "backups").exists())

    def test_startup_never_converts_existing_v3_catalog(self) -> None:
        conn = self.legacy()
        before = dump(conn)
        with patch.object(migrations, "convert_catalog") as converter:
            with self.assertRaisesRegex(SchemaError, "one-off converter"):
                get_db_connection(db_path=self.path, backend="sqlite")
            converter.assert_not_called()
        self.assertEqual(dump(conn), before)
        self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 3)
        self.assertFalse((self.root / "backups").exists())

    def test_current_schema_can_be_validated_read_only_without_history(self) -> None:
        conn = self.connect()
        ensure_schema(conn)
        before = dump(conn)
        readonly = sqlite3.connect(self.path.as_uri() + "?mode=ro", uri=True)
        self.addCleanup(readonly.close)
        ensure_schema(readonly)
        self.assertEqual(dump(readonly), before)
        self.assertEqual(readonly.total_changes, 0)

    def test_startup_does_not_repair_partial_or_inconsistent_catalogs(self) -> None:
        conn = self.connect()
        conn.execute("CREATE TABLE media(id INTEGER PRIMARY KEY, path TEXT UNIQUE)")
        before = dump(conn)
        with self.assertRaises(SchemaError):
            ensure_schema(conn)
        self.assertEqual(dump(conn), before)
        conn.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
        with self.assertRaisesRegex(SchemaError, "missing"):
            ensure_schema(conn)
        self.assertEqual(dump(conn), before)

    def test_startup_rejects_newer_schema_without_stamping_it_down(self) -> None:
        conn = self.legacy()
        conn.execute("PRAGMA user_version=99")
        before = dump(conn)
        with self.assertRaises(SchemaError):
            ensure_schema(conn)
        self.assertEqual(dump(conn), before)
        self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 99)

    def test_initialization_failure_rolls_back_new_tables_and_version(self) -> None:
        conn = self.connect()
        with patch.object(schema, "INDEXES", (*schema.INDEXES, "invalid SQL")):
            with self.assertRaises(sqlite3.Error):
                ensure_schema(conn)
        self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 0)
        self.assertEqual(list(conn.execute("SELECT name FROM sqlite_master")), [])
        ensure_schema(conn)  # A failed initialization remains retryable.

    def test_schema_setup_leaves_pending_edits_to_the_caller(self) -> None:
        conn = self.legacy()
        conn.execute("UPDATE comments SET text='pending edit' WHERE id=5")
        with self.assertRaisesRegex(SchemaError, "pending transaction"):
            ensure_schema(conn)
        self.assertTrue(conn.in_transaction)
        self.assertEqual(conn.execute("SELECT text FROM comments WHERE id=5").fetchone()[0],
                         "pending edit")
        conn.rollback()

    def test_connection_factory_closes_failed_startup_connection(self) -> None:
        conn = self.legacy()
        with patch("managers.db_utils.sqlite3.connect", return_value=conn):
            with self.assertRaises(SchemaError):
                get_db_connection(db_path=self.path, backend="sqlite")
        with self.assertRaises(sqlite3.ProgrammingError):
            conn.execute("SELECT 1")

    def test_explicit_conversion_preserves_every_row_and_existing_schema(self) -> None:
        conn = self.legacy()
        before_rows = rows(conn)
        before_dump = dump(conn)
        recovery = convert_catalog(self.path, backup_dir=self.backups)
        self.assertEqual(rows(conn), before_rows)
        # V4 currently changes only the format marker. Tables and data stay exact.
        self.assertEqual(dump(conn), before_dump)
        self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 4)
        assert recovery is not None
        self.assertEqual(recovery.parent, self.backups)
        backup = self.connect(recovery)
        self.assertEqual(dump(backup), before_dump)
        self.assertEqual(backup.execute("PRAGMA user_version").fetchone()[0], 3)
        ensure_schema(conn)

    def test_existing_accessors_read_preserved_comments_and_presets(self) -> None:
        conn = self.legacy()
        convert_catalog(self.path, backup_dir=self.backups)
        dao = MediaDAO(conn)
        self.assertEqual([row["id"] for row in dao.list_comments(10)], [9, 5])
        self.assertEqual(dao.list_comments(10)[1]["text"], "First line\nSecond line — café 日本語")
        self.assertEqual({row["id"] for row in dao.list_presets_for_media(10)}, {7, 14})
        self.assertEqual({row["id"] for row in dao.list_presets_in_group("shared-group")}, {7, 8})
        preset = dao.list_presets_in_group("legacy-folder-group")[0]
        self.assertIsNone(preset["media_id"])
        self.assertEqual((preset["zoom"], preset["pan_x"], preset["pan_y"]), (0.625, 15, -8))
        self.assertGreater(dao.add_comment(10, "new comment", 10), 80)
        conn.execute("INSERT INTO presets(group_id,name,media_id,zoom,pan_x,pan_y) "
                     "VALUES ('new','New',10,1,0,0)")
        self.assertGreater(conn.execute("SELECT last_insert_rowid()").fetchone()[0], 90)
        conn.commit()

    def test_rerunning_conversion_is_a_noop(self) -> None:
        conn = self.legacy()
        convert_catalog(self.path, backup_dir=self.backups)
        before = dump(conn)
        backups = list(self.backups.iterdir())
        self.assertIsNone(convert_catalog(self.path, backup_dir=self.backups))
        self.assertEqual(dump(conn), before)
        self.assertEqual(list(self.backups.iterdir()), backups)

    def test_earlier_v4_history_is_ignored_and_preserved(self) -> None:
        conn = self.legacy()
        # Test-only fixture of the earlier implementation's optional history.
        conn.executescript("""
            CREATE TABLE schema_migrations(version INTEGER PRIMARY KEY, name TEXT, applied_at TEXT);
            INSERT INTO schema_migrations VALUES(4,'adopt_legacy_catalog','2026-09-20');
            PRAGMA user_version=4;
        """)
        before = dump(conn)
        ensure_schema(conn)
        self.assertIsNone(convert_catalog(self.path, backup_dir=self.backups))
        self.assertEqual(dump(conn), before)
        self.assertFalse(self.backups.exists())

    def test_converter_rejects_unknown_source_versions_without_changes(self) -> None:
        conn = self.legacy()
        for version in (0, 1, 2, 99):
            with self.subTest(version=version):
                conn.execute(f"PRAGMA user_version={version}")
                before = dump(conn)
                with self.assertRaisesRegex(ConversionError, "only converts the known v3"):
                    convert_catalog(self.path, backup_dir=self.backups)
                self.assertEqual(dump(conn), before)
                self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], version)
                self.assertFalse(self.backups.exists())

    def test_failure_rolls_back_ddl_data_and_version_and_retains_backup(self) -> None:
        conn = self.legacy()
        before = dump(conn)
        original_convert = migrations._convert_v3

        def failing_conversion(connection):
            original_convert(connection)
            connection.execute("ALTER TABLE media ADD COLUMN failed_step TEXT")
            connection.execute("UPDATE comments SET text='must roll back' WHERE id=5")
            raise RuntimeError("injected failure")

        with patch.object(migrations, "_convert_v3", failing_conversion):
            with self.assertRaisesRegex(ConversionError, "Recovery copy:"):
                convert_catalog(self.path, backup_dir=self.backups)

        self.assertEqual(dump(conn), before)
        self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 3)
        recovery_files = list(self.backups.glob("*.sqlite3"))
        self.assertEqual(len(recovery_files), 1)
        self.assertEqual(dump(self.connect(recovery_files[0])), before)
        convert_catalog(self.path, backup_dir=self.backups)  # Restart/retry is safe.

    def test_preservation_check_aborts_if_metadata_changes(self) -> None:
        conn = self.legacy()
        before = dump(conn)

        def corrupting_conversion(connection):
            connection.execute("PRAGMA user_version=4")
            connection.execute("UPDATE presets SET zoom=999 WHERE id=7")

        with patch.object(migrations, "_convert_v3", corrupting_conversion):
            with self.assertRaisesRegex(ConversionError, "data changed unexpectedly"):
                convert_catalog(self.path, backup_dir=self.backups)
        self.assertEqual(dump(conn), before)
        self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 3)

    def test_backup_failure_aborts_before_changes(self) -> None:
        conn = self.legacy()
        before = dump(conn)
        self.backups.write_text("not a directory", encoding="utf-8")
        with self.assertRaises(ConversionError):
            convert_catalog(self.path, backup_dir=self.backups)
        self.assertEqual(dump(conn), before)
        self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 3)

    def test_backup_includes_committed_wal_data(self) -> None:
        conn = self.legacy()
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA wal_autocheckpoint=0")
        conn.execute("UPDATE comments SET text='committed in WAL' WHERE id=5")
        conn.commit()
        before = dump(conn)
        recovery = convert_catalog(self.path, backup_dir=self.backups)
        self.assertEqual(dump(self.connect(recovery)), before)

    def test_default_backup_directory_is_beside_explicit_database(self) -> None:
        self.legacy()
        recovery = convert_catalog(self.path)
        assert recovery is not None
        self.assertEqual(recovery.parent, self.root / "backups" / "migrations")

    def test_unknown_metadata_layout_is_not_repaired_or_discarded(self) -> None:
        conn = self.legacy()
        conn.execute("ALTER TABLE presets RENAME COLUMN zoom TO old_custom_zoom")
        before = dump(conn)
        with self.assertRaisesRegex(ConversionError, "presets is missing: zoom"):
            convert_catalog(self.path, backup_dir=self.backups)
        self.assertEqual(dump(conn), before)

    def test_orphaned_metadata_is_not_silently_deleted(self) -> None:
        conn = self.legacy()
        conn.execute("PRAGMA foreign_keys=OFF")
        conn.execute("INSERT INTO comments(media_id,text) VALUES (9999,'keep me')")
        conn.commit()
        before = dump(conn)
        with self.assertRaisesRegex(ConversionError, "broken metadata references"):
            convert_catalog(self.path, backup_dir=self.backups)
        self.assertEqual(dump(conn), before)

    def test_missing_database_path_does_not_create_a_file(self) -> None:
        with self.assertRaises(sqlite3.OperationalError):
            convert_catalog(self.path)
        self.assertFalse(self.path.exists())

    def test_cli_requires_an_explicit_database(self) -> None:
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                migrations.main([])
        self.assertEqual(error.exception.code, 2)
        self.assertFalse(self.path.exists())

    def test_cli_reports_success_and_failure_with_exit_codes(self) -> None:
        conn = self.legacy()
        output = io.StringIO()
        with redirect_stdout(output):
            result = migrations.main(["--database", str(self.path), "--backup-dir", str(self.backups)])
        self.assertEqual(result, 0)
        self.assertIn("Recovery copy:", output.getvalue())
        conn.execute("PRAGMA user_version=99")
        with redirect_stderr(io.StringIO()):
            self.assertEqual(migrations.main(["--database", str(self.path)]), 1)
        self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 99)


if __name__ == "__main__":
    unittest.main()

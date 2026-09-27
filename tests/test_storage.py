from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from managers.dao import MediaDAO
from managers.db_utils import SCHEMA_VERSION, get_db_connection
from managers.undo_manager import UndoEntry, UndoManager
from services.rename_service import RenameService
from utils.config import load_config


class StorageTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.conn = get_db_connection(db_path=self.root / "test.db", backend="sqlite")
        self.dao = MediaDAO(self.conn)

    def tearDown(self) -> None:
        self.conn.close()
        self.temp_dir.cleanup()

    def make_file(self, relative: str, content: bytes = b"image") -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def test_reverse_order_variant_detection(self) -> None:
        variant = self.make_file("gallery/photo_v1.png")
        base = self.make_file("gallery/photo.png")

        variant_id = self.dao.insert_media(str(variant))
        self.dao.detect_and_stack(variant_id, str(variant))
        base_id = self.dao.insert_media(str(base))
        self.dao.detect_and_stack(base_id, str(base))

        self.assertEqual(self.dao.stack_paths(str(base)), [str(base), str(variant)])

    def test_large_subset_is_sorted_globally(self) -> None:
        rows = [
            (str(self.root / f"item-{index}.png"), index, 0, 1000 - index, "image")
            for index in range(905)
        ]
        self.conn.executemany(
            "INSERT INTO media(path, added, is_dir, byte_size, type) VALUES (?,?,?,?,?)",
            rows,
        )
        self.conn.commit()
        subset = [row[0] for row in rows]

        ordered = self.dao.order_subset(subset, "size", True)

        self.assertEqual(ordered, list(reversed(subset)))

    def test_folder_scope_excludes_descendants_and_prefix_siblings(self) -> None:
        direct = self.make_file("Art/direct.png")
        nested = self.make_file("Art/Nested/nested.png")
        sibling = self.make_file("Artwork/sibling.png")
        for path in (direct, nested, sibling):
            self.dao.insert_media(str(path))

        self.assertEqual(self.dao.paths_in_folder(direct.parent), [str(direct)])

    def test_commit_false_participates_in_callers_transaction(self) -> None:
        path = self.make_file("rollback.png")

        with self.assertRaises(RuntimeError):
            with self.conn:
                self.dao.insert_media(str(path), commit=False)
                raise RuntimeError("force rollback")

        self.assertIsNone(
            self.conn.execute("SELECT id FROM media WHERE path=?", (str(path),)).fetchone()
        )

    def test_rename_restores_file_when_database_update_fails(self) -> None:
        old_path = self.make_file("old.png")
        new_path = self.root / "new.png"
        service = RenameService(self.dao, backup_dir=self.root / "overwritten")

        self.assertFalse(service.rename(str(old_path), str(new_path)))
        self.assertTrue(old_path.exists())
        self.assertFalse(new_path.exists())

    def test_overwrite_restores_both_files_when_database_update_fails(self) -> None:
        source = self.make_file("source.png", b"source")
        destination = self.make_file("destination.png", b"destination")
        self.dao.insert_media(str(source))
        self.dao.insert_media(str(destination))
        self.conn.execute(
            """CREATE TRIGGER reject_path_update BEFORE UPDATE OF path ON media
               BEGIN SELECT RAISE(ABORT, 'test failure'); END"""
        )
        self.conn.commit()
        service = RenameService(self.dao, backup_dir=self.root / "overwritten")

        self.assertFalse(service.overwrite(str(source), str(destination)))
        self.assertEqual(source.read_bytes(), b"source")
        self.assertEqual(destination.read_bytes(), b"destination")


class SchemaInitializationTestCase(unittest.TestCase):
    def test_fresh_schema_is_created(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "fresh.db"

            conn = get_db_connection(db_path=db_path, backend="sqlite")
            tables = {
                row[0]
                for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            }
            columns = {row[1] for row in conn.execute("PRAGMA table_info(media)")}
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            conn.close()

            self.assertTrue({"media", "presets", "tags", "comments", "bookmarks", "variants"} <= tables)
            self.assertTrue({"device", "inode", "mtime", "favorite", "type"} <= columns)
            self.assertEqual(version, SCHEMA_VERSION)


class ConfigurationTestCase(unittest.TestCase):
    def test_repository_config_is_valid(self) -> None:
        config = load_config(Path(__file__).resolve().parents[1] / "config.toml")
        self.assertEqual(config.collection_root, Path(r"X:\Collection"))
        self.assertFalse(config.migrate_drive_comments)

    def test_relative_paths_resolve_from_config_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config_path = root / "oculus.toml"
            config_path.write_text(
                """
[paths]
database = "data/catalog.db"
log = "state/oculus.log"
backup_dir = "state/backups"
operation_backup_dir = "state/operations"
collection_root = "media"

[maintenance]
backup_on_startup = false
migrate_drive_comments = true
""",
                encoding="utf-8",
            )

            config = load_config(config_path)

            self.assertEqual(config.database_path, root / "data/catalog.db")
            self.assertEqual(config.collection_root, root / "media")
            self.assertFalse(config.backup_on_startup)
            self.assertTrue(config.migrate_drive_comments)

    def test_failed_undo_remains_available(self) -> None:
        class FailingRenameService:
            @staticmethod
            def undo(_entry):
                return False

        with tempfile.TemporaryDirectory() as temp_dir:
            undo = UndoManager(log_path=Path(temp_dir) / "undo.json")
            undo.set_rename_service(FailingRenameService())
            undo.push(UndoEntry("old", "new"))

            self.assertFalse(undo.undo_last())
            self.assertTrue(undo.can_undo())


if __name__ == "__main__":
    unittest.main()

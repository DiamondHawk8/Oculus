"""
Usage (CLI)
$ python -m tests.perf_scan ./sample_sets/large

Outputs (example)
Scanned 1,000 files in 3.42 s  →  292.4 files/s
"""
from __future__ import annotations

import argparse
import sys
import tempfile
import time
from pathlib import Path

from PySide6.QtWidgets import QApplication

from managers.media_manager import MediaManager
from managers.db_utils import get_db_connection
from managers.undo_manager import UndoManager

# ensure project root is on sys.path so the import works when running via -m
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))




def _parse_cli() -> Path:
    p = argparse.ArgumentParser(description="Benchmark MediaManager.scan_folder")
    p.add_argument("folder", type=Path, help="Path containing images to scan")
    args = p.parse_args()
    folder = args.folder.expanduser().resolve()
    if not folder.is_dir():
        p.error(f"folder '{folder}' is not a directory")
    return folder


def main() -> None:
    folder = _parse_cli()
    app = QApplication([])

    temp_dir = tempfile.TemporaryDirectory()
    temp_root = Path(temp_dir.name)
    conn = get_db_connection(db_path=temp_root / "perf.db", backend="sqlite")
    undo = UndoManager(log_path=temp_root / "rename_log.json")
    mm = MediaManager(conn, undo, operation_backup_dir=temp_root / "overwritten")
    t0 = time.perf_counter()

    def _done(summary):
        dt = time.perf_counter() - t0
        total: int = summary.added + summary.skipped
        per_s = total / dt if dt else 0.0
        print(f"\nScanned {total:,} files in {dt:.2f} s  :  {per_s:.1f} files/s")
        conn.close()
        temp_dir.cleanup()
        app.quit()

    mm.import_finished.connect(_done)
    mm.scan_folder(folder)
    app.exec()


if __name__ == "__main__":
    main()

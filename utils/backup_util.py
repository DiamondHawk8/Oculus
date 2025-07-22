import datetime
import gzip
import json
import logging
import os
import pathlib
import sqlite3

logger = logging.getLogger(__name__)

BACKUP_DIR = pathlib.Path("backups")
BACKUP_DIR.mkdir(exist_ok=True)
MAX_BACKUPS = 100  # keep latest N files
COMPRESS = True  # gzip the JSON to save space


def export_db_to_json(conn: sqlite3.Connection) -> pathlib.Path:
    """
    Dump every user table in conn to a single JSON object and write it to
    backups/db_YYYYMMDD_HHMMSS.json(.gz). Returns the path.
    """
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"db_{ts}.json"
    out = BACKUP_DIR / (name + (".gz" if COMPRESS else ""))

    cur = conn.cursor()
    tables = [
        r[0] for r in cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    ]
    dump: dict[str, list[dict]] = {}

    for tbl in tables:
        rows = cur.execute(f"SELECT * FROM {tbl}").fetchall()
        cols = [d[0] for d in cur.description]
        dump[tbl] = [dict(zip(cols, row)) for row in rows]

    raw = json.dumps(dump, indent=2, ensure_ascii=False)

    if COMPRESS:
        with gzip.open(out, "wt", encoding="utf-8") as fp:
            fp.write(raw)
    else:
        out.write_text(raw, encoding="utf-8")

    logger.info("Database exported to %s", out)
    _prune_old_backups()
    return out


def _prune_old_backups():
    files = sorted(BACKUP_DIR.glob("db_*.json*"), key=os.path.getmtime, reverse=True)
    for f in files[MAX_BACKUPS:]:
        f.unlink(missing_ok=True)

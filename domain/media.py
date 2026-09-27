"""Small shared rules for media discovery"""

import os
import re
from pathlib import Path

VIDEO_EXTENSIONS = frozenset({".mp4", ".mkv", ".webm", ".mov", ".avi"})
MEDIA_EXTENSIONS = VIDEO_EXTENSIONS | {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}
_VARIANT = re.compile(r"^(.*)_v(\d+)$", re.IGNORECASE)


def file_identity(st: os.stat_result) -> tuple[str, str]:
    # Tagged strings preserve Windows file IDs better than SQLite INTEGER
    return f"d:{st.st_dev}", f"i:{st.st_ino}"


def media_kind(path: Path, is_dir: bool) -> str:
    if is_dir:
        return "dir"
    if path.suffix.lower() in VIDEO_EXTENSIONS:
        return "video"
    if path.suffix.lower() == ".gif":
        return "gif"
    else:
        return "image"



def variant_key(path: Path) -> tuple[str, int | None]:
    match = _VARIANT.match(path.stem)
    if match:
        stem, digits = match.groups()
        # Unusual filenames must not overflow SQLite integers or Python's
        # integer-string limit and abort an otherwise valid import.
        if len(digits) <= 19 and int(digits) <= 2**63 - 1:
            return (stem + path.suffix).casefold(), int(digits)
    return path.name.casefold(), None

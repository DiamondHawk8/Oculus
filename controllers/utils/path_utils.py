import os
import re
from pathlib import Path
from typing import List, Tuple

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".mp4", ".mkv", ".mov", ".avi"}



def natural_key(path: str):
    """
    Split basename into text / int chunks so 2 < 10.
    """
    name = os.path.basename(path).lower()
    return [int(tok) if tok.isdigit() else tok
            for tok in re.split(r'(\d+)', name)]


def list_subdirs(folder: str | Path) -> List[str]:
    """
    Return absolute paths of immediate sub-folders (no files).
    :param folder:
    :return:
    """
    return [str(p) for p in Path(folder).iterdir() if p.is_dir()]


def list_images(folder: str | Path) -> List[str]:
    """
    Return absolute paths of image files in that folder (non-recursive).
    :param folder:
    :return:
    """
    return [
        str(p) for p in Path(folder).iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXT
    ]


def split_dirs_files(paths: List[str]) -> Tuple[List[str], List[str]]:
    """
    Split an arbitrary path list into (dirs, files).
    :param paths:
    :return:
    """
    dirs = [p for p in paths if Path(p).is_dir()]
    files = [p for p in paths if Path(p).is_file()]
    return dirs, files

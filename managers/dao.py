from __future__ import annotations
import os, time, uuid
from pathlib import Path
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}

class MediaDAO:
    """
    Pure synchronous DB helper, no QT/Pyside
    """

    def __init__(self, conn):
        self.conn = conn
        self.cur = conn.cursor()
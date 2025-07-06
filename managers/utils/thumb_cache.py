from collections import OrderedDict
from PySide6.QtGui import QPixmap

class ThumbCache:
    """
    In-memory LRU cache keyed by (path, size).
    """
    def __init__(self, capacity: int = 512):
        self.capacity = capacity
        self._cache: OrderedDict[tuple[str, int], QPixmap] = OrderedDict()

    # ------------------------------------------------------
    def get(self, path: str, size: int) -> QPixmap | None:
        key = (path, size)
        pix = self._cache.get(key)
        if pix is not None:
            self._cache.move_to_end(key)  # mark as recently used
        return pix

    def set(self, path: str, size: int, pix: QPixmap):
        key = (path, size)
        self._cache[key] = pix
        self._cache.move_to_end(key)
        if len(self._cache) > self.capacity:
            self._cache.popitem(last=False)  # evict oldest

    def replace_capacity(self, capacity: int):
        self.capacity = capacity
        while len(self._cache) > self.capacity:
            self._cache.popitem(last=False)

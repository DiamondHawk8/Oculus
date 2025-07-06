from pathlib import Path
from managers.dao import MediaDAO

class VariantService:
    """
    Filename‐based auto-stacking and look-ups.
    """

    def __init__(self, dao: MediaDAO):
        self.dao = dao

    def detect_and_stack(self, media_id: int, path: str):
        self.dao.detect_and_stack(media_id, path)

    def is_variant(self, path: str) -> bool:
        return self.dao.is_variant(path)

    def is_stacked_base(self, media_id: int) -> bool:
        return self.dao.is_stacked_base(media_id)

    def stack_paths(self, path: str) -> list[str]:
        return self.dao.stack_paths(path)

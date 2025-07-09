from pathlib import Path

from PySide6.QtCore import QObject, Signal


class MetadataBackend:
    """
    Helper for DB operations related to the metadata backend.
    """
    def __init__(self, media_manager):
        self._media = media_manager

    def id_for_path(self, path: str) -> int:
        mid = self._media.get_media_id(path)
        return mid if mid is not None else -1

    def ids_with_variants(self, path: str, include: bool) -> list[int]:
        paths = (self._media.stack_paths(path) if include else [path])
        return [self.id_for_path(p) for p in paths]

    def target_media_ids(self, paths: list[str], scope: str, include_variants: bool) -> list[int]:
        """
        Return the list of media_ids to operate on, based on the selected scope
        radio button and the 'apply to variants' checkbox.
        :return:
        """
        ids: list[int] = []
        if scope == "this":
            ids.extend(self.ids_with_variants(paths[0], include_variants))

        elif scope == "selected":
            for p in paths:
                ids.extend(self.ids_with_variants(p, include_variants))

        elif scope == "folder":
            folder = str(Path(paths[0]).parent)
            rows = self._media.dao.fetchall(
                "SELECT path FROM media WHERE path LIKE ?", (f"{folder}%",)
            )
            for r in rows:
                path = r["path"]
                if include_variants:
                    ids.extend(self.ids_with_variants(path, True))
                else:
                    if not self._media.is_variant(path):
                        ids.append(self.id_for_path(path))
        # dedupe keep-order
        return list(dict.fromkeys(ids))

from dataclasses import dataclass, field
from typing import Dict, Set

from widgets.media_renderer import MediaViewerDialog
from PySide6.QtCore import Qt
from pathlib import Path

import logging

logger = logging.getLogger(__name__)


@dataclass
class GalleryState:
    current_folder: str | None = None
    expanded_bases: Set[str] = field(default_factory=set)
    row_map: Dict[str, int] = field(default_factory=dict)

    def is_expanded(self, base: str) -> bool:
        return base in self.expanded_bases


class ViewerState:
    def __init__(self):
        self.dialog: MediaViewerDialog | None = None
        self.callback = None
        self.is_open = False

    def open(self, model, index, media_manager, tag_manager, host_widget):
        logger.debug(f"Opening viewer state for model {model}")
        path = model.data(index, Qt.UserRole)
        if not path or not Path(path).is_file():
            return

        stack = media_manager.stack_paths(path)
        paths = [p for p in model.get_paths() if Path(p).is_file()]
        cur_idx = paths.index(path)

        self.dialog = MediaViewerDialog(paths, cur_idx, media_manager, tag_manager, stack, parent=host_widget)
        self.is_open = True
        self.dialog.finished.connect(self._on_closed)
        self.dialog.exec()

    def _on_closed(self, *_):
        self.is_open = False
        self.dialog = None

    def open_via_callback(self, nav_paths, cur_idx, stack, selected,
                          host_widget, media_manager, tag_manager):
        """
        Route the request to the callback injected by TabController,
        so each tab owns one persistent viewer managed by TabController.
        """
        if callable(self.callback):
            self.callback(nav_paths, cur_idx, stack)
        else:
            dlg = MediaViewerDialog(
                nav_paths, cur_idx,
                media_manager, tag_manager,
                stack, selected_path=selected,
                parent=host_widget
            )
            dlg.finished.connect(self._on_closed)
            self.dialog = dlg
            self.is_open = True

    def open_paths(self, nav_paths, cur_idx, stack, selected,
                   media_manager, tag_manager, host_widget):
        dlg = MediaViewerDialog(
            nav_paths, cur_idx, media_manager, tag_manager,
            stack, selected_path=selected, parent=host_widget
        )
        self.dialog = dlg
        self.is_open = True
        dlg.finished.connect(self._on_closed)

import argparse
import sys
import logging
import importlib
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt, QEvent

import utils.backup_util

from ui.custom_grips import CustomGrip
from ui.ui_main import Ui_MainWindow

from managers.media_manager import MediaManager
from managers.search_manager import SearchManager
from managers.tag_manager import TagManager
from managers.keybind_manager import KeybindManager
from managers.db_utils import ensure_schema, get_db_connection
from managers.undo_manager import UndoManager

from controllers.gallery_controller import GalleryController
from controllers.import_controller import ImportController
from controllers.search_controller import SearchController
from controllers.tab_controller import TabController

from utils.config import AppConfig, load_config

logger = logging.getLogger(__name__)

ACTIVE_BACKEND = "sqlite"

GALLERY_PAGE_INDEX = 0
WIDGET_PAGE_INDEX = 1
IMPORT_PAGE_INDEX = 2
SEARCH_PAGE_INDEX = 3

class MainWindow(QMainWindow):

    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config

        self.setup_window()

        self.conn = get_db_connection(
            db_path=config.database_path,
            backend=ACTIVE_BACKEND,
            initialize_schema=False,
        )
        if config.backup_on_startup:
            # Capture the pre-migration state so schema upgrades remain
            utils.backup_util.export_db_to_json(self.conn, config.backup_dir)
            logger.info("Pre-migration database backup saved")
        else:
            logger.info("Startup database backup disabled")
        ensure_schema(self.conn)
        self.conn.execute("PRAGMA journal_mode=WAL")
        logger.info("Connected to database")

        # backend managers
        self.undo = UndoManager(log_path=config.operation_backup_dir / "rename_log.json")
        self.media = MediaManager(
            self.conn,
            self.undo,
            operation_backup_dir=config.operation_backup_dir / "overwritten",
            parent=self,
        )
        self.tags = TagManager(self.conn)
        self.search = SearchManager(self.conn, self.tags)
        logger.debug("Main managers instantiated")

        self._run_optional_comment_migration()

        # Other Managers
        self.keybinds = KeybindManager(self)

        # Logic Controllers
        self.tab_controller = TabController(self.ui.galleryTabs, self.media, self.tags, self.keybinds)
        self.gallery_controller = GalleryController(self.ui, self.media, self.tags, self.tab_controller,
                                                    self.ui.gallery_page)

        self.search_controller = SearchController(self.ui, self.media, self.tags, self.search, self.tab_controller,
                                                  self.ui.search_page, self.gallery_controller)
        self.import_controller = ImportController(self, self.ui, self.media, self.tags, self.gallery_controller)
        logger.debug("Controllers instantiated")

        # Connect window buttons
        self.ui.closeAppBtn.clicked.connect(self.close)
        self.ui.minimizeAppBtn.clicked.connect(self.showMinimized)

        roots = self.media.root_folders()
        if roots:
            # Prefer the configured collection path, but fall back to a DB
            # root when the drive is unavailable (for example on another PC).
            configured_root = config.collection_root
            root_path = configured_root if configured_root and configured_root.is_dir() else roots[-1]
            self.gallery_controller.open_folder(str(root_path))
        else:
            self.gallery_controller.populate_gallery([])  # empty state

        def _toggle_max_restore():
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()

        self.ui.maximizeRestoreAppBtn.clicked.connect(_toggle_max_restore)

        # Register global keybinds
        self.keybinds.register("Ctrl+Z", lambda: self.undo.undo_last())

        # Connect page buttons
        self.ui.btn_home.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(GALLERY_PAGE_INDEX))
        self.ui.btn_adv.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(WIDGET_PAGE_INDEX))
        self.ui.btn_import.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(IMPORT_PAGE_INDEX))
        self.ui.btn_search.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(SEARCH_PAGE_INDEX))
        logger.info("Main window setup complete")

    def _run_optional_comment_migration(self) -> None:
        if not self.config.migrate_drive_comments:
            return
        if not self.config.migration_root:
            logger.warning("Comment migration enabled without a migration_root")
            return

        # The migration utility is intentionally optional and may be absent

        try:
            migration_module = importlib.import_module("utils.migrate_drive_comments")
        except ModuleNotFoundError:
            logger.warning("Comment migration requested, but its utility is unavailable")
            return
        migration_module.migrate(
            self.config.migration_root,
            conn=self.conn,
            backup_root=self.config.backup_dir / "drive_comments",
        )

    def setup_window(self) -> None:

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        # Make borderless
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Create grips for window
        self._grips = [
            CustomGrip(self, Qt.LeftEdge, disable_color=True),
            CustomGrip(self, Qt.RightEdge, disable_color=True),
            CustomGrip(self, Qt.TopEdge, disable_color=True),
            CustomGrip(self, Qt.BottomEdge, disable_color=True),
        ]

        # Enable mouse tracking + install event filter
        self._drag_pos = None
        self.ui.contentTopBg.setMouseTracking(True)
        self.ui.contentTopBg.installEventFilter(self)

        logger.info("Main window setup")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        g = 10
        w, h = self.width(), self.height()

        self._grips[0].setGeometry(0, g, g, h - 2 * g)
        self._grips[1].setGeometry(w - g, g, g, h - 2 * g)
        self._grips[2].setGeometry(0, 0, w, g)
        self._grips[3].setGeometry(0, h - g, w, g)

    def eventFilter(self, obj, event):
        if obj == self.ui.contentTopBg:
            if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.LeftButton:
                self._drag_pos = event.globalPosition().toPoint()
                return True

            elif event.type() == QEvent.Type.MouseMove and self._drag_pos:
                delta = event.globalPosition().toPoint() - self._drag_pos
                self.move(self.pos() + delta)
                self._drag_pos = event.globalPosition().toPoint()
                return True

            elif event.type() == QEvent.Type.MouseButtonRelease:
                self._drag_pos = None
                return True

        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        # Explicit closure keeps WAL/checkpoint lifecycle tied to the window.
        self.conn.close()
        super().closeEvent(event)


def parse_cli():
    p = argparse.ArgumentParser(description="Oculus Image Viewer")
    p.add_argument("--open-folder", help="Open with this folder selected")
    p.add_argument("--open-file", help="Open viewer directly on this file")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_cli()
    app_config = load_config()
    app_config.log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=app_config.log_path, level=logging.DEBUG)
    app = QApplication(sys.argv)
    win = MainWindow(app_config)

    # honor CLI flags
    if args.open_folder:
        win.gallery_controller.open_folder(args.open_folder)
    elif args.open_file:
        win.gallery_controller.open_folder(str(Path(args.open_file).parent))
        idx = win.gallery_controller.state.row_map.get(args.open_file)
        if idx is not None:
            win.gallery_controller._open_viewer(
                win.gallery_controller._model.index(idx)
            )

    win.show()
    sys.exit(app.exec())

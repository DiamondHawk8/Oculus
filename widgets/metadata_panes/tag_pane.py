from PySide6.QtCore import Signal, Qt, QStringListModel, QObject
from PySide6.QtWidgets import QWidget, QCompleter, QLineEdit, QListWidget, QMessageBox


class TagPane(QObject):
    """
    Pure controller for the tag tab. Operates on widgets provided by the dialog.
    """
    tagsChanged = Signal()

    def __init__(
            self,
            list_tags: QListWidget,
            list_pending: QListWidget,
            edit_tag: QLineEdit,
            btn_add,
            btn_remove,
            btn_copy,
            btn_paste,
            tag_manager,
            copy_buffer: list[str],
            parent=None,
    ):
        super().__init__(parent)
        self._tags = tag_manager
        self._buf = copy_buffer

        # widget refs
        self.listTags = list_tags
        self.listPending = list_pending
        self.editTag = edit_tag

        # completer
        self.editTag.setCompleter(
            QCompleter(QStringListModel(self._tags.distinct_tags()), self.editTag)
        )

        # wire buttons
        btn_add.clicked.connect(self._add_pending)
        btn_remove.clicked.connect(self._remove_pending)
        btn_copy.clicked.connect(self._copy_tags)
        btn_paste.clicked.connect(self._paste_tags)

    # ---------- public API ---------- #
    def load(self, media_id: int):
        self.listTags.clear()
        for t in self._tags.get_tags(media_id):
            self.listTags.addItem(t)

    def save(self, target_ids: list[int], replace_mode: bool):
        if not target_ids:
            return
        pending = {self.listPending.item(i).text().strip().lower()
                   for i in range(self.listPending.count())}
        if not pending or not target_ids:
            return
        for mid in target_ids:
            current = set(self._tags.get_tags(mid))
            if replace_mode:
                to_remove = pending & current
                if to_remove:
                    self._tags.delete_tags(mid, to_remove)
            else:
                to_add = pending - current
                if to_add:
                    self._tags.set_tags(mid, to_add, overwrite=False)
        self.tagsChanged.emit()

    # ---------- internal slots ---------- #
    def _add_pending(self):
        tag = self.editTag.text().strip().lower()
        if tag and not self.listPending.findItems(tag, Qt.MatchFixedString):
            self.listPending.addItem(tag)
            self.editTag.clear()

    def _remove_pending(self):
        for itm in self.listPending.selectedItems():
            self.listPending.takeItem(self.listPending.row(itm))

    def _copy_tags(self):
        src = self.listPending if self.listPending.hasFocus() else self.listTags
        self._buf = [src.item(i).text() for i in range(src.count())]

    def _paste_tags(self):
        if not self._buf:
            return
        existing = {self.listPending.item(i).text()
                    for i in range(self.listPending.count())}
        for t in self._buf:
            if t not in existing:
                self.listPending.addItem(t)

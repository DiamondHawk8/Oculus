from PySide6.QtCore import Qt, QDateTime
from PySide6.QtWidgets import QListWidgetItem
from ui.ui_comment_panel import Ui_CommentPanel


class CommentPanel(Ui_CommentPanel):
    def __init__(self, comment_service, media_id, parent=None):
        super().__init__()
        self.setupUi(parent or self)
        self._svc = comment_service
        self._mid = media_id

        self.btnAdd.clicked.connect(self._add)
        self.reload()

    def setMedia(self, media_id):
        self._mid = media_id
        self.reload()

    def reload(self):
        self.listComments.clear()
        for c in self._svc.dao.list_comments(self._mid):
            ts = QDateTime.fromString(c["created"], Qt.ISODate).toString("yyyy-MM-dd hh:mm")
            item = QListWidgetItem(f"[{ts}]  {c['text']}")
            self.listComments.addItem(item)

    def _add(self):
        txt = self.editComment.toPlainText().strip()
        if not txt:
            return
        self._svc.add(self._mid, txt)
        self.editComment.clear()
        self.reload()

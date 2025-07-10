from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QMessageBox
from ui.ui_comments_panel import Ui_CommentsPanel
from widgets.comment_widget import CommentWidget


class CommentsPanel(QWidget):
    panelClosed = Signal()

    def __init__(self, comment_service, parent=None):
        super().__init__(parent)
        self.ui = Ui_CommentsPanel()
        self.ui.setupUi(self)
        self._svc = comment_service
        self._media_id = None

        # Signals from service
        self._svc.commentAdded.connect(self._on_added)
        self._svc.commentDeleted.connect(self._on_deleted)

        # Post button / Return key
        self.ui.btnPost.clicked.connect(self._post_comment)
        self.ui.editComment.returnPressed.connect(self._post_comment)

    def load_comments(self, media_id: int):
        """
        Fill the panel with comments for media_id.
        :param media_id:
        :return:
        """
        self._media_id = media_id
        self._clear_thread()
        for c in self._svc.list_comments(media_id):
            self._add_comment_widget(c)

    # ---------- service callbacks ---------- #
    def _on_added(self, media_id: int, comment_row: dict):
        if media_id == self._media_id:
            self._add_comment_widget(comment_row)

    def _on_deleted(self, media_id: int, comment_id: int):
        if media_id != self._media_id:
            return

        # scan children for matching widget
        lay = self.ui.commentsContainer.layout()
        for i in reversed(range(lay.count())):
            w = lay.itemAt(i).widget()
            if isinstance(w, CommentWidget) and w.comment_id == comment_id:
                w.setParent(None)
                break

    # ---------- local helpers ---------- #
    def _add_comment_widget(self, row: dict):
        w = CommentWidget(row["id"], "Me", row["text"], row["created"])
        w.deleteClicked.connect(self._svc.delete_comment)
        self.ui.commentsContainer.layout().insertWidget(0, w)

    def _clear_thread(self):
        lay = self.ui.commentsContainer.layout()
        while lay.count():
            child = lay.takeAt(0).widget()
            if child:
                child.setParent(None)

    def _post_comment(self):
        txt = self.ui.editComment.text().strip()
        if not txt:
            return
        if self._media_id is None:
            QMessageBox.warning(self, "No media", "No file selected.")
            return
        self._svc.add_comment(self._media_id, txt)
        self.ui.editComment.clear()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.hide()
            self.panelClosed.emit()
        else:
            super().keyPressEvent(e)

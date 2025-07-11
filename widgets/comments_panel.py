from PySide6.QtCore import Signal, Qt, QEvent, QSettings
from PySide6.QtWidgets import QWidget, QMessageBox, QSizePolicy, QCheckBox
from ui.ui_comments_panel import Ui_CommentsPanel
from widgets.comment_widget import CommentWidget


class CommentsPanel(QWidget):
    panelClosed = Signal()
    editingBegan = Signal()
    editingEnded = Signal()

    def __init__(self, comment_service, parent=None):
        super().__init__(parent)
        self.ui = Ui_CommentsPanel()
        self.ui.setupUi(self)
        self._settings = QSettings("Oculus", "ImageViewer")

        self.setAutoFillBackground(True)
        self.setStyleSheet("background:#222; color:#eee;")

        self._svc = comment_service
        self._media_id = None

        # Signals from service
        self._svc.commentAdded.connect(self._on_added)
        self._svc.commentDeleted.connect(self._on_deleted)
        self._svc.commentEdited.connect(self._on_edited)

        # Post button / Return key
        self.ui.btnPost.clicked.connect(self._post_comment)
        self.ui.editComment.installEventFilter(self)

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
        w.deleteClicked.connect(self._confirm_delete)
        w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        w.editSaved.connect(self._on_local_edit)
        self.ui.commentsContainer.layout().addWidget(w, 0, Qt.AlignTop)

    def _confirm_delete(self, cid: int):
        if self._settings.value("skipDeleteConfirm", False, bool):
            self._svc.delete_comment(cid)
            return

        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle("Delete comment")
        box.setText("Delete this comment?")
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        chk = QCheckBox("Don't ask again", box)
        box.setCheckBox(chk)

        if box.exec() == QMessageBox.Yes:
            if chk.isChecked():
                self._settings.setValue("skipDeleteConfirm", True)
            self._svc.delete_comment(cid)

    def _clear_thread(self):
        lay = self.ui.commentsContainer.layout()
        while lay.count():
            child = lay.takeAt(0).widget()
            if child:
                child.setParent(None)

    def _post_comment(self):

        txt = self.ui.editComment.toPlainText().strip()
        clear_fn = self.ui.editComment.clear

        if not txt:
            return
        if self._media_id is None:
            QMessageBox.warning(self, "No media", "No file selected.")
            return

        self._svc.add_comment(self._media_id, txt)
        clear_fn()

    def _on_local_edit(self, cid: int, new_text: str):
        self._svc.edit_comment(cid, new_text)

    def _on_edited(self, media_id: int, row: dict):
        if media_id != self._media_id:
            return
        lay = self.ui.commentsContainer.layout()
        for i in range(lay.count()):
            w = lay.itemAt(i).widget()
            if isinstance(w, CommentWidget) and w.comment_id == row["id"]:
                w.refresh_text(row["text"])  # new helper on widget
                break

    def set_input_visible(self, visible: bool):
        self.ui.editComment.setVisible(visible)
        self.ui.btnPost.setVisible(visible)

    def toggle_input(self):
        self.editingEnded.emit()
        self.set_input_visible(not self.ui.editComment.isVisible())

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.hide()
            e.accept()
            self.editingEnded.emit()
            return
        super().keyPressEvent(e)

    def eventFilter(self, obj, ev):
        if obj is getattr(self, "_editor", None):
            if ev.type() == QEvent.FocusOut:
                self.editingEnded.emit()
        if obj is self.ui.editComment and ev.type() == QEvent.KeyPress:
            if ev.key() in (Qt.Key_Return, Qt.Key_Enter) and ev.modifiers() & Qt.ControlModifier:
                self._post_comment()
                return True
        return super().eventFilter(obj, ev)

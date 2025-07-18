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
        self._skip_next_reorder = False
        self._media_id = None
        self._active_editor = None

        # Allow for dragging of comment widgets
        self.ui.commentsContainer.setAcceptDrops(True)
        self.ui.commentsContainer.installEventFilter(self)

        # Signals from service
        self._svc.commentAdded.connect(self._on_added)
        self._svc.commentDeleted.connect(self._on_deleted)
        self._svc.commentEdited.connect(self._on_edited)
        self._svc.commentReordered.connect(self._on_reordered)

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

    def _on_reordered(self, media_id: int):
        if media_id != self._media_id:
            return
        if self._skip_next_reorder:  # ignore the echo from local drag
            self._skip_next_reorder = False
            return
        self.load_comments(media_id)  # refresh for changes from other panels

    # ---------- local helpers ---------- #
    def _add_comment_widget(self, row: dict):
        w = CommentWidget(row["id"], "Me", row["text"], row["created"])
        w.deleteClicked.connect(self._confirm_delete)
        w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        w.editSaved.connect(self._on_local_edit)
        w.editingBegan.connect(lambda w=w: self._on_edit_started(w))
        w.editingEnded.connect(lambda w=w: self._on_edit_ended(w))
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

    def _on_edit_started(self, widget):
        if self._active_editor and self._active_editor is not widget:
            # cancel previous editor without saving
            self._active_editor.cancel_edit(save=False)
        self._active_editor = widget
        self.editingBegan.emit()

    def _on_edit_ended(self, widget):
        if widget is self._active_editor:
            self._active_editor = None
        self.editingEnded.emit()

    def set_input_visible(self, visible: bool):
        self.ui.editComment.setVisible(visible)
        self.ui.btnPost.setVisible(visible)

    def toggle_input(self):
        self.editingEnded.emit()
        self.set_input_visible(not self.ui.editComment.isVisible())

    def _reorder_comment_widget(self, comment_id, drop_pos):
        lay = self.ui.commentsContainer.layout()
        w = None
        # Find dragged widget
        dragged = None
        for i in range(lay.count()):
            w = lay.itemAt(i).widget()
            if isinstance(w, CommentWidget) and w.comment_id == comment_id:
                dragged = w
                break
        if not dragged:
            return

        # Remove and reinsert at correct position
        lay.removeWidget(dragged)

        insert_idx = 0
        for i in range(lay.count()):
            w = lay.itemAt(i).widget()
            if drop_pos.y() < w.y():
                break
            insert_idx += 1

        lay.insertWidget(insert_idx, dragged, 0, Qt.AlignTop)
        # build new order list
        new_ids = [
            lay.itemAt(i).widget().comment_id
            for i in range(lay.count())
            if isinstance(lay.itemAt(i).widget(), CommentWidget)
        ]

        self._skip_next_reorder = True  # suppress self-refresh
        self._svc.set_order(self._media_id, new_ids)
        lay.update()

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
        if obj is self.ui.commentsContainer:
            if ev.type() == QEvent.DragEnter:
                ev.accept()
                return True
        if ev.type() == QEvent.Drop:
            comment_id = int(ev.mimeData().text())
            self._reorder_comment_widget(comment_id, ev.pos())
            return True
        return super().eventFilter(obj, ev)

from PySide6.QtCore import Signal, Qt, QEvent
from PySide6.QtGui import QTextOption
from PySide6.QtWidgets import QWidget, QSizePolicy, QPlainTextEdit, QToolButton, QHBoxLayout
from ui.ui_comment_widget import Ui_CommentWidget


class CommentWidget(QWidget):
    deleteClicked = Signal(int)
    editSaved = Signal(int, str)  # id, new_text
    editingBegan = Signal()
    editingEnded = Signal()

    def __init__(self, cid, author, text, ts, parent=None):
        super().__init__(parent)
        self.ui = Ui_CommentWidget()
        self.ui.setupUi(self)
        self.comment_id = cid
        self._orig_text = text

        self.ui.labelAuthor.setText(f"<b>{author}</b>")
        self.ui.labelText.setText(text)
        self.ui.labelTime.setText(f"<i>{ts}</i>")

        # --- edit controls ---
        self.ui.btnEdit.clicked.connect(self._enter_edit)
        self.ui.btnDelete.clicked.connect(lambda: self.deleteClicked.emit(cid))

    def _enter_edit(self):
        if hasattr(self, "_editor"):  # already in edit mode → ignore
            return
        self.editingBegan.emit()

        self._editor = QPlainTextEdit(self._orig_text, self)
        self._editor.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self._editor.setMinimumHeight(60)
        self._editor.setStyleSheet("background:#444; color:#eee; border:none;")

        btnSave = QToolButton(self)
        btnSave.setText("✔︎")
        btnCancel = QToolButton(self)
        btnCancel.setText("✕")

        row = QHBoxLayout()
        row.addWidget(btnSave)
        row.addWidget(btnCancel)
        row.addStretch()

        v = self.layout()  # root QVBoxLayout from .ui
        v.removeWidget(self.ui.labelText)
        self.ui.labelText.hide()
        v.addWidget(self._editor)
        v.addLayout(row)

        btnSave.clicked.connect(lambda: self._finish_edit(save=True))
        btnCancel.clicked.connect(lambda: self._finish_edit(save=False))

    def _finish_edit(self, save: bool):
        if not hasattr(self, "_editor"):
            return
        new_text = self._editor.toPlainText().strip()

        lay = self.layout()
        lay.removeWidget(self._editor)

        self._editor.setParent(None)
        for w in [btn for btn in self.findChildren(QToolButton) if btn.text() in {"✔︎", "✕"}]:
            lay.removeWidget(w)
            w.setParent(None)

        self.ui.labelText.show()
        if save and new_text and new_text != self._orig_text:
            self._orig_text = new_text
            self.ui.labelText.setText(new_text)
            self.editSaved.emit(self.comment_id, new_text)

        del self._editor
        self.editingEnded.emit()

    def eventFilter(self, obj, ev):
        if obj is getattr(self, "_editor", None) and ev.type() == QEvent.FocusOut:
            self.editingEnded.emit()
        return super().eventFilter(obj, ev)

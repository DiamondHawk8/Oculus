from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget
from ui.ui_comment_widget import Ui_CommentWidget


class CommentWidget(QWidget):
    deleteClicked = Signal(int)

    def __init__(self, comment_id: int, author: str, text: str, ts: str, parent=None):
        super().__init__(parent)
        self.ui = Ui_CommentWidget()
        self.ui.setupUi(self)

        self.comment_id = comment_id
        self.ui.labelAuthor.setText(f"<b>{author}</b>")
        self.ui.labelText.setText(text)
        self.ui.labelTime.setText(f"<i>{ts}</i>")

        self.ui.btnDelete.clicked.connect(lambda: self.deleteClicked.emit(comment_id))

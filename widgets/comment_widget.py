from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QSizePolicy
from ui.ui_comment_widget import Ui_CommentWidget


class CommentWidget(QWidget):
    deleteClicked = Signal(int)

    def __init__(self, comment_id: int, author: str, text: str, ts: str, parent=None):
        super().__init__(parent)
        self.ui = Ui_CommentWidget()
        self.ui.setupUi(self)

        self.ui.labelText.setWordWrap(True)
        self.ui.labelText.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.ui.labelText.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.comment_id = comment_id
        self.ui.labelAuthor.setText(f"<b>{author}</b>")
        self.ui.labelText.setText(text)
        self.ui.labelTime.setText(f"<i>{ts}</i>")

        self.ui.btnDelete.clicked.connect(lambda: self.deleteClicked.emit(comment_id))

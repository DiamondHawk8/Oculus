from PySide6.QtCore import Signal, QObject

from managers.dao import MediaDAO


class CommentService(QObject):
    commentAdded = Signal(int, dict)
    commentDeleted = Signal(int, int)

    def __init__(self, dao: MediaDAO, parent=None):
        super().__init__(parent)
        self.dao = dao

    def add_comment(self, media_id: int, text: str):
        cid = self.dao.add_comment(media_id, text)
        row = {"id": cid, "text": text, "created": "now"}   # or fetch full row
        self.commentAdded.emit(media_id, row)
        return cid

    def delete_comment(self, comment_id: int):
        row = self.dao.fetchone("SELECT media_id FROM comments WHERE id=?", (comment_id,))
        if row:
            self.dao.delete_comment(comment_id)
            self.commentDeleted.emit(row["media_id"], comment_id)

    def list_comments(self, media_id: int) -> list[dict]:
        return self.dao.list_comments(media_id)

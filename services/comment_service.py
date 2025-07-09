from PySide6.QtCore import Signal, QObject

from managers.dao import MediaDAO


class CommentService(QObject):
    comment_added = Signal(int)
    comment_deleted = Signal(int)

    def __init__(self, dao: MediaDAO, parent=None):
        super().__init__(parent)
        self.dao = dao

    def add(self, media_id: int, text: str):
        cid = self.dao.add_comment(media_id, text)
        self.comment_added.emit(media_id)
        return cid

    def delete(self, cid: int, media_id: int):
        self.dao.delete_comment(cid)
        self.comment_deleted.emit(media_id)

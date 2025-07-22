from PySide6.QtCore import Signal, QObject

from managers.dao import MediaDAO


class CommentService(QObject):
    commentAdded = Signal(int, dict)
    commentDeleted = Signal(int, int)
    commentEdited = Signal(int, dict)  # media_id, new_row
    commentReordered = Signal(int)

    def __init__(self, dao: MediaDAO, parent=None):
        super().__init__(parent)
        self.dao = dao

    def add_comment(self, media_id: int, text: str):
        max_seq = self.dao.fetchone(
            "SELECT COALESCE(MAX(seq), 0) + 1 AS nxt FROM comments WHERE media_id=?", (media_id,)
        )["nxt"]
        cid = self.dao.add_comment(media_id, text, seq=max_seq)
        row = {"id": cid, "text": text, "created": "now"}
        self.commentAdded.emit(media_id, row)
        return cid

    def delete_comment(self, comment_id: int):
        row = self.dao.fetchone("SELECT media_id FROM comments WHERE id=?", (comment_id,))
        if row:
            self.dao.delete_comment(comment_id)
            self.commentDeleted.emit(row["media_id"], comment_id)

    def list_comments(self, media_id: int) -> list[dict]:
        return self.dao.list_comments(media_id)

    def edit_comment(self, comment_id: int, new_text: str):
        new_text = new_text.strip()
        if not new_text:
            return

        self.dao.update_comment(comment_id, new_text)
        row = self.dao.fetchone(
            "SELECT media_id, text, created FROM comments WHERE id=?", (comment_id,)
        )
        if row:
            payload = {"id": comment_id,
                       "text": row["text"],
                       "created": row["created"]}
            self.commentEdited.emit(row["media_id"], payload)

    def set_order(self, media_id: int, ordered_ids: list[int]):
        if not ordered_ids:
            return
        self.dao.update_comment_sequence(media_id, ordered_ids)
        self.commentReordered.emit(media_id)

    def exists(self, media_id: int, text: str) -> bool:
        """
        Return True if text already exists for this media item.
        Case-sensitive match
        """
        row = self.dao.fetchone(
            "SELECT 1 FROM comments WHERE media_id = ? AND text = ? LIMIT 1",
            (media_id, text),
        )
        return row is not None

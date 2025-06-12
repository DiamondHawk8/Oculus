from typing import Any
import sqlite3


class BaseManager:
    """
    Shared DB helpers for all managers.
    """

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.cur = conn.cursor()

    # wrappers
    def execute(self, sql: str, params: tuple = ()) -> None:
        self.cur.execute(sql, params)
        self.conn.commit()

    def fetchone(self, sql: str, params: tuple = ()) -> Any:
        self.cur.execute(sql, params)
        return self.cur.fetchone()

    def fetchall(self, sql: str, params: tuple = ()) -> list:
        self.cur.execute(sql, params)
        return self.cur.fetchall()

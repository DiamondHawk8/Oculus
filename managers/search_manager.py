from __future__ import annotations

import logging
from pathlib import Path
from typing import Sequence, List

from db_utils import get_db_connection

logger = logging.getLogger(__name__)


class SearchManager:

    def __init__(self, db_path: str | Path, backend: str = "sqlite") -> None:
        """
        :param
            db_path : str | Path
            backend : {'sqlite', 'postgres'}, default 'sqlite'
        ex
        SearchManager('oculus.db')
        sm.simple_search('cat')
        ['/photos/cat01.jpg', '/cats/black_cat.png']
        """
        self.backend = backend.lower()
        self.conn = get_db_connection(db_path=db_path, backend=self.backend)
        self.cur = self.conn.cursor()

    def simple_search(self, term: str) -> List[str]:
        """
        Return a list of file paths whose path contains term..
        Phase-4 will switch to full-text search on PostgreSQL via ``tsvector``.
        """
        if not term:
            return []

        term_lower = f"%{term.lower()}%"
        placeholder = "%s" if self.backend == "postgres" else "?"
        sql = f"SELECT path FROM media WHERE LOWER(path) LIKE {placeholder};"

        logger.debug("Executing search SQL=%s term=%s", sql, term_lower)
        self.cur.execute(sql, (term_lower,))
        return [row[0] for row in self.cur.fetchall()]



    def tag_search(self, term: str) -> List[str]:
        """
        """
        if not term:
            return []

        like = f"%{term.lower()}%"
        placeholder = "%s" if self.backend == "postgres" else "?"
        sql = (
            f"SELECT DISTINCT m.path "
            f"FROM media m "
            f"JOIN tags t ON t.media_id = m.id "
            f"WHERE LOWER(t.tag) LIKE {placeholder};"
        )

        logger.debug("Tag search SQL=%s term=%s", sql, like)
        self.cur.execute(sql, (like,))
        return [row[0] for row in self.cur.fetchall()]

    def _fts_query_postgres(self, term: str) -> List[str]:  # pragma: no cover
        """
        Future replacement simple_search using PostgreSQL FTS.
        """
        raise NotImplementedError("FTS not implemented until Phase 4")

"""
search_manager.py – filename + advanced tag search (AND / OR / parentheses)
"""

from __future__ import annotations
import logging
from pathlib import Path
from typing import List, Set, Union

from db_utils import get_db_connection

_LOG = logging.getLogger(__name__)


Token = str
Operator = str
AST = Union[str, tuple]

def _tokenize(expr: str) -> List[str]:
    tokens: List[str] = []
    buf = []
    for ch in expr:
        if ch.isspace():
            continue
        if ch in ",|()":
            if buf:
                tokens.append("".join(buf).lower())
                buf.clear()
            tokens.append(ch)
        else:
            buf.append(ch)
    if buf:
        tokens.append("".join(buf).lower())
    return tokens


def _parse(tokens: List[str]) -> AST:
    pos = 0
    def parse_expr() -> AST:
        node = parse_term()
        while peek() == ",":
            next_tok()
            right = parse_term()
            node = ("AND", node, right)
        return node

    def parse_term() -> AST:
        node = parse_factor()
        while peek() == "|":
            next_tok()
            right = parse_factor()
            node = ("OR", node, right)
        return node

    def parse_factor() -> AST:
        tok = next_tok()
        if tok == "(":
            node = parse_expr()
            if next_tok() != ")":
                raise ValueError("Unmatched '(' in tag expression")
            return node
        if tok in (",", "|", ")", None):
            raise ValueError(f"Unexpected token {tok!r}")
        return tok

    def peek():
        return tokens[pos] if pos < len(tokens) else None

    def next_tok():
        nonlocal pos
        tok = tokens[pos] if pos < len(tokens) else None
        pos += 1
        return tok

    ast = parse_expr()
    if pos < len(tokens):
        raise ValueError(f"There are trailing tokens: {tokens[pos:]}")
    return ast


# --------------------------------------------------------------------------- #
#  SearchManager
# --------------------------------------------------------------------------- #
class SearchManager:


    def __init__(self, db_path: str | Path, backend: str = "sqlite") -> None:
        self.backend = backend.lower()
        self.conn = get_db_connection(db_path=db_path, backend=self.backend)
        self.cur = self.conn.cursor()

    def simple_search(self, term: str) -> List[str]:
        if not term:
            return []
        like = f"%{term.lower()}%"
        ph = "%s" if self.backend == "postgres" else "?"
        sql = f"SELECT path FROM media WHERE LOWER(path) LIKE {ph};"
        self.cur.execute(sql, (like,))
        return [row[0] for row in self.cur.fetchall()]


    def tag_search(self, expr: str) -> List[str]:
        """
        Boolean tag search using ',', '|', and parentheses.

        e.g. sm.tag_search("red,(blue|green)")
        """
        if not expr.strip():
            return []

        try:
            ast = _parse(_tokenize(expr))
        except ValueError as exc:
            _LOG.error("Parse error in tag expression '%s': %s", expr, exc)
            return []

        cache: dict[str, Set[str]] = {}

        def eval_ast(node: AST) -> Set[str]:
            if isinstance(node, str):                      # literal tag
                if node not in cache:
                    cache[node] = self._paths_for_tag(node)
                return cache[node]
            op, left, right = node
            if op == "AND":
                return eval_ast(left) & eval_ast(right)
            if op == "OR":
                return eval_ast(left) | eval_ast(right)
            raise RuntimeError(f"Unknown operator {op}")

        result = eval_ast(ast)
        return sorted(result)

    def _paths_for_tag(self, tag: str) -> Set[str]:
        ph = "%s" if self.backend == "postgres" else "?"
        sql = (
            f"SELECT DISTINCT m.path "
            f"FROM media m JOIN tags t ON t.media_id = m.id "
            f"WHERE LOWER(t.tag) = {ph};"
        )
        self.cur.execute(sql, (tag,))
        return {row[0] for row in self.cur.fetchall()}

    def _fts_query_postgres(self, term: str) -> List[str]:  # pragma: no cover
        raise NotImplementedError("FTS not implemented until Phase 4")

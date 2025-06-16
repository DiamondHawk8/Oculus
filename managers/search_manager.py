from __future__ import annotations
from typing import List, Set, Union
import logging

from .base import BaseManager
from .tag_manager import TagManager

logger = logging.getLogger(__name__)

Token = str
Operator = str
AST = Union[str, tuple]


def _tokenize(expr: str) -> List[str]:
    logger.debug(f"Tokenizing {expr}")
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


class SearchManager(BaseManager):
    def __init__(self, conn, tag_manager: TagManager):
        super().__init__(conn)
        self.tags = tag_manager

    # TODO, Allow for toggling of including folders in search result
    # TODO, Make paths not skew search results
    def simple_search(self, term: str) -> List[str]:
        if not term:
            return []
        like = f"%{term.lower()}%"
        self.cur.execute(
            "SELECT path FROM media WHERE LOWER(path) LIKE ?", (like,)
        )
        return [row["path"] for row in self.cur.fetchall()]

    def tag_search(self, expr: str) -> List[str]:
        if not expr.strip():
            return []

        try:
            ast = _parse(_tokenize(expr))
        except ValueError as exc:
            logger.error("Parse error in tag expression '%s': %s", expr, exc)
            return []

        cache: dict[str, Set[str]] = {}

        def eval_ast(node: AST) -> Set[str]:
            if isinstance(node, str):
                if node not in cache:
                    cache[node] = self._paths_for_tag(node)
                return cache[node]
            op, left, right = node
            return (eval_ast(left) & eval_ast(right)) if op == "AND" else (eval_ast(left) | eval_ast(right))

        return sorted(eval_ast(ast))

    def _paths_for_tag(self, tag: str) -> Set[str]:
        self.cur.execute(
            """
            SELECT DISTINCT m.path
            FROM media m JOIN tags t ON t.media_id = m.id
            WHERE LOWER(t.tag) = ?
            """,
            (tag.lower(),),
        )
        return {row["path"] for row in self.cur.fetchall()}

    def _fts_query_postgres(self, term: str) -> List[str]:  # pragma: no cover
        raise NotImplementedError("FTS not implemented until Phase 6")

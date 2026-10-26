"""CI-only opt-in syntax adapter, NOT shipped or connected to offline_core.

Parses JS/TS/TSX as inert source text. These are syntax candidates, not
verified vulnerabilities. Explicit unsupported/failed/blocked states.
"""
from __future__ import annotations
from dataclasses import dataclass

LANGUAGES = {"js", "ts", "tsx"}
MAX_BYTES = 512 * 1024
MAX_NODES = 25000


class UnsupportedParser(RuntimeError):
    pass


@dataclass(frozen=True)
class Candidate:
    rule: str
    line: int
    byte_column: int


@dataclass(frozen=True)
class Analysis:
    status: str
    language: str
    candidates: tuple[Candidate, ...]
    visited: int
    syntax_only: bool = True
    shipped: bool = False
    approved_for_sale: bool = False


def _parser(language: str):
    try:
        from tree_sitter import Language, Parser
        import tree_sitter_javascript
        import tree_sitter_typescript
    except ImportError as exc:
        raise UnsupportedParser("optional grammar not installed") from exc
    languages = {
        "js": tree_sitter_javascript.language,
        "ts": tree_sitter_typescript.language_typescript,
        "tsx": tree_sitter_typescript.language_tsx,
    }
    return Parser(Language(languages[language]()))


def inspect(source: str, language: str) -> Analysis:
    if language not in LANGUAGES:
        raise ValueError("language not supported")
    if not isinstance(source, str):
        raise TypeError("source must be str")
    raw = source.encode("utf-8")
    if len(raw) > MAX_BYTES:
        return Analysis("blocked", language, (), 0)
    tree = _parser(language).parse(raw)
    root = tree.root_node
    if root.has_error or root.is_missing or root.end_byte != len(raw):
        return Analysis("syntax_failed", language, (), 0)
    stack = [root]
    candidates = []
    visited = 0
    while stack:
        node = stack.pop()
        visited += 1
        if visited > MAX_NODES:
            return Analysis("blocked", language, (), visited)
        if node.type == "call_expression":
            callee = node.child_by_field_name("function")
            if (callee is not None and callee.type == "identifier"
                    and raw[callee.start_byte:callee.end_byte] == b"eval"):
                candidates.append(Candidate(
                    "JS-DIRECT-EVAL-PATTERN", node.start_point.row + 1,
                    node.start_point.column))
        if node.type == "new_expression":
            named = node.named_children
            if (named and named[0].type == "identifier"
                    and raw[named[0].start_byte:named[0].end_byte] == b"Function"):
                candidates.append(Candidate(
                    "JS-NEW-FUNCTION-PATTERN", node.start_point.row + 1,
                    node.start_point.column))
        stack.extend(reversed(node.named_children))
    candidates.sort(key=lambda x: (x.line, x.byte_column, x.rule))
    return Analysis("syntax_checked", language, tuple(candidates), visited)

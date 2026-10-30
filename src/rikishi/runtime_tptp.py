"""Parse complete TPTP statement boundaries, leaving formula semantics to the prover."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

_KINDS: Final = frozenset({"fof", "cnf", "tff", "thf", "include"})
_WORD: Final = re.compile(r"[a-z][A-Za-z0-9_]*")
_NAME: Final = re.compile(r"(?:[a-z][A-Za-z0-9_]*|[+-]?(?:0|[1-9][0-9]*))")
_CLOSERS: Final = {"(": ")", "[": "]"}


class TPTPError(ValueError):
    """An unsupported directive or malformed statement cannot be safely replayed."""

    message: str
    offset: int

    def __init__(self, message: str, offset: int = 0) -> None:
        self.message = message
        self.offset = offset
        super().__init__(f"{message} at character {offset}")


@dataclass(frozen=True, slots=True)
class TPTPStatement:
    """Original complete text, with decoded names and include paths when applicable."""

    text: str
    kind: str
    name: str | None
    include_path: str | None
    source_name: str | None = None


def _skip_layout(text: str, offset: int) -> int:
    while offset < len(text):
        if text[offset].isspace():
            offset += 1
            continue
        if text.startswith("%", offset):
            offset += 1
            while offset < len(text) and text[offset] not in "\r\n":
                offset += 1
            continue
        if text.startswith("/*", offset):
            end = text.find("*/", offset + 2)
            if end < 0:
                raise TPTPError("unterminated block comment", offset)
            offset = end + 2
            continue
        break
    return offset


def _quoted_end(text: str, start: int) -> int:
    offset = start + 1
    while offset < len(text):
        if text.startswith("\\", offset):
            offset += 2
            continue
        if text.startswith(text[start], offset):
            return offset + 1
        offset += 1
    raise TPTPError("unterminated quoted string", start)


def _arguments(text: str, start: int) -> tuple[list[tuple[int, int]], int]:
    stack = [")"]
    arguments: list[tuple[int, int]] = []
    beginning = offset = start + 1
    while offset < len(text):
        offset = _skip_layout(text, offset)
        if offset == len(text):
            break
        if text[offset] in "'\"":
            offset = _quoted_end(text, offset)
            continue
        closer = _CLOSERS.get(text[offset])
        if closer is not None:
            stack.append(closer)
        elif text[offset] in ")]":
            if text[offset] != stack.pop():
                raise TPTPError("unbalanced parentheses or brackets", offset)
            if not stack:
                arguments.append((beginning, offset))
                return arguments, offset + 1
        elif text.startswith(",", offset) and len(stack) == 1:
            arguments.append((beginning, offset))
            beginning = offset + 1
        offset += 1
    raise TPTPError("unterminated statement or unbalanced nesting", start)


def _single_quoted(text: str, start: int, end: int) -> str:
    quoted_end = _quoted_end(text, start)
    if _skip_layout(text, quoted_end) != end:
        raise TPTPError("expected a single quoted token", start)
    value: list[str] = []
    offset = start + 1
    while offset < quoted_end - 1:
        if text.startswith("\\", offset):
            offset += 1
            if text[offset] not in "\\'":
                raise TPTPError("unsupported single quoted escape", offset - 1)
        value.append(text[offset])
        offset += 1
    if not value:
        raise TPTPError("empty single quoted token", start)
    return "".join(value)


def _formula_name(text: str, start: int, end: int) -> str:
    start = _skip_layout(text, start)
    if text.startswith("'", start):
        if "\\'" in text[start:_quoted_end(text, start) - 1]:
            raise TPTPError("escaped apostrophes in formula names are unsupported", start)
        return _single_quoted(text, start, end)
    match = _NAME.match(text, start)
    if match is None or _skip_layout(text, match.end()) != end:
        raise TPTPError("invalid TPTP formula name", start)
    return match.group()


def _file_source_name(text: str, start: int, end: int) -> str | None:
    start = _skip_layout(text, start)
    kind = _WORD.match(text, start)
    if kind is None or kind.group() != "file":
        return None
    opening = _skip_layout(text, kind.end())
    if not text.startswith("(", opening):
        raise TPTPError("expected file source argument list", opening)
    arguments, closing = _arguments(text, opening)
    if len(arguments) != 2 or _skip_layout(text, closing) != end:
        raise TPTPError("unsupported file source annotation", start)
    path_start, path_end = arguments[0]
    path_start = _skip_layout(text, path_start)
    if not text.startswith("'", path_start):
        raise TPTPError("file source path must be single quoted", path_start)
    if _skip_layout(text, _quoted_end(text, path_start)) != path_end:
        raise TPTPError("expected a single file source path", path_start)
    return _formula_name(text, *arguments[1])


def parse_tptp(text: str) -> list[TPTPStatement]:
    """Parse structural statements without interpreting their logical formulas.

    Scanning is iterative and linear in the input size. Statements retain every
    character from their kind through the top-level terminating dot, including
    inner whitespace, quotes, and comments. Standalone leading comments are
    omitted. Quoted formula names support doubled backslashes; escaped
    apostrophes are rejected because the pinned E corrupts their identity.
    Numeric names retain their spelling. Include paths must be unescaped
    single-quoted literals: backslashes, selections and unknown directives fail
    closed.
    """
    statements: list[TPTPStatement] = []
    offset = _skip_layout(text, 0)
    while offset < len(text):
        start = offset
        kind_match = _WORD.match(text, offset)
        if kind_match is None or kind_match.group() not in _KINDS:
            raise TPTPError("unsupported TPTP statement kind", offset)
        kind = kind_match.group()
        offset = _skip_layout(text, kind_match.end())
        if not text.startswith("(", offset):
            raise TPTPError("expected opening parenthesis", offset)
        arguments, end = _arguments(text, offset)
        offset = _skip_layout(text, end)
        if not text.startswith(".", offset):
            raise TPTPError("expected terminating dot", offset)
        end = offset + 1
        name: str | None = None
        include_path: str | None = None
        source_name: str | None = None
        if kind.startswith("include"):
            if len(arguments) != 1:
                raise TPTPError("unsupported TPTP include selection or arguments", start)
            argument_start, argument_end = arguments[0]
            argument_start = _skip_layout(text, argument_start)
            if not text.startswith("'", argument_start):
                raise TPTPError("include path must be single quoted", argument_start)
            quoted_end = _quoted_end(text, argument_start)
            if "\\" in text[argument_start:quoted_end]:
                raise TPTPError("backslashes in include paths are unsupported", argument_start)
            include_path = _single_quoted(text, argument_start, argument_end)
        else:
            if not 3 <= len(arguments) <= 5:
                raise TPTPError("expected name, role, formula and optional annotations", start)
            for argument_start, argument_end in arguments:
                if _skip_layout(text, argument_start) == argument_end:
                    raise TPTPError("empty TPTP formula argument", argument_start)
            name = _formula_name(text, *arguments[0])
            if len(arguments) >= 4:
                source_name = _file_source_name(text, *arguments[3])
        statements.append(TPTPStatement(text[start:end], kind, name, include_path, source_name))
        offset = _skip_layout(text, end)
    return statements

"""Bounded, literal queries against an existing source index."""

import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from typing import Final, Literal, Protocol

from rikishi.graph_types import CorpusFile, FilePage, FormulaPage, Page, Provenance, SourceFormula


class IndexReader(Protocol):
    def _connect(self) -> sqlite3.Connection: ...


class QueryError(ValueError):
    """A query parameter lies outside the supported read-only contract."""

    def __init__(self, parameter: str, requirement: str):
        super().__init__(f"{parameter} {requirement}")


def bounded(value: int, parameter: str, low: int, high: int) -> None:
    if type(value) is not int or not low <= value <= high:
        raise QueryError(parameter, f"must be an integer between {low} and {high}")


def literal(value: str, parameter: str, required: bool = False) -> None:
    if type(value) is not str or len(value) > 2048 or "\x00" in value:
        raise QueryError(parameter, "must be text of at most 2048 characters without NUL")
    if (required or value != "") and not value.strip():
        raise QueryError(parameter, "must be nonempty when supplied")


@dataclass(frozen=True, slots=True)
class FileQuery:
    path: str = ""
    sort: Literal["path", "formulas"] = "path"
    descending: bool = False
    limit: int = 50
    offset: int = 0

    def __post_init__(self) -> None:
        literal(self.path, "path")
        if self.sort not in ("path", "formulas"):
            raise QueryError("sort", "must be path or formulas")
        if type(self.descending) is not bool:
            raise QueryError("descending", "must be boolean")
        bounded(self.limit, "limit", 1, 500)
        bounded(self.offset, "offset", 0, 1_000_000)


@dataclass(frozen=True, slots=True)
class FormulaQuery:
    text: str = ""
    head: str = ""
    path: str = ""
    term: str = ""
    limit: int = 50
    offset: int = 0

    def __post_init__(self) -> None:
        for name in ("text", "head", "path", "term"):
            literal(getattr(self, name), name)
        bounded(self.limit, "limit", 1, 500)
        bounded(self.offset, "offset", 0, 1_000_000)


DEFAULT_FILES: Final = FileQuery()
DEFAULT_FORMULAS: Final = FormulaQuery()


def provenance(connection: sqlite3.Connection) -> Provenance:
    metadata = {row[0]: json.loads(row[1]) for row in connection.execute(
        "SELECT key,value FROM metadata WHERE key IN ('source_commit','source_clean')"
    )}
    return Provenance(source_commit=metadata["source_commit"], source_clean=metadata["source_clean"])


def page(total: int, filtered: int, query: FileQuery | FormulaQuery) -> Page:
    returned = min(query.limit, max(0, filtered - query.offset))
    return Page(total=total, filtered_total=filtered, returned=returned, limit=query.limit,
                offset=query.offset, truncated=returned < filtered,
                has_more=query.offset + returned < filtered)


def corpus_files(index: IndexReader, query: FileQuery = DEFAULT_FILES) -> FilePage:
    """Page indexed files, with literal path substring matching and complete totals."""
    direction = "DESC" if query.descending else "ASC"
    order = {"path": f"path {direction}",
             "formulas": f"formulas {direction},path ASC"}[query.sort]
    with closing(index._connect()) as connection, connection:
        total, formulas = connection.execute(
            "SELECT COUNT(*),COALESCE(SUM(formulas),0) FROM files"
        ).fetchone()
        filtered, selected_formulas = connection.execute(
            "SELECT COUNT(*),COALESCE(SUM(formulas),0) FROM files WHERE instr(path,?)>0",
            (query.path,),
        ).fetchone()
        items = [CorpusFile(path=row[0], sha256=row[1], formulas=row[2]) for row in
                 connection.execute("SELECT path,sha256,formulas FROM files "
                                    f"WHERE instr(path,?)>0 ORDER BY {order} LIMIT ? OFFSET ?",
                                    (query.path, query.limit, query.offset))]
        return FilePage(**page(total, filtered, query), items=items, total_formulas=formulas,
                        filtered_formulas=selected_formulas, provenance=provenance(connection),
                        scope="successfully indexed files; path is a literal substring")


def source_formula(row: sqlite3.Row) -> SourceFormula:
    return SourceFormula(id=row["id"], path=row["path"], line=row["line"], text=row["text"],
                         predicate=row["predicate"], source_sha256=row["source_sha256"])


def formula_search(index: IndexReader, query: FormulaQuery = DEFAULT_FORMULAS) -> FormulaPage:
    """Search retained top-level formulas; nested terms use the occurrence inventory."""
    conditions = ["instr(f.text,?)>0"]
    parameters: list[str | int] = [query.text]
    for column, value in (("f.predicate", query.head), ("f.path", query.path)):
        if value:
            conditions.append(f"{column}=?")
            parameters.append(value)
    if query.term:
        conditions.append("f.id IN (SELECT formula_id FROM occurrences WHERE term=?)")
        parameters.append(query.term)
    where = " AND ".join(conditions)
    with closing(index._connect()) as connection, connection:
        total = connection.execute("SELECT COUNT(*) FROM formulas").fetchone()[0]
        filtered = connection.execute(
            f"SELECT COUNT(*) FROM formulas f WHERE {where}", parameters
        ).fetchone()[0]
        items = [source_formula(row) for row in connection.execute(
            "SELECT f.*,s.sha256 AS source_sha256 FROM formulas f JOIN files s ON s.path=f.path "
            f"WHERE {where} ORDER BY f.path,f.line,f.id LIMIT ? OFFSET ?",
            (*parameters, query.limit, query.offset),
        )]
        return FormulaPage(**page(total, filtered, query), items=items,
                           provenance=provenance(connection),
                           scope="indexed top-level formulas; literal text; exact head/path/term")

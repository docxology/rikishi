from collections import deque
from contextlib import closing
from dataclasses import dataclass
from typing import Literal

from rikishi.corpus_query import (
    IndexReader,
    QueryError,
    bounded,
    literal,
    provenance,
    source_formula,
)
from rikishi.graph_types import PathEdge, TaxonomyPath
from rikishi.ontology_analysis import TAXONOMY_RELATIONS


@dataclass(frozen=True, slots=True)
class TaxonomyPathQuery:
    source: str
    target: str
    relation: Literal["subclass", "subrelation"] = "subclass"
    path: str = ""
    max_depth: int = 20
    max_visited: int = 10_000

    def __post_init__(self) -> None:
        literal(self.source, "source", required=True)
        literal(self.target, "target", required=True)
        literal(self.path, "path")
        if self.relation not in TAXONOMY_RELATIONS:
            raise QueryError("relation", "must be subclass or subrelation")
        bounded(self.max_depth, "max_depth", 0, 100)
        bounded(self.max_visited, "max_visited", 1, 100_000)


def taxonomy_path(index: IndexReader, query: TaxonomyPathQuery) -> TaxonomyPath:
    """Find one shortest directed source path; bounded absence is never called exhaustive."""
    with closing(index._connect()) as connection, connection:
        for name in (query.source, query.target):
            if not connection.execute("SELECT 1 FROM terms WHERE name=?", (name,)).fetchone():
                raise KeyError(name)
        previous: dict[str, tuple[str, int] | None] = {query.source: None}
        pending = deque([(query.source, 0)])
        status: Literal["found", "not_found", "max_depth", "max_visited"] = "not_found"
        depth_limited = False
        while pending:
            name, depth = pending.popleft()
            if name == query.target:
                status = "found"
                break
            remaining = query.max_visited - len(previous)
            rows = connection.execute(
                "SELECT e.object,MIN(e.formula_id) FROM edges e "
                "JOIN formulas f ON f.id=e.formula_id WHERE e.subject=? AND e.predicate=? "
                "AND (?='' OR f.path=?) GROUP BY e.object ORDER BY e.object",
                (name, query.relation, query.path, query.path),
            )
            for neighbor, identity in rows:
                if neighbor in previous:
                    continue
                if depth >= query.max_depth:
                    depth_limited = True
                    break
                if remaining == 0:
                    status = "max_visited"
                    break
                previous[neighbor] = (name, identity)
                remaining -= 1
                pending.append((neighbor, depth + 1))
            if status == "max_visited":
                break
        if status == "not_found" and depth_limited:
            status = "max_depth"
        # A discovered target is already a shortest BFS path, even if another neighbor hit the cap.
        if query.target in previous:
            status = "found"
        nodes: list[str] = []
        edges: list[PathEdge] = []
        if status == "found":
            name = query.target
            nodes.append(name)
            while (step := previous[name]) is not None:
                parent, identity = step
                row = connection.execute(
                    "SELECT f.*,s.sha256 AS source_sha256 FROM formulas f "
                    "JOIN files s ON s.path=f.path WHERE f.id=?", (identity,)
                ).fetchone()
                edges.append(PathEdge(source=parent, target=name, relation=query.relation,
                                      formula=source_formula(row)))
                nodes.append(parent)
                name = parent
            nodes.reverse()
            edges.reverse()
        return TaxonomyPath(source=query.source, target=query.target, relation=query.relation,
                            path=query.path, status=status, nodes=nodes, edges=edges,
                            visited=len(previous), max_depth=query.max_depth,
                            max_visited=query.max_visited, provenance=provenance(connection),
                            scope="one shortest direct child-to-parent source path; no inferred "
                            "assertions; not_found exhausts reachable nodes; bounds report separately")

"""Direct source-structure diagnostics; no logical or consistency inference."""

from contextlib import closing
from dataclasses import dataclass
from typing import Final, Literal

from rikishi.corpus_query import IndexReader, QueryError, bounded, literal, provenance
from rikishi.graph_types import (
    CycleComponent,
    RelationSummary,
    RelationSummaryResult,
    TaxonomyNode,
    TaxonomyResult,
)
from rikishi.ontology_graph import strong_components, weak_components

TAXONOMY_RELATIONS: Final = ("subclass", "subrelation")
MAX_DIRECT_EDGES: Final = 1_000_000


@dataclass(frozen=True, slots=True)
class TaxonomyQuery:
    relation: Literal["subclass", "subrelation"] = "subclass"
    path: str = ""
    limit: int = 50
    offset: int = 0

    def __post_init__(self) -> None:
        if self.relation not in TAXONOMY_RELATIONS:
            raise QueryError("relation", "must be subclass or subrelation")
        literal(self.path, "path")
        bounded(self.limit, "limit", 1, 500)
        bounded(self.offset, "offset", 0, 1_000_000)


DEFAULT_TAXONOMY: Final = TaxonomyQuery()


def relation_inventory(index: IndexReader) -> RelationSummaryResult:
    """Inventory every indexed binary relation, counting repeated source assertions."""
    with closing(index._connect()) as connection, connection:
        rows = connection.execute("""
            WITH triples AS (
                SELECT predicate,subject,object,COUNT(*) AS assertions FROM edges
                GROUP BY predicate,subject,object
            ), nodes AS (
                SELECT predicate,subject AS name FROM triples
                UNION SELECT predicate,object AS name FROM triples
            ), counts AS (SELECT predicate,COUNT(*) AS count FROM nodes GROUP BY predicate)
            SELECT t.predicate,SUM(t.assertions),COUNT(*),c.count
            FROM triples t JOIN counts c ON c.predicate=t.predicate
            GROUP BY t.predicate ORDER BY t.predicate
        """)
        items = [RelationSummary(relation=row[0], assertion_count=row[1], unique_edges=row[2],
                                 duplicate_assertions=row[1] - row[2], node_count=row[3])
                 for row in rows]
        return RelationSummaryResult(items=items, total=len(items),
                                     assertion_count=sum(item["assertion_count"] for item in items),
                                     unique_edges=sum(item["unique_edges"] for item in items),
                                     provenance=provenance(connection),
                                     scope="all indexed top-level atomic binary triples; no closure")


def taxonomy_analysis(index: IndexReader, query: TaxonomyQuery = DEFAULT_TAXONOMY) -> TaxonomyResult:
    """Measure distinct child-to-parent edges and endpoint-only graph populations."""
    with closing(index._connect()) as connection, connection:
        total = connection.execute(
            "SELECT COUNT(*) FROM (SELECT subject FROM edges WHERE predicate=? UNION "
            "SELECT object FROM edges WHERE predicate=?)", (query.relation, query.relation)
        ).fetchone()[0]
        where = "e.predicate=? AND (?='' OR f.path=?)"
        parameters = (query.relation, query.path, query.path)
        assertions = connection.execute(
            f"SELECT COUNT(*) FROM edges e JOIN formulas f ON f.id=e.formula_id WHERE {where}",
            parameters,
        ).fetchone()[0]
        triples = list(connection.execute(
            "SELECT DISTINCT e.subject,e.object FROM edges e "
            f"JOIN formulas f ON f.id=e.formula_id WHERE {where} "
            "ORDER BY e.subject,e.object LIMIT ?", (*parameters, MAX_DIRECT_EDGES + 1)
        ))
        origin = provenance(connection)
    if len(triples) > MAX_DIRECT_EDGES:
        raise QueryError("graph", f"exceeds {MAX_DIRECT_EDGES} distinct edges; select a source path")
    parents: dict[str, set[str]] = {}
    children: dict[str, set[str]] = {}
    for subject, target in triples:
        parents.setdefault(subject, set()).add(target)
        parents.setdefault(target, set())
        children.setdefault(target, set()).add(subject)
        children.setdefault(subject, set())
    components = weak_components(parents, children)
    cycles = [members for members in strong_components(parents, children)
              if len(members) > 1 or members[0] in parents[members[0]]]
    cycle_names = {name: members[0] for members in cycles for name in members}
    names = sorted(parents)
    items = [TaxonomyNode(name=name, parent_count=len(parents[name]),
                          child_count=len(children[name]), component=components[name],
                          cycle_component=cycle_names.get(name))
             for name in names[query.offset:query.offset + query.limit]]
    evidence = [CycleComponent(representative=members[0], node_count=len(members),
                               members=members[:10], members_truncated=len(members) > 10)
                for members in cycles[:query.limit]]
    return TaxonomyResult(
        items=items, total=total, filtered_total=len(names), returned=len(items),
        limit=query.limit, offset=query.offset, truncated=len(items) < len(names),
        has_more=query.offset + len(items) < len(names), relation=query.relation, path=query.path,
        assertion_count=assertions, unique_edges=len(triples),
        duplicate_assertions=assertions - len(triples), node_count=len(names),
        root_count=sum(not targets for targets in parents.values()),
        multiple_parent_count=sum(len(targets) > 1 for targets in parents.values()),
        weak_component_count=len(set(components.values())), cyclic_component_count=len(cycles),
        cyclic_node_count=len(cycle_names), self_loop_count=sum(n in parents[n] for n in names),
        cycle_components=evidence, cycle_components_truncated=len(evidence) < len(cycles),
        provenance=origin, scope="distinct direct child-to-parent edges; selected-relation endpoints "
        "only; roots have zero parents; cycles are directed SCCs; exact source path; no inference",
    )

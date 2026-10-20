"""Exact descriptive measurements of indexed syntax, never inferred semantics."""

from contextlib import closing
from typing import TypedDict

from rikishi.ontology import OntologyIndex


class CompositionRow(TypedDict):
    label: str
    count: int
    share: float | None


class DegreeRow(TypedDict):
    degree: int
    terms: int


class CorpusAnalytics(TypedDict):
    source_commit: str
    source_clean: bool | None
    formula_denominator: int
    term_denominator: int
    indexed_files: int
    rejected_files: int
    file_hhi: float | None
    largest_file_share: float | None
    top_ten_file_share: float | None
    predicates: list[CompositionRow]
    edge_assertions: int
    unique_edges: int
    duplicate_edge_assertions: int
    incident_terms: int
    zero_degree_terms: int
    mean_total_degree: float | None
    degree_distribution: list[DegreeRow]


def measure_corpus(index: OntologyIndex) -> CorpusAnalytics:
    """Measure all indexed rows; edge degree deduplicates labeled directed triples.

    Every indexed symbol is in the degree denominator, including relation names
    and symbols appearing only inside formulas. Self loops contribute two to
    total (in plus out) degree. Empty denominators yield null, never a fake zero.
    """
    with closing(index._connect()) as connection:
        import json

        metadata = {r[0]: json.loads(r[1]) for r in connection.execute("SELECT * FROM metadata")}
        sizes = [
            r[0] for r in connection.execute("SELECT formulas FROM files ORDER BY formulas DESC")
        ]
        formulas = sum(sizes)
        terms = connection.execute("SELECT COUNT(*) FROM terms").fetchone()[0]
        assertions = connection.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
        unique = connection.execute(
            "SELECT COUNT(*) FROM (SELECT DISTINCT subject,predicate,object FROM edges)"
        ).fetchone()[0]
        predicates = [
            CompositionRow(label=r[0], count=r[1], share=r[1] / formulas if formulas else None)
            for r in connection.execute(
                "SELECT predicate,COUNT(*) FROM formulas GROUP BY predicate ORDER BY COUNT(*) DESC,predicate"
            )
        ]
        distribution = [
            DegreeRow(degree=r[0], terms=r[1])
            for r in connection.execute("""
            WITH triples AS (SELECT DISTINCT subject,predicate,object FROM edges),
            endpoints AS (SELECT subject AS name FROM triples UNION ALL SELECT object FROM triples),
            degrees AS (SELECT name,COUNT(*) AS degree FROM endpoints GROUP BY name),
            all_degrees AS (SELECT COALESCE(degree,0) AS degree FROM terms LEFT JOIN degrees USING(name))
            SELECT degree,COUNT(*) FROM all_degrees GROUP BY degree ORDER BY degree
        """)
        ]
    zero = next((r["terms"] for r in distribution if r["degree"] == 0), 0)
    return CorpusAnalytics(
        source_commit=metadata["source_commit"],
        source_clean=metadata["source_clean"],
        formula_denominator=formulas,
        term_denominator=terms,
        indexed_files=len(sizes),
        rejected_files=len(metadata["parse_errors"]),
        file_hhi=sum((n / formulas) ** 2 for n in sizes) if formulas else None,
        largest_file_share=sizes[0] / formulas if formulas else None,
        top_ten_file_share=sum(sizes[:10]) / formulas if formulas else None,
        predicates=predicates,
        edge_assertions=assertions,
        unique_edges=unique,
        duplicate_edge_assertions=assertions - unique,
        incident_terms=terms - zero,
        zero_degree_terms=zero,
        mean_total_degree=2 * unique / terms if terms else None,
        degree_distribution=distribution,
    )

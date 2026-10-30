from typing import Literal, TypedDict


class GraphNode(TypedDict):
    id: str
    label: str


class GraphEdge(TypedDict):
    source: str
    target: str
    relation: str


class RelationInventory(TypedDict):
    relation: str
    count: int


class Neighborhood(TypedDict):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    total_edges: int
    returned_edges: int
    truncated: bool
    relations: list[RelationInventory]


class Provenance(TypedDict):
    source_commit: str
    source_clean: bool | None


class Page(TypedDict):
    total: int
    filtered_total: int
    returned: int
    limit: int
    offset: int
    truncated: bool
    has_more: bool


class CorpusFile(TypedDict):
    path: str
    sha256: str
    formulas: int


class SourceFormula(TypedDict):
    id: int
    path: str
    line: int
    text: str
    predicate: str
    source_sha256: str


class FilePage(Page):
    items: list[CorpusFile]
    total_formulas: int
    filtered_formulas: int
    provenance: Provenance
    scope: str


class FormulaPage(Page):
    items: list[SourceFormula]
    provenance: Provenance
    scope: str


class RelationSummary(TypedDict):
    relation: str
    assertion_count: int
    unique_edges: int
    duplicate_assertions: int
    node_count: int


class RelationSummaryResult(TypedDict):
    items: list[RelationSummary]
    total: int
    assertion_count: int
    unique_edges: int
    provenance: Provenance
    scope: str


class TaxonomyNode(TypedDict):
    name: str
    parent_count: int
    child_count: int
    component: str
    cycle_component: str | None


class CycleComponent(TypedDict):
    representative: str
    node_count: int
    members: list[str]
    members_truncated: bool


class TaxonomyResult(Page):
    items: list[TaxonomyNode]
    relation: str
    path: str
    assertion_count: int
    unique_edges: int
    duplicate_assertions: int
    node_count: int
    root_count: int
    multiple_parent_count: int
    weak_component_count: int
    cyclic_component_count: int
    cyclic_node_count: int
    self_loop_count: int
    cycle_components: list[CycleComponent]
    cycle_components_truncated: bool
    provenance: Provenance
    scope: str


class PathEdge(GraphEdge):
    formula: SourceFormula


class TaxonomyPath(TypedDict):
    source: str
    target: str
    relation: str
    path: str
    status: Literal["found", "not_found", "max_depth", "max_visited"]
    nodes: list[str]
    edges: list[PathEdge]
    visited: int
    max_depth: int
    max_visited: int
    provenance: Provenance
    scope: str

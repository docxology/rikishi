import os
from pathlib import Path
from typing import Literal

from mcp.server.fastmcp import FastMCP

from rikishi.analytics import CorpusAnalytics, measure_corpus
from rikishi.bridge_models import BridgeReport, BridgeStudy
from rikishi.bridge_views import BridgeCaseView
from rikishi.corpus_query import FileQuery, FormulaQuery
from rikishi.fep import (
    DemoResult,
    EnergyResult,
    LogEnergyResult,
    demo,
    free_energy,
    free_energy_log,
)
from rikishi.graph_types import (
    FilePage,
    FormulaPage,
    Neighborhood,
    RelationSummaryResult,
    TaxonomyPath,
    TaxonomyResult,
)
from rikishi.ontology import OntologyIndex
from rikishi.ontology_analysis import TaxonomyQuery
from rikishi.taxonomy_paths import TaxonomyPathQuery


def create_server(root: Path) -> FastMCP:
    server = FastMCP(
        "rikishi",
        instructions=(
            "Read-only SUMO structural index. Asserted edges are not inferred proofs. "
            "FEP mappings are proposed connections; numerical examples are finite, in nats."
        ),
    )
    index = OntologyIndex(root / ".rikishi/ontology.sqlite")

    @server.tool()
    def bridge_catalog() -> BridgeStudy:
        """Inspect declared shared finite witnesses; run no native prover or compiler."""
        from rikishi.bridge_study import catalog

        return catalog()

    @server.tool()
    def bridge_verify_report(report: str, sha256: str) -> BridgeReport:
        """Replay saved Lean/numerical/SUMO evidence against a separately retained digest."""
        from rikishi.bridge_views import inspect_report

        return inspect_report(root, report, sha256)

    @server.tool()
    def bridge_inspect_case(
        report: str, sha256: str, case_id: str, prover: Literal["e", "v"] = "e",
    ) -> BridgeCaseView:
        """Read captured native output joined to exact source and a shared Lean/numerical witness."""
        from rikishi.bridge_views import inspect_case
        from rikishi.inference_views import CaseSelection

        return inspect_case(root, CaseSelection(report, sha256, case_id, prover))

    @server.tool()
    def inference_catalog() -> dict[str, object]:
        from rikishi.inference_study import catalog

        return catalog().model_dump(mode="json")

    @server.tool()
    def inference_verify_report(report: str, sha256: str) -> dict[str, object]:
        from rikishi.inference_views import inspect_report

        return inspect_report(root, report, sha256)

    @server.tool()
    def inference_inspect_case(
        report: str, sha256: str, case_id: str, prover: Literal["e", "v"] = "e",
    ) -> dict[str, object]:
        from rikishi.inference_views import CaseSelection, inspect_case

        return inspect_case(root, CaseSelection(report, sha256, case_id, prover))

    @server.tool()
    def corpus_stats() -> dict:
        """Return source revision, measured corpus counts, and explicit parse failures."""
        return index.stats()

    @server.tool()
    def corpus_analytics() -> CorpusAnalytics:
        """Measure source composition and asserted graph with explicit denominators, not truth."""
        return measure_corpus(index)

    @server.tool()
    def corpus_files(
        path: str = "", sort: Literal["path", "formulas"] = "path",
        descending: bool = False, limit: int = 50, offset: int = 0,
    ) -> FilePage:
        """Page source files with hashes; path matches a literal substring, totals stay explicit."""
        return index.corpus_files(FileQuery(path, sort, descending, limit, offset))

    @server.tool()
    def formula_search(
        text: str = "", head: str = "", path: str = "", term: str = "",
        limit: int = 50, offset: int = 0,
    ) -> FormulaPage:
        """Search literal formula text and exact head/file/term; retain source hashes and lines."""
        return index.formula_search(FormulaQuery(text, head, path, term, limit, offset))

    @server.tool()
    def relation_inventory() -> RelationSummaryResult:
        """Measure every direct binary relation, with repeated assertions separated from triples."""
        return index.relation_inventory()

    @server.tool()
    def taxonomy_analysis(
        relation: Literal["subclass", "subrelation"] = "subclass", path: str = "",
        limit: int = 50, offset: int = 0,
    ) -> TaxonomyResult:
        """Measure direct taxonomy structure; graph cycles are not logical inconsistency proofs."""
        return index.taxonomy_analysis(TaxonomyQuery(relation, path, limit, offset))

    @server.tool()
    def taxonomy_path(
        source: str, target: str, relation: Literal["subclass", "subrelation"] = "subclass",
        path: str = "", max_depth: int = 20, max_visited: int = 10_000,
    ) -> TaxonomyPath:
        """Find a shortest child-to-parent source path; report traversal limits explicitly."""
        return index.taxonomy_path(TaxonomyPathQuery(
            source, target, relation, path, max_depth, max_visited,
        ))

    @server.tool()
    def search_terms(query: str, limit: int = 30) -> list[dict]:
        """Search SUMO term names; limit is 1 through 200."""
        return index.search(query, limit)

    @server.tool()
    def inspect_term(name: str) -> dict:
        """Inspect documentation, asserted parents, and formulas with source file and line."""
        return index.term(name)

    @server.tool()
    def relation_graph(name: str, limit: int = 80, relation: str | None = None) -> Neighborhood:
        """Return at most limit asserted binary edges adjacent to a term, not inference."""
        return index.neighborhood(name, limit, relation)

    @server.tool()
    def finite_free_energy(
        prior: list[float], likelihood: list[float], posterior: list[float]
    ) -> EnergyResult:
        """Evaluate finite variational free energy in nats and check its KL decomposition."""
        return free_energy(prior, likelihood, posterior)

    @server.tool(description=(
        "Evaluate a finite model from nonpositive log probabilities. Null input denotes exact "
        "zero mass; null evidence denotes positive evidence below the linear float range."
    ))
    def finite_free_energy_log(
        log_prior: list[float | None], log_likelihood: list[float | None], posterior: list[float]
    ) -> LogEnergyResult:
        return free_energy_log(log_prior, log_likelihood, posterior)

    @server.resource("sumo://corpus")
    def corpus_resource() -> dict:
        return index.stats()

    @server.resource("rikishi://fep-example")
    def example_resource() -> DemoResult:
        return demo()

    return server


def main() -> None:
    create_server(Path(os.environ.get("RIKISHI_ROOT", ".")).resolve()).run(transport="stdio")

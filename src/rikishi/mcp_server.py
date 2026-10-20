import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from rikishi.fep import demo, free_energy
from rikishi.ontology import OntologyIndex


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
    def corpus_stats() -> dict:
        """Return source revision, measured corpus counts, and explicit parse failures."""
        return index.stats()

    @server.tool()
    def search_terms(query: str, limit: int = 30) -> list[dict]:
        """Search SUMO term names; limit is 1 through 200."""
        return index.search(query, limit)

    @server.tool()
    def inspect_term(name: str) -> dict:
        """Inspect documentation, asserted parents, and formulas with source file and line."""
        return index.term(name)

    @server.tool()
    def relation_graph(name: str, limit: int = 80) -> dict:
        """Return at most limit asserted binary edges adjacent to a term, not inference."""
        return index.neighborhood(name, limit)

    @server.tool()
    def finite_free_energy(
        prior: list[float], likelihood: list[float], posterior: list[float]
    ) -> dict:
        """Evaluate finite variational free energy in nats and check its KL decomposition."""
        return free_energy(prior, likelihood, posterior)

    @server.resource("sumo://corpus")
    def corpus_resource() -> dict:
        return index.stats()

    @server.resource("rikishi://fep-example")
    def example_resource() -> dict:
        return demo()

    return server


def main() -> None:
    create_server(Path(os.environ.get("RIKISHI_ROOT", ".")).resolve()).run(transport="stdio")

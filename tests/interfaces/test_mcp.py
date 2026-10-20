import json
import math

import anyio

from rikishi.mcp_server import create_server
from rikishi.ontology import OntologyIndex


def test_mcp_tools_real_index_and_probability_errors(tmp_path):
    source = tmp_path / "sumo"
    source.mkdir()
    (source / "Merge.kif").write_text("(subclass Human Animal)")
    OntologyIndex(tmp_path / ".rikishi/ontology.sqlite").build(source)
    server = create_server(tmp_path)

    async def scenario():
        names = {tool.name for tool in await server.list_tools()}
        assert names == {
            "corpus_stats",
            "corpus_analytics",
            "search_terms",
            "inspect_term",
            "relation_graph",
            "finite_free_energy",
        }
        tools = [
            ("corpus_stats", {}),
            ("corpus_analytics", {}),
            ("search_terms", {"query": "Human"}),
            ("inspect_term", {"name": "Human"}),
            ("relation_graph", {"name": "Human"}),
            (
                "finite_free_energy",
                {"prior": [0.5, 0.5], "likelihood": [0.8, 0.2], "posterior": [0.8, 0.2]},
            ),
        ]
        for name, arguments in tools:
            result = await server.call_tool(name, arguments)
            if isinstance(result, tuple):
                payload = result[1] if name == "corpus_analytics" else result[1]["result"]
            else:
                payload = json.loads(result[0].text)
            match name:
                case "corpus_stats":
                    assert payload["formulas"] == 1
                case "corpus_analytics":
                    assert payload["formula_denominator"] == 1
                    assert payload["unique_edges"] == 1
                case "search_terms":
                    assert payload[0]["name"] == "Human"
                case "inspect_term":
                    assert payload["parents"] == [{"name": "Animal", "relation": "subclass"}]
                case "relation_graph":
                    assert payload["edges"] == [
                        {"source": "Human", "target": "Animal", "relation": "subclass"}
                    ]
                case "finite_free_energy":
                    assert abs(payload["free_energy"] - math.log(2)) < 1e-12
                    assert payload["exact_posterior"] == [0.8, 0.2]
        resources = await server.list_resources()
        assert {str(r.uri) for r in resources} == {"sumo://corpus", "rikishi://fep-example"}
        for resource in resources:
            contents = await server.read_resource(str(resource.uri))
            payload = json.loads(next(iter(contents)).content)
            if str(resource.uri) == "sumo://corpus":
                assert payload["files"] == 1
                assert payload["parse_errors"] == []
            else:
                assert payload["result"]["evidence"] == 0.5
                assert len(payload["scan"]) == 101

    anyio.run(scenario)

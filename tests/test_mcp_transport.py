import json
import os
import sys

import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from rikishi.ontology import OntologyIndex


def test_real_mcp_stdio_initialize_tools_and_failure(tmp_path):
    source = tmp_path / "sumo"
    source.mkdir()
    (source / "Merge.kif").write_text("(subclass Human Animal)")
    OntologyIndex(tmp_path / ".rikishi/ontology.sqlite").build(source)

    async def scenario():
        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-m", "rikishi", "--root", str(tmp_path), "mcp"],
            env=dict(os.environ),
        )
        with anyio.fail_after(20):
            async with (
                stdio_client(parameters) as (reader, writer),
                ClientSession(reader, writer) as session,
            ):
                initialized = await session.initialize()
                assert initialized.serverInfo.name == "rikishi"
                tools = await session.list_tools()
                assert len(tools.tools) == 5
                success = await session.call_tool("inspect_term", {"name": "Human"})
                assert success.isError is False
                assert json.loads(success.content[0].text)["name"] == "Human"
                stats = await session.call_tool("corpus_stats", {})
                assert json.loads(stats.content[0].text)["formulas"] == 1
                graph = await session.call_tool("relation_graph", {"name": "Human"})
                assert json.loads(graph.content[0].text)["edges"] == [
                    {"source": "Human", "target": "Animal", "relation": "subclass"}
                ]
                failure = await session.call_tool("inspect_term", {"name": "NotInOntology"})
                assert failure.isError is True
                invalid = await session.call_tool(
                    "finite_free_energy",
                    {"prior": [2.0], "likelihood": [0.5], "posterior": [1.0]},
                )
                assert invalid.isError is True
                resources = await session.list_resources()
                assert len(resources.resources) == 2

    anyio.run(scenario)

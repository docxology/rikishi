import json
import os
import subprocess
import sys

import anyio
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from rikishi.ontology import OntologyIndex


@pytest.fixture
def analysis_root(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "Merge.kif").write_text(
        "(subclass Human Animal)\n(subclass Animal Entity)\n"
        "(subclass Human Animal)\n"
        '(documentation Human EnglishLanguage "A human; 100% literal.")\n'
    )
    (source / "Other.kif").write_text(
        "(subrelation teaches relates)\n(=> (instance ?X Human) (instance ?X Animal))\n"
    )
    OntologyIndex(tmp_path / ".rikishi/ontology.sqlite").build(source)
    return tmp_path


def invoke(root, *arguments):
    return subprocess.run(
        [sys.executable, "-m", "rikishi", "--root", str(root), *arguments],
        capture_output=True, text=True, check=False, timeout=20,
    )


@pytest.mark.parametrize("arguments", [
    ("files", "--path", "Merge", "--limit", "1"),
    ("formulas", "--head", "subclass", "--term", "Human", "--limit", "1"),
    ("relations",),
    ("taxonomy", "--relation", "subclass"),
    ("taxonomy-path", "Human", "Entity"),
])
def test_analysis_cli_retains_source_population_and_evidence(analysis_root, arguments):
    result = invoke(analysis_root, *arguments)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["provenance"] == {"source_commit": "unversioned", "source_clean": None}
    match arguments[0]:
        case "files":
            assert payload["total"] == 2
            assert payload["filtered_total"] == 1
            assert payload["items"][0]["path"] == "Merge.kif"
            assert len(payload["items"][0]["sha256"]) == 64
        case "formulas":
            assert payload["total"] == 6
            assert payload["filtered_total"] == 2
            assert payload["has_more"] is True
            assert payload["items"][0]["text"] == "(subclass Human Animal)"
            assert payload["items"][0]["line"] == 1
        case "relations":
            rows = {row["relation"]: row for row in payload["items"]}
            assert rows["subclass"]["assertion_count"] == 3
            assert rows["subclass"]["unique_edges"] == 2
        case "taxonomy":
            assert payload["node_count"] == 3
            assert payload["root_count"] == 1
            assert payload["cyclic_node_count"] == 0
        case "taxonomy-path":
            assert payload["status"] == "found"
            assert payload["nodes"] == ["Human", "Animal", "Entity"]
            assert [edge["formula"]["line"] for edge in payload["edges"]] == [1, 2]


@pytest.mark.parametrize("arguments", [
    ("files", "--limit", "0"),
    ("formulas", "--text", "\t"),
    ("taxonomy", "--offset", "-1"),
    ("taxonomy-path", "Human", "Entity", "--max-visited", "0"),
])
def test_invalid_analysis_cli_parameters_fail_explicitly(analysis_root, arguments):
    result = invoke(analysis_root, *arguments)
    assert result.returncode == 1, result.stderr
    assert json.loads(result.stderr)["error"] == "QueryError"
    assert result.stdout == ""


def test_analysis_tools_through_actual_mcp_transport(analysis_root):
    async def scenario():
        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-m", "rikishi", "--root", str(analysis_root), "mcp"],
            env=dict(os.environ),
        )
        with anyio.fail_after(30):
            async with (stdio_client(parameters) as (reader, writer),
                        ClientSession(reader, writer) as session):
                await session.initialize()
                names = {tool.name for tool in (await session.list_tools()).tools}
                assert {"corpus_files", "formula_search", "relation_inventory",
                        "taxonomy_analysis", "taxonomy_path"} <= names
                cases = [
                    ("corpus_files", {"path": "Other"}, "filtered_total", 1),
                    ("formula_search", {"text": "100%"}, "filtered_total", 1),
                    ("relation_inventory", {}, "unique_edges", 3),
                    ("taxonomy_analysis", {}, "node_count", 3),
                    ("taxonomy_path", {"source": "Human", "target": "Entity"}, "status", "found"),
                ]
                for name, arguments, key, expected in cases:
                    result = await session.call_tool(name, arguments)
                    assert result.isError is False, result.content
                    assert json.loads(result.content[0].text)[key] == expected
                invalid = await session.call_tool("corpus_files", {"limit": 0})
                assert invalid.isError is True
                missing = await session.call_tool("taxonomy_path", {
                    "source": "Entity", "target": "Human", "max_depth": 1,
                })
                assert json.loads(missing.content[0].text)["status"] == "not_found"

    anyio.run(scenario)

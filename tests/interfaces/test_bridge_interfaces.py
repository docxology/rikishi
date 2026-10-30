import json
from fractions import Fraction
from hashlib import sha256

import anyio
import pytest
from fastapi.testclient import TestClient
from mcp.server.fastmcp.exceptions import ToolError

from rikishi.bridge_study import catalog
from rikishi.bridge_views import inspect_case, inspect_report
from rikishi.cli import main
from rikishi.dashboard import create_app
from rikishi.inference_views import CaseSelection
from rikishi.mcp_server import create_server
from rikishi.ontology import OntologyIndex


@pytest.fixture
def bridge_view_root(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "Merge.kif").write_text("(subclass Human Animal)\n")
    OntologyIndex(tmp_path / ".rikishi/ontology.sqlite").build(source)
    return tmp_path


def test_bridge_catalog_agrees_across_cli_http_and_mcp(bridge_view_root, capsys):
    expected = catalog().model_dump(mode="json")
    assert main(["--root", str(bridge_view_root), "bridge-catalog"]) == 0
    assert json.loads(capsys.readouterr().out) == expected
    with TestClient(create_app(bridge_view_root / ".rikishi/ontology.sqlite")) as client:
        assert client.get("/api/bridge/catalog").json() == expected
    server = create_server(bridge_view_root)

    async def check():
        _, structured = await server.call_tool("bridge_catalog", {})
        assert structured == expected

    anyio.run(check)


@pytest.mark.parametrize("digest", ["", "f" * 63, "F" * 64, "invalid"])
def test_bridge_inspection_requires_a_well_formed_digest(bridge_view_root, digest):
    with pytest.raises(ValueError, match="64 lowercase"):
        inspect_report(bridge_view_root, "missing.json", digest)


@pytest.mark.parametrize("route", ["report", "explorer"])
@pytest.mark.parametrize("relative,status", [
    ("missing.json", 404), ("../outside.json", 422), ("/absolute.json", 422),
])
def test_bridge_http_rejects_missing_and_escaping_reports(bridge_view_root, route, relative, status):
    with TestClient(create_app(bridge_view_root / ".rikishi/ontology.sqlite")) as client:
        response = client.get(f"/api/bridge/{route}", params={"report": relative, "sha256": "0" * 64})
        assert response.status_code == status


def test_bridge_http_rejects_report_aliases(bridge_view_root):
    target = bridge_view_root / "packet.json"
    target.write_text("{}")
    (bridge_view_root / "alias.json").symlink_to(target)
    with TestClient(create_app(bridge_view_root / ".rikishi/ontology.sqlite")) as client:
        assert client.get("/api/bridge/report", params={
            "report": "alias.json", "sha256": "0" * 64,
        }).status_code == 422


@pytest.mark.parametrize("command", ["bridge-verify", "bridge-case", "bridge-figures"])
def test_bridge_cli_refuses_missing_digest(command):
    arguments = [command, "report.json"]
    if command == "bridge-case":
        arguments.append("case-id")
    if command == "bridge-figures":
        arguments.append("new-figures")
    with pytest.raises(SystemExit) as error:
        main(arguments)
    assert error.value.code == 2


@pytest.mark.integration
def test_verified_bridge_packet_crosses_cli_http_and_mcp(bridge_packet, capsys):
    root, path, digest, report = (bridge_packet.root, bridge_packet.path,
                                  bridge_packet.sha256, bridge_packet.report)
    relative = str(path.relative_to(root))
    assert main(["--root", str(root), "bridge-verify", relative, "--sha256", digest]) == 0
    assert json.loads(capsys.readouterr().out) == report.model_dump(mode="json")
    run = next(case for case in report.cases if case.prover == "e" and case.kind == "positive")
    expected = inspect_case(root, CaseSelection(relative, digest, run.id, "e"))
    assert main(["--root", str(root), "bridge-case", relative, run.id,
                 "--prover", "e", "--sha256", digest]) == 0
    assert json.loads(capsys.readouterr().out) == expected.model_dump(mode="json")
    parameters = {"report": relative, "sha256": digest}
    with TestClient(create_app(root / ".rikishi/ontology.sqlite")) as client:
        assert client.get("/api/bridge/report", params=parameters).json() == report.model_dump(mode="json")
        assert client.get("/api/bridge/case", params={**parameters, "case_id": run.id}).json() == expected.model_dump(mode="json")
        assert client.get("/api/bridge/case", params={**parameters, "case_id": "missing"}).status_code == 404
        assert client.get("/api/bridge/report", params={**parameters, "sha256": "0" * 64}).status_code == 422
        assert client.get("/api/bridge/case", params={**parameters, "case_id": run.id, "prover": "invalid"}).status_code == 422
        explorer = client.get("/api/bridge/explorer", params=parameters)
        assert explorer.status_code == 200
        assert explorer.headers["x-content-type-options"] == "nosniff"
        assert "text/html" in explorer.headers["content-type"]
        assert digest in explorer.text
        assert "Content-Security-Policy" in explorer.text
        assert all(witness.id in explorer.text for witness in report.witnesses)
        assert all(control.source in explorer.text for control in report.lean.controls)
        assert all(environment.source in explorer.text for environment in report.lean.environments)
        assert client.get("/api/bridge/explorer", params={**parameters, "sha256": "0" * 64}).status_code == 422
    server = create_server(root)

    async def check():
        _, structured = await server.call_tool("bridge_verify_report", parameters)
        assert structured == report.model_dump(mode="json")
        _, case = await server.call_tool("bridge_inspect_case", {**parameters, "case_id": run.id})
        assert case == expected.model_dump(mode="json")
        with pytest.raises(ToolError):
            await server.call_tool("bridge_verify_report", {**parameters, "sha256": "0" * 64})

    anyio.run(check)


@pytest.mark.integration
@pytest.mark.parametrize("kind", ["background", "positive", "negative", "removed-premise", "refutation"])
@pytest.mark.parametrize("prover", ["e", "v"])
def test_case_inspection_joins_actual_source_and_the_same_finite_witness(bridge_packet, kind, prover):
    report = bridge_packet.report
    run = next(case for case in report.cases if case.kind == kind and case.prover == prover)
    relative = str(bridge_packet.path.relative_to(bridge_packet.root))
    view = inspect_case(bridge_packet.root, CaseSelection(relative, bridge_packet.sha256, run.id, prover))
    assert view.scenario.id == run.group
    assert view.witness.id == view.scenario.witness_id == view.numerical.witness_id
    prior = tuple(Fraction(value) for value in view.witness.prior)
    likelihood = tuple(Fraction(value) for value in view.witness.likelihood)
    masses = tuple(p * l for p, l in zip(prior, likelihood, strict=True))
    assert tuple(Fraction(value) for value in view.numerical.exact_posterior) == tuple(value / sum(masses) for value in masses)
    assert sha256(view.lean_source.encode()).hexdigest() == report.lean.source_sha256
    assert all(view.witness.namespace in name.split(".") for name in view.lean_declarations)
    assert any(name.endswith(".posterior_reconstruction") for name in view.lean_declarations)
    assert {claim.line for claim in view.source_claims} == {item.line for item in view.scenario.selections}
    assert f"SZS status {run.observed}" in view.stdout
    assert sha256(view.problem.encode()).hexdigest() == run.problem_sha256

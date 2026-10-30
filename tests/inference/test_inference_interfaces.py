import json
import shutil
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

import anyio
import pytest
from fastapi.testclient import TestClient

from rikishi.cli import main
from rikishi.dashboard import create_app
from rikishi.inference_study import catalog
from rikishi.inference_views import (
    CaseSelection,
    inspect_case,
    inspect_report,
    publish_report,
    published_report,
    report_path,
)
from rikishi.manuscript_provenance import ProvenanceError
from rikishi.mcp_server import create_server
from rikishi.ontology import OntologyIndex
from rikishi.publication_inference import load_inference_context, verify_inference_content


@pytest.fixture
def view_root(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "Merge.kif").write_text("(subclass Human Animal)")
    OntologyIndex(tmp_path / ".rikishi/ontology.sqlite").build(source)
    return tmp_path


def test_catalog_uses_shared_authority_in_cli_http_and_mcp(view_root, capsys):
    expected = catalog().model_dump(mode="json")
    assert main(["--root", str(view_root), "inference-catalog"]) == 0
    assert json.loads(capsys.readouterr().out) == expected
    with TestClient(create_app(view_root / ".rikishi/ontology.sqlite")) as client:
        assert client.get("/api/inference/catalog").json() == expected
        assert client.get("/api/inference/published").status_code == 404
        assert client.get("/api/inference/report", params={"report": "missing", "sha256": "0" * 64}).status_code == 404
        assert client.get("/api/inference/report", params={"report": "x", "sha256": "bad"}).status_code == 422
    server = create_server(view_root)

    async def scenario():
        result = await server.call_tool("inference_catalog", {})
        payload = result[1] if isinstance(result, tuple) else json.loads(result[0].text)
        assert payload == expected

    anyio.run(scenario)


@pytest.mark.parametrize("relative", ["", " ", "../escape", "/absolute"])
def test_report_paths_reject_escaping_and_empty_values(view_root, relative):
    with pytest.raises(ValueError, match="repository-relative"):
        report_path(view_root, relative)


def test_report_symlinks_and_bad_digests_fail(view_root):
    target = view_root / "report.json"
    target.write_text("{}")
    (view_root / "alias.json").symlink_to(target)
    with pytest.raises(ValueError, match="symlink"):
        report_path(view_root, "alias.json")
    for digest in ("", "0" * 63, "Z" * 64):
        with pytest.raises(ValueError, match="64 lowercase"):
            inspect_report(view_root, "report.json", digest)
    with TestClient(create_app(view_root / ".rikishi/ontology.sqlite")) as client:
        assert client.get("/api/inference/report", params={"report": "alias.json", "sha256": "0" * 64}).status_code == 422


@pytest.mark.parametrize("payload", [{}, {"report": 1, "sha256": "0" * 64}, {"report": "x", "sha256": "0" * 64, "extra": True}])
def test_published_descriptor_is_strict(view_root, payload):
    path = view_root / "output/inference/published.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="descriptor"):
        published_report(view_root)
    with TestClient(create_app(view_root / ".rikishi/ontology.sqlite")) as client:
        assert client.get("/api/inference/published").status_code == 422


@pytest.fixture(scope="module")
def native_campaign():
    from rikishi.inference_replay import validate_inference_report

    root = Path(__file__).resolve().parents[2]
    parent = root / ".rikishi/results" / ("inference-interface-" + uuid4().hex)
    parent.mkdir()
    output = parent / "campaign"
    assert main(["--root", str(root), "inference-run", str(output), "--prover", "both", "--timeout", "60"]) == 0
    path = output / "inference-report.json"
    report = validate_inference_report(path, trusted_report_sha256=sha256(path.read_bytes()).hexdigest())
    assert report.summary.passed
    assert main(["--root", str(root), "inference-run", str(output)]) == 1
    return root, output


@pytest.mark.integration
def test_native_report_crosses_cli_http_mcp_and_publication(native_campaign, view_root, capsys):
    root, directory = native_campaign
    report = directory / "inference-report.json"
    digest = sha256(report.read_bytes()).hexdigest()
    relative = str(report.relative_to(root))
    assert main(["--root", str(root), "inference-verify", relative, "--sha256", digest]) == 0
    cli = json.loads(capsys.readouterr().out)
    case_id = cli["cases"][0]["id"]
    captured = inspect_case(root, CaseSelection(relative, digest, case_id, "e"))
    assert captured["case"] == cli["cases"][0]
    assert "fof(premise_" in captured["problem"]
    assert "SZS status Satisfiable" in captured["stdout"]
    with TestClient(create_app(root / ".rikishi/ontology.sqlite")) as client:
        response = client.get("/api/inference/report", params={"report": relative, "sha256": digest})
        assert response.status_code == 200
        assert response.json() == cli
        rejected = client.get("/api/inference/report", params={"report": relative, "sha256": "0" * 64})
        assert rejected.status_code == 422
        parameters = {"report": relative, "sha256": digest, "case_id": case_id, "prover": "e"}
        assert client.get("/api/inference/case", params=parameters).json() == captured
        assert client.get("/api/inference/case", params={**parameters, "case_id": "missing"}).status_code == 404
        assert client.get("/api/inference/case", params={**parameters, "sha256": "0" * 64}).status_code == 422
    server = create_server(root)

    async def scenario():
        result = await server.call_tool("inference_verify_report", {"report": relative, "sha256": digest})
        payload = result[1] if isinstance(result, tuple) else json.loads(result[0].text)
        assert payload == cli
        case = await server.call_tool("inference_inspect_case", {
            "report": relative, "sha256": digest, "case_id": case_id, "prover": "e"})
        case_payload = case[1] if isinstance(case, tuple) else json.loads(case[0].text)
        assert case_payload == captured

    anyio.run(scenario)
    copied = view_root / "output/inference"
    shutil.copytree(directory, copied)
    arguments = ["--root", str(view_root), "inference-publish", "output/inference/inference-report.json", "--sha256", digest]
    assert main(arguments) == 0
    descriptor = json.loads(capsys.readouterr().out)
    assert descriptor == {"report": "output/inference/inference-report.json", "sha256": digest}
    assert publish_report(view_root, descriptor["report"], digest) == descriptor
    prior = copied / "published.json"
    prior.write_text("{}")
    assert main(arguments) == 0
    capsys.readouterr()
    assert [item.read_text() for item in copied.glob("published-before-*.json")] == ["{}"]
    prior.unlink()
    prior.symlink_to(copied / "inference-report.json")
    with pytest.raises(ValueError, match="symlink"):
        publish_report(view_root, descriptor["report"], digest)
    prior.unlink()
    assert main(arguments) == 0
    capsys.readouterr()
    assert published_report(view_root)["report"] == cli
    with TestClient(create_app(view_root / ".rikishi/ontology.sqlite")) as client:
        assert client.get("/api/inference/published").json()["report"] == cli
    context = load_inference_context(directory)
    assert int(context.values["INFERENCE_SCENARIOS"]) == len(catalog().scenarios)
    table = context.values["INFERENCE_SUMMARY_TABLE"]
    rendered = " ".join(" ".join(cell.strip() for cell in row.strip("|").split("|")) for row in table.splitlines()[2:])
    verify_inference_content(rendered, context, "real table cells")
    with pytest.raises(ProvenanceError, match="result row missing"):
        verify_inference_content("altered result table", context, "mutated table")

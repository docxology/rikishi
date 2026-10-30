import json
import shutil
import subprocess
from html.parser import HTMLParser
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from rikishi.dashboard import create_app
from rikishi.ontology import OntologyIndex
from rikishi.reports import build_report


@pytest.fixture
def database(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "sample.kif").write_text(
        "(subclass Human Agent)\n(subclass Agent Entity)\n"
        '(documentation Human EnglishLanguage "A human agent.")\n',
        encoding="utf-8",
    )
    path = tmp_path / "index.sqlite"
    OntologyIndex(path).build(source)
    return path


def test_live_dashboard_and_api(database):
    with TestClient(create_app(database)) as client:
        page = client.get("/")
        assert page.status_code == 200
        assert "Ontology explorer" in page.text
        for asset in ("style.css", "app.js", "analytics.js"):
            response = client.get("/static/" + asset)
            assert response.status_code == 200
            assert len(response.content) > 500
        assert client.get("/api/stats").json()["formulas"] == 3
        measured = client.get("/api/analytics")
        assert measured.status_code == 200
        assert measured.json()["formula_denominator"] == 3
        assert measured.json()["unique_edges"] == 2
        result = client.get("/api/search", params={"q": "Human"}).json()
        assert result[0]["name"] == "Human"
        assert client.get("/api/search", params={"q": "NoSuchTerm"}).json() == []
        term = client.get("/api/terms/Human").json()
        assert term["documentation"][0]["text"] == "A human agent."
        assert term["formulas"][0]["line"] == 1
        assert term["formulas"][0]["path"] == "sample.kif"
        graph = client.get("/api/graph", params={"term": "Human"}).json()
        assert graph["edges"] == [{"source": "Human", "target": "Agent", "relation": "subclass"}]
        assert graph["total_edges"] == graph["returned_edges"] == 1
        assert graph["truncated"] is False
        assert graph["relations"] == [{"relation": "subclass", "count": 1}]
        assert client.get("/docs").status_code == 200
        optimum = client.get("/api/fep?q=0.8").json()
        assert optimum["result"]["kl_to_posterior"] == pytest.approx(0)
        assert (
            client.get("/api/fep?q=0").json()["result"]["free_energy"]
            > optimum["result"]["free_energy"]
        )


@pytest.mark.parametrize("url", ["/api/terms/Missing", "/api/graph?term=Missing"])
def test_missing_terms_are_explicit_404(database, url):
    with TestClient(create_app(database)) as client:
        response = client.get(url)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


@pytest.mark.parametrize(
    "url",
    [
        "/api/search?q=",
        "/api/search?q=x&limit=0",
        "/api/graph?term=Human&limit=101",
        "/api/graph?term=",
        "/api/graph?term=Human&relation=",
        "/api/graph?term=Human&relation=" + "x" * 201,
        "/api/fep?q=1.1",
        "/api/fep?q=nan",
    ],
)
def test_invalid_queries_fail_validation(database, url):
    with TestClient(create_app(database)) as client:
        assert client.get(url).status_code == 422


@pytest.mark.parametrize("relation", [" ", "\t", "\r\n", " \t\n", "\u00a0", "\u001c"])
def test_blank_relation_filters_are_client_errors(database, relation):
    with TestClient(create_app(database), raise_server_exceptions=False) as client:
        response = client.get("/api/graph", params={"term": "Human", "relation": relation})
        assert response.status_code == 422
        assert response.json()["detail"] == "relation must be nonempty when supplied"


def test_missing_database_does_not_create_one(tmp_path):
    missing = tmp_path / "absent.sqlite"
    with pytest.raises(FileNotFoundError, match="Build the ontology index first"):
        create_app(missing)
    assert not missing.exists()


def test_report_contains_real_counts_and_figures(database, tmp_path):
    artifacts = build_report(database, tmp_path / "report")
    assert set(artifacts) == {
        "html",
        "data",
        "svg",
        "png",
        "analytics",
        "summary",
        "composition_svg",
        "composition_png",
    }
    for artifact in artifacts.values():
        assert Path(artifact).stat().st_size > 50
    data = json.loads(Path(artifacts["data"]).read_text())
    assert data["formulas"] == 3
    assert data["files"] == 1
    html = Path(artifacts["html"]).read_text()
    assert "__DATA__" not in html
    assert "__STYLE__" not in html
    assert "__ANALYTICS" not in html
    assert "Composition and connectivity" in html
    assert json.loads(Path(artifacts["analytics"]).read_text())["unique_edges"] == 2
    assert '"formulas": 3' in html
    assert 'src="http' not in html
    assert Path(artifacts["png"]).read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert "<svg" in Path(artifacts["svg"]).read_text()


def test_report_escapes_embedded_markup(tmp_path):
    source = tmp_path / "<script>"
    source.mkdir()
    (source / "fixture.kif").write_text("(subclass A B)", encoding="utf-8")
    database = tmp_path / "index.sqlite"
    OntologyIndex(database).build(source)
    artifacts = build_report(database, tmp_path / "report")
    html = Path(artifacts["html"]).read_text()
    embedded = html.split('<script id="data" type="application/json">')[1].split("</script>")[0]
    assert "<script>" not in embedded
    assert "\\u003cscript>" in embedded
    assert json.loads(embedded)["source_root"] == str(source)


def test_relation_filter_applies_before_budget_and_retains_inventory(tmp_path, corpus_factory):
    index = corpus_factory(tmp_path, {"one.kif": (
        "(disjoint Human Mineral)\n(subclass Human Animal)\n(subclass Human Animal)\n"
        "(subclass Child Human)\n(instance Human Species)"
    )})
    with TestClient(create_app(index.path)) as client:
        all_edges = client.get("/api/graph", params={"term": "Human", "limit": 1}).json()
        assert all_edges["total_edges"] == 4
        assert all_edges["returned_edges"] == 1
        assert all_edges["truncated"] is True
        assert all_edges["edges"][0]["relation"] == "disjoint"
        filtered = client.get("/api/graph", params={"term": "Human", "limit": 1, "relation": "subclass"}).json()
        assert filtered["total_edges"] == 2
        assert filtered["returned_edges"] == 1
        assert filtered["truncated"] is True
        assert filtered["edges"] == [{"source": "Child", "target": "Human", "relation": "subclass"}]
        assert filtered["relations"] == all_edges["relations"]
        complete = client.get("/api/graph", params={"term": "Human", "limit": 2, "relation": "subclass"}).json()
        assert complete["truncated"] is False
        assert complete["returned_edges"] == complete["total_edges"] == 2
        absent = client.get("/api/graph", params={"term": "Human", "relation": "absent"}).json()
        assert absent["edges"] == []
        assert absent["nodes"] == [{"id": "Human", "label": "Human"}]
        assert absent["total_edges"] == absent["returned_edges"] == 0
        assert absent["truncated"] is False
        assert absent["relations"] == all_edges["relations"]


class ScriptBlocks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.blocks = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self.current = {"attributes": dict(attrs), "text": ""}

    def handle_data(self, data):
        if self.current is not None:
            self.current["text"] += data

    def handle_endtag(self, tag):
        if tag == "script" and self.current is not None:
            self.blocks.append(self.current)
            self.current = None


def test_report_tokens_in_source_labels_remain_literal_data(tmp_path):
    source = tmp_path / "__ANALYTICS____ANALYTICS_JS____REPORT_JS____STYLE__<script>"
    source.mkdir()
    (source / "<img onerror=alert(1)>.kif").write_text(
        "(__DATA__ A B)\n(__ANALYTICS__ B C)\n(__REPORT_JS__ C D)", encoding="utf-8"
    )
    database = tmp_path / "index.sqlite"
    index = OntologyIndex(database)
    index.build(source)
    artifacts = build_report(database, tmp_path / "report")
    parsed = ScriptBlocks()
    parsed.feed(Path(artifacts["html"]).read_text())
    embedded = {block["attributes"].get("id"): block["text"] for block in parsed.blocks}
    assert json.loads(embedded["data"]) == index.stats()
    assert json.loads(embedded["analytics-data"]) == json.loads(Path(artifacts["analytics"]).read_text())
    assert "<img" not in embedded["data"]
    assert "<script>" not in embedded["data"]
    assert "renderFileDistribution" in embedded[None]


@pytest.mark.integration
def test_static_and_embedded_javascript_compile_with_rejecting_control(database, tmp_path):
    node = shutil.which("node")
    assert node is not None, "Native JS verification requires Node.js"
    static = Path(__file__).resolve().parents[2] / "src" / "rikishi" / "static"
    paths = list(static.glob("*.js"))
    artifacts = build_report(database, tmp_path / "report")
    parsed = ScriptBlocks()
    parsed.feed(Path(artifacts["html"]).read_text())
    for number, block in enumerate(parsed.blocks):
        assert "src" not in block["attributes"], "Portable HTML must embed every script"
        if block["attributes"].get("type") == "application/json":
            json.loads(block["text"])
        else:
            path = tmp_path / f"inline-{number}.js"
            path.write_text(block["text"], encoding="utf-8")
            paths.append(path)
    for path in paths:
        result = subprocess.run([node, "--check", str(path)], check=False, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
    broken = tmp_path / "invalid.js"
    broken.write_text("const = ;", encoding="utf-8")
    rejected = subprocess.run([node, "--check", str(broken)], check=False, capture_output=True, text=True)
    assert rejected.returncode != 0
    assert "SyntaxError" in rejected.stderr

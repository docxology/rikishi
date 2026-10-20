import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from rikishi.dashboard import build_report, create_app
from rikishi.ontology import OntologyIndex


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
        for asset in ("style.css", "app.js"):
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
        "/api/fep?q=1.1",
        "/api/fep?q=nan",
    ],
)
def test_invalid_queries_fail_validation(database, url):
    with TestClient(create_app(database)) as client:
        assert client.get(url).status_code == 422


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

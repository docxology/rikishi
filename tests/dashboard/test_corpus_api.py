import hashlib

import pytest
from fastapi.testclient import TestClient

from rikishi.dashboard import create_app


@pytest.fixture
def indexed(corpus_factory, tmp_path):
    return corpus_factory(tmp_path, {
        "literal%_.kif": "(subclass Child Parent)\n(subclass Parent Root)\n"
        "(subclass Child Parent)\n(subclass Sibling Parent)\n",
        "other.kif": '(documentation Child EnglishLanguage "Literal <script>_100%</script>")\n'
        "(subrelation related connected)\n",
    })


def test_files_and_formulas_page_the_complete_filtered_population(indexed):
    before = hashlib.sha256(indexed.path.read_bytes()).hexdigest()
    with TestClient(create_app(indexed.path)) as client:
        files = client.get("/api/corpus/files", params={"path": "%_", "limit": 1}).json()
        assert files["total"] == 2
        assert files["filtered_total"] == files["returned"] == 1
        assert files["total_formulas"] == 6
        assert files["filtered_formulas"] == 4
        assert files["items"][0]["path"] == "literal%_.kif"
        assert len(files["items"][0]["sha256"]) == 64
        assert files["has_more"] is False
        assert files["provenance"]["source_clean"] is None
        sorted_files = client.get("/api/corpus/files", params={
            "sort": "formulas", "descending": True, "limit": 1,
        }).json()
        assert sorted_files["items"][0]["formulas"] == 4
        assert sorted_files["has_more"] is sorted_files["truncated"] is True
        formulas = client.get("/api/corpus/formulas", params={
            "head": "subclass", "term": "Child", "limit": 1,
        }).json()
        assert formulas["total"] == 6
        assert formulas["filtered_total"] == 2
        assert formulas["returned"] == 1
        assert formulas["has_more"] is formulas["truncated"] is True
        assert formulas["items"][0]["text"] == "(subclass Child Parent)"
        assert formulas["items"][0]["line"] == 1
        assert len(formulas["items"][0]["source_sha256"]) == 64
        second = client.get("/api/corpus/formulas", params={
            "head": "subclass", "term": "Child", "limit": 1, "offset": 1,
        }).json()
        assert second["items"][0]["line"] == 3
        assert second["has_more"] is False
        assert second["truncated"] is True
        assert client.get("/api/corpus/formulas", params={"text": "child"}).json()[
            "filtered_total"
        ] == 0
        literal = client.get("/api/corpus/formulas", params={"text": "_100%"}).json()
        assert literal["filtered_total"] == 1
        assert "<script>" in literal["items"][0]["text"]
        assert client.get("/api/corpus/formulas", params={"path": "literal"}).json()[
            "filtered_total"
        ] == 0
    assert hashlib.sha256(indexed.path.read_bytes()).hexdigest() == before


def test_relation_diagnostics_and_source_paths(indexed):
    with TestClient(create_app(indexed.path)) as client:
        relations = client.get("/api/corpus/relations").json()
        subclass = next(row for row in relations["items"] if row["relation"] == "subclass")
        assert subclass == {
            "relation": "subclass", "assertion_count": 4, "unique_edges": 3,
            "duplicate_assertions": 1, "node_count": 4,
        }
        taxonomy = client.get("/api/taxonomy", params={"limit": 1}).json()
        assert taxonomy["node_count"] == 4
        assert taxonomy["root_count"] == 1
        assert taxonomy["returned"] == 1
        assert taxonomy["has_more"] is True
        route = client.get("/api/taxonomy/path", params={
            "source": "Child", "target": "Root",
        }).json()
        assert route["status"] == "found"
        assert route["nodes"] == ["Child", "Parent", "Root"]
        assert route["edges"][0]["formula"]["line"] == 1
        assert route["edges"][0]["formula"]["path"] == "literal%_.kif"
        bounded = client.get("/api/taxonomy/path", params={
            "source": "Child", "target": "Root", "max_depth": 0,
        }).json()
        assert bounded["status"] == "max_depth"
        assert bounded["edges"] == []
        assert client.get("/api/taxonomy/path", params={
            "source": "Missing", "target": "Root",
        }).status_code == 404


@pytest.mark.parametrize("route,params", [
    ("files", {"limit": 0}), ("files", {"offset": -1}),
    ("files", {"sort": "DROP TABLE files"}), ("files", {"path": " "}),
    ("formulas", {"term": "\x00"}), ("formulas", {"head": "\t"}),
    ("formulas", {"limit": 501}), ("formulas", {"offset": 1_000_001}),
])
def test_query_transport_rejects_invalid_controls(indexed, route, params):
    with TestClient(create_app(indexed.path), raise_server_exceptions=False) as client:
        response = client.get("/api/corpus/" + route, params=params)
        assert response.status_code == 422
        assert response.json()["detail"]


@pytest.mark.parametrize("route,params", [
    ("/api/taxonomy", {"relation": "instance"}),
    ("/api/taxonomy", {"path": "\x00"}),
    ("/api/taxonomy/path", {"source": " ", "target": "Root"}),
    ("/api/taxonomy/path", {"source": "Child", "target": "Root", "max_visited": 0}),
])
def test_taxonomy_transport_rejects_invalid_controls(indexed, route, params):
    with TestClient(create_app(indexed.path), raise_server_exceptions=False) as client:
        assert client.get(route, params=params).status_code == 422


def test_empty_corpus_retains_defined_totals(corpus_factory, tmp_path):
    index = corpus_factory(tmp_path, {"empty.kif": "; no formulas\n"})
    with TestClient(create_app(index.path)) as client:
        files = client.get("/api/corpus/files").json()
        assert files["total_formulas"] == files["filtered_formulas"] == 0
        assert files["items"][0]["formulas"] == 0
        for route in ("/api/corpus/formulas", "/api/taxonomy"):
            data = client.get(route).json()
            assert data["items"] == []
            assert data["total"] == data["filtered_total"] == data["returned"] == 0
            assert data["has_more"] is data["truncated"] is False
        assert client.get("/api/corpus/relations").json()["items"] == []

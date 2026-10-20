import json
import sqlite3
import subprocess

import pytest

from rikishi.ontology import OntologyIndex


@pytest.fixture
def index(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "Merge.kif").write_text(
        "(subclass Human Animal)\n(subclass Animal Entity)\n(instance Ada Human)\n"
        '(documentation Human EnglishLanguage "A human being")\n'
        "(forall (?X) (=> (instance ?X Human) (instance ?X Animal)))\n"
        "((PredicateFn Human) Animal)\n(domain agent 1 Process)\n"
        '(documentation Human FrenchLanguage "Un humain")\n(instance ?X Human)\n'
    )
    (source / "nested").mkdir()
    (source / "nested/domain.kif").write_text("(disjoint Human Rock)\n(instance Ada Human)")
    result = OntologyIndex(tmp_path / "index.sqlite")
    result.build(source)
    return result


def test_corpus_counts_and_relations(index):
    stats = index.stats()
    assert (stats["files"], stats["formulas"], stats["edges"]) == (2, 11, 5)
    assert stats["source_commit"] == "unversioned"
    assert stats["parse_errors"] == []
    assert stats["top_files"][0] == {"path": "Merge.kif", "formulas": 9}
    assert {r["predicate"] for r in stats["top_predicates"]} >= {"subclass", "forall", "<compound>"}


def test_search_term_and_graph_keep_provenance(index):
    assert index.search("huma")[0]["name"] == "Human"
    assert index.search("") == []
    assert index.search("%") == []
    assert index.search("'") == []
    assert index.search("_") == []
    human = index.term("Human")
    assert human["formula_count"] == 9
    assert human["parents"] == [{"name": "Animal", "relation": "subclass"}]
    assert human["children"] == [{"name": "Ada", "relation": "instance"}]
    assert human["documentation"][0]["path"] == "Merge.kif"
    assert human["documentation"][0]["line"] == 4
    assert human["formulas"][0]["text"] == "(subclass Human Animal)"
    graph = index.neighborhood("Human", limit=1)
    assert len(graph["edges"]) == 1
    assert "Human" in {r["id"] for r in graph["nodes"]}


@pytest.mark.parametrize(
    "method,args",
    [
        ("search", ("x", 0)),
        ("search", ("x", 201)),
        ("neighborhood", ("Human", 0)),
        ("neighborhood", ("Human", 501)),
    ],
)
def test_bounds_rejected(index, method, args):
    with pytest.raises(ValueError):
        getattr(index, method)(*args)


@pytest.mark.parametrize("method", ["term", "neighborhood"])
def test_missing_term_is_error(index, method):
    with pytest.raises(KeyError):
        getattr(index, method)("NotInOntology")


def test_missing_index_and_source_are_explicit(tmp_path):
    index = OntologyIndex(tmp_path / "missing.sqlite")
    with pytest.raises(FileNotFoundError):
        index.stats()
    with pytest.raises(FileNotFoundError):
        index.build(tmp_path / "missing-source")
    assert not index.path.exists()


def test_malformed_file_report_does_not_publish_partial_formulas(tmp_path):
    source = tmp_path / "kif"
    source.mkdir()
    (source / "good.kif").write_text("(instance Ada Human)")
    (source / "broken.kif").write_text("(instance Bob Human) (unclosed")
    (source / "encoding.kif").write_bytes(b"\xff")
    index = OntologyIndex(tmp_path / "db.sqlite")
    stats = index.build(source)
    assert stats["files"] == 1
    assert stats["formulas"] == 1
    assert {e["path"] for e in stats["parse_errors"]} == {"broken.kif", "encoding.kif"}
    assert stats["discovered_files"] == 3
    assert index.search("Bob") == []
    (source / "good.kif").write_text("(instance Carl Human)")
    index.build(source)
    assert index.search("Ada") == []
    assert index.search("Carl")[0]["name"] == "Carl"
    assert list(tmp_path.glob("index-*.sqlite")) == []


def test_export_has_hashes_and_no_local_root(index, tmp_path):
    data = index.export(tmp_path / "export")
    assert "source_root" not in data
    manifest = json.loads((tmp_path / "export/source-manifest.json").read_text())
    assert len(manifest) == 2
    assert len(manifest[0]["sha256"]) == 64
    with sqlite3.connect(index.path) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_git_provenance_dirty_and_atomic_failure(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    kif = source / "Merge.kif"
    kif.write_text("(instance Ada Human)")
    subprocess.run(["git", "init", str(source)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(source), "add", "Merge.kif"], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(source),
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-m",
            "Fixture",
        ],
        check=True,
        capture_output=True,
    )
    index = OntologyIndex(tmp_path / "index.sqlite")
    stats = index.build(source)
    assert stats["source_clean"] is True
    assert len(stats["source_commit"]) == 40
    kif.write_text("(instance Grace Human)")
    dirty = index.build(source)
    assert dirty["source_clean"] is False
    assert dirty["source_commit"] == stats["source_commit"]
    (source / ".git/HEAD").write_text("ref: refs/heads/nonexistent\n")
    with pytest.raises(subprocess.CalledProcessError):
        index.build(source)
    assert index.search("Grace")[0]["name"] == "Grace"
    assert list(tmp_path.glob("index-*.sqlite")) == []

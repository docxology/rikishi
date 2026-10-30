import hashlib

import pytest

from rikishi.corpus_query import FileQuery, FormulaQuery, QueryError


@pytest.fixture
def corpus(tmp_path, corpus_factory):
    return corpus_factory(tmp_path, {
        "a.kif": '; comment\n(subclass A B)\n(subclass A B)\n'
        '(documentation A EnglishLanguage "literal %_\\\\ marker")\n'
        '(forall (?X) (=> (instance ?X A) (instance ?X B)))',
        "nested/b_%.kif": "(subclass B Root)\n(subrelation related relation)",
        "empty.kif": "; empty",
        "rejected.kif": "(unclosed",
    })


def test_files_totals_hashes_sorting_and_paging(corpus):
    result = corpus.corpus_files(FileQuery(limit=1))
    assert (result["total"], result["filtered_total"], result["total_formulas"]) == (3, 3, 6)
    assert result["returned"] == 1
    assert result["has_more"] and result["truncated"]
    all_items = [corpus.corpus_files(FileQuery(limit=1, offset=n))["items"][0] for n in range(3)]
    assert [row["path"] for row in all_items] == ["a.kif", "empty.kif", "nested/b_%.kif"]
    for row in all_items:
        source = corpus.path.parent / "source" / row["path"]
        assert row["sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert corpus.corpus_files(FileQuery(sort="formulas", descending=True))["items"] == all_items[:1] + all_items[2:] + all_items[1:2]
    assert corpus.corpus_files(FileQuery(descending=True))["items"] == all_items[::-1]
    assert corpus.corpus_files(FileQuery(sort="formulas"))["items"][0]["path"] == "empty.kif"
    filtered = corpus.corpus_files(FileQuery(path="_%"))
    assert filtered["filtered_total"] == 1
    assert filtered["filtered_formulas"] == 2 and filtered["total_formulas"] == 6
    assert filtered["provenance"] == {"source_commit": "unversioned", "source_clean": None}
    beyond = corpus.corpus_files(FileQuery(offset=20))
    assert beyond["items"] == [] and not beyond["has_more"] and beyond["truncated"]
    assert corpus.corpus_files(FileQuery(path="missing"))["filtered_formulas"] == 0


def test_formula_search_is_literal_contextual_and_source_exact(corpus):
    result = corpus.formula_search(FormulaQuery(term="A", head="subclass", path="a.kif"))
    assert result["total"] == 6 and result["filtered_total"] == 2
    assert [r["line"] for r in result["items"]] == [2, 3]
    assert all(r["text"] == "(subclass A B)" for r in result["items"])
    assert result["items"][0]["source_sha256"] == corpus.source_manifest()[0]["sha256"]
    nested = corpus.formula_search(FormulaQuery(term="A", head="forall"))
    assert nested["filtered_total"] == 1
    assert nested["items"][0]["text"].startswith("(forall")
    assert corpus.formula_search(FormulaQuery(text="%_"))["filtered_total"] == 1
    assert corpus.formula_search(FormulaQuery(text="\\"))["filtered_total"] == 1
    assert corpus.formula_search(FormulaQuery(text="SUBCLASS"))["filtered_total"] == 0
    for hostile in ("' OR 1=1 --", "%", "../a.kif"):
        assert corpus.formula_search(FormulaQuery(head=hostile))["items"] == []
        assert corpus.formula_search(FormulaQuery(path=hostile))["items"] == []
        assert corpus.formula_search(FormulaQuery(term=hostile))["items"] == []
    pages = [corpus.formula_search(FormulaQuery(limit=1, offset=n)) for n in range(6)]
    assert [p["items"][0] for p in pages] == corpus.formula_search()["items"]
    assert len({p["items"][0]["id"] for p in pages}) == 6
    assert not pages[-1]["has_more"]
    assert corpus.formula_search(FormulaQuery(offset=20))["items"] == []


@pytest.mark.parametrize("factory", [
    lambda: FileQuery(limit=0), lambda: FileQuery(limit=501), lambda: FileQuery(limit=True),
    lambda: FileQuery(offset=-1), lambda: FileQuery(offset=1_000_001),
    lambda: FileQuery(path=" "), lambda: FileQuery(path="\x00"),
    lambda: FileQuery(path="x" * 2049), lambda: FileQuery(sort="path;DROP TABLE files"),
    lambda: FileQuery(descending=1), lambda: FormulaQuery(limit=0),
    lambda: FormulaQuery(offset=-1), lambda: FormulaQuery(text="\n"),
    lambda: FormulaQuery(head=" "), lambda: FormulaQuery(term=" "),
    lambda: FormulaQuery(path=" "), lambda: FormulaQuery(text=None),
])
def test_query_negative_guards(factory):
    with pytest.raises(QueryError):
        factory()


def test_term_reports_caps_without_changing_existing_payload(tmp_path, corpus_factory):
    index = corpus_factory(tmp_path, {"many.kif": "\n".join(
        f"(subclass Child{n:03} Root)" for n in range(205)
    )})
    root = index.term("Root")
    assert root["formula_count"] == root["formulas_total"] == root["children_total"] == 205
    assert len(root["formulas"]) == 100 and root["formulas_truncated"]
    assert len(root["children"]) == 200 and root["children_truncated"]
    assert not index.term("Child000")["formulas_truncated"]
    assert not index.term("Child000")["children_truncated"]

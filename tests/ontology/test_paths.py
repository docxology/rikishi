import pytest

from rikishi.corpus_query import QueryError
from rikishi.taxonomy_paths import TaxonomyPathQuery


@pytest.fixture
def corpus(tmp_path, corpus_factory):
    return corpus_factory(tmp_path, {"a.kif":
        "; source line\n(subclass A B)\n(subclass A C)\n(subclass B Root)\n"
        "(subclass C Root)\n(subclass Root A)\n(subclass X Y)\n(subclass Self Self)\n"
        '(documentation Solo EnglishLanguage "Isolated")\n'
        "(subclass A B)\n(subrelation p q)",
        "b.kif": "(subclass A Root)"})


def test_paths_are_shortest_deterministic_and_source_backed(corpus):
    full = corpus.taxonomy_path(TaxonomyPathQuery("A", "Root"))
    assert full["status"] == "found" and full["nodes"] == ["A", "Root"]
    assert full["edges"][0]["formula"]["path"] == "b.kif"
    query = TaxonomyPathQuery("A", "Root", path="a.kif")
    result = corpus.taxonomy_path(query)
    assert result == corpus.taxonomy_path(query)
    assert result["nodes"] == ["A", "B", "Root"]
    assert [e["formula"]["line"] for e in result["edges"]] == [2, 4]
    assert [e["formula"]["text"] for e in result["edges"]] == ["(subclass A B)", "(subclass B Root)"]
    assert all(e["formula"]["source_sha256"] == corpus.source_manifest()[0]["sha256"]
               for e in result["edges"])
    assert corpus.taxonomy_path(TaxonomyPathQuery("Root", "B", path="a.kif"))["nodes"] == ["Root", "A", "B"]
    assert corpus.taxonomy_path(TaxonomyPathQuery("p", "q", relation="subrelation"))["status"] == "found"


def test_absence_depth_visit_exhaustion_and_zero_length_are_distinct(corpus):
    absent = corpus.taxonomy_path(TaxonomyPathQuery("X", "A"))
    assert absent["status"] == "not_found" and absent["visited"] == 2
    assert absent["nodes"] == absent["edges"] == []
    assert corpus.taxonomy_path(TaxonomyPathQuery("A", "X"))["status"] == "not_found"
    assert corpus.taxonomy_path(TaxonomyPathQuery("Solo", "A", max_depth=0))["status"] == "not_found"
    assert corpus.taxonomy_path(TaxonomyPathQuery("Self", "A", max_depth=0))["status"] == "not_found"
    assert corpus.taxonomy_path(TaxonomyPathQuery("A", "Root", max_depth=0))["status"] == "max_depth"
    assert corpus.taxonomy_path(TaxonomyPathQuery("A", "Root", path="a.kif", max_depth=1))["status"] == "max_depth"
    assert corpus.taxonomy_path(TaxonomyPathQuery("A", "Root", max_visited=1))["status"] == "max_visited"
    assert corpus.taxonomy_path(TaxonomyPathQuery("A", "B", max_visited=2))["status"] == "found"
    same = corpus.taxonomy_path(TaxonomyPathQuery("Solo", "Solo", max_depth=0, max_visited=1))
    assert same["status"] == "found" and same["nodes"] == ["Solo"] and same["edges"] == []
    assert corpus.taxonomy_path(TaxonomyPathQuery("A", "Root", path="../a.kif"))["status"] == "not_found"
    for source, target in (("missing", "A"), ("A", "missing"), ("' OR 1=1 --", "A")):
        with pytest.raises(KeyError):
            corpus.taxonomy_path(TaxonomyPathQuery(source, target))


@pytest.mark.parametrize("factory", [
    lambda: TaxonomyPathQuery(" ", "A"), lambda: TaxonomyPathQuery("A", ""),
    lambda: TaxonomyPathQuery("A", "B", relation="instance"),
    lambda: TaxonomyPathQuery("A", "B", path=" "),
    lambda: TaxonomyPathQuery("A", "B", max_depth=-1),
    lambda: TaxonomyPathQuery("A", "B", max_depth=101),
    lambda: TaxonomyPathQuery("A", "B", max_visited=0),
    lambda: TaxonomyPathQuery("A", "B", max_visited=100_001),
])
def test_path_negative_guards(factory):
    with pytest.raises(QueryError):
        factory()

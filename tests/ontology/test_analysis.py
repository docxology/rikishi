import pytest

from rikishi.corpus_query import QueryError
from rikishi.ontology_analysis import TaxonomyQuery


@pytest.fixture
def corpus(tmp_path, corpus_factory):
    return corpus_factory(tmp_path, {"a.kif":
        "(subclass A B)\n(subclass A B)\n(subclass A C)\n(subclass B Root)\n"
        "(subclass C Root)\n(subclass X Y)\n(subclass Y X)\n(subclass Self Self)\n"
        '(documentation Solo EnglishLanguage "Not an endpoint")\n'
        "(forall (?X) (subclass Nested Root))\n(subrelation p q)\n(instance Ada A)",
        "b.kif": "(subclass Other Top)"})


def test_complete_relation_inventory_retains_duplicates_and_excludes_nested(corpus):
    result = corpus.relation_inventory()
    assert result["total"] == 3
    relations = {row["relation"]: row for row in result["items"]}
    assert relations["subclass"] == {
        "relation": "subclass", "assertion_count": 9, "unique_edges": 8,
        "duplicate_assertions": 1, "node_count": 9,
    }
    assert relations["instance"]["node_count"] == 2
    assert result["assertion_count"] == 11 and result["unique_edges"] == 10
    assert [row["relation"] for row in result["items"]] == sorted(relations)


def test_taxonomy_endpoint_population_components_roots_parents_and_cycles(corpus):
    result = corpus.taxonomy_analysis()
    assert (result["total"], result["filtered_total"], result["node_count"]) == (9, 9, 9)
    assert result["assertion_count"] == 9 and result["unique_edges"] == 8
    assert result["duplicate_assertions"] == 1
    assert result["root_count"] == 2 and result["multiple_parent_count"] == 1
    assert result["weak_component_count"] == 4
    assert result["cyclic_component_count"] == 2 and result["cyclic_node_count"] == 3
    assert result["self_loop_count"] == 1
    nodes = {row["name"]: row for row in result["items"]}
    assert nodes["A"] == {"name": "A", "parent_count": 2, "child_count": 0,
                          "component": "A", "cycle_component": None}
    assert nodes["Root"]["child_count"] == 2
    assert nodes["X"]["cycle_component"] == nodes["Y"]["cycle_component"] == "X"
    assert "Solo" not in nodes and "Nested" not in nodes and "subclass" not in nodes
    assert result["cycle_components"] == [
        {"representative": "Self", "node_count": 1, "members": ["Self"], "members_truncated": False},
        {"representative": "X", "node_count": 2, "members": ["X", "Y"], "members_truncated": False},
    ]
    page = corpus.taxonomy_analysis(TaxonomyQuery(limit=1, offset=1))
    assert page["items"] == result["items"][1:2]
    assert page["has_more"] and page["truncated"] and page["cycle_components_truncated"]
    assert page["unique_edges"] == result["unique_edges"]
    assert corpus.taxonomy_analysis(TaxonomyQuery(offset=100))["items"] == []
    filtered = corpus.taxonomy_analysis(TaxonomyQuery(path="b.kif"))
    assert filtered["total"] == 9 and filtered["filtered_total"] == 2
    assert filtered["root_count"] == filtered["unique_edges"] == 1
    assert corpus.taxonomy_analysis(TaxonomyQuery(path="%"))["node_count"] == 0
    assert corpus.taxonomy_analysis(TaxonomyQuery(relation="subrelation"))["node_count"] == 2


def test_empty_index_and_empty_relation_are_defined(tmp_path, corpus_factory):
    index = corpus_factory(tmp_path, {"empty.kif": "; nothing"})
    assert index.relation_inventory()["items"] == []
    result = index.taxonomy_analysis()
    for key in ("node_count", "root_count", "unique_edges", "weak_component_count",
                "cyclic_component_count", "multiple_parent_count", "self_loop_count"):
        assert result[key] == 0
    assert result["items"] == result["cycle_components"] == []
    assert not result["truncated"] and not result["has_more"]
    assert index.corpus_files()["total_formulas"] == 0
    assert index.formula_search()["items"] == []


def test_long_chain_and_large_scc_are_iterative(tmp_path, corpus_factory):
    text = "\n".join(f"(subclass N{i:04} N{i+1:04})" for i in range(1100))
    text += "\n(subclass N1100 N1090)"
    index = corpus_factory(tmp_path, {"chain.kif": text})
    result = index.taxonomy_analysis(TaxonomyQuery(limit=1))
    assert result["weak_component_count"] == result["cyclic_component_count"] == 1
    assert result["cyclic_node_count"] == 11
    assert result["cycle_components"][0]["members_truncated"]
    assert len(result["cycle_components"][0]["members"]) == 10


@pytest.mark.parametrize("factory", [
    lambda: TaxonomyQuery(relation="instance"), lambda: TaxonomyQuery(relation=" "),
    lambda: TaxonomyQuery(path=" "), lambda: TaxonomyQuery(limit=0),
    lambda: TaxonomyQuery(offset=-1),
])
def test_taxonomy_guards(factory):
    with pytest.raises(QueryError):
        factory()

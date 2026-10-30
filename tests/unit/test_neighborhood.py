import pytest


def test_incident_unique_counts_and_filter_inventory(tmp_path, corpus_factory):
    index = corpus_factory(tmp_path, {"Merge.kif":
        "(subclass Human Animal)\n(subclass Human Animal)\n"
        "(instance Ada Human)\n(disjoint Human Rock)\n(subclass Human Human)"})
    graph = index.neighborhood("Human", limit=1)
    assert graph["total_edges"] == 4
    assert graph["returned_edges"] == 1
    assert graph["truncated"] is True
    assert graph["relations"] == [
        {"relation": "disjoint", "count": 1}, {"relation": "instance", "count": 1},
        {"relation": "subclass", "count": 2},
    ]
    filtered = index.neighborhood("Human", relation="subclass")
    assert filtered["edges"] == [
        {"source": "Human", "target": "Animal", "relation": "subclass"},
        {"source": "Human", "target": "Human", "relation": "subclass"},
    ]
    assert filtered["total_edges"] == filtered["returned_edges"] == 2
    assert filtered["truncated"] is False
    assert filtered["relations"] == graph["relations"]


def test_empty_filtered_and_isolated_neighborhoods_are_explicit(tmp_path, corpus_factory):
    index = corpus_factory(tmp_path, {
        "Merge.kif": '(subclass Human Animal)\n(documentation Solo EnglishLanguage "Isolated")'
    })
    unknown = index.neighborhood("Human", relation="NotAnIncidentRelation")
    assert unknown["edges"] == []
    assert unknown["nodes"] == [{"id": "Human", "label": "Human"}]
    assert unknown["total_edges"] == 0
    isolated = index.neighborhood("Solo")
    assert isolated["relations"] == []
    assert isolated["total_edges"] == isolated["returned_edges"] == 0
    assert isolated["truncated"] is False
    with pytest.raises(ValueError, match="nonempty"):
        index.neighborhood("Human", relation=" ")

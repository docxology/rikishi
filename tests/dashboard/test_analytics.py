import pytest

from rikishi.analytics import measure_corpus
from rikishi.ontology import OntologyIndex


def index_text(tmp_path, text):
    source = tmp_path / "source"
    source.mkdir()
    (source / "one.kif").write_text(text, encoding="utf-8")
    index = OntologyIndex(tmp_path / "index.sqlite")
    index.build(source)
    return index


def test_exact_counts_duplicates_self_loops_and_denominators(tmp_path):
    index = index_text(
        tmp_path,
        '(subclass A B)\n(subclass A B)\n(subclass A A)\n(documentation C EnglishLanguage "Text")',
    )
    data = measure_corpus(index)
    assert data["formula_denominator"] == 4
    assert data["edge_assertions"] == 3
    assert data["unique_edges"] == 2
    assert data["duplicate_edge_assertions"] == 1
    assert data["incident_terms"] == 2
    assert data["degree_distribution"] == [
        {"degree": 0, "terms": 4},
        {"degree": 1, "terms": 1},
        {"degree": 3, "terms": 1},
    ]
    assert (
        sum(r["degree"] * r["terms"] for r in data["degree_distribution"])
        == 2 * data["unique_edges"]
    )
    assert sum(r["terms"] for r in data["degree_distribution"]) == data["term_denominator"]
    assert data["mean_total_degree"] == pytest.approx(4 / 6)
    assert sum(r["share"] for r in data["predicates"]) == pytest.approx(1)
    assert data["file_hhi"] == 1


def test_composition_is_not_truncated_at_thirty_heads(tmp_path):
    data = measure_corpus(index_text(tmp_path, "\n".join(f"(head{i} A B)" for i in range(35))))
    assert len(data["predicates"]) == 35
    assert sum(r["count"] for r in data["predicates"]) == 35
    assert data["zero_degree_terms"] == 35


@pytest.mark.parametrize("text,rejected", [("; empty file", 0), ("(broken", 1)])
def test_empty_denominators_and_rejected_files_are_explicit(tmp_path, text, rejected):
    data = measure_corpus(index_text(tmp_path, text))
    assert data["rejected_files"] == rejected
    assert data["formula_denominator"] == 0
    assert data["file_hhi"] is None
    assert data["largest_file_share"] is None
    assert data["top_ten_file_share"] is None
    assert data["mean_total_degree"] is None
    assert data["predicates"] == []
    assert data["degree_distribution"] == []


def test_missing_index_is_not_created(tmp_path):
    path = tmp_path / "missing.sqlite"
    with pytest.raises(FileNotFoundError):
        measure_corpus(OntologyIndex(path))
    assert not path.exists()


def test_file_concentration_uses_formula_population(tmp_path):
    index = index_text(tmp_path, "(subclass A B)\n(subclass C D)\n(subclass E F)")
    (tmp_path / "source" / "two.kif").write_text("(subclass G H)", encoding="utf-8")
    index.build(tmp_path / "source")
    data = measure_corpus(index)
    assert data["largest_file_share"] == 0.75
    assert data["top_ten_file_share"] == 1
    assert data["file_hhi"] == 0.625

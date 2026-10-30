from pathlib import Path

import pytest
from defusedxml import ElementTree

from rikishi.analytics import measure_corpus
from rikishi.ontology import OntologyIndex
from rikishi.reports import _composition_figure, build_report


def _text(path: str) -> str:
    root = ElementTree.parse(path).getroot()
    assert root is not None
    return " ".join(root.itertext())


def test_report_figures_label_full_denominators_and_remainder(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "literal$source.kif").write_text(
        "\n".join(f"(head{i} A B)" for i in range(12)) + "\n(head0 A B)\n",
        encoding="utf-8",
    )
    index = OntologyIndex(tmp_path / "index.sqlite")
    index.build(source)
    artifacts = build_report(index.path, tmp_path / "report")
    composition = _text(artifacts["composition_svg"])
    files = _text(artifacts["svg"])
    assert "All 13 formulas: ten largest heads + exact remainder" in composition
    assert "All remaining heads" in composition
    assert "2  (15.4%)" in composition
    assert "Degree 0: 12  (85.7%)" in composition
    assert "14 indexed symbols" in composition
    assert r"\mathdefault" not in composition
    assert "literal$source.kif" in files
    assert "13  (100.0%)" in files
    assert "13 top-level formulas in 1 parsed files" in files


def test_degree_plot_keeps_every_exact_point_and_zero(tmp_path: Path) -> None:
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    source = tmp_path / "source"
    source.mkdir()
    (source / "sample.kif").write_text(
        "(subclass A B)\n(subclass A B)\n(subclass B B)\n"
        '(documentation C EnglishLanguage "No endpoint")\n',
        encoding="utf-8",
    )
    index = OntologyIndex(tmp_path / "index.sqlite")
    index.build(source)
    measurements = measure_corpus(index)
    figure = Figure(figsize=(7.2, 6.7), dpi=100)
    canvas = FigureCanvasAgg(figure)
    try:
        _composition_figure(figure, measurements)
        degree = figure.axes[1]
        assert degree.collections[0].get_offsets().tolist() == [
            [row["degree"], row["terms"]] for row in measurements["degree_distribution"]
        ]
        assert degree.collections[1].get_offsets().tolist() == [
            [0, measurements["zero_degree_terms"]]
        ]
        assert degree.get_xscale() == degree.get_yscale() == "symlog"
        assert degree.get_xlim()[0] < 0 < degree.get_xlim()[1]
        canvas.draw()
        renderer = canvas.get_renderer()
        assert all("$" not in tick.get_text() for tick in degree.get_xticklabels())
        assert all("$" not in tick.get_text() for tick in degree.get_yticklabels())
        for text in figure.texts:
            assert figure.bbox.contains(*text.get_window_extent(renderer).get_points()[0])
            assert figure.bbox.contains(*text.get_window_extent(renderer).get_points()[1])
    finally:
        figure.clear()


def test_empty_corpus_uses_undefined_shares_and_real_zero_counts(tmp_path: Path) -> None:
    source = tmp_path / "empty-source"
    source.mkdir()
    (source / "empty.kif").write_text("; no expressions\n", encoding="utf-8")
    index = OntologyIndex(tmp_path / "index.sqlite")
    index.build(source)
    artifacts = build_report(index.path, tmp_path / "report")
    for key in ("svg", "composition_svg"):
        text = _text(artifacts[key])
        assert "0  (share undefined)" in text
        assert "nan" not in text
        assert "0.0%" not in text
    assert measure_corpus(index)["degree_distribution"] == []


def test_missing_report_database_fails_before_outputs(tmp_path: Path) -> None:
    output = tmp_path / "report"
    with pytest.raises(FileNotFoundError):
        build_report(tmp_path / "missing.sqlite", output)
    assert not output.exists()

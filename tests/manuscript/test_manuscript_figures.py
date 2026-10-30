from __future__ import annotations

import copy
import json
import math
import os
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest
from defusedxml import ElementTree
from PIL import Image
from pydantic import ValidationError

from rikishi.fep import DemoParameters, DemoResult, demo
from rikishi.graph_types import GraphNode, Neighborhood
from rikishi.manuscript_figures import (
    FigureDataError,
    _cover,
    _finite_model_figure,
    _validate_example,
    render_manuscript_figures,
)
from rikishi.manuscript_provenance import CorpusMeasurement
from rikishi.ontology import OntologyIndex


class LabeledDemoResult(DemoResult):
    state_labels: list[str]
    scan_points: int


@pytest.fixture
def measured_graph(
    tmp_path: Path, git_commit: Callable[[Path], str]
) -> tuple[CorpusMeasurement, Neighborhood]:
    source = tmp_path / "source"
    source.mkdir()
    (source / "Merge.kif").write_text(
        "(subclass Concept Entity)\n(subclass Body Entity)\n(subclass Sign Entity)\n"
        "(subclass Body Entity)\n(instance Entity Category)\n"
        '(documentation Entity EnglishLanguage "Fixture root")\n',
        encoding="utf-8",
    )
    git_commit(source)
    index = OntologyIndex(tmp_path / "fixture.sqlite")
    index.build(source)
    return (
        CorpusMeasurement.model_validate(index.stats()),
        index.neighborhood("Entity", limit=500, relation="subclass"),
    )


def numerical_example(*, changed: bool = False) -> LabeledDemoResult:
    parameters = DemoParameters(
        prior=(0.25, 0.75) if changed else (0.5, 0.5),
        likelihood=(0.9, 0.1) if changed else (0.7, 0.3),
        candidate=(0.6, 0.4),
        scan_points=9,
        state_labels=("left $literal$", "right") if changed else ("inside", "outside"),
    )
    return LabeledDemoResult(
        **demo(parameters),
        state_labels=list(parameters.state_labels),
        scan_points=parameters.scan_points,
    )


def svg_text(path: Path) -> str:
    root = ElementTree.parse(path).getroot()
    assert root is not None
    return " ".join(root.itertext())


def test_actual_image_formats_and_exact_input_receipt(
    tmp_path: Path, measured_graph: tuple[CorpusMeasurement, Neighborhood]
) -> None:
    corpus, graph = measured_graph
    example = numerical_example()
    output = tmp_path / "figures"
    paths = render_manuscript_figures(output, example, corpus, graph, dpi=100, decimal_places=4)
    assert paths == [
        output / name
        for name in (
            "fep-free-energy.png",
            "graphical-abstract.png",
            "graphical-abstract.svg",
            "graphical-abstract.json",
        )
    ]
    for name, dimensions in (
        ("fep-free-energy.png", (720, 580)),
        ("graphical-abstract.png", (720, 640)),
    ):
        with Image.open(output / name) as image:
            assert image.format == "PNG"
            assert image.size == dimensions
            colors = image.convert("RGB").getcolors(maxcolors=image.width * image.height)
            assert colors is not None and len(colors) > 16
            assert (25, 52, 73) in {color for _, color in colors}
            assert image.info["dpi"] == pytest.approx((100, 100), abs=0.1)
    receipt = json.loads((output / "graphical-abstract.json").read_text())
    assert receipt["example"] == example
    assert receipt["corpus"] == corpus.model_dump()
    assert receipt["taxonomy"] == graph
    assert receipt["rendering"] == {"dpi": 100, "decimal_places": 4}
    root = ElementTree.parse(output / "graphical-abstract.svg").getroot()
    assert root is not None
    assert root.attrib["viewBox"] == "0 0 518.4 460.8"
    assert all(path.is_file() and path.stat().st_size > 1000 for path in paths)


def test_graph_uses_actual_source_labels_and_child_to_parent_arrows(
    tmp_path: Path, measured_graph: tuple[CorpusMeasurement, Neighborhood]
) -> None:
    corpus, graph = measured_graph
    render_manuscript_figures(
        tmp_path / "figures", numerical_example(), corpus, graph, dpi=100, decimal_places=3
    )
    path = tmp_path / "figures" / "graphical-abstract.svg"
    text = svg_text(path)
    for node in graph["nodes"]:
        assert node["label"] in text
    assert f"{corpus.files:,} files" in text
    assert f"{corpus.formulas:,} formulas" in text
    assert f"{corpus.terms:,} terms" in text
    assert f"{corpus.edges:,} edge assertions" in text
    root = ElementTree.parse(path).getroot()
    assert root is not None
    groups = [
        element
        for element in root.iter()
        if element.attrib.get("id", "").startswith("subclass-edge-")
    ]
    assert len(groups) == len(graph["edges"])
    for group in groups:
        paths = [element for element in group.iter() if element.tag.endswith("path")]
        assert len(paths) == 2
        coordinates = [float(value) for value in re.findall(r"-?\d+\.?\d*", paths[0].attrib["d"])]
        assert coordinates[1] > coordinates[-1]


def test_perturbed_model_changes_posterior_labels_and_pixels(
    tmp_path: Path, measured_graph: tuple[CorpusMeasurement, Neighborhood]
) -> None:
    corpus, graph = measured_graph
    first, changed = numerical_example(), numerical_example(changed=True)
    render_manuscript_figures(tmp_path / "first", first, corpus, graph, dpi=100, decimal_places=5)
    render_manuscript_figures(
        tmp_path / "changed", changed, corpus, graph, dpi=100, decimal_places=5
    )
    text = svg_text(tmp_path / "changed" / "graphical-abstract.svg")
    assert "Analytical q* = 0.75000" in text
    assert "q(left $literal$)" in text
    assert "[0.25000, 0.75000]" in text
    assert "[0.90000, 0.10000]" in text
    assert f"{(-math.log(0.3)):.5f}" in text
    assert "Analytical q* = 0.70000" in svg_text(tmp_path / "first" / "graphical-abstract.svg")
    for name in ("fep-free-energy.png", "graphical-abstract.png"):
        assert (tmp_path / "first" / name).read_bytes() != (
            tmp_path / "changed" / name
        ).read_bytes()


def test_unnamed_demo_uses_mathematical_state_indices(
    tmp_path: Path, measured_graph: tuple[CorpusMeasurement, Neighborhood]
) -> None:
    corpus, graph = measured_graph
    example = demo(
        DemoParameters(
            prior=(0.4, 0.6),
            likelihood=(0.5, 0.5),
            candidate=(0.0, 1.0),
            scan_points=2,
            state_labels=("first", "second"),
        )
    )
    render_manuscript_figures(
        tmp_path / "figures", example, corpus, graph, dpi=72, decimal_places=0
    )
    assert "q(state 0)" in svg_text(tmp_path / "figures" / "graphical-abstract.svg")


@pytest.mark.parametrize(
    "damage",
    [
        "truncated",
        "total",
        "returned",
        "empty",
        "duplicate_node",
        "duplicate_edge",
        "missing_root",
        "reversed",
        "wrong_relation",
        "missing_endpoint",
        "disconnected",
        "inventory",
        "duplicate_inventory",
        "empty_inventory",
        "blank_label",
        "long_label",
        "control_label",
        "capacity",
    ],
)
def test_invalid_taxonomy_is_rejected_before_writing(
    tmp_path: Path, measured_graph: tuple[CorpusMeasurement, Neighborhood], damage: str
) -> None:
    corpus, original = measured_graph
    graph = copy.deepcopy(original)
    match damage:
        case "truncated":
            graph["truncated"] = True
        case "total":
            graph["total_edges"] += 1
        case "returned":
            graph["returned_edges"] -= 1
        case "empty":
            graph["edges"] = []
        case "duplicate_node":
            graph["nodes"].append(graph["nodes"][0])
        case "duplicate_edge":
            graph["edges"][1] = graph["edges"][0]
        case "missing_root":
            graph["nodes"] = [node for node in graph["nodes"] if node["id"] != "Entity"]
        case "reversed":
            graph["edges"][0]["source"], graph["edges"][0]["target"] = "Entity", "Body"
        case "wrong_relation":
            graph["edges"][0]["relation"] = "instance"
        case "missing_endpoint":
            graph["edges"][0]["source"] = "Absent"
        case "disconnected":
            graph["nodes"].append({"id": "Unused", "label": "Unused"})
        case "inventory":
            graph["relations"][-1]["count"] += 1
        case "duplicate_inventory":
            graph["relations"].append(graph["relations"][0])
        case "empty_inventory":
            graph["relations"][0]["count"] = 0
        case "blank_label":
            graph["nodes"][0]["label"] = " "
        case "long_label":
            graph["nodes"][0]["label"] = "x" * 29
        case "control_label":
            graph["nodes"][0]["label"] = "line\nbreak"
        case "capacity":
            graph["nodes"] = [GraphNode(id="Entity", label="Entity")] + [
                GraphNode(id=f"Type{i}", label=f"Type{i}") for i in range(8)
            ]
            graph["edges"] = [
                {"source": f"Type{i}", "target": "Entity", "relation": "subclass"} for i in range(8)
            ]
            graph["total_edges"] = graph["returned_edges"] = 8
            graph["relations"] = [{"relation": "subclass", "count": 8}]
    output = tmp_path / "rejected"
    with pytest.raises(FigureDataError):
        render_manuscript_figures(
            output, numerical_example(), corpus, graph, dpi=100, decimal_places=4
        )
    assert not output.exists()


@pytest.mark.parametrize(
    "damage",
    [
        "prior",
        "candidate",
        "dimension",
        "result",
        "posterior",
        "posterior_dimension",
        "optimum",
        "scan_energy",
        "scan_gap",
        "scan_order",
        "scan_empty",
        "nonfinite",
        "units",
        "scan_count",
        "labels_count",
        "labels_equal",
        "labels_blank",
        "labels_long",
        "labels_control",
    ],
)
def test_invalid_numerical_evidence_is_rejected_before_writing(
    tmp_path: Path, measured_graph: tuple[CorpusMeasurement, Neighborhood], damage: str
) -> None:
    corpus, graph = measured_graph
    example = numerical_example()
    match damage:
        case "prior":
            example["prior"] = [0.3, 0.3]
        case "candidate":
            example["candidate"] = [0.7, 0.3]
        case "dimension":
            example["likelihood"] = [0.5]
        case "result":
            example["result"]["evidence"] += 0.01
        case "posterior":
            example["result"]["exact_posterior"] = [0.6, 0.4]
        case "posterior_dimension":
            example["result"]["exact_posterior"] = [1.0]
        case "optimum":
            example["optimum"]["free_energy"] += 0.01
        case "scan_energy":
            example["scan"][3]["free_energy"] += 0.01
        case "scan_gap":
            del example["scan"][3]
            example["scan_points"] = len(example["scan"])
        case "scan_order":
            example["scan"].reverse()
        case "scan_empty":
            example["scan"] = []
        case "nonfinite":
            example["scan"][2]["free_energy"] = math.inf
        case "units":
            example["units"] = "bits"
        case "scan_count":
            example["scan_points"] += 1
        case "labels_count":
            example["state_labels"] = ["only"]
        case "labels_equal":
            example["state_labels"] = ["same", "same"]
        case "labels_blank":
            example["state_labels"] = [" ", "second"]
        case "labels_long":
            example["state_labels"] = ["x" * 29, "second"]
        case "labels_control":
            example["state_labels"] = ["line\nbreak", "second"]
    output = tmp_path / "rejected"
    with pytest.raises((ValueError, ValidationError)):
        render_manuscript_figures(output, example, corpus, graph, dpi=100, decimal_places=4)
    assert not output.exists()


@pytest.mark.parametrize("damage", ["dirty", "parse", "empty", "terms", "edges", "formulas"])
def test_untrustworthy_corpus_is_rejected_before_writing(
    tmp_path: Path, measured_graph: tuple[CorpusMeasurement, Neighborhood], damage: str
) -> None:
    corpus, graph = measured_graph
    values = corpus.model_dump()
    match damage:
        case "dirty":
            values["source_clean"] = False
        case "parse":
            values["parse_errors"] = [{"path": "bad.kif", "message": "Malformed"}]
        case "empty":
            values["formulas"] = 0
        case "terms":
            values["terms"] = 1
        case "edges":
            values["edges"] = 1
        case "formulas":
            values["formulas"] = 1
    rejected = CorpusMeasurement.model_validate(values)
    output = tmp_path / "rejected"
    with pytest.raises(FigureDataError):
        render_manuscript_figures(
            output, numerical_example(), rejected, graph, dpi=100, decimal_places=4
        )
    assert not output.exists()


@pytest.mark.parametrize(
    ("dpi", "places"), [(71, 3), (1201, 3), (True, 3), (100, -1), (100, 10), (100, True)]
)
def test_invalid_render_configuration_is_rejected(
    tmp_path: Path, measured_graph: tuple[CorpusMeasurement, Neighborhood], dpi: int, places: int
) -> None:
    corpus, graph = measured_graph
    with pytest.raises(FigureDataError):
        render_manuscript_figures(
            tmp_path / "rejected",
            numerical_example(),
            corpus,
            graph,
            dpi=dpi,
            decimal_places=places,
        )


def test_filesystem_failure_propagates(
    tmp_path: Path, measured_graph: tuple[CorpusMeasurement, Neighborhood]
) -> None:
    corpus, graph = measured_graph
    output = tmp_path / "occupied"
    output.write_text("preserved input")
    with pytest.raises(FileExistsError):
        render_manuscript_figures(
            output, numerical_example(), corpus, graph, dpi=100, decimal_places=4
        )
    assert output.read_text() == "preserved input"


def test_import_does_not_load_plotting_or_create_artifacts(tmp_path: Path) -> None:
    cache = tmp_path / "uncreated-matplotlib-cache"
    subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import rikishi.manuscript_figures; assert 'matplotlib' not in sys.modules",
        ],
        cwd=tmp_path,
        env={**os.environ, "MPLCONFIGDIR": str(cache), "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        text=True,
        check=True,
    )
    assert list(tmp_path.iterdir()) == []


def test_truncation_reports_the_evidence_failure(
    tmp_path: Path, measured_graph: tuple[CorpusMeasurement, Neighborhood]
) -> None:
    corpus, graph = measured_graph
    graph["truncated"] = True
    with pytest.raises(FigureDataError, match="complete, nonempty Entity subclass"):
        render_manuscript_figures(
            tmp_path / "rejected", numerical_example(), corpus, graph, dpi=100, decimal_places=4
        )


def test_cover_xlabel_and_posterior_label_do_not_overlap(
    measured_graph: tuple[CorpusMeasurement, Neighborhood],
) -> None:
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    corpus, graph = measured_graph
    figure = Figure(figsize=(7.2, 6.4), dpi=180)
    canvas = FigureCanvasAgg(figure)
    try:
        _cover(figure, _validate_example(numerical_example(changed=True)), corpus, graph, 6)
        canvas.draw()
        renderer = canvas.get_renderer()
        xlabel = figure.axes[-1].xaxis.label.get_window_extent(renderer)
        posterior = next(text for text in figure.texts if text.get_text().startswith("Analytical"))
        assert not xlabel.overlaps(posterior.get_window_extent(renderer))
    finally:
        figure.clear()


@pytest.mark.parametrize("changed", [False, True])
def test_finite_panels_plot_exact_model_scan_and_decomposition(changed: bool) -> None:
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    example = _validate_example(numerical_example(changed=changed))
    figure = Figure(figsize=(7.2, 5.8), dpi=100)
    canvas = FigureCanvasAgg(figure)
    try:
        _finite_model_figure(figure, example, 6)
        model, objective, decomposition = figure.axes
        expected = [
            example.prior,
            example.likelihood,
            example.result["exact_posterior"],
            example.candidate,
        ]
        assert [bar.get_width() for bar in model.patches] == pytest.approx(
            [vector[state] for state in range(2) for vector in expected]
        )
        assert list(objective.lines[0].get_xdata()) == [p["q_state_zero"] for p in example.scan]
        assert list(objective.lines[0].get_ydata()) == [p["free_energy"] for p in example.scan]
        assert [bar.get_width() for bar in decomposition.patches] == pytest.approx(
            [
                example.result["surprise"],
                example.result["surprise"],
                example.result["kl_to_posterior"],
                example.optimum["kl_to_posterior"],
            ]
        )
        assert [bar.get_x() for bar in decomposition.patches[2:]] == pytest.approx(
            [example.result["surprise"]] * 2
        )
        canvas.draw()
        renderer = canvas.get_renderer()
        for text in figure.texts:
            assert figure.bbox.contains(*text.get_window_extent(renderer).get_points()[0])
            assert figure.bbox.contains(*text.get_window_extent(renderer).get_points()[1])
    finally:
        figure.clear()


@pytest.mark.parametrize("letter", ["X", "W"])
def test_supported_seven_child_layout_keeps_complete_labels_separate(
    tmp_path: Path, git_commit: Callable[[Path], str], letter: str
) -> None:
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    children = [f"Category{i}" + letter * 19 for i in range(7)]
    source = tmp_path / "source"
    source.mkdir()
    (source / "fixture.kif").write_text(
        "\n".join(f"(subclass {child} Entity)" for child in children), encoding="utf-8"
    )
    git_commit(source)
    index = OntologyIndex(tmp_path / "fixture.sqlite")
    index.build(source)
    figure = Figure(figsize=(7.2, 6.4), dpi=100)
    canvas = FigureCanvasAgg(figure)
    try:
        _cover(
            figure,
            _validate_example(numerical_example()),
            CorpusMeasurement.model_validate(index.stats()),
            index.neighborhood("Entity", limit=500, relation="subclass"),
            6,
        )
        canvas.draw()
        renderer = canvas.get_renderer()
        labels = figure.axes[0].texts[:-1]
        assert [text.get_text().replace("\n", "") for text in labels] == children
        boxes = [text.get_bbox_patch().get_window_extent(renderer) for text in labels]
        for position, box in enumerate(boxes):
            assert figure.bbox.contains(*box.get_points()[0])
            assert figure.bbox.contains(*box.get_points()[1])
            assert all(not box.overlaps(other) for other in boxes[position + 1 :])
    finally:
        figure.clear()

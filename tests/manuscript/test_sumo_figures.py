from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping
from hashlib import sha256
from pathlib import Path
from typing import Literal, assert_never

import pytest
from defusedxml import ElementTree
from PIL import Image

from rikishi.ontology import OntologyIndex
from rikishi.sumo_demonstrations import SumoReport, demonstrate_sumo, validate_sumo_report
from rikishi.sumo_figures import SumoFigureError, render_sumo_system

SOURCE = """; Actual selected SUMO assertions, relocated into a real fixture.
(partition Entity Physical Abstract)
(subclass Physical Entity)
(subclass Abstract Entity)
(subclass Process Physical)
(subclass Proposition Abstract)
(instance agent CaseRole)
(instance ProbabilityFn UnaryFunction)
(domain agent 1 Process)
(domain agent 2 AutonomousAgent)
(domain ProbabilityFn 1 Formula)
(range ProbabilityFn RealNumber)
(=>
  (instance ?AGENT AutonomousAgent)
  (modalAttribute
    (exists (?PROC)
      (and
        (instance ?PROC Process)
        (agent ?PROC ?AGENT)))
    Possibility))
"""


@pytest.fixture
def report(
    tmp_path: Path, corpus_factory: Callable[[Path, Mapping[str, str]], OntologyIndex]
) -> SumoReport:
    index = corpus_factory(tmp_path, {"Merge.kif": SOURCE})
    return demonstrate_sumo(index, tmp_path)


def visible_text(path: Path) -> str:
    root = ElementTree.parse(path).getroot()
    assert root is not None
    return "\n".join(node.text or "" for node in root.iter()
                     if node.tag.endswith(("}text", "}tspan")))


def test_formats_dimensions_and_exact_inputs(tmp_path: Path, report: SumoReport) -> None:
    # Given
    output = tmp_path / "figures"
    # When
    paths = render_sumo_system(output, report, dpi=100)
    # Then
    assert paths == [output / f"sumo-system.{suffix}" for suffix in ("png", "svg", "json")]
    receipt = json.loads(paths[2].read_text(encoding="utf-8"))
    assert receipt == {"report": report.model_dump(), "rendering": {
        "dpi": 100, "width_mm": 174, "height_mm": 190,
    }}
    digest = sha256(report.model_dump_json().encode()).hexdigest()
    with Image.open(paths[0]) as image:
        assert image.format == "PNG"
        assert image.size == (int(174 / 25.4 * 100), int(190 / 25.4 * 100))
        assert image.info["dpi"] == pytest.approx((100, 100), abs=0.1)
        assert image.info["Description"] == f"{report.scope} Report SHA-256: {digest}"
        colors = image.convert("RGB").getcolors(maxcolors=image.width * image.height)
        assert colors is not None
        assert {(25, 52, 73), (23, 107, 98), (163, 94, 56)} <= {c for _, c in colors}
    root = ElementTree.parse(paths[1]).getroot()
    assert root is not None
    assert list(map(float, root.attrib["viewBox"].split())) == pytest.approx(
        [0, 0, 174 / 25.4 * 72, 190 / 25.4 * 72]
    )
    assert not any(node.tag.endswith("}image") for node in root.iter())
    assert len([node for node in root.iter() if node.tag.endswith("}text")]) > 30
    assert f"{report.scope} Report SHA-256: {digest}" in " ".join(root.itertext())


@pytest.mark.parametrize("dpi", [72, 300])
def test_visible_svg_text_meets_print_font_floor(
    tmp_path: Path, report: SumoReport, dpi: int
) -> None:
    # Given
    output = tmp_path / "figures"
    # When
    render_sumo_system(output, report, dpi=dpi)
    # Then
    root = ElementTree.parse(output / "sumo-system.svg").getroot()
    assert root is not None
    width_pt = float(root.attrib["width"].removesuffix("pt"))
    point_scale = width_pt / float(root.attrib["viewBox"].split()[2])
    font_sizes = []
    for node in root.iter():
        if node.tag.endswith(("}text", "}tspan")) and (node.text or "").strip():
            size = re.search(r"(?:^|;)\s*font-size:\s*([\d.]+)px(?:;|$)", node.attrib["style"])
            assert size is not None, node.attrib
            font_sizes.append(float(size[1]) * point_scale)
    assert len(font_sizes) > 30
    assert min(font_sizes) >= 7.5


def test_svg_preserves_assertions_context_and_source_identity(
    tmp_path: Path, report: SumoReport
) -> None:
    # Given
    output = tmp_path / "figures"
    # When
    render_sumo_system(output, report, dpi=100)
    # Then
    text = visible_text(output / "sumo-system.svg")
    for citation in report.cases["hierarchy"] + report.cases["nested_formula"]:
        for line in citation.raw_kif.splitlines():
            if citation.predicate != "subclass":
                assert line in text
    for source_value in (report.source.path, report.source.commit, report.source.sha256):
        assert source_value in text
    assert "no full-SUMO proof or consistency claim" in text
    root = ElementTree.parse(output / "sumo-system.svg").getroot()
    assert root is not None
    groups = {node.attrib["id"]: node for node in root.iter() if "id" in node.attrib}
    for name, count in report.observations.model_dump().items():
        values = [node.text for node in groups[f"inventory-{name}"].iter()
                  if node.tag.endswith("}text")]
        assert values == [f"{count:,}"]
    for child, parent in (("Physical", "Entity"), ("Abstract", "Entity"),
                          ("Process", "Physical"), ("Proposition", "Abstract")):
        edge = groups[f"subclass-{child}-to-{parent}"]
        paths = [node for node in edge.iter() if node.tag.endswith("}path")]
        assert len(paths) == 2
        coordinates = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", paths[0].attrib["d"])]
        assert coordinates[1] > coordinates[-1]
    assert sum(key.startswith("subclass-") for key in groups) == 4
    assert not any(key.startswith("partition-") for key in groups)
    for name in ("instance-agent-to-CaseRole", "instance-ProbabilityFn-to-UnaryFunction"):
        paths = [node for node in groups[name].iter() if node.tag.endswith("}path")]
        assert "stroke-dasharray" in paths[0].attrib["style"]
    for name in ("constraint-agent-1-Process", "constraint-agent-2-AutonomousAgent",
                 "constraint-ProbabilityFn-1-Formula", "constraint-ProbabilityFn-RealNumber"):
        assert name in groups


def test_valid_source_mutations_change_labels_counts_citations_and_pixels(
    tmp_path: Path, corpus_factory: Callable[[Path, Mapping[str, str]], OntologyIndex]
) -> None:
    # Given
    first_root, changed_root = tmp_path / "first", tmp_path / "changed"
    first = demonstrate_sumo(corpus_factory(first_root, {"Merge.kif": SOURCE}), first_root)
    changed_source = "\n; moved source lines\n" + SOURCE.replace("?PROC", "?EVENT")
    changed_source += "(instance ReceiptEvidence CorpusMarker)\n"
    changed = demonstrate_sumo(
        corpus_factory(changed_root, {"Merge.kif": changed_source}), changed_root
    )
    render_sumo_system(first_root / "figures", first, dpi=100)
    # When
    render_sumo_system(changed_root / "figures", changed, dpi=100)
    # Then
    text = visible_text(changed_root / "figures/sumo-system.svg")
    assert "(agent ?EVENT ?AGENT)" in text
    assert "?PROC" not in text
    assert changed.observations.source_formulas == first.observations.source_formulas + 1
    assert changed.observations.projected_binary_edges == first.observations.projected_binary_edges + 1
    assert changed.observations.cited_formulas == first.observations.cited_formulas
    root = ElementTree.parse(changed_root / "figures/sumo-system.svg").getroot()
    assert root is not None
    groups = {node.attrib["id"]: node for node in root.iter() if "id" in node.attrib}
    for name, count in (("source_formulas", 13), ("projected_binary_edges", 8)):
        assert [node.text for node in groups[f"inventory-{name}"].iter()
                if node.tag.endswith("}text")] == [str(count)]
    selected = changed.cases["nested_formula"][0]
    assert f"Merge.kif: {selected.line}-{selected.end_line}" in text
    assert changed.source.sha256 in text
    assert changed.source.sha256 != first.source.sha256
    assert json.loads((changed_root / "figures/sumo-system.json").read_text())["report"] == (
        changed.model_dump()
    )
    assert (changed_root / "figures/sumo-system.png").read_bytes() != (
        first_root / "figures/sumo-system.png"
    ).read_bytes()


def test_render_needs_only_retained_bytes(tmp_path: Path, report: SumoReport) -> None:
    # Given
    (tmp_path / "source").rename(tmp_path / "source.saved")
    (tmp_path / "index.sqlite").rename(tmp_path / "index.saved")
    restored = validate_sumo_report(json.loads(report.model_dump_json()))
    # When
    paths = render_sumo_system(tmp_path / "portable", restored, dpi=72)
    # Then
    assert all(path.is_file() and path.stat().st_size > 1000 for path in paths)


@pytest.mark.parametrize("dpi", [True, False, 100.0, "100", 0, 71, 1201, -100])
def test_invalid_dpi_rejected_before_writes(
    tmp_path: Path, report: SumoReport, dpi: int
) -> None:
    # Given
    output = tmp_path / "absent"
    # When / Then
    with pytest.raises(SumoFigureError, match="dpi"):
        render_sumo_system(output, report, dpi=dpi)
    assert not output.exists()


@pytest.mark.parametrize("existing", [False, True])
@pytest.mark.parametrize("mutation", ["scope", "count", "citation", "source", "case"])
def test_tampered_report_rejected_before_writes(
    tmp_path: Path, report: SumoReport, existing: bool,
    mutation: Literal["scope", "count", "citation", "source", "case"],
) -> None:
    # Given
    match mutation:
        case "scope":
            bad = report.model_copy(update={"scope": "Full SUMO proof"})
        case "count":
            bad = report.model_copy(update={"observations": report.observations.model_copy(
                update={"source_formulas": 999})})
        case "citation":
            cases = {key: list(value) for key, value in report.cases.items()}
            cases["nested_formula"][0] = cases["nested_formula"][0].model_copy(
                update={"raw_kif": "(agent Process AutonomousAgent)"})
            bad = report.model_copy(update={"cases": cases})
        case "source":
            bad = report.model_copy(update={"source": report.source.model_copy(
                update={"sha256": "0" * 64})})
        case "case":
            bad = report.model_copy(update={"cases": {}})
        case unreachable:
            assert_never(unreachable)
    output = tmp_path / "output"
    originals = {f"sumo-system.{suffix}": f"preserve {suffix}".encode()
                 for suffix in ("png", "svg", "json")}
    if existing:
        output.mkdir()
        for name, value in originals.items():
            (output / name).write_bytes(value)
    # When / Then
    with pytest.raises(ValueError):
        render_sumo_system(output, bad, dpi=100)
    if existing:
        assert {path.name: path.read_bytes() for path in output.iterdir()} == originals
    else:
        assert not output.exists()


@pytest.mark.parametrize("change", ["lines", "columns", "path"])
def test_oversized_valid_source_rejected_before_output(
    tmp_path: Path, corpus_factory: Callable[[Path, Mapping[str, str]], OntologyIndex],
    change: Literal["lines", "columns", "path"],
) -> None:
    # Given
    source = SOURCE
    match change:
        case "lines":
            source = source.replace("(modalAttribute\n", "(modalAttribute\n\n\n\n")
        case "columns":
            source = source.replace("?PROC", "?" + "EVENT" * 15)
        case "path":
            pass
        case unreachable:
            assert_never(unreachable)
    report = demonstrate_sumo(corpus_factory(tmp_path, {"Merge.kif": source}), tmp_path)
    if change == "path":
        report = report.model_copy(update={"source": report.source.model_copy(
            update={"path": "long/" * 20 + "Merge.kif"})})
    valid = validate_sumo_report(report)
    output = tmp_path / "absent"
    # When / Then
    with pytest.raises(SumoFigureError, match="print layout"):
        render_sumo_system(output, valid, dpi=100)
    assert not output.exists()

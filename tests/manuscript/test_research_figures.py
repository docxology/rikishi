from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import uuid
from decimal import Decimal
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
from typing import Literal, assert_never

import pytest
from defusedxml import ElementTree
from PIL import Image
from pydantic import TypeAdapter

from rikishi.alignment import run_alignment, validate_alignment_report
from rikishi.competency import load_study
from rikishi.research_figures import (
    FigureInputs,
    ReportInput,
    ResearchFigureError,
    _check_pair,
    _print_figure,
    _report_input,
    render_research_figures,
)

pytestmark = pytest.mark.integration
Mutation = Literal["numeric", "source", "policy", "empty", "empty-logical", "summary", "problem"]


class Html(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.scripts: list[tuple[dict[str, str | None], str]] = []
        self.tags: list[tuple[str, dict[str, str | None]]] = []
        self.active: dict[str, str | None] | None = None
        self.script = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append((tag, dict(attrs)))
        if tag == "script":
            self.active = dict(attrs)
            self.script = ""

    def handle_data(self, data: str) -> None:
        if self.active is not None:
            self.script += data

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self.active is not None:
            self.scripts.append((self.active, self.script))
            self.active = None


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


@pytest.fixture(scope="module")
def visual_evidence(native_workspace: Path) -> Path:
    parent = native_workspace / ("research-visuals-tests-" + uuid.uuid4().hex)
    parent.mkdir()
    return parent


@pytest.fixture
def tmp_path(visual_evidence: Path, request: pytest.FixtureRequest) -> Path:
    path = visual_evidence / request.node.name
    path.mkdir()
    return path


@pytest.fixture(scope="module")
def campaigns(project_root: Path, visual_evidence: Path, portable_inputs) -> tuple[Path, Path]:
    supplied = os.environ.get("RIKISHI_RESEARCH_FIGURE_TEST_REPORTS")
    if supplied is not None:
        paths = TypeAdapter(tuple[Path, Path]).validate_json(supplied)
        assert [validate_alignment_report(path).prover for path in paths] == ["e", "v"]
        return paths
    parent = visual_evidence / "campaigns0"
    parent.mkdir()
    study = load_study()
    workbook = portable_inputs.workbook_path
    assert sha256(workbook.read_bytes()).hexdigest() == study.workbook_sha256
    paths = []
    for family in ("e", "v"):
        directory = parent / family
        run_alignment(project_root, directory, workbook_path=workbook, prover=family)
        paths.append(directory / "alignment-report.json")
    return paths[0], paths[1]


@pytest.fixture(scope="module")
def rendered(campaigns: tuple[Path, Path], visual_evidence: Path) -> list[Path]:
    return render_research_figures(visual_evidence / "paired0", campaigns[0],
                                   comparison_path=campaigns[1], dpi=120, decimal_places=3)


@pytest.fixture
def copied(campaigns: tuple[Path, Path], tmp_path: Path) -> Path:
    directory = tmp_path / "portable"
    shutil.copytree(campaigns[0].parent, directory)
    return directory / "alignment-report.json"


def test_exports_retain_exact_validated_inputs_and_measured_ratios(
    campaigns: tuple[Path, Path], rendered: list[Path],
) -> None:
    # Given
    report = validate_alignment_report(campaigns[0])
    # When
    data = FigureInputs.model_validate_json(rendered[2].read_bytes())
    # Then
    assert [p.name for p in rendered] == ["research-controls.png", "research-controls.svg",
                                         "research-controls.json", "research-dashboard.html"]
    for binding, path in zip(data.reports, campaigns, strict=True):
        assert binding.sha256 == sha256(path.read_bytes()).hexdigest()
        assert binding.report == validate_alignment_report(path)
    assert data.reports[0].report.summary == report.summary
    expected = [*report.numerical.rows, *report.numerical.extremes]
    assert len(data.numerical_rows) == len(expected)
    for actual, row in zip(data.numerical_rows, expected, strict=True):
        assert actual.id == row.input.id
        assert actual.tolerance == row.tolerance
        assert actual.ratios.reference == pytest.approx(
            float(Decimal.from_float(row.max_reference_error) / Decimal(row.tolerance)), rel=1e-14)
        assert actual.ratios.permutation == pytest.approx(row.permutation_max_error / float(row.tolerance))
        assert actual.ratios.rescaling == pytest.approx(row.rescaling_max_error / float(row.tolerance))
    assert sum(group.rows for group in data.aggregates) == len(report.numerical.rows)
    for group in data.aggregates:
        originals = [r for r in report.numerical.rows
                     if (r.dimension, r.candidate) == (group.dimension, group.candidate)]
        assert group.zeros["permutation"] == sum(r.permutation_max_error == 0 for r in originals)
        assert group.maxima.reference == pytest.approx(
            max(r.max_reference_error / float(r.tolerance) for r in originals))


def test_print_dimensions_vector_text_full_cases_and_threshold(rendered: list[Path]) -> None:
    # Given
    data = FigureInputs.model_validate_json(rendered[2].read_bytes())
    # When
    svg = ElementTree.parse(rendered[1]).getroot()
    # Then
    assert svg is not None
    assert data.height_mm == 210
    with Image.open(rendered[0]) as image:
        assert image.size == (int(174 / 25.4 * data.dpi), int(data.height_mm / 25.4 * data.dpi))
        assert image.info["dpi"] == pytest.approx((data.dpi, data.dpi), abs=0.1)
    assert not any(node.tag.endswith("}image") for node in svg.iter())
    text = "\n".join(node.text or "" for node in svg.iter() if node.tag.endswith(("}text", "}tspan")))
    for case in data.reports[0].report.study.cases:
        assert case.id in text
    for binding in data.reports:
        assert binding.sha256[:12] in text
        assert binding.sha256 in "\n".join(data.provenance)
        assert binding.report.prover.upper() in text
    font_sizes = [float(size) for size in re.findall(r"font-size: ([\d.]+)px", rendered[1].read_text())]
    assert font_sizes and min(font_sizes) >= 7.5
    assert min(font_sizes) * min(1, 200 / data.height_mm) >= 7
    assert "threshold = 1" in text
    assert "\\mathdefault" not in text
    assert "semantic validation=False" in text
    assert data.ratio_threshold == 1
    assert any(row.ratios.permutation == 0 for row in data.numerical_rows)


def test_repeat_render_is_byte_deterministic(campaigns: tuple[Path, Path], tmp_path: Path) -> None:
    # Given
    arguments = {"comparison_path": campaigns[1], "dpi": 72, "decimal_places": 0}
    # When
    first = render_research_figures(tmp_path / "first", campaigns[0], **arguments)
    second = render_research_figures(tmp_path / "second", campaigns[0], **arguments)
    # Then
    assert [p.read_bytes() for p in first] == [p.read_bytes() for p in second]


def test_single_prover_export_does_not_invent_a_comparison(
    campaigns: tuple[Path, Path], tmp_path: Path,
) -> None:
    # Given / When
    paths = render_research_figures(tmp_path / "single", campaigns[1], dpi=72, decimal_places=8)
    # Then
    data = FigureInputs.model_validate_json(paths[2].read_bytes())
    assert [r.report.prover for r in data.reports] == ["v"]


@pytest.mark.parametrize(("dpi", "decimals"), [(71, 2), (1201, 2), (True, 2), (100, -1),
                                               (100, 9), (100, True)])
def test_invalid_render_policy_rejects_before_output(tmp_path: Path, dpi: int, decimals: int) -> None:
    # Given
    output = tmp_path / "absent"
    # When / Then
    with pytest.raises(ResearchFigureError):
        render_research_figures(output, tmp_path / "missing.json", dpi=dpi, decimal_places=decimals)
    assert not output.exists()


@pytest.mark.parametrize("mutation", ["numeric", "source", "policy", "empty", "empty-logical",
                                      "summary", "problem"])
def test_tampered_inputs_reject_before_output(copied: Path, tmp_path: Path, mutation: Mutation) -> None:
    # Given
    payload = json.loads(copied.read_bytes())
    match mutation:
        case "numeric":
            payload["numerical"]["rows"][0]["result"]["free_energy"] += 0.25
        case "source":
            source = copied.parent / "source-report.json"
            values = json.loads(source.read_bytes())
            values["source"]["text"] += "\n; altered complete retained source\n"
            values["source"]["sha256"] = sha256(values["source"]["text"].encode()).hexdigest()
            _write(source, values)
        case "policy":
            payload["study"]["timeout_seconds"] += 1
        case "empty":
            payload["numerical"]["rows"] = []
        case "empty-logical":
            payload["logical"] = []
        case "summary":
            payload["summary"]["semantic_validation"] = True
        case "problem":
            (copied.parent / "problems/background.p").write_text("fof(false,axiom,$false).\n")
        case unreachable:
            assert_never(unreachable)
    _write(copied, payload)
    output = tmp_path / "rejected"
    # When / Then
    with pytest.raises(ValueError) as rejected:
        render_research_figures(output, copied, dpi=72, decimal_places=2)
    assert not output.exists()
    _write(tmp_path / "rejection.json", {"mutation": mutation, "error": str(rejected.value),
                                         "live_invocation": False})


def test_same_family_pair_rejects(campaigns: tuple[Path, Path], tmp_path: Path) -> None:
    # Given / When / Then
    with pytest.raises(ResearchFigureError, match="distinct"):
        render_research_figures(tmp_path / "rejected", campaigns[0], comparison_path=campaigns[0],
                                dpi=72, decimal_places=2)
    assert not (tmp_path / "rejected").exists()


def test_pair_rejects_different_source_report_bytes(
    campaigns: tuple[Path, Path], tmp_path: Path,
) -> None:
    # Given
    directory = tmp_path / "v"
    shutil.copytree(campaigns[1].parent, directory)
    source = directory / "source-report.json"
    source.write_bytes(source.read_bytes() + b"\n")
    assert validate_alignment_report(directory / "alignment-report.json")
    # When / Then
    with pytest.raises(ResearchFigureError, match="retained bytes differ"):
        render_research_figures(tmp_path / "rejected", campaigns[0],
                                comparison_path=directory / "alignment-report.json",
                                dpi=72, decimal_places=2)
    assert not (tmp_path / "rejected").exists()


def test_pair_guard_rejects_altered_numerical_data(campaigns: tuple[Path, Path]) -> None:
    # Given
    left, right = map(_report_input, campaigns)
    altered = right.report.model_copy(update={"numerical": right.report.numerical.model_copy(
        update={"rows": []})})
    # When / Then
    with pytest.raises(ResearchFigureError, match="numerical data differ"):
        _check_pair(left, ReportInput(path=right.path, sha256=right.sha256, report=altered))


@pytest.mark.parametrize("status", ["Unsatisfiable", "GaveUp"])
def test_validated_incomplete_saved_control_is_shown_honestly(
    copied: Path, tmp_path: Path, status: str,
) -> None:
    # Given
    payload = json.loads(copied.read_bytes())
    run = payload["logical"][0]
    capture_path = copied.parent / run["capture"]
    capture = json.loads(capture_path.read_bytes())
    stdout = capture_path.parent / capture["stdout"]["path"]
    before = stdout.read_bytes()
    after = before.replace(b"SZS status Satisfiable", f"SZS status {status}".encode())
    assert after != before
    stdout.write_bytes(after)
    capture["stdout"].update(size=len(after), sha256=sha256(after).hexdigest())
    capture["returncode"] = 0
    _write(capture_path, capture)
    run.update(capture_sha256=sha256(capture_path.read_bytes()).hexdigest(), observed=status,
               disposition="mismatch" if status == "Unsatisfiable" else "unresolved")
    payload["summary"].update(logical_matched=len(payload["logical"]) - 1,
                               logical_mismatched=int(status == "Unsatisfiable"),
                               logical_unresolved=int(status == "GaveUp"),
                               baseline_satisfiable=False, campaign_complete=False)
    payload["replay_boundary"] += " Synthetic saved-control mutation; not live solver evidence."
    _write(copied, payload)
    assert not validate_alignment_report(copied).summary.campaign_complete
    # When
    paths = render_research_figures(tmp_path / "incomplete", copied, dpi=72, decimal_places=2)
    # Then
    data = FigureInputs.model_validate_json(paths[2].read_bytes())
    assert data.reports[0].report.logical[0].observed == status
    assert not data.reports[0].report.summary.campaign_complete
    assert not data.reports[0].report.summary.semantic_validation


def test_long_full_provenance_is_retained_without_expanding_print(copied: Path, tmp_path: Path) -> None:
    # Given
    payload = json.loads(copied.read_bytes())
    payload["replay_boundary"] += " complete provenance" * 300
    _write(copied, payload)
    # When
    paths = render_research_figures(tmp_path / "complete", copied, dpi=72, decimal_places=2)
    # Then
    data = FigureInputs.model_validate_json(paths[2].read_bytes())
    assert data.height_mm == 210
    assert "Replay boundary: " + payload["replay_boundary"] in data.provenance
    parsed = Html()
    parsed.feed(paths[3].read_text())
    embedded = next(text for attrs, text in parsed.scripts if attrs.get("id") == "research-data")
    assert json.loads(embedded)["provenance"] == data.provenance
    assert any(attrs.get("id") == "complete-provenance" for _, attrs in parsed.tags)


def test_geometric_layout_refuses_unbounded_visible_text(rendered: list[Path]) -> None:
    data = FigureInputs.model_validate_json(rendered[2].read_bytes())
    with pytest.raises(ResearchFigureError, match="print layout"):
        _print_figure(data.model_copy(update={"boundary": "W" * 1000}), [])


def test_unsafe_source_strings_remain_inert(copied: Path, tmp_path: Path) -> None:
    # Given
    payload = json.loads(copied.read_bytes())
    attack = "</script><img src=x onerror=alert(1)> & \u2028\u2029"
    payload["replay_boundary"] = attack
    _write(copied, payload)
    # When
    paths = render_research_figures(tmp_path / "escaped", copied, dpi=72, decimal_places=2)
    # Then
    parsed = Html()
    parsed.feed(paths[3].read_text())
    embedded = next(text for attrs, text in parsed.scripts if attrs.get("id") == "research-data")
    assert "<" not in embedded and "&" not in embedded
    assert json.loads(embedded)["reports"][0]["report"]["replay_boundary"] == attack
    assert not any(tag == "img" or any(key.startswith("on") for key in attrs)
                   for tag, attrs in parsed.tags)


def test_explorer_has_no_remote_dependencies_and_javascript_rejects_invalid_syntax(
    rendered: list[Path], tmp_path: Path, project_root: Path,
) -> None:
    # Given
    parsed = Html()
    parsed.feed(rendered[3].read_text())
    node = shutil.which("node")
    assert node is not None
    executable = []
    for index, (attrs, text) in enumerate(parsed.scripts):
        assert "src" not in attrs
        if attrs.get("type") != "application/json":
            path = tmp_path / f"inline-{index}.js"
            path.write_text(text)
            executable.append(path)
    executable.append(project_root / "tests/manuscript/research_browser_scenarios.js")
    # When
    results = [subprocess.run([node, "--check", str(path)], capture_output=True, text=True,
                              check=False) for path in executable]
    # Then
    assert all(r.returncode == 0 for r in results), [r.stderr for r in results]
    assert not any(tag in {"link", "iframe", "img"} for tag, _ in parsed.tags)
    broken = tmp_path / "syntax-negative-control.js"
    broken.write_text("const = ;")
    rejected = subprocess.run([node, "--check", str(broken)], capture_output=True, text=True, check=False)
    assert rejected.returncode != 0 and "SyntaxError" in rejected.stderr
    (tmp_path / "syntax-negative-control.stderr").write_text(rejected.stderr)


def test_existing_artifacts_are_preserved(rendered: list[Path]) -> None:
    # Given
    before = [p.read_bytes() for p in rendered]
    data = FigureInputs.model_validate_json(before[2])
    # When / Then
    with pytest.raises(FileExistsError):
        render_research_figures(rendered[0].parent, Path(data.reports[0].path), dpi=72, decimal_places=2)
    assert before == [p.read_bytes() for p in rendered]

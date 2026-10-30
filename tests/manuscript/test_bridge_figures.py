"""Pure geometry/math checks and explicitly saved-packet integration tests."""

from __future__ import annotations

import json
import re
import subprocess
from fractions import Fraction
from hashlib import sha256
from html.parser import HTMLParser
from importlib.resources import files
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pytest
from defusedxml import ElementTree
from PIL import Image
from pydantic import ValidationError

from rikishi.bridge_figures import (
    BridgeFigureError,
    BridgeFigureInputs,
    _check_geometry,
    _control_figure,
    _curve,
    _energy_figure,
    _evidence_figure,
    _number,
    _retained,
    bridge_explorer_html,
    build_bridge_figure_inputs,
    render_bridge_figures,
)
from rikishi.bridge_models import BridgeError, FiniteWitness, WitnessEntities
from rikishi.fep import free_energy
from rikishi.runtime_artifacts import ArtifactError

if TYPE_CHECKING:
    from conftest import BridgePacket


class _Scripts(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.scripts: list[str] = []
        self.attributes: list[dict[str, str | None]] = []
        self.active = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "script":
            self.active = True
            self.scripts.append("")
            self.attributes.append(dict(attrs))

    def handle_data(self, data: str) -> None:
        if self.active:
            self.scripts[-1] += data

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self.active = False


class _VisibleCopy(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.capture = False
        self.excluded = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"body", "title"}:
            self.capture = True
        if tag in {"script", "style"}:
            self.excluded += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"body", "title"}:
            self.capture = False
        if tag in {"script", "style"}:
            self.excluded -= 1

    def handle_data(self, data: str) -> None:
        if self.capture and self.excluded == 0:
            self.parts.append(data)


def _late_definitions(html: str) -> tuple[str, ...]:
    parser = _VisibleCopy()
    parser.feed(html)
    visible = " ".join(" ".join(parser.parts).split())
    terms = {"FEP": "Free Energy Principle", "SUMO": "Suggested Upper Merged Ontology",
             "KL": "Kullback–Leibler", "KIF": "Knowledge Interchange Format",
             "FOL": "first-order logic", "HTML": "Hypertext Markup Language",
             "JSON": "JavaScript Object Notation", "SHA-256": "256-bit Secure Hash Algorithm"}
    late = []
    for abbreviation, name in terms.items():
        first = re.search(r"(?<!\w)" + re.escape(abbreviation) + r"(?!\w)", visible)
        definition = re.search(re.escape(name) + r"\s*\(" + re.escape(abbreviation) + r"\)", visible)
        if first is not None and (definition is None or definition.start() >= first.start()):
            late.append(abbreviation)
    return tuple(late)


def test_visible_acronyms_are_defined_before_use_with_late_definition_control() -> None:
    template = files("rikishi").joinpath("data/bridge-explorer.html").read_text()
    assert _late_definitions(template) == ()
    late = template.replace("<h1>", "<h1>FEP–SUMO ", 1)
    assert {"FEP", "SUMO"} <= set(_late_definitions(late))


def _late_figure_keys(text: str) -> tuple[str, ...]:
    terms = {"KL": "Kullback–Leibler divergence", "SHA-256": "Secure Hash Algorithm, 256-bit"}
    late = []
    for abbreviation, name in terms.items():
        first = re.search(r"(?<!\w)" + re.escape(abbreviation) + r"(?!\w)", text)
        definition = re.search(re.escape(name) + r"\s*\(" + re.escape(abbreviation) + r"\)", text)
        if first is not None and (definition is None or definition.start() >= first.start()):
            late.append(abbreviation)
    return tuple(late)


def test_standalone_figure_key_check_rejects_late_definitions() -> None:
    keys = "Kullback–Leibler divergence (KL); Secure Hash Algorithm, 256-bit (SHA-256)."
    assert _late_figure_keys(keys) == ()
    assert set(_late_figure_keys("Floating KL; packet SHA-256. " + keys)) == {"KL", "SHA-256"}


def test_complete_curve_has_actual_energy_and_both_endpoints() -> None:
    witness = FiniteWitness(
        id="pure-test", namespace="PureTest", prior=("1/4", "3/4"),
        likelihood=("1/2", "2/3"), candidate=("1/3", "2/3"),
        entities=WitnessEntities(model="BridgeModel", representation="BridgeRepresentation",
                                 calculation="BridgeCalculation", result="BridgeResult",
                                 agent="BridgeAgent"))
    curve = _curve(witness)
    assert len(curve.q) == 201
    assert curve.q[0] == 0 and curve.q[-1] == 1
    assert curve.q == tuple(sorted(set(curve.q)))
    for q, energy, kl in zip(curve.q, curve.free_energy, curve.kl, strict=True):
        oracle = free_energy((0.25, 0.75), (0.5, 2 / 3), (q, 1 - q))
        assert energy == oracle["free_energy"]
        assert kl == oracle["kl_to_posterior"]
        assert energy == pytest.approx(kl + curve.surprise, abs=1e-14)


def test_small_floating_residual_is_retained_at_print_precision() -> None:
    assert float(_number(-1e-17, 6)) == -1e-17
    assert float(_number(1e-17, 6)) == 1e-17
    assert _number(-0.0, 6) == "0.000000"
    assert _number(0.25, 6) == "0.250000"


def test_geometry_gate_rejects_clipping_and_illegible_type() -> None:
    from matplotlib.figure import Figure

    fig = Figure(figsize=(4, 3))
    label = fig.text(0.2, 0.5, "in bounds", fontsize=9)
    _check_geometry(fig)
    label.set_x(1.01)
    with pytest.raises(BridgeFigureError, match="bounds"):
        _check_geometry(fig)
    label.set_x(0.2)
    label.set_fontsize(6)
    with pytest.raises(BridgeFigureError, match="7.5"):
        _check_geometry(fig)
    label.set_fontsize(9)
    fig.text(0.2, 0.5, "overlap", fontsize=9)
    with pytest.raises(BridgeFigureError, match="overlap"):
        _check_geometry(fig)
    fig.clear()


@pytest.mark.parametrize(("dpi", "places"), [(True, 6), (71, 6), (1201, 6),
                                               (300, True), (300, -1), (300, 9)])
def test_presentation_limits_reject_before_reading(dpi: int, places: int) -> None:
    with pytest.raises(BridgeFigureError):
        build_bridge_figure_inputs(Path("missing.json"), trusted_report_sha256="0" * 64,
                                   dpi=dpi, decimal_places=places)


def test_output_boundaries_reject_before_packet_access(tmp_path: Path) -> None:
    occupied = tmp_path / "occupied"
    occupied.mkdir()
    with pytest.raises(FileExistsError):
        render_bridge_figures(tmp_path / "missing.json", occupied,
                              trusted_report_sha256="0" * 64)
    alias = tmp_path / "alias"
    alias.symlink_to(occupied, target_is_directory=True)
    with pytest.raises(FileExistsError):
        render_bridge_figures(tmp_path / "missing.json", alias,
                              trusted_report_sha256="0" * 64)
    with pytest.raises(ArtifactError, match="symlink"):
        render_bridge_figures(tmp_path / "missing.json", alias / "new",
                              trusted_report_sha256="0" * 64)
    with pytest.raises(ArtifactError):
        render_bridge_figures(tmp_path / "missing.json", tmp_path / "absent" / "new",
                              trusted_report_sha256="0" * 64)
    assert not (tmp_path / "absent").exists()


def test_retained_text_requires_matching_hash_and_unlinked_path(tmp_path: Path) -> None:
    path = tmp_path / "retained.txt"
    original = "Retained text: <script> is inert data.\n"
    path.write_text(original)
    digest = sha256(original.encode()).hexdigest()
    assert _retained(tmp_path, path.name, digest) == original
    path.write_text(original + "changed\n")
    with pytest.raises(BridgeError, match="changed"):
        _retained(tmp_path, path.name, digest)
    alias = tmp_path / "alias.txt"
    alias.symlink_to(path)
    with pytest.raises(ArtifactError, match="symlink"):
        _retained(tmp_path, alias.name, digest)


def test_offline_template_script_syntax_with_rejecting_control(tmp_path: Path) -> None:
    template = files("rikishi").joinpath("data/bridge-explorer.html").read_text()
    assert template.count("__BRIDGE_DATA__") == 1
    parser = _Scripts()
    parser.feed(template)
    scripts = [script for attrs, script in zip(parser.attributes, parser.scripts, strict=True)
               if attrs.get("type") != "application/json"]
    assert scripts
    for index, script in enumerate(scripts):
        target = tmp_path / f"template-{index}.js"
        target.write_text(script)
        subprocess.run(["node", "--check", str(target)], check=True,
                       capture_output=True, text=True)
    bad = tmp_path / "invalid.js"
    bad.write_text("function {")
    rejected = subprocess.run(["node", "--check", str(bad)], check=False,
                              capture_output=True, text=True)
    assert rejected.returncode != 0 and rejected.stderr


@pytest.fixture(scope="module")
def inputs(bridge_packet: BridgePacket) -> BridgeFigureInputs:
    return build_bridge_figure_inputs(bridge_packet.path,
                                      trusted_report_sha256=bridge_packet.sha256, dpi=100)


@pytest.mark.integration
def test_packet_bound_inputs_deduplicate_captures_and_proofs(
    bridge_packet: BridgePacket, inputs: BridgeFigureInputs,
) -> None:
    report = bridge_packet.report
    assert inputs.report == report
    assert inputs.report_sha256 == bridge_packet.sha256
    assert len(inputs.cases) == len(report.cases)
    assert {(row.case_id, row.prover) for row in inputs.cases} == {
        (row.id, row.prover) for row in report.cases}
    assert "theorem posterior_reconstruction" in inputs.lean_source
    assert inputs.lean_proofs
    assert set(inputs.lean_proofs) < set(report.lean.declarations)
    assert all(not name.endswith((".prior", ".kernel", ".candidate"))
               for name in inputs.lean_proofs)
    commands = (*report.lean.commands, *(row.command for row in report.lean.environments),
                *(row.command for row in report.lean.controls))
    assert len(inputs.lean_logs) == len(commands)
    assert len(inputs.lean_sources) == len(report.lean.environments) + len(report.lean.controls)
    for actual, command in zip(inputs.lean_logs, commands, strict=True):
        assert actual.path == command.log
        assert actual.sha256 == command.log_sha256
        assert sha256(actual.text.encode()).hexdigest() == command.log_sha256
        assert actual.command == command.command
        assert actual.returncode == command.returncode
        assert actual.timeout_seconds == command.timeout_seconds
        assert actual.elapsed_seconds == command.elapsed_seconds
        assert actual.timed_out == command.timed_out
    for source in inputs.lean_sources:
        assert sha256(source.text.encode()).hexdigest() == source.sha256
    assert {(row.kind, row.evidence_id, row.path) for row in inputs.lean_logs} == {
        *(("main", row.log, row.log) for row in report.lean.commands),
        *(("positive-environment", row.id, row.command.log) for row in report.lean.environments),
        *(("negative-control", row.id, row.command.log) for row in report.lean.controls)}
    assert {(row.kind, row.id, row.path, row.sha256) for row in inputs.lean_sources} == {
        *(("positive-environment", row.id, row.source, row.source_sha256)
          for row in report.lean.environments),
        *(("negative-control", row.id, row.source, row.source_sha256)
          for row in report.lean.controls)}
    assert any(row.returncode != 0 for row in inputs.lean_logs)
    assert sha256(inputs.extension.encode()).hexdigest() == report.extension_sha256
    assert len(inputs.witness_facts) == len(report.witnesses)
    bindings = {(row.id, row.prover): row for row in report.cases}
    for row in inputs.cases:
        assert sha256(row.problem.encode()).hexdigest() == bindings[(row.case_id, row.prover)].problem_sha256
    assert "lean_source" not in type(inputs.cases[0]).model_fields
    with pytest.raises(ValidationError):
        inputs.dpi = 200
    with pytest.raises(BridgeError, match="SHA-256"):
        build_bridge_figure_inputs(bridge_packet.path, trusted_report_sha256="0" * 64)


@pytest.mark.integration
def test_figures_have_data_coordinates_actual_categorical_statuses_and_geometry(
    inputs: BridgeFigureInputs,
) -> None:
    import matplotlib
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.text import Text

    with matplotlib.rc_context({"text.parse_math": False}):
        evidence = _evidence_figure(inputs)
        energy = _energy_figure(inputs)
        controls = _control_figure(inputs)
        for fig in (evidence, energy, controls):
            _check_geometry(fig)
            assert fig.get_figwidth() * 25.4 == pytest.approx(191.9)
            canvas = FigureCanvasAgg(fig)
            canvas.draw()
            renderer = canvas.get_renderer()
            text = [artist for artist in fig.findobj(Text)
                    if artist.get_visible() and artist.get_text()]
            text.sort(key=lambda artist: (-artist.get_window_extent(renderer).y1,
                                           artist.get_window_extent(renderer).x0))
            reading_order = " ".join(artist.get_text() for artist in text)
            assert _late_figure_keys(reading_order) == ()
            assert re.search(r"\bIDs?\b", reading_order) is None
            assert f"packet digest prefix (16 hex): {inputs.report_sha256[:16]}" in reading_order
        scenario = next(row for row in inputs.report.scenarios
                        if row.witness_id == inputs.report.witnesses[0].id
                        and row.role == "result" and row.query.lstrip().startswith("(exists"))
        figure_text = " ".join(" ".join(artist.get_text().split()) for artist in evidence.texts)
        assert scenario.id in figure_text
        assert " ".join(scenario.query.split()) in figure_text
        assert (f"source digest prefix (16 hex): {inputs.report.lean.source_sha256[:16]}"
                in figure_text)
        for index, witness in enumerate(inputs.report.witnesses):
            row = next(item for item in inputs.report.numerical if item.witness_id == witness.id)
            axis = energy.axes[2 * index + 1]
            np.testing.assert_array_equal(axis.lines[0].get_xdata(), inputs.curves[index].q)
            np.testing.assert_array_equal(axis.lines[0].get_ydata(), inputs.curves[index].free_energy)
            np.testing.assert_allclose(np.asarray(axis.collections[0].get_offsets())[0],
                                       [float(Fraction(row.exact_posterior[0])), row.result.surprise])
            np.testing.assert_allclose(np.asarray(axis.collections[1].get_offsets())[0],
                                       [float(Fraction(witness.candidate[0])), row.result.free_energy])
        assert len(controls.axes[0].patches) == len(inputs.report.cases)
        cells = [item.get_text() for item in controls.axes[0].texts]
        expected = {"Satisfiable": "SAT", "Theorem": "THM",
                    "CounterSatisfiable": "C-SAT", "Unsatisfiable": "UNSAT"}
        assert sorted(cells) == sorted(expected[row.observed] for row in inputs.report.cases)
        for fig in (evidence, energy, controls):
            fig.clear()


@pytest.mark.integration
def test_export_metadata_vector_geometry_and_no_overwrite(
    bridge_packet: BridgePacket, tmp_path: Path,
) -> None:
    output = tmp_path / "figures"
    paths = render_bridge_figures(bridge_packet.path, output,
                                  trusted_report_sha256=bridge_packet.sha256, dpi=100)
    assert len(paths) == 8
    data = BridgeFigureInputs.model_validate_json((output / "bridge-figure-inputs.json").read_bytes())
    assert data.report_sha256 == bridge_packet.sha256
    assert data.report == bridge_packet.report
    for path in paths:
        assert path.stat().st_size > 0
        if path.suffix == ".png":
            with Image.open(path) as image:
                assert image.width == int(data.width_mm / 25.4 * data.dpi)
                assert data.report_sha256 in image.info["Description"]
        if path.suffix == ".svg":
            svg = ElementTree.parse(path).getroot()
            assert svg is not None
            assert not any(node.tag.endswith("}image") for node in svg.iter())
            assert data.report_sha256 in path.read_text()
    before = {path.name: path.read_bytes() for path in paths}
    with pytest.raises(FileExistsError):
        render_bridge_figures(bridge_packet.path, output,
                              trusted_report_sha256=bridge_packet.sha256)
    assert before == {path.name: path.read_bytes() for path in paths}
    alias = tmp_path / "alias"
    alias.symlink_to(output, target_is_directory=True)
    with pytest.raises(FileExistsError):
        render_bridge_figures(bridge_packet.path, alias,
                              trusted_report_sha256=bridge_packet.sha256)


@pytest.mark.integration
def test_failed_trust_creates_no_output(bridge_packet: BridgePacket, tmp_path: Path) -> None:
    output = tmp_path / "rejected"
    with pytest.raises(BridgeError, match="SHA-256"):
        render_bridge_figures(bridge_packet.path, output, trusted_report_sha256="0" * 64)
    assert not output.exists()


@pytest.mark.integration
def test_explorer_embeds_inert_exact_json_and_valid_script(
    inputs: BridgeFigureInputs, tmp_path: Path,
) -> None:
    hostile = "</script><img src=x onerror=alert(1)>&\u2028\u2029"
    changed = inputs.model_copy(update={"lean_source": inputs.lean_source + hostile})
    html = bridge_explorer_html(changed)
    assert hostile not in html
    assert "\\u003c/script\\u003e" in html
    parser = _Scripts()
    parser.feed(html)
    payloads = [text for attrs, text in zip(parser.attributes, parser.scripts, strict=True)
                if attrs.get("type") == "application/json"]
    assert len(payloads) == 1
    assert json.loads(payloads[0])["lean_source"] == changed.lean_source
    for index, (attrs, script) in enumerate(zip(parser.attributes, parser.scripts, strict=True)):
        if attrs.get("type") != "application/json":
            target = tmp_path / f"script-{index}.js"
            target.write_text(script)
            subprocess.run(["node", "--check", str(target)],
                           check=True, capture_output=True, text=True)
    assert not re.search(r"\b(?:fetch|XMLHttpRequest|WebSocket)\s*\(", html)
    assert not re.search(r"\.innerHTML\s*=", html)

"""Derive manuscript observations from the complete shared-witness packet."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
from math import isfinite, log
from pathlib import Path

from rikishi.bridge_models import BridgeReport
from rikishi.bridge_replay import validate_bridge_report
from rikishi.manuscript_provenance import require_evidence
from rikishi.runtime_artifacts import read_regular


@dataclass(frozen=True, slots=True)
class BridgeContext:
    report: BridgeReport
    values: dict[str, str]
    input_sha256: dict[str, str]


def _display_number(value: float, places: int) -> str:
    fixed = f"{value:.{places}f}"
    return f"{value:.{places}e}" if value != 0 and float(fixed) == 0 else fixed


def load_bridge_context(directory: Path, *, decimal_places: int) -> BridgeContext:
    """Require actual Lean controls, finite values and complete two-prover outcomes."""
    if type(decimal_places) is not int or not 0 <= decimal_places <= 15:
        raise ValueError("decimal_places must be an integer from zero through fifteen")
    path = directory / "bridge-report.json"
    digest = sha256(read_regular(path)).hexdigest()
    report = validate_bridge_report(path, trusted_report_sha256=digest)
    require_evidence(report.provers == ("e", "v") and report.summary.passed,
                     "Publication requires a complete two-prover finite bridge campaign")
    require_evidence(bool(report.lean.declarations) and bool(report.lean.controls)
                     and all(item.rejected for item in report.lean.controls)
                     and len(report.lean.environments) == len(report.lean.controls)
                     and all(item.command.returncode == 0 for item in report.lean.environments)
                     and all(item.passed for item in report.numerical),
                     "Publication requires compiled Lean obligations and rejected controls")
    witnesses = {item.id: item for item in report.witnesses}
    groups = {item.id: item.witness_id for item in report.scenarios}
    totals = Counter(groups[item.group] for item in report.cases)
    matched = Counter(groups[item.group] for item in report.cases if item.matched)
    rows = ["| Witness | Posterior (false, true) | Free energy / nats | Floating divergence / nats | Native matched/total |",
            "| --- | --- | ---: | ---: | ---: |"]
    exact = ["| Witness | Prior p | Likelihood K(s,true) | Joint pK | Evidence Z | Posterior | Candidate q |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    for row in report.numerical:
        witness = witnesses[row.witness_id]
        posterior = ", ".join(row.exact_posterior)
        rows.append(f"| {witness.id} | ({posterior}) | {_display_number(row.result.free_energy, decimal_places)} | "
                    f"{_display_number(row.result.kl_to_posterior, decimal_places)} | "
                    f"{matched[witness.id]}/{totals[witness.id]} |")
        joint = tuple(str(Fraction(p) * Fraction(k))
                      for p, k in zip(witness.prior, witness.likelihood, strict=True))
        vectors = [", ".join(vector) for vector in (
            witness.prior, witness.likelihood, joint, row.exact_posterior, witness.candidate)]
        label = witness.id.split("-", 1)[0].title()
        exact.append(f"| {label} | ({vectors[0]}) | ({vectors[1]}) | ({vectors[2]}) | "
                     f"{row.evidence} | ({vectors[3]}) | ({vectors[4]}) |")
    from rikishi.witness_research import build_witness_research, research_tables

    channel_table, scaling_table = research_tables(build_witness_research(report, digest))
    from rikishi.witness_dynamics import build_witness_dynamics, dynamics_table

    sequential_table = dynamics_table(build_witness_dynamics(report, digest))
    from rikishi.witness_sequence_atlas import build_sequence_atlas, sequence_atlas_table

    mixed_table = sequence_atlas_table(build_sequence_atlas(report.witnesses, digest))
    require_evidence(sha256(read_regular(path)).hexdigest() == digest,
                     "Bridge report changed during publication context loading")
    return BridgeContext(report, {
        "BRIDGE_WITNESSES": str(report.summary.witnesses),
        "BRIDGE_SCENARIOS": str(report.summary.scenarios),
        "BRIDGE_NATIVE_RUNS": str(report.summary.total),
        "BRIDGE_LEAN_DECLARATIONS": str(report.summary.lean_declarations),
        "BRIDGE_SUMMARY_TABLE": "\n".join(rows),
        "BRIDGE_EXACT_TABLE": "\n".join(exact),
        "WITNESS_CHANNEL_TABLE": channel_table,
        "WITNESS_SCALING_TABLE": scaling_table,
        "WITNESS_SEQUENTIAL_TABLE": sequential_table,
        "WITNESS_SEQUENCE_ATLAS_TABLE": mixed_table,
        "BRIDGE_WITNESS_LABELS": "; ".join(
            f"{w.id.split('-', 1)[0].title()} = `{w.id}`" for w in report.witnesses) + ".",
        "BRIDGE_REPORT_SHA256": digest,
    }, {"bridge-report.json": digest})


def verify_bridge_content(text: str, context: BridgeContext, edition: str) -> None:
    """Require each report-derived numerical/native row in the actual edition."""
    compact = re.sub(r"\s+", "", text)
    for row in [line for key in ("BRIDGE_SUMMARY_TABLE", "BRIDGE_EXACT_TABLE",
                                "WITNESS_CHANNEL_TABLE", "WITNESS_SCALING_TABLE",
                                "WITNESS_SEQUENTIAL_TABLE", "WITNESS_SEQUENCE_ATLAS_TABLE")
                for line in context.values[key].splitlines()[2:]]:
        expected = "".join(cell.strip() for cell in row.strip("|").split("|"))
        require_evidence(re.sub(r"\s+", "", expected) in compact,
                         f"Bridge result row missing: {edition}, {row}")


def verify_bridge_figures(root: Path, context: BridgeContext, *, dpi: int, decimal_places: int) -> None:
    """Check copied figure evidence and independently recompute the plotted finite curves."""
    from defusedxml import ElementTree
    from PIL import Image

    from rikishi.bridge_figures import (
        BridgeFigureInputs,
        bridge_explorer_html,
        build_bridge_figure_inputs,
    )

    directory = root / "output/manuscript/figures"
    data = BridgeFigureInputs.model_validate_json(read_regular(directory / "bridge-figure-inputs.json"))
    expected = build_bridge_figure_inputs(
        root / "output/manuscript/bridge/bridge-report.json",
        trusted_report_sha256=context.input_sha256["bridge-report.json"],
        dpi=dpi, decimal_places=decimal_places,
    )
    require_evidence(data == expected and data.report == context.report,
                     "Bridge figure inputs differ from the verified packet")
    import json

    abstract_inputs = json.loads(read_regular(directory / "witness-abstracts.json"))
    require_evidence(abstract_inputs == {
        "report_sha256": data.report_sha256, "study_id": data.report.study_id,
        "witnesses": [w.model_dump(mode="json") for w in data.report.witnesses],
        "source_claims": [c.model_dump(mode="json") for c in data.report.source_claims],
        "numerical": [n.model_dump(mode="json") for n in data.report.numerical],
        "width_mm": 191.9, "height_mm": 205, "dpi": dpi,
    }, "Graphical abstract inputs differ from verified witness/source/numerical evidence")
    curve_ids = [curve.witness_id for curve in data.curves]
    require_evidence(len(set(curve_ids)) == len(curve_ids)
                     and set(curve_ids) == {w.id for w in context.report.witnesses},
                     "Bridge curve witness inventory differs")
    for witness in context.report.witnesses:
        curve = next(item for item in data.curves if item.witness_id == witness.id)
        require_evidence(len(curve.q) == len(curve.free_energy) == len(curve.kl)
                         and len(curve.q) >= 2 and curve.q[0] == 0 and curve.q[-1] == 1
                         and all(isfinite(value) for value in curve.q)
                         and all(0 < right - left <= 0.025
                                 for left, right in zip(curve.q[:-1], curve.q[1:], strict=True)),
                         "Bridge energy curve does not cover the finite candidate interval")
        prior = tuple(float(Fraction(value)) for value in witness.prior)
        likelihood = tuple(float(Fraction(value)) for value in witness.likelihood)
        joint = tuple(p * l for p, l in zip(prior, likelihood, strict=True))
        evidence = sum(joint)
        posterior = tuple(value / evidence for value in joint)
        surprise = -log(evidence)
        require_evidence(abs(curve.surprise - surprise) <= data.study.tolerance,
                         "Bridge plotted surprise differs from the finite input")
        for q0, energy, divergence in zip(curve.q, curve.free_energy, curve.kl, strict=True):
            candidate = (q0, 1 - q0)
            objective = sum(q * (log(q) - log(j)) for q, j in zip(candidate, joint, strict=True) if q > 0)
            relative = sum(q * (log(q) - log(p)) for q, p in zip(candidate, posterior, strict=True) if q > 0)
            require_evidence(isfinite(energy) and isfinite(divergence)
                             and abs(energy - objective) <= data.study.tolerance
                             and abs(divergence - relative) <= data.study.tolerance,
                             "Bridge plotted energy or divergence differs from direct finite logarithms")
    names = ("bridge-evidence", "bridge-free-energy", "bridge-native-controls")
    description = f"Verified bridge packet SHA-256 {data.report_sha256}"
    for name in names:
        with Image.open(directory / f"{name}.png") as image:
            require_evidence(image.info.get("Description") == description
                             and abs(image.width - data.width_mm / 25.4 * dpi) <= 1,
                             f"Bridge PNG provenance or physical width differs: {name}")
        svg = ElementTree.fromstring(read_regular(directory / f"{name}.svg"))
        require_evidence(svg.findtext(".//{http://purl.org/dc/elements/1.1/}description") == description,
                         f"Bridge SVG provenance differs: {name}")
    require_evidence((directory / "bridge-explorer.html").read_text() == bridge_explorer_html(data),
                     "Bridge explorer differs from its canonical data and template")
    files = [*(f"{name}.{extension}" for name in names for extension in ("png", "svg")),
             "bridge-figure-inputs.json", "bridge-explorer.html"]
    for name in files:
        original = read_regular(directory / name)
        for other in ("output/figures", "output/web/figures"):
            require_evidence(read_regular(root / other / name) == original,
                             f"Bridge figure evidence copy differs: {other}/{name}")
    from rikishi.witness_research import verify_witness_research
    from rikishi.witness_research_figures import RESEARCH_FIGURES

    verify_witness_research(read_regular(directory / "witness-research.json"),
                            context.report, context.input_sha256["bridge-report.json"])
    description = "Derived finite witness research; bridge packet SHA-256 " + data.report_sha256
    for name in RESEARCH_FIGURES:
        with Image.open(directory / f"{name}.png") as image:
            require_evidence(image.info.get("Description") == description
                             and image.size == (2266, 2185),
                             f"Witness research PNG provenance or geometry differs: {name}")
        svg = ElementTree.fromstring(read_regular(directory / f"{name}.svg"))
        require_evidence(svg.findtext(".//{http://purl.org/dc/elements/1.1/}description") == description,
                         f"Witness research SVG provenance differs: {name}")
    for name in ["witness-research.json", *(f"{n}.{s}" for n in RESEARCH_FIGURES
                                          for s in ("png", "svg"))]:
        for other in ("output/figures", "output/web/figures"):
            require_evidence(read_regular(root / other / name) == read_regular(directory / name),
                             f"Witness research evidence copy differs: {other}/{name}")
    from rikishi.witness_dynamics import verify_witness_dynamics

    verify_witness_dynamics(read_regular(directory / "witness-dynamics.json"),
                            context.report, context.input_sha256["bridge-report.json"])
    description = ("Derived numerical experiment; no new Lean or native SUMO results; "
                   "bridge packet SHA-256 " + data.report_sha256)
    with Image.open(directory / "witness-sequential.png") as image:
        require_evidence(image.info.get("Description") == description
                         and image.size == (2266, 2421),
                         "Sequential witness PNG provenance or geometry differs")
    svg = ElementTree.fromstring(read_regular(directory / "witness-sequential.svg"))
    require_evidence(svg.findtext(".//{http://purl.org/dc/elements/1.1/}description") == description,
                     "Sequential witness SVG provenance differs")
    for name in ("witness-dynamics.json", "witness-sequential.png", "witness-sequential.svg"):
        for other in ("output/figures", "output/web/figures"):
            require_evidence(read_regular(root / other / name) == read_regular(directory / name),
                             f"Witness research evidence copy differs: {other}/{name}")
    from rikishi.witness_sequence_atlas import (
        build_sequence_atlas,
        verify_sequence_atlas,
        verify_sequence_atlas_svg,
    )

    verify_sequence_atlas(read_regular(directory / "witness-sequences.json"),
                          context.report.witnesses, context.input_sha256["bridge-report.json"])
    description = ("Derived mixed-sequence arithmetic; no new Lean or native SUMO results; "
                   "bridge packet SHA-256 " + data.report_sha256)
    with Image.open(directory / "witness-sequences.png") as image:
        require_evidence(image.info.get("Description") == description
                         and image.size == (2266, 2421),
                         "Mixed-sequence atlas PNG provenance or geometry differs")
    svg = ElementTree.fromstring(read_regular(directory / "witness-sequences.svg"))
    verify_sequence_atlas_svg(read_regular(directory / "witness-sequences.svg"),
                             build_sequence_atlas(context.report.witnesses,
                                                  context.input_sha256["bridge-report.json"]))
    require_evidence(svg.findtext(".//{http://purl.org/dc/elements/1.1/}description") == description,
                     "Mixed-sequence atlas SVG provenance differs")
    for name in ("witness-sequences.json", "witness-sequences.png", "witness-sequences.svg"):
        for other in ("output/figures", "output/web/figures"):
            require_evidence(read_regular(root / other / name) == read_regular(directory / name),
                             f"Mixed-sequence atlas evidence copy differs: {other}/{name}")
    event_source = read_regular(root / "examples/EventTransport.lean")
    for other in ("output/manuscript/figures", "output/figures", "output/web/figures"):
        require_evidence(read_regular(root / other / "EventTransport.lean") == event_source,
                         f"Event-transport proof source copy differs: {other}")

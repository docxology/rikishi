"""Read-only, digest-bound inspection of shared finite witnesses and native cases."""

from __future__ import annotations

import re
from hashlib import sha256
from pathlib import Path
from typing import assert_never

from rikishi.bridge_models import (
    BridgeError,
    BridgeReport,
    BridgeScenario,
    FiniteWitness,
    NumericalWitness,
)
from rikishi.inference_models import CaseOutcome, Frozen, Selection, SourceClaim
from rikishi.inference_views import CaseSelection, report_path
from rikishi.runtime_artifacts import (
    checked_source_path,
    load_capture,
    read_regular,
    verified_bytes,
)


class BridgeCaseView(Frozen):
    """The observed native problem joined to the same mathematical witness."""

    case: CaseOutcome
    scenario: BridgeScenario
    witness: FiniteWitness
    numerical: NumericalWitness
    source_claims: tuple[SourceClaim, ...]
    active_source_claims: tuple[SourceClaim, ...]
    active_selections: tuple[Selection, ...]
    active_assumptions: tuple[str, ...]
    omitted_source_lines: tuple[int, ...]
    omitted_assumption: str | None
    conjecture: str | None
    refutation_premise: str | None
    lean_declarations: tuple[str, ...]
    lean_source: str
    lean_source_sha256: str
    command: tuple[str, ...]
    problem: str
    stdout: str
    stderr: str
    scope: str


def inspect_report(root: Path, relative: str, digest: str) -> BridgeReport:
    """Replay a saved packet against a required independently retained digest."""
    from rikishi.bridge_replay import validate_bridge_report

    if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise BridgeError("sha256 must contain exactly 64 lowercase hexadecimal characters")
    return validate_bridge_report(report_path(root, relative), trusted_report_sha256=digest)


def _retained(directory: Path, relative: str, digest: str) -> bytes:
    path = checked_source_path(directory / relative)
    if not path.is_relative_to(directory):
        raise BridgeError("Retained bridge input escapes its packet directory")
    data = read_regular(path)
    if sha256(data).hexdigest() != digest:
        raise BridgeError("Retained bridge input changed after report replay")
    return data


def _case_view(directory: Path, report: BridgeReport, run: CaseOutcome) -> BridgeCaseView:
    from rikishi.bridge_study import mass_facts

    scenario = next((item for item in report.scenarios if item.id == run.group), None)
    if scenario is None:
        raise BridgeError("Bridge case has no registered scenario")
    witness = next((item for item in report.witnesses if item.id == scenario.witness_id), None)
    numerical = next((item for item in report.numerical if item.witness_id == scenario.witness_id), None)
    if witness is None or numerical is None:
        raise BridgeError("Bridge scenario has no shared numerical witness")
    _retained(directory, run.capture, run.capture_sha256)
    capture_path = directory / run.capture
    capture = load_capture(capture_path, run.invocation_id)
    source = _retained(directory, report.lean.source, report.lean.source_sha256)
    selected_lines = {item.line for item in scenario.selections}
    omitted_lines = tuple(item.line for index, item in enumerate(scenario.selections)
                          if run.kind == "removed-premise" and index == scenario.removed_selection)
    active_selections = tuple(item for index, item in enumerate(scenario.selections)
                               if not (run.kind == "removed-premise" and index == scenario.removed_selection))
    active_lines = {item.line for item in active_selections}
    assumptions = (*scenario.assumptions, *mass_facts(witness))
    active_assumptions = tuple(value for index, value in enumerate(assumptions)
                               if not (run.kind == "removed-premise" and index == scenario.removed_assumption))
    omitted_assumption = (assumptions[scenario.removed_assumption]
                          if run.kind == "removed-premise" and scenario.removed_assumption is not None else None)
    match run.kind:
        case "background":
            conjecture, refutation = None, None
        case "refutation":
            conjecture, refutation = None, f"(not {scenario.query})"
        case "negative":
            conjecture, refutation = scenario.negative_query, None
        case "positive" | "removed-premise":
            conjecture, refutation = scenario.query, None
        case unreachable:
            assert_never(unreachable)
    return BridgeCaseView(
        case=run, scenario=scenario, witness=witness, numerical=numerical,
        source_claims=tuple(item for item in report.source_claims if item.line in selected_lines),
        active_source_claims=tuple(item for item in report.source_claims
                                   if item.line in active_lines), active_selections=active_selections,
        active_assumptions=active_assumptions, omitted_source_lines=omitted_lines,
        omitted_assumption=omitted_assumption, conjecture=conjecture, refutation_premise=refutation,
        lean_declarations=tuple(name for name in report.lean.declarations
                                if witness.namespace in name.split(".")),
        lean_source=source.decode("utf-8"), lean_source_sha256=report.lean.source_sha256,
        command=tuple(capture.command),
        problem=verified_bytes(capture.problem, capture_path.parent).decode("utf-8"),
        stdout=verified_bytes(capture.stdout, capture_path.parent).decode("utf-8"),
        stderr=verified_bytes(capture.stderr, capture_path.parent).decode("utf-8"),
        scope=("Shared inputs and explicitly separate obligations: exact selected SUMO premises, "
               "captured native outcome, concrete Lean declarations and finite numerical values. "
               "This inspection runs no prover or compiler and checks no proof-calculus steps."),
    )


def inspect_case(root: Path, selection: CaseSelection) -> BridgeCaseView:
    """Expose actual source, Lean witness and captured output without running tools."""
    report = inspect_report(root, selection.report, selection.sha256)
    run = next((item for item in report.cases
                if item.id == selection.case_id and item.prover == selection.prover), None)
    if run is None:
        raise KeyError("Bridge case not found in the verified report")
    return _case_view(report_path(root, selection.report).parent, report, run)


def inspect_cases(root: Path, relative: str, digest: str) -> tuple[BridgeCaseView, ...]:
    """Build an offline case inventory with one complete packet replay."""
    report = inspect_report(root, relative, digest)
    directory = report_path(root, relative).parent
    return tuple(_case_view(directory, report, run) for run in report.cases)

"""Digest-bound portable reconstruction of a concrete finite bridge packet."""

from __future__ import annotations

from hashlib import sha256
from importlib.resources import files
from pathlib import Path
from typing import Final

from rikishi.bridge_compiler import validate_lean
from rikishi.bridge_models import (
    BridgeError,
    BridgeReport,
    BridgeStudy,
    BridgeSummary,
    LeanEvidence,
    NumericalWitness,
)
from rikishi.bridge_study import (
    NUMERICAL,
    cases,
    catalog,
    derive_source_claims,
    extension,
    numerical,
    study_sha256,
)
from rikishi.inference_models import CaseOutcome
from rikishi.inference_replay import IMPLEMENTATION as INFERENCE_IMPLEMENTATION
from rikishi.inference_replay import replay_case
from rikishi.runtime_artifacts import checked_source_path, read_regular

IMPLEMENTATION: Final = (*INFERENCE_IMPLEMENTATION, "bridge_models.py", "bridge_study.py",
                         "bridge_compiler.py", "bridge_runner.py", "bridge_replay.py", "fep.py",
                         "formal_verification.py")
BOUNDARY: Final = (
    "Shared rational witness data link generated Lean finite-law/posterior/KL obligations, "
    "Python numerical measurements and source-constrained first-order role scenarios. Local "
    "interpretations and uninterpreted rational KIF labels are explicit; no SUMO-to-Lean "
    "semantic preservation, floating-point correctness, whole-ontology consistency or empirical "
    "FEP claim. Portable replay requires an independently trusted outer digest and rederives "
    "the study, exact retained source, numerical manifest, authored extension, generated Lean "
    "source, problems and strict captured statuses with per-family background controls. "
    "Retained Lean compilation artifacts, commands, logs, axioms and dependency-identity "
    "receipts are checked for consistency; replay is not new Lean checking. Full external "
    "dependency artifact bytes are not retained or authenticated by replay. Neither retained "
    "compiler evidence nor prover captures authenticate historical process execution, and "
    "prover proof steps are not independently checked.")


def implementation_bindings() -> dict[str, str]:
    return {name: sha256(files("rikishi").joinpath(name).read_bytes()).hexdigest()
            for name in IMPLEMENTATION}


def summary(study: BridgeStudy, runs: tuple[CaseOutcome, ...],
            numbers: tuple[NumericalWitness, ...], lean: LeanEvidence) -> BridgeSummary:
    """Derive denominators and completion from actual observations only."""
    resolved = {"Theorem", "Unsatisfiable", "Satisfiable", "CounterSatisfiable", "ContradictoryAxioms"}
    matched = sum(run.matched for run in runs)
    unresolved = sum(run.observed not in resolved for run in runs)
    backgrounds = [run.observed == "Satisfiable" for run in runs if run.kind == "background"]
    background_ok = bool(backgrounds) and all(backgrounds)
    numbers_ok = sum(row.passed for row in numbers)
    controls_ok = sum(control.rejected for control in lean.controls)
    passed = (bool(runs) and matched == len(runs) and background_ok
              and numbers_ok == len(study.witnesses) and bool(lean.declarations)
              and controls_ok == len(lean.controls) and controls_ok >= 3
              and len(lean.environments) == len(lean.controls)
              and all(e.command.returncode == 0 and not e.command.timed_out
                      for e in lean.environments))
    return BridgeSummary(
        witnesses=len(study.witnesses), scenarios=len(study.scenarios),
        numerical_passed=numbers_ok, lean_declarations=len(lean.declarations),
        lean_controls=len(lean.controls), lean_controls_rejected=controls_ok,
        total=len(runs), matched=matched, mismatched=len(runs) - matched - unresolved,
        unresolved=unresolved, backgrounds_satisfiable=background_ok, passed=passed)


def validate_bridge_report(path: Path, *, trusted_report_sha256: str) -> BridgeReport:
    """Reconstruct saved evidence without invoking a compiler, prover or mutable upstream."""
    path = checked_source_path(path)
    raw = read_regular(path)
    if len(trusted_report_sha256) != 64 or sha256(raw).hexdigest() != trusted_report_sha256:
        raise BridgeError("Trusted bridge report SHA-256 mismatch")
    report = BridgeReport.model_validate_json(raw)
    directory = path.parent
    study = catalog()
    retained_study = BridgeStudy.model_validate_json(read_regular(checked_source_path(directory / "study.json")))
    if (retained_study != study or report.study_id != study.study_id
            or report.study_sha256 != study_sha256(study) or report.witnesses != study.witnesses
            or report.scenarios != study.scenarios or report.replay_boundary != BOUNDARY):
        raise BridgeError("Bridge authority, witness identities or trust boundary differ")
    claims = derive_source_claims(study, read_regular(checked_source_path(directory / "source/Merge.kif")))
    local = extension(study).encode()
    if (claims != report.source_claims or sha256(local).hexdigest() != report.extension_sha256
            or read_regular(checked_source_path(directory / "extension.kif")) != local):
        raise BridgeError("Source claims or local interpretation do not rederive")
    numbers = numerical(study)
    manifest = NUMERICAL.validate_json(read_regular(checked_source_path(directory / "numerical.json")))
    if report.numerical != numbers or manifest != numbers or not all(n.passed for n in numbers):
        raise BridgeError("Numerical witness manifest or results do not rederive")
    implementation = implementation_bindings()
    retained = {name: sha256(read_regular(checked_source_path(directory / "implementation" / name))).hexdigest()
                for name in IMPLEMENTATION}
    if report.implementation != implementation or retained != implementation:
        raise BridgeError("Current or retained bridge implementation differs from the campaign")
    source_lock = sha256(read_regular(checked_source_path(directory / "sumo.lock.json"))).hexdigest()
    dependency_lock = sha256(read_regular(checked_source_path(directory / "uv.lock"))).hexdigest()
    if (source_lock != study.lock_sha256 or report.lock_sha256 != source_lock
            or report.dependency_lock_sha256 != dependency_lock
            or dependency_lock != study.dependency_lock_sha256):
        raise BridgeError("Source or dependency lock binding differs")
    if report.provers not in (("e",), ("v",), ("e", "v")):
        raise BridgeError("Unexpected or duplicate bridge prover families")
    binaries = {family: sha256(read_regular(checked_source_path(directory / "binaries" / f"{family}.bin"))).hexdigest()
                for family in report.provers}
    if report.binary_sha256 != binaries:
        raise BridgeError("Retained bridge executable bytes differ")
    validate_lean(directory, study, report.lean)
    generated = cases(study, claims)
    expected_ids = [(family, case.id) for family in report.provers for case in generated]
    if [(run.prover, run.id) for run in report.cases] != expected_ids:
        raise BridgeError("Missing, reordered, duplicate or unexpected bridge cases")
    by_id = {case.id: case for case in generated}
    backgrounds: dict[tuple[str, str], str] = {}
    for run in report.cases:
        case = by_id[run.id]
        observed = replay_case(directory, run, case, report.timeout_seconds)
        if run.prover_sha256 != binaries[run.prover]:
            raise BridgeError("Case executable differs from retained bytes")
        if run.kind == "background":
            backgrounds[(run.prover, run.group)] = observed
        matched = observed == case.expected and backgrounds.get((run.prover, run.group)) == "Satisfiable"
        if run.matched != matched or not matched:
            raise BridgeError("Bridge polarity or same-family background control failed")
    derived = summary(study, report.cases, numbers, report.lean)
    if report.summary != derived or not derived.passed:
        raise BridgeError("Bridge summary does not rederive or a required obligation failed")
    return report

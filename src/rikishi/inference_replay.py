from __future__ import annotations

from hashlib import sha256
from importlib.resources import files
from pathlib import Path

from rikishi.inference_models import (
    CaseOutcome,
    InferenceCase,
    InferenceError,
    InferenceReport,
    InferenceSummary,
)
from rikishi.inference_study import cases, derive_source_claims, load_study, study_sha256
from rikishi.runtime_artifacts import (
    SZS_STATUS,
    ProverKind,
    checked_source_path,
    expanded_problem,
    load_capture,
    read_regular,
    verified_bytes,
)

IMPLEMENTATION = (
    "inference_models.py", "inference_compiler.py", "inference_study.py",
    "inference_runner.py", "inference_replay.py", "kif.py", "runtime.py",
    "runtime_capture.py", "runtime_artifacts.py", "runtime_results.py",
    "runtime_process.py", "runtime_tptp.py",
)
BOUNDARY = (
    "Source-bound finite first-order fragments with declared predicate specialization and "
    "synthetic witness assumptions; no arbitrary SUMO translation or complete-corpus consistency. "
    "Portable replay checks an independently supplied report digest, exact retained source, "
    "study, compiler, problems, binary bytes and captured status interpretation. It does not "
    "authenticate historical process execution or independently check proof steps.")


def implementation_bindings() -> dict[str, str]:
    return {name: sha256(files("rikishi").joinpath(name).read_bytes()).hexdigest()
            for name in IMPLEMENTATION}


def command_flags(prover: ProverKind, timeout: int) -> list[str]:
    return (["--auto", "--tstp-format", "--proof-object", f"--cpu-limit={timeout}"]
            if prover == "e" else ["--proof", "tptp", "--mode", "casc", "-t", str(timeout)])


def replay_case(directory: Path, run: CaseOutcome, case: InferenceCase,
                timeout: int) -> str:
    expected_path = f"captures/{run.prover}/{case.id}/capture.json"
    if (run.id != case.id or run.group != case.group or run.kind != case.kind
            or run.expected != case.expected or run.capture != expected_path):
        raise InferenceError("Case identity, polarity or capture path differs from the study")
    path = checked_source_path(directory / run.capture)
    if sha256(read_regular(path)).hexdigest() != run.capture_sha256:
        raise InferenceError("Capture digest differs from the report")
    capture = load_capture(path, run.invocation_id)
    raw = case.problem.encode()
    if (capture.prover != run.prover or capture.includes
            or capture.command[1:-1] != command_flags(run.prover, timeout)
            or capture.source_problem != capture.command[-1]
            or capture.provenance != {"prover_sha256": run.prover_sha256}
            or sha256(raw).hexdigest() != run.problem_sha256
            or verified_bytes(capture.problem, path.parent) != raw
            or read_regular(checked_source_path(directory / "problems" / f"{case.id}.p")) != raw):
        raise InferenceError("Captured invocation differs from the regenerated problem or resource policy")
    expanded_problem(capture, path.parent)
    stdout = verified_bytes(capture.stdout, path.parent).decode("utf-8")
    verified_bytes(capture.stderr, path.parent)
    statuses = set(SZS_STATUS.findall(stdout))
    if len(statuses) > 1 or (not capture.timed_out and len(statuses) != 1):
        raise InferenceError("Captured output has missing or conflicting SZS statuses")
    observed = "Timeout" if capture.timed_out else statuses.pop()
    allowed_exits = {0, 1} if observed in {"Satisfiable", "CounterSatisfiable"} else {0}
    if observed in {"Theorem", "Unsatisfiable", "ContradictoryAxioms",
                    "Satisfiable", "CounterSatisfiable"} and capture.returncode not in allowed_exits:
        raise InferenceError("Captured SZS status disagrees with the process exit")
    if run.observed != observed:
        raise InferenceError("Reported outcome differs from the captured status")
    return observed


def summary(outcomes: list[CaseOutcome], scenario_count: int) -> InferenceSummary:
    matched = sum(run.matched for run in outcomes)
    resolved = {"Theorem", "CounterSatisfiable", "Satisfiable", "Unsatisfiable",
                "ContradictoryAxioms"}
    unresolved = sum(run.observed not in resolved for run in outcomes)
    return InferenceSummary(scenarios=scenario_count, total=len(outcomes), matched=matched,
                            mismatched=len(outcomes) - matched - unresolved,
                            unresolved=unresolved, passed=matched == len(outcomes) and bool(outcomes))


def validate_inference_report(path: Path, *, trusted_report_sha256: str) -> InferenceReport:
    """Replay only with a separately trusted outer digest; integrity is not process authentication."""
    path = checked_source_path(path)
    raw = read_regular(path)
    if len(trusted_report_sha256) != 64 or sha256(raw).hexdigest() != trusted_report_sha256:
        raise InferenceError("Trusted report SHA-256 mismatch")
    report = InferenceReport.model_validate_json(raw)
    directory = path.parent
    study = load_study(checked_source_path(directory / "study.json"))
    claims = derive_source_claims(study, read_regular(checked_source_path(directory / "source/Merge.kif")))
    if (report.study_id != study.study_id or report.study_sha256 != study_sha256(study)
            or report.source_claims != claims or report.replay_boundary != BOUNDARY):
        raise InferenceError("Source claims, study or replay boundary do not rederive")
    implementation = implementation_bindings()
    retained = {name: sha256(read_regular(checked_source_path(
        directory / "implementation" / name))).hexdigest() for name in IMPLEMENTATION}
    if report.implementation != implementation or retained != implementation:
        raise InferenceError("Retained or current implementation differs from the campaign binding")
    if report.provers not in (["e"], ["v"], ["e", "v"]):
        raise InferenceError("Unexpected or duplicate prover families")
    binaries = {family: sha256(read_regular(checked_source_path(
        directory / "binaries" / f"{family}.bin"))).hexdigest() for family in report.provers}
    if report.binary_sha256 != binaries:
        raise InferenceError("Retained binary bytes differ from the campaign binding")
    lock = read_regular(checked_source_path(directory / "sumo.lock.json"))
    if sha256(lock).hexdigest() != report.lock_sha256 or report.lock_sha256 != study.lock_sha256:
        raise InferenceError("Retained source lock differs from the campaign binding")
    generated = cases(study, claims)
    by_id = {case.id: case for case in generated}
    identities = [(family, case.id) for family in report.provers for case in generated]
    if [(run.prover, run.id) for run in report.cases] != identities:
        raise InferenceError("Missing, reordered, duplicate or unexpected cases")
    backgrounds: dict[tuple[str, str], str] = {}
    for run, (_, case_id) in zip(report.cases, identities, strict=True):
        case = by_id[case_id]
        observed = replay_case(directory, run, case, report.timeout_seconds)
        if run.prover_sha256 != binaries[run.prover]:
            raise InferenceError("Case binary binding differs from retained bytes")
        if run.kind == "background":
            backgrounds[(run.prover, run.group)] = observed
        matched = observed == case.expected and backgrounds.get((run.prover, run.group)) == "Satisfiable"
        if run.matched != matched or not matched:
            raise InferenceError("Expected polarity or paired background satisfiability failed")
    if report.summary != summary(report.cases, len(study.scenarios)):
        raise InferenceError("Summary does not rederive from captured cases")
    return report

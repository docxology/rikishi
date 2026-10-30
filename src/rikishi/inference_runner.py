from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Literal

from rikishi.inference_models import CaseOutcome, InferenceError, InferenceReport
from rikishi.inference_replay import (
    BOUNDARY,
    IMPLEMENTATION,
    implementation_bindings,
    replay_case,
    summary,
    validate_inference_report,
)
from rikishi.inference_study import cases, catalog, derive_source_claims, study_sha256
from rikishi.runtime import prove, prover_executable
from rikishi.runtime_artifacts import ProverKind, checked_source_path, load_capture, read_regular
from rikishi.runtime_results import ExpectedATPInvocation, verify_invocation


def run_inference(root: Path, output: Path, *,
                  prover: Literal["both", "e", "v"] = "both", timeout: int = 5) -> InferenceReport:
    """Create fresh retained native evidence; a failed campaign remains on disk and raises."""
    root = checked_source_path(root)
    if (prover not in {"both", "e", "v"} or not isinstance(timeout, int)
            or isinstance(timeout, bool) or not 1 <= timeout <= 300):
        raise InferenceError("Use prover both/e/v and an integer timeout between 1 and 300")
    output = output if output.is_absolute() else root / output
    if not output.absolute().is_relative_to(root) or not output.resolve().is_relative_to(root):
        raise InferenceError("Campaign output must be inside the repository")
    checked_source_path(output.parent)
    study = catalog()
    source = read_regular(checked_source_path(root / study.source_path))
    claims = derive_source_claims(study, source)
    generated = cases(study, claims)
    lock = read_regular(checked_source_path(root / "config/sumo.lock.json"))
    if sha256(lock).hexdigest() != study.lock_sha256:
        raise InferenceError("Source lock differs from the supported pinned study")
    families: list[ProverKind] = ["e", "v"] if prover == "both" else [prover]
    binary_paths = {family: checked_source_path(prover_executable(root, family)) for family in families}
    binary_bytes = {family: read_regular(path) for family, path in binary_paths.items()}
    binary_hashes = {family: sha256(data).hexdigest() for family, data in binary_bytes.items()}
    implementation = implementation_bindings()
    output.mkdir(exist_ok=False)
    for name in ("source", "implementation", "binaries", "problems", "captures"):
        (output / name).mkdir()
    (output / "study.json").write_text(study.model_dump_json(indent=2) + "\n")
    (output / "source/Merge.kif").write_bytes(source)
    (output / "sumo.lock.json").write_bytes(lock)
    for name in IMPLEMENTATION:
        (output / "implementation" / name).write_bytes(read_regular(root / "src/rikishi" / name))
    for family, data in binary_bytes.items():
        (output / "binaries" / f"{family}.bin").write_bytes(data)
        (output / "captures" / family).mkdir()
    for case in generated:
        (output / "problems" / f"{case.id}.p").write_text(case.problem)
    outcomes: list[CaseOutcome] = []
    for family in families:
        backgrounds: dict[str, str] = {}
        for case in generated:
            problem = output / "problems" / f"{case.id}.p"
            capture_path = output / "captures" / family / case.id / "capture.json"
            try:
                result = prove(problem, root, timeout=timeout, prover=family,
                               output=capture_path.parent)
                observed = str(result["status"])
                if Path(str(result["capture"])) != capture_path:
                    raise InferenceError("Runtime returned an unexpected capture path")
            except TimeoutError:
                observed = "Timeout"
            capture = load_capture(capture_path)
            verify_invocation(capture, ExpectedATPInvocation(
                invocation_id=capture.invocation_id, executable=binary_paths[family],
                provenance={"prover_sha256": binary_hashes[family]},
                problem_sha256=sha256(case.problem.encode()).hexdigest(), prover=family))
            if case.kind == "background":
                backgrounds[case.group] = observed
            matched = observed == case.expected and backgrounds.get(case.group) == "Satisfiable"
            run = CaseOutcome(
                id=case.id, group=case.group, kind=case.kind, prover=family, expected=case.expected,
                observed=observed, matched=matched,
                capture=capture_path.relative_to(output).as_posix(),
                capture_sha256=sha256(read_regular(capture_path)).hexdigest(),
                problem_sha256=sha256(case.problem.encode()).hexdigest(),
                invocation_id=capture.invocation_id, prover_sha256=binary_hashes[family])
            replay_case(output, run, case, timeout)
            outcomes.append(run)
    if (implementation_bindings() != implementation
            or any(sha256(read_regular(path)).hexdigest() != binary_hashes[family]
                   for family, path in binary_paths.items())
            or read_regular(root / study.source_path) != source
            or read_regular(root / "config/sumo.lock.json") != lock):
        raise InferenceError("Campaign inputs changed during execution; evidence remains incomplete")
    report = InferenceReport(
        study_id=study.study_id, study_sha256=study_sha256(study), source_claims=claims,
        implementation=implementation, binary_sha256=binary_hashes, lock_sha256=study.lock_sha256,
        provers=families, timeout_seconds=timeout, cases=outcomes,
        summary=summary(outcomes, len(study.scenarios)), replay_boundary=BOUNDARY)
    report_path = output / "inference-report.json"
    report_path.write_text(report.model_dump_json(indent=2) + "\n")
    return validate_inference_report(report_path, trusted_report_sha256=sha256(read_regular(report_path)).hexdigest())

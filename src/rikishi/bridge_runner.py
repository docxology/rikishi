"""Fresh native evidence producer for shared finite FEP–SUMO witnesses."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Literal, assert_never

from rikishi.bridge_compiler import compile_witnesses
from rikishi.bridge_models import BridgeError, BridgeReport
from rikishi.bridge_replay import (
    BOUNDARY,
    IMPLEMENTATION,
    implementation_bindings,
    summary,
    validate_bridge_report,
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
from rikishi.inference_replay import replay_case
from rikishi.runtime import prove, prover_executable
from rikishi.runtime_artifacts import ProverKind, checked_source_path, load_capture, read_regular
from rikishi.runtime_results import ExpectedATPInvocation, verify_invocation


def run_bridge(root: Path, output: Path, *,
               prover: Literal["both", "e", "v"] = "both", timeout: int = 10) -> BridgeReport:
    """Retain a new bounded campaign; failed obligations leave their evidence on disk."""
    root = checked_source_path(root)
    if (prover not in {"both", "e", "v"} or type(timeout) is not int or not 1 <= timeout <= 300):
        raise BridgeError("Use prover both/e/v and an integer timeout between 1 and 300")
    output = output if output.is_absolute() else root / output
    if not output.absolute().is_relative_to(root) or not output.resolve().is_relative_to(root):
        raise BridgeError("Bridge output must be inside the repository")
    checked_source_path(output.parent)
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    if Path(__file__).resolve().parent != root / "src/rikishi":
        raise BridgeError("Native bridge production requires this canonical package checkout")
    study = catalog()
    source = read_regular(checked_source_path(root / study.source_path))
    claims = derive_source_claims(study, source)
    generated = cases(study, claims)
    source_lock = read_regular(checked_source_path(root / "config/sumo.lock.json"))
    dependency_lock = read_regular(checked_source_path(root / "uv.lock"))
    if sha256(source_lock).hexdigest() != study.lock_sha256:
        raise BridgeError("SUMO lock differs from the bridge authority")
    if sha256(dependency_lock).hexdigest() != study.dependency_lock_sha256:
        raise BridgeError("Dependency lock differs from the bridge authority")
    families: tuple[ProverKind, ...]
    match prover:
        case "both":
            families = ("e", "v")
        case "e" | "v":
            families = (prover,)
        case unreachable:
            assert_never(unreachable)
    paths = {family: checked_source_path(prover_executable(root, family)) for family in families}
    binaries = {family: read_regular(path) for family, path in paths.items()}
    binary_hashes = {family: sha256(data).hexdigest() for family, data in binaries.items()}
    implementation = implementation_bindings()
    numbers = numerical(study)
    if not all(row.passed for row in numbers):
        raise BridgeError("Numerical witnesses failed their independent reference checks")
    local = extension(study).encode()
    output.mkdir(exist_ok=False)
    for name in ("source", "implementation", "binaries", "problems", "captures"):
        (output / name).mkdir()
    (output / "study.json").write_text(study.model_dump_json(indent=2) + "\n")
    (output / "source/Merge.kif").write_bytes(source)
    (output / "sumo.lock.json").write_bytes(source_lock)
    (output / "uv.lock").write_bytes(dependency_lock)
    (output / "extension.kif").write_bytes(local)
    (output / "numerical.json").write_bytes(NUMERICAL.dump_json(numbers, indent=2) + b"\n")
    for name in IMPLEMENTATION:
        (output / "implementation" / name).write_bytes(read_regular(root / "src/rikishi" / name))
    for family, data in binaries.items():
        (output / "binaries" / f"{family}.bin").write_bytes(data)
        (output / "captures" / family).mkdir()
    for case in generated:
        (output / "problems" / f"{case.id}.p").write_text(case.problem)
    lean = compile_witnesses(root, output, study)
    outcomes: list[CaseOutcome] = []
    for family in families:
        backgrounds: dict[str, str] = {}
        for case in generated:
            capture_path = output / "captures" / family / case.id / "capture.json"
            try:
                result = prove(output / "problems" / f"{case.id}.p", root,
                               timeout=timeout, prover=family, output=capture_path.parent)
                observed = str(result["status"])
                if Path(str(result["capture"])) != capture_path:
                    raise BridgeError("Runtime returned an unexpected bridge capture path")
            except TimeoutError:
                observed = "Timeout"
            capture = load_capture(capture_path)
            verify_invocation(capture, ExpectedATPInvocation(
                invocation_id=capture.invocation_id, executable=paths[family],
                provenance={"prover_sha256": binary_hashes[family]},
                problem_sha256=sha256(case.problem.encode()).hexdigest(), prover=family))
            if case.kind == "background":
                backgrounds[case.group] = observed
            outcome = CaseOutcome(
                id=case.id, group=case.group, kind=case.kind, prover=family, expected=case.expected,
                observed=observed,
                matched=observed == case.expected and backgrounds.get(case.group) == "Satisfiable",
                capture=capture_path.relative_to(output).as_posix(),
                capture_sha256=sha256(read_regular(capture_path)).hexdigest(),
                problem_sha256=sha256(case.problem.encode()).hexdigest(),
                invocation_id=capture.invocation_id, prover_sha256=binary_hashes[family])
            replay_case(output, outcome, case, timeout)
            outcomes.append(outcome)
    if (implementation_bindings() != implementation
            or read_regular(root / study.source_path) != source
            or read_regular(root / "config/sumo.lock.json") != source_lock
            or read_regular(root / "uv.lock") != dependency_lock
            or any(sha256(read_regular(path)).hexdigest() != binary_hashes[family]
                   for family, path in paths.items())):
        raise BridgeError("Bridge inputs changed during execution; retained campaign is incomplete")
    runs = tuple(outcomes)
    report = BridgeReport(
        study_id=study.study_id, study_sha256=study_sha256(study), witnesses=study.witnesses,
        scenarios=study.scenarios, source_claims=claims, extension_sha256=sha256(local).hexdigest(),
        numerical=numbers, lean=lean, implementation=implementation, binary_sha256=binary_hashes,
        lock_sha256=study.lock_sha256, dependency_lock_sha256=sha256(dependency_lock).hexdigest(),
        provers=families, timeout_seconds=timeout, cases=runs,
        summary=summary(study, runs, numbers, lean), replay_boundary=BOUNDARY)
    path = output / "bridge-report.json"
    path.write_text(report.model_dump_json(indent=2) + "\n")
    return validate_bridge_report(path, trusted_report_sha256=sha256(read_regular(path)).hexdigest())

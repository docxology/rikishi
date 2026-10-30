"""Native observations and rehashed adversarial copies of an authentic packet."""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from shutil import copytree
from typing import Literal, Protocol, assert_never

import pytest

from rikishi.bridge_models import BridgeError, BridgeReport
from rikishi.bridge_replay import validate_bridge_report
from rikishi.bridge_study import NUMERICAL
from rikishi.inference_models import InferenceError
from rikishi.runtime_artifacts import Capture, read_regular

pytestmark = pytest.mark.integration


class Packet(Protocol):
    @property
    def path(self) -> Path: ...

    @property
    def sha256(self) -> str: ...

    @property
    def report(self) -> BridgeReport: ...


@dataclass(frozen=True, slots=True)
class Copy:
    path: Path
    report: BridgeReport


@pytest.fixture
def copied_bridge(bridge_packet: Packet, tmp_path: Path) -> Copy:
    directory = tmp_path / "packet"
    copytree(bridge_packet.path.parent, directory)
    return Copy(directory / "bridge-report.json", bridge_packet.report)


def reject_rehashed(packet: Copy, report: BridgeReport) -> None:
    """The test supplies a new outer digest, so an inner semantic check must reject."""
    packet.path.write_text(report.model_dump_json(indent=2) + "\n")
    digest = sha256(packet.path.read_bytes()).hexdigest()
    with pytest.raises((BridgeError, InferenceError)):
        validate_bridge_report(packet.path, trusted_report_sha256=digest)


def test_fresh_campaign_observes_each_control_in_each_family(bridge_packet: Packet) -> None:
    report = validate_bridge_report(bridge_packet.path, trusted_report_sha256=bridge_packet.sha256)
    assert report.provers == ("e", "v")
    for scenario in report.scenarios:
        for family in report.provers:
            observed = {run.kind: run.observed for run in report.cases
                        if run.group == scenario.id and run.prover == family}
            assert observed == {"background": "Satisfiable", "positive": "Theorem",
                                "negative": "CounterSatisfiable",
                                "removed-premise": "CounterSatisfiable", "refutation": "Unsatisfiable"}
    assert report.summary.total == len(report.cases)
    assert report.summary.matched == len(report.cases)
    assert report.summary.passed and not report.semantic_validation


def test_explicit_outer_custody_binding_is_required(bridge_packet: Packet) -> None:
    with pytest.raises(BridgeError, match="Trusted bridge"):
        validate_bridge_report(bridge_packet.path, trusted_report_sha256="0" * 64)


def test_rehash_cannot_change_numerical_manifest(copied_bridge: Copy) -> None:
    report = copied_bridge.report
    row = report.numerical[0]
    false = row.model_copy(update={"result": row.result.model_copy(
        update={"free_energy": row.result.free_energy + 0.5})})
    rows = (false, *report.numerical[1:])
    (copied_bridge.path.parent / "numerical.json").write_bytes(NUMERICAL.dump_json(rows, indent=2))
    reject_rehashed(copied_bridge, report.model_copy(update={"numerical": rows}))


def test_rehash_cannot_change_generated_lean_proof(copied_bridge: Copy) -> None:
    report = copied_bridge.report
    path = copied_bridge.path.parent / report.lean.source
    path.write_text(path.read_text() + "\ntheorem forged : False := by sorry\n")
    digest = sha256(path.read_bytes()).hexdigest()
    lean = report.lean.model_copy(update={"source_sha256": digest,
        "artifacts": {**report.lean.artifacts, report.lean.source: digest}})
    reject_rehashed(copied_bridge, report.model_copy(update={"lean": lean}))


def test_rehash_cannot_change_captured_status(copied_bridge: Copy) -> None:
    report = copied_bridge.report
    runs = tuple(run.model_copy(update={"observed": "CounterSatisfiable"})
                 if run.kind == "positive" else run for run in report.cases)
    reject_rehashed(copied_bridge, report.model_copy(update={"cases": runs}))


def test_rehash_cannot_change_expected_polarity(copied_bridge: Copy) -> None:
    report = copied_bridge.report
    first = report.cases[0].model_copy(update={"expected": "Unsatisfiable"})
    reject_rehashed(copied_bridge, report.model_copy(update={"cases": (first, *report.cases[1:])}))


def test_synthetic_rehashed_inconsistent_background_is_not_credited(copied_bridge: Copy) -> None:
    """This edited capture is a replay negative control, never a native observation."""
    report = copied_bridge.report
    run = report.cases[0]
    assert run.kind == "background" and run.observed == "Satisfiable"
    path = copied_bridge.path.parent / run.capture
    capture = Capture.model_validate_json(path.read_bytes())
    stdout = path.parent / capture.stdout.path
    raw = read_regular(stdout)
    changed = raw.replace(b"SZS status Satisfiable", b"SZS status Unsatisfiable")
    assert changed != raw
    stdout.write_bytes(changed)
    capture = capture.model_copy(update={"returncode": 0, "stdout": capture.stdout.model_copy(
        update={"sha256": sha256(changed).hexdigest(), "size": len(changed)})})
    path.write_text(capture.model_dump_json(indent=2) + "\n")
    altered = run.model_copy(update={"observed": "Unsatisfiable", "capture_sha256": sha256(path.read_bytes()).hexdigest()})
    reject_rehashed(copied_bridge, report.model_copy(update={"cases": (altered, *report.cases[1:])}))


def test_rehash_cannot_omit_control(copied_bridge: Copy) -> None:
    report = copied_bridge.report
    reject_rehashed(copied_bridge, report.model_copy(update={"cases": report.cases[:-1]}))


def test_rehash_cannot_change_source_claim(copied_bridge: Copy) -> None:
    report = copied_bridge.report
    false = report.source_claims[0].model_copy(update={"end_line": 999999})
    reject_rehashed(copied_bridge, report.model_copy(update={"source_claims": (false, *report.source_claims[1:])}))


def test_rehash_cannot_change_dependency_lock(copied_bridge: Copy) -> None:
    report = copied_bridge.report
    path = copied_bridge.path.parent / "uv.lock"
    path.write_bytes(path.read_bytes() + b"\n# forged binding\n")
    reject_rehashed(copied_bridge, report.model_copy(
        update={"dependency_lock_sha256": sha256(path.read_bytes()).hexdigest()}))


@pytest.mark.parametrize("mutation", ["problem", "implementation", "binary", "extension", "study"])
def test_retained_input_corruption_is_rejected(copied_bridge: Copy, mutation: str) -> None:
    report = copied_bridge.report
    directory = copied_bridge.path.parent
    selected = {
        "problem": directory / "problems" / f"{report.cases[0].id}.p",
        "implementation": directory / "implementation/bridge_study.py",
        "binary": directory / "binaries/e.bin",
        "extension": directory / "extension.kif",
        "study": directory / "study.json",
    }[mutation]
    if mutation == "study":
        from rikishi.bridge_study import catalog

        changed = catalog().model_copy(update={"tolerance": 1e-13})
        selected.write_text(changed.model_dump_json())
    else:
        selected.write_bytes(selected.read_bytes() + b"\n% deliberate corruption\n")
    reject_rehashed(copied_bridge, report)


@pytest.mark.parametrize("mutation", ["resource", "exit", "provenance", "timed-out", "stdout"])
def test_rehashed_capture_policy_cannot_be_relaxed(
    copied_bridge: Copy, mutation: Literal["resource", "exit", "provenance", "timed-out", "stdout"],
) -> None:
    report = copied_bridge.report
    index = next(i for i, run in enumerate(report.cases) if run.kind == "positive")
    run = report.cases[index]
    path = copied_bridge.path.parent / run.capture
    capture = Capture.model_validate_json(path.read_bytes())
    match mutation:
        case "resource":
            command = [arg.replace("--cpu-limit=10", "--cpu-limit=11") for arg in capture.command]
            assert command != capture.command
            capture = capture.model_copy(update={"command": command})
        case "exit":
            capture = capture.model_copy(update={"returncode": 4})
        case "provenance":
            capture = capture.model_copy(update={"provenance": {"prover_sha256": "0" * 64}})
        case "timed-out":
            capture = capture.model_copy(update={"timed_out": True})
        case "stdout":
            stdout = path.parent / capture.stdout.path
            changed = stdout.read_bytes() + b"\n% SZS status Satisfiable\n"
            stdout.write_bytes(changed)
            capture = capture.model_copy(update={"stdout": capture.stdout.model_copy(
                update={"sha256": sha256(changed).hexdigest(), "size": len(changed)})})
        case unreachable:
            assert_never(unreachable)
    path.write_text(capture.model_dump_json(indent=2) + "\n")
    altered = run.model_copy(update={"capture_sha256": sha256(path.read_bytes()).hexdigest()})
    runs = (*report.cases[:index], altered, *report.cases[index + 1:])
    reject_rehashed(copied_bridge, report.model_copy(update={"cases": runs}))


def test_rehashed_summary_cannot_invent_completion(copied_bridge: Copy) -> None:
    report = copied_bridge.report
    false = report.summary.model_copy(update={"matched": report.summary.matched + 1})
    reject_rehashed(copied_bridge, report.model_copy(update={"summary": false}))


def test_rehashed_missing_import_error_is_not_a_proof_rejection(copied_bridge: Copy) -> None:
    report = copied_bridge.report
    control = report.lean.controls[0]
    relative = control.command.log
    path = copied_bridge.path.parent / relative
    path.write_text("control.lean:1:0: error: unknown module prefix 'MissingDependency'\n")
    digest = sha256(path.read_bytes()).hexdigest()
    changed = control.model_copy(update={"command": control.command.model_copy(
        update={"log_sha256": digest})})
    lean = report.lean.model_copy(update={
        "controls": (changed, *report.lean.controls[1:]),
        "artifacts": {**report.lean.artifacts, relative: digest},
    })
    reject_rehashed(copied_bridge, report.model_copy(update={"lean": lean}))


def test_rehashed_failed_positive_environment_is_not_credited(copied_bridge: Copy) -> None:
    report = copied_bridge.report
    positive = report.lean.environments[0]
    changed = positive.model_copy(update={"command": positive.command.model_copy(
        update={"returncode": 1})})
    lean = report.lean.model_copy(update={"environments": (changed, *report.lean.environments[1:])})
    reject_rehashed(copied_bridge, report.model_copy(update={"lean": lean}))


def test_rehashed_positive_environment_source_does_not_bypass_reconstruction(copied_bridge: Copy) -> None:
    report = copied_bridge.report
    positive = report.lean.environments[0]
    path = copied_bridge.path.parent / positive.source
    path.write_text(path.read_text() + "\ntheorem forgedEnvironment : False := by sorry\n")
    digest = sha256(path.read_bytes()).hexdigest()
    changed = positive.model_copy(update={"source_sha256": digest})
    lean = report.lean.model_copy(update={
        "environments": (changed, *report.lean.environments[1:]),
        "artifacts": {**report.lean.artifacts, positive.source: digest},
    })
    reject_rehashed(copied_bridge, report.model_copy(update={"lean": lean}))


def test_rehashed_lean_budget_cannot_be_confused_with_prover_timeout(copied_bridge: Copy) -> None:
    report = copied_bridge.report
    changed = report.lean.commands[0].model_copy(update={"timeout_seconds": 1})
    lean = report.lean.model_copy(update={"commands": (changed, *report.lean.commands[1:])})
    reject_rehashed(copied_bridge, report.model_copy(update={"lean": lean}))

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import pytest
from pydantic import ValidationError

from rikishi.runtime_artifacts import (
    COMMAND_POLICY,
    PATH_POLICY,
    SZS_STATUS,
    ArtifactError,
    load_capture,
    read_regular,
    receipt,
)
from rikishi.runtime_capture import capture_prover
from rikishi.runtime_process import run_bounded
from rikishi.runtime_results import ExpectedATPInvocation, interpret_sigma_result

pytestmark = pytest.mark.integration

UNSUPPORTED_E_ARGUMENTS: Final = [
    pytest.param(("--cpu-limit=5", "{extra}", "{root}"), id="extra-positional-file"),
    pytest.param(("--cpu-limit=5", "-", "{root}"), id="stdin-before-final-file"),
    pytest.param(("--cpu-limit=5", "--watchlist={extra}", "{root}"), id="file-valued-option"),
    pytest.param(("--cpu-limit=5", "--watchlist=-", "{root}"), id="stdin-option-value"),
    pytest.param(("--cpu-limit=5", "--definitional-cnf=24", "{root}"), id="unsupported-transform"),
    pytest.param(("--cpu-limit", "5", "{root}"), id="split-cpu-value-is-an-input"),
    pytest.param(("--cpu-limit=5", "--answers", "1", "{root}"), id="split-answer-value"),
    pytest.param(("--cpu-limit=5", "-"), id="final-stdin"),
    pytest.param(("--cpu-limit=5", "root.p"), id="relative-final-input"),
    pytest.param(("--auto", "{root}"), id="missing-cpu-limit"),
    pytest.param(("--cpu-limit=5", "--cpu-limit=6", "{root}"), id="duplicate-cpu-limit"),
    pytest.param(("--cpu-limit=0", "{root}"), id="zero-cpu-limit"),
    pytest.param(("--cpu-limit=-1", "{root}"), id="negative-cpu-limit"),
    pytest.param(("--cpu-limit=1.5", "{root}"), id="fractional-cpu-limit"),
    pytest.param(("--cpu-limit=5", "--answers=0", "{root}"), id="zero-answer-limit"),
]


@dataclass(frozen=True, slots=True)
class LegacyCapture:
    path: Path
    sidecar: Path
    expected: ExpectedATPInvocation


@pytest.fixture(scope="module")
def native_e(project_root: Path) -> Path:
    binary = project_root / ".rikishi/upstream/eprover/PROVER/eprover"
    assert binary.is_file(), "R3 command regressions require the installed real E prover"
    return binary


@pytest.fixture
def problem_files(tmp_path: Path) -> tuple[Path, Path]:
    root, extra = tmp_path / "root.p", tmp_path / "extra.p"
    root.write_text("fof(root_fact,axiom,q).\nfof(goal,conjecture,p).\n")
    extra.write_text("fof(extra_fact,axiom,p).\n")
    return root, extra


def _command(binary: Path, problem: Path) -> list[str]:
    return [str(binary), "--auto", "--tstp-format", "--proof-object", "--cpu-limit=5",
            str(problem)]


def _provenance(binary: Path) -> dict[str, str]:
    return {"prover_sha256": hashlib.sha256(read_regular(binary)).hexdigest()}


def _arguments(arguments: tuple[str, ...], binary: Path,
               problems: tuple[Path, Path]) -> list[str]:
    root, extra = problems
    return [str(binary), *(item.format(root=root, extra=extra) for item in arguments)]


@pytest.fixture
def legacy_multi_input(tmp_path: Path, native_e: Path,
                       problem_files: tuple[Path, Path]) -> LegacyCapture:
    root, extra = problem_files
    directory = tmp_path / "legacy.artifacts"
    directory.mkdir()
    frozen = directory / "problem.p"
    frozen.write_bytes(root.read_bytes())
    direct = _command(native_e, root)
    command = [*direct[:-1], str(extra), direct[-1]]
    stdout, stderr = directory / "stdout.txt", directory / "stderr.txt"
    process = run_bounded(command, cwd=tmp_path, stdout=stdout, stderr=stderr, timeout=10)
    assert not process.timed_out
    assert process.returncode == 0
    assert set(SZS_STATUS.findall(stdout.read_text())) == {"Theorem"}
    provenance = _provenance(native_e)
    # Do not use capture_prover or Capture to manufacture historical evidence:
    # their current guards must not prevent exercising the saved-result reader.
    payload = {
        "path_policy": PATH_POLICY, "prover": "e", "invocation_id": "r3-multi-input",
        "command": command, "source_problem": str(root),
        "problem": receipt(frozen, directory).model_dump(), "includes": [],
        "stdout": receipt(stdout, directory).model_dump(),
        "stderr": receipt(stderr, directory).model_dump(),
        "returncode": process.returncode, "timed_out": process.timed_out,
        "provenance": provenance,
    }
    capture_path = directory / "capture.json"
    capture_path.write_text(json.dumps(payload))
    sidecar = tmp_path / "legacy.json"
    sidecar.write_text(json.dumps({
        "status": "Theorem", "atp_returncode": process.returncode,
        "stdout_lines": len(stdout.read_bytes().splitlines()),
        "invocation_id": "r3-multi-input", "capture": directory.name + "/capture.json",
    }))
    expected = ExpectedATPInvocation("r3-multi-input", native_e, provenance,
                                     hashlib.sha256(root.read_bytes()).hexdigest(), prover="e")
    return LegacyCapture(capture_path, sidecar, expected)


def test_native_multiple_inputs_prove_more_than_frozen_final_file(
    legacy_multi_input: LegacyCapture, native_e: Path, tmp_path: Path,
) -> None:
    # Given: real E proved the two-input invocation; only root's bytes were frozen.
    frozen = legacy_multi_input.path.parent / "problem.p"
    # When: the same E options run against those frozen bytes alone.
    stdout, stderr = tmp_path / "replay.stdout.txt", tmp_path / "replay.stderr.txt"
    replay = run_bounded(_command(native_e, frozen), cwd=tmp_path,
                         stdout=stdout, stderr=stderr, timeout=10)
    # Then: the frozen problem has a countermodel, so that original proof is unsafe.
    assert not replay.timed_out
    assert replay.returncode in {0, 1}
    assert set(SZS_STATUS.findall(stdout.read_text())) == {"CounterSatisfiable"}


def test_legacy_multi_input_capture_without_command_policy_is_rejected(
    legacy_multi_input: LegacyCapture,
) -> None:
    # Given: all real process receipts and trusted invocation bindings agree.
    # When: the reader encounters the independently built pre-policy capture.
    with pytest.raises(ValidationError, match="command_policy"):
        load_capture(legacy_multi_input.path)
    result = interpret_sigma_result(legacy_multi_input.sidecar, 0,
                                    expected=legacy_multi_input.expected)
    # Then: historical output cannot certify a current proof.
    assert result["status"] == "InvalidATPResult"
    assert result["outcome"] == "error"
    assert result["evidence"] == "not_verified"
    assert not result["proved"]


@pytest.mark.parametrize("arguments", UNSUPPORTED_E_ARGUMENTS)
def test_current_policy_cannot_authorize_unsafe_saved_e_command(
    legacy_multi_input: LegacyCapture, native_e: Path,
    problem_files: tuple[Path, Path], arguments: tuple[str, ...],
) -> None:
    # Given: even an adversarial capture carries both current policy labels.
    payload = json.loads(legacy_multi_input.path.read_text())
    payload["command_policy"] = COMMAND_POLICY
    payload["command"] = _arguments(arguments, native_e, problem_files)
    legacy_multi_input.path.write_text(json.dumps(payload))
    # When: semantic command checks run on the saved record and bound result.
    with pytest.raises(ArtifactError, match="command|argument"):
        load_capture(legacy_multi_input.path)
    result = interpret_sigma_result(legacy_multi_input.sidecar, 0,
                                    expected=legacy_multi_input.expected)
    # Then: policy labels never rehabilitate an unsupported command.
    assert result["status"] == "InvalidATPResult"
    assert result["outcome"] == "error"
    assert result["evidence"] == "not_verified"
    assert not result["proved"]


@pytest.mark.parametrize("arguments", UNSUPPORTED_E_ARGUMENTS)
def test_capture_rejects_unsafe_e_command_before_writing(
    native_e: Path, problem_files: tuple[Path, Path], tmp_path: Path,
    arguments: tuple[str, ...],
) -> None:
    # Given: existing real input files and the trusted native executable hash.
    directory = tmp_path / "rejected"
    directory.mkdir()
    command = _arguments(arguments, native_e, problem_files)
    # When: capture is asked to execute an unsupported command.
    with pytest.raises(ArtifactError, match="command|argument"):
        capture_prover(command, directory, invocation_id="r3-rejected",
                       provenance=_provenance(native_e), timeout=10)
    # Then: rejection precedes even the problem snapshot and process-output files.
    assert list(directory.iterdir()) == []


@pytest.mark.parametrize("sigma", [False, True], ids=["direct-e", "sigma-e"])
@pytest.mark.parametrize("axiom,status", [("p", "Theorem"), ("q", "CounterSatisfiable")])
def test_supported_single_input_e_commands_retain_real_outcomes(
    native_e: Path, tmp_path: Path, sigma: bool, axiom: str, status: str,
) -> None:
    # Given: independent theorem and countermodel problems under both known grammars.
    problem = tmp_path / "accepted.p"
    problem.write_text(f"fof(fact,axiom,{axiom}).\nfof(goal,conjecture,p).\n")
    command = ([str(native_e), "--cpu-limit=5", "--conjectures-are-questions", "--answers=1",
                str(problem)] if sigma else _command(native_e, problem))
    directory = tmp_path / "accepted.artifacts"
    directory.mkdir()
    # When: the real invocation is captured and inspected with complete bindings.
    capture = capture_prover(command, directory, invocation_id="r3-accepted",
                             provenance=_provenance(native_e), timeout=10, prover="e")
    stdout = read_regular(directory / capture.stdout.path)
    sidecar = tmp_path / "accepted.json"
    sidecar.write_text(json.dumps({
        "status": status, "atp_returncode": capture.returncode,
        "stdout_lines": len(stdout.splitlines()), "invocation_id": capture.invocation_id,
        "capture": directory.name + "/capture.json",
    }))
    expected = ExpectedATPInvocation(capture.invocation_id, native_e, capture.provenance,
                                     hashlib.sha256(problem.read_bytes()).hexdigest(), prover="e")
    result = interpret_sigma_result(sidecar, 0, expected=expected)
    # Then: valid commands preserve the native result and current proof boundary.
    assert not capture.timed_out
    assert set(SZS_STATUS.findall(stdout.decode())) == {status}
    assert load_capture(directory / "capture.json") == capture
    assert result["status"] == status
    assert result["outcome"] == ("entailed" if axiom == "p" else "not_entailed")
    assert result["proved"] == (axiom == "p")
    assert result["evidence"] == "sha256_verified"

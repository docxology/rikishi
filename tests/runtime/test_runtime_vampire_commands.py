import hashlib
import json
from pathlib import Path

import pytest

from rikishi.runtime_artifacts import (
    SZS_STATUS,
    ArtifactError,
    expanded_problem,
    load_capture,
    read_regular,
)
from rikishi.runtime_capture import capture_prover
from rikishi.runtime_process import run_bounded
from rikishi.runtime_results import ExpectedATPInvocation, interpret_sigma_result


@pytest.mark.integration
@pytest.mark.parametrize("answers", [False, True])
@pytest.mark.parametrize("goal,status", [("p", "Theorem"), ("q", "CounterSatisfiable")])
def test_real_vampire_sigma_command_is_single_frozen_problem(
    project_root: Path, tmp_path: Path, answers: bool, goal: str, status: str,
) -> None:
    binary = project_root / ".rikishi/runtime/vampire"
    inputs = tmp_path / "inputs"
    nested = inputs / "nested"
    nested.mkdir(parents=True)
    (inputs / "leaf.p").write_text("fof(root_fact,axiom,q).\n")
    (nested / "leaf.p").write_text("fof(nested_fact,axiom,p).\n")
    (nested / "outer.p").write_text("include('leaf.p').\n")
    problem = inputs / "problem.p"
    problem.write_text(f"include('nested/outer.p'). fof(goal,conjecture,{goal}).\n")
    problem_digest = hashlib.sha256(problem.read_bytes()).hexdigest()
    directory = tmp_path / "artifacts"
    directory.mkdir()
    flags = ["--proof", "tptp", "--mode", "casc"]
    if answers:
        flags.extend(["-qa", "plain"])
    provenance = {"prover_sha256": hashlib.sha256(read_regular(binary)).hexdigest()}
    capture = capture_prover(
        [str(binary), *flags, "-t", "5", str(problem)], directory,
        invocation_id="vampire-single-input", provenance=provenance, timeout=10, prover="v",
    )
    stdout = read_regular(directory / capture.stdout.path).decode()
    assert not capture.timed_out
    assert set(SZS_STATUS.findall(stdout)) == {status}
    frozen_text = expanded_problem(capture, directory)
    assert frozen_text.split() == ["fof(nested_fact,axiom,p).", f"fof(goal,conjecture,{goal})."]
    assert {item.source for item in capture.includes} == {str(nested / "outer.p"), str(nested / "leaf.p")}
    inputs.rename(tmp_path / "moved-inputs")
    assert not problem.exists()
    assert load_capture(directory / "capture.json") == capture
    assert expanded_problem(capture, directory) == frozen_text
    replay = tmp_path / "frozen.p"
    replay.write_text(frozen_text)
    replay_directory = tmp_path / "replay"
    replay_directory.mkdir()
    replay_capture = capture_prover(
        [str(binary), *flags, "-t", "5", str(replay)], replay_directory,
        invocation_id="vampire-frozen-replay", provenance=provenance, timeout=10, prover="v",
    )
    assert not replay_capture.timed_out
    assert set(SZS_STATUS.findall((replay_directory / "stdout.txt").read_text())) == {status}
    sidecar = tmp_path / "result.json"
    sidecar.write_text(json.dumps({
        "status": status, "atp_returncode": capture.returncode,
        "stdout_lines": len(stdout.splitlines()), "invocation_id": capture.invocation_id,
        "capture": "artifacts/capture.json",
    }))
    expected = ExpectedATPInvocation(capture.invocation_id, binary, provenance,
                                     problem_digest, prover="v")
    result = interpret_sigma_result(sidecar, 0, expected=expected)
    assert result["proved"] == (status == "Theorem")
    assert result["outcome"] == ("entailed" if status == "Theorem" else "not_entailed")
    wrong_family = ExpectedATPInvocation(capture.invocation_id, binary, provenance,
                                         expected.problem_sha256, prover="e")
    assert interpret_sigma_result(sidecar, 0, expected=wrong_family)["outcome"] == "error"


@pytest.mark.integration
def test_pinned_vampire_rejects_sigma_legacy_option_before_input(
    project_root: Path, tmp_path: Path,
) -> None:
    binary = project_root / ".rikishi/runtime/vampire"
    problem = tmp_path / "problem.p"
    problem.write_text("fof(fact,axiom,p). fof(goal,conjecture,p).\n")
    command = [str(binary), "--output_axiom_names", "on", "--proof", "tptp", "--mode", "casc",
               "-t", "5", str(problem)]
    native = run_bounded(command, cwd=tmp_path, stdout=tmp_path / "native.stdout",
                         stderr=tmp_path / "native.stderr", timeout=10)
    assert not native.timed_out
    assert native.returncode == 4
    assert "output_axiom_names is not a valid option" in (tmp_path / "native.stdout").read_text()
    assert not SZS_STATUS.findall((tmp_path / "native.stdout").read_text())
    rejected = tmp_path / "rejected"
    rejected.mkdir()
    with pytest.raises(ArtifactError, match="unsupported Vampire prover argument"):
        capture_prover(command, rejected, invocation_id="vampire-unsupported-sigma",
                       provenance={"prover_sha256": hashlib.sha256(read_regular(binary)).hexdigest()},
                       timeout=10, prover="v")
    assert list(rejected.iterdir()) == []

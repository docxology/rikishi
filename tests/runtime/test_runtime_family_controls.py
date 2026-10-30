from __future__ import annotations

import hashlib
import json
import shutil
import signal
from pathlib import Path
from uuid import uuid4

import pytest
from native_timeout_control import capture_native_control

from rikishi.runtime import prove, prover_executable
from rikishi.runtime_artifacts import ArtifactError, load_capture, read_regular, receipt
from rikishi.runtime_capture import capture_prover
from rikishi.runtime_diagnostics import diagnose, proof_premises
from rikishi.runtime_results import ExpectedATPInvocation, verify_invocation
from rikishi.runtime_tptp import TPTPError


@pytest.fixture
def controls_output(native_workspace: Path) -> Path:
    directory = (native_workspace
                 / ("runtime-implementation-controls-" + uuid4().hex))
    directory.mkdir()
    return directory


@pytest.mark.integration
@pytest.mark.parametrize("prover", ["e", "v"])
def test_bound_capture_rejects_wrong_family_unbound_stale_and_wrong_input(
    project_root: Path, tmp_path: Path, controls_output: Path, prover: str,
) -> None:
    problem = tmp_path / "problem.p"
    problem.write_text("fof(fact,axiom,p). fof(goal,conjecture,p).\n")
    result = prove(problem, project_root, 2, prover=prover, output=controls_output / "direct")
    path = Path(str(result["capture"]))
    capture = load_capture(path)
    binary = prover_executable(project_root, prover)
    expected = ExpectedATPInvocation(capture.invocation_id, binary, capture.provenance,
                                     capture.problem.sha256, prover=prover)
    verify_invocation(capture, expected)
    invalid = [
        ExpectedATPInvocation("stale", binary, capture.provenance, capture.problem.sha256, prover=prover),
        ExpectedATPInvocation(capture.invocation_id, binary, capture.provenance, None, prover=prover),
        ExpectedATPInvocation(capture.invocation_id, binary, capture.provenance, "0" * 64, prover=prover),
        ExpectedATPInvocation(capture.invocation_id, binary, capture.provenance,
                              capture.problem.sha256, prover="v" if prover == "e" else "e"),
    ]
    for binding in invalid:
        with pytest.raises(ArtifactError, match="trusted executable, input, or source bindings"):
            verify_invocation(capture, binding)
    for mutation in ("command_executable", "command_input", "provenance", "saved_input", "stdout"):
        copied = controls_output / mutation
        shutil.copytree(path.parent, copied)
        payload = json.loads((copied / "capture.json").read_text())
        if mutation == "command_executable":
            payload["command"][0] = str(tmp_path / "other-executable")
        elif mutation == "command_input":
            payload["command"][-1] = str(tmp_path / "other-input.p")
        elif mutation == "provenance":
            payload["provenance"]["prover_sha256"] = "0" * 64
        else:
            (copied / ("problem.p" if mutation == "saved_input" else "stdout.txt")).write_text("tampered")
        (copied / "capture.json").write_text(json.dumps(payload))
        output = controls_output / (mutation + "-diagnostic")
        with pytest.raises(ArtifactError):
            diagnose(copied / "capture.json", project_root, timeout=2, output=output)
        assert not output.exists()


@pytest.mark.integration
@pytest.mark.parametrize("prover", ["e", "v"])
def test_forged_saved_theorem_output_cannot_replace_real_countermodel_replay(
    project_root: Path, tmp_path: Path, controls_output: Path, prover: str,
) -> None:
    problem = tmp_path / "countermodel.p"
    problem.write_text("fof(fact,axiom,p). fof(goal,conjecture,q).\n")
    result = prove(problem, project_root, 2, prover=prover, output=controls_output / "direct")
    directory = Path(str(result["capture"])).parent
    payload = json.loads((directory / "capture.json").read_text())
    delimiter = "CNFRefutation" if prover == "e" else "Proof for forged"
    (directory / "stdout.txt").write_text(
        f"% SZS status Theorem\n% SZS output start {delimiter}\n"
        "fof(fact,axiom,p,file('/untrusted/problem.p',fact)).\n"
        f"% SZS output end {delimiter}\n")
    payload["stdout"] = receipt(directory / "stdout.txt", directory).model_dump()
    payload["returncode"] = 0
    (directory / "capture.json").write_text(json.dumps(payload))
    report = diagnose(directory / "capture.json", project_root, timeout=2,
                      output=controls_output / "diagnostic")
    assert report["status"] == "CounterSatisfiable"
    assert report["premise_count"] == 0
    assert report["subset_status"] == "not_run"


@pytest.mark.integration
@pytest.mark.parametrize("prover", ["e", "v"])
def test_real_family_capture_outer_timeout_is_retained(
    project_root: Path, tmp_path: Path, controls_output: Path, prover: str,
) -> None:
    binary = prover_executable(project_root, prover)
    problem = tmp_path / "problem.p"
    problem.write_text("fof(fact,axiom,p). fof(goal,conjecture,p).\n")
    flags = (["--auto", "--cpu-limit=2"] if prover == "e"
             else ["--proof", "tptp", "--mode", "casc", "-t", "2"])
    directory = controls_output / "timeout"
    command = [str(binary), *flags, str(problem)]
    capture = capture_native_control(command, directory, prover=prover, stopped=True)
    assert capture.timed_out is True
    assert capture.returncode == -signal.SIGKILL
    assert capture.command == command and capture.prover == prover
    assert capture.provenance["prover_sha256"] == hashlib.sha256(read_regular(binary)).hexdigest()
    assert load_capture(directory / "capture.json") == capture


@pytest.mark.integration
@pytest.mark.parametrize("prover", ["e", "v"])
def test_real_family_completion_before_wait_is_not_an_outer_timeout(
    project_root: Path, tmp_path: Path, controls_output: Path, prover: str,
) -> None:
    binary = prover_executable(project_root, prover)
    problem = tmp_path / "problem.p"
    problem.write_text("fof(fact,axiom,p). fof(goal,conjecture,p).\n")
    flags = (["--auto", "--cpu-limit=2"] if prover == "e"
             else ["--proof", "tptp", "--mode", "casc", "-t", "2"])
    directory = controls_output / "completed-before-wait"
    command = [str(binary), *flags, str(problem)]
    capture = capture_native_control(command, directory, prover=prover, stopped=False)
    assert capture.timed_out is False
    assert capture.returncode == 0
    assert capture.command == command and capture.prover == prover
    assert capture.provenance["prover_sha256"] == hashlib.sha256(read_regular(binary)).hexdigest()
    assert "SZS status Theorem" in (directory / "stdout.txt").read_text()
    assert load_capture(directory / "capture.json") == capture


@pytest.mark.integration
def test_vampire_diagnostic_retains_question_answering_option(
    project_root: Path, tmp_path: Path, controls_output: Path,
) -> None:
    binary = prover_executable(project_root, "v")
    problem = tmp_path / "problem.p"
    problem.write_text("fof(fact,axiom,p). fof(goal,conjecture,p).\n")
    directory = controls_output / "original"
    directory.mkdir()
    capture_prover(
        [str(binary), "--proof", "tptp", "--mode", "casc", "-qa", "plain", "-t", "5", str(problem)],
        directory, invocation_id="v-qa", timeout=10, prover="v",
        provenance={"prover_sha256": hashlib.sha256(read_regular(binary)).hexdigest()},
    )
    report = diagnose(directory / "capture.json", project_root, timeout=2,
                      output=controls_output / "diagnostic")
    assert report["subset_status"] == "Theorem"
    for subdirectory in ("proof", "subset-check"):
        capture = load_capture(controls_output / "diagnostic" / subdirectory / "capture.json")
        assert capture.prover == "v"
        assert capture.command[1:-1] == ["--proof", "tptp", "--mode", "casc", "-qa", "plain", "-t", "2"]


@pytest.mark.parametrize("statement", [
    "fof(a,axiom,p,file('/saved/problem.p',a)). broken",
    "fof(a,axiom,p,file('/saved/problem.p','bad\\q')).",
    "fof(a,axiom,p,file('/saved/problem.p','bad\\\'name')).",
    "fof(a,axiom,p,file('/saved/problem.p',)).",
    "fof(a,axiom,p,file('/saved/problem.p',a))",
])
def test_vampire_malformed_complete_block_names_fail_closed(statement: str) -> None:
    stdout = f"% SZS output start Proof for problem\n{statement}\n% SZS output end Proof for problem\n"
    with pytest.raises(TPTPError):
        proof_premises(stdout, prover="v")


@pytest.mark.integration
@pytest.mark.parametrize("names", [("'fact name'", "'goal name'"), ("123", "456"),
                                    (r"'fact\\name'", r"'goal\\name'")])
def test_vampire_named_premises_preserve_complete_statements(
    project_root: Path, tmp_path: Path, controls_output: Path, names: tuple[str, str],
) -> None:
    fact, goal = names
    problem = tmp_path / "names.p"
    problem.write_text(f"fof({fact},axiom,\n p). fof({goal},conjecture,\n p).\n")
    result = prove(problem, project_root, 2, prover="v", output=controls_output / "direct")
    report = diagnose(Path(str(result["capture"])), project_root, timeout=2,
                      output=controls_output / "diagnostic")
    assert report["premise_count"] == 2
    assert report["subset_status"] == "Theorem"
    assert (controls_output / "diagnostic/proof-premises.p").read_text() == (
        f"fof({fact},axiom,\n p).\nfof({goal},conjecture,\n p).\n")


@pytest.mark.integration
def test_ambiguous_saved_names_cannot_export_a_premise_set(
    project_root: Path, tmp_path: Path, controls_output: Path,
) -> None:
    problem = tmp_path / "ambiguous.p"
    problem.write_text("fof(fact,axiom,p). fof(fact,axiom,q). fof(goal,conjecture,p).\n")
    result = prove(problem, project_root, 2, output=controls_output / "direct")
    with pytest.raises(ArtifactError, match="map uniquely"):
        diagnose(Path(str(result["capture"])), project_root, timeout=2,
                 output=controls_output / "diagnostic")
    assert not (controls_output / "diagnostic/diagnostic.json").exists()

import hashlib
import json
import os
import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from rikishi.runtime import prove
from rikishi.runtime_artifacts import (
    COMMAND_POLICY,
    PATH_POLICY,
    SZS_STATUS,
    ArtifactError,
    expanded_problem,
    load_capture,
    read_regular,
    receipt,
)
from rikishi.runtime_capture import capture_prover
from rikishi.runtime_process import run_bounded
from rikishi.runtime_results import ExpectedATPInvocation, interpret_sigma_result

pytestmark = pytest.mark.integration


@pytest.fixture
def native_e(project_root):
    binary = project_root / ".rikishi/upstream/eprover/PROVER/eprover"
    assert binary.is_file(), "R3 regressions require the installed real E prover"
    return binary


@pytest.fixture
def isolated_runtime(tmp_path, native_e):
    root = tmp_path / "runtime"
    binary = root / ".rikishi/upstream/eprover/PROVER/eprover"
    binary.parent.mkdir(parents=True)
    shutil.copy2(native_e, binary)
    return root


def _command(binary: Path, problem: Path) -> list[str]:
    return [str(binary), "--auto", "--tstp-format", "--proof-object", "--cpu-limit=5",
            str(problem)]


def _provenance(binary: Path) -> dict[str, str]:
    return {"prover_sha256": hashlib.sha256(read_regular(binary)).hexdigest()}


def _native(command: list[str], directory: Path, status: str) -> None:
    directory.mkdir()
    process = run_bounded(command, cwd=Path(command[-1]).parent,
                          stdout=directory / "stdout.txt", stderr=directory / "stderr.txt",
                          timeout=10)
    assert not process.timed_out
    assert process.returncode in ({0} if status == "Theorem" else {0, 1})
    assert set(SZS_STATUS.findall((directory / "stdout.txt").read_text())) == {status}


def _sidecar(capture_path: Path, status: str = "Theorem") -> Path:
    payload = json.loads(capture_path.read_text())
    path = capture_path.parent.parent / (capture_path.parent.name + ".result.json")
    path.write_text(json.dumps({
        "status": status, "atp_returncode": payload["returncode"],
        "stdout_lines": len((capture_path.parent / payload["stdout"]["path"]).read_bytes().splitlines()),
        "invocation_id": payload["invocation_id"],
        "capture": capture_path.parent.name + "/capture.json",
    }))
    return path


def _invalid_bound(capture_path: Path, expected: ExpectedATPInvocation) -> None:
    result = interpret_sigma_result(_sidecar(capture_path), 0, expected=expected)
    assert result["status"] == "InvalidATPResult"
    assert result["outcome"] == "error"
    assert result["evidence"] == "not_verified"
    assert not result["proved"]


@pytest.fixture
def legacy_symlink_capture(tmp_path, native_e):
    inputs = tmp_path / "inputs"
    lexical, target = inputs / "lexical", inputs / "target"
    lexical.mkdir(parents=True)
    target.mkdir()
    (lexical / "background.p").write_text("fof(lexical_fact,axiom,p).\n")
    (target / "background.p").write_text("fof(target_fact,axiom,q).\n")
    outer = target / "outer.p"
    outer.write_text("include('background.p').\n")
    (lexical / "linked.p").symlink_to(outer)
    problem = lexical / "query.p"
    problem.write_text("include('linked.p').\nfof(goal,conjecture,p).\n")
    command = _command(native_e, problem)
    original = tmp_path / "native-original"
    _native(command, original, "Theorem")

    directory = tmp_path / "legacy.artifacts"
    directory.mkdir()
    for source, saved in [(problem, "problem.p"), (outer, "include-0.p"),
                           (target / "background.p", "include-1.p"),
                           (original / "stdout.txt", "stdout.txt"),
                           (original / "stderr.txt", "stderr.txt")]:
        (directory / saved).write_bytes(source.read_bytes())
    frozen = tmp_path / "old-frozen.p"
    frozen.write_text((directory / "include-1.p").read_text() + "fof(goal,conjecture,p).\n")
    _native(_command(native_e, frozen), tmp_path / "native-frozen", "CounterSatisfiable")

    provenance = _provenance(native_e)
    payload = {
        "command_policy": COMMAND_POLICY, "prover": "e",
        "invocation_id": "r3-legacy", "command": command, "source_problem": str(problem),
        "problem": receipt(directory / "problem.p", directory).model_dump(),
        "includes": [
            {**receipt(directory / "include-0.p", directory).model_dump(), "source": str(outer)},
            {**receipt(directory / "include-1.p", directory).model_dump(),
             "source": str(target / "background.p")},
        ],
        "stdout": receipt(directory / "stdout.txt", directory).model_dump(),
        "stderr": receipt(directory / "stderr.txt", directory).model_dump(),
        "returncode": 0, "timed_out": False, "provenance": provenance,
    }
    capture_path = directory / "capture.json"
    capture_path.write_text(json.dumps(payload))
    expected = ExpectedATPInvocation("r3-legacy", native_e, provenance,
                                     hashlib.sha256(problem.read_bytes()).hexdigest())
    return capture_path, expected, inputs


def test_native_file_symlink_nested_include_rejected_before_execution(legacy_symlink_capture,
                                                                     tmp_path):
    capture_path, expected, _ = legacy_symlink_capture
    command = json.loads(capture_path.read_text())["command"]
    rejected = tmp_path / "rejected"
    rejected.mkdir()
    with pytest.raises(ArtifactError, match="[Ss]ymlink"):
        capture_prover(command, rejected, invocation_id="r3-rejected",
                       provenance=dict(expected.provenance), timeout=10)
    assert not (rejected / "stdout.txt").exists()
    assert not (rejected / "capture.json").exists()


@pytest.mark.parametrize("policy", [None, "resolved-v0"])
def test_legacy_symlink_capture_requires_exact_policy(legacy_symlink_capture, policy):
    capture_path, expected, _ = legacy_symlink_capture
    if policy is not None:
        payload = json.loads(capture_path.read_text())
        payload["path_policy"] = policy
        capture_path.write_text(json.dumps(payload))
    with pytest.raises(ValidationError, match="path_policy"):
        load_capture(capture_path)
    _invalid_bound(capture_path, expected)


def test_adding_policy_cannot_rehabilitate_resolved_metadata_after_inputs_move(
    legacy_symlink_capture, tmp_path,
):
    capture_path, expected, inputs = legacy_symlink_capture
    payload = json.loads(capture_path.read_text())
    payload["path_policy"] = "lexical-absolute-no-symlinks-v1"
    capture_path.write_text(json.dumps(payload))
    inputs.rename(tmp_path / "moved-inputs")
    # A dangling replacement alias would make live .resolve() accept the old metadata.
    lexical = inputs / "lexical"
    lexical.mkdir(parents=True)
    (lexical / "linked.p").symlink_to(inputs / "target/outer.p")
    assert not Path(payload["source_problem"]).exists()
    assert all(not Path(item["source"]).exists() for item in payload["includes"])
    capture = load_capture(capture_path)
    with pytest.raises(ArtifactError, match="unrecorded.*lexical/linked\\.p"):
        expanded_problem(capture, capture_path.parent)
    _invalid_bound(capture_path, expected)


@pytest.mark.parametrize("location", ["include_directory", "source_file", "source_directory"])
def test_symlink_inputs_rejected_by_capture_and_runtime(tmp_path, native_e, isolated_runtime,
                                                       location):
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    target = inputs / "target"
    target.mkdir()
    (target / "background.p").write_text("fof(fact,axiom,p).\n")
    real_problem = target / "query.p"
    real_problem.write_text("include('background.p').\nfof(goal,conjecture,p).\n")
    if location == "include_directory":
        (inputs / "alias").symlink_to(target, target_is_directory=True)
        problem = inputs / "query.p"
        problem.write_text("include('alias/background.p').\nfof(goal,conjecture,p).\n")
    elif location == "source_file":
        problem = target / "linked-query.p"
        problem.symlink_to(real_problem)
    else:
        (inputs / "alias").symlink_to(target, target_is_directory=True)
        problem = inputs / "alias/query.p"
    command = _command(native_e, problem)
    _native(command, tmp_path / "native-accepted", "Theorem")
    rejected = tmp_path / "rejected"
    rejected.mkdir()
    with pytest.raises(ArtifactError, match="[Ss]ymlink"):
        capture_prover(command, rejected, invocation_id="r3-links",
                       provenance=_provenance(native_e), timeout=10)
    assert not (rejected / "stdout.txt").exists()
    assert not (rejected / "capture.json").exists()
    with pytest.raises(ArtifactError, match="[Ss]ymlink"):
        prove(problem, isolated_runtime, timeout=5)
    assert not list((isolated_runtime / ".rikishi/results").rglob("stdout.txt"))
    assert not list((isolated_runtime / ".rikishi/results").rglob("capture.json"))


@pytest.mark.parametrize("location", ["source", "include"])
def test_symlink_component_before_parent_rejected_before_normalization(
    tmp_path, native_e, isolated_runtime, location,
):
    lexical, target = tmp_path / "lexical", tmp_path / "target"
    lexical.mkdir()
    (target / "child").mkdir(parents=True)
    (lexical / "alias").symlink_to(target / "child", target_is_directory=True)
    (lexical / "background.p").write_text("fof(lexical_fact,axiom,q).\n")
    (target / "background.p").write_text("fof(target_fact,axiom,p).\n")
    if location == "source":
        text = "include('background.p').\nfof(goal,conjecture,p).\n"
        (lexical / "query.p").write_text(text)
        (target / "query.p").write_text(text)
        problem = lexical / "alias/../query.p"
        checked_path = problem
    else:
        problem = lexical / "query.p"
        problem.write_text("include('alias/../background.p').\nfof(goal,conjecture,p).\n")
        checked_path = lexical / "alias/../background.p"
    assert "alias" in checked_path.parts
    assert "alias" not in Path(os.path.normpath(checked_path)).parts
    command = _command(native_e, problem)
    _native(command, tmp_path / "native-accepted", "Theorem")
    rejected = tmp_path / "rejected"
    rejected.mkdir()
    with pytest.raises(ArtifactError, match="[Ss]ymlink"):
        capture_prover(command, rejected, invocation_id="r3-parent",
                       provenance=_provenance(native_e), timeout=10)
    assert not (rejected / "stdout.txt").exists()
    assert not (rejected / "capture.json").exists()
    with pytest.raises(ArtifactError, match="[Ss]ymlink"):
        prove(problem, isolated_runtime, timeout=5)
    assert not list((isolated_runtime / ".rikishi/results").rglob("stdout.txt"))


@pytest.mark.parametrize("mutation", ["changed_files", "moved_directory_with_replacement_symlink"])
def test_nested_capture_replay_and_bound_reader_ignore_mutable_original_paths(
    tmp_path, native_e, isolated_runtime, mutation,
):
    inputs = tmp_path / "inputs"
    (inputs / "nested").mkdir(parents=True)
    (inputs / "axioms").mkdir()
    problem = inputs / "query.p"
    outer, background = inputs / "nested/outer.p", inputs / "axioms/background.p"
    problem.write_text("include('nested/outer.p').\nfof(goal,conjecture,p).\n")
    outer.write_text("include('../axioms/background.p').\n")
    background.write_text("fof(fact,axiom,p).\n")
    directory = tmp_path / "nested.artifacts"
    directory.mkdir()
    capture = capture_prover(_command(native_e, problem), directory, invocation_id="r3-nested",
                             provenance=_provenance(native_e), timeout=10)
    assert PATH_POLICY == capture.path_policy == "lexical-absolute-no-symlinks-v1"
    assert set(SZS_STATUS.findall(read_regular(directory / capture.stdout.path).decode())) == {"Theorem"}
    expected = ExpectedATPInvocation(capture.invocation_id, native_e, capture.provenance,
                                     capture.problem.sha256)
    capture_path = directory / "capture.json"
    sidecar = _sidecar(capture_path)
    before = interpret_sigma_result(sidecar, 0, expected=expected)
    assert before["proved"] and before["evidence"] == "sha256_verified"
    frozen = expanded_problem(capture, directory)
    if mutation == "changed_files":
        problem.write_text("original problem replaced with non-TPTP text")
        outer.write_text("include('missing.p').\n")
        background.write_text("fof(changed,axiom,q).\n")
    else:
        inputs.rename(tmp_path / "moved-inputs")
        replacement = tmp_path / "replacement"
        replacement.mkdir()
        inputs.symlink_to(replacement, target_is_directory=True)
        assert inputs.is_symlink()
        assert not problem.exists() and not outer.exists() and not background.exists()
    saved = load_capture(capture_path)
    assert saved == capture
    assert expanded_problem(saved, directory) == frozen
    accepted = interpret_sigma_result(sidecar, 0, expected=expected)
    assert accepted["status"] == "Theorem"
    assert accepted["outcome"] == "entailed"
    assert accepted["proved"] and accepted["evidence"] == "sha256_verified"
    replay = tmp_path / "replay.p"
    replay.write_text(frozen)
    assert prove(replay, isolated_runtime, timeout=5)["status"] == "Theorem"

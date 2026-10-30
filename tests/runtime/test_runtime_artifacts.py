import hashlib
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from rikishi.runtime_artifacts import (
    Artifact,
    ArtifactError,
    ProverKind,
    checked_source_path,
    expanded_problem,
    jar_classes_sha256,
    load_capture,
    normalized_source_identity,
    read_regular,
    validate_prover_command,
    verified_bytes,
)
from rikishi.runtime_capture import capture_prover, main
from rikishi.runtime_process import run_bounded
from rikishi.runtime_results import interpret_sigma_result


def _python_provenance(executable: Path) -> dict[str, str]:
    return {"prover_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
            "fixture": "real-process"}


def _process_driver(tmp_path: Path, body: str) -> Path:
    driver = tmp_path / "driver"
    driver.write_text(f"#!{sys.executable}\n{body}\n")
    driver.chmod(0o700)
    return driver


@pytest.mark.parametrize("prover,options", [
    ("e", ["--cpu-limit=5", "--conjectures-are-questions", "--answers=1"]),
    ("e", ["--auto", "--tstp-format", "--proof-object", "--cpu-limit=5"]),
    ("v", ["--proof", "tptp", "--mode", "casc", "-t", "5"]),
    ("v", ["--proof", "tptp", "--mode", "casc", "-qa", "plain", "-t", "5"]),
])
def test_supported_native_command_grammar(tmp_path: Path, prover: ProverKind, options: list[str]) -> None:
    problem = tmp_path / "problem.p"
    problem.write_text("fof(fact,axiom,p).")
    validate_prover_command([str(tmp_path / "native-prover"), *options, str(problem)], prover)


@pytest.mark.parametrize("prover,arguments", [
    ("e", []),
    ("e", ["--auto"]),
    ("e", ["--cpu-limit", "5"]),
    ("e", ["--cpu-limit=0"]),
    ("e", ["--cpu-limit=5", "--cpu-limit=6"]),
    ("e", ["--cpu-limit=5", "--answers=0"]),
    ("e", ["--cpu-limit=5", "--include=extra.p"]),
    ("e", ["--cpu-limit=5", "extra.p"]),
    ("e", ["--cpu-limit=5", "-"]),
    ("v", ["--mode", "casc", "-t"]),
    ("v", ["--mode", "casc", "-t", "5"]),
    ("v", ["--proof", "tptp", "--mode", "casc", "-t", "0"]),
    ("v", ["--proof", "file", "--mode", "casc", "-t", "5"]),
    ("v", ["--proof", "tptp", "--mode", "casc", "-t", "5", "-t", "6"]),
    ("v", ["--proof", "tptp", "--mode", "casc", "--include", "extra.p"]),
    ("v", ["--output_axiom_names", "on", "--proof", "tptp", "--mode", "casc", "-t", "5"]),
])
def test_unsupported_native_command_grammar(tmp_path: Path, prover: ProverKind, arguments: list[str]) -> None:
    problem = tmp_path / "problem.p"
    problem.write_text("fof(fact,axiom,p).")
    with pytest.raises(ArtifactError):
        validate_prover_command([str(tmp_path / "native-prover"), *arguments, str(problem)], prover)


@pytest.mark.parametrize("command", [[], ["/prover"], ["relative", "--cpu-limit=5", "/problem"],
                                     ["/prover", "--cpu-limit=5", "-"],
                                     ["/prover", "--cpu-limit=5", "/problem\0bad"]])
def test_prover_command_requires_exact_file_shape(command: list[str]) -> None:
    with pytest.raises(ArtifactError, match="one final absolute problem"):
        validate_prover_command(command, "e")


@pytest.mark.parametrize("artifact", ["problem.p", "stdout.txt", "stderr.txt"])
def test_tampered_saved_evidence_cannot_certify_proof(atp_sidecar, artifact):
    sidecar = atp_sidecar()
    directory = sidecar.parent / "atp.artifacts"
    assert interpret_sigma_result(sidecar, 0)["outcome"] == "unverified"
    (directory / artifact).write_bytes(b"changed")
    result = interpret_sigma_result(sidecar, 0)
    assert result["status"] == "InvalidATPResult"
    assert not result["proved"]


def test_status_only_sidecar_is_rejected(tmp_path):
    sidecar = tmp_path / "unbound.json"
    sidecar.write_text(json.dumps({"status": "Theorem", "atp_returncode": 0,
                                  "stdout_lines": 1, "invocation_id": "fresh"}))
    assert interpret_sigma_result(sidecar, 0, invocation_id="fresh")["outcome"] == "error"


@pytest.mark.parametrize("mutation", ["status", "count", "exit", "capture_id", "timeout", "extra"])
def test_receipt_disagreement_is_an_error(atp_sidecar, mutation):
    sidecar = atp_sidecar()
    payload = json.loads(sidecar.read_text())
    capture_path = sidecar.parent / payload["capture"]
    capture = json.loads(capture_path.read_text())
    if mutation == "status":
        payload["status"] = "CounterSatisfiable"
    elif mutation == "count":
        payload["stdout_lines"] = 100
    elif mutation == "exit":
        capture["returncode"] = 4
    elif mutation == "capture_id":
        capture["invocation_id"] = "stale"
    elif mutation == "timeout":
        capture["timed_out"] = True
    else:
        capture["unexpected"] = True
    capture_path.write_text(json.dumps(capture))
    sidecar.write_text(json.dumps(payload))
    assert interpret_sigma_result(sidecar, 0)["outcome"] == "error"


@pytest.mark.parametrize("kind", ["symlink", "fifo", "directory", "oversized", "missing"])
def test_unsafe_evidence_is_rejected_without_blocking(tmp_path, kind):
    path = tmp_path / "unsafe"
    if kind == "symlink":
        target = tmp_path / "target"
        target.write_text("safe")
        path.symlink_to(target)
    elif kind == "fifo":
        os.mkfifo(path)
    elif kind == "directory":
        path.mkdir()
    elif kind == "oversized":
        path.write_text("four")
    with pytest.raises(ArtifactError):
        read_regular(path, limit=3)


@pytest.mark.parametrize("relative", ["../outside", "/outside", "nested/file"])
def test_artifact_paths_cannot_escape_directory(tmp_path, relative):
    artifact = Artifact(path=relative, size=0, sha256=hashlib.sha256(b"").hexdigest())
    with pytest.raises(ArtifactError):
        verified_bytes(artifact, tmp_path)


def test_capture_replays_frozen_transitive_include_bytes(tmp_path):
    leaf = tmp_path / "leaf.p"
    leaf.write_text("fof(fact,axiom,p).\n")
    background = tmp_path / "background.p"
    background.write_text("include('leaf.p').\n")
    problem = tmp_path / "query.p"
    problem.write_text("include('background.p').\nfof(goal,conjecture,p).\n")
    directory = tmp_path / "capture"
    directory.mkdir()
    driver = _process_driver(tmp_path, "import sys\nprint('# SZS status Theorem')\nprint('retained stderr',file=sys.stderr)")
    capture = capture_prover([str(driver), "--cpu-limit=5", str(problem)], directory,
                             invocation_id="real-process", provenance=_python_provenance(driver), timeout=5)
    leaf.write_text("fof(changed,axiom,q).\n")
    background.write_text("changed")
    saved = load_capture(directory / "capture.json", "real-process")
    assert saved == capture
    assert expanded_problem(saved, directory).split() == ["fof(fact,axiom,p).", "fof(goal,conjecture,p)."]
    assert read_regular(directory / "stdout.txt") == b"# SZS status Theorem\n"
    assert read_regular(directory / "stderr.txt") == b"retained stderr\n"
    with pytest.raises(ArtifactError, match="another invocation"):
        load_capture(directory / "capture.json", "stale")


@pytest.mark.parametrize("directive", ["include('missing').", "include('x', [a])."])
def test_unrecorded_include_cannot_replay(atp_sidecar, directive):
    sidecar = atp_sidecar()
    capture_path = sidecar.parent / "atp.artifacts/capture.json"
    data = json.loads(capture_path.read_text())
    problem = capture_path.parent / "problem.p"
    problem.write_text(directive)
    data["problem"].update(size=len(problem.read_bytes()), sha256=hashlib.sha256(problem.read_bytes()).hexdigest())
    capture_path.write_text(json.dumps(data))
    with pytest.raises(ArtifactError, match="include"):
        expanded_problem(load_capture(capture_path), capture_path.parent)


def test_process_failure_preserves_stdout_stderr_and_exit(tmp_path):
    result = run_bounded([sys.executable, "-c",
                          "import sys; print('out'); print('err',file=sys.stderr); sys.exit(17)"],
                         cwd=tmp_path, stdout=tmp_path / "out", stderr=tmp_path / "err", timeout=5)
    assert result.returncode == 17
    assert not result.timed_out
    assert (tmp_path / "out").read_text() == "out\n"
    assert (tmp_path / "err").read_text() == "err\n"


def test_process_wall_bound_kills_descendants(tmp_path):
    code = ("import subprocess,sys,time; child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); "
            "print(child.pid,flush=True); time.sleep(60)")
    result = run_bounded([sys.executable, "-c", code], cwd=tmp_path,
                         stdout=tmp_path / "out", stderr=tmp_path / "err", timeout=1)
    assert result.timed_out
    assert result.returncode < 0
    pid = (tmp_path / "out").read_text().strip()
    process = subprocess.run(["ps", "-o", "stat=", "-p", pid],
                             capture_output=True, text=True, timeout=5, check=False)
    assert not process.stdout.strip() or process.stdout.strip().startswith("Z")


def test_process_invalid_bound_and_missing_executable(tmp_path):
    with pytest.raises(ValueError):
        run_bounded(["absent"], cwd=tmp_path, stdout=tmp_path / "out", stderr=tmp_path / "err", timeout=0)
    with pytest.raises(FileNotFoundError):
        run_bounded([str(tmp_path / "absent")], cwd=tmp_path,
                    stdout=tmp_path / "out", stderr=tmp_path / "err", timeout=5)


def test_process_interrupt_cleans_up_before_reraising(tmp_path):
    code = "import os,signal,time; os.kill(os.getppid(),signal.SIGINT); time.sleep(60)"
    with pytest.raises(KeyboardInterrupt):
        run_bounded([sys.executable, "-c", code], cwd=tmp_path,
                    stdout=tmp_path / "out", stderr=tmp_path / "err", timeout=5)


@pytest.mark.parametrize("timeout", [False, True])
def test_executable_adapter_returns_real_exit_and_output(tmp_path, capfd, timeout):
    problem = tmp_path / "problem.p"
    problem.write_text("fof(p,axiom,p).\n")
    directory = tmp_path / "capture"
    directory.mkdir()
    code = "import time; time.sleep(60)" if timeout else "import sys; print('output'); print('error',file=sys.stderr); sys.exit(17)"
    driver = _process_driver(tmp_path, code)
    environment = {"RIKISHI_ATP_CAPTURE": str(directory), "RIKISHI_REAL_PROVER": str(driver),
                   "RIKISHI_INVOCATION_ID": "adapter", "RIKISHI_PROVENANCE": json.dumps(_python_provenance(driver)),
                   "RIKISHI_PROVER_WALL_TIMEOUT": "0.2" if timeout else "5"}
    assert main(environment, ["--cpu-limit=5", str(problem)]) == (137 if timeout else 17)
    captured = capfd.readouterr()
    assert captured.out == ("" if timeout else "output\n")
    assert captured.err == ("" if timeout else "error\n")


def test_capture_detects_input_change_during_real_process(tmp_path):
    problem = tmp_path / "input.p"
    problem.write_text("fof(original,axiom,p).")
    directory = tmp_path / "capture"
    directory.mkdir()
    driver = _process_driver(tmp_path, "import pathlib,sys; pathlib.Path(sys.argv[-1]).write_text('changed')")
    with pytest.raises(ArtifactError, match="changed during execution"):
        capture_prover([str(driver), "--cpu-limit=5", str(problem)], directory,
                       invocation_id="changed", provenance=_python_provenance(driver), timeout=5)
    assert not (directory / "capture.json").exists()
    assert (directory / "problem.p").read_text() == "fof(original,axiom,p)."


def test_recursive_include_capture_cannot_certify_replay(tmp_path):
    problem = tmp_path / "self.p"
    problem.write_text("include('self.p').\n")
    directory = tmp_path / "capture"
    directory.mkdir()
    driver = _process_driver(tmp_path, "print('output')")
    with pytest.raises(ArtifactError, match="recursive"):
        capture_prover([str(driver), "--cpu-limit=5", str(problem)], directory,
                       invocation_id="recursive", provenance=_python_provenance(driver), timeout=5)


@pytest.mark.parametrize("capture", ["../escape/capture.json", "/absolute/capture.json", "deep/path/to/capture.json"])
def test_sidecar_cannot_redirect_to_other_evidence(atp_sidecar, capture):
    sidecar = atp_sidecar()
    payload = json.loads(sidecar.read_text())
    payload["capture"] = capture
    sidecar.write_text(json.dumps(payload))
    assert interpret_sigma_result(sidecar, 0)["outcome"] == "error"


def test_java_class_binding_survives_repacking_but_detects_code_change(tmp_path):
    jars = [tmp_path / name for name in ["original.jar", "repacked.jar", "changed.jar"]]
    for index, jar in enumerate(jars):
        with zipfile.ZipFile(jar, "w") as archive:
            archive.writestr("resource.txt", str(index))
            classes = [("A.class", b"class-a"), ("B.class", b"class-b")]
            if index == 1:
                classes.reverse()
            if index == 2:
                classes[0] = ("A.class", b"changed-class")
            for name, data in classes:
                archive.writestr(name, data)
    assert jar_classes_sha256(jars[0]) == jar_classes_sha256(jars[1])
    assert jar_classes_sha256(jars[0]) != jar_classes_sha256(jars[2])


def test_captured_prover_wall_timeout_remains_inconclusive(atp_sidecar):
    sidecar = atp_sidecar(status="Timeout", atp_exit=137, lines=0)
    capture_path = sidecar.parent / "atp.artifacts/capture.json"
    payload = json.loads(capture_path.read_text())
    payload.update(returncode=-9, timed_out=True)
    capture_path.write_text(json.dumps(payload))
    result = interpret_sigma_result(sidecar, 0, invocation_id="current")
    assert result["status"] == "Timeout"
    assert result["outcome"] == "inconclusive"
    assert not result["proved"]


@pytest.mark.parametrize("source", ["relative.p", "/a/../b.p", "/a//b.p", "//a/b.p"])
def test_saved_source_identity_requires_normalized_absolute_path(source):
    with pytest.raises(ArtifactError, match="normalized absolute lexical path"):
        normalized_source_identity(source)


def test_saved_source_identity_does_not_require_live_file(tmp_path):
    absent = str(tmp_path / "deleted" / "problem.p")
    assert normalized_source_identity(absent) == absent


def test_source_path_checks_ancestors_before_collapsing_parent_steps(tmp_path):
    ordinary = tmp_path / "ordinary.p"
    ordinary.write_text("fof(fact,axiom,p).")
    directory = tmp_path / "directory"
    directory.mkdir()
    assert checked_source_path(directory / ".." / ordinary.name) == ordinary
    with pytest.raises(ArtifactError, match="not a directory"):
        checked_source_path(ordinary / ".." / ordinary.name)
    with pytest.raises(ArtifactError, match="cannot inspect"):
        checked_source_path(tmp_path / "missing.p")
    with pytest.raises(ArtifactError, match="ordinary absolute filesystem root"):
        checked_source_path(Path("/" + str(ordinary)))

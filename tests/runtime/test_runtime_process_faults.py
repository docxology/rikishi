from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from rikishi.runtime import compare, prove
from rikishi.runtime_artifacts import ArtifactError, load_capture
from rikishi.runtime_diagnostics import diagnose


def _fault_executable(root: Path, relative: str, body: str) -> Path:
    binary = root / relative
    binary.parent.mkdir(parents=True, exist_ok=True)
    binary.write_text(f"#!{sys.executable}\n{body}\n")
    binary.chmod(0o700)
    return binary


@pytest.mark.parametrize("stdout,exitcode,message", [
    ("no status", 4, "no SZS status"),
    ("# SZS status Theorem\n# SZS status CounterSatisfiable", 0, "conflicting statuses"),
    ("# SZS status Theorem", 4, "proof status disagrees"),
    ("# SZS status CounterSatisfiable", 4, "model status disagrees"),
])
def test_direct_process_faults_preserve_evidence_and_raise(
    tmp_path: Path, stdout: str, exitcode: int, message: str,
) -> None:
    _fault_executable(tmp_path, ".rikishi/upstream/eprover/PROVER/eprover",
                      f"import sys\nprint({stdout!r})\nsys.exit({exitcode})")
    problem = tmp_path / "problem.p"
    problem.write_text("fof(goal,conjecture,p).\n")
    output = tmp_path / "failure"
    with pytest.raises(RuntimeError, match=message):
        prove(problem, tmp_path, 1, output=output)
    capture = load_capture(output / "capture.json")
    assert capture.returncode == exitcode
    assert (output / "stdout.txt").read_text() == stdout + "\n"


def test_direct_process_timeout_kills_descendants_and_retains_capture(tmp_path: Path) -> None:
    _fault_executable(
        tmp_path, ".rikishi/upstream/eprover/PROVER/eprover",
        "import subprocess,sys,time\n"
        "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'])\n"
        "print(child.pid,flush=True)\ntime.sleep(60)",
    )
    problem = tmp_path / "problem.p"
    problem.write_text("fof(goal,conjecture,p).\n")
    output = tmp_path / "failure"
    with pytest.raises(TimeoutError, match="wall-clock bound"):
        prove(problem, tmp_path, 1, output=output)
    capture = load_capture(output / "capture.json")
    assert capture.timed_out
    assert capture.returncode < 0
    pid = (output / "stdout.txt").read_text().strip()
    process = subprocess.run(["ps", "-o", "stat=", "-p", pid], check=False,
                             capture_output=True, text=True, timeout=5)
    assert not process.stdout.strip() or process.stdout.strip().startswith("Z")


def test_comparison_process_resource_fault_is_inconclusive(tmp_path: Path) -> None:
    for relative in (".rikishi/upstream/eprover/PROVER/eprover", ".rikishi/runtime/vampire"):
        _fault_executable(tmp_path, relative, "print('# SZS status ResourceOut')")
    problem = tmp_path / "problem.p"
    problem.write_text("fof(goal,conjecture,p).\n")
    report = compare(problem, tmp_path, 1, output=tmp_path / "comparison")
    assert report["statuses"] == {"e": "ResourceOut", "v": "ResourceOut"}
    assert report["outcome"] == "inconclusive"
    assert report["agreement"] is None
    assert report["semantic_validation"] is False
    assert json.loads((tmp_path / "comparison/comparison.json").read_text()) == report


def test_comparison_rechecks_first_capture_after_second_process(tmp_path: Path) -> None:
    _fault_executable(tmp_path, ".rikishi/upstream/eprover/PROVER/eprover",
                      "print('# SZS status ResourceOut')")
    _fault_executable(
        tmp_path, ".rikishi/runtime/vampire",
        "import hashlib,json,pathlib,sys\n"
        "directory=pathlib.Path(sys.argv[-1]).parent/'comparison'/'e'\n"
        "problem=directory/'problem.p'\nproblem.write_text('fof(changed,axiom,q).')\n"
        "path=directory/'capture.json'\npayload=json.loads(path.read_text())\n"
        "payload['problem'].update(size=problem.stat().st_size,"
        "sha256=hashlib.sha256(problem.read_bytes()).hexdigest())\n"
        "path.write_text(json.dumps(payload))\nprint('# SZS status ResourceOut')",
    )
    problem = tmp_path / "problem.p"
    problem.write_text("fof(goal,conjecture,p).\n")
    with pytest.raises(ArtifactError, match="comparison"):
        compare(problem, tmp_path, 1, output=tmp_path / "comparison")
    assert not (tmp_path / "comparison/comparison.json").exists()


@pytest.mark.integration
def test_export_replay_gate_rejects_real_subprocess_failure(
    project_root: Path, tmp_path: Path,
) -> None:
    native = project_root / ".rikishi/upstream/eprover/PROVER/eprover"
    _fault_executable(
        tmp_path, ".rikishi/upstream/eprover/PROVER/eprover",
        "import pathlib,subprocess,sys\n"
        "if pathlib.Path(sys.argv[-1]).name=='proof-premises.p':\n sys.exit(17)\n"
        f"sys.exit(subprocess.call([{str(native)!r},*sys.argv[1:]]))",
    )
    problem = tmp_path / "problem.p"
    problem.write_text("fof(fact,axiom,p). fof(goal,conjecture,p).\n")
    prove(problem, tmp_path, 1, output=tmp_path / "original")
    output = tmp_path / "diagnostic"
    with pytest.raises(ArtifactError, match="subset failed native replay"):
        diagnose(tmp_path / "original/capture.json", tmp_path, timeout=1, output=output)
    assert not (output / "diagnostic.json").exists()
    assert load_capture(output / "subset-check/capture.json").returncode == 17

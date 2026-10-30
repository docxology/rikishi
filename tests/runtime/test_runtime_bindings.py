import hashlib
import json
import sys
from pathlib import Path
from uuid import uuid4

import pytest

from rikishi.runtime import prove
from rikishi.runtime_artifacts import ArtifactError, load_capture, read_regular
from rikishi.runtime_capture import capture_prover
from rikishi.runtime_results import ExpectedATPInvocation, interpret_sigma_result


def _sidecar(capture_path: Path, status: str) -> Path:
    capture = load_capture(capture_path)
    path = capture_path.parent.parent / (uuid4().hex + ".result.json")
    path.write_text(json.dumps({
        "status": status, "atp_returncode": capture.returncode,
        "stdout_lines": len(read_regular(capture_path.parent / capture.stdout.path).splitlines()),
        "invocation_id": capture.invocation_id,
        "capture": capture_path.parent.name + "/capture.json",
    }))
    return path


@pytest.mark.integration
def test_arbitrary_producer_cannot_replace_actual_e_countermodel(project_root, tmp_path):
    problem = tmp_path / "nonentailed.p"
    problem.write_text("fof(fact,axiom,p). fof(goal,conjecture,q).\n")
    real = prove(problem, project_root, timeout=5)
    assert real["status"] == "CounterSatisfiable"
    capture_path = Path(real["capture"])
    capture = load_capture(capture_path)
    binary = project_root / ".rikishi/upstream/eprover/PROVER/eprover"
    expected = ExpectedATPInvocation(capture.invocation_id, binary, capture.provenance,
                                     hashlib.sha256(problem.read_bytes()).hexdigest())
    assert interpret_sigma_result(_sidecar(capture_path, "CounterSatisfiable"), 0,
                                  expected=expected)["outcome"] == "not_entailed"
    arbitrary = tmp_path / "arbitrary.artifacts"
    arbitrary.mkdir()
    python_hash = hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest()
    command = [sys.executable, "-c", "print('# SZS status Theorem')", str(problem)]
    with pytest.raises(ArtifactError, match="unsupported E prover argument"):
        capture_prover(command, arbitrary, invocation_id=capture.invocation_id,
                       provenance={"prover_sha256": python_hash}, timeout=5)
    assert not (arbitrary / "stdout.txt").exists()
    driver = tmp_path / "arbitrary-producer"
    driver.write_text(f"#!{sys.executable}\nprint('# SZS status Theorem')\n")
    driver.chmod(0o700)
    command = [str(driver), "--cpu-limit=5", str(problem)]
    capture_prover(command, arbitrary, invocation_id=capture.invocation_id,
                   provenance={"prover_sha256": hashlib.sha256(driver.read_bytes()).hexdigest()}, timeout=5)
    sidecar = _sidecar(arbitrary / "capture.json", "Theorem")
    unbound = interpret_sigma_result(sidecar, 0, invocation_id=capture.invocation_id)
    assert unbound["outcome"] == "unverified"
    assert not unbound["proved"]
    assert interpret_sigma_result(sidecar, 0, expected=expected)["outcome"] == "error"
    rejected = tmp_path / "forged-provenance"
    rejected.mkdir()
    with pytest.raises(ArtifactError, match="recorded prover hash"):
        capture_prover(command, rejected, invocation_id=capture.invocation_id,
                       provenance=dict(capture.provenance), timeout=5)
    assert not (rejected / "stdout.txt").exists()


@pytest.mark.integration
@pytest.mark.parametrize("changed", [None, "input", "invocation", "provenance", "command_input"])
def test_actual_e_theorem_requires_caller_bindings(project_root, tmp_path, changed):
    problem = tmp_path / "entailed.p"
    problem.write_text("fof(fact,axiom,p). fof(goal,conjecture,p).\n")
    real = prove(problem, project_root, timeout=5)
    capture_path = Path(real["capture"])
    capture = load_capture(capture_path)
    provenance = dict(capture.provenance)
    digest = hashlib.sha256(problem.read_bytes()).hexdigest()
    identity = capture.invocation_id
    if changed == "input":
        digest = "0" * 64
    elif changed == "invocation":
        identity = "different"
    elif changed == "provenance":
        provenance["source"] = "different"
    elif changed == "command_input":
        payload = json.loads(capture_path.read_text())
        payload["command"][-1] = str(tmp_path / "other.p")
        capture_path.write_text(json.dumps(payload))
    expected = ExpectedATPInvocation(identity, project_root / ".rikishi/upstream/eprover/PROVER/eprover",
                                     provenance, digest)
    result = interpret_sigma_result(_sidecar(capture_path, "Theorem"), 0, expected=expected)
    assert result["proved"] == (changed is None)
    assert result["outcome"] == ("entailed" if changed is None else "error")

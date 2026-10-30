import json
import os
import shutil
import uuid
from hashlib import sha256
from pathlib import Path

import pytest

from rikishi.inference_models import InferenceError
from rikishi.inference_replay import validate_inference_report
from rikishi.inference_runner import run_inference
from rikishi.runtime_artifacts import ArtifactError

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def inference_campaign(project_root):
    selected = os.environ.get("RIKISHI_INFERENCE_TEST_PACKET")
    if selected:
        directory = Path(selected)
        if not directory.is_absolute():
            directory = project_root / directory
        path = directory / "inference-report.json"
        digest = os.environ["RIKISHI_INFERENCE_TEST_SHA256"]
        report = validate_inference_report(path, trusted_report_sha256=digest)
    else:
        directory = project_root / ".rikishi/results" / ("inference-tests-" + uuid.uuid4().hex)
        # Keep a declared finite budget for real proof search on contended hosts.
        # Resource-policy mutations below derive their expected limit from this report.
        report = run_inference(project_root, directory, timeout=60)
    return directory, report


@pytest.fixture
def inference_copy(inference_campaign, tmp_path):
    destination = tmp_path / "portable"
    shutil.copytree(inference_campaign[0], destination)
    return destination


def _write(path, payload):
    path.write_text(json.dumps(payload, indent=2) + "\n")


def test_real_native_campaign_has_four_polarities_and_consistent_backgrounds(inference_campaign):
    directory, report = inference_campaign
    assert report.summary.passed
    assert report.provers == ["e", "v"]
    assert report.summary.scenarios >= 24
    assert report.summary.total == report.summary.scenarios * 5 * 2
    assert report.summary.matched == report.summary.total
    assert report.summary.mismatched == report.summary.unresolved == 0
    assert {run.observed for run in report.cases} == {
        "Theorem", "CounterSatisfiable", "Satisfiable", "Unsatisfiable"}
    backgrounds = {(run.prover, run.group): run.observed for run in report.cases
                   if run.kind == "background"}
    assert all(backgrounds[(run.prover, run.group)] == "Satisfiable"
               for run in report.cases if run.kind == "positive")
    path = directory / "inference-report.json"
    assert validate_inference_report(path, trusted_report_sha256=sha256(path.read_bytes()).hexdigest()) == report


def test_relocated_packet_replays_without_original_runtime_paths(inference_copy, inference_campaign):
    path = inference_copy / "inference-report.json"
    assert validate_inference_report(path, trusted_report_sha256=sha256(path.read_bytes()).hexdigest()) == inference_campaign[1]


def test_outer_digest_is_required_and_rejects_coherent_report_replacement(inference_copy):
    path = inference_copy / "inference-report.json"
    digest = sha256(path.read_bytes()).hexdigest()
    report = json.loads(path.read_bytes())
    report["summary"]["total"] += 1
    _write(path, report)
    with pytest.raises(InferenceError, match="Trusted report"):
        validate_inference_report(path, trusted_report_sha256=digest)
    with pytest.raises(InferenceError, match="Trusted report"):
        validate_inference_report(path, trusted_report_sha256="")
    with pytest.raises(TypeError):
        validate_inference_report(path)


@pytest.mark.parametrize("mutation", [
    "source", "study", "source-claim", "implementation", "implementation-bytes",
    "binary", "binary-binding", "lock", "lock-binding", "boundary", "study-id", "study-hash",
    "families", "missing-case", "reordered-cases", "case-id", "case-polarity", "case-observation",
    "case-matched", "capture-path", "capture-hash", "problem", "problem-hash", "proof",
    "stderr", "capture-family", "capture-resource", "capture-source", "capture-provenance",
    "capture-exit", "capture-timeout", "capture-invocation", "summary", "status-conflict",
    "status-missing", "background-contradiction", "negative-theorem", "model-exit",
])
def test_replay_rejects_tampered_native_packet_even_with_new_outer_digest(inference_copy, mutation):
    path = inference_copy / "inference-report.json"
    report = json.loads(path.read_bytes())
    index = 0 if mutation in {"background-contradiction", "model-exit"} else 1
    if mutation == "negative-theorem":
        index = 2
    run = report["cases"][index]
    capture_path = inference_copy / run["capture"]
    capture = json.loads(capture_path.read_bytes())
    if mutation == "source":
        source = inference_copy / "source/Merge.kif"
        source.write_bytes(source.read_bytes() + b"\n; source corruption\n")
    elif mutation == "study":
        study_path = inference_copy / "study.json"
        study = json.loads(study_path.read_bytes())
        study["scenarios"][0]["query"] = "(subclass Animal Human)"
        _write(study_path, study)
    elif mutation == "source-claim":
        report["source_claims"][0]["line"] += 1
    elif mutation == "implementation":
        report["implementation"]["kif.py"] = "0" * 64
    elif mutation == "implementation-bytes":
        (inference_copy / "implementation/kif.py").write_bytes(b"changed parser")
    elif mutation == "binary":
        (inference_copy / "binaries/e.bin").write_bytes(b"changed executable")
    elif mutation == "binary-binding":
        run["prover_sha256"] = "0" * 64
    elif mutation == "lock":
        (inference_copy / "sumo.lock.json").write_text("{}")
    elif mutation == "lock-binding":
        report["lock_sha256"] = "0" * 64
    elif mutation == "boundary":
        report["replay_boundary"] = "arbitrary SUMO verified"
    elif mutation == "study-id":
        report["study_id"] = "unknown"
    elif mutation == "study-hash":
        report["study_sha256"] = "0" * 64
    elif mutation == "families":
        report["provers"] = ["e", "e"]
    elif mutation == "missing-case":
        report["cases"].pop()
    elif mutation == "reordered-cases":
        report["cases"][1], report["cases"][2] = report["cases"][2], report["cases"][1]
    elif mutation == "case-id":
        run["group"] = "invented"
    elif mutation == "case-polarity":
        run["expected"] = "CounterSatisfiable"
    elif mutation == "case-observation":
        run["observed"] = "Unsatisfiable"
    elif mutation == "case-matched":
        run["matched"] = False
    elif mutation == "capture-path":
        run["capture"] = "../capture.json"
    elif mutation == "capture-hash":
        run["capture_sha256"] = "0" * 64
    elif mutation == "problem":
        (inference_copy / "problems" / f"{run['id']}.p").write_text("fof(false,axiom,$false).\n")
    elif mutation == "problem-hash":
        run["problem_sha256"] = "0" * 64
    elif mutation in {"proof", "stderr"}:
        artifact = capture["stdout" if mutation == "proof" else "stderr"]
        target = capture_path.parent / artifact["path"]
        target.write_bytes(target.read_bytes() + b"\n% corrupted native bytes\n")
    elif mutation.startswith("capture-") or mutation == "model-exit":
        if mutation == "capture-family":
            capture["prover"] = "v"
        elif mutation == "capture-resource":
            original = list(capture["command"])
            limit = report["timeout_seconds"]
            capture["command"] = [arg.replace(f"--cpu-limit={limit}", f"--cpu-limit={limit + 1}")
                                  for arg in original]
            assert capture["command"] != original
        elif mutation == "capture-source":
            capture["source_problem"] += ".changed"
        elif mutation == "capture-provenance":
            capture["provenance"]["prover_sha256"] = "0" * 64
        elif mutation in {"capture-exit", "model-exit"}:
            capture["returncode"] = 7
        elif mutation == "capture-timeout":
            capture["timed_out"] = True
        elif mutation == "capture-invocation":
            capture["invocation_id"] = "stale"
        _write(capture_path, capture)
        run["capture_sha256"] = sha256(capture_path.read_bytes()).hexdigest()
    elif mutation == "summary":
        report["summary"]["matched"] -= 1
    else:
        target = capture_path.parent / capture["stdout"]["path"]
        raw = target.read_bytes()
        if mutation == "status-conflict":
            raw += b"\n# SZS status CounterSatisfiable\n"
        elif mutation == "status-missing":
            raw = raw.replace(b"SZS status", b"removed status")
        else:
            changed = "Unsatisfiable" if mutation == "background-contradiction" else "Theorem"
            raw = raw.replace(f"SZS status {run['observed']}".encode(), f"SZS status {changed}".encode())
            run["observed"] = changed
            capture["returncode"] = 0
        target.write_bytes(raw)
        capture["stdout"]["sha256"] = sha256(raw).hexdigest()
        capture["stdout"]["size"] = len(raw)
        _write(capture_path, capture)
        run["capture_sha256"] = sha256(capture_path.read_bytes()).hexdigest()
    _write(path, report)
    with pytest.raises((InferenceError, ArtifactError, ValueError)):
        validate_inference_report(path, trusted_report_sha256=sha256(path.read_bytes()).hexdigest())

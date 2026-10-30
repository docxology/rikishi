import json
import shutil
import subprocess
import sys
import uuid
from hashlib import sha256

import pytest

from rikishi.alignment import (
    alignment_substitutions,
    run_alignment,
    validate_alignment_report,
)
from rikishi.competency import AlignmentError
from rikishi.ontology import OntologyIndex
from rikishi.runtime_artifacts import ArtifactError
from rikishi.sumo_demonstrations import demonstrate_sumo


@pytest.fixture(scope="module")
def campaign(project_root, native_workspace, portable_inputs):
    directory = native_workspace / (
        "alignment-tests-" + uuid.uuid4().hex)
    report = run_alignment(project_root, directory, workbook_path=portable_inputs.workbook_path)
    return directory, report


@pytest.fixture
def copied(campaign, tmp_path):
    directory, _ = campaign
    destination = tmp_path / "portable"
    shutil.copytree(directory, destination, ignore=shutil.ignore_patterns("negative-controls"))
    return destination


def _write(path, payload):
    path.write_text(json.dumps(payload, indent=2) + "\n")


def _bind_capture(directory, report, index=0):
    run = report["logical"][index]
    path = directory / run["capture"]
    run["capture_sha256"] = sha256(path.read_bytes()).hexdigest()


@pytest.mark.integration
def test_native_campaign_has_satisfiable_baseline_and_all_controls(campaign):
    directory, report = campaign
    assert report.summary.campaign_complete
    assert report.summary.baseline_satisfiable
    assert report.summary.logical_cases == report.summary.logical_matched == 12
    assert report.summary.numerical_rows == report.summary.numerical_passed == 144
    assert not report.summary.semantic_validation
    outcomes = {r.id: r.observed for r in report.logical}
    assert outcomes["empty-double-class"] == "Satisfiable"
    assert outcomes["inhabited-double-class"] == outcomes["alias"] == "Unsatisfiable"
    assert outcomes["model-physical"] == "CounterSatisfiable"
    assert outcomes["model-not-physical"] == "Theorem"
    assert validate_alignment_report(directory / "alignment-report.json") == report
    substitutions = alignment_substitutions(report)
    assert substitutions["ALIGNMENT_LOGICAL_MATCHED"] == "12"
    assert substitutions["ALIGNMENT_NUMERICAL_ROWS"] == "144"


@pytest.mark.integration
def test_portable_replay_uses_frozen_sources_and_captures(copied, campaign):
    path = copied / "alignment-report.json"
    outer = sha256(path.read_bytes()).hexdigest()
    assert validate_alignment_report(path, trusted_report_sha256=outer) == campaign[1]


@pytest.mark.integration
@pytest.mark.parametrize("mutation", [
    "source-excerpt", "source-row", "source-rehash", "workbook", "study-polarity",
    "run-polarity", "numerical", "summary", "problem", "solver-bytes", "solver-rehash",
    "capture-path", "capture-family", "capture-resource", "capture-exit", "missing-case",
    "extension", "bindings", "implementation", "capture-binding", "missing-status", "model-exit",
])
def test_portable_replay_rejects_real_copied_mutations(copied, mutation, campaign):
    path = copied / "alignment-report.json"
    report = json.loads(path.read_bytes())
    run = report["logical"][1]
    capture_path = copied / run["capture"]
    capture = json.loads(capture_path.read_bytes())
    match mutation:
        case "source-excerpt":
            citation = report["source_claims"]["citations"][0]
            citation["raw_kif"] = "(subclass Process Abstract)"
            citation["sha256"] = sha256(citation["raw_kif"].encode()).hexdigest()
        case "source-row":
            report["source_claims"]["cells"]["I190"] = "invented source sense"
        case "source-rehash":
            source_path = copied / "source-report.json"
            source = json.loads(source_path.read_bytes())
            source["source"]["text"] += "\n; changed complete source\n"
            source["source"]["sha256"] = sha256(source["source"]["text"].encode()).hexdigest()
            _write(source_path, source)
        case "workbook":
            workbook = copied / "workbook.xlsx"
            workbook.write_bytes(workbook.read_bytes() + b"false source")
        case "study-polarity":
            study_path = copied / "study.json"
            study = json.loads(study_path.read_bytes())
            study["cases"][1]["expected"] = "CounterSatisfiable"
            _write(study_path, study)
        case "run-polarity":
            run["expected"] = "CounterSatisfiable"
        case "numerical":
            report["numerical"]["rows"][0]["result"]["free_energy"] += 0.25
        case "summary":
            report["summary"]["logical_matched"] += 1
        case "problem":
            (copied / "problems/model-abstract.p").write_text("fof(false,axiom,$false).\n")
        case "solver-bytes" | "solver-rehash":
            stdout = capture_path.parent / capture["stdout"]["path"]
            changed = stdout.read_bytes().replace(b"SZS status Theorem", b"SZS status CounterSatisfiable")
            assert changed != stdout.read_bytes()
            stdout.write_bytes(changed)
            if mutation == "solver-rehash":
                capture["stdout"]["size"] = len(changed)
                capture["stdout"]["sha256"] = sha256(changed).hexdigest()
                _write(capture_path, capture)
                _bind_capture(copied, report, 1)
        case "capture-path":
            run["capture"] = "../capture.json"
        case "capture-binding":
            run["capture_sha256"] = "0" * 64
        case "missing-status":
            stdout = capture_path.parent / capture["stdout"]["path"]
            changed = stdout.read_bytes().replace(b"SZS status Theorem", b"removed status Theorem")
            stdout.write_bytes(changed)
            capture["stdout"]["size"] = len(changed)
            capture["stdout"]["sha256"] = sha256(changed).hexdigest()
            _write(capture_path, capture)
            _bind_capture(copied, report, 1)
        case "model-exit":
            capture_path = copied / report["logical"][0]["capture"]
            capture = json.loads(capture_path.read_bytes())
            capture["returncode"] = 7
            _write(capture_path, capture)
            _bind_capture(copied, report)
        case "capture-family":
            capture["prover"] = "v"
            _write(capture_path, capture)
            _bind_capture(copied, report, 1)
        case "capture-resource":
            capture["command"] = [arg.replace("--cpu-limit=5", "--cpu-limit=4")
                                  for arg in capture["command"]]
            _write(capture_path, capture)
            _bind_capture(copied, report, 1)
        case "capture-exit":
            capture["returncode"] = 7
            _write(capture_path, capture)
            _bind_capture(copied, report, 1)
        case "missing-case":
            report["logical"].pop()
        case "extension":
            (copied / "extension.kif").write_text("(instance model Process)\n")
        case "bindings":
            (copied / "bindings/uv.lock").write_text("false lock")
        case "implementation":
            report["implementation"]["src/rikishi/alignment.py"] = "0" * 64
    _write(path, report)
    with pytest.raises((AlignmentError, ArtifactError, ValueError)) as rejected:
        validate_alignment_report(path)
    retained = campaign[0] / "negative-controls" / mutation
    shutil.copytree(copied, retained)
    _write(retained / "rejection.json", {"control": mutation, "rejected": True,
                                       "error_type": type(rejected.value).__name__,
                                       "error": str(rejected.value)})


@pytest.mark.integration
@pytest.mark.parametrize("status", ["Unsatisfiable", "GaveUp"])
def test_saved_bad_baseline_blocks_acceptance_even_when_rehashed(copied, status, campaign):
    path = copied / "alignment-report.json"
    report = json.loads(path.read_bytes())
    run = report["logical"][0]
    capture_path = copied / run["capture"]
    capture = json.loads(capture_path.read_bytes())
    stdout = capture_path.parent / capture["stdout"]["path"]
    data = stdout.read_bytes().replace(b"SZS status Satisfiable", f"SZS status {status}".encode())
    stdout.write_bytes(data)
    capture["stdout"]["size"] = len(data)
    capture["stdout"]["sha256"] = sha256(data).hexdigest()
    capture["returncode"] = 0
    _write(capture_path, capture)
    _bind_capture(copied, report)
    run["observed"] = status
    run["disposition"] = "mismatch" if status == "Unsatisfiable" else "unresolved"
    summary = report["summary"]
    summary.update(logical_matched=11, logical_mismatched=int(status == "Unsatisfiable"),
                   logical_unresolved=int(status == "GaveUp"), baseline_satisfiable=False,
                   campaign_complete=False)
    _write(path, report)
    valid = validate_alignment_report(path)
    assert not valid.summary.campaign_complete
    assert not valid.summary.baseline_satisfiable
    retained = campaign[0] / "negative-controls" / ("synthetic-baseline-" + status)
    shutil.copytree(copied, retained)
    _write(retained / "control.json", {"control": "synthetic-saved-baseline", "status": status,
                                     "live_invocation": False, "summary": valid.summary.model_dump()})


@pytest.mark.integration
def test_outer_binding_rejects_coherent_saved_report_replacement(copied):
    path = copied / "alignment-report.json"
    outer = sha256(path.read_bytes()).hexdigest()
    report = json.loads(path.read_bytes())
    report["replay_boundary"] += " coherent replacement"
    _write(path, report)
    with pytest.raises(AlignmentError, match="Outer report"):
        validate_alignment_report(path, trusted_report_sha256=outer)


@pytest.mark.integration
def test_runner_refuses_existing_campaign_output(campaign, project_root, portable_inputs):
    with pytest.raises(FileExistsError):
        run_alignment(project_root, campaign[0], workbook_path=portable_inputs.workbook_path)


@pytest.mark.integration
@pytest.mark.parametrize("name", ["captures", "problems", "bindings"])
def test_replay_rejects_symlinked_evidence_directories(copied, tmp_path, name):
    source = copied / name
    source.rename(tmp_path / name)
    source.symlink_to(tmp_path / name, target_is_directory=True)
    with pytest.raises(ArtifactError, match="symlink"):
        validate_alignment_report(copied / "alignment-report.json")


@pytest.mark.integration
def test_explicit_inputs_resolve_against_root_without_historical_paths(
    project_root, tmp_path, native_workspace, portable_inputs,
):
    output = native_workspace / (
        "alignment-relative-source-" + uuid.uuid4().hex)
    inputs = native_workspace / (
        "alignment-explicit-inputs-" + uuid.uuid4().hex)
    inputs.mkdir()
    shutil.copyfile(portable_inputs.workbook_path, inputs / "original.xlsx")
    index = OntologyIndex(inputs / "sumo.sqlite")
    index.build(project_root / ".rikishi/upstream/sumo")
    source = demonstrate_sumo(index, project_root)
    (inputs / "source-report.json").write_text(source.model_dump_json(indent=2) + "\n")
    command = [sys.executable, "-c", (
        "import sys; from pathlib import Path; from rikishi.alignment import run_alignment; "
        "r=run_alignment(Path(sys.argv[1]),Path(sys.argv[2]),"
        "source_report=Path(sys.argv[3])/'source-report.json',"
        "workbook_path=Path(sys.argv[3])/'original.xlsx'); "
        "assert r.summary.campaign_complete"), str(project_root), str(output)]
    command.append(str(inputs.relative_to(project_root)))
    result = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr


@pytest.mark.integration
def test_vampire_campaign_uses_the_same_declared_problems(project_root, campaign, portable_inputs):
    directory = campaign[0].with_name(campaign[0].name + "-v")
    report = run_alignment(project_root, directory, prover="v",
                           workbook_path=portable_inputs.workbook_path)
    assert report.summary.campaign_complete
    assert [run.problem_sha256 for run in report.logical] == [run.problem_sha256 for run in campaign[1].logical]
    assert validate_alignment_report(directory / "alignment-report.json") == report

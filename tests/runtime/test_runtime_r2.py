import hashlib
import json
from pathlib import Path
from uuid import uuid4

import pytest

from rikishi.runtime import prove
from rikishi.runtime_artifacts import (
    COMMAND_POLICY,
    PATH_POLICY,
    ArtifactError,
    Capture,
    IncludedArtifact,
    read_regular,
    receipt,
)
from rikishi.runtime_capture import capture_prover
from rikishi.runtime_diagnostics import main as diagnose_cli
from rikishi.runtime_diagnostics import proof_premises
from rikishi.runtime_process import run_bounded
from rikishi.runtime_results import ExpectedATPInvocation, interpret_sigma_result


@pytest.mark.integration
@pytest.mark.parametrize("slashes", [2, 4])
def test_native_escaped_include_mismatch_is_rejected(project_root, tmp_path, slashes):
    decoded = tmp_path / ("background" + "\\" * (slashes // 2) + "name.p")
    literal = tmp_path / ("background" + "\\" * slashes + "name.p")
    decoded.write_text("fof(wrong,axiom,q).\n")
    literal.write_text("fof(right,axiom,p).\n")
    assert decoded.read_bytes() != literal.read_bytes()
    assert not decoded.samefile(literal)
    problem = tmp_path / "query.p"
    problem.write_text(f"include('{literal.name}').\nfof(goal,conjecture,p).\n")
    binary = project_root / ".rikishi/upstream/eprover/PROVER/eprover"
    command = [str(binary), "--auto", "--tstp-format", "--proof-object", "--cpu-limit=5", str(problem)]
    original = run_bounded(command, cwd=tmp_path, stdout=tmp_path / "stdout.txt",
                           stderr=tmp_path / "stderr.txt", timeout=10)
    assert original.returncode == 0
    assert "SZS status Theorem" in (tmp_path / "stdout.txt").read_text()
    provenance = {"prover_sha256": hashlib.sha256(read_regular(binary)).hexdigest()}
    rejected = tmp_path / "rejected"
    rejected.mkdir()
    with pytest.raises(ArtifactError, match="backslashes in include paths"):
        capture_prover(command, rejected, invocation_id="r2", provenance=provenance, timeout=10)
    assert not (rejected / "stdout.txt").exists()
    assert not (rejected / "capture.json").exists()
    directory = tmp_path / "old.artifacts"
    directory.mkdir()
    (directory / "problem.p").write_bytes(problem.read_bytes())
    (directory / "include-0.p").write_bytes(decoded.read_bytes())
    (directory / "stdout.txt").write_bytes((tmp_path / "stdout.txt").read_bytes())
    (directory / "stderr.txt").write_bytes((tmp_path / "stderr.txt").read_bytes())
    capture = Capture(
        path_policy=PATH_POLICY,
        command_policy=COMMAND_POLICY, prover="e",
        invocation_id="r2", command=command, source_problem=str(problem),
        problem=receipt(directory / "problem.p", directory),
        includes=[IncludedArtifact(**receipt(directory / "include-0.p", directory).model_dump(),
                                   source=str(decoded))],
        stdout=receipt(directory / "stdout.txt", directory),
        stderr=receipt(directory / "stderr.txt", directory),
        returncode=0, timed_out=False, provenance=provenance,
    )
    (directory / "capture.json").write_text(capture.model_dump_json())
    sidecar = tmp_path / "result.json"
    sidecar.write_text(json.dumps({
        "status": "Theorem", "atp_returncode": 0,
        "stdout_lines": len((directory / "stdout.txt").read_text().splitlines()),
        "invocation_id": "r2", "capture": directory.name + "/capture.json",
    }))
    expected = ExpectedATPInvocation("r2", binary, provenance, hashlib.sha256(problem.read_bytes()).hexdigest())
    result = interpret_sigma_result(sidecar, 0, expected=expected)
    assert result["status"] == "InvalidATPResult"
    assert not result["proved"]


@pytest.mark.integration
@pytest.mark.parametrize("fact,goal", [
    ("'fact'", "'goal'"),
    ("'fact name'", "'goal name'"),
    (r"'fact\\name'", r"'goal\\name'"),
    (r"'fact\\s name'", r"'goal\\s name'"),
])
def test_native_quoted_proof_names_export_and_replay(project_root, tmp_path, capsys, fact, goal):
    problem = tmp_path / "quoted.p"
    problem.write_text(f"fof({fact},axiom,p).\nfof({goal},conjecture,p).\n")
    original = prove(problem, project_root, timeout=5)
    assert original["status"] == "Theorem"
    output = project_root / ".rikishi/results" / (uuid4().hex + "-r2-quoted")
    assert diagnose_cli([original["capture"], "--root", str(project_root),
                         "--timeout", "5", "--output", str(output)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["premise_count"] == 2
    assert report["subset_status"] == "Theorem"
    subset = Path(report["premises"])
    assert subset.read_text() == problem.read_text()
    assert prove(subset, project_root, timeout=5)["status"] == "Theorem"


@pytest.mark.integration
def test_native_apostrophe_name_collision_fails_closed(project_root, tmp_path):
    binary = project_root / ".rikishi/upstream/eprover/PROVER/eprover"
    provenance = {"prover_sha256": hashlib.sha256(read_regular(binary)).hexdigest()}
    names = [(r"'fact\'s name'", r"'goal\'s name'"),
             (r"'fact\\s name'", r"'goal\\s name'")]
    observed = []
    problems = []
    for index, (fact, goal) in enumerate(names):
        problem = tmp_path / f"names-{index}.p"
        problem.write_text(f"fof({fact},axiom,p).\nfof({goal},conjecture,p).\n")
        problems.append(problem)
        result = run_bounded(
            [str(binary), "--auto", "--tstp-format", "--proof-object", "--cpu-limit=5", str(problem)],
            cwd=tmp_path, stdout=tmp_path / f"stdout-{index}.txt",
            stderr=tmp_path / f"stderr-{index}.txt", timeout=10,
        )
        assert result.returncode == 0
        stdout = (tmp_path / f"stdout-{index}.txt").read_text()
        assert "SZS status Theorem" in stdout
        observed.append(proof_premises(stdout))
    assert problems[0].read_bytes() != problems[1].read_bytes()
    assert observed[0] == observed[1] == ["fact\\s name", "goal\\s name"]
    rejected = tmp_path / "rejected"
    rejected.mkdir()
    with pytest.raises(ArtifactError, match="escaped apostrophes in formula names"):
        capture_prover([str(binary), "--auto", "--cpu-limit=5", str(problems[0])], rejected,
                       invocation_id="r2-apostrophe", provenance=provenance, timeout=10)
    assert not (rejected / "stdout.txt").exists()

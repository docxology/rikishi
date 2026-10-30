import hashlib
import json
import os
import subprocess
from pathlib import Path
from uuid import uuid4

import pytest

from rikishi.runtime import prove
from rikishi.runtime_artifacts import ArtifactError, load_capture, read_regular
from rikishi.runtime_context import (
    CONTRADICTORY_BACKGROUND_SHA256,
    CONTRADICTORY_CORE_BINDINGS,
    recorded_negative_context,
)
from rikishi.runtime_diagnostics import diagnose, main, proof_premises


@pytest.mark.parametrize("removed", [None, 0, 1, 2, 3])
@pytest.mark.integration
def test_saved_real_core_and_each_single_deletion(project_root, tmp_path, removed):
    fixture = Path(__file__).parent / "fixtures/path-contradiction.p"
    problem = tmp_path / "subset.p"
    problem.write_text("\n".join(line for i, line in enumerate(fixture.read_text().splitlines())
                                 if i != removed) + "\n")
    result = prove(problem, project_root, timeout=5)
    assert result["status"] == ("Unsatisfiable" if removed is None else "Satisfiable")
    capture_path = Path(result["capture"])
    capture = load_capture(capture_path)
    assert read_regular(capture_path.parent / capture.problem.path) == problem.read_bytes()
    assert not result["proved"]


def test_proof_premises_require_complete_refutation_block():
    leaf = "fof(a,axiom,p,file('/saved/problem.p',a))."
    assert proof_premises(leaf) == []
    assert proof_premises("# SZS output start CNFRefutation\n" + leaf) == []
    block = "# SZS output start CNFRefutation\n" + leaf + "\n# SZS output end CNFRefutation"
    assert proof_premises(block) == ["a"]


@pytest.mark.parametrize("changed", [*CONTRADICTORY_CORE_BINDINGS, "background"])
def test_historical_context_requires_matching_profile_and_sources(changed):
    bindings = dict(CONTRADICTORY_CORE_BINDINGS)
    backgrounds = [CONTRADICTORY_BACKGROUND_SHA256]
    assert recorded_negative_context(bindings, backgrounds) == "contradictory_translated_axioms_previously_observed"
    if changed == "background":
        backgrounds = ["different"]
    else:
        bindings[changed] = "different"
    assert recorded_negative_context(bindings, backgrounds) == "unknown"


@pytest.mark.parametrize("timeout", [0, 31])
def test_diagnostics_are_bounded_before_reading_capture(tmp_path, timeout):
    with pytest.raises(ValueError, match="CPU limit"):
        diagnose(tmp_path / "absent", tmp_path, timeout=timeout, output=tmp_path / "result")


def test_diagnostics_reject_tampered_input_before_running(atp_sidecar, tmp_path):
    sidecar = atp_sidecar()
    capture_path = tmp_path / "atp.artifacts/capture.json"
    (capture_path.parent / "problem.p").write_text("changed")
    with pytest.raises(ArtifactError, match="checksum"):
        diagnose(capture_path, tmp_path, output=tmp_path / "result")
    assert not (tmp_path / "result").exists()
    assert sidecar.exists()


@pytest.mark.integration
def test_real_saved_problem_diagnostic_cli(project_root, tmp_path, capsys):
    fixture = Path(__file__).parent / "fixtures/path-contradiction.p"
    result = prove(fixture, project_root, timeout=5)
    output = project_root / ".rikishi/results" / (uuid4().hex + "-diagnostic")
    assert main([result["capture"], "--root", str(project_root), "--timeout", "5", "--output", str(output)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "Unsatisfiable"
    assert report["premise_count"] == 4
    assert report["minimality"] == "not_established"
    assert (output / "proof-premises.p").read_bytes() == fixture.read_bytes()


@pytest.mark.integration
def test_inconclusive_diagnostic_and_unsafe_replay_requests(project_root, tmp_path, capsys):
    problem = tmp_path / "countermodel.p"
    problem.write_text("fof(fact,axiom,p).\nfof(goal,conjecture,q).\n")
    result = prove(problem, project_root, timeout=5)
    capture_path = Path(result["capture"])
    with pytest.raises(ValueError, match="inside the repository"):
        diagnose(capture_path, project_root, output=tmp_path / "outside")
    output = project_root / ".rikishi/results" / (uuid4().hex + "-countermodel")
    assert main([str(capture_path), "--root", str(project_root), "--output", str(output)]) == 2
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "CounterSatisfiable"
    assert report["premise_count"] == 0
    payload = json.loads(capture_path.read_text())
    payload["command"].insert(1, "--output-file=/unowned")
    capture_path.write_text(json.dumps(payload))
    with pytest.raises(ArtifactError, match="unsupported"):
        diagnose(capture_path, project_root, output=output)
    payload["command"].remove("--output-file=/unowned")
    payload["provenance"]["prover_sha256"] = "changed"
    capture_path.write_text(json.dumps(payload))
    with pytest.raises(ArtifactError, match="same recorded E"):
        diagnose(capture_path, project_root, output=output)


@pytest.mark.integration
@pytest.mark.parametrize("source", ["RuntimeTypeGuardRegression.java", "RuntimeCacheDiagnostic.java"])
def test_real_java_regressions(project_root, tmp_path, source):
    environment = json.loads((project_root / ".rikishi/runtime/environment.json").read_text())
    java = Path(environment["JAVA_HOME"]) / "bin/java"
    sigma = Path(environment["SIGMA_SRC"])
    command = [str(java), f"-Duser.home={project_root / '.rikishi/runtime'}",
               f"-Djava.io.tmpdir={tmp_path}", "-cp", f"{sigma}/build/sigmakee.jar:{sigma}/lib/*",
               str(project_root / "scripts/runtime" / source), str(tmp_path)]
    result = subprocess.run(command, env=dict(os.environ, **environment), cwd=project_root,
                            capture_output=True, text=True, timeout=30, check=False)
    assert result.returncode == 0, result.stderr
    if source == "RuntimeTypeGuardRegression.java":
        assert "subclass" in result.stdout
        assert "s__ExtensionFn(s__Oval)" in result.stdout
        assert "s__Human" in result.stdout
    else:
        assert "parentPartial=false; pathPartial=false; pathTotal=true" in result.stdout
        assert "parentPartial=true; pathPartial=true; pathTotal=true" in result.stdout
    lock = json.loads((project_root / "config/sumo.lock.json").read_text())
    patch = lock["patches"][0]
    assert hashlib.sha256((project_root / patch["path"]).read_bytes()).hexdigest() == patch["sha256"]
    if source == "RuntimeTypeGuardRegression.java":
        original = subprocess.run(
            ["git", "show", lock["repositories"]["sigmakee"]["commit"] + ":" + patch["source"]],
            cwd=sigma, capture_output=True, timeout=10, check=True,
        ).stdout
        assert hashlib.sha256(original).hexdigest() == patch["before_sha256"]
        unpatched = tmp_path / "FormulaPreprocessor.java"
        unpatched.write_bytes(original)
        classes = tmp_path / "classes"
        classes.mkdir()
        compiled = subprocess.run(
            [str(java.with_name("javac")), "-cp", command[4], "-d", str(classes), str(unpatched)],
            cwd=project_root, env=dict(os.environ, **environment),
            capture_output=True, text=True, timeout=60, check=False,
        )
        assert compiled.returncode == 0, compiled.stderr
        negative = list(command)
        negative[4] = str(classes) + ":" + command[4]
        rejected = subprocess.run(negative, env=dict(os.environ, **environment), cwd=project_root,
                                  capture_output=True, text=True, timeout=30, check=False)
        assert rejected.returncode != 0
        assert "Compound class was flattened" in rejected.stderr

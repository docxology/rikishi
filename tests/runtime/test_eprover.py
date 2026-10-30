import json
import os
import subprocess

import pytest

from rikishi.runtime import bootstrap, prove, status
from rikishi.runtime_artifacts import ArtifactError


@pytest.mark.integration
def test_installed_runtime_is_pinned(project_root):
    result = status(project_root)
    assert result["eprover"]
    assert result["sumo_files"] > 100
    assert all(item["pinned"] for item in result["repositories"].values())


def test_missing_runtime_is_explicit(tmp_path):
    (tmp_path / "config").mkdir()
    (tmp_path / "config/sumo.lock.json").write_text(json.dumps({"repositories": {"sumo": {"commit": "absent"}}}))
    assert status(tmp_path)["repositories"] == {"sumo": {"commit": None, "pinned": False, "changes": None}}
    problem = tmp_path / "missing.p"
    problem.write_text("fof(goal,conjecture,p).")
    with pytest.raises(FileNotFoundError, match="E prover"):
        prove(problem, tmp_path)


@pytest.mark.parametrize("timeout", [0, 301])
def test_invalid_timeout(timeout, tmp_path):
    with pytest.raises(ValueError, match="timeout"):
        prove(tmp_path / "missing", tmp_path, timeout)


@pytest.mark.parametrize("conjecture,expected", [("mortal(socrates)", "Theorem"), ("immortal(socrates)", "CounterSatisfiable")])
@pytest.mark.integration
def test_real_e_distinguishes_entailment(tmp_path, conjecture, expected, project_root):
    problem = tmp_path / "syllogism.p"
    problem.write_text("fof(rule,axiom,(![X]:(human(X)=>mortal(X)))).\n"
                       "fof(fact,axiom,human(socrates)).\n"
                       f"fof(goal,conjecture,{conjecture}).\n")
    result = prove(problem, project_root)
    assert result["status"] == expected
    assert result["proved"] == (expected == "Theorem")


@pytest.mark.integration
def test_real_e_rejects_malformed_input(tmp_path, project_root):
    problem = tmp_path / "broken.p"
    problem.write_text("this is not TPTP")
    with pytest.raises(ArtifactError, match="unsupported TPTP"):
        prove(problem, project_root)


@pytest.mark.integration
def test_special_problem_is_rejected_before_prover_launch(tmp_path, project_root):
    problem = tmp_path / "blocked.p"
    os.mkfifo(problem)
    with pytest.raises(ArtifactError, match="regular file"):
        prove(problem, project_root, timeout=1)


def test_bootstrap_failure_propagates(tmp_path):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts/bootstrap-sumo.sh").write_text("exit 17\n")
    with pytest.raises(subprocess.CalledProcessError) as caught:
        bootstrap(tmp_path)
    assert caught.value.returncode == 17

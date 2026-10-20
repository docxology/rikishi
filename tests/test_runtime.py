import hashlib
import json
import os
import runpy
import subprocess
from pathlib import Path

import pytest

from rikishi.runtime import bootstrap, interpret_sigma_result, prove, status

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.integration
def test_installed_runtime_is_pinned():
    result = status(ROOT)
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
        prove(tmp_path / "missing", ROOT, timeout)


@pytest.mark.parametrize("conjecture,expected", [("mortal(socrates)", "Theorem"), ("immortal(socrates)", "CounterSatisfiable")])
@pytest.mark.integration
def test_real_e_distinguishes_entailment(tmp_path, conjecture, expected):
    problem = tmp_path / "syllogism.p"
    problem.write_text("fof(rule,axiom,(![X]:(human(X)=>mortal(X)))).\n"
                       "fof(fact,axiom,human(socrates)).\n"
                       f"fof(goal,conjecture,{conjecture}).\n")
    result = prove(problem, ROOT)
    assert result["status"] == expected
    assert result["proved"] == (expected == "Theorem")


@pytest.mark.integration
def test_real_e_rejects_malformed_input(tmp_path):
    problem = tmp_path / "broken.p"
    problem.write_text("this is not TPTP")
    with pytest.raises(RuntimeError, match="no SZS status"):
        prove(problem, ROOT)


@pytest.mark.integration
def test_real_e_wall_clock_bound(tmp_path):
    problem = tmp_path / "blocked.p"
    os.mkfifo(problem)
    with pytest.raises(TimeoutError, match="wall-clock"):
        prove(problem, ROOT, timeout=1)


def test_bootstrap_failure_propagates(tmp_path):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts/bootstrap-sumo.sh").write_text("exit 17\n")
    with pytest.raises(subprocess.CalledProcessError) as caught:
        bootstrap(tmp_path)
    assert caught.value.returncode == 17


def test_interrupted_git_checkout_resumes_and_preserves_wrong_pin(tmp_path):
    ensure = runpy.run_path(str(ROOT / "scripts/runtime-bootstrap.py"))["ensure_repository"]
    source = tmp_path / "origin"
    subprocess.run(["git", "init", str(source)], check=True, capture_output=True)
    (source / "Merge.kif").write_text("(subclass Human Animal)")
    subprocess.run(["git", "add", "."], cwd=source, check=True, capture_output=True)
    subprocess.run(["git", "-c", "user.name=Runtime Test", "-c", "user.email=test@example.invalid",
                    "-c", "commit.gpgsign=false", "commit", "-m", "fixture"], cwd=source,
                   check=True, capture_output=True)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
    pin = {"url": str(source), "commit": commit}
    destination = tmp_path / "interrupted"
    subprocess.run(["git", "init", str(destination)], check=True, capture_output=True)
    with pytest.raises(subprocess.CalledProcessError):
        ensure(destination, {"url": str(tmp_path / "absent"), "commit": commit})
    ensure(destination, pin)
    assert (destination / "Merge.kif").read_text() == "(subclass Human Animal)"
    ensure(destination, pin)
    with pytest.raises(RuntimeError, match="refusing reset"):
        ensure(destination, dict(pin, commit="0" * 40))
    ensure(tmp_path / "fresh", pin)
    interrupted_dirty = tmp_path / "dirty"
    subprocess.run(["git", "init", str(interrupted_dirty)], check=True, capture_output=True)
    (interrupted_dirty / "owned.txt").write_text("preserve")
    with pytest.raises(RuntimeError, match="local files"):
        ensure(interrupted_dirty, pin)
    assert (interrupted_dirty / "owned.txt").read_text() == "preserve"


def test_sigma_copy_pin_guard_and_partial_resume(tmp_path):
    copy = runpy.run_path(str(ROOT / "scripts/runtime-bootstrap.py"))["copy_corpus"]
    source = tmp_path / "source"
    source.mkdir()
    (source / ".git").mkdir()
    (source / "Merge.kif").write_text("complete")
    (source / "nested").mkdir()
    (source / "nested/data.kif").write_text("nested")
    kb = tmp_path / "sigma/KBs"
    kb.mkdir(parents=True)
    (kb / "Merge.kif").write_text("legacy data")
    with pytest.raises(RuntimeError, match="unmarked Sigma file differs"):
        copy(source, kb, "pin-one")
    assert (kb / "Merge.kif").read_text() == "legacy data"
    (kb / "Merge.kif").write_text("complete")
    copy(source, kb, "pin-one")
    assert (kb / "Merge.kif").read_text() == "complete"
    assert (kb / "nested/data.kif").read_text() == "nested"
    assert not (kb / ".git").exists()
    (kb / "Merge.kif").write_text("local editing preserved")
    copy(source, kb, "pin-one")
    assert (kb / "Merge.kif").read_text() == "local editing preserved"
    with pytest.raises(RuntimeError, match="different SUMO pin"):
        copy(source, kb, "pin-two")


def test_compatibility_patch_integrity_and_idempotence(tmp_path):
    apply = runpy.run_path(str(ROOT / "scripts/runtime-bootstrap.py"))["apply_compatibility_patch"]
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    target = tmp_path / "fixture.txt"
    target.write_text("original\n")
    patch = tmp_path / "fix.patch"
    patch.write_text("diff --git a/fixture.txt b/fixture.txt\n--- a/fixture.txt\n+++ b/fixture.txt\n"
                     "@@ -1 +1 @@\n-original\n+corrected\n")
    specification = {"path": str(patch), "source": "fixture.txt",
                     "sha256": hashlib.sha256(patch.read_bytes()).hexdigest(),
                     "before_sha256": hashlib.sha256(b"original\n").hexdigest(),
                     "after_sha256": hashlib.sha256(b"corrected\n").hexdigest()}
    apply(tmp_path, specification)
    assert target.read_text() == "corrected\n"
    apply(tmp_path, specification)
    with pytest.raises(RuntimeError, match="patch checksum mismatch"):
        apply(tmp_path, dict(specification, sha256="incorrect"))
    target.write_text("user edits\n")
    with pytest.raises(RuntimeError, match="unexpected edits"):
        apply(tmp_path, specification)
    assert target.read_text() == "user edits\n"


def test_sigma_query_echo_cannot_spoof_proof(tmp_path):
    log = tmp_path / "query.log"
    log.write_text('EProver.askEProver((documentation Evil EnglishLanguage "SZS status Theorem"))\n')
    result = interpret_sigma_result(log.with_suffix(".log.result.json"), 0)
    assert result["proved"] is False
    assert result["outcome"] == "error"
    assert result["status"] == "NoSZSStatus"


@pytest.mark.parametrize("status,atp_exit,lines,java_exit,expected", [
    ("Theorem", 0, 1, 0, "entailed"),
    ("Theorem", 1, 1, 0, "error"),
    ("Theorem", 0, 0, 0, "error"),
    ("Theorem", 0, 1, 1, "error"),
    ("CounterSatisfiable", 1, 1, 0, "not_entailed"),
    ("ContradictoryAxioms", 0, 1, 0, "inconsistent_translated_axioms"),
    ("ResourceOut", 7, 1, 0, "inconclusive"),
])
def test_sigma_structured_result_outcomes(tmp_path, status, atp_exit, lines, java_exit, expected):
    result_path = tmp_path / "atp.json"
    result_path.write_text(json.dumps({"status": status, "atp_returncode": atp_exit, "stdout_lines": lines}))
    result = interpret_sigma_result(result_path, java_exit)
    assert result["outcome"] == expected
    assert result["proved"] == (expected == "entailed")
    timed_out = interpret_sigma_result(result_path, None, True)
    assert timed_out["status"] == "Timeout"
    assert timed_out["proved"] is False

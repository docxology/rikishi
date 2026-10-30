from __future__ import annotations

import hashlib
import json
from pathlib import Path
from uuid import uuid4

import pytest

from rikishi import runtime
from rikishi.runtime_artifacts import ArtifactError, expanded_problem, load_capture
from rikishi.runtime_diagnostics import diagnose, proof_premises
from rikishi.runtime_tptp import parse_tptp


@pytest.fixture
def family_output(native_workspace: Path) -> Path:
    directory = (native_workspace
                 / ("runtime-implementation-native-" + uuid4().hex))
    directory.mkdir()
    return directory


@pytest.mark.integration
@pytest.mark.parametrize("prover", ["e", "v"])
@pytest.mark.parametrize("goal,status", [("p", "Theorem"), ("q", "CounterSatisfiable")])
def test_direct_family_nested_capture_and_moved_replay(
    project_root: Path, tmp_path: Path, family_output: Path, prover: str, goal: str, status: str,
) -> None:
    inputs = tmp_path / "inputs"
    nested = inputs / "nested"
    nested.mkdir(parents=True)
    (inputs / "leaf.p").write_text("fof(decoy,axiom,q).\n")
    (nested / "leaf.p").write_text("fof(fact,axiom,\n p).\n")
    (nested / "outer.p").write_text("include('leaf.p').\n")
    problem = inputs / "problem.p"
    problem.write_text(f"include('nested/outer.p'). fof(goal,conjecture,{goal}).\n")
    result = runtime.prove(problem, project_root, 2, prover=prover, output=family_output / "direct")
    assert result["status"] == status
    assert result["prover"] == prover
    assert result["proved"] == (status == "Theorem")
    assert result["semantic_validation"] is False
    capture_path = Path(str(result["capture"]))
    capture = load_capture(capture_path)
    assert capture.prover == prover
    assert capture.problem.sha256 == hashlib.sha256(problem.read_bytes()).hexdigest()
    assert len(capture.includes) == 2
    frozen = expanded_problem(capture, capture_path.parent)
    assert "decoy" not in frozen
    inputs.rename(tmp_path / "moved-inputs")
    report = diagnose(capture_path, project_root, timeout=2, output=family_output / "diagnostic")
    assert report["status"] == status
    assert report["prover"] == prover
    assert report["minimality"] == "not_established"
    assert report["semantic_validation"] is False
    if status == "Theorem":
        assert report["premise_names"] == ["fact", "goal"]
        assert report["subset_status"] == "Theorem"
        subset = load_capture(family_output / "diagnostic/subset-check/capture.json")
        assert subset.prover == prover
        exported = (family_output / "diagnostic/proof-premises.p").read_text()
        assert [statement.text for statement in parse_tptp(exported)] == [
            statement.text for statement in parse_tptp(frozen)]
    else:
        assert report["premise_names"] == []
        assert report["subset_status"] == "not_run"
        assert not (family_output / "diagnostic/subset-check").exists()


def test_vampire_extractor_is_explicit_and_requires_one_matching_complete_block() -> None:
    leaf = "fof(a,axiom,p,file('/saved/problem.p',a))."
    block = "% SZS output start Proof for problem\n" + leaf + "\n% SZS output end Proof for problem\n"
    assert proof_premises(block) == []
    assert proof_premises(block, prover="v") == ["a"]
    for invalid in (leaf, block.split("% SZS output end")[0],
                    block.replace("end Proof for problem", "end Proof for different"),
                    block + block,
                    block.replace("end Proof", "end CNFRefutation")):
        assert proof_premises(invalid, prover="v") == []
    with pytest.raises(ValueError, match="prover"):
        proof_premises(block, prover="unknown")


@pytest.mark.integration
def test_direct_comparison_retains_identical_inputs(project_root: Path, tmp_path: Path,
                                                   family_output: Path) -> None:
    problem = tmp_path / "problem.p"
    problem.write_text("fof(fact,axiom,p). fof(goal,conjecture,p).\n")
    report = runtime.compare(problem, project_root, 2, output=family_output / "comparison")
    assert report["agreement"] is True
    assert report["outcome"] == "agreement"
    assert report["statuses"] == {"e": "Theorem", "v": "Theorem"}
    assert report["semantic_validation"] is False
    captures = [load_capture(family_output / f"comparison/{family}/capture.json")
                for family in ("e", "v")]
    assert captures[0].problem.sha256 == captures[1].problem.sha256
    assert json.loads((family_output / "comparison/comparison.json").read_text()) == report


@pytest.mark.integration
@pytest.mark.parametrize("prover", ["e", "v"])
@pytest.mark.parametrize("removed", [None, 0, 1, 2, 3])
def test_direct_family_saved_contradiction_and_all_deletions(
    project_root: Path, tmp_path: Path, family_output: Path, prover: str, removed: int | None,
) -> None:
    fixture = Path(__file__).parent / "fixtures/path-contradiction.p"
    problem = tmp_path / "subset.p"
    problem.write_text("\n".join(line for i, line in enumerate(fixture.read_text().splitlines())
                                 if i != removed) + "\n")
    result = runtime.prove(problem, project_root, 2, prover=prover, output=family_output / "direct")
    assert result["status"] == ("Unsatisfiable" if removed is None else "Satisfiable")
    assert not result["proved"]
    report = diagnose(Path(str(result["capture"])), project_root, timeout=2,
                      output=family_output / "diagnostic")
    assert report["premise_count"] == (4 if removed is None else 0)
    assert report["subset_status"] == ("Unsatisfiable" if removed is None else "not_run")


@pytest.mark.integration
@pytest.mark.parametrize("prover", ["e", "v"])
def test_direct_family_explosive_background_is_no_query_proof(
    project_root: Path, tmp_path: Path, family_output: Path, prover: str,
) -> None:
    problem = tmp_path / "explosion.p"
    problem.write_text("fof(positive,axiom,p). fof(negative,axiom,~p). fof(goal,conjecture,q).\n")
    result = runtime.prove(problem, project_root, 2, prover=prover, output=family_output / "direct")
    assert result["status"] == "ContradictoryAxioms"
    assert not result["proved"]
    report = diagnose(Path(str(result["capture"])), project_root, timeout=2,
                      output=family_output / "diagnostic")
    assert report["premise_names"] == ["negative", "positive"]
    assert report["subset_status"] == "Unsatisfiable"
    assert report["minimality"] == "not_established"


@pytest.mark.integration
def test_direct_output_is_fresh_local_and_has_no_symlink_components(
    project_root: Path, tmp_path: Path, family_output: Path,
) -> None:
    problem = tmp_path / "problem.p"
    problem.write_text("fof(goal,conjecture,p).\n")
    with pytest.raises(ValueError, match="inside the repository"):
        runtime.prove(problem, project_root, output=tmp_path / "outside")
    occupied = family_output / "occupied"
    occupied.mkdir()
    (occupied / "preserved").write_text("existing evidence")
    with pytest.raises(FileExistsError):
        runtime.prove(problem, project_root, output=occupied)
    linked = family_output / "linked"
    linked.symlink_to(occupied, target_is_directory=True)
    with pytest.raises(ArtifactError, match="symlink"):
        runtime.prove(problem, project_root, output=linked / "child")
    assert (occupied / "preserved").read_text() == "existing evidence"
    assert not (occupied / "child").exists()


@pytest.mark.parametrize("prover", ["unknown", "Vampire", "E"])
def test_unknown_direct_family_is_rejected(tmp_path: Path, prover: str) -> None:
    problem = tmp_path / "problem.p"
    problem.write_text("fof(goal,conjecture,p).\n")
    with pytest.raises(ValueError, match="prover"):
        runtime.prove(problem, tmp_path, prover=prover)
    assert not (tmp_path / ".rikishi").exists()


def test_vampire_missing_runtime_is_explicit(tmp_path: Path) -> None:
    problem = tmp_path / "problem.p"
    problem.write_text("fof(goal,conjecture,p).\n")
    with pytest.raises(FileNotFoundError, match="Vampire"):
        runtime.prove(problem, tmp_path, prover="v")


@pytest.mark.parametrize("timeout", [0, 301])
def test_comparison_timeout_is_checked_before_output(tmp_path: Path, timeout: int) -> None:
    with pytest.raises(ValueError, match="timeout"):
        runtime.compare(tmp_path / "missing", tmp_path, timeout)
    assert list(tmp_path.iterdir()) == []

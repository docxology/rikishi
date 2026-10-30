from pathlib import Path
from uuid import uuid4

import pytest

from rikishi.runtime import prove
from rikishi.runtime_artifacts import expanded_problem, load_capture
from rikishi.runtime_diagnostics import diagnose


@pytest.mark.integration
@pytest.mark.parametrize("layout", ["same_line", "multiline", "comments"])
def test_native_replay_freezes_all_include_layouts(project_root, tmp_path, layout):
    background = tmp_path / "background.p"
    background.write_text("fof(fact,axiom,p).\n")
    problem = tmp_path / "query.p"
    include = {
        "same_line": "include('background.p').",
        "multiline": "include\n(\n'background.p'\n)\n.",
        "comments": "include ( /* path */ 'background.p' /* end */ ).",
    }[layout]
    problem.write_text("fof(goal,conjecture,p). " + include + "\n")
    first = prove(problem, project_root, timeout=5)
    assert first["status"] == "Theorem"
    capture_path = Path(first["capture"])
    capture = load_capture(capture_path)
    assert len(capture.includes) == 1
    background.write_text("fof(fact,axiom,q).\n")
    changed = prove(problem, project_root, timeout=5)
    assert changed["status"] == "CounterSatisfiable"
    replay = tmp_path / "replay.p"
    replay.write_text(expanded_problem(capture, capture_path.parent))
    assert prove(replay, project_root, timeout=5)["status"] == "Theorem"


@pytest.mark.integration
@pytest.mark.parametrize("layout", ["multiline", "same_line", "indented"])
def test_native_export_preserves_complete_proof_premises(project_root, tmp_path, layout):
    texts = {
        "multiline": "fof(fact,axiom,\n p).\nfof(goal,conjecture,\n p).\n",
        "same_line": "fof(fact,axiom,p). fof(goal,conjecture,p).\n",
        "indented": "  fof(fact,axiom,p).\n  fof(goal,conjecture,p).\n",
    }
    problem = tmp_path / "premises.p"
    problem.write_text(texts[layout])
    first = prove(problem, project_root, timeout=5)
    output = project_root / ".rikishi/results" / (uuid4().hex + "-premise-export")
    diagnostic = diagnose(Path(first["capture"]), project_root, timeout=5, output=output)
    assert diagnostic["status"] == "Theorem"
    assert diagnostic["subset_status"] == "Theorem"
    assert diagnostic["premise_count"] == 2
    subset = Path(diagnostic["premises"])
    assert prove(subset, project_root, timeout=5)["status"] == "Theorem"

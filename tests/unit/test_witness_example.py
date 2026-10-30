import json
import subprocess
import sys
from pathlib import Path


def test_mixed_history_example_runs_without_native_workspaces(project_root: Path,
                                                             tmp_path: Path) -> None:
    # Given a fresh cwd with no sources, renderer, Lean or solver workspace.
    # When the documented Python example runs as an actual subprocess.
    result = subprocess.run([sys.executable, str(project_root / "examples/witness_sequences.py")],
                            cwd=tmp_path, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    # Then its independently calculated results distinguish the two normalizations.
    assert data["observations"] == [True, False]
    assert data["models"]["uniform-prior"]["evidence"] == "3/16"
    assert data["models"]["uniform-prior"]["posterior"] == ["1/2", "1/2"]
    assert data["models"]["biased-prior"]["evidence"] == "5/24"
    assert data["models"]["biased-prior"]["posterior"] == ["2/5", "3/5"]
    assert data["model_prior"] == ["1/2", "1/2"]
    assert data["posterior_model_weights"] == ["9/19", "10/19"]
    assert data["model_averaged_next_true"] == "11/19"
    assert list(tmp_path.iterdir()) == []

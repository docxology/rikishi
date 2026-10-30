import json
import math
import subprocess
import sys

import pytest

from rikishi.cli import main


@pytest.fixture
def root(tmp_path):
    source = tmp_path / ".rikishi/upstream/sumo"
    source.mkdir(parents=True)
    (source / "Merge.kif").write_text("(subclass Human Animal)\n(instance Ada Human)")
    assert main(["--root", str(tmp_path), "index"]) == 0
    return tmp_path


@pytest.mark.parametrize(
    "command",
    [
        ["stats"],
        ["verify-source"],
        ["metrics"],
        ["search", "Human"],
        ["term", "Human"],
        ["graph", "Human"],
        ["fep-demo"],
        ["report"],
    ],
)
def test_real_cli_commands(root, capsys, command):
    capsys.readouterr()
    assert main(["--root", str(root), *command]) == 0
    assert json.loads(capsys.readouterr().out)


def test_cli_negative_controls(root, capsys):
    assert main(["--root", str(root), "term", "NoSuchTerm"]) == 1
    assert "KeyError" in capsys.readouterr().err
    assert main(["--root", str(root), "search", "Human", "--limit", "0"]) == 1
    assert main(["--root", str(root), "dashboard", "--port", "0"]) == 1
    (root / ".rikishi/upstream/sumo/Merge.kif").write_text("(subclass Human Entity)")
    assert main(["--root", str(root), "verify-source"]) == 1
    assert json.loads(capsys.readouterr().out)["modified"] == ["Merge.kif"]
    (root / ".rikishi/upstream/sumo/broken.kif").write_text("(")
    assert main(["--root", str(root), "index"]) == 1


def test_actual_module_entrypoint_and_missing_database(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "rikishi", "--root", str(tmp_path), "stats"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert json.loads(result.stderr)["error"] == "FileNotFoundError"
    help_result = subprocess.run(
        [sys.executable, "-m", "rikishi", "--help"], capture_output=True, text=True, check=False
    )
    assert help_result.returncode == 0
    assert "bootstrap" in help_result.stdout


def test_relation_filter_and_lean_verifier_errors(root, capsys):
    capsys.readouterr()
    assert main(["--root", str(root), "graph", "Human", "--relation", "subclass"]) == 0
    graph = json.loads(capsys.readouterr().out)
    assert graph["total_edges"] == graph["returned_edges"] == 1
    assert {edge["relation"] for edge in graph["edges"]} == {"subclass"}
    assert main(["--root", str(root), "fep-verify", "--timeout", "0"]) == 1
    assert "compiler timeout" in capsys.readouterr().err


@pytest.mark.parametrize("logarithmic", [False, True])
def test_explicit_model_evaluation_uses_real_cli_and_json(tmp_path, logarithmic):
    path = tmp_path / "model.json"
    document = (
        {"log_prior": [math.log(0.5)] * 2, "log_likelihood": [-1000.0, -1001.0]}
        if logarithmic else {"prior": [0.5, 0.5], "likelihood": [0.8, 0.2]}
    )
    document["posterior"] = [0.5, 0.5]
    path.write_text(json.dumps(document))
    command = [sys.executable, "-m", "rikishi", "fep-evaluate", str(path)]
    if logarithmic:
        command.append("--logarithmic")
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["free_energy"] == pytest.approx(1000.5 if logarithmic else math.log(2.5))
    if logarithmic:
        assert payload["evidence"] is None
    document["posterior"] = [True, False]
    path.write_text(json.dumps(document))
    invalid = subprocess.run(command, capture_output=True, text=True, check=False)
    assert invalid.returncode == 1
    assert json.loads(invalid.stderr)["error"] == "ValidationError"

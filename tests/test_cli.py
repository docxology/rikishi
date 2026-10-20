import json
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

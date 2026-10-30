import json
import subprocess
import sys

from rikishi.active_inference import demo
from rikishi.cli import main


def test_active_demo_without_index_or_native_tools(tmp_path, capsys):
    assert main(["--root", str(tmp_path), "active-demo"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report == demo()
    assert report["minimizers"] == ["sense"]
    assert report["actions"][0]["outcomes"] == report["actions"][1]["outcomes"]
    assert list(tmp_path.iterdir()) == []


def test_actual_active_demo_module_entrypoint(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "rikishi", "--root", str(tmp_path), "active-demo"],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == demo()
    assert result.stderr == ""

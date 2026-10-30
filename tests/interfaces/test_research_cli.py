import json
import subprocess
import sys
from hashlib import sha256
from uuid import uuid4

import pytest


@pytest.mark.integration
def test_research_cli_runs_replays_and_rejects_changed_digest(
    project_root, native_workspace, portable_inputs,
):
    output = native_workspace / ("research-cli-" + uuid4().hex)
    command = [sys.executable, "-m", "rikishi", "--root", str(project_root)]
    produce = [*command, "research-run", str(output),
               "--workbook", str(portable_inputs.workbook_path)]
    run = subprocess.run(produce,
                         capture_output=True, text=True, timeout=90, check=False)
    assert run.returncode == 0, run.stderr
    observed = json.loads(run.stdout)
    assert observed["summary"]["campaign_complete"]
    report = output / "alignment-report.json"
    digest = sha256(report.read_bytes()).hexdigest()
    replay = subprocess.run([*command, "research-verify", str(report), "--sha256", digest],
                            capture_output=True, text=True, timeout=30, check=False)
    assert replay.returncode == 0, replay.stderr
    assert json.loads(replay.stdout) == observed
    rejected = subprocess.run([*command, "research-verify", str(report), "--sha256", "0" * 64],
                              capture_output=True, text=True, timeout=30, check=False)
    assert rejected.returncode == 1
    assert json.loads(rejected.stderr)["message"] == "Outer report binding mismatch"
    occupied = subprocess.run(produce,
                              capture_output=True, text=True, timeout=30, check=False)
    assert occupied.returncode == 1
    assert json.loads(occupied.stderr)["error"] == "FileExistsError"
    assert sha256(report.read_bytes()).hexdigest() == digest


def test_cache_cli_rejects_timeout_before_output(project_root, tmp_path):
    output = tmp_path / "not-created"
    result = subprocess.run([sys.executable, "-m", "rikishi", "--root", str(project_root),
                             "cache-diagnostic", str(output), "--timeout", "0"],
                            capture_output=True, text=True, timeout=20, check=False)
    assert result.returncode == 1
    assert "timeout" in json.loads(result.stderr)["message"]
    assert not output.exists()

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pytest

ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.integration


@pytest.mark.parametrize("prover", ["e", "v", "compare"])
def test_native_prover_cli_preserves_captures_and_rejects_occupied_output(prover, native_workspace):
    work = native_workspace / ("cli-prover-" + uuid4().hex)
    work.mkdir()
    problem = work / "problem.p"
    problem.write_text("fof(fact,axiom,p).\nfof(goal,conjecture,p).\n")
    output = work / "capture"
    command = [sys.executable, "-m", "rikishi", "--root", str(ROOT)]
    if prover == "compare":
        command.extend(["compare-provers", str(problem)])
    else:
        command.extend(["prove", str(problem), "--prover", prover])
    command.extend(["--timeout", "2", "--output", str(output)])
    result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=30)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    if prover == "compare":
        assert payload["statuses"] == {"e": "Theorem", "v": "Theorem"}
        assert payload["same_input"] is True
        assert payload["semantic_validation"] is False
        captures = [Path(p) for p in payload["captures"].values()]
    else:
        assert payload["status"] == "Theorem"
        assert payload["proved"] is True
        assert payload["prover"] == prover
        captures = [output / "capture.json"]
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in captures}
    rejected = subprocess.run(command, capture_output=True, text=True, check=False, timeout=30)
    assert rejected.returncode == 1
    assert json.loads(rejected.stderr)["error"] in {"ValueError", "FileExistsError"}
    assert {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in captures} == before

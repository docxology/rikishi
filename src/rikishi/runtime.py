"""Explicit local runtime inspection and bounded execution of the real E prover."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


def status(root: Path) -> dict[str, object]:
    """Inspect installed artifacts and upstream revisions without modifying them."""
    root = root.resolve()
    lock = json.loads((root / "config/sumo.lock.json").read_text())
    repositories: dict[str, object] = {}
    for name, specification in lock["repositories"].items():
        checkout = root / ".rikishi/upstream" / name
        revision = None
        changes = None
        if (checkout / ".git").exists():
            result = subprocess.run(
                ["git", "-C", str(checkout), "rev-parse", "HEAD"],
                capture_output=True, text=True, check=True, timeout=10,
            )
            revision = result.stdout.strip()
            changes = subprocess.run(
                ["git", "-C", str(checkout), "status", "--porcelain"],
                capture_output=True, text=True, check=True, timeout=10,
            ).stdout.splitlines()
        repositories[name] = {"commit": revision, "pinned": revision == specification["commit"],
                              "changes": changes}
    return {
        "repositories": repositories,
        "eprover": (root / ".rikishi/upstream/eprover/PROVER/eprover").is_file(),
        "sigma_jar": (root / ".rikishi/upstream/sigmakee/build/sigmakee.jar").is_file(),
        "sumo_files": len(list((root / ".rikishi/upstream/sumo").rglob("*.kif"))),
    }


def prove(problem: Path, root: Path, timeout: int = 10) -> dict[str, object]:
    """Run E on a TPTP problem; report SZS outcomes without equating failure to falsity."""
    if not 1 <= timeout <= 300:
        raise ValueError("timeout must be between 1 and 300 seconds")
    problem = problem.resolve(strict=True)
    binary = root.resolve() / ".rikishi/upstream/eprover/PROVER/eprover"
    if not binary.is_file():
        raise FileNotFoundError("E prover is not installed; run scripts/bootstrap-sumo.sh")
    command = [str(binary), "--auto", "--tstp-format", "--proof-object",
               f"--cpu-limit={timeout}", str(problem)]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout + 5, check=False)
    except subprocess.TimeoutExpired as error:
        raise TimeoutError(f"E exceeded its {timeout + 5} second wall-clock bound") from error
    match = re.search(r"SZS status (\w+)", result.stdout)
    if match is None:
        raise RuntimeError(f"E returned no SZS status (exit {result.returncode}): {result.stderr}")
    return {"status": match.group(1), "proved": match.group(1) == "Theorem",
            "returncode": result.returncode, "stdout": result.stdout,
            "stderr": result.stderr, "problem": str(problem), "command": command}


def bootstrap(root: Path) -> dict[str, object]:
    """Run the explicit bootstrap; installation errors propagate to the caller."""
    subprocess.run(["bash", str(root.resolve() / "scripts/bootstrap-sumo.sh")],
                   check=True, timeout=1800, stdout=sys.stderr)
    return status(root)


def interpret_sigma_result(path: Path, returncode: int | None, timed_out: bool = False) -> dict[str, object]:
    result = json.loads(path.read_text()) if path.is_file() else {}
    status = "Timeout" if timed_out else result.get("status", "NoSZSStatus")
    outcome = {"Theorem": "entailed", "CounterSatisfiable": "not_entailed",
               "ContradictoryAxioms": "inconsistent_translated_axioms"}.get(status, "inconclusive")
    if returncode not in (0, None) or status == "NoSZSStatus":
        outcome = "error"
    if outcome == "entailed" and (result.get("atp_returncode") != 0 or not result.get("stdout_lines")):
        outcome = "error"
    return {"status": status, "outcome": outcome, "proved": outcome == "entailed",
            "atp_returncode": result.get("atp_returncode"),
            "consistency": "contradictory_translated_axioms_detected" if status == "ContradictoryAxioms" else "not_established"}

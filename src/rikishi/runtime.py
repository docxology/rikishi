"""Explicit local runtime inspection and bounded native E/V execution."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import uuid
from pathlib import Path

from rikishi.runtime_artifacts import (
    SZS_STATUS,
    ArtifactError,
    Capture,
    ProverKind,
    checked_source_path,
    load_capture,
    read_regular,
    verified_bytes,
)
from rikishi.runtime_capture import capture_prover
from rikishi.runtime_results import ExpectedATPInvocation, verify_invocation

__all__ = ["bootstrap", "compare", "prove", "status"]


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


def prover_executable(root: Path, prover: ProverKind) -> Path:
    match prover:
        case "e":
            relative = ".rikishi/upstream/eprover/PROVER/eprover"
            name = "E prover"
        case "v":
            relative = ".rikishi/runtime/vampire"
            name = "Vampire"
        case _:
            raise ValueError("prover must be 'e' or 'v'")
    binary = root.resolve() / relative
    if not binary.is_file():
        raise FileNotFoundError(f"{name} is not installed; run scripts/bootstrap-sumo.sh")
    return binary


def _fresh_directory(root: Path, output: Path | None, prefix: str) -> Path:
    directory = output if output is not None else root / ".rikishi/results" / (prefix + uuid.uuid4().hex)
    directory = directory.absolute()
    if not directory.resolve().is_relative_to(root.resolve()):
        raise ValueError("runtime output must be inside the repository")
    parent = directory
    while not parent.exists() and not parent.is_symlink():
        parent = parent.parent
    checked_source_path(parent)
    directory.mkdir(parents=True, exist_ok=False)
    return checked_source_path(directory)


def prove(
    problem: Path, root: Path, timeout: int = 10, *, prover: ProverKind = "e",
    output: Path | None = None,
) -> dict[str, object]:
    """Run one bound native family; output must be a fresh repository-local directory."""
    if not 1 <= timeout <= 300:
        raise ValueError("timeout must be between 1 and 300 seconds")
    problem = checked_source_path(problem)
    problem_hash = hashlib.sha256(read_regular(problem)).hexdigest()
    binary = prover_executable(root, prover)
    flags = (["--auto", "--tstp-format", "--proof-object", f"--cpu-limit={timeout}"]
             if prover == "e" else ["--proof", "tptp", "--mode", "casc", "-t", str(timeout)])
    command = [str(binary), *flags, str(problem)]
    invocation_id = uuid.uuid4().hex
    provenance = {"prover_sha256": hashlib.sha256(read_regular(binary)).hexdigest()}
    expected = ExpectedATPInvocation(invocation_id, binary, provenance, problem_hash, prover=prover)
    directory = _fresh_directory(root.resolve(), output, prover + "-")
    capture_prover(command, directory, invocation_id=invocation_id,
                   provenance=provenance, timeout=timeout + 5, prover=prover)
    capture = load_capture(directory / "capture.json", invocation_id)
    verify_invocation(capture, expected)
    stdout = verified_bytes(capture.stdout, directory).decode("utf-8")
    stderr = verified_bytes(capture.stderr, directory).decode("utf-8")
    if capture.timed_out:
        raise TimeoutError(f"{prover} exceeded its {timeout + 5} second wall-clock bound; evidence: {directory}")
    statuses = set(SZS_STATUS.findall(stdout))
    if len(statuses) != 1:
        raise RuntimeError(f"{prover} returned no SZS status or conflicting statuses (exit {capture.returncode}): {stderr}")
    outcome = statuses.pop()
    if outcome in {"Theorem", "Unsatisfiable", "ContradictoryAxioms"} and capture.returncode != 0:
        raise RuntimeError(f"{prover} proof status disagrees with exit {capture.returncode}; evidence: {directory}")
    if outcome in {"Satisfiable", "CounterSatisfiable"} and capture.returncode not in {0, 1}:
        raise RuntimeError(f"{prover} model status disagrees with exit {capture.returncode}; evidence: {directory}")
    return {"status": outcome, "proved": outcome == "Theorem",
            "returncode": capture.returncode, "stdout": stdout,
            "stderr": stderr, "problem": str(problem), "command": command,
            "capture": str(directory / "capture.json"), "semantic_validation": False,
            "prover": prover}


def compare(
    problem: Path, root: Path, timeout: int = 10, *, output: Path | None = None,
) -> dict[str, object]:
    """Compare statuses only after both captures retain identical problem/include bytes."""
    if not 1 <= timeout <= 300:
        raise ValueError("timeout must be between 1 and 300 seconds")
    directory = _fresh_directory(root.resolve(), output, "compare-")
    statuses: dict[str, str] = {}
    captures: dict[str, str] = {}
    observed: dict[str, Capture] = {}
    identities: list[tuple[str, list[tuple[str, str, int]]]] = []
    for family in ("e", "v"):
        result = prove(problem, root, timeout, prover=family, output=directory / family)
        path = directory / family / "capture.json"
        capture = load_capture(path)
        observed[family] = capture
        statuses[family] = str(result["status"])
        captures[family] = str(path)
        identities.append((capture.problem.sha256,
                           sorted((item.source, item.sha256, item.size) for item in capture.includes)))
    for family, expected_capture in observed.items():
        if load_capture(Path(captures[family])) != expected_capture:
            raise ArtifactError("comparison evidence changed during execution")
    if identities[0] != identities[1]:
        raise ArtifactError("comparison captures do not retain identical problem/include bytes")
    conclusive = {"Theorem", "CounterSatisfiable", "Satisfiable", "Unsatisfiable", "ContradictoryAxioms"}
    agreement = statuses["e"] == statuses["v"] if set(statuses.values()) <= conclusive else None
    report: dict[str, object] = {
        "statuses": statuses, "agreement": agreement,
        "outcome": "inconclusive" if agreement is None else "agreement" if agreement else "disagreement",
        "captures": captures, "problem_sha256": identities[0][0],
        "same_input": True, "semantic_validation": False,
    }
    (directory / "comparison.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def bootstrap(root: Path) -> dict[str, object]:
    """Run the explicit bootstrap; installation errors propagate to the caller."""
    subprocess.run(["bash", str(root.resolve() / "scripts/bootstrap-sumo.sh")],
                   check=True, timeout=1800, stdout=sys.stderr)
    return status(root)

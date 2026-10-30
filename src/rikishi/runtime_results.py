import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from rikishi.runtime_artifacts import (
    SZS_STATUS,
    ArtifactError,
    Capture,
    ProverKind,
    expanded_problem,
    load_capture,
    normalized_source_identity,
    read_regular,
    verified_bytes,
)


@dataclass(frozen=True, slots=True)
class ExpectedATPInvocation:
    invocation_id: str
    executable: Path
    provenance: Mapping[str, str]
    problem_sha256: str | None = None
    prover: ProverKind = "e"


def verify_invocation(capture: Capture, expected: ExpectedATPInvocation) -> None:
    executable = expected.executable.resolve(strict=True)
    executable_hash = hashlib.sha256(read_regular(executable)).hexdigest()
    if (capture.invocation_id != expected.invocation_id
            or capture.prover != expected.prover
            or not Path(capture.command[0]).is_absolute()
            or Path(capture.command[0]).resolve() != executable
            or expected.provenance.get("prover_sha256") != executable_hash
            or (expected.problem_sha256 is None and not expected.provenance.get("query_sha256"))
            or capture.provenance != dict(expected.provenance)
            or not Path(capture.command[-1]).is_absolute()
            or normalized_source_identity(capture.command[-1]) != capture.source_problem
            or (expected.problem_sha256 is not None
                and capture.problem.sha256 != expected.problem_sha256)):
        raise ArtifactError("capture does not match the trusted executable, input, or source bindings")


class ATPResult(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")
    status: str = Field(pattern=r"^[A-Za-z]+$")
    atp_returncode: int
    stdout_lines: int = Field(ge=0)
    invocation_id: str = Field(min_length=1)
    capture: str


class SigmaOutcome(TypedDict):
    status: str
    outcome: str
    proved: bool
    atp_returncode: int | None
    consistency: str
    validation_scope: str
    semantic_validation: bool
    evidence: str


def interpret_sigma_result(
    path: Path, returncode: int | None, timed_out: bool = False, *, invocation_id: str | None = None,
    expected: ExpectedATPInvocation | None = None,
) -> SigmaOutcome:
    result = None
    status = "Timeout" if timed_out else "NoSZSStatus"
    evidence = "not_verified"
    prover_timed_out = False
    if not timed_out and path.exists():
        try:
            result = ATPResult.model_validate_json(read_regular(path, limit=64 * 1024))
            capture_path = path.parent / result.capture
            if (Path(result.capture).is_absolute() or ".." in Path(result.capture).parts
                    or len(Path(result.capture).parts) != 2 or capture_path.parent.is_symlink()):
                raise ArtifactError("capture path must stay inside its invocation directory")
            capture = load_capture(capture_path, result.invocation_id)
            if expected is not None:
                verify_invocation(capture, expected)
            expanded_problem(capture, capture_path.parent)
            stdout = verified_bytes(capture.stdout, capture_path.parent).decode("utf-8")
            statuses = set(SZS_STATUS.findall(stdout))
            expected_exit = capture.returncode if capture.returncode >= 0 else 128 - capture.returncode
            prover_timed_out = capture.timed_out and capture.returncode < 0
            if (len(stdout.splitlines()) != result.stdout_lines or expected_exit != result.atp_returncode
                    or (capture.timed_out and not prover_timed_out)
                    or (not prover_timed_out and statuses != {result.status})):
                raise ArtifactError("ATP result does not match saved process evidence")
        except (ValidationError, ArtifactError, UnicodeError, OSError):
            result = None
            status = "InvalidATPResult"
        else:
            status = "Timeout" if prover_timed_out else result.status
            evidence = "sha256_verified" if expected is not None else "sha256_verified_unbound"
    outcome = {"Theorem": "entailed", "CounterSatisfiable": "not_entailed", "NoSZSStatus": "error",
               "ContradictoryAxioms": "inconsistent_translated_axioms"}.get(status, "inconclusive")
    if not timed_out and (returncode != 0 or result is None):
        outcome = "error"
    if result is not None:
        expected_exits = {"Theorem": {0}, "CounterSatisfiable": {0, 1}, "ContradictoryAxioms": {0}}
        if ((invocation_id is not None and result.invocation_id != invocation_id)
                or (not result.stdout_lines and not prover_timed_out)):
            outcome = "error"
        if status in expected_exits and result.atp_returncode not in expected_exits[status]:
            outcome = "error"
        if expected is None and outcome not in {"error", "inconclusive"}:
            outcome = "unverified"
    return {"status": status, "outcome": outcome, "proved": outcome == "entailed",
            "atp_returncode": result.atp_returncode if result else None,
            "consistency": "contradictory_translated_axioms_detected"
            if outcome == "inconsistent_translated_axioms" else "not_established",
            "validation_scope": "translated_query_only", "semantic_validation": False,
            "evidence": evidence}

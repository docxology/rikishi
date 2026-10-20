from pathlib import Path
from typing import TypedDict

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class ATPResult(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")
    status: str = Field(pattern=r"^[A-Za-z]+$")
    atp_returncode: int
    stdout_lines: int = Field(ge=0)
    stderr: list[str] = Field(default_factory=list)
    invocation_id: str | None = None


class SigmaOutcome(TypedDict):
    status: str
    outcome: str
    proved: bool
    atp_returncode: int | None
    consistency: str


def interpret_sigma_result(
    path: Path, returncode: int | None, timed_out: bool = False, *, invocation_id: str | None = None,
) -> SigmaOutcome:
    result = None
    status = "Timeout" if timed_out else "NoSZSStatus"
    if not timed_out and path.is_file():
        try:
            result = ATPResult.model_validate_json(path.read_text())
        except ValidationError:
            status = "InvalidATPResult"
        else:
            status = result.status
    outcome = {"Theorem": "entailed", "CounterSatisfiable": "not_entailed", "NoSZSStatus": "error",
               "ContradictoryAxioms": "inconsistent_translated_axioms"}.get(status, "inconclusive")
    if not timed_out and (returncode != 0 or result is None):
        outcome = "error"
    if result is not None:
        expected_exits = {"Theorem": {0}, "CounterSatisfiable": {0, 1}, "ContradictoryAxioms": {0}}
        if (invocation_id is not None and result.invocation_id != invocation_id) or not result.stdout_lines:
            outcome = "error"
        if status in expected_exits and result.atp_returncode not in expected_exits[status]:
            outcome = "error"
    return {"status": status, "outcome": outcome, "proved": outcome == "entailed",
            "atp_returncode": result.atp_returncode if result else None,
            "consistency": "contradictory_translated_axioms_detected"
            if status == "ContradictoryAxioms" and outcome != "error" else "not_established"}

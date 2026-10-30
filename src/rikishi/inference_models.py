from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from rikishi.runtime_artifacts import ProverKind

type Polarity = Literal["Theorem", "CounterSatisfiable", "Satisfiable", "Unsatisfiable"]
type CaseKind = Literal["background", "positive", "negative", "removed-premise", "refutation"]


class InferenceError(ValueError):
    pass


class Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class Selection(Frozen):
    line: int = Field(ge=1)
    predicate_bindings: dict[str, str] = Field(default_factory=dict)


class Scenario(Frozen):
    id: str = Field(pattern=r"^[a-z][a-z0-9-]*$")
    title: str
    category: str
    selections: list[Selection]
    assumptions: list[str]
    query: str
    negative_query: str
    removed_selection: int | None = None
    removed_assumption: int | None = None


class InferenceStudy(Frozen):
    schema_version: Literal[1]
    study_id: str
    source_path: Literal[".rikishi/upstream/sumo/Merge.kif"]
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_commit: str
    lock_sha256: str
    source_url: str
    semantic_scope: str
    supported_syntax: list[str]
    scenarios: list[Scenario]


class SourceClaim(Frozen):
    source_path: str
    line: int
    end_line: int
    raw_kif: str
    sha256: str


class InferenceCase(Frozen):
    id: str
    group: str
    kind: CaseKind
    expected: Polarity
    problem: str


class CaseOutcome(Frozen):
    id: str
    group: str
    kind: CaseKind
    prover: ProverKind
    expected: Polarity
    observed: str
    matched: bool
    capture: str
    capture_sha256: str
    problem_sha256: str
    invocation_id: str
    prover_sha256: str


class InferenceSummary(Frozen):
    scenarios: int
    total: int
    matched: int
    mismatched: int
    unresolved: int
    passed: bool


class InferenceReport(Frozen):
    schema_version: Literal[1] = 1
    study_id: str
    study_sha256: str
    source_claims: list[SourceClaim]
    implementation: dict[str, str]
    binary_sha256: dict[str, str]
    lock_sha256: str
    provers: list[ProverKind]
    timeout_seconds: int = Field(ge=1, le=300)
    cases: list[CaseOutcome]
    summary: InferenceSummary
    replay_boundary: str

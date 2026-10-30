"""Typed custody boundary for the finite FEP–SUMO witness experiment."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from rikishi.inference_models import CaseOutcome, Frozen, Scenario, SourceClaim
from rikishi.runtime_artifacts import ProverKind


class BridgeError(ValueError):
    """A bridge input or retained obligation does not satisfy its contract."""


class WitnessEntities(Frozen):
    model: str = Field(pattern=r"^Bridge[A-Za-z0-9]+$")
    representation: str = Field(pattern=r"^Bridge[A-Za-z0-9]+$")
    calculation: str = Field(pattern=r"^Bridge[A-Za-z0-9]+$")
    result: str = Field(pattern=r"^Bridge[A-Za-z0-9]+$")
    agent: str = Field(pattern=r"^Bridge[A-Za-z0-9]+$")


class FiniteWitness(Frozen):
    id: str = Field(pattern=r"^[a-z][a-z0-9-]*$")
    namespace: str = Field(pattern=r"^[A-Z][A-Za-z0-9]*$")
    prior: tuple[str, str]
    likelihood: tuple[str, str]
    candidate: tuple[str, str]
    observed: Literal[True] = True
    entities: WitnessEntities


class BridgeScenario(Scenario):
    witness_id: str
    role: Literal["model", "representation", "calculation", "result"]


class BridgeStudy(Frozen):
    schema_version: Literal[1] = 1
    study_id: str
    source_path: Literal[".rikishi/upstream/sumo/Merge.kif"]
    source_sha256: str
    source_commit: str
    lock_sha256: str
    dependency_lock_sha256: str
    formal_revision: str
    formal_sources: dict[str, str]
    decimal_precision: int = Field(ge=40, le=200)
    tolerance: float = Field(gt=0, le=1e-10)
    witnesses: tuple[FiniteWitness, ...]
    scenarios: tuple[BridgeScenario, ...]
    local_rules: tuple[str, ...]
    context_lines: tuple[int, ...]
    semantic_scope: str


class EnergyValues(Frozen):
    evidence: float
    surprise: float
    free_energy: float
    kl_to_posterior: float
    exact_posterior: tuple[float, float]
    identity_residual: float


class DecimalValues(Frozen):
    evidence: str
    surprise: str
    free_energy: str
    kl_to_posterior: str
    exact_posterior: tuple[str, str]
    identity_residual: str


class NumericalWitness(Frozen):
    witness_id: str
    input: FiniteWitness
    evidence: str
    exact_posterior: tuple[str, str]
    result: EnergyValues
    reference: DecimalValues
    max_reference_error: float
    reconstruction_residuals: tuple[str, str]
    tolerance: float
    passed: bool


class LeanCommand(Frozen):
    command: tuple[str, ...]
    returncode: int
    timeout_seconds: int = Field(ge=1, le=600)
    elapsed_seconds: float = Field(ge=0, allow_inf_nan=False)
    timed_out: Literal[False] = False
    log: str
    log_sha256: str


class LeanControl(Frozen):
    id: str
    source: str
    source_sha256: str
    command: LeanCommand
    rejected: bool


class LeanEnvironment(Frozen):
    id: str
    source: str
    source_sha256: str
    command: LeanCommand
    declarations: tuple[str, ...]
    declaration_axioms: str


class LeanEvidence(Frozen):
    revision: str
    source: str
    source_sha256: str
    declarations: tuple[str, ...]
    declaration_axioms: str
    commands: tuple[LeanCommand, ...]
    controls: tuple[LeanControl, ...]
    environments: tuple[LeanEnvironment, ...]
    artifacts: dict[str, str]
    base_receipt_sha256: str
    base_timeout_seconds: int = Field(ge=1, le=600)
    base_elapsed_seconds: float = Field(ge=0, allow_inf_nan=False)
    compiler_sha256: str
    scope: str


class BridgeSummary(Frozen):
    witnesses: int
    scenarios: int
    numerical_passed: int
    lean_declarations: int
    lean_controls: int
    lean_controls_rejected: int
    total: int
    matched: int
    mismatched: int
    unresolved: int
    backgrounds_satisfiable: bool
    passed: bool


class BridgeReport(Frozen):
    schema_version: Literal[1] = 1
    study_id: str
    study_sha256: str
    witnesses: tuple[FiniteWitness, ...]
    scenarios: tuple[BridgeScenario, ...]
    source_claims: tuple[SourceClaim, ...]
    extension_sha256: str
    numerical: tuple[NumericalWitness, ...]
    lean: LeanEvidence
    implementation: dict[str, str]
    binary_sha256: dict[str, str]
    lock_sha256: str
    dependency_lock_sha256: str
    provers: tuple[ProverKind, ...]
    timeout_seconds: int = Field(ge=1, le=300)
    cases: tuple[CaseOutcome, ...]
    summary: BridgeSummary
    semantic_validation: Literal[False] = False
    replay_boundary: str

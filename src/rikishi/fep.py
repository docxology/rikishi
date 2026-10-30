"""Finite free energy and explicitly proposed links to a pinned Lean source."""

from __future__ import annotations

import math
import re
import subprocess
from collections.abc import Sequence
from importlib.resources import files
from pathlib import Path
from typing import Final, NotRequired, Self, TypedDict

from pydantic import BaseModel, ConfigDict, Field, model_validator

PIN: Final = "9a0694f16b8e89b66b2f7f8cc7426c650dd2c4de"
SOURCE: Final = "lean/FepSketches/finite_information.lean"
DECLARATIONS: Final = ("finiteKL_nonneg", "finiteKL_self", "finiteKL_eq_crossEntropy_sub_entropy")


class ProbabilityError(ValueError):
    """A finite model violates its probability or support contract."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


class EnergyResult(TypedDict):
    evidence: float
    surprise: float
    free_energy: float
    kl_to_posterior: float
    exact_posterior: list[float]
    identity_residual: float


class LogEnergyResult(TypedDict):
    evidence: float | None
    log_evidence: float
    surprise: float
    free_energy: float
    kl_to_posterior: float
    exact_posterior: list[float]
    log_exact_posterior: list[float | None]
    posterior_underflow_indices: list[int]
    identity_residual: float


def _probabilities(values: Sequence[float], name: str, *, normalized: bool) -> None:
    if not values or any(not math.isfinite(v) or v < 0 or v > 1 for v in values):
        raise ProbabilityError(f"{name} must contain finite probabilities in [0, 1]")
    if normalized and not math.isclose(math.fsum(values), 1.0, abs_tol=1e-12, rel_tol=0):
        raise ProbabilityError(f"{name} must sum to one")


def _finite_sum(values: Sequence[float]) -> float:
    try:
        return math.fsum(values)
    except OverflowError as error:
        raise ProbabilityError("calculation exceeds finite floating-point range") from error


def _log_probabilities(
    values: Sequence[float | None], name: str, *, normalized: bool
) -> None:
    if not values or any(v is not None and (not math.isfinite(v) or v > 0) for v in values):
        raise ProbabilityError(f"{name} must contain finite nonpositive logs or null for zero")
    if normalized:
        supported = [v for v in values if v is not None]
        if not supported:
            raise ProbabilityError(f"{name} must describe probabilities summing to one")
        peak = max(supported)
        total = _finite_sum([math.exp(v - peak) for v in supported])
        if not math.isclose(peak + math.log(total), 0.0, abs_tol=1e-12, rel_tol=0):
            raise ProbabilityError(f"{name} must describe probabilities summing to one")


def free_energy_log(
    log_prior: Sequence[float | None],
    log_likelihood: Sequence[float | None],
    posterior: Sequence[float],
) -> LogEnergyResult:
    """Evaluate from logarithmic inputs; null denotes exact zero mass.

    The posterior remains a normalized linear vector. A null returned evidence
    denotes positive evidence below the linear float range, not impossibility.
    Log posterior values retain support when their linear projections underflow.
    """
    _log_probabilities(log_prior, "log_prior", normalized=True)
    _log_probabilities(log_likelihood, "log_likelihood", normalized=False)
    _probabilities(posterior, "posterior", normalized=True)
    if len(log_prior) != len(log_likelihood) or len(log_prior) != len(posterior):
        raise ProbabilityError("prior, likelihood and posterior lengths must agree")
    supported_likelihood = [
        likelihood for prior, likelihood in zip(log_prior, log_likelihood, strict=True)
        if prior is not None and likelihood is not None
    ]
    if not supported_likelihood:
        raise ProbabilityError("observation must have positive evidence")
    likelihood_peak = max(supported_likelihood)
    scaled_joint = [
        None if p is None or likelihood is None else _finite_sum([p, likelihood - likelihood_peak])
        for p, likelihood in zip(log_prior, log_likelihood, strict=True)
    ]
    joint_peak = max(value for value in scaled_joint if value is not None)
    weights = [0.0 if value is None else math.exp(value - joint_peak) for value in scaled_joint]
    total_weight = _finite_sum(weights)
    normalizer = math.log(total_weight)
    log_evidence = _finite_sum([likelihood_peak, joint_peak, normalizer])
    log_exact = [
        None if value is None else _finite_sum([value - joint_peak, -normalizer])
        for value in scaled_joint
    ]
    energy_terms: list[float] = []
    divergence_terms: list[float] = []
    for q, p, likelihood, exact in zip(
        posterior, log_prior, log_likelihood, log_exact, strict=True
    ):
        if q == 0:
            continue
        if p is None or likelihood is None or exact is None:
            raise ProbabilityError("positive posterior mass requires positive joint support")
        entropy_term = q * math.log(q)
        energy_terms.append(_finite_sum([entropy_term, -q * p, -q * likelihood]))
        divergence_terms.append(_finite_sum([entropy_term, -q * exact]))
    energy = _finite_sum(energy_terms)
    divergence = _finite_sum(divergence_terms)
    evidence = math.exp(log_evidence)
    exact = [value / total_weight for value in weights]
    return {
        "evidence": evidence if evidence > 0 else None,
        "log_evidence": log_evidence,
        "surprise": -log_evidence,
        "free_energy": energy,
        "kl_to_posterior": divergence,
        "exact_posterior": exact,
        "log_exact_posterior": log_exact,
        "posterior_underflow_indices": [
            i for i, (value, mass) in enumerate(zip(log_exact, exact, strict=True))
            if value is not None and mass == 0.0
        ],
        "identity_residual": _finite_sum([energy, log_evidence, -divergence]),
    }


def free_energy(
    prior: Sequence[float], likelihood: Sequence[float], posterior: Sequence[float]
) -> EnergyResult:
    """Compute F(q)=sum q log(q/p(s,o)) in nats, with strict support checks.

    ``likelihood[i]`` is p(observation | state i), not a distribution over
    states. Zero q contributes zero. Positive q on zero joint mass is rejected
    because its free energy is infinite and cannot be serialized as finite JSON.
    """
    _probabilities(prior, "prior", normalized=True)
    _probabilities(likelihood, "likelihood", normalized=False)
    _probabilities(posterior, "posterior", normalized=True)
    if len(prior) != len(likelihood) or len(prior) != len(posterior):
        raise ProbabilityError("prior, likelihood and posterior lengths must agree")
    result = free_energy_log(
        [None if p == 0 else math.log(p) for p in prior],
        [None if p == 0 else math.log(p) for p in likelihood],
        posterior,
    )
    joint_projection = [p * likelihood[i] for i, p in enumerate(prior)]
    evidence = math.fsum(joint_projection)
    if evidence == 0:
        raise ProbabilityError("positive evidence is below linear float range; use free_energy_log")
    surprise = -math.log(evidence)
    return {
        "evidence": evidence,
        "surprise": surprise,
        "free_energy": result["free_energy"],
        "kl_to_posterior": result["kl_to_posterior"],
        "exact_posterior": [mass / evidence for mass in joint_projection],
        "identity_residual": _finite_sum([result["free_energy"], -surprise,
                                           -result["kl_to_posterior"]]),
    }


class _ModelInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", allow_inf_nan=False)


class _LinearModelInput(_ModelInput):
    prior: tuple[float, ...]
    likelihood: tuple[float, ...]
    posterior: tuple[float, ...]


class _LogModelInput(_ModelInput):
    log_prior: tuple[float | None, ...]
    log_likelihood: tuple[float | None, ...]
    posterior: tuple[float, ...]


def evaluate_model(path: Path, *, logarithmic: bool = False) -> EnergyResult | LogEnergyResult:
    content = path.read_bytes()
    if logarithmic:
        model = _LogModelInput.model_validate_json(content)
        return free_energy_log(model.log_prior, model.log_likelihood, model.posterior)
    model = _LinearModelInput.model_validate_json(content)
    return free_energy(model.prior, model.likelihood, model.posterior)


class DemoParameters(BaseModel):
    """Immutable binary model whose candidate and full inclusive scan are finite."""

    model_config = ConfigDict(
        strict=True, frozen=True, extra="forbid", allow_inf_nan=False, revalidate_instances="always"
    )

    prior: tuple[float, float]
    likelihood: tuple[float, float]
    candidate: tuple[float, float]
    scan_points: int = Field(ge=2)
    state_labels: tuple[str, str]

    @model_validator(mode="after")
    def check_model(self) -> Self:
        free_energy(self.prior, self.likelihood, self.candidate)
        free_energy(self.prior, self.likelihood, (1.0, 0.0))
        free_energy(self.prior, self.likelihood, (0.0, 1.0))
        labels = tuple(label.strip() for label in self.state_labels)
        if not all(labels) or labels[0] == labels[1]:
            raise ProbabilityError("state_labels must contain two distinct nonblank names")
        return self


def load_demo_parameters(path: Path | None = None) -> DemoParameters:
    """Load the packaged authority or an explicit JSON file; invalid input raises."""
    content = (
        files("rikishi").joinpath("data", "fep-example.json").read_bytes()
        if path is None
        else path.read_bytes()
    )
    return DemoParameters.model_validate_json(content)


class ScanPoint(TypedDict):
    q_state_zero: float
    free_energy: float


class DemoResult(TypedDict):
    units: str
    prior: list[float]
    likelihood: list[float]
    candidate: list[float]
    result: EnergyResult
    optimum: EnergyResult
    scan: list[ScanPoint]
    interpretation: str
    state_labels: NotRequired[list[str]]
    scan_points: NotRequired[int]


def demo(parameters: DemoParameters | None = None) -> DemoResult:
    """Calculate the checked binary model and its configured inclusive scan."""
    model = load_demo_parameters() if parameters is None else DemoParameters.model_validate(parameters)
    prior, likelihood, candidate = list(model.prior), list(model.likelihood), list(model.candidate)
    result = free_energy(prior, likelihood, candidate)
    scan: list[ScanPoint] = []
    for i in range(model.scan_points):
        q = i / (model.scan_points - 1)
        scan.append(
            {
                "q_state_zero": q,
                "free_energy": free_energy(prior, likelihood, (q, 1 - q))["free_energy"],
            }
        )
    return {
        "units": "nats",
        "prior": prior,
        "likelihood": likelihood,
        "candidate": candidate,
        "result": result,
        "optimum": free_energy(prior, likelihood, result["exact_posterior"]),
        "scan": scan,
        "interpretation": "Finite numerical illustration; proposed ontology connections are not a proof of the Free Energy Principle.",
    }


class Declaration(TypedDict):
    name: str
    line: int
    url: str


class FormalizationInspection(TypedDict):
    commit: str
    working_tree_clean: bool
    source: str
    declarations: list[Declaration]
    verification_scope: str


def inspect_formalization(repo: Path, revision: str = PIN) -> FormalizationInspection:
    """Inspect committed source at the recorded pin, without running Lean or modifying it."""
    repo = repo.resolve(strict=True)
    commit = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--verify", f"{revision}^{{commit}}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    source = subprocess.run(
        ["git", "-C", str(repo), "show", f"{commit}:{SOURCE}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    status = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    declarations: list[Declaration] = []
    for name in DECLARATIONS:
        matches = [
            i
            for i, line in enumerate(source.splitlines(), 1)
            if re.match(rf"^theorem\s+{re.escape(name)}\b", line)
        ]
        if len(matches) != 1:
            raise ProbabilityError(f"expected exactly one pinned declaration: {name}")
        line = matches[0]
        declarations.append(
            {
                "name": f"FEP.FiniteInformation.{name}",
                "line": line,
                "url": f"https://github.com/ActiveInferenceInstitute/fep_formal/blob/{commit}/{SOURCE}#L{line}",
            }
        )
    return {
        "commit": commit,
        "working_tree_clean": not bool(status),
        "source": SOURCE,
        "declarations": declarations,
        "verification_scope": "Pinned committed source inspection only; no Lean compilation or proof transport into SUMO performed.",
    }

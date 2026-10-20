"""Finite free energy and explicitly proposed links to a pinned Lean source."""

from __future__ import annotations

import math
import re
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Final, TypedDict

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


def _probabilities(values: Sequence[float], name: str, *, normalized: bool) -> None:
    if not values or any(not math.isfinite(v) or v < 0 or v > 1 for v in values):
        raise ProbabilityError(f"{name} must contain finite probabilities in [0, 1]")
    if normalized and not math.isclose(math.fsum(values), 1.0, abs_tol=1e-12, rel_tol=0):
        raise ProbabilityError(f"{name} must sum to one")


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
    joint = [p * likelihood[i] for i, p in enumerate(prior)]
    evidence = math.fsum(joint)
    if evidence <= 0:
        raise ProbabilityError("observation must have positive evidence")
    if any(q > 0 and joint[i] <= 0 for i, q in enumerate(posterior)):
        raise ProbabilityError("positive posterior mass requires positive joint support")
    exact = [p / evidence for p in joint]
    energy = math.fsum(
        q * (math.log(q) - math.log(joint[i])) for i, q in enumerate(posterior) if q > 0
    )
    divergence = math.fsum(
        q * (math.log(q) - math.log(exact[i])) for i, q in enumerate(posterior) if q > 0
    )
    surprise = -math.log(evidence)
    return {
        "evidence": evidence,
        "surprise": surprise,
        "free_energy": energy,
        "kl_to_posterior": divergence,
        "exact_posterior": exact,
        "identity_residual": energy - surprise - divergence,
    }


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


def demo() -> DemoResult:
    """Return a reproducible binary inference example and a 101-point curve."""
    prior, likelihood, candidate = [0.5, 0.5], [0.8, 0.2], [0.5, 0.5]
    result = free_energy(prior, likelihood, candidate)
    return {
        "units": "nats",
        "prior": prior,
        "likelihood": likelihood,
        "candidate": candidate,
        "result": result,
        "optimum": free_energy(prior, likelihood, result["exact_posterior"]),
        "scan": [
            {
                "q_state_zero": i / 100,
                "free_energy": free_energy(prior, likelihood, [i / 100, 1 - i / 100])[
                    "free_energy"
                ],
            }
            for i in range(101)
        ],
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

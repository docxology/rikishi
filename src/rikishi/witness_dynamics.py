"""Exact repeated conditioning and seeded forward simulation of fixed witnesses."""

from __future__ import annotations

from fractions import Fraction
from random import Random
from typing import Literal

from pydantic import Field

from rikishi.bridge_models import BridgeReport
from rikishi.finite_channels import FiniteChannel, FiniteChannelError, Law, exact_bayes
from rikishi.inference_models import Frozen


class ExactStep(Frozen):
    n: int
    cumulative_evidence: str
    posterior: tuple[str, ...]
    next_predictive: str


class SequentialRow(ExactStep):
    success_count: int
    false_count: int
    simulated_evidence: str
    simulated_posterior_false: str | None


class WitnessTrajectory(Frozen):
    witness_id: str
    prior: tuple[str, str]
    likelihood: tuple[str, str]
    kernel: tuple[tuple[str, ...], ...]
    simulation_seed: int
    rows: tuple[SequentialRow, ...]


class WitnessDynamics(Frozen):
    schema_version: Literal[1] = 1
    report_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    scope: Literal["Derived numerical experiment; no new Lean or native SUMO results"] = (
        "Derived numerical experiment; no new Lean or native SUMO results")
    assumptions: Literal[
        "Persistent Boolean state; observations conditionally independent given state/model; all true"
    ] = "Persistent Boolean state; observations conditionally independent given state/model; all true"
    state_order: tuple[Literal[False], Literal[True]] = (False, True)
    steps: Literal[12] = 12
    trials: Literal[65536] = 65536
    seed: Literal[20261026] = 20261026
    algorithm: Literal["Python Random MT19937; randrange(denominator) < numerator; latent once; all 12 draws"] = (
        "Python Random MT19937; randrange(denominator) < numerator; latent once; all 12 draws")
    witnesses: tuple[WitnessTrajectory, ...]
    model_weights: tuple[str, ...]


def sequential_conditioning(prior: Law, likelihood: Law, steps: int) -> tuple[ExactStep, ...]:
    """Compare direct powers with independent iterative Bayes, including n=0.

    A single hidden state persists through all observations. The selected
    likelihood is completed to a normalized Boolean observation kernel.
    Zero-evidence sequences are rejected rather than assigned a posterior.
    """
    if type(steps) is not int or steps < 0:
        raise FiniteChannelError("steps must be a nonnegative integer")
    exact_bayes(prior, likelihood)
    FiniteChannel("fixed-observation", tuple((1 - ell, ell) for ell in likelihood))
    posterior, cumulative = prior, Fraction(1)
    rows: list[ExactStep] = []
    for n in range(steps + 1):
        joint = tuple(p * ell ** n for p, ell in zip(prior, likelihood, strict=True))
        evidence = sum(joint, Fraction(0))
        direct = tuple(value / evidence for value in joint)
        if cumulative != evidence or posterior != direct:
            raise FiniteChannelError("Direct powers and iterative conditioning disagree")
        update = exact_bayes(posterior, likelihood)
        next_evidence = sum((p * ell ** (n + 1)
                             for p, ell in zip(prior, likelihood, strict=True)), Fraction(0))
        if update.evidence != next_evidence / evidence:
            raise FiniteChannelError("Predictive evidence ratio disagrees with Bayes update")
        rows.append(ExactStep(n=n, cumulative_evidence=str(evidence),
                              posterior=tuple(map(str, direct)),
                              next_predictive=str(update.evidence)))
        posterior, cumulative = update.posterior, cumulative * update.evidence
    return tuple(rows)


def _simulate(prior: Law, likelihood: Law, seed: int,
              trials: int, steps: int) -> tuple[tuple[int, int], ...]:
    """Sample the generative model, retaining counts for every all-true prefix.

    Integer draws avoid converting rational probabilities to binary floats.
    All draws are consumed even after a failed prefix; each witness restarts
    its separately recorded random seed. Counts are mutable accumulators only.
    """
    rng = Random(seed)
    successes, false_counts = [0] * (steps + 1), [0] * (steps + 1)
    for _ in range(trials):
        state = 0 if rng.randrange(prior[0].denominator) < prior[0].numerator else 1
        likelihood_state = likelihood[state]
        alive = True
        successes[0] += 1
        false_counts[0] += int(state == 0)
        for n in range(1, steps + 1):
            observed = rng.randrange(likelihood_state.denominator) < likelihood_state.numerator
            alive = alive and observed
            successes[n] += int(alive)
            false_counts[n] += int(alive and state == 0)
    return tuple(zip(successes, false_counts, strict=True))


def build_witness_dynamics(report: BridgeReport, report_sha256: str) -> WitnessDynamics:
    """Derive trajectories from a caller-validated BridgeReport, without native execution."""
    witnesses: list[WitnessTrajectory] = []
    for index, witness in enumerate(report.witnesses):
        prior = tuple(map(Fraction, witness.prior))
        likelihood = tuple(map(Fraction, witness.likelihood))
        exact = sequential_conditioning(prior, likelihood, 12)
        seed = 20261026 + index
        counts = _simulate(prior, likelihood, seed, 65536, 12)
        rows = tuple(SequentialRow(
            n=row.n, cumulative_evidence=row.cumulative_evidence,
            posterior=row.posterior, next_predictive=row.next_predictive,
            success_count=successes, false_count=false_count,
            simulated_evidence=str(Fraction(successes, 65536)),
            simulated_posterior_false=str(Fraction(false_count, successes)) if successes else None
        ) for row, (successes, false_count) in zip(exact, counts, strict=True))
        witnesses.append(WitnessTrajectory(
            witness_id=witness.id, prior=witness.prior, likelihood=witness.likelihood,
            kernel=tuple((str(1 - ell), str(ell)) for ell in likelihood),
            simulation_seed=seed, rows=rows))
    by_id = {witness.witness_id: witness for witness in witnesses}
    uniform, biased = by_id["uniform-prior"], by_id["biased-prior"]
    weights = tuple(str(Fraction(b.cumulative_evidence) / (
        Fraction(u.cumulative_evidence) + Fraction(b.cumulative_evidence)))
        for u, b in zip(uniform.rows, biased.rows, strict=True))
    return WitnessDynamics(report_sha256=report_sha256,
                           witnesses=tuple(witnesses), model_weights=weights)


def verify_witness_dynamics(raw: bytes, report: BridgeReport, report_sha256: str) -> None:
    """Reject any changed exact, simulation, assumption, or source-binding field."""
    actual = WitnessDynamics.model_validate_json(raw)
    if actual != build_witness_dynamics(report, report_sha256):
        raise FiniteChannelError("Witness dynamics differs from report-derived exact and seeded values")


def dynamics_table(data: WitnessDynamics) -> str:
    """Render the n=2 checkpoint table directly from the derived payload."""
    lines = ["| Witness | Z₂ | Posterior (false, true) | P(next true) | Simulated prefix count / trials |",
             "| --- | ---: | --- | ---: | ---: |"]
    for witness in data.witnesses:
        row = witness.rows[2]
        lines.append(f"| {witness.witness_id} | {row.cumulative_evidence} | "
                     f"({', '.join(row.posterior)}) | {row.next_predictive} | "
                     f"{row.success_count} / {data.trials} |")
    return "\n".join(lines)

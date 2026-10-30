"""Exact derived experiments; never extend the historical Lean or ATP verdicts."""

from __future__ import annotations

from decimal import MAX_EMAX, MIN_EMIN, Context, Decimal, localcontext
from fractions import Fraction
from typing import Final, Literal

from pydantic import Field

from rikishi.bridge_models import BridgeReport
from rikishi.finite_channels import (
    FiniteChannel,
    apply_channel,
    channel_information,
    exact_bayes,
)
from rikishi.inference_models import Frozen

PRECISION: Final = 100


class ChannelExperiment(Frozen):
    witness_id: str
    channel_id: str
    channel: tuple[tuple[str, ...], ...]
    coarse_prior: tuple[str, ...]
    coarse_joint: tuple[str, ...]
    coarse_likelihood: tuple[str, ...]
    coarse_candidate: tuple[str, ...]
    coarse_posterior: tuple[str, ...]
    pushed_posterior: tuple[str, ...]
    evidence: str
    kl_before: str
    kl_after: str
    information_loss: str
    tolerance: str


class EvidenceScaling(Frozen):
    witness_id: str
    scale: str
    prior: tuple[str, ...]
    original_likelihood: tuple[str, ...]
    scaled_kernel: tuple[tuple[str, ...], ...]
    original_evidence: str
    scaled_evidence: str
    original_posterior: tuple[str, ...]
    scaled_posterior: tuple[str, ...]
    original_surprise: str
    scaled_surprise: str
    surprise_shift: str


class ObservationExperiment(Frozen):
    witness_id: str
    observation_error: Literal["1/4"] = "1/4"
    noisy_likelihood: tuple[str, ...]
    noisy_evidence: str
    noisy_posterior: tuple[str, ...]
    repeated_true_prediction: str


class WitnessResearch(Frozen):
    schema_version: Literal[1] = 1
    report_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    precision: Literal[100] = PRECISION
    scope: Literal["Derived exact rational and Decimal experiments; no new Lean or native SUMO results"]
    channels: tuple[ChannelExperiment, ...]
    scalings: tuple[EvidenceScaling, ...]
    observations: tuple[ObservationExperiment, ...]
    biased_to_uniform_bayes_factor: str
    biased_model_posterior_equal_priors: str


def _strings(values: tuple[Fraction, ...]) -> tuple[str, ...]:
    return tuple(str(value) for value in values)


def research_channels() -> tuple[FiniteChannel, ...]:
    """Explicit hidden-state channels, ordered source-state then target-state."""
    f = Fraction
    return (
        FiniteChannel("identity", ((f(1), f(0)), (f(0), f(1)))),
        FiniteChannel("swap-labels", ((f(0), f(1)), (f(1), f(0)))),
        FiniteChannel("noisy-quarter", ((f(3, 4), f(1, 4)), (f(1, 4), f(3, 4)))),
        FiniteChannel("erase-state", ((f(1),), (f(1),))),
    )


def build_witness_research(report: BridgeReport, report_sha256: str) -> WitnessResearch:
    """Derive new mathematics from shared inputs without inventing native cases.

    The caller obtains ``report`` through trusted bridge replay. This pure layer
    checks the derived conditioning route; it does not authenticate that replay.
    Every output state in these four declared channels has positive prior mass.
    """
    channels: list[ChannelExperiment] = []
    scalings: list[EvidenceScaling] = []
    observations: list[ObservationExperiment] = []
    for witness in report.witnesses:
        prior = tuple(Fraction(v) for v in witness.prior)
        likelihood = tuple(Fraction(v) for v in witness.likelihood)
        candidate = tuple(Fraction(v) for v in witness.candidate)
        original = exact_bayes(prior, likelihood)
        for channel in research_channels():
            coarse_prior = apply_channel(prior, channel)
            # Joint mass is a sub-probability, so divide by Z before using the
            # normalized-law channel API, then restore Z by exact arithmetic.
            pushed_posterior = apply_channel(original.posterior, channel)
            coarse_joint = tuple(v * original.evidence for v in pushed_posterior)
            coarse_likelihood = tuple(j / p for j, p in zip(
                coarse_joint, coarse_prior, strict=True))
            coarse = exact_bayes(coarse_prior, coarse_likelihood)
            if coarse.evidence != original.evidence or coarse.posterior != pushed_posterior:
                raise ValueError("Derived state-channel conditioning does not commute")
            information = channel_information(candidate, original.posterior, channel,
                                              precision=PRECISION)
            channels.append(ChannelExperiment(
                witness_id=witness.id, channel_id=channel.name,
                channel=tuple(_strings(row) for row in channel.rows),
                coarse_prior=_strings(coarse_prior), coarse_joint=_strings(coarse_joint),
                coarse_likelihood=_strings(coarse_likelihood),
                coarse_candidate=_strings(apply_channel(candidate, channel)),
                coarse_posterior=_strings(coarse.posterior),
                pushed_posterior=_strings(pushed_posterior), evidence=str(coarse.evidence),
                kl_before=str(information.before), kl_after=str(information.after),
                information_loss=str(information.loss), tolerance=str(information.tolerance)))
        scale = Fraction(1, 2)
        selected = tuple(scale * value for value in likelihood)
        kernel = FiniteChannel("half-evidence", tuple((1 - value, value) for value in selected))
        scaled = exact_bayes(prior, selected)
        if scaled.posterior != original.posterior or scaled.evidence != scale * original.evidence:
            raise ValueError("Uniform likelihood scaling changed its posterior")
        with localcontext(Context(prec=PRECISION, Emax=MAX_EMAX, Emin=MIN_EMIN)):
            surprise = -(Decimal(original.evidence.numerator)
                         / Decimal(original.evidence.denominator)).ln()
            scaled_surprise = -(Decimal(scaled.evidence.numerator)
                                / Decimal(scaled.evidence.denominator)).ln()
            shift = scaled_surprise - surprise
        scalings.append(EvidenceScaling(
            witness_id=witness.id, scale=str(scale), prior=_strings(prior),
            original_likelihood=_strings(likelihood),
            scaled_kernel=tuple(_strings(row) for row in kernel.rows),
            original_evidence=str(original.evidence), scaled_evidence=str(scaled.evidence),
            original_posterior=_strings(original.posterior), scaled_posterior=_strings(scaled.posterior),
            original_surprise=str(surprise), scaled_surprise=str(scaled_surprise),
            surprise_shift=str(shift)))
        # This channel acts on observations, rather than on hidden states.
        noisy_likelihood = tuple(Fraction(1, 4) + value / 2 for value in likelihood)
        noisy = exact_bayes(prior, noisy_likelihood)
        repeated = sum((r * ell for r, ell in zip(original.posterior, likelihood,
                                                 strict=True)), Fraction(0))
        observations.append(ObservationExperiment(
            witness_id=witness.id, noisy_likelihood=_strings(noisy_likelihood),
            noisy_evidence=str(noisy.evidence), noisy_posterior=_strings(noisy.posterior),
            repeated_true_prediction=str(repeated)))
    evidence = {row.witness_id: Fraction(row.original_evidence) for row in scalings}
    factor = evidence["biased-prior"] / evidence["uniform-prior"]
    return WitnessResearch(report_sha256=report_sha256,
                           scope="Derived exact rational and Decimal experiments; no new Lean or native SUMO results",
                           channels=tuple(channels), scalings=tuple(scalings),
                           observations=tuple(observations),
                           biased_to_uniform_bayes_factor=str(factor),
                           biased_model_posterior_equal_priors=str(factor / (1 + factor)))


def verify_witness_research(raw: bytes, report: BridgeReport, report_sha256: str) -> None:
    """Recompute all exact and high-precision fields, including authority identity."""
    actual = WitnessResearch.model_validate_json(raw)
    expected = build_witness_research(report, report_sha256)
    if actual != expected:
        raise ValueError("Witness research differs from exact report-derived experiments")


def research_tables(data: WitnessResearch) -> tuple[str, str]:
    """Return deterministic tables consumed by every publication edition."""
    channels = ["| Witness | State channel | Candidate after | Posterior after | KL before / nats | KL after / nats |",
                "| --- | --- | --- | --- | ---: | ---: |"]
    for row in data.channels:
        label = row.witness_id.split("-", 1)[0].title()
        channels.append(f"| {label} | {row.channel_id} | ({', '.join(row.coarse_candidate)}) | "
                        f"({', '.join(row.coarse_posterior)}) | {_display(row.kl_before)} | "
                        f"{_display(row.kl_after)} |")
    scalings = ["| Witness | Original evidence | Scaled evidence | Unchanged posterior | Surprise increase / nats |",
                "| --- | --- | --- | --- | ---: |"]
    for row in data.scalings:
        label = row.witness_id.split("-", 1)[0].title()
        scalings.append(f"| {label} | {row.original_evidence} | {row.scaled_evidence} | "
                        f"({', '.join(row.scaled_posterior)}) | {_display(row.surprise_shift)} |")
    return "\n".join(channels), "\n".join(scalings)


def _display(raw: str) -> str:
    with localcontext(Context(prec=PRECISION, Emax=MAX_EMAX, Emin=MIN_EMIN)):
        return f"{Decimal(raw):.6f}"

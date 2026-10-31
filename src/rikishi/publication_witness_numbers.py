"""Inline manuscript numbers from replayed witnesses and their derived payloads."""

from __future__ import annotations

from collections.abc import Iterable
from decimal import MAX_EMAX, MIN_EMIN, Context, Decimal, localcontext
from fractions import Fraction

from rikishi.bridge_models import BridgeReport, FiniteWitness
from rikishi.finite_channels import exact_bayes
from rikishi.witness_dynamics import WitnessDynamics
from rikishi.witness_research import PRECISION, WitnessResearch


def _vector(values: Iterable[str | Fraction]) -> str:
    return "(" + ",".join(map(str, values)) + ")"


def _tex(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return rf"\frac{{{value.numerator}}}{{{value.denominator}}}"


def witness_base_numbers(witness: FiniteWitness) -> dict[str, str]:
    """Exact display values for the manuscript's full-support Boolean witnesses.

    These are formatting inputs, not evidence of native execution. Both prose
    and graphical labels use this route instead of transcribing worked values.
    """
    prior = tuple(map(Fraction, witness.prior))
    likelihood = tuple(map(Fraction, witness.likelihood))
    posterior = exact_bayes(prior, likelihood)
    if any(value <= 0 for value in (*prior, *likelihood)):
        raise ValueError("Inline witness odds require full prior and likelihood support")
    joint = tuple(p * k for p, k in zip(prior, likelihood, strict=True))
    fields = {
        "PRIOR": _vector(prior), "LIKELIHOOD": _vector(likelihood),
        "CANDIDATE": _vector(map(Fraction, witness.candidate)), "JOINT": _vector(joint),
        "EVIDENCE": str(posterior.evidence), "POSTERIOR": _vector(posterior.posterior),
        "KERNEL_FALSE": _vector((1 - likelihood[0], likelihood[0])),
        "KERNEL_TRUE": _vector((1 - likelihood[1], likelihood[1])),
        "PRIOR_ODDS": str(prior[1] / prior[0]),
        "LIKELIHOOD_RATIO": str(likelihood[1] / likelihood[0]),
        "POSTERIOR_ODDS": str(posterior.posterior[1] / posterior.posterior[0]),
        "UNWEIGHTED_LIKELIHOOD": str(sum(likelihood) / len(likelihood)),
        "REDRAWN_STEP2_EVIDENCE": str(posterior.evidence ** 2),
    }
    for state, label in enumerate(("FALSE", "TRUE")):
        fields["RECONSTRUCTION_" + label] = (
            _tex(posterior.posterior[state]) + r"\times" + _tex(posterior.evidence)
            + "=" + _tex(joint[state]))
        fields["RECONSTRUCTION_" + label + "_PLAIN"] = (
            f"({posterior.posterior[state]})({posterior.evidence})={joint[state]}")
    return fields


def witness_number_substitutions(
    report: BridgeReport, research: WitnessResearch, dynamics: WitnessDynamics,
    *, decimal_places: int,
) -> dict[str, str]:
    """Format the same mathematical objects as the generated tables and figures.

    The caller replays the authentic bridge packet and freshly derives both
    payloads. This formatter neither authenticates execution nor adds native or
    Lean claims. The named prose requires the three registered witnesses.
    """
    if type(decimal_places) is not int or not 0 <= decimal_places <= 15:
        raise ValueError("decimal_places must be an integer from zero through fifteen")
    names = {"uniform-prior": "UNIFORM", "biased-prior": "BIASED", "exact-candidate": "EXACT"}
    if len(report.witnesses) != len(names) or {w.id for w in report.witnesses} != names.keys():
        raise ValueError("Numerical prose requires the three registered witness identities")
    if research.report_sha256 != dynamics.report_sha256:
        raise ValueError("Numerical prose payloads bind different bridge reports")
    channels = {(row.witness_id, row.channel_id): row for row in research.channels}
    observations = {row.witness_id: row for row in research.observations}
    scalings = {row.witness_id: row for row in research.scalings}
    trajectories = {row.witness_id: row for row in dynamics.witnesses}
    values = {
        "NUM_RESEARCH_PRECISION": str(research.precision),
        "NUM_SIMULATION_TRIALS": f"{dynamics.trials:,}",
        "NUM_SIMULATION_STEPS": str(dynamics.steps),
        "NUM_BAYES_FACTOR": research.biased_to_uniform_bayes_factor,
        "NUM_BIASED_MODEL_POSTERIOR": research.biased_model_posterior_equal_priors,
    }
    try:
        values["NUM_BIASED_MODEL_POSTERIOR_STEP2"] = dynamics.model_weights[2]
        for witness in report.witnesses:
            prefix = "NUM_" + names[witness.id] + "_"
            noise = channels[witness.id, "noisy-quarter"]
            observation = observations[witness.id]
            scaling = scalings[witness.id]
            step = trajectories[witness.id].rows[2]
            if step.n != 2:
                raise ValueError("Numerical prose requires the n=2 trajectory checkpoint")
            fields = {
                **witness_base_numbers(witness),
                "NOISY_CHANNEL_FALSE": _vector(noise.channel[0]),
                "NOISY_CHANNEL_TRUE": _vector(noise.channel[1]),
                "COARSE_PRIOR": _vector(noise.coarse_prior),
                "COARSE_JOINT": _vector(noise.coarse_joint),
                "COARSE_LIKELIHOOD": _vector(noise.coarse_likelihood),
                "COARSE_POSTERIOR": _vector(noise.coarse_posterior),
                "OBSERVATION_ERROR": observation.observation_error,
                "NOISY_POSTERIOR": _vector(observation.noisy_posterior),
                "NOISY_EVIDENCE": observation.noisy_evidence,
                "NEXT_PREDICTION": observation.repeated_true_prediction,
                "EVIDENCE_SCALE": scaling.scale,
                "SCALE_RECIPROCAL": str(1 / Fraction(scaling.scale)),
                "STEP2_POSTERIOR": _vector(step.posterior),
                "STEP2_EVIDENCE": step.cumulative_evidence,
            }
            with localcontext(Context(prec=PRECISION, Emax=MAX_EMAX, Emin=MIN_EMIN)):
                fields["KL_BEFORE"] = f"{Decimal(noise.kl_before):.{decimal_places}f}"
                fields["KL_AFTER"] = f"{Decimal(noise.kl_after):.{decimal_places}f}"
            values.update({prefix + key: value for key, value in fields.items()})
    except (KeyError, IndexError, ZeroDivisionError) as error:
        raise ValueError("Numerical prose requires complete supported witness payloads") from error
    return values

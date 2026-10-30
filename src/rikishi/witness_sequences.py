"""Exact mixed observations and declared model mixtures on a persistent state.

Rows of a complete kernel describe P(False | state), P(True | state).
Observations are conditionally independent given the one persistent state and
model. These derived calculations add no Lean theorem or native SUMO outcome.
"""

from dataclasses import dataclass
from fractions import Fraction
from typing import Final

from rikishi.finite_channels import (
    FiniteChannel,
    FiniteChannelError,
    Law,
    apply_channel,
    exact_bayes,
)

MAX_OBSERVATIONS: Final = 1024


@dataclass(frozen=True, slots=True)
class SequenceStep:
    """One prefix, including its exact joint and complete next-observation law."""

    n: int
    observation: bool | None
    observation_probability: Fraction | None
    cumulative_evidence: Fraction
    joint: Law
    posterior: Law
    next_predictive: Law


@dataclass(frozen=True, slots=True)
class SequenceResult:
    """All persistent-state prefixes and the distinct redrawn-state evidence."""

    prior: Law
    kernel: FiniteChannel
    observations: tuple[bool, ...]
    steps: tuple[SequenceStep, ...]
    redrawn_evidence: Fraction


def _observations(observations: tuple[bool, ...]) -> None:
    if type(observations) is not tuple:
        raise FiniteChannelError("observations must be an immutable tuple")
    if len(observations) > MAX_OBSERVATIONS:
        raise FiniteChannelError(f"observations must contain at most {MAX_OBSERVATIONS} values")
    if any(type(value) is not bool for value in observations):
        raise FiniteChannelError("observations must contain only Boolean values")


def _initial_predictive(prior: Law, kernel: FiniteChannel) -> Law:
    if type(kernel) is not FiniteChannel:
        raise FiniteChannelError("kernel must be a FiniteChannel")
    if len(kernel.rows[0]) != 2:
        raise FiniteChannelError("kernel must have exactly two observation columns: False, True")
    return apply_channel(prior, kernel)


def _joint(prior: Law, kernel: FiniteChannel, true_count: int, false_count: int) -> Law:
    """Compute the joint from event counts, independently of iterative Bayes."""
    return tuple(mass * row[0] ** false_count * row[1] ** true_count
                 for mass, row in zip(prior, kernel.rows, strict=True))


def condition_sequence(prior: Law, kernel: FiniteChannel,
                       observations: tuple[bool, ...]) -> SequenceResult:
    """Condition a complete Boolean kernel on an exact observation path.

    The hidden carrier can have any finite nonempty size. Inputs must use exact
    Fraction laws and an immutable tuple of actual bool values. Each positive
    prefix is checked by direct joint powers and iterative Bayes. An impossible
    prefix raises rather than supplying a conditional law. The empty path has
    evidence one and does not condition on any future outcome.

    ``redrawn_evidence`` instead redraws the hidden state from the original prior
    before every observation. Equal final counts imply exchangeable final laws
    in the persistent model, but their intermediate paths may differ.
    """
    _observations(observations)
    initial = _initial_predictive(prior, kernel)
    posterior, cumulative, redrawn = prior, Fraction(1), Fraction(1)
    steps = [SequenceStep(0, None, None, cumulative, prior, prior, initial)]
    true_count = 0
    for n, observation in enumerate(observations, start=1):
        column = int(observation)
        update = exact_bayes(posterior, tuple(row[column] for row in kernel.rows))
        true_count += column
        joint = _joint(prior, kernel, true_count, n - true_count)
        evidence = sum(joint, Fraction(0))
        cumulative *= update.evidence
        if evidence != cumulative or update.posterior != tuple(mass / evidence for mass in joint):
            raise FiniteChannelError("Direct joint products and iterative conditioning disagree")
        posterior = update.posterior
        redrawn *= initial[column]
        steps.append(SequenceStep(n, observation, update.evidence, evidence, joint,
                                  posterior, apply_channel(posterior, kernel)))
    return SequenceResult(prior, kernel, observations, tuple(steps), redrawn)


@dataclass(frozen=True, slots=True)
class SequenceModel:
    """A named, validated exact prior and complete Boolean observation kernel."""

    name: str
    prior: Law
    kernel: FiniteChannel

    def __post_init__(self) -> None:
        if type(self.name) is not str or not self.name.strip():
            raise FiniteChannelError("model name must be nonblank text")
        _initial_predictive(self.prior, self.kernel)


@dataclass(frozen=True, slots=True)
class ModelSequenceResult:
    """A model's sequence likelihood and conditional state/predictive laws.

    Zero likelihood leaves both conditional laws absent; no arbitrary posterior
    is assigned to an impossible event.
    """

    name: str
    evidence: Fraction
    posterior: Law | None
    next_predictive: Law | None


@dataclass(frozen=True, slots=True)
class ModelComparison:
    """Prior-weighted model evidence, posterior weights and predictive mixture."""

    observations: tuple[bool, ...]
    model_prior: Law
    models: tuple[ModelSequenceResult, ...]
    evidence: Fraction
    posterior: Law
    next_predictive: Law


def compare_sequence_models(models: tuple[SequenceModel, ...], observations: tuple[bool, ...],
                            *, model_prior: Law | None = None) -> ModelComparison:
    """Compare the same observations under declared finite candidate models.

    Omitted model priors mean an explicit uniform distribution over the supplied
    unique names. A zero-likelihood component receives zero weight and no state
    posterior. Zero evidence for the complete prior-weighted mixture rejects.
    This is conditional inference within the supplied model set, not calibration,
    a fitted-model evaluation or empirical evidence that a model is adequate.
    """
    _observations(observations)
    if type(models) is not tuple or not models:
        raise FiniteChannelError("models must be a nonempty tuple of SequenceModel values")
    if any(type(model) is not SequenceModel for model in models):
        raise FiniteChannelError("models must contain only SequenceModel values")
    if len({model.name for model in models}) != len(models):
        raise FiniteChannelError("model names must be unique")
    weights = (Fraction(1, len(models)),) * len(models) if model_prior is None else model_prior
    exact_bayes(weights, (Fraction(1),) * len(models))
    true_count = sum(observations)
    results: list[ModelSequenceResult] = []
    for model in models:
        joint = _joint(model.prior, model.kernel, true_count, len(observations) - true_count)
        evidence = sum(joint, Fraction(0))
        if evidence == 0:
            results.append(ModelSequenceResult(model.name, evidence, None, None))
        else:
            last = condition_sequence(model.prior, model.kernel, observations).steps[-1]
            results.append(ModelSequenceResult(model.name, evidence, last.posterior,
                                               last.next_predictive))
    mixture = exact_bayes(weights, tuple(result.evidence for result in results))
    predictive = tuple(
        sum((weight * result.next_predictive[y]
             for weight, result in zip(mixture.posterior, results, strict=True)
             if result.next_predictive is not None), Fraction(0))
        for y in (0, 1))
    return ModelComparison(observations, weights, tuple(results), mixture.evidence,
                           mixture.posterior, predictive)


@dataclass(frozen=True, slots=True)
class BinomialFrequencyDiagnostic:
    """Exact observed frequency, signed error and model-based sampling variance."""

    successes: int
    trials: int
    probability: Fraction
    frequency: Fraction
    error: Fraction
    frequency_variance: Fraction
    impossible_under_model: bool


def binomial_frequency_diagnostic(successes: int, trials: int,
                                 probability: Fraction) -> BinomialFrequencyDiagnostic:
    """Describe one event across declared independent identically distributed trials.

    The frequency variance is p(1-p)/N using the caller's exact model probability,
    not a plug-in estimate or confidence interval. Prefix indicators from separate
    trajectories satisfy this assumption for each fixed prefix; different prefixes
    within one trajectory are correlated. No threshold or pass decision is made.
    """
    if type(trials) is not int or trials <= 0:
        raise FiniteChannelError("trials must be a positive integer")
    if type(successes) is not int or not 0 <= successes <= trials:
        raise FiniteChannelError("successes must be an integer from zero through trials")
    if type(probability) is not Fraction or not 0 <= probability <= 1:
        raise FiniteChannelError("probability must be an exact Fraction in [0, 1]")
    frequency = Fraction(successes, trials)
    variance = probability * (1 - probability) / trials
    error = frequency - probability
    return BinomialFrequencyDiagnostic(successes, trials, probability, frequency,
                                       error, variance, variance == 0 and error != 0)

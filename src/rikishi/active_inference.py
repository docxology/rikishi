"""One-step finite planning with explicit outcome preferences.

Masses and hypothetical conditioning are exact Fractions; information quantities
use Decimal natural logarithms. The adopted outcome-risk-plus-ambiguity score
is checked against expected preference surprisal minus state information gain.
This module supplies no SUMO entailment, Lean proof or empirical agent claim.
"""

from dataclasses import dataclass
from decimal import MAX_EMAX, MIN_EMIN, Context, Decimal, localcontext
from fractions import Fraction

from rikishi.finite_channels import (
    BayesResult,
    FiniteChannel,
    FiniteChannelError,
    Law,
    apply_channel,
    exact_bayes,
    relative_entropy,
)


@dataclass(frozen=True, slots=True)
class Action:
    """Current-to-next-state transition followed by a next-state-to-outcome channel.

    Rows are conditioning inputs, columns are outputs in both channels. All
    actions in one plan share the current-state and outcome meanings; their
    next-state carriers can differ. Names identify actions, not SUMO entities.
    """

    name: str
    transition: FiniteChannel
    observation: FiniteChannel

    def __post_init__(self) -> None:
        if type(self.name) is not str or not self.name.strip():
            raise FiniteChannelError("action name must be nonblank text")
        if type(self.transition) is not FiniteChannel or type(self.observation) is not FiniteChannel:
            raise FiniteChannelError("action channels must be FiniteChannel values")
        if len(self.transition.rows[0]) != len(self.observation.rows):
            raise FiniteChannelError("transition output and observation input dimensions must agree")


@dataclass(frozen=True, slots=True)
class ActionScore:
    """Exact predictions and approximate information quantities in nats."""

    name: str
    predicted: Law
    outcomes: Law
    risk: Decimal
    ambiguity: Decimal
    expected_surprisal: Decimal
    information_gain: Decimal
    expected_free_energy: Decimal
    decomposition_residual: Decimal
    tolerance: Decimal
    precision: int


@dataclass(frozen=True, slots=True)
class ActionPlan:
    """All scores and all numerical minimizers, in the supplied action order.

    No hidden tie-break or random draw is applied. A candidate is retained if
    its score is within the larger of its tolerance and the best one's.
    """

    scores: tuple[ActionScore, ...]
    minimizers: tuple[str, ...]
    precision: int


def _decimal(value: Fraction) -> Decimal:
    return Decimal(value.numerator) / Decimal(value.denominator)


def _entropy(law: Law) -> Decimal:
    return -sum((_decimal(p) * _decimal(p).ln() for p in law if p), Decimal(0))


def _predict(belief: Law, action: Action) -> tuple[Law, Law]:
    if type(action) is not Action:
        raise FiniteChannelError("action must be an Action")
    predicted = apply_channel(belief, action.transition)
    return predicted, apply_channel(predicted, action.observation)


def condition_action(belief: Law, action: Action, observation: int) -> BayesResult:
    """Advance the belief through the action, then condition on an actual outcome.

    The outcome is a zero-based integer column index, never a Boolean. An
    impossible observation rejects; hypothetical scoring does not observe it.
    Repeated calls are a filtering interface, not a sampled environment loop.
    """
    predicted, outcomes = _predict(belief, action)
    if type(observation) is not int or not 0 <= observation < len(outcomes):
        raise FiniteChannelError("observation must be an in-range integer column index")
    return exact_bayes(predicted, tuple(row[observation] for row in action.observation.rows))


def score_action(belief: Law, action: Action, preferences: Law, *, precision: int = 80) -> ActionScore:
    """Evaluate G = KL(predicted outcomes || preferences) + expected ambiguity.

    Preferences are a normalized strictly positive Fraction law over the common
    outcome alphabet. This is the adopted one-step outcome-preference functional,
    not an assertion that every formulation of expected free energy is identical.
    Information gain is independently summed over exact hypothetical posteriors.
    All Decimal operations use a fresh context with 20 guard digits; the signed
    decomposition residual is retained and must meet the reported tolerance.
    """
    predicted, outcomes = _predict(belief, action)
    risk = relative_entropy(outcomes, preferences, precision=precision)
    if any(value == 0 for value in preferences):
        raise FiniteChannelError("preferences must have strictly positive support")
    with localcontext(Context(prec=precision + 20, Emax=MAX_EMAX, Emin=MIN_EMIN)) as ctx:
        ambiguity = sum((_decimal(p) * _entropy(row)
                         for p, row in zip(predicted, action.observation.rows, strict=True)),
                        Decimal(0))
        expected_surprisal = -sum(
            (_decimal(p) * _decimal(c).ln() for p, c in zip(outcomes, preferences, strict=True)
             if p), Decimal(0))
        gain = Decimal(0)
        for o, mass in enumerate(outcomes):
            if mass == 0:
                continue
            posterior = exact_bayes(predicted, tuple(row[o] for row in action.observation.rows))
            gain += _decimal(mass) * relative_entropy(posterior.posterior, predicted,
                                                      precision=precision)
        objective = risk + ambiguity
        residual = objective - (expected_surprisal - gain)
        tolerance = (Decimal(10) ** (8 - precision)
                     * max(Decimal(1), abs(objective), abs(expected_surprisal), abs(gain))
                     * (len(predicted) + len(outcomes)))
        if abs(residual) > tolerance:
            raise FiniteChannelError("expected-free-energy decomposition exceeds tolerance")
        ctx.prec = precision
        return ActionScore(action.name, predicted, outcomes, +risk, +ambiguity,
                           +expected_surprisal, +gain, +objective, +residual, +tolerance, precision)


def plan_actions(belief: Law, actions: tuple[Action, ...], preferences: Law, *,
                 precision: int = 80) -> ActionPlan:
    """Score every uniquely named action, retaining all numerical minimizers.

    Every action must accept the belief and predict the preference alphabet.
    There are no implicit costs, policy priors, precision learning or planning
    horizon. Encode any outcome costs explicitly in the declared preferences.
    """
    if type(actions) is not tuple or not actions:
        raise FiniteChannelError("actions must be a nonempty immutable tuple")
    if any(type(action) is not Action for action in actions):
        raise FiniteChannelError("actions must contain only Action values")
    if len({action.name for action in actions}) != len(actions):
        raise FiniteChannelError("action names must be unique")
    scores = tuple(score_action(belief, action, preferences, precision=precision) for action in actions)
    best = min(scores, key=lambda score: score.expected_free_energy)
    with localcontext(Context(prec=precision + 20, Emax=MAX_EMAX, Emin=MIN_EMIN)):
        minimizers = tuple(score.name for score in scores
                           if score.expected_free_energy - best.expected_free_energy
                           <= max(score.tolerance, best.tolerance))
    return ActionPlan(scores, minimizers, precision)


def demo() -> dict[str, object]:
    """Synthetic sense-versus-noise example with identical outcome marginals.

    With uniform preferences, a noiseless sensor resolves state uncertainty;
    an independent fair-noise sensor does not. The transitions are identities.
    The returned inputs are the complete authority for this standalone example.
    """
    half = (Fraction(1, 2),) * 2
    identity = FiniteChannel("identity", ((Fraction(1), Fraction(0)),
                                          (Fraction(0), Fraction(1))))
    actions = (Action("sense", identity, identity),
               Action("noise", identity, FiniteChannel("noise", (half, half))))
    plan = plan_actions(half, actions, half)
    return {
        "scope": "synthetic one-step outcome-preference planning; no native or empirical evidence",
        "state_order": ["false", "true"], "outcome_order": ["false", "true"],
        "belief": [str(p) for p in half], "preferences": [str(p) for p in half],
        "precision": plan.precision, "minimizers": list(plan.minimizers),
        "actions": [{
            "name": action.name,
            "transition": [[str(p) for p in row] for row in action.transition.rows],
            "observation": [[str(p) for p in row] for row in action.observation.rows],
            "predicted": [str(p) for p in score.predicted],
            "outcomes": [str(p) for p in score.outcomes],
            **{field: str(getattr(score, field)) for field in (
                "risk", "ambiguity", "expected_surprisal", "information_gain",
                "expected_free_energy", "decomposition_residual", "tolerance")},
        } for action, score in zip(actions, plan.scores, strict=True)],
    }

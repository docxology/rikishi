"""Finite decision controls with exact channels and independent logarithms."""

from decimal import Context, Decimal, localcontext
from fractions import Fraction as F

import pytest

from rikishi.active_inference import (
    Action,
    condition_action,
    plan_actions,
    score_action,
)
from rikishi.finite_channels import FiniteChannel, FiniteChannelError


def identity(n=2):
    return FiniteChannel("identity", tuple(tuple(F(i == j) for j in range(n)) for i in range(n)))


def action(name="sense", rows=None, transition=None):
    return Action(name, transition or identity(), FiniteChannel(
        "observation", rows or ((F(1), F(0)), (F(0), F(1)))))


def test_information_seeking_distinguishes_equal_outcome_predictions():
    prior = preferences = (F(1, 2), F(1, 2))
    informative = action()
    noise = action("noise", ((F(1, 2), F(1, 2)),) * 2)
    plan = plan_actions(prior, (informative, noise), preferences)
    sense, noisy = plan.scores
    with localcontext(Context(prec=80)):
        log2 = Decimal(2).ln()
        assert abs(sense.information_gain - log2) < Decimal("1e-70")
        assert abs(noisy.expected_free_energy - log2) < Decimal("1e-70")
    assert sense.outcomes == noisy.outcomes == prior
    assert sense.risk == noisy.risk == sense.ambiguity == 0
    assert noisy.information_gain == sense.expected_free_energy == 0
    assert plan.minimizers == ("sense",)
    assert abs(sense.decomposition_residual) <= sense.tolerance
    assert abs(noisy.decomposition_residual) <= noisy.tolerance
    assert condition_action(prior, informative, 1).posterior == (F(0), F(1))


def test_preferences_can_reverse_the_information_seeking_choice():
    prior = (F(1, 2), F(1, 2))
    sense = action()
    reach = action("reach", ((F(1), F(0)),) * 2)
    assert plan_actions(prior, (sense, reach), prior).minimizers == ("sense",)
    result = plan_actions(prior, (sense, reach), (F(99, 100), F(1, 100)))
    assert result.minimizers == ("reach",)
    assert result.scores[0].information_gain > result.scores[1].information_gain


def test_action_transition_changes_the_prediction_before_conditioning():
    reset = FiniteChannel("reset", ((F(0), F(1)),) * 2)
    move = action("move", transition=reset)
    score = score_action((F(1), F(0)), move, (F(1, 4), F(3, 4)))
    assert score.predicted == score.outcomes == (F(0), F(1))
    assert score.information_gain == 0
    assert condition_action((F(1), F(0)), move, 1).posterior == (F(0), F(1))
    with pytest.raises(FiniteChannelError, match="positive evidence"):
        condition_action((F(1), F(0)), move, 0)


def test_general_carriers_and_unreachable_states():
    transition = FiniteChannel("expand", ((F(1, 3), F(2, 3), F(0)),))
    observe = FiniteChannel("observe", ((F(1), F(0)), (F(0), F(1)), (F(1, 2), F(1, 2))))
    score = score_action((F(1),), Action("expand", transition, observe), (F(1, 3), F(2, 3)))
    assert score.predicted == (F(1, 3), F(2, 3), F(0))
    assert score.outcomes == (F(1, 3), F(2, 3))
    assert score.risk == score.ambiguity == 0


def test_independent_joint_sum_and_caller_context_isolation():
    prior = (F(2, 7), F(5, 7))
    preferences = (F(1, 7), F(2, 7), F(4, 7))
    observe = ((F(1, 2), F(1, 3), F(1, 6)), (F(1, 5), F(0), F(4, 5)))
    a = action(rows=observe)
    with localcontext(Context(prec=90)):
        predicted = (F(2, 7), F(5, 7))
        outcomes = tuple(sum((predicted[s] * observe[s][o] for s in range(2)), F(0))
                         for o in range(3))
        reference = Decimal(0)
        for s in range(2):
            for o in range(3):
                joint = predicted[s] * observe[s][o]
                if joint:
                    ratio = outcomes[o] / (preferences[o] * observe[s][o])
                    reference += (Decimal(joint.numerator) / Decimal(joint.denominator)
                                  * (Decimal(ratio.numerator) / Decimal(ratio.denominator)).ln())
    with localcontext(Context(prec=3, Emax=9, Emin=-9)):
        score = score_action(prior, a, preferences, precision=80)
    assert abs(score.expected_free_energy - reference) < Decimal("1e-70")
    assert abs(score.decomposition_residual) <= score.tolerance


def test_ties_are_explicit_and_order_is_preserved():
    prior = (F(1, 2), F(1, 2))
    result = plan_actions(prior, (action("second"), action("first")), prior)
    assert result.minimizers == ("second", "first")
    assert result.precision == 80


@pytest.mark.parametrize("name", ["", " ", 1, True])
def test_action_rejects_bad_names(name):
    with pytest.raises(FiniteChannelError, match="name"):
        action(name)


def test_action_rejects_wrong_channels_and_mismatched_carriers():
    with pytest.raises(FiniteChannelError, match="FiniteChannel"):
        Action("bad", "identity", identity())
    with pytest.raises(FiniteChannelError, match="FiniteChannel"):
        Action("bad", identity(), None)
    with pytest.raises(FiniteChannelError, match="dimensions"):
        Action("bad", identity(3), identity())


@pytest.mark.parametrize("prior", [(F(1, 3), F(1, 3)), (0.5, 0.5), [F(1, 2)] * 2])
def test_rejects_invalid_beliefs(prior):
    with pytest.raises(FiniteChannelError):
        score_action(prior, action(), (F(1, 2), F(1, 2)))


@pytest.mark.parametrize("preferences", [
    (F(0), F(1)), (F(1, 3), F(1, 3)), (F(1),), (0.5, 0.5), [F(1, 2)] * 2,
])
def test_rejects_invalid_preferences(preferences):
    with pytest.raises(FiniteChannelError):
        score_action((F(1, 2), F(1, 2)), action(), preferences)


@pytest.mark.parametrize("precision", [True, 39, 201, 80.0])
def test_rejects_invalid_precision(precision):
    with pytest.raises(FiniteChannelError, match="precision"):
        score_action((F(1, 2), F(1, 2)), action(), (F(1, 2), F(1, 2)), precision=precision)


@pytest.mark.parametrize("actions", [(), [], ("bad",), (action(), action())])
def test_plan_rejects_empty_mutable_wrong_or_duplicate_actions(actions):
    with pytest.raises(FiniteChannelError):
        plan_actions((F(1, 2), F(1, 2)), actions, (F(1, 2), F(1, 2)))


@pytest.mark.parametrize("observation", [-1, 2, True, 0.5])
def test_rejects_wrong_observation_indices(observation):
    with pytest.raises(FiniteChannelError, match="observation"):
        condition_action((F(1, 2), F(1, 2)), action(), observation)


def test_public_methods_reject_wrong_action_type():
    with pytest.raises(FiniteChannelError, match="Action"):
        score_action((F(1),), None, (F(1),))
    with pytest.raises(FiniteChannelError, match="Action"):
        condition_action((F(1),), None, 0)


def test_structural_zero_observations_have_no_invented_posterior():
    a = action(rows=((F(1), F(0)),) * 2)
    score = score_action((F(1, 2), F(1, 2)), a, (F(1, 2), F(1, 2)))
    assert score.outcomes == (F(1), F(0))
    assert score.information_gain == score.ambiguity == 0
    assert score.expected_free_energy == score.expected_surprisal


def test_action_order_and_state_permutations_do_not_change_scores():
    rows = ((F(3, 4), F(1, 4)), (F(1, 3), F(2, 3)))
    p, c = (F(1, 3), F(2, 3)), (F(1, 4), F(3, 4))
    first = score_action(p, action(rows=rows), c)
    second = score_action(p[::-1], action(rows=rows[::-1]), c)
    assert first.expected_free_energy == second.expected_free_energy
    assert first.information_gain == second.information_gain


def test_numerical_ties_are_reported_without_rounding_the_score_difference_away():
    prior = (F(1, 2), F(1, 2))
    almost = action("almost", ((F(1) - F(1, 10**40), F(1, 10**40)), (F(0), F(1))))
    plan = plan_actions(prior, (action(), almost), prior, precision=40)
    assert plan.scores[0].expected_free_energy < plan.scores[1].expected_free_energy
    assert plan.minimizers == ("sense", "almost")


def test_plan_requires_compatible_input_and_outcome_carriers():
    with pytest.raises(FiniteChannelError, match="dimensions"):
        plan_actions((F(1),), (action(),), (F(1, 2), F(1, 2)))
    with pytest.raises(FiniteChannelError, match="dimensions"):
        plan_actions((F(1, 2), F(1, 2)), (action(),), (F(1),))


def test_zero_preferences_reject_even_when_the_outcome_is_unreachable():
    with pytest.raises(FiniteChannelError, match="strictly positive"):
        score_action((F(1, 2), F(1, 2)), action(rows=((F(1), F(0)),) * 2), (F(1), F(0)))

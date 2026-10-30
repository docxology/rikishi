"""Exact mixed-observation paths, model mixtures and finite-count diagnostics."""

from dataclasses import FrozenInstanceError
from fractions import Fraction as F
from itertools import product
from math import prod

import pytest

from rikishi.finite_channels import FiniteChannel, FiniteChannelError
from rikishi.witness_sequences import (
    MAX_OBSERVATIONS,
    SequenceModel,
    binomial_frequency_diagnostic,
    compare_sequence_models,
    condition_sequence,
)


@pytest.fixture
def uniform() -> SequenceModel:
    return SequenceModel("uniform-prior", (F(1, 2), F(1, 2)),
                         FiniteChannel("uniform-kernel", ((F(3, 4), F(1, 4)),
                                                          (F(1, 4), F(3, 4)))))


@pytest.fixture
def biased() -> SequenceModel:
    return SequenceModel("biased-prior", (F(1, 3), F(2, 3)),
                         FiniteChannel("biased-kernel", ((F(1, 2), F(1, 2)),
                                                         (F(1, 4), F(3, 4)))))


def test_mixed_sequence_returns_exact_prefixes_and_predictive_laws(uniform: SequenceModel) -> None:
    # Given an informative complete kernel and mixed observations.
    # When a single hidden state persists through True, False, True.
    result = condition_sequence(uniform.prior, uniform.kernel, (True, False, True))
    # Then every prefix retains evidence, posterior and the next complete law.
    assert [step.cumulative_evidence for step in result.steps] == [F(1), F(1, 2), F(3, 16), F(3, 32)]
    assert [step.posterior for step in result.steps] == [
        (F(1, 2), F(1, 2)), (F(1, 4), F(3, 4)),
        (F(1, 2), F(1, 2)), (F(1, 4), F(3, 4))]
    assert result.steps[-1].next_predictive == (F(3, 8), F(5, 8))
    assert result.steps[0].observation is None
    assert tuple(step.observation for step in result.steps[1:]) == result.observations
    assert result.redrawn_evidence == F(1, 8)
    assert result.redrawn_evidence != result.steps[-1].cumulative_evidence


def test_empty_sequence_retains_a_prior_even_when_true_is_impossible() -> None:
    # Given a model that only produces False.
    kernel = FiniteChannel("false-only", ((F(1), F(0)),))
    # When no observation has occurred.
    result = condition_sequence((F(1),), kernel, ())
    # Then no unsupported future observation is conditioned upon.
    assert len(result.steps) == 1
    assert result.steps[0].posterior == (F(1),)
    assert result.steps[0].next_predictive == (F(1), F(0))
    assert result.steps[0].cumulative_evidence == result.redrawn_evidence == 1


def test_all_three_step_paths_match_independent_products_and_partition_the_law(
    uniform: SequenceModel, biased: SequenceModel,
) -> None:
    # Given two declared models and the complete eight-path observation space.
    for model in (uniform, biased):
        total = F(0)
        by_count = {}
        # When each exact path is conditioned.
        for observations in product((False, True), repeat=3):
            result = condition_sequence(model.prior, model.kernel, observations)
            row = result.steps[-1]
            joint = tuple(p * prod((kernel[int(y)] for y in observations), start=F(1))
                          for p, kernel in zip(model.prior, model.kernel.rows, strict=True))
            evidence = sum(joint, F(0))
            # Then explicit path products agree and permutations preserve final values.
            assert row.joint == joint
            assert row.cumulative_evidence == evidence
            assert row.posterior == tuple(value / evidence for value in joint)
            assert row.next_predictive == tuple(
                sum((joint[s] * model.kernel.rows[s][y] for s in range(2)), F(0)) / evidence
                for y in (0, 1))
            key = sum(observations)
            value = (row.cumulative_evidence, row.posterior, row.next_predictive)
            if key in by_count:
                assert by_count[key] == value
            by_count[key] = value
            total += evidence
        assert total == 1


def test_same_final_count_does_not_identify_the_prefix_path(uniform: SequenceModel) -> None:
    # Given exchangeable full sequences with different first observations.
    left = condition_sequence(uniform.prior, uniform.kernel, (True, False))
    # When the order is reversed.
    right = condition_sequence(uniform.prior, uniform.kernel, (False, True))
    # Then final laws agree while the intermediate state beliefs differ.
    assert left.steps[-1].posterior == right.steps[-1].posterior
    assert left.steps[1].posterior != right.steps[1].posterior


def test_finite_hidden_carrier_need_not_have_two_states() -> None:
    # Given three hidden states but two observed outcomes.
    prior = (F(1, 2), F(1, 3), F(1, 6))
    kernel = FiniteChannel("three-states", ((F(1), F(0)), (F(1, 2), F(1, 2)), (F(0), F(1))))
    # When True then False is observed from a persistent state.
    row = condition_sequence(prior, kernel, (True, False)).steps[-1]
    # Then only the middle state can explain both observations.
    assert row.joint == (F(0), F(1, 12), F(0))
    assert row.posterior == (F(0), F(1), F(0))
    assert row.next_predictive == (F(1, 2), F(1, 2))


@pytest.mark.parametrize("observations", [(True,), (False, True)])
def test_zero_evidence_rejects_instead_of_inventing_a_posterior(observations) -> None:
    # Given a deterministic false-only observation model.
    kernel = FiniteChannel("false-only", ((F(1), F(0)),))
    # When an impossible observation appears, then the actual Bayes path rejects it.
    with pytest.raises(FiniteChannelError, match="positive evidence"):
        condition_sequence((F(1),), kernel, observations)


@pytest.mark.parametrize("observations", [[True], (1,), (0,), (1.0,), ("true",), (None,), True])
def test_observation_boundary_rejects_coercion(uniform: SequenceModel, observations) -> None:
    # Given values that could be mistaken for a Boolean sequence.
    # When the public API is called, then it rejects rather than coercing them.
    with pytest.raises(FiniteChannelError, match="Boolean|tuple"):
        condition_sequence(uniform.prior, uniform.kernel, observations)


def test_sequence_length_bound_accepts_boundary_and_rejects_next() -> None:
    # Given a deterministic kernel whose exact arithmetic does not grow in size.
    kernel = FiniteChannel("false-only", ((F(1), F(0)),))
    # When the declared maximum is used, then all prefixes are retained.
    assert len(condition_sequence((F(1),), kernel, (False,) * MAX_OBSERVATIONS).steps) == (
        MAX_OBSERVATIONS + 1)
    # An over-budget request must fail before running a larger path.
    with pytest.raises(FiniteChannelError, match="at most"):
        condition_sequence((F(1),), kernel, (False,) * (MAX_OBSERVATIONS + 1))


@pytest.mark.parametrize("prior", [(F(1, 3), F(1, 3)), [F(1, 2), F(1, 2)],
                                  (0.5, 0.5), (F(-1), F(2)), (F(1),)])
def test_prior_boundary_reuses_exact_law_contract(uniform: SequenceModel, prior) -> None:
    # Given an invalid probability law or dimension.
    # When conditioning begins, then the exact shared contract rejects it.
    with pytest.raises(FiniteChannelError):
        condition_sequence(prior, uniform.kernel, ())


@pytest.mark.parametrize("kernel", [None, True, ((F(1), F(0)),),
                                   FiniteChannel("one-outcome", ((F(1),),)),
                                   FiniteChannel("three-outcomes", ((F(1, 3),) * 3,))])
def test_kernel_must_be_a_complete_boolean_channel(kernel) -> None:
    # Given a non-channel or a non-Boolean observation space.
    # When conditioning begins, then a complete two-column channel is required.
    with pytest.raises(FiniteChannelError, match="FiniteChannel|two observation"):
        condition_sequence((F(1),), kernel, ())


def test_equal_prior_model_weights_use_sequence_evidence(
    uniform: SequenceModel, biased: SequenceModel,
) -> None:
    # Given equal initial model probabilities and the same mixed sequence.
    # When exact marginal likelihoods are compared.
    result = compare_sequence_models((uniform, biased), (True, False))
    # Then state posteriors and model probabilities retain distinct denominators.
    assert result.model_prior == (F(1, 2), F(1, 2))
    assert tuple(model.evidence for model in result.models) == (F(3, 16), F(5, 24))
    assert result.evidence == F(19, 96)
    assert result.posterior == (F(9, 19), F(10, 19))
    assert result.models[0].posterior == (F(1, 2), F(1, 2))
    assert result.models[1].posterior == (F(2, 5), F(3, 5))
    assert result.next_predictive == (F(8, 19), F(11, 19))


def test_explicit_model_prior_changes_weights_and_zero_prior_stays_zero(
    uniform: SequenceModel, biased: SequenceModel,
) -> None:
    # Given an explicit preference for the uniform model.
    # When the same data are evaluated under that prior.
    result = compare_sequence_models((uniform, biased), (True, False),
                                     model_prior=(F(3, 4), F(1, 4)))
    # Then the prior-weighted evidence is used rather than equal-prior normalization.
    assert result.posterior == (F(27, 37), F(10, 37))
    assert result.evidence == F(37, 192)
    excluded = compare_sequence_models((uniform, biased), (True, False),
                                       model_prior=(F(1), F(0)))
    assert excluded.posterior == (F(1), F(0))
    assert excluded.next_predictive == (F(1, 2), F(1, 2))


def test_impossible_component_gets_zero_weight_without_a_fabricated_state_posterior(
    uniform: SequenceModel,
) -> None:
    # Given one false-only model and another model supporting True.
    impossible = SequenceModel("false-only", (F(1),),
                               FiniteChannel("false-only", ((F(1), F(0)),)))
    # When True is observed under their mixture.
    result = compare_sequence_models((impossible, uniform), (True,))
    # Then the impossible component has no conditional state law.
    assert result.posterior == (F(0), F(1))
    assert result.models[0].evidence == 0
    assert result.models[0].posterior is None
    assert result.models[0].next_predictive is None
    assert result.next_predictive == (F(3, 8), F(5, 8))
    with pytest.raises(FiniteChannelError, match="positive evidence"):
        compare_sequence_models((impossible, uniform), (True,), model_prior=(F(1), F(0)))


@pytest.mark.parametrize("models", [(), [], (None,), (True,)])
def test_model_comparison_requires_nonempty_typed_models(models) -> None:
    # Given an invalid model collection.
    # When comparison is requested, then the model boundary rejects it.
    with pytest.raises(FiniteChannelError, match="models"):
        compare_sequence_models(models, ())


def test_duplicate_model_names_reject(uniform: SequenceModel) -> None:
    # Given two indistinguishable identifiers.
    # When comparing them, then retained model identities must remain unique.
    with pytest.raises(FiniteChannelError, match="unique"):
        compare_sequence_models((uniform, uniform), ())


@pytest.mark.parametrize("observations", [[True], (1,), (0.0,), ("false",)])
def test_model_comparison_rejects_observation_coercion(uniform: SequenceModel,
                                                     observations) -> None:
    # Given a model and a coercible observation collection.
    # When using the separate comparison entrypoint, then its boundary also rejects.
    with pytest.raises(FiniteChannelError, match="Boolean|tuple"):
        compare_sequence_models((uniform,), observations)


@pytest.mark.parametrize("name", ["", "   ", True, 1])
def test_model_name_must_be_nonblank_text(uniform: SequenceModel, name) -> None:
    # Given a missing or non-text model identifier.
    # When constructing the immutable model, then it rejects the name.
    with pytest.raises(FiniteChannelError, match="name"):
        SequenceModel(name, uniform.prior, uniform.kernel)


@pytest.mark.parametrize("weights", [(F(1),), (F(1, 3), F(1, 3)), (0.5, 0.5),
                                    [F(1, 2), F(1, 2)], (True, False)])
def test_model_prior_rejects_invalid_laws(uniform: SequenceModel, biased: SequenceModel,
                                        weights) -> None:
    # Given malformed, unnormalized or wrong-dimensional model weights.
    # When comparison is invoked, then prior normalization cannot be inferred.
    with pytest.raises(FiniteChannelError):
        compare_sequence_models((uniform, biased), (), model_prior=weights)


def test_empty_model_comparison_preserves_prior_and_mixes_initial_predictions(
    uniform: SequenceModel, biased: SequenceModel,
) -> None:
    # Given no data and explicit model weights.
    # When comparing the models.
    result = compare_sequence_models((uniform, biased), (), model_prior=(F(1, 4), F(3, 4)))
    # Then posterior model probabilities equal their prior.
    assert result.posterior == result.model_prior == (F(1, 4), F(3, 4))
    assert result.evidence == 1
    assert result.next_predictive == (F(3, 8), F(5, 8))


def test_results_are_frozen_exact_values(uniform: SequenceModel, biased: SequenceModel) -> None:
    # Given actual returned immutable values.
    sequence = condition_sequence(uniform.prior, uniform.kernel, (True,))
    comparison = compare_sequence_models((uniform, biased), (True,))
    # When attempting to overwrite state, then mutation fails.
    for value in (uniform, sequence, sequence.steps[-1], comparison, comparison.models[0]):
        with pytest.raises(FrozenInstanceError):
            setattr(value, next(iter(value.__dataclass_fields__)), None)
        assert not hasattr(value, "__dict__")


def test_binomial_frequency_variance_is_exact_for_a_declared_prefix_probability() -> None:
    # Given a fixed-prefix indicator from independent simulated trajectories.
    # When its count is compared with the declared exact model probability.
    result = binomial_frequency_diagnostic(20645, 65536, F(5, 16))
    # Then sampling variance and signed error are exact; no pass threshold is invented.
    assert result.frequency == F(20645, 65536)
    assert result.error == F(165, 65536)
    assert result.frequency_variance == F(55, 16777216)
    assert not result.impossible_under_model


@pytest.mark.parametrize("count,probability,impossible", [(0, F(0), False), (1, F(0), True),
                                                        (10, F(1), False), (9, F(1), True)])
def test_deterministic_binomial_models_identify_impossible_counts(count, probability,
                                                               impossible) -> None:
    # Given a deterministic declared event probability.
    # When a concrete count is inspected.
    result = binomial_frequency_diagnostic(count, 10, probability)
    # Then variance is zero and incompatible counts are explicitly identified.
    assert result.frequency_variance == 0
    assert result.impossible_under_model is impossible


@pytest.mark.parametrize("count,trials,probability", [
    (True, 10, F(1, 2)), (1, True, F(1, 2)), (1.0, 10, F(1, 2)),
    (1, 10.0, F(1, 2)), (-1, 10, F(1, 2)), (11, 10, F(1, 2)),
    (0, 0, F(1, 2)), (0, -1, F(1, 2)), (1, 10, 0.5),
    (1, 10, True), (1, 10, F(-1)), (1, 10, F(2)),
])
def test_binomial_diagnostic_rejects_invalid_counts_or_probability(count, trials,
                                                                 probability) -> None:
    # Given invalid counts or a coercible/inadmissible probability.
    # When the exact diagnostic is called, then it rejects at its boundary.
    with pytest.raises(FiniteChannelError):
        binomial_frequency_diagnostic(count, trials, probability)

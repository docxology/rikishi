"""Exact stochastic channels, independent KL oracles, and malformed controls."""

from dataclasses import FrozenInstanceError, fields
from decimal import ROUND_DOWN, Decimal, localcontext
from fractions import Fraction as F

import pytest

from rikishi.finite_channels import (
    BayesResult,
    ChannelInformation,
    FiniteChannel,
    FiniteChannelError,
    apply_channel,
    channel_information,
    exact_bayes,
    relative_entropy,
)


def _assert_frozen(value: FiniteChannel | BayesResult | ChannelInformation) -> None:
    for field in fields(value):
        with pytest.raises(FrozenInstanceError):
            setattr(value, field.name, getattr(value, field.name))
    assert not hasattr(value, "__dict__")


@pytest.mark.parametrize(
    ("rows", "expected"),
    [
        (((F(1), F(0)), (F(0), F(1))), (F(3, 4), F(1, 4))),
        (((F(0), F(1)), (F(1), F(0))), (F(1, 4), F(3, 4))),
        (((F(1),), (F(1),)), (F(1),)),
        (((F(3, 4), F(1, 4)), (F(1, 4), F(3, 4))), (F(5, 8), F(3, 8))),
    ],
)
def test_exact_channel_action(rows, expected):
    assert apply_channel((F(3, 4), F(1, 4)), FiniteChannel("example", rows)) == expected


def test_three_state_rectangular_channel_and_bayes():
    prior = (F(1, 2), F(1, 3), F(1, 6))
    channel = FiniteChannel("merge", ((F(1), F(0)), (F(0), F(1)), (F(0), F(1))))
    assert apply_channel(prior, channel) == (F(1, 2), F(1, 2))
    update = exact_bayes(prior, (F(1, 2), F(1), F(0)))
    assert update.joint == (F(1, 4), F(1, 3), F(0))
    assert update.evidence == F(7, 12)
    assert update.posterior == (F(3, 7), F(4, 7), F(0))
    _assert_frozen(update)
    _assert_frozen(channel)


def test_binary_bayes_and_zero_prior():
    update = exact_bayes((F(1, 2), F(1, 2)), (F(4, 5), F(1, 5)))
    assert update.posterior == (F(4, 5), F(1, 5))
    assert update.evidence == F(1, 2)
    assert exact_bayes((F(0), F(1)), (F(0), F(1))).posterior == (F(0), F(1))


@pytest.mark.parametrize("precision", [40, 100, 200])
def test_kl_independent_closed_form_and_context_isolation(precision: int):
    with localcontext() as ctx:
        ctx.prec = precision + 10
        expected = Decimal(3) / 4 * Decimal(3).ln() - Decimal(2).ln()
    with localcontext() as ctx:
        ctx.prec = 6
        ctx.rounding = ROUND_DOWN
        ctx.Emax = 9
        ctx.Emin = -9
        actual = relative_entropy((F(3, 4), F(1, 4)), (F(1, 2), F(1, 2)), precision=precision)
    with localcontext() as ctx:
        ctx.prec = precision + 10
        assert abs(actual - expected) < Decimal(10) ** (2 - precision)


def test_kl_support_conventions_and_tiny_exact_mass():
    assert relative_entropy((F(0), F(1)), (F(0), F(1))) == 0
    tiny = F(1, 10**1000)
    assert relative_entropy((tiny, 1 - tiny), (tiny, 1 - tiny)) == 0
    with pytest.raises(FiniteChannelError, match="support"):
        relative_entropy((F(1), F(0)), (F(0), F(1)))


@pytest.mark.parametrize(
    ("rows", "relation"),
    [
        (((F(1), F(0)), (F(0), F(1))), "preserve"),
        (((F(0), F(1)), (F(1), F(0))), "preserve"),
        (((F(1),), (F(1),)), "collapse"),
        (((F(3, 4), F(1, 4)), (F(1, 4), F(3, 4))), "contract"),
    ],
)
def test_data_processing_preservation_collapse_and_contraction(rows, relation):
    result = channel_information(
        (F(3, 4), F(1, 4)), (F(1, 2), F(1, 2)), FiniteChannel(relation, rows)
    )
    assert result.before > 0
    assert result.residual <= result.tolerance
    with localcontext() as ctx:
        ctx.prec = 120
        assert result.loss == result.before - result.after
        assert result.residual == -result.loss
    if relation == "preserve":
        assert abs(result.loss) <= result.tolerance
    elif relation == "collapse":
        assert result.after == 0
        assert result.loss == result.before
    else:
        assert 0 < result.after < result.before
        assert result.candidate_after == (F(5, 8), F(3, 8))
        assert result.reference_after == (F(1, 2), F(1, 2))
    _assert_frozen(result)


def test_three_state_strict_contraction_and_precision_tolerance():
    channel = FiniteChannel("merge", ((F(1), F(0)), (F(0), F(1)), (F(0), F(1))))
    low = channel_information((F(1, 2), F(1, 3), F(1, 6)), (F(1, 3),) * 3, channel, precision=40)
    high = channel_information((F(1, 2), F(1, 3), F(1, 6)), (F(1, 3),) * 3, channel, precision=100)
    assert low.loss > low.tolerance
    assert high.loss > high.tolerance
    assert high.tolerance < low.tolerance


@pytest.mark.parametrize(
    "rows",
    [
        (),
        ((),),
        ((F(1),), (F(1, 2), F(1, 2))),
        ((F(-1), F(2)),),
        ((F(1, 3), F(1, 3)),),
        [[F(1)]],
        ([F(1)],),
        ((True,),),
        ((1,),),
        ((1.0,),),
        (("1",),),
        ((Decimal(1),),),
    ],
)
def test_malformed_channels_are_rejected(rows):
    with pytest.raises(FiniteChannelError):
        FiniteChannel("bad", rows)


@pytest.mark.parametrize("name", ["", "  ", None, 1, True])
def test_channel_name_rejection(name):
    with pytest.raises(FiniteChannelError):
        FiniteChannel(name, ((F(1),),))


@pytest.mark.parametrize(
    "law", [(), (F(1, 2),), (F(-1), F(2)), [F(1)], (True,), (1,), (1.0,), ("1",), (Decimal(1),)]
)
def test_law_rejection_at_all_boundaries(law):
    channel = FiniteChannel("one", ((F(1),),))
    with pytest.raises(FiniteChannelError):
        apply_channel(law, channel)
    with pytest.raises(FiniteChannelError):
        exact_bayes(law, (F(1),))
    with pytest.raises(FiniteChannelError):
        relative_entropy(law, (F(1),))
    with pytest.raises(FiniteChannelError):
        relative_entropy((F(1),), law)


@pytest.mark.parametrize(
    "likelihood", [(), (F(-1),), (F(2),), [F(1)], (True,), (1,), (1.0,), ("1",), (Decimal(1),)]
)
def test_likelihood_rejection(likelihood):
    with pytest.raises(FiniteChannelError):
        exact_bayes((F(1),), likelihood)


def test_zero_evidence_and_dimension_rejection():
    with pytest.raises(FiniteChannelError, match="evidence"):
        exact_bayes((F(0), F(1)), (F(1), F(0)))
    with pytest.raises(FiniteChannelError, match="dimension"):
        exact_bayes((F(1),), (F(1), F(1)))
    with pytest.raises(FiniteChannelError, match="dimension"):
        apply_channel((F(1),), FiniteChannel("two", ((F(1),), (F(1),))))
    with pytest.raises(FiniteChannelError, match="dimension"):
        relative_entropy((F(1),), (F(1, 2), F(1, 2)))


@pytest.mark.parametrize("precision", [True, False, 39, 201, 40.0, "100", None])
def test_precision_rejection(precision):
    with pytest.raises(FiniteChannelError, match="precision"):
        relative_entropy((F(1),), (F(1),), precision=precision)
    with pytest.raises(FiniteChannelError, match="precision"):
        channel_information((F(1),), (F(1),), FiniteChannel("one", ((F(1),),)), precision=precision)


def test_asymmetric_channel_detects_transpose_error():
    rows = ((F(1, 2), F(1, 2), F(0)), (F(0), F(1, 2), F(1, 2)), (F(1, 2), F(0), F(1, 2)))
    prior = (F(1, 2), F(1, 3), F(1, 6))
    actual = apply_channel(prior, FiniteChannel("asymmetric", rows))
    transposed = apply_channel(prior, FiniteChannel("transpose", tuple(zip(*rows, strict=True))))
    assert actual == (F(1, 3), F(5, 12), F(1, 4))
    assert transposed == (F(5, 12), F(1, 4), F(1, 3))
    assert actual != transposed


def test_bayes_commutes_with_coarse_graining_of_the_joint():
    prior = (F(1, 2), F(1, 3), F(1, 6))
    update = exact_bayes(prior, (F(1, 2), F(1), F(0)))
    channel = FiniteChannel("merge", ((F(1), F(0)), (F(0), F(1)), (F(0), F(1))))
    coarse_prior = apply_channel(prior, channel)
    coarse_posterior = apply_channel(update.posterior, channel)
    coarse_joint = tuple(update.evidence * mass for mass in coarse_posterior)
    likelihood = tuple(j / p for j, p in zip(coarse_joint, coarse_prior, strict=True))
    coarse = exact_bayes(coarse_prior, likelihood)
    assert coarse.evidence == update.evidence == F(7, 12)
    assert coarse.posterior == coarse_posterior == (F(3, 7), F(4, 7))
    with pytest.raises(FiniteChannelError, match="sum exactly"):
        apply_channel(update.joint, channel)

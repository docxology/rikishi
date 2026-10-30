"""Exact finite stochastic channels with numerical relative entropy in nats.

Fraction arithmetic determines all probability masses. Decimal logarithms are
approximations, with an explicit tolerance on the data-processing residual.
These calculations supply neither native SUMO evidence nor new Lean proofs.
"""

from dataclasses import dataclass
from decimal import MAX_EMAX, MIN_EMIN, Context, Decimal, localcontext
from fractions import Fraction

type Law = tuple[Fraction, ...]


class FiniteChannelError(ValueError):
    """A probability, support, dimension, or numerical contract was violated."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def _probabilities(values: Law, name: str, *, normalized: bool) -> None:
    """Check the exact immutable public boundary without coercing inputs."""
    if type(values) is not tuple or not values:
        raise FiniteChannelError(f"{name} must be a nonempty tuple")
    if any(type(value) is not Fraction for value in values):
        raise FiniteChannelError(f"{name} entries must be exact Fraction values")
    if any(value < 0 or value > 1 for value in values):
        raise FiniteChannelError(f"{name} entries must lie in [0, 1]")
    if normalized and sum(values, Fraction(0)) != 1:
        raise FiniteChannelError(f"{name} must sum exactly to one")


def _precision(precision: int) -> None:
    if type(precision) is not int or not 40 <= precision <= 200:
        raise FiniteChannelError("precision must be an integer from 40 through 200")


@dataclass(frozen=True, slots=True)
class FiniteChannel:
    """A row-stochastic matrix: rows are inputs and columns are outputs."""

    name: str
    rows: tuple[Law, ...]

    def __post_init__(self) -> None:
        if type(self.name) is not str or not self.name.strip():
            raise FiniteChannelError("channel name must be a nonblank string")
        if type(self.rows) is not tuple or not self.rows:
            raise FiniteChannelError("channel rows must be a nonempty tuple")
        for row in self.rows:
            _probabilities(row, "channel row", normalized=True)
        if any(len(row) != len(self.rows[0]) for row in self.rows):
            raise FiniteChannelError("channel rows must have equal dimensions")


@dataclass(frozen=True, slots=True)
class BayesResult:
    """Joint masses for one observation, its evidence, and conditional law."""

    joint: Law
    evidence: Fraction
    posterior: Law


@dataclass(frozen=True, slots=True)
class ChannelInformation:
    """Numerical data processing with exact transformed laws.

    ``loss = before - after`` and ``residual = after - before`` are signed,
    unclamped quantities. Acceptance requires ``residual <= tolerance``.
    Tolerance is 10**(8-precision) times the larger of one and the KL magnitudes,
    times the total number of input and output states; it is a numerical check,
    not an interval-arithmetic proof or an exact equality certificate.
    """

    before: Decimal
    after: Decimal
    loss: Decimal
    residual: Decimal
    tolerance: Decimal
    candidate_after: Law
    reference_after: Law
    precision: int


def apply_channel(law: Law, channel: FiniteChannel) -> Law:
    """Push a normalized input law through a row-stochastic channel exactly."""
    _probabilities(law, "law", normalized=True)
    if len(law) != len(channel.rows):
        raise FiniteChannelError("law and channel input dimensions must agree")
    return tuple(
        sum((mass * weight for mass, weight in zip(law, column, strict=True)), Fraction(0))
        for column in zip(*channel.rows, strict=True)
    )


def exact_bayes(prior: Law, likelihood: Law) -> BayesResult:
    """Condition on one observation; likelihood need not sum over states to one."""
    _probabilities(prior, "prior", normalized=True)
    _probabilities(likelihood, "likelihood", normalized=False)
    if len(prior) != len(likelihood):
        raise FiniteChannelError("prior and likelihood dimensions must agree")
    joint = tuple(p * ell for p, ell in zip(prior, likelihood, strict=True))
    evidence = sum(joint, Fraction(0))
    if evidence == 0:
        raise FiniteChannelError("observation must have positive evidence")
    return BayesResult(joint, evidence, tuple(mass / evidence for mass in joint))


def relative_entropy(candidate: Law, reference: Law, *, precision: int = 100) -> Decimal:
    """Evaluate KL(candidate || reference), using natural logs and zero terms.

    Positive candidate mass outside reference support raises instead of returning
    infinity. A fresh context, 20 guard digits, and maximal Decimal exponent
    range isolate computation from the caller's rounding and exponent settings.
    """
    _precision(precision)
    _probabilities(candidate, "candidate", normalized=True)
    _probabilities(reference, "reference", normalized=True)
    if len(candidate) != len(reference):
        raise FiniteChannelError("candidate and reference dimensions must agree")
    with localcontext(Context(prec=precision + 20, Emax=MAX_EMAX, Emin=MIN_EMIN)) as ctx:
        terms: list[Decimal] = []
        for q, p in zip(candidate, reference, strict=True):
            if q == 0:
                continue
            if p == 0:
                raise FiniteChannelError("positive candidate mass requires reference support")
            ratio = q / p
            log_ratio = (Decimal(ratio.numerator) / Decimal(ratio.denominator)).ln()
            terms.append(Decimal(q.numerator) / Decimal(q.denominator) * log_ratio)
        value = sum(terms, Decimal(0))
        ctx.prec = precision
        return +value


def channel_information(
    candidate: Law, reference: Law, channel: FiniteChannel, *, precision: int = 100
) -> ChannelInformation:
    """Check numerical KL contraction under the same exact channel.

    The three mathematical inputs are independent; the keyword-only precision
    controls their numerical evaluation without altering those inputs.
    """
    before = relative_entropy(candidate, reference, precision=precision)
    candidate_after = apply_channel(candidate, channel)
    reference_after = apply_channel(reference, channel)
    after = relative_entropy(candidate_after, reference_after, precision=precision)
    with localcontext(Context(prec=precision + 20, Emax=MAX_EMAX, Emin=MIN_EMIN)):
        loss = before - after
        residual = -loss
        tolerance = (
            Decimal(10) ** (8 - precision)
            * max(Decimal(1), abs(before), abs(after))
            * (len(candidate) + len(candidate_after))
        )
        if residual > tolerance:
            raise FiniteChannelError(
                f"data-processing residual {residual} exceeds tolerance {tolerance}"
            )
    return ChannelInformation(
        before, after, loss, residual, tolerance, candidate_after, reference_after, precision
    )

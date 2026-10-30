import json
import math
import random
from decimal import Decimal, localcontext

import pytest

from rikishi.fep import ProbabilityError, evaluate_model, free_energy, free_energy_log


def test_positive_joint_support_survives_product_underflow():
    with localcontext() as context:
        context.prec = 80
        joint = Decimal("1e-300") * Decimal("1e-300")
        expected = float(-joint.ln())
    assert 1e-300 * 1e-300 == 0.0
    result = free_energy([1e-300, 1.0], [1e-300, 0.5], [1.0, 0.0])
    assert result["evidence"] == pytest.approx(0.5)
    assert result["free_energy"] == pytest.approx(expected)
    assert result["kl_to_posterior"] == pytest.approx(expected - math.log(2))
    assert abs(result["identity_residual"]) < 1e-12


def test_log_evidence_remains_available_below_linear_float_range():
    result = free_energy_log([math.log(0.5)] * 2, [-1000.0, -1001.0], [0.5, 0.5])
    with localcontext() as context:
        context.prec = 80
        evidence = ((Decimal(-1000).exp() + Decimal(-1001).exp()) / 2)
        log_evidence = evidence.ln()
        posterior = [float(Decimal(-x).exp() / (2 * evidence)) for x in (1000, 1001)]
    assert result["evidence"] is None
    assert result["log_evidence"] == pytest.approx(float(log_evidence))
    assert result["exact_posterior"] == pytest.approx(posterior)
    assert result["free_energy"] == pytest.approx(1000.5)
    assert abs(result["identity_residual"]) < 1e-12
    json.dumps(result, allow_nan=False)


def test_log_posterior_distinguishes_underflow_from_exact_zero():
    result = free_energy_log(
        [math.log(1e-300), 0.0, None], [math.log(1e-300), math.log(0.5), None],
        [1.0, 0.0, 0.0],
    )
    assert result["exact_posterior"] == [0.0, 1.0, 0.0]
    assert result["posterior_underflow_indices"] == [0]
    assert result["log_exact_posterior"][0] == pytest.approx(2 * math.log(1e-300) + math.log(2))
    assert result["log_exact_posterior"][2] is None
    assert result["free_energy"] == pytest.approx(-2 * math.log(1e-300))


def test_common_likelihood_scale_preserves_prior_ratios():
    prior = [0.25, 0.75]
    result = free_energy_log([math.log(p) for p in prior], [-1e300] * 2, prior)
    assert result["exact_posterior"] == pytest.approx(prior)
    assert result["log_exact_posterior"] == pytest.approx([math.log(p) for p in prior])
    assert result["log_evidence"] == -1e300
    assert result["kl_to_posterior"] == pytest.approx(0.0, abs=1e-14)


def test_zero_candidate_on_exact_zero_support_is_valid():
    result = free_energy_log([None, 0.0], [None, 0.0], [0.0, 1.0])
    assert result["free_energy"] == result["kl_to_posterior"] == 0.0
    assert result["log_exact_posterior"] == [None, 0.0]
    assert result["posterior_underflow_indices"] == []


@pytest.mark.parametrize(
    ("prior", "likelihood", "q", "reason"),
    [
        ([], [], [], "log_prior"),
        ([None, None], [0.0, 0.0], [0.5, 0.5], "summing to one"),
        ([0.1, None], [0.0, 0.0], [0.5, 0.5], "log_prior"),
        ([-1.0, -1.0], [0.0, 0.0], [0.5, 0.5], "summing to one"),
        ([0.0, None], [None, 0.0], [1.0, 0.0], "positive evidence"),
        ([math.log(0.5)] * 2, [None, 0.0], [0.5, 0.5], "joint support"),
        ([0.0, None], [], [1.0, 0.0], "log_likelihood"),
        ([0.0, None], [0.1, 0.0], [1.0, 0.0], "log_likelihood"),
        ([0.0, None], [float("nan"), 0.0], [1.0, 0.0], "log_likelihood"),
        ([0.0, None], [float("inf"), 0.0], [1.0, 0.0], "log_likelihood"),
        ([0.0, None], [float("-inf"), 0.0], [1.0, 0.0], "log_likelihood"),
        ([0.0, None], [0.0], [1.0, 0.0], "lengths"),
        ([0.0, None], [0.0, 0.0], [0.4, 0.4], "sum to one"),
        ([-1e308, 0.0], [-1e308, 0.0], [1.0, 0.0], "finite floating-point range"),
    ],
)
def test_log_domain_rejects_invalid_models(prior, likelihood, q, reason):
    with pytest.raises(ProbabilityError, match=reason):
        free_energy_log(prior, likelihood, q)


def test_linear_interface_explains_unrepresentable_evidence():
    with pytest.raises(ProbabilityError, match="use free_energy_log"):
        free_energy([1e-300, 1.0], [1e-300, 0.0], [1.0, 0.0])


@pytest.mark.parametrize("states", [2, 3, 8])
def test_seeded_models_match_independent_decimal_arithmetic(states):
    rng = random.Random(20261021 + states)
    for _ in range(12):
        raw_prior = [rng.uniform(0.01, 1.0) for _ in range(states)]
        raw_q = [rng.uniform(0.01, 1.0) for _ in range(states)]
        prior = [p / math.fsum(raw_prior) for p in raw_prior]
        q = [p / math.fsum(raw_q) for p in raw_q]
        likelihood = [rng.uniform(0.01, 1.0) for _ in range(states)]
        with localcontext() as context:
            context.prec = 80
            joint = [Decimal(p) * Decimal(l) for p, l in zip(prior, likelihood, strict=True)]
            evidence = sum(joint)
            energy = sum(Decimal(v) * (Decimal(v).ln() - j.ln())
                         for v, j in zip(q, joint, strict=True))
            exact = [float(p / evidence) for p in joint]
        linear = free_energy(prior, likelihood, q)
        logarithmic = free_energy_log([math.log(p) for p in prior],
                                      [math.log(p) for p in likelihood], q)
        assert linear["free_energy"] == pytest.approx(float(energy), abs=1e-12)
        assert linear["exact_posterior"] == pytest.approx(exact)
        assert logarithmic["free_energy"] == linear["free_energy"]
        assert abs(linear["identity_residual"]) < 1e-12


@pytest.mark.parametrize("logarithmic", [False, True])
def test_real_model_json_has_a_strict_declared_schema(tmp_path, logarithmic):
    document = (
        {"log_prior": [math.log(0.5)] * 2, "log_likelihood": [-1000.0, -1001.0]}
        if logarithmic else {"prior": [0.5, 0.5], "likelihood": [0.8, 0.2]}
    )
    document["posterior"] = [0.5, 0.5]
    path = tmp_path / "model.json"
    path.write_text(json.dumps(document))
    result = evaluate_model(path, logarithmic=logarithmic)
    assert result["free_energy"] == pytest.approx(1000.5 if logarithmic else math.log(2.5))
    document["extra"] = 1
    path.write_text(json.dumps(document))
    with pytest.raises(ValueError, match="extra_forbidden"):
        evaluate_model(path, logarithmic=logarithmic)

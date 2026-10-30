"""Pure source/model controls: these tests never invoke native tools."""

from decimal import Decimal
from fractions import Fraction

import pytest
from pydantic import ValidationError

from rikishi.bridge_models import BridgeError
from rikishi.bridge_study import (
    cases,
    catalog,
    decimal_reference,
    derive_source_claims,
    exact_posterior,
    extension,
    mass_facts,
    numerical,
    probabilities,
)
from rikishi.inference_compiler import Compiler
from rikishi.inference_models import InferenceError
from rikishi.kif import parse
from rikishi.portable_inputs import PortableInputs


def test_exact_rational_oracles_and_bool_order() -> None:
    study = catalog()
    expected = {
        "uniform-prior": (Fraction(1, 2), (Fraction(1, 4), Fraction(3, 4))),
        "biased-prior": (Fraction(2, 3), (Fraction(1, 4), Fraction(3, 4))),
        "exact-candidate": (Fraction(7, 12), (Fraction(6, 7), Fraction(1, 7))),
    }
    assert {w.id: exact_posterior(w) for w in study.witnesses} == expected
    assert len({w.entities.model for w in study.witnesses}) == len(study.witnesses)


@pytest.mark.parametrize("values", [
    ("0", "1"), ("-1/2", "3/2"), ("2/4", "1/2"), ("1/0", "1/2"),
    ("nan", "1/2"), ("0.5", "1/2"),
])
def test_mass_parser_rejects_real_invalid_inputs(values: tuple[str, str]) -> None:
    with pytest.raises(BridgeError):
        probabilities(values)


def test_rational_data_not_mutable_at_report_boundary() -> None:
    witness = catalog().witnesses[0]
    with pytest.raises(ValidationError):
        witness.id = "changed"


def test_python_results_agree_with_independent_exact_input_reference() -> None:
    study = catalog()
    rows = numerical(study)
    assert len(rows) == len(study.witnesses)
    assert all(row.passed and row.max_reference_error < 1e-12 for row in rows)
    assert all(row.reconstruction_residuals == ("0", "0") for row in rows)
    biased = next(row for row in rows if row.witness_id == "biased-prior")
    assert biased.result.kl_to_posterior > 0.3
    assert biased.result.free_energy > biased.result.surprise
    exact = next(row for row in rows if row.witness_id == "exact-candidate")
    assert abs(exact.result.kl_to_posterior) < 1e-12
    assert abs(Decimal(exact.reference.identity_residual)) < Decimal("1e-70")


def test_decimal_reference_preserves_rational_input_beyond_float_precision() -> None:
    study = catalog()
    reference = decimal_reference(study.witnesses[1], study.decimal_precision)
    assert reference.evidence.startswith("0.666666666666666666666666666666666")
    assert abs(Decimal(reference.exact_posterior[0]) - Decimal("0.25")) < Decimal("1e-70")


def test_complete_source_claims_and_strict_problem_compilation(portable_inputs: PortableInputs) -> None:
    study = catalog()
    source = portable_inputs.merge_bytes
    claims = derive_source_claims(study, source)
    original = {f.line: f for f in parse(source.decode())}
    assert all(c.raw_kif == original[c.line].text
               and c.end_line == c.line + c.raw_kif.count("\n") for c in claims)
    generated = cases(study, claims)
    assert len(generated) == len(study.scenarios) * 5
    assert len({case.id for case in generated}) == len(generated)
    assert {case.group for case in generated} == {s.id for s in study.scenarios}
    context = next(c for c in claims if c.line == 489)
    with pytest.raises(InferenceError):
        Compiler().formula(context.raw_kif)


def test_rehashed_source_drift_is_rejected(portable_inputs: PortableInputs) -> None:
    study = catalog()
    source = portable_inputs.merge_bytes
    with pytest.raises(BridgeError, match="SUMO bytes"):
        derive_source_claims(study, source.replace(b"(subclass Proposition Abstract)",
                                                b"(subclass Proposition Process)", 1))


def test_every_problem_binds_same_rational_witness_manifest(portable_inputs: PortableInputs) -> None:
    study = catalog()
    claims = derive_source_claims(study, portable_inputs.merge_bytes)
    generated = cases(study, claims)
    for witness in study.witnesses:
        scenario_ids = {s.id for s in study.scenarios if s.witness_id == witness.id}
        formulas = [Compiler().formula(fact) for fact in mass_facts(witness)]
        assert all(all(formula in case.problem for formula in formulas)
                   for case in generated if case.group in scenario_ids)
    local = extension(study)
    assert len(list(parse(local))) == len(set(local.splitlines()))


def test_existential_result_scenario_does_not_assert_named_output() -> None:
    study = catalog()
    for witness in study.witnesses:
        scenario = next(s for s in study.scenarios if s.id == witness.id + "-result-existence")
        named = f"(result {witness.entities.calculation} {witness.entities.result})"
        assert scenario.negative_query == named
        assert scenario.removed_selection == 0 and scenario.selections[0].line == 16326
        assert all(named not in assumption and assumption not in study.local_rules
                   for assumption in scenario.assumptions)


def test_removed_source_premise_really_changes_selected_kernel(portable_inputs: PortableInputs) -> None:
    study = catalog()
    claims = derive_source_claims(study, portable_inputs.merge_bytes)
    generated = cases(study, claims)
    for scenario in study.scenarios:
        assert scenario.removed_selection is not None
        selection = scenario.selections[scenario.removed_selection]
        source = next(c for c in claims if c.line == selection.line)
        formula = Compiler().formula(source.raw_kif, selection.predicate_bindings)
        positive = next(c.problem for c in generated if c.group == scenario.id and c.kind == "positive")
        removed = next(c.problem for c in generated if c.group == scenario.id and c.kind == "removed-premise")
        assert any(line.endswith(f",axiom,{formula}).") for line in positive.splitlines())
        assert not any(line.endswith(f",axiom,{formula}).") for line in removed.splitlines())

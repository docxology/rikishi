import json
from decimal import Decimal
from hashlib import sha256

import pytest

from rikishi.alignment import decimal_reference, numerical_matrix, run_alignment
from rikishi.competency import (
    AlignmentError,
    derive_source_claims,
    extension_text,
    load_study,
    logical_problem,
)
from rikishi.portable_inputs import PortableInputs
from rikishi.sumo_demonstrations import SumoReport


@pytest.fixture(scope="module")
def matrix():
    return numerical_matrix()


@pytest.fixture(scope="module")
def claims(portable_inputs: PortableInputs):
    study = load_study()
    return derive_source_claims(study, portable_inputs.source_report, portable_inputs.workbook_bytes)


def test_seeded_matrix_has_all_declared_models_and_candidates(matrix):
    study = load_study()
    expected = {(d, m, c) for d in study.numerical.dimensions
                for m in range(study.numerical.models_per_dimension)
                for c in study.numerical.candidates}
    assert {(r.dimension, r.model_index, r.candidate) for r in matrix.rows} == expected
    assert all(r.passed for r in matrix.rows)
    assert max(r.max_reference_error for r in matrix.rows) < 1e-12
    assert len({r.input.id for r in matrix.rows}) == len(matrix.rows)
    assert all(1 <= w <= 100 for r in matrix.rows for w in r.prior_weights)


def test_decimal_identity_and_controls_are_independent(matrix):
    for row in matrix.rows:
        reference = row.reference
        assert abs(Decimal(reference.free_energy) + Decimal(reference.log_evidence)
                   - Decimal(reference.kl_to_posterior)) < Decimal("1e-12")
        assert row.permutation_max_error <= float(row.tolerance)
        assert row.rescaling_max_error <= float(row.tolerance)


def test_boundary_results_preserve_underflow_and_exact_zero(matrix):
    rows = {row.input.id: row for row in matrix.extremes}
    assert all(row.passed for row in rows.values())
    small = rows["positive-evidence-underflow"].result
    assert small.evidence is None
    assert small.free_energy == 1000.5
    assert small.log_evidence < -1000
    posterior = rows["positive-posterior-underflow"].result
    assert posterior.exact_posterior[0] == 0.0
    assert posterior.log_exact_posterior[0] is not None
    assert posterior.posterior_underflow_indices == [0]
    zero = rows["structural-zero"].result
    assert zero.log_exact_posterior[0] is None
    assert zero.posterior_underflow_indices == []


def test_invalid_inputs_fail_for_real_contract_errors(matrix):
    assert len(matrix.invalid) == len(load_study().numerical.invalid)
    assert all(case.rejected and case.error for case in matrix.invalid)
    errors = {case.id: case.error for case in matrix.invalid}
    assert "positive evidence" in errors["impossible-evidence"]
    assert "support" in errors["invalid-support"]
    assert "lengths" in errors["dimension"]


def test_authority_rejects_modified_parameters(tmp_path):
    authority = load_study().model_dump(mode="json")
    authority["numerical"]["ordinary_tolerance"] = "1"
    path = tmp_path / "study.json"
    path.write_text(json.dumps(authority))
    with pytest.raises(AlignmentError, match="authority"):
        load_study(path)


def test_source_claims_keep_complete_formulas_senses_and_blanks(claims):
    study = load_study()
    assert [c.line for c in claims.citations] == study.citation_lines
    assert {s.row for s in claims.senses} == set(study.workbook_rows)
    assert claims.sheet.endswith(" ")
    assert all(claims.cells[f"{c}431"] == "" for c in "HIJKL")
    assert "subclass of Process" in claims.cells["I190"]
    assert all(sha256(c.raw_kif.encode()).hexdigest() == c.sha256 for c in claims.citations)
    assert any(c.end_line > c.line and "=>" in c.raw_kif for c in claims.citations)


@pytest.mark.parametrize("mutation", ["bytes", "path", "commit", "workbook"])
def test_source_binding_rejects_rehashed_false_sources(portable_inputs: PortableInputs, mutation):
    study = load_study()
    source = portable_inputs.source_report
    workbook = portable_inputs.workbook_bytes
    data = source.model_dump(mode="json")
    match mutation:
        case "bytes":
            data["source"]["text"] += "\n; a rehashed false source\n"
            data["source"]["sha256"] = sha256(data["source"]["text"].encode()).hexdigest()
        case "path":
            data["source"]["path"] = "invented/Merge.kif"
        case "commit":
            data["source"]["commit"] = "a" * 40
        case "workbook":
            workbook += b"mutation"
    with pytest.raises(ValueError):
        derive_source_claims(study, SumoReport.model_validate(data), workbook)


def test_declared_problems_keep_consistency_and_polarity_cases(claims):
    study = load_study()
    problems = {case.id: logical_problem(study, claims, case) for case in study.cases}
    assert len(problems) == 12
    assert "conjecture" not in problems["background"]
    assert "conjecture,~instance(model,physical)" in problems["model-not-physical"]
    assert "instance(witness,double_class)" not in problems["empty-double-class"]
    assert "instance(witness,double_class)" in problems["inhabited-double-class"]
    assert "model = execution" in problems["alias"]
    assert "abstract_counterpart(model,execution)" in problems["background"]
    assert "Reasoning" not in extension_text(study)


def test_problem_builder_refuses_unsupported_local_expression(claims):
    study = load_study().model_copy(update={"local_formulas": ["(equal X Y)"]})
    with pytest.raises(AlignmentError, match="Unsupported expression"):
        logical_problem(study, claims, study.cases[0])


def test_runner_rejects_unsupported_study_before_execution(project_root, tmp_path):
    study = load_study().model_copy(update={"study_id": "other"})
    with pytest.raises(AlignmentError, match="Unsupported study"):
        run_alignment(project_root, tmp_path / "unused", study=study)


def test_runner_refuses_output_outside_repository(project_root, tmp_path):
    with pytest.raises(ValueError):
        run_alignment(project_root, tmp_path / "unused")


def test_decimal_reference_keeps_positive_evidence_below_float_range():
    study = load_study()
    reference = decimal_reference(study.numerical.extremes[0], study.numerical.decimal_precision)
    assert Decimal(reference.evidence) > 0
    assert float(Decimal(reference.evidence)) == 0
    assert abs(Decimal(reference.free_energy) - Decimal("1000.5")) < Decimal("1e-15")

from hashlib import sha256

import pytest

from rikishi.inference_models import InferenceError
from rikishi.inference_study import cases, catalog, derive_source_claims, load_study, study_sha256
from rikishi.runtime_tptp import parse_tptp


def test_source_bound_catalog_generates_distinct_controlled_problems(portable_inputs):
    study = catalog()
    claims = derive_source_claims(study, portable_inputs.merge_bytes)
    generated = cases(study, claims)
    assert len(study.scenarios) >= 24
    assert len({s.category for s in study.scenarios}) >= 8
    assert len(generated) == len(study.scenarios) * 5
    assert len({case.id for case in generated}) == len(generated)
    assert {c.expected for c in generated} == {
        "Theorem", "CounterSatisfiable", "Satisfiable", "Unsatisfiable"}
    assert len({c.line for c in claims}) == len(claims)
    for claim in claims:
        assert claim.sha256 == sha256(claim.raw_kif.encode()).hexdigest()
        assert claim.end_line == claim.line + claim.raw_kif.count("\n")
        assert claim.source_path == study.source_path
    for case in generated:
        statements = parse_tptp(case.problem)
        assert statements
        if case.kind in {"background", "refutation"}:
            assert all(",axiom," in statement.text for statement in statements)
        else:
            assert ",conjecture," in statements[-1].text
    for offset in range(0, len(generated), 5):
        group = generated[offset:offset + 5]
        assert group[0].kind == "background"
        assert len(parse_tptp(group[3].problem)) == len(parse_tptp(group[1].problem)) - 1
        assert group[3].problem != group[1].problem


def test_complete_source_tampering_and_invalid_source_selector_fail(portable_inputs):
    study = catalog()
    with pytest.raises(InferenceError, match="Complete source"):
        derive_source_claims(study, portable_inputs.merge_bytes + b"\n; altered\n")
    first = study.scenarios[0]
    changed = first.model_copy(update={"selections": [first.selections[0].model_copy(update={"line": 1})]})
    invalid = study.model_copy(update={"scenarios": [changed]})
    with pytest.raises(InferenceError, match="complete source formula"):
        derive_source_claims(invalid, portable_inputs.merge_bytes)


@pytest.mark.parametrize("changes", [
    {"removed_selection": None, "removed_assumption": None},
    {"removed_selection": 0, "removed_assumption": 0},
    {"removed_selection": 999},
    {"removed_selection": None, "removed_assumption": 999},
    {"removed_selection": -1},
])
def test_invalid_premise_mutation_is_rejected(changes):
    study = catalog()
    invalid = study.scenarios[0].model_copy(update=changes)
    with pytest.raises(InferenceError, match="remove|Removed"):
        cases(study.model_copy(update={"scenarios": [invalid]}), [])


def test_study_file_and_digest_require_packaged_authority(tmp_path):
    study = catalog()
    path = tmp_path / "study.json"
    path.write_text(study.model_dump_json())
    assert load_study(path) == study
    assert study_sha256(study) == sha256(study.model_dump_json().encode()).hexdigest()
    path.write_text(study.model_copy(update={"semantic_scope": "invented equivalence"}).model_dump_json())
    with pytest.raises(InferenceError, match="packaged authority"):
        load_study(path)

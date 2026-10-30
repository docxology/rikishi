import pytest

from rikishi.inference_compiler import Compiler
from rikishi.inference_models import InferenceError
from rikishi.kif import KifError
from rikishi.runtime_tptp import parse_tptp


@pytest.mark.parametrize("formula", [
    "(instance StudyWitness Human)",
    "(=> (and (subclass ?X ?Y) (instance ?Z ?X)) (instance ?Z ?Y))",
    "(=> (disjoint ?A ?B) (not (exists (?X) (and (instance ?X ?A) (instance ?X ?B)))))",
    "(forall (?X ?Y) (or (equal ?X ?Y) (not (equal ?X ?Y))))",
    "(<=> (part ?A ?B) (and (component ?A ?B) (not (equal ?A ?B))))",
    "(domain parent 1 Organism)",
    "(and (p ?X) (exists (?X) (q ?X)) (r ?X))",
])
def test_compiled_formulas_are_complete_tptp(formula):
    compiled = Compiler().formula(formula)
    statements = parse_tptp(f"fof(selected,axiom,{compiled}).")
    assert len(statements) == 1
    assert "?X" not in compiled


def test_predicate_specialization_keeps_object_symbol_separate():
    compiler = Compiler()
    formula = compiler.formula(
        "(=> (instance ?REL SymmetricRelation) (forall (?A ?B) (=> (?REL ?A ?B) (?REL ?B ?A))))",
        {"?REL": "sibling"})
    assert "c_7369626c696e67" in formula
    assert "r_7369626c696e67" in formula
    assert "V3f52454c" not in formula
    assert compiler.arities == {"instance": 2, "sibling": 2}


def test_hex_names_are_injective_and_free_variables_are_closed():
    compiler = Compiler()
    formula = compiler.formula("(and (a_b ?X) (ab ?Y) (a-b ?X))")
    assert "![V3f58,V3f59]" in formula
    assert all(name in formula for name in ("r_615f62", "r_6162", "r_612d62"))
    quantified = compiler.formula("(exists (?X) (a_b ?X))")
    assert "!" not in quantified


@pytest.mark.parametrize("formula", [
    "", "(p a) (q b)", "(?REL a b)", "(p @ROW)", "(p (Fn a))", '(p "text")',
    "(p -3)", "(p 1.5)", "(p a:b)", "(p)", "(not (p a) (q a))", "(=> (p a))",
    "(and (p a))", "(or)", "(equal a)", "(forall ?X (p ?X))", "(forall (?X))",
    "(forall (a) (p a))", "(exists (?X ?X) (p ?X))", "(p a", "(p ())",
    "((p a) b)", "(forall (?X) ?X)",
])
def test_unsupported_syntax_fails_explicitly(formula):
    with pytest.raises((InferenceError, KifError)):
        Compiler().formula(formula)


@pytest.mark.parametrize("bindings", [
    {"bad": "part"}, {"?REL": "?OTHER"}, {"?REL": "not:a:symbol"},
    {"?OTHER": "part"},
])
def test_invalid_or_unused_specializations_are_rejected(bindings):
    with pytest.raises(InferenceError):
        Compiler().formula("(part a b)", bindings)


def test_quantified_specialization_and_inconsistent_arity_are_rejected():
    with pytest.raises(InferenceError, match="specialized"):
        Compiler().formula("(forall (?REL) (?REL a b))", {"?REL": "part"})
    compiler = Compiler()
    compiler.formula("(part a b)")
    with pytest.raises(InferenceError, match="arity"):
        compiler.formula("(part a b c)")

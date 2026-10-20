import pytest

from rikishi.kif import KifError, String, parse, symbols


def test_multiline_strings_comments_and_provenance():
    text = '; ignored\n(subclass Human Animal)\n(documentation Human EnglishLanguage "a; (person)\nwith \\"quotes\\"")'
    formulas = list(parse(text))
    assert formulas[0].line == 2
    assert formulas[0].text == "(subclass Human Animal)"
    assert formulas[1].expression[-1] == String('a; (person)\nwith "quotes"')
    assert formulas[1].line == 3


@pytest.mark.parametrize("text", [")", "(p x", '"outside"', "atom", "()", '(p "x', '(p "x\\'])
def test_malformed_input_rejected(text):
    with pytest.raises(KifError):
        list(parse(text, "broken.kif"))


def test_nested_formulas_exclude_literals_variables_and_logic():
    formula = next(parse("(forall (?X) (=> (instance ?X Human) (equal (AgeFn ?X) 3.2)))"))
    assert symbols(formula.expression) == {"instance", "Human", "AgeFn"}
    assert symbols(String("Human")) == set()
    assert list(parse("; comment without newline")) == []


def test_row_variables_and_strings_are_not_terms():
    assert symbols(("Predicate", "@ROW", String("label"), "-2")) == {"Predicate"}

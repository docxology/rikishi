"""Pure structural TPTP parser checks, independent of installed provers and files."""

from dataclasses import FrozenInstanceError

import pytest

from rikishi.runtime_tptp import TPTPError, TPTPStatement, parse_tptp


def test_same_line_includes_and_complete_multiline_statements() -> None:
    fact = "fof(fact,axiom,\n    p)."
    include = "include('background.p')."
    goal = "fof(goal,conjecture,\n    p)."
    assert parse_tptp(f"\t{fact} {include}\t{goal}") == [
        TPTPStatement(fact, "fof", "fact", None),
        TPTPStatement(include, "include", None, "background.p"),
        TPTPStatement(goal, "fof", "goal", None),
    ]


@pytest.mark.parametrize("kind", ["fof", "cnf", "tff", "thf"])
def test_supported_formula_kinds_with_nested_content(kind: str) -> None:
    text = f"{kind} ( name , axiom , ! [X:$i] : (p(X) => q([a,b],f(X))) )."
    assert parse_tptp(text) == [TPTPStatement(text, kind, "name", None)]


@pytest.mark.parametrize(
    ("name", "decoded"),
    [
        ("name_12", "name_12"),
        ("a", "a"),
        ("'name_12'", "name_12"),
        ("'123'", "123"),
        ("123", "123"),
        ("0", "0"),
        ("+12", "+12"),
        ("-12", "-12"),
        (r"'a\\b.%'", "a\\b.%"),
        ("'a b,(c)[d]'", "a b,(c)[d]"),
    ],
)
def test_formula_names_decode_quoted_atoms(name: str, decoded: str) -> None:
    statement = parse_tptp(f"fof(/* name */ {name} % keep comment\n,axiom,p).")[0]
    assert statement.name == decoded
    assert statement.include_path is None


@pytest.mark.parametrize(
    "text",
    [
        "include('background.p').",
        "include ( /* comment */ 'background.p' /* comment */ ).",
        "include\n(\n% before path\n'background.p'\n% after path\n)\n.",
        "include/* between tokens */('background.p')/* before dot */.",
    ],
)
def test_include_layout_and_comments(text: str) -> None:
    assert parse_tptp(text) == [TPTPStatement(text, "include", None, "background.p")]


def test_include_path_percent_and_dots_remain_literal() -> None:
    text = "include('dir.%/file.p')."
    assert parse_tptp(text)[0].include_path == "dir.%/file.p"


@pytest.mark.parametrize("path", [r"a\\b.p", r"a\\\\b.p", r"a\'b.p"])
def test_include_path_escapes_fail_closed(path: str) -> None:
    with pytest.raises(TPTPError, match="backslashes in include paths"):
        parse_tptp(f"include('{path}').")


@pytest.mark.parametrize("name,decoded", [
    ("plain", "plain"), ("'plain'", "plain"), ("'quoted name'", "quoted name"),
    (r"'back\\slash'", "back\\slash"),
    ("123", "123"), ("'123'", "123"),
])
def test_file_source_names_share_formula_name_parser(name: str, decoded: str) -> None:
    source = f"fof(derived,axiom,p,file /* source */ ('source.p', /* leaf */ {name}))."
    assert parse_tptp(source)[0].source_name == decoded


def test_nested_file_term_is_not_an_input_leaf() -> None:
    text = "fof(derived,plain,p,inference(rule,[file('fake.p',fake)],[earlier]))."
    assert parse_tptp(text)[0].source_name is None


@pytest.mark.parametrize("source", ["file", "file('a')", "file('a',x,y)",
                                    "file(a,x)", "file('a' 'b',x)", "file('a',Upper)"])
def test_unsupported_file_source_annotations_fail_closed(source: str) -> None:
    with pytest.raises(TPTPError):
        parse_tptp(f"fof(derived,axiom,p,{source}).")


def test_quoted_content_does_not_create_includes_or_statement_boundaries() -> None:
    formula = r'''fof('a%.name',axiom,p('include(\'fake.p\').% /* [)',
        "include('fake.p').% /* ] ) \" \\" )).'''
    assert parse_tptp(formula) == [TPTPStatement(formula, "fof", "a%.name", None)]


def test_comments_with_quotes_dots_and_nesting_are_opaque() -> None:
    formula = (
        "fof/* ' broken quote ) [ . include('fake.p'). */(fact,axiom,\n"
        "  % \" unmatched quote ] ) . include('also-fake.p').\n"
        "  p /* . ) [ */)."
    )
    assert parse_tptp("% ignored include('leading.p').\n" + formula) == [
        TPTPStatement(formula, "fof", "fact", None)
    ]


@pytest.mark.parametrize("newline", ["\n", "\r", "\r\n"])
def test_line_comments_end_at_each_line_ending(newline: str) -> None:
    text = f"% comment{newline}fof(a,axiom,p).% trailing{newline}include('b.p')."
    assert [statement.kind for statement in parse_tptp(text)] == ["fof", "include"]


@pytest.mark.parametrize("text", ["", " \t\r\n", "% comment at EOF", "/* comment */ % tail"])
def test_empty_or_comment_only_input(text: str) -> None:
    assert parse_tptp(text) == []


def test_formula_annotations_and_decimal_dots_remain_intact() -> None:
    text = (
        "fof(a,axiom,p(1.25,-2.5E+4),"
        "inference(rule,[status(thm)],[file('some.file.p',original)]),[description('a.b')])."
    )
    assert parse_tptp(text)[0].text == text


@pytest.mark.parametrize(
    "text",
    [
        "include('background.p',[a]).",
        "include('background.p',[]).",
        "include('background.p', /* selection */ [a,b]).",
        "include('background.p',a).",
        'include("background.p").',
        "include(background).",
        "include().",
        "include('').",
        "include('a' 'b').",
        r"include('bad\q.p').",
        "include('a.p') include('b.p').",
        "include('a.p',).",
        "input_formula(a,axiom,p).",
        "tpi(a,axiom,p).",
        "tcf(a,axiom,p).",
        "unknown(a).",
        "FOF(a,axiom,p).",
    ],
)
def test_unsupported_directives_fail_closed(text: str) -> None:
    with pytest.raises(TPTPError):
        parse_tptp(text)


@pytest.mark.parametrize(
    "text",
    [
        ".",
        "fof a,axiom,p).",
        "fof(a,axiom,p)",
        "fof(a,axiom,p). garbage",
        "fof(a,axiom,p)..",
        "fof(a,axiom,p). include('a.p'",
        "fof(a,axiom,p). /* unterminated",
        "/* unterminated",
        "fof(a,axiom,p /* unterminated).",
        "fof(a,axiom,'unterminated).",
        'fof(a,axiom,"unterminated).',
        "fof(a,axiom,'escaped closing quote\\').",
        "fof(a,axiom,'trailing backslash\\",
        "fof(a,axiom,p([a,b)).",
        "fof(a,axiom,p((a])).",
        "fof(a,axiom,p]).",
        "fof(a,axiom,p(]).",
        "fof(a,axiom,p).)",
        "fof(a,axiom,p.",
        "fof(a,axiom,p)extra.",
        "fof(a,axiom,p) . /* comment */ [",
        "fof(,axiom,p).",
        "fof(a,,p).",
        "fof(a,axiom,/* empty */).",
        "fof(a,axiom).",
        "fof(a,axiom,p,source,info,extra).",
    ],
)
def test_malformed_structure_fails_closed(text: str) -> None:
    with pytest.raises(TPTPError):
        parse_tptp(text)


@pytest.mark.parametrize(
    "name", ["Upper", "_name", "01", "1.5", "a-b", "'a' suffix", '"name"', "''", r"'bad\q'", r"'escaped\'name'"]
)
def test_invalid_formula_names_fail_closed(name: str) -> None:
    with pytest.raises(TPTPError):
        parse_tptp(f"fof({name},axiom,p).")


def test_deep_balanced_nesting_uses_no_python_recursion() -> None:
    formula = "fof(deep,axiom," + "([" * 2000 + "p" + "])" * 2000 + ")."
    assert parse_tptp(formula)[0].text == formula


@pytest.mark.parametrize("attribute", ["text", "kind", "name", "include_path"])
def test_statement_records_are_frozen(attribute: str) -> None:
    statement = parse_tptp("fof(a,axiom,p).")[0]
    with pytest.raises(FrozenInstanceError):
        setattr(statement, attribute, "changed")


def test_errors_are_value_errors_with_location() -> None:
    with pytest.raises(TPTPError) as failure:
        parse_tptp("fof(a,axiom,p).\nunknown().")
    assert isinstance(failure.value, ValueError)
    assert failure.value.offset == 16
    assert "unsupported TPTP statement kind" in str(failure.value)

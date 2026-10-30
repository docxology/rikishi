from __future__ import annotations

from hashlib import sha256
from importlib.resources import files
from pathlib import Path

from rikishi.inference_compiler import Compiler
from rikishi.inference_models import (
    CaseKind,
    InferenceCase,
    InferenceError,
    InferenceStudy,
    Polarity,
    Scenario,
    SourceClaim,
)
from rikishi.kif import parse
from rikishi.runtime_artifacts import read_regular


def catalog() -> InferenceStudy:
    study = InferenceStudy.model_validate_json(
        files("rikishi").joinpath("data/inference-study-v1.json").read_bytes())
    identifiers = [s.id for s in study.scenarios]
    if not identifiers or len(set(identifiers)) != len(identifiers):
        raise InferenceError("Study requires unique scenario identifiers")
    for scenario in study.scenarios:
        _check_mutation(scenario)
    return study


def _check_mutation(scenario: Scenario) -> None:
    selected = scenario.removed_selection
    assumed = scenario.removed_assumption
    if (selected is None) == (assumed is None):
        raise InferenceError("Each scenario must remove exactly one selected or assumed premise")
    if selected is not None and not 0 <= selected < len(scenario.selections):
        raise InferenceError("Removed selection is outside the scenario")
    if assumed is not None and not 0 <= assumed < len(scenario.assumptions):
        raise InferenceError("Removed assumption is outside the scenario")


def derive_source_claims(study: InferenceStudy, source: bytes) -> list[SourceClaim]:
    if sha256(source).hexdigest() != study.source_sha256:
        raise InferenceError("Complete source file differs from the pinned study")
    formulas = {f.line: f for f in parse(source.decode("utf-8"), study.source_path)}
    selected_lines = sorted({s.line for scenario in study.scenarios for s in scenario.selections})
    claims: list[SourceClaim] = []
    for line in selected_lines:
        if line not in formulas:
            raise InferenceError(f"Selected line is not a complete source formula: {line}")
        formula = formulas[line]
        claims.append(SourceClaim(
            source_path=study.source_path, line=line,
            end_line=line + formula.text.count("\n"), raw_kif=formula.text,
            sha256=sha256(formula.text.encode()).hexdigest()))
    return claims


def study_sha256(study: InferenceStudy) -> str:
    return sha256(study.model_dump_json().encode()).hexdigest()


def _problem(scenario: Scenario, claims: dict[int, SourceClaim], kind: CaseKind) -> str:
    compiler = Compiler()
    axioms: list[str] = []
    for index, selection in enumerate(scenario.selections):
        if kind == "removed-premise" and index == scenario.removed_selection:
            continue
        axioms.append(compiler.formula(claims[selection.line].raw_kif,
                                       selection.predicate_bindings))
    for index, assumption in enumerate(scenario.assumptions):
        if kind == "removed-premise" and index == scenario.removed_assumption:
            continue
        axioms.append(compiler.formula(assumption))
    statements = [f"fof(premise_{i},axiom,{formula})." for i, formula in enumerate(axioms)]
    if kind == "refutation":
        statements.append(f"fof(negated_query,axiom,{compiler.formula('(not ' + scenario.query + ')')}).")
    elif kind != "background":
        query = scenario.negative_query if kind == "negative" else scenario.query
        statements.append(f"fof(question,conjecture,{compiler.formula(query)}).")
    return "\n".join(statements) + "\n"


def cases(study: InferenceStudy, claims: list[SourceClaim]) -> list[InferenceCase]:
    source = {c.line: c for c in claims}
    generated: list[InferenceCase] = []
    kinds: tuple[tuple[CaseKind, Polarity], ...] = (
        ("background", "Satisfiable"), ("positive", "Theorem"),
        ("negative", "CounterSatisfiable"), ("removed-premise", "CounterSatisfiable"),
        ("refutation", "Unsatisfiable"))
    for scenario in study.scenarios:
        _check_mutation(scenario)
        for kind, expected in kinds:
            generated.append(InferenceCase(
                id=f"{scenario.id}-{kind}", group=scenario.id, kind=kind,
                expected=expected, problem=_problem(scenario, source, kind)))
    return generated


def load_study(path: Path) -> InferenceStudy:
    study = catalog()
    if InferenceStudy.model_validate_json(read_regular(path)) != study:
        raise InferenceError("Retained study differs from the supported packaged authority")
    return study

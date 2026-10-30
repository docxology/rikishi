"""Source-bound SUMO examples and portable replay, without general ontology inference."""

import re
from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Final, Literal, TypedDict

from pydantic import BaseModel, ConfigDict, JsonValue

from rikishi.kif import Formula, parse, symbols
from rikishi.ontology import OntologyIndex
from rikishi.projection import taxonomy_problem
from rikishi.runtime import prove
from rikishi.runtime_artifacts import checked_source_path, read_regular
from rikishi.source_audit import audit_sources

_TERMS: Final = ("Physical", "Abstract", "Proposition", "Process", "agent", "ProbabilityFn")
_SCOPE: Final = (
    "Selected SUMO source assertions and restricted top-level binary-edge projection; "
    "nested formulas retain their context. No ATP proof, consistency claim, or inference "
    "from graph absence. Portable replay checks retained bytes, not Git authenticity."
)
_PATTERNS: Final = {
    "hierarchy": (("partition", "Entity", "Physical", "Abstract"),
                  ("subclass", "Physical", "Entity"), ("subclass", "Abstract", "Entity"),
                  ("subclass", "Process", "Physical"), ("subclass", "Proposition", "Abstract")),
    "typing": (("subclass", "Process", "Physical"), ("instance", "agent", "CaseRole"),
               ("instance", "ProbabilityFn", "UnaryFunction")),
    "agent_signature": (("domain", "agent", "1", "Process"),
                        ("domain", "agent", "2", "AutonomousAgent")),
    "probability_signature": (("instance", "ProbabilityFn", "UnaryFunction"),
                              ("domain", "ProbabilityFn", "1", "Formula"),
                              ("range", "ProbabilityFn", "RealNumber")),
}


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class FrozenSource(_Frozen):
    path: str
    ontology_path: Literal["Merge.kif"]
    commit: str
    clean: bool | None
    text: str
    sha256: str


class FormulaCitation(_Frozen):
    predicate: str
    selected_terms: list[str]
    line: int
    end_line: int
    raw_kif: str
    sha256: str
    indexed_binary_edge: bool


class SourceObservations(_Frozen):
    source_formulas: int
    projected_binary_edges: int
    cited_formulas: int


class SumoReport(_Frozen):
    schema_version: Literal[1] = 1
    scope: str
    source: FrozenSource
    selected_terms: list[str]
    cases: dict[str, list[FormulaCitation]]
    observations: SourceObservations


class SumoSubstitutions(TypedDict):
    SUMO_SOURCE_PATH: str
    SUMO_SOURCE_COMMIT: str
    SUMO_SOURCE_SHA256: str
    SUMO_SOURCE_FORMULAS: str
    SUMO_PROJECTED_BINARY_EDGES: str
    SUMO_CITED_FORMULAS: str
    SUMO_HIERARCHY_KIF: str
    SUMO_TYPING_KIF: str
    SUMO_AGENT_SIGNATURE_KIF: str
    SUMO_PROBABILITY_SIGNATURE_KIF: str
    SUMO_NESTED_FORMULA_KIF: str


class TaxonomyRun(TypedDict):
    status: str
    proved: bool
    problem: str
    capture: str
    problem_sha256: str


class TaxonomyDemonstration(TypedDict):
    scope: str
    source_commit: str
    source_file_sha256: str
    subject: str
    positive_target: str
    negative_target: str
    source_report: str
    projection_source_sha256: str
    positive: TaxonomyRun
    negative: TaxonomyRun


def _relative(path: str) -> str:
    candidate = PurePosixPath(path)
    if candidate.is_absolute() or ".." in candidate.parts or str(candidate) != path or path == ".":
        message = f"Expected a normalized root-relative path: {path}"
        raise ValueError(message)
    return path


def _binary(formula: Formula) -> bool:
    expression = formula.expression
    names = symbols(expression)
    return (len(expression) == 3 and all(isinstance(x, str) for x in expression)
            and expression[1] in names and expression[2] in names)


def _one(formulas: list[Formula]) -> Formula:
    if len(formulas) != 1:
        message = f"Expected exactly one selected SUMO assertion, found {len(formulas)}"
        raise ValueError(message)
    return formulas[0]


def _derive(source: FrozenSource) -> SumoReport:
    _relative(source.path)
    if PurePosixPath(source.path).name != source.ontology_path:
        message = "SUMO source path does not identify the selected ontology file"
        raise ValueError(message)
    if source.commit != "unversioned" and re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", source.commit) is None:
        message = "Malformed SUMO source revision"
        raise ValueError(message)
    if sha256(source.text.encode("utf-8")).hexdigest() != source.sha256:
        message = "Frozen SUMO source SHA-256 mismatch"
        raise ValueError(message)
    formulas = list(parse(source.text.removeprefix("\ufeff"), source.ontology_path))
    cases = {name: [_one([f for f in formulas if f.expression == pattern]) for pattern in patterns]
             for name, patterns in _PATTERNS.items()}
    cases["nested_formula"] = [_one([
        f for f in formulas if len(f.expression) == 3 and f.expression[0] == "=>"
        and isinstance(f.expression[2], tuple) and len(f.expression[2]) == 3
        and f.expression[2][0] == "modalAttribute"
        and isinstance(f.expression[2][1], tuple) and len(f.expression[2][1]) == 3
        and f.expression[2][1][0] == "exists"
        and {"AutonomousAgent", "Process", "agent", "Possibility"} <= symbols(f.expression)
    ])]
    citations = {name: [FormulaCitation(
        predicate=str(f.expression[0]), selected_terms=sorted(set(_TERMS) & symbols(f.expression)),
        line=f.line, end_line=f.line + f.text.count("\n"), raw_kif=f.text,
        sha256=sha256(f.text.encode("utf-8")).hexdigest(), indexed_binary_edge=_binary(f),
    ) for f in selected] for name, selected in cases.items()}
    return SumoReport(
        scope=_SCOPE, source=source, selected_terms=list(_TERMS), cases=citations,
        observations=SourceObservations(
            source_formulas=len(formulas), projected_binary_edges=sum(map(_binary, formulas)),
            cited_formulas=len({(f.line, f.text) for selected in cases.values() for f in selected}),
        ),
    )


def validate_sumo_report(report: SumoReport | Mapping[str, JsonValue]) -> SumoReport:
    """Reparse frozen bytes and rederive every observation without disk or an index."""
    payload = report.model_dump() if isinstance(report, SumoReport) else report
    candidate = SumoReport.model_validate(payload)
    if candidate != _derive(candidate.source):
        message = "SUMO report does not match observations rederived from frozen source"
        raise ValueError(message)
    return candidate


def demonstrate_sumo(index: OntologyIndex, root: Path) -> SumoReport:
    """Audit an existing index and freeze exact source examples, with no ATP run."""
    root = root.resolve(strict=True)
    checked_source_path(index.path).relative_to(root)
    stats = index.stats()
    source_root = Path(stats["source_root"])
    path = checked_source_path(source_root / "Merge.kif")
    relative = path.relative_to(root).as_posix()
    audit = audit_sources(index)
    if not audit.passed:
        message = f"Stale or incomplete SUMO source/index: {audit.to_dict()}"
        raise ValueError(message)
    raw = read_regular(path)
    digest = sha256(raw).hexdigest()
    manifest = [row for row in index.source_manifest() if row["path"] == "Merge.kif"]
    if len(manifest) != 1 or manifest[0]["sha256"] != digest:
        message = "SUMO source changed during acquisition or is missing from the index"
        raise ValueError(message)
    source = FrozenSource(path=relative, ontology_path="Merge.kif", commit=stats["source_commit"],
                          clean=stats["source_clean"], text=raw.decode("utf-8"), sha256=digest)
    report = _derive(source)
    for term in report.selected_terms:
        index.term(term)
    formulas = list(parse(source.text.removeprefix("\ufeff"), source.ontology_path))
    for predicate in ("subclass", "instance", "range"):
        indexed = {(row["line"], row["text"], row["source_sha256"])
                   for row in index.assertions(predicate, source.ontology_path)}
        expected = {(f.line, f.text, digest) for f in formulas
                    if _binary(f) and f.expression[0] == predicate}
        if indexed != expected:
            message = "SUMO source assertion is missing from the indexed projection or was changed"
            raise ValueError(message)
    return report


def report_to_substitutions(report: SumoReport | Mapping[str, JsonValue]) -> SumoSubstitutions:
    """Supply source-derived manuscript values after portable validation."""
    valid = validate_sumo_report(report)
    excerpts = {name: "\n".join(c.raw_kif for c in case) for name, case in valid.cases.items()}
    return SumoSubstitutions(
        SUMO_SOURCE_PATH=valid.source.path, SUMO_SOURCE_COMMIT=valid.source.commit,
        SUMO_SOURCE_SHA256=valid.source.sha256,
        SUMO_SOURCE_FORMULAS=str(valid.observations.source_formulas),
        SUMO_PROJECTED_BINARY_EDGES=str(valid.observations.projected_binary_edges),
        SUMO_CITED_FORMULAS=str(valid.observations.cited_formulas),
        SUMO_HIERARCHY_KIF=excerpts["hierarchy"], SUMO_TYPING_KIF=excerpts["typing"],
        SUMO_AGENT_SIGNATURE_KIF=excerpts["agent_signature"],
        SUMO_PROBABILITY_SIGNATURE_KIF=excerpts["probability_signature"],
        SUMO_NESTED_FORMULA_KIF=excerpts["nested_formula"],
    )


def prove_sumo_taxonomy(index: OntologyIndex, root: Path, output: Path) -> TaxonomyDemonstration:
    """Run native restricted taxonomy entailment and a countermodel control separately."""
    report = demonstrate_sumo(index, root)
    root = root.resolve(strict=True)
    output = output if output.is_absolute() else root / output
    output.resolve().relative_to(root)
    output.mkdir(parents=True, exist_ok=False)
    (output / "source-report.json").write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    selection = [c for c in report.cases["hierarchy"] if c.predicate == "subclass"]
    selected_source = output / "selected-source"
    selected_source.mkdir()
    selected_bytes = ("\n".join(c.raw_kif for c in selection) + "\n").encode("utf-8")
    (selected_source / "Merge.kif").write_bytes(selected_bytes)
    selected_index = OntologyIndex(output / "projection.sqlite")
    selected_index.build(selected_source)
    runs: list[TaxonomyRun] = []
    for name, target, expected in (("positive", "Entity", "Theorem"),
                                   ("negative", "Abstract", "CounterSatisfiable")):
        problem = output / f"{name}.p"
        metadata = taxonomy_problem(selected_index, "Process", target, problem)
        result = prove(problem, root, timeout=5)
        if result["status"] != expected or result["proved"] != (name == "positive"):
            message = f"Unexpected native taxonomy control outcome: {result['status']}"
            raise RuntimeError(message)
        runs.append(TaxonomyRun(status=str(result["status"]), proved=result["proved"] is True,
                                problem=problem.relative_to(root).as_posix(),
                                capture=Path(str(result["capture"])).relative_to(root).as_posix(),
                                problem_sha256=metadata["problem_sha256"]))
    return TaxonomyDemonstration(
        scope="Native E proof/control over the selected hierarchy subclass facts plus transitivity only; "
              "not full SUMO inference or an original-SUMO countermodel.",
        source_commit=report.source.commit, source_file_sha256=report.source.sha256,
        subject="Process", positive_target="Entity", negative_target="Abstract",
        source_report=(output / "source-report.json").relative_to(root).as_posix(),
        projection_source_sha256=sha256(selected_bytes).hexdigest(),
        positive=runs[0], negative=runs[1],
    )

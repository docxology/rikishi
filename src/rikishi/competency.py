"""The finite study's source custody and explicitly selected FOL interpretation."""

from __future__ import annotations

import io
import zipfile
from hashlib import sha256
from importlib.resources import files
from pathlib import Path
from typing import Final, Literal

from defusedxml import ElementTree as XML
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

from rikishi.kif import parse
from rikishi.runtime_artifacts import (
    SZS_STATUS,
    ArtifactError,
    ProverKind,
    checked_source_path,
    expanded_problem,
    load_capture,
    read_regular,
    verified_bytes,
)
from rikishi.sumo_demonstrations import SumoReport, validate_sumo_report


class Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True, allow_inf_nan=False)


class AlignmentError(ValueError):
    """The study's declared authority or a derived observation does not replay."""


class Sense(Frozen):
    row: int
    decision: str


class Interpretation(Frozen):
    selected_source_lines: list[int]
    symbols: dict[str, str]
    carrier: str
    kernel: list[str]
    omitted: list[str]


class LogicalCase(Frozen):
    id: str = Field(pattern=r"^[a-z][a-z0-9-]*$")
    additions: list[str]
    conjecture: str | None
    expected: Literal["Satisfiable", "Unsatisfiable", "Theorem", "CounterSatisfiable"]


class NumericalInput(Frozen):
    id: str
    log_prior: list[float | str | None]
    log_likelihood: list[float | str | None]
    posterior: list[float]


class NumericalStudy(Frozen):
    seed: int
    rng: Literal["PCG64"]
    dimensions: list[int]
    models_per_dimension: int
    weight_min: int
    weight_max: int
    likelihood_divisor: int
    candidates: list[Literal["prior", "uniform", "exact-posterior", "posterior-mode"]]
    decimal_precision: int
    ordinary_tolerance: str
    extreme_tolerance: str
    permutation: Literal["reverse"]
    likelihood_rescaling: float
    extremes: list[NumericalInput]
    invalid: list[NumericalInput]


class Study(Frozen):
    schema_version: Literal[1]
    study_id: str
    scope: str
    source_report_path: str
    index_path: str
    sumo_path: str
    sumo_commit: str
    sumo_sha256: str
    sumo_url: str
    citation_lines: list[int]
    workbook_path: str
    workbook_sha256: str
    workbook_url: str
    access_date: str
    workbook_sheet: str
    workbook_rows: list[int]
    workbook_columns: list[str]
    bindings: dict[str, str]
    senses: list[Sense]
    local_formulas: list[str]
    interpretation: Interpretation
    timeout_seconds: int
    cases: list[LogicalCase]
    numerical: NumericalStudy


def load_study(path: Path | None = None) -> Study:
    """Load the supported version; a supplied spec must equal the packaged authority."""
    canonical = Study.model_validate_json(
        files("rikishi").joinpath("data/alignment-study-v1.json").read_bytes())
    if path is not None and Study.model_validate_json(read_regular(path)) != canonical:
        raise AlignmentError("Study differs from the supported packaged authority")
    return canonical


class Citation(Frozen):
    source_path: str
    line: int
    end_line: int
    raw_kif: str
    sha256: str


class SourceClaims(Frozen):
    citations: list[Citation]
    sheet: str
    cells: dict[str, str]
    senses: list[Sense]


_NS: Final = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
_SELECTED_FORMULA: Final = TypeAdapter(
    tuple[Literal["subclass", "instance", "abstractCounterpart"], str, str])


def derive_source_claims(study: Study, report: SumoReport, workbook: bytes) -> SourceClaims:
    """Reparse complete pinned source and original XLSX cells, including focused blanks."""
    valid = validate_sumo_report(report)
    if (valid.source.path != study.sumo_path or valid.source.commit != study.sumo_commit
            or valid.source.sha256 != study.sumo_sha256
            or sha256(workbook).hexdigest() != study.workbook_sha256):
        raise AlignmentError("Source bytes/revision differ from the packaged study binding")
    formulas = {f.line: f for f in parse(valid.source.text, "Merge.kif")}
    citations: list[Citation] = []
    for line in study.citation_lines:
        f = formulas[line]
        citations.append(Citation(source_path=valid.source.path, line=line,
                                  end_line=line + f.text.count("\n"), raw_kif=f.text,
                                  sha256=sha256(f.text.encode()).hexdigest()))
    with zipfile.ZipFile(io.BytesIO(workbook)) as archive:
        book = XML.fromstring(archive.read("xl/workbook.xml"))
        sheet = next(s for s in book.findall("s:sheets/s:sheet", _NS)
                     if s.attrib["name"] == study.workbook_sheet)
        relation = sheet.attrib[
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
        rels = XML.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        target = next(r.attrib["Target"] for r in rels if r.attrib["Id"] == relation)
        strings = XML.fromstring(archive.read("xl/sharedStrings.xml"))
        shared = ["".join(t.text or "" for t in s.iterfind(".//s:t", _NS)) for s in strings]
        sheet_path = target.lstrip("/") if target.startswith("/") else "xl/" + target
        grid = XML.fromstring(archive.read(sheet_path))
        values: dict[str, str] = {}
        for c in grid.findall("s:sheetData/s:row/s:c", _NS):
            value = c.findtext("s:v", default="", namespaces=_NS)
            values[c.attrib["r"]] = shared[int(value)] if c.attrib.get("t") == "s" else value
    cells = {f"{column}{row}": values.get(f"{column}{row}", "")
             for row in study.workbook_rows for column in study.workbook_columns}
    return SourceClaims(citations=citations, sheet=study.workbook_sheet,
                        cells=cells, senses=study.senses)


def extension_text(study: Study) -> str:
    """The exact local extension is a study input, not a SUMO numerical axiom."""
    return ("; Rikishi finite alignment study v1: locally authored content/execution senses.\n"
            "; Numerical laws and biological adequacy are not axioms of this extension.\n"
            + "\n".join(study.local_formulas) + "\n")


def logical_problem(study: Study, claims: SourceClaims, case: LogicalCase) -> str:
    """Emit only two selected source edges and five explicit local assertions."""
    edges = [c.raw_kif for c in claims.citations if c.line in study.interpretation.selected_source_lines]
    statements = list(study.interpretation.kernel)
    for index, text in enumerate([*edges, *study.local_formulas]):
        expression = next(parse(text)).expression
        try:
            predicate, a, b = _SELECTED_FORMULA.validate_python(expression)
        except ValidationError as error:
            raise AlignmentError("Unsupported expression in the declared finite selection") from error
        name = predicate.replace("abstractCounterpart", "abstract_counterpart")
        names = study.interpretation.symbols
        atom = f"{name}({names[a]},{names[b]})"
        statements.append(f"fof(selected_{index},axiom,{atom}).")
    statements.extend(f"fof(control_{i},axiom,{atom})." for i, atom in enumerate(case.additions))
    if case.conjecture is not None:
        statements.append(f"fof(question,conjecture,{case.conjecture}).")
    return "\n".join(statements) + "\n"


class LogicalRun(Frozen):
    id: str
    expected: str
    observed: str
    disposition: Literal["matched", "mismatch", "unresolved"]
    capture: str
    capture_sha256: str
    invocation_id: str
    prover_sha256: str
    problem_sha256: str


def replay_logical_run(directory: Path, run: LogicalRun, problem: str,
                       prover: ProverKind, timeout: int) -> LogicalRun:
    """Check saved capture integrity and interpretation, without claiming live invocation trust."""
    if run.capture != f"captures/{run.id}/capture.json":
        raise AlignmentError("Unexpected campaign capture path")
    path = checked_source_path(directory / run.capture)
    if sha256(read_regular(path)).hexdigest() != run.capture_sha256:
        raise AlignmentError("Capture receipt differs from the campaign binding")
    capture = load_capture(path, run.invocation_id)
    raw = problem.encode()
    command_bound = (f"--cpu-limit={timeout}" in capture.command if prover == "e"
                     else ["-t", str(timeout)] == capture.command[
                         capture.command.index("-t"):capture.command.index("-t") + 2])
    if (capture.prover != prover or not command_bound
            or capture.includes or capture.provenance != {"prover_sha256": run.prover_sha256}
            or capture.source_problem != capture.command[-1]
            or sha256(raw).hexdigest() != run.problem_sha256
            or verified_bytes(capture.problem, path.parent) != raw
            or read_regular(checked_source_path(directory / "problems" / f"{run.id}.p")) != raw):
        raise AlignmentError("Capture is not bound to the regenerated problem and resource policy")
    expanded_problem(capture, path.parent)
    stdout = verified_bytes(capture.stdout, path.parent).decode("utf-8")
    statuses = set(SZS_STATUS.findall(stdout))
    if len(statuses) > 1 or (not capture.timed_out and not statuses):
        raise ArtifactError("Saved output has missing or conflicting SZS statuses")
    observed = "Timeout" if capture.timed_out else statuses.pop()
    if observed in {"Theorem", "Unsatisfiable", "ContradictoryAxioms"} and capture.returncode != 0:
        raise ArtifactError("Saved proof status disagrees with the process exit code")
    if observed in {"Satisfiable", "CounterSatisfiable"} and capture.returncode not in {0, 1}:
        raise ArtifactError("Saved model status disagrees with the process exit code")
    resolved = {"Satisfiable", "Unsatisfiable", "Theorem", "CounterSatisfiable", "ContradictoryAxioms"}
    disposition = ("matched" if observed == run.expected else
                   "mismatch" if observed in resolved else "unresolved")
    derived = run.model_copy(update={"observed": observed, "disposition": disposition})
    if run != derived:
        raise AlignmentError("Saved logical result differs from its captured output")
    return derived

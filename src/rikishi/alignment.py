"""Source-bound finite campaigns; numerical checks and FOL outcomes remain separate."""

from __future__ import annotations

import json
import math
from decimal import Decimal, localcontext
from hashlib import sha256
from importlib.resources import files
from pathlib import Path
from typing import Literal, assert_never

import numpy as np

from rikishi.competency import (
    AlignmentError,
    Frozen,
    LogicalRun,
    NumericalInput,
    NumericalStudy,
    SourceClaims,
    Study,
    derive_source_claims,
    extension_text,
    load_study,
    logical_problem,
    replay_logical_run,
)
from rikishi.fep import ProbabilityError, free_energy_log
from rikishi.ontology import OntologyIndex
from rikishi.runtime import prove, prover_executable
from rikishi.runtime_artifacts import (
    ProverKind,
    checked_source_path,
    load_capture,
    read_regular,
)
from rikishi.runtime_results import ExpectedATPInvocation, verify_invocation
from rikishi.sumo_demonstrations import SumoReport, demonstrate_sumo

__all__ = ["AlignmentReport", "alignment_substitutions", "load_study", "run_alignment",
           "validate_alignment_report"]


class EnergyObservation(Frozen):
    evidence: float | None
    log_evidence: float
    surprise: float
    free_energy: float
    kl_to_posterior: float
    exact_posterior: list[float]
    log_exact_posterior: list[float | None]
    posterior_underflow_indices: list[int]
    identity_residual: float


class DecimalReference(Frozen):
    evidence: str
    log_evidence: str
    free_energy: str
    kl_to_posterior: str
    exact_posterior: list[str]
    log_exact_posterior: list[str | None]


def decimal_reference(inputs: NumericalInput, precision: int) -> DecimalReference:
    """Independent direct Decimal exp/sum/log, using the exact supplied binary floats."""
    with localcontext() as context:
        context.prec = precision
        joint = [Decimal(0) if p is None or l is None else
                 (Decimal.from_float(float(p)) + Decimal.from_float(float(l))).exp()
                 for p, l in zip(inputs.log_prior, inputs.log_likelihood, strict=True)]
        evidence = sum(joint, Decimal(0))
        exact = [j / evidence for j in joint]
        energy = Decimal(0)
        kl = Decimal(0)
        for probability, j, posterior in zip(inputs.posterior, joint, exact, strict=True):
            q = Decimal.from_float(probability)
            if q:
                energy += q * (q.ln() - j.ln())
                kl += q * (q.ln() - posterior.ln())
        return DecimalReference(
            evidence=str(evidence), log_evidence=str(evidence.ln()), free_energy=str(energy),
            kl_to_posterior=str(kl), exact_posterior=[str(q) for q in exact],
            log_exact_posterior=[str(q.ln()) if q else None for q in exact])


def _logs(values: list[float | str | None]) -> list[float | None]:
    return [None if value is None else float(value) for value in values]


def _evaluate(inputs: NumericalInput) -> EnergyObservation:
    return EnergyObservation.model_validate(free_energy_log(
        _logs(inputs.log_prior), _logs(inputs.log_likelihood), inputs.posterior))


class NumericalRow(Frozen):
    input: NumericalInput
    dimension: int
    model_index: int | None
    candidate: str
    prior_weights: list[int]
    likelihood_weights: list[int]
    result: EnergyObservation
    reference: DecimalReference
    max_reference_error: float
    permutation_max_error: float
    rescaling_max_error: float
    tolerance: str
    passed: bool


def _compare_row(inputs: NumericalInput, spec: NumericalStudy, *, extreme: bool) -> NumericalRow:
    result = _evaluate(inputs)
    reference = decimal_reference(inputs, spec.decimal_precision)
    comparisons = [(result.free_energy, reference.free_energy),
                   (result.log_evidence, reference.log_evidence),
                   (result.kl_to_posterior, reference.kl_to_posterior),
                   (result.surprise, str(-Decimal(reference.log_evidence))),
                   *zip(result.exact_posterior, reference.exact_posterior, strict=True)]
    errors = [abs(Decimal.from_float(a) - Decimal(b)) for a, b in comparisons]
    for actual, expected in zip(result.log_exact_posterior, reference.log_exact_posterior, strict=True):
        if actual is not None and expected is not None:
            errors.append(abs(Decimal.from_float(actual) - Decimal(expected)))
        elif actual is not expected:
            raise AlignmentError("Structural zero differs from the Decimal support")
    expected_underflow = [i for i, (mass, logmass) in enumerate(
        zip(reference.exact_posterior, reference.log_exact_posterior, strict=True))
        if logmass is not None and float(Decimal(mass)) == 0.0]
    evidence = float(Decimal(reference.evidence))
    support_passed = (result.posterior_underflow_indices == expected_underflow
                      and (result.evidence is None) == (evidence == 0.0))
    if result.evidence is not None:
        errors.append(abs(Decimal.from_float(result.evidence) - Decimal(reference.evidence)))
    permuted = _evaluate(inputs.model_copy(update={
        "log_prior": inputs.log_prior[::-1], "log_likelihood": inputs.log_likelihood[::-1],
        "posterior": inputs.posterior[::-1]}))
    permutation_error = max(abs(result.free_energy - permuted.free_energy),
                            abs(result.kl_to_posterior - permuted.kl_to_posterior),
                            abs(result.log_evidence - permuted.log_evidence),
                            *(abs(a - b) for a, b in zip(
                                result.exact_posterior, permuted.exact_posterior[::-1], strict=True)))
    shift = math.log(spec.likelihood_rescaling)
    scaled = _evaluate(inputs.model_copy(update={"log_likelihood": [
        None if v is None else float(v) + shift for v in inputs.log_likelihood]}))
    rescaling_error = max(abs(scaled.free_energy - result.free_energy + shift),
                          abs(scaled.log_evidence - result.log_evidence - shift),
                          abs(scaled.kl_to_posterior - result.kl_to_posterior),
                          *(abs(a - b) for a, b in zip(
                              scaled.exact_posterior, result.exact_posterior, strict=True)))
    tolerance = spec.extreme_tolerance if extreme else spec.ordinary_tolerance
    bound = Decimal(tolerance)
    max_error = max(errors)
    passed = (max_error <= bound and permutation_error <= float(bound)
              and rescaling_error <= float(bound) and support_passed
              and abs(result.identity_residual) <= float(bound)
              and result.kl_to_posterior >= -float(bound))
    return NumericalRow(input=inputs, dimension=len(inputs.posterior), model_index=None,
                        candidate="boundary", prior_weights=[], likelihood_weights=[],
                        result=result, reference=reference, max_reference_error=float(max_error),
                        permutation_max_error=permutation_error, rescaling_max_error=rescaling_error,
                        tolerance=tolerance, passed=passed)


class InvalidObservation(Frozen):
    id: str
    rejected: bool
    error: str | None


class NumericalReport(Frozen):
    rows: list[NumericalRow]
    extremes: list[NumericalRow]
    invalid: list[InvalidObservation]


def numerical_matrix(study: Study | None = None) -> NumericalReport:
    """Evaluate the predeclared seeded matrix and controls without a native prover."""
    spec = (study or load_study()).numerical
    rng = np.random.Generator(np.random.PCG64(spec.seed))
    rows: list[NumericalRow] = []
    for dimension in spec.dimensions:
        for index in range(spec.models_per_dimension):
            weights = [int(v) for v in rng.integers(spec.weight_min, spec.weight_max + 1, dimension)]
            likelihoods = [int(v) for v in rng.integers(spec.weight_min, spec.weight_max + 1, dimension)]
            prior = [w / sum(weights) for w in weights]
            log_prior: list[float | str | None] = [math.log(p) for p in prior]
            log_likelihood: list[float | str | None] = [
                math.log(w / spec.likelihood_divisor) for w in likelihoods]
            inputs = NumericalInput(id="reference", log_prior=log_prior,
                                    log_likelihood=log_likelihood, posterior=prior)
            exact = decimal_reference(inputs, spec.decimal_precision).exact_posterior
            for candidate in spec.candidates:
                match candidate:
                    case "prior":
                        posterior = prior
                    case "uniform":
                        posterior = [1.0 / dimension] * dimension
                    case "exact-posterior":
                        posterior = [float(Decimal(q)) for q in exact]
                    case "posterior-mode":
                        mode = max(range(dimension), key=lambda i: Decimal(exact[i]))
                        posterior = [float(i == mode) for i in range(dimension)]
                    case unreachable:
                        assert_never(unreachable)
                inputs = inputs.model_copy(update={"id": f"d{dimension}-m{index}-{candidate}",
                                                    "posterior": posterior})
                rows.append(_compare_row(inputs, spec, extreme=False).model_copy(update={
                    "model_index": index, "candidate": candidate, "prior_weights": weights,
                    "likelihood_weights": likelihoods}))
    extremes = [_compare_row(inputs, spec, extreme=True) for inputs in spec.extremes]
    invalid: list[InvalidObservation] = []
    for inputs in spec.invalid:
        error = None
        try:
            _evaluate(inputs)
        except ProbabilityError as failure:
            error = str(failure)
        invalid.append(InvalidObservation(id=inputs.id, rejected=error is not None, error=error))
    return NumericalReport(rows=rows, extremes=extremes, invalid=invalid)


class CampaignSummary(Frozen):
    logical_cases: int
    logical_matched: int
    logical_unresolved: int
    logical_mismatched: int
    baseline_satisfiable: bool
    numerical_rows: int
    numerical_passed: int
    extreme_cases: int
    extreme_passed: int
    invalid_cases: int
    invalid_rejected: int
    campaign_complete: bool
    semantic_validation: Literal[False] = False


def _summary(logical: list[LogicalRun], numerical: NumericalReport) -> CampaignSummary:
    counts = {s: sum(r.disposition == s for r in logical) for s in
              ("matched", "mismatch", "unresolved")}
    baseline = any(r.id == "background" and r.observed == "Satisfiable" for r in logical)
    numerical_passed = sum(r.passed for r in numerical.rows)
    extreme_passed = sum(r.passed for r in numerical.extremes)
    invalid_rejected = sum(r.rejected for r in numerical.invalid)
    complete = (baseline and counts["matched"] == len(logical)
                and numerical_passed == len(numerical.rows)
                and extreme_passed == len(numerical.extremes)
                and invalid_rejected == len(numerical.invalid))
    return CampaignSummary(
        logical_cases=len(logical), logical_matched=counts["matched"],
        logical_unresolved=counts["unresolved"], logical_mismatched=counts["mismatch"],
        baseline_satisfiable=baseline, numerical_rows=len(numerical.rows),
        numerical_passed=numerical_passed, extreme_cases=len(numerical.extremes),
        extreme_passed=extreme_passed, invalid_cases=len(numerical.invalid),
        invalid_rejected=invalid_rejected, campaign_complete=complete)


class AlignmentReport(Frozen):
    schema_version: Literal[1] = 1
    study: Study
    authority_sha256: str
    source_claims: SourceClaims
    bindings: dict[str, str]
    implementation: dict[str, str]
    prover: ProverKind
    invocation_trust: Literal["live-bound-at-creation"] = "live-bound-at-creation"
    replay_boundary: str
    logical: list[LogicalRun]
    numerical: NumericalReport
    summary: CampaignSummary


def _digest(model: Frozen) -> str:
    return sha256(json.dumps(model.model_dump(mode="json"), sort_keys=True,
                             separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def run_alignment(root: Path, output: Path, *, study: Study | None = None,
                  source_report: Path | None = None, workbook_path: Path | None = None,
                  prover: ProverKind = "e") -> AlignmentReport:
    """Run in a fresh repository-local directory; retain each native capture and all inputs."""
    root = checked_source_path(root)
    spec = study or load_study()
    if spec != load_study():
        raise AlignmentError("Unsupported study authority")
    if prover not in {"e", "v"}:
        raise AlignmentError("Unsupported prover family")
    output = output if output.is_absolute() else root / output
    output.resolve().relative_to(root)
    checked_source_path(output.parent)
    bindings = {name: sha256(read_regular(root / name)).hexdigest() for name in spec.bindings}
    if bindings != spec.bindings:
        raise AlignmentError("Lock/dependency inputs differ from the study authority")
    if source_report is None:
        source = demonstrate_sumo(OntologyIndex(root / spec.index_path), root)
    else:
        source_report = source_report if source_report.is_absolute() else root / source_report
        source = SumoReport.model_validate_json(read_regular(checked_source_path(source_report)))
    workbook_path = workbook_path or Path(spec.workbook_path)
    workbook_path = workbook_path if workbook_path.is_absolute() else root / workbook_path
    workbook = read_regular(checked_source_path(workbook_path))
    claims = derive_source_claims(spec, source, workbook)
    if read_regular(root / "examples/fep-ontology.kif").decode() != extension_text(spec):
        raise AlignmentError("Local KIF extension differs from the study authority")
    output.mkdir(exist_ok=False)
    for name in ("problems", "captures", "bindings"):
        (output / name).mkdir()
    (output / "source-report.json").write_text(source.model_dump_json(indent=2) + "\n")
    (output / "workbook.xlsx").write_bytes(workbook)
    (output / "study.json").write_text(spec.model_dump_json(indent=2) + "\n")
    (output / "extension.kif").write_text(extension_text(spec))
    for name in spec.bindings:
        (output / "bindings" / Path(name).name).write_bytes(read_regular(root / name))
    implementation_paths = ["src/rikishi/alignment.py", "src/rikishi/competency.py",
                            "src/rikishi/fep.py", "src/rikishi/runtime.py",
                            "src/rikishi/runtime_artifacts.py", "src/rikishi/runtime_capture.py",
                            "src/rikishi/runtime_results.py", "src/rikishi/runtime_tptp.py"]
    implementation = {name: sha256(read_regular(root / name)).hexdigest()
                      for name in implementation_paths}
    numerical = numerical_matrix(spec)
    runs: list[LogicalRun] = []
    for case in spec.cases:
        text = logical_problem(spec, claims, case)
        problem = output / "problems" / f"{case.id}.p"
        problem.write_text(text)
        capture_path = output / "captures" / case.id / "capture.json"
        try:
            result = prove(problem, root, timeout=spec.timeout_seconds, prover=prover,
                           output=capture_path.parent)
            observed = str(result["status"])
            if Path(str(result["capture"])) != capture_path:
                raise AlignmentError("Runtime returned an unexpected capture path")
        except TimeoutError:
            observed = "Timeout"
        capture = load_capture(capture_path)
        binary = prover_executable(root, prover)
        verify_invocation(capture, ExpectedATPInvocation(
            invocation_id=capture.invocation_id, executable=binary,
            provenance={"prover_sha256": sha256(read_regular(binary)).hexdigest()},
            problem_sha256=sha256(text.encode()).hexdigest(), prover=prover))
        resolved = {"Satisfiable", "Unsatisfiable", "Theorem", "CounterSatisfiable", "ContradictoryAxioms"}
        disposition = ("matched" if observed == case.expected else
                       "mismatch" if observed in resolved else "unresolved")
        run = LogicalRun(id=case.id, expected=case.expected, observed=observed,
                         disposition=disposition, capture=capture_path.relative_to(output).as_posix(),
                         capture_sha256=sha256(read_regular(capture_path)).hexdigest(),
                         invocation_id=capture.invocation_id,
                         prover_sha256=capture.provenance["prover_sha256"],
                         problem_sha256=sha256(text.encode()).hexdigest())
        runs.append(replay_logical_run(output, run, text, prover, spec.timeout_seconds))
    if implementation != {name: sha256(read_regular(root / name)).hexdigest()
                           for name in implementation_paths}:
        raise AlignmentError("Implementation changed during campaign; preserve incomplete evidence")
    report = AlignmentReport(
        study=spec, authority_sha256=_digest(spec), source_claims=claims, bindings=bindings,
        implementation=implementation, prover=prover, logical=runs, numerical=numerical,
        summary=_summary(runs, numerical),
        replay_boundary="Portable replay rederives pinned sources, problems, numerical results and "
        "saved capture interpretation. It does not authenticate solver execution or independently "
        "check ATP proofs. Live invocation was bound only at creation. Supply an independently "
        "trusted outer report SHA-256 to detect coherent report replacement.")
    (output / "alignment-report.json").write_text(report.model_dump_json(indent=2) + "\n")
    return report


def validate_alignment_report(path: Path, *, trusted_report_sha256: str | None = None) -> AlignmentReport:
    """Replay saved evidence without executing a solver; an optional outer digest supplies trust."""
    path = checked_source_path(path)
    raw = read_regular(path)
    if trusted_report_sha256 is not None and sha256(raw).hexdigest() != trusted_report_sha256:
        raise AlignmentError("Outer report binding mismatch")
    report = AlignmentReport.model_validate_json(raw)
    spec = load_study(path.parent / "study.json")
    if report.study != spec or report.authority_sha256 != _digest(spec):
        raise AlignmentError("Report study/polarity differs from the packaged authority")
    source = SumoReport.model_validate_json(read_regular(path.parent / "source-report.json"))
    claims = derive_source_claims(spec, source, read_regular(path.parent / "workbook.xlsx"))
    if report.source_claims != claims:
        raise AlignmentError("Source claims do not rederive from complete retained source bytes")
    if read_regular(path.parent / "extension.kif").decode() != extension_text(spec):
        raise AlignmentError("Retained local interpretation differs from the study authority")
    bindings = {name: sha256(read_regular(checked_source_path(
        path.parent / "bindings" / Path(name).name))).hexdigest()
                for name in spec.bindings}
    if report.bindings != bindings or bindings != spec.bindings:
        raise AlignmentError("Retained lock/dependency binding mismatch")
    expected_implementation = {name: sha256(files("rikishi").joinpath(
        name.removeprefix("src/rikishi/")).read_bytes()).hexdigest() for name in (
            "src/rikishi/alignment.py", "src/rikishi/competency.py", "src/rikishi/fep.py",
            "src/rikishi/runtime.py", "src/rikishi/runtime_artifacts.py",
            "src/rikishi/runtime_capture.py", "src/rikishi/runtime_results.py",
            "src/rikishi/runtime_tptp.py")}
    if report.implementation != expected_implementation:
        raise AlignmentError("Replay implementation differs from the campaign source binding")
    if [r.id for r in report.logical] != [c.id for c in spec.cases]:
        raise AlignmentError("Missing, reordered or duplicate competency cases")
    for case, run in zip(spec.cases, report.logical, strict=True):
        if run.expected != case.expected:
            raise AlignmentError("Expected competency polarity changed")
        replay_logical_run(path.parent, run, logical_problem(spec, claims, case),
                           report.prover, spec.timeout_seconds)
    numerical = numerical_matrix(spec)
    if report.numerical != numerical:
        raise AlignmentError("Numerical results do not replay from the declared seed and inputs")
    if report.summary != _summary(report.logical, numerical):
        raise AlignmentError("Campaign summary does not follow from measured outcomes")
    return report


def alignment_substitutions(report: AlignmentReport) -> dict[str, str]:
    """Expose measured manuscript values without granting a semantic validation badge."""
    return {"ALIGNMENT_" + name.upper(): str(value) for name, value in
            report.summary.model_dump().items()}

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from rikishi.alignment import (
    AlignmentReport,
    alignment_substitutions,
    validate_alignment_report,
)
from rikishi.manuscript_provenance import require_evidence


@dataclass(frozen=True, slots=True)
class ResearchContext:
    primary: AlignmentReport
    comparison: AlignmentReport
    values: dict[str, str]
    input_sha256: dict[str, str]


def load_research_context(directory: Path, *, decimal_places: int) -> ResearchContext:
    if type(decimal_places) is not int or decimal_places < 0:
        raise ValueError("decimal_places must be a nonnegative integer")
    paths = {family: directory / family / "alignment-report.json" for family in ("e", "v")}
    digests = {family: hashlib.sha256(path.read_bytes()).hexdigest()
               for family, path in paths.items()}
    reports = {family: validate_alignment_report(path, trusted_report_sha256=digests[family])
               for family, path in paths.items()}
    require_evidence(
        digests == {family: hashlib.sha256(path.read_bytes()).hexdigest()
                    for family, path in paths.items()},
        "Research report changed during publication context loading",
    )
    e, v = reports["e"], reports["v"]
    require_evidence(e.prover == "e" and v.prover == "v", "Research prover families differ")
    require_evidence(e.study == v.study and e.source_claims == v.source_claims,
                     "Research study or source claims differ between prover families")
    require_evidence(e.numerical == v.numerical, "Research numerical matrices differ")
    require_evidence(
        [(run.id, run.expected, run.problem_sha256) for run in e.logical]
        == [(run.id, run.expected, run.problem_sha256) for run in v.logical],
        "Research competency inputs differ between prover families",
    )
    require_evidence(e.summary.campaign_complete and v.summary.campaign_complete,
                     "Research campaign is incomplete; inspect its retained results")
    values = alignment_substitutions(e)
    values.update({
        "ALIGNMENT_V_LOGICAL_MATCHED": str(v.summary.logical_matched),
        "ALIGNMENT_NATIVE_INVOCATIONS": str(len(e.logical) + len(v.logical)),
        "ALIGNMENT_CROSS_FAMILY_AGREEMENT": str(sum(
            first.observed == second.observed for first, second
            in zip(e.logical, v.logical, strict=True))),
        "ALIGNMENT_MODEL_COUNT": str(len({(row.dimension, row.model_index)
                                          for row in e.numerical.rows})),
        "ALIGNMENT_DIMENSIONS": ", ".join(str(n) for n in sorted(
            {row.dimension for row in e.numerical.rows})),
        "ALIGNMENT_REFERENCE_PRECISION": str(e.study.numerical.decimal_precision),
        "ALIGNMENT_ORDINARY_TOLERANCE": e.study.numerical.ordinary_tolerance,
        "ALIGNMENT_EXTREME_TOLERANCE": e.study.numerical.extreme_tolerance,
        "ALIGNMENT_AUTHORITY_SHA256": e.authority_sha256,
        "ALIGNMENT_SOURCE_ROWS": str(len(e.study.workbook_rows)),
        "ALIGNMENT_LOGICAL_TABLE": "\n".join([
            "| Competency/control | Expected | E | Vampire |",
            "| -------------------------------- | ------------------- | ------------------- | ------------------- |",
            *(f"| `{first.id}` | {first.expected} | {first.observed} | {second.observed} |"
              for first, second in zip(e.logical, v.logical, strict=True)),
        ]),
    })
    numerical_rows = []
    for dimension in sorted({row.dimension for row in e.numerical.rows}):
        selected = [row for row in e.numerical.rows if row.dimension == dimension]
        errors = [max(getattr(row, attribute) for row in selected) for attribute in
                  ("max_reference_error", "permutation_max_error", "rescaling_max_error")]
        formatted = " | ".join(f"{value:.{decimal_places}e}" for value in errors)
        numerical_rows.append(f"| {dimension} | {len(selected)} | {formatted} |")
    values["ALIGNMENT_NUMERICAL_TABLE"] = "\n".join([
        "| States | Rows | Reference | Permutation | Rescaling |",
        "| ---: | ---: | ---: | ---: | ---: |",
        *numerical_rows,
    ])
    return ResearchContext(e, v, values, {paths[family].relative_to(directory).as_posix(): digest
                                        for family, digest in digests.items()})

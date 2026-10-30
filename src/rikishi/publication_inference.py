from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from rikishi.inference_models import InferenceReport
from rikishi.inference_replay import validate_inference_report
from rikishi.inference_study import catalog
from rikishi.manuscript_provenance import require_evidence
from rikishi.runtime_artifacts import read_regular


@dataclass(frozen=True, slots=True)
class InferenceContext:
    report: InferenceReport
    values: dict[str, str]
    input_sha256: dict[str, str]


def load_inference_context(directory: Path) -> InferenceContext:
    path = directory / "inference-report.json"
    digest = sha256(read_regular(path)).hexdigest()
    report = validate_inference_report(path, trusted_report_sha256=digest)
    require_evidence(report.provers == ["e", "v"] and report.summary.passed,
                     "Publication requires a complete two-prover inference campaign")
    scenarios = catalog().scenarios
    counts = Counter(item.category for item in scenarios)
    categories = {item.id: item.category for item in scenarios}
    matched = Counter((categories[run.group], run.prover) for run in report.cases if run.matched)
    table = ["| Source category | Scenarios | E matched | Vampire matched |",
             "| --- | ---: | ---: | ---: |"]
    table.extend(f"| {category} | {counts[category]} | {matched[category, 'e']} | {matched[category, 'v']} |"
                 for category in sorted(counts))
    require_evidence(sha256(read_regular(path)).hexdigest() == digest,
                     "Inference report changed during publication context loading")
    return InferenceContext(report, {
        "INFERENCE_SCENARIOS": str(report.summary.scenarios),
        "INFERENCE_NATIVE_RUNS": str(report.summary.total),
        "INFERENCE_MATCHED": str(report.summary.matched),
        "INFERENCE_SUMMARY_TABLE": "\n".join(table),
        "INFERENCE_REPORT_SHA256": digest,
    }, {"inference-report.json": digest})


def verify_inference_content(text: str, context: InferenceContext, edition: str) -> None:
    compact = re.sub(r"\s+", "", text)
    for row in context.values["INFERENCE_SUMMARY_TABLE"].splitlines()[2:]:
        expected = "".join(cell.strip() for cell in row.strip("|").split("|"))
        require_evidence(re.sub(r"\s+", "", expected) in compact,
                         f"Inference result row missing: {edition}, {row}")

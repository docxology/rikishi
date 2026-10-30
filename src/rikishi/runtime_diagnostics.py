"""Replay frozen inputs and validate named premises with their recorded native family."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from rikishi.runtime import _fresh_directory, prover_executable
from rikishi.runtime_artifacts import (
    SZS_STATUS,
    ArtifactError,
    Capture,
    ProverKind,
    expanded_problem,
    load_capture,
    read_regular,
    verified_bytes,
)
from rikishi.runtime_capture import capture_prover
from rikishi.runtime_results import ExpectedATPInvocation, verify_invocation
from rikishi.runtime_tptp import parse_tptp

_PROOF_BLOCK = re.compile(
    r"^[%#][ \t]*SZS output start CNFRefutation[^\r\n]*[\r\n]+"
    r"(.*?)^[%#][ \t]*SZS output end CNFRefutation[^\r\n]*$",
    re.MULTILINE | re.DOTALL,
)


def _proof_blocks(stdout: str, prover: ProverKind) -> list[str]:
    match prover:
        case "e":
            return _PROOF_BLOCK.findall(stdout)
        case "v":
            markers = list(re.finditer(
                r"^[%#][ \t]*SZS output (start|end) ([^\r\n]*)", stdout, re.MULTILINE,
            ))
            if len(markers) != 2:
                return []
            start, end = markers
            name = start.group(2).rstrip()
            if (start.group(1) != "start" or end.group(1) != "end"
                    or not re.fullmatch(r"Proof for \S(?:[^\r\n]*\S)?", name)
                    or name != end.group(2).rstrip()):
                return []
            return [stdout[start.end():end.start()]]
        case _:
            raise ValueError("prover must be 'e' or 'v'")


def proof_premises(stdout: str, *, prover: ProverKind = "e") -> list[str]:
    blocks = _proof_blocks(stdout, prover)
    return sorted({statement.source_name for block in blocks for statement in parse_tptp(block)
                   if statement.source_name is not None})


def _replay(command: list[str], directory: Path, source: Capture, timeout: int) -> Capture:
    expected = ExpectedATPInvocation(
        source.invocation_id + "-" + directory.name, Path(command[0]), source.provenance,
        hashlib.sha256(read_regular(Path(command[-1]))).hexdigest(), prover=source.prover,
    )
    capture_prover(command, directory, invocation_id=expected.invocation_id,
                   provenance=source.provenance, timeout=timeout + 5, prover=source.prover)
    capture = load_capture(directory / "capture.json", expected.invocation_id)
    verify_invocation(capture, expected)
    return capture


def diagnose(capture_path: Path, root: Path, *, timeout: int = 5, output: Path) -> dict[str, object]:
    """Replay saved bytes with proof flags; a proof premise set is not a minimal core."""
    if not 1 <= timeout <= 30:
        raise ValueError("diagnostic CPU limit must be between 1 and 30 seconds")
    capture = load_capture(capture_path)
    binary = prover_executable(root, capture.prover)
    label = "E" if capture.prover == "e" else "Vampire"
    if hashlib.sha256(read_regular(binary)).hexdigest() != capture.provenance.get("prover_sha256"):
        raise ArtifactError(f"diagnostic requires the same recorded {label} executable")
    verify_invocation(capture, ExpectedATPInvocation(
        capture.invocation_id, binary, capture.provenance, capture.problem.sha256,
        prover=capture.prover,
    ))
    frozen = expanded_problem(capture, capture_path.parent)
    output = _fresh_directory(root.resolve(), output, "diagnostic-")
    problem = output / "replay.p"
    problem.write_text(frozen, encoding="utf-8")
    options = capture.command[1:-1]
    if capture.prover == "e":
        flags = [argument for argument in options if not argument.startswith("--cpu-limit=")]
        flags = [*flags, *[flag for flag in ("--tstp-format", "--proof-object") if flag not in flags],
                 f"--cpu-limit={timeout}"]
    else:
        flags = [item for index in range(0, len(options), 2) if options[index] != "-t"
                 for item in options[index:index + 2]]
        flags.extend(["-t", str(timeout)])
    run = output / "proof"
    run.mkdir()
    result = _replay([str(binary), *flags, str(problem)], run, capture, timeout)
    stdout = verified_bytes(result.stdout, run).decode("utf-8")
    statuses = set(SZS_STATUS.findall(stdout))
    status = next(iter(statuses)) if len(statuses) == 1 else "NoUniqueSZSStatus"
    proof_blocks = (_proof_blocks(stdout, capture.prover)
                    if not result.timed_out and result.returncode == 0
                    and status in {"Theorem", "Unsatisfiable", "ContradictoryAxioms"} else [])
    premises = sorted({statement.source_name for block in proof_blocks for statement in parse_tptp(block)
                       if statement.source_name is not None})
    (output / "proof.tstp").write_text("\n".join(proof_blocks), encoding="utf-8")
    selected: list[str] = []
    for statement in parse_tptp(read_regular(problem).decode("utf-8")):
        if statement.name in premises:
            selected.append(statement.text)
    if len(selected) != len(premises):
        raise ArtifactError("proof premise names do not map uniquely to complete saved statements")
    core = output / "proof-premises.p"
    core.write_text("\n".join(selected) + "\n", encoding="utf-8")
    subset_status = "not_run"
    if selected:
        subset_directory = output / "subset-check"
        subset_directory.mkdir()
        subset = _replay([str(binary), *flags, str(core)], subset_directory, capture, timeout)
        subset_statuses = set(SZS_STATUS.findall(verified_bytes(subset.stdout, subset_directory).decode("utf-8")))
        subset_status = next(iter(subset_statuses)) if len(subset_statuses) == 1 else "NoUniqueSZSStatus"
        if subset.timed_out or subset.returncode != 0 or subset_status not in {"Theorem", "Unsatisfiable", "ContradictoryAxioms"}:
            raise ArtifactError("exported proof subset failed native replay validation")
    report: dict[str, object] = {
        "status": status, "prover": capture.prover,
        "returncode": result.returncode, "timed_out": result.timed_out,
        "source_capture": str(capture_path.resolve()), "capture": str(run / "capture.json"),
        "premise_names": premises, "premise_count": len(selected), "premises": str(core),
        "minimality": "not_established", "semantic_validation": False,
        "subset_status": subset_status,
    }
    with (output / "diagnostic.json").open("x") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("capture", type=Path)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--timeout", type=int, default=5)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    report = diagnose(args.capture, args.root, timeout=args.timeout, output=args.output)
    print(json.dumps(report, indent=2))
    return 0 if report["premise_count"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

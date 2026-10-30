"""Thin command-line adapters for the shared finite witness study."""

from __future__ import annotations

import argparse
from pathlib import Path

from pydantic import JsonValue


def register(commands: argparse._SubParsersAction) -> None:
    commands.add_parser("bridge-catalog", help="Inspect the finite FEP_Formal–SUMO witness study")
    run = commands.add_parser("bridge-run", help="Run concrete Lean, numerical and SUMO native obligations")
    run.add_argument("output", type=Path)
    run.add_argument("--prover", choices=("both", "e", "v"), default="both")
    run.add_argument("--timeout", type=int, default=10)
    verify = commands.add_parser("bridge-verify", help="Replay a retained finite-witness packet")
    verify.add_argument("report", type=Path)
    verify.add_argument("--sha256", required=True, help="Separately retained outer report digest")
    case = commands.add_parser("bridge-case", help="Inspect one native case and its shared Lean/numerical witness")
    case.add_argument("report", type=Path)
    case.add_argument("case_id")
    case.add_argument("--prover", choices=("e", "v"), default="e")
    case.add_argument("--sha256", required=True, help="Separately retained outer report digest")
    figures = commands.add_parser("bridge-figures", help="Render report-derived figures and an offline explorer")
    figures.add_argument("report", type=Path)
    figures.add_argument("output", type=Path)
    figures.add_argument("--sha256", required=True, help="Separately retained outer report digest")


def _path(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def execute(args: argparse.Namespace) -> tuple[JsonValue, int]:
    root = args.root.resolve()
    match args.command:
        case "bridge-catalog":
            from rikishi.bridge_study import catalog

            return catalog().model_dump(mode="json"), 0
        case "bridge-run":
            from rikishi.bridge_runner import run_bridge

            report = run_bridge(root, args.output, prover=args.prover, timeout=args.timeout)
            return report.model_dump(mode="json"), 0 if report.summary.passed else 2
        case "bridge-verify":
            from rikishi.bridge_replay import validate_bridge_report

            report = validate_bridge_report(_path(root, args.report), trusted_report_sha256=args.sha256)
            return report.model_dump(mode="json"), 0 if report.summary.passed else 2
        case "bridge-case":
            from rikishi.bridge_views import inspect_case
            from rikishi.inference_views import CaseSelection

            path = _path(root, args.report).relative_to(root)
            result = inspect_case(root, CaseSelection(str(path), args.sha256, args.case_id, args.prover))
            return result.model_dump(mode="json"), 0
        case "bridge-figures":
            from rikishi.bridge_figures import render_bridge_figures

            paths = render_bridge_figures(_path(root, args.report), _path(root, args.output),
                                          trusted_report_sha256=args.sha256)
            return {"files": [str(path) for path in paths]}, 0
        case _:
            raise ValueError(f"Unknown bridge command: {args.command}")

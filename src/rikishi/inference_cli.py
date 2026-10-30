from __future__ import annotations

import argparse
from pathlib import Path


def register(commands: argparse._SubParsersAction) -> None:
    commands.add_parser("inference-catalog", help="Inspect the source-bound SUMO inference study")
    run = commands.add_parser("inference-run", help="Run real native inference and adversarial controls")
    run.add_argument("output", type=Path)
    run.add_argument("--prover", choices=("both", "e", "v"), default="both")
    run.add_argument("--timeout", type=int, default=5)
    verify = commands.add_parser("inference-verify", help="Replay a retained inference report")
    verify.add_argument("report", type=Path)
    verify.add_argument("--sha256", required=True, help="Separately retained outer report digest")
    publish = commands.add_parser("inference-publish", help="Register a verified saved campaign in the local dashboard")
    publish.add_argument("report", type=Path)
    publish.add_argument("--sha256", required=True, help="Separately retained outer report digest")


def execute(args: argparse.Namespace) -> tuple[object, int]:
    match args.command:
        case "inference-catalog":
            from rikishi.inference_study import catalog

            return catalog().model_dump(mode="json"), 0
        case "inference-run":
            from rikishi.inference_runner import run_inference

            report = run_inference(args.root.resolve(), args.output, prover=args.prover,
                                   timeout=args.timeout)
            return report.model_dump(mode="json"), 0 if report.summary.passed else 2
        case "inference-verify":
            from rikishi.inference_replay import validate_inference_report

            path = args.report if args.report.is_absolute() else args.root / args.report
            report = validate_inference_report(path, trusted_report_sha256=args.sha256)
            return report.model_dump(mode="json"), 0 if report.summary.passed else 2
        case "inference-publish":
            from rikishi.inference_views import publish_report

            relative = args.report.relative_to(args.root.resolve()) if args.report.is_absolute() else args.report
            return publish_report(args.root.resolve(), str(relative), args.sha256), 0
        case _:
            raise ValueError(f"Unknown inference command: {args.command}")

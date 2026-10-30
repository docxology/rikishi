import argparse
import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

from rikishi.ontology import OntologyIndex


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="rikishi", description="Operate the real SUMO corpus")
    result.add_argument("--root", type=Path, default=Path(os.environ.get("RIKISHI_ROOT", ".")))
    commands = result.add_subparsers(dest="command", required=True)
    from rikishi.analysis_cli import register
    from rikishi.bridge_cli import register as register_bridge
    from rikishi.inference_cli import register as register_inference

    register(commands)
    register_inference(commands)
    register_bridge(commands)
    commands.add_parser("bootstrap", help="Install pinned upstream SUMO and reasoning tools")
    commands.add_parser("doctor", help="Inspect actual runtime capabilities")
    index = commands.add_parser("index", help="Index all .kif files, reporting every parse failure")
    index.add_argument("--source", type=Path)
    search = commands.add_parser("search", help="Search indexed term names")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=30)
    term = commands.add_parser("term", help="Inspect source-bound formulas and documentation")
    term.add_argument("name")
    graph = commands.add_parser("graph", help="Export a bounded asserted-relation graph")
    graph.add_argument("name")
    graph.add_argument("--limit", type=int, default=80)
    graph.add_argument("--relation")
    commands.add_parser("stats", help="Measure indexed corpus")
    commands.add_parser("verify-source", help="Compare current source hashes and revision to index")
    commands.add_parser("metrics", help="Measure file concentration, predicates, and asserted graph")
    commands.add_parser("report", help="Export corpus manifest, dashboard, and figures")
    commands.add_parser("fep-demo", help="Run a finite variational free-energy example")
    commands.add_parser("active-demo", help="Compare one-step actions with explicit preferences")
    energy = commands.add_parser("fep-evaluate", help="Evaluate an explicit finite JSON model")
    energy.add_argument("model", type=Path)
    energy.add_argument("--logarithmic", action="store_true", help="Read log_prior/log_likelihood")
    inspect = commands.add_parser("fep-inspect", help="Inspect proposed Lean/SUMO source mappings")
    inspect.add_argument("--repo", type=Path)
    verify = commands.add_parser("fep-verify", help="Compile pinned finite Lean modules in isolation")
    verify.add_argument("--repo", type=Path)
    verify.add_argument("--compiler", type=Path)
    verify.add_argument("--packages", type=Path)
    verify.add_argument("--output", type=Path)
    verify.add_argument("--timeout", type=int, default=180)
    dashboard = commands.add_parser("dashboard", help="Serve the workbench on loopback")
    dashboard.add_argument("--port", type=int, default=8765)
    proof = commands.add_parser("prove", help="Run the installed ATP on a TPTP problem")
    proof.add_argument("problem", type=Path)
    proof.add_argument("--timeout", type=int, default=10)
    proof.add_argument("--prover", choices=("e", "v"), default="e")
    proof.add_argument("--output", type=Path, help="Fresh repository-local capture directory")
    comparison = commands.add_parser("compare-provers", help="Compare E/V on identical input bytes")
    comparison.add_argument("problem", type=Path)
    comparison.add_argument("--timeout", type=int, default=10)
    comparison.add_argument("--output", type=Path, help="Fresh repository-local comparison directory")
    research = commands.add_parser("research-run", help="Run the declared finite alignment study")
    research.add_argument("output", type=Path, help="Fresh repository-local campaign directory")
    research.add_argument("--prover", choices=("e", "v"), default="e")
    research.add_argument("--workbook", type=Path)
    research.add_argument("--source-report", type=Path)
    replay = commands.add_parser("research-verify", help="Replay retained finite study evidence")
    replay.add_argument("report", type=Path)
    replay.add_argument("--sha256", help="Separately trusted outer report digest")
    cache = commands.add_parser("cache-diagnostic", help="Build isolated fresh Sigma cache controls")
    cache.add_argument("output", type=Path, help="Fresh repository-local evidence directory")
    cache.add_argument("--timeout", type=int, default=60)
    taxonomy = commands.add_parser(
        "taxonomy-proof", help="Prove a source-bound first-order subclass projection"
    )
    taxonomy.add_argument("subject")
    taxonomy.add_argument("target")
    taxonomy.add_argument("--timeout", type=int, default=10)
    commands.add_parser("mcp", help="Serve the read-only MCP interface over stdio")
    return result


def execute(args: argparse.Namespace) -> tuple[object, int]:
    root = args.root.resolve()
    index = OntologyIndex(root / ".rikishi" / "ontology.sqlite")
    match args.command:
        case "active-demo":
            from rikishi.active_inference import demo as active_demo

            return active_demo(), 0
        case "bridge-catalog" | "bridge-run" | "bridge-verify" | "bridge-case" | "bridge-figures":
            from rikishi.bridge_cli import execute as execute_bridge

            return execute_bridge(args)
        case "inference-catalog" | "inference-run" | "inference-verify" | "inference-publish":
            from rikishi.inference_cli import execute as execute_inference

            return execute_inference(args)
        case "files" | "formulas" | "relations" | "taxonomy" | "taxonomy-path":
            from rikishi.analysis_cli import execute as execute_analysis

            return execute_analysis(index, args), 0
        case "index":
            stats = index.build(args.source or root / ".rikishi/upstream/sumo")
            index.export(root / "output/data")
            return stats, 1 if stats["parse_errors"] else 0
        case "stats":
            return index.stats(), 0
        case "verify-source":
            from rikishi.source_audit import audit_sources

            audit = audit_sources(index)
            return audit.to_dict(), 0 if audit.passed else 1
        case "metrics":
            from rikishi.analytics import measure_corpus

            return measure_corpus(index), 0
        case "search":
            return index.search(args.query, args.limit), 0
        case "term":
            return index.term(args.name), 0
        case "graph":
            return index.neighborhood(args.name, args.limit, args.relation), 0
        case "doctor" | "bootstrap":
            from rikishi import runtime

            return (
                runtime.status(root) if args.command == "doctor" else runtime.bootstrap(root)
            ), 0
        case "prove":
            from rikishi.runtime import prove

            result = prove(args.problem, root, args.timeout, prover=args.prover, output=args.output)
            return result, 0 if result["proved"] else 1
        case "compare-provers":
            from rikishi.runtime import compare

            result = compare(args.problem, root, args.timeout, output=args.output)
            return result, 0 if result["outcome"] == "agreement" else 2
        case "research-run":
            from rikishi.alignment import run_alignment

            report = run_alignment(root, args.output, prover=args.prover,
                                   workbook_path=args.workbook, source_report=args.source_report)
            return report.model_dump(mode="json"), 0 if report.summary.campaign_complete else 2
        case "research-verify":
            from rikishi.alignment import validate_alignment_report

            report = validate_alignment_report(args.report, trusted_report_sha256=args.sha256)
            return report.model_dump(mode="json"), 0 if report.summary.campaign_complete else 2
        case "cache-diagnostic":
            from rikishi.cache_inheritance import diagnose_cache_inheritance

            result = diagnose_cache_inheritance(root, args.output, timeout=args.timeout)
            return result, 0 if result["status"] == "observed" else 2
        case "taxonomy-proof":
            from rikishi.projection import taxonomy_problem
            from rikishi.runtime import prove

            output = root / "output/reasoning/taxonomy.p"
            metadata = taxonomy_problem(index, args.subject, args.target, output)
            result = prove(output, root, args.timeout)
            result["scope"] = metadata["scope"]
            result["source_commit"] = metadata["source_commit"]
            result["source_clean"] = metadata["source_clean"]
            result["source_file_sha256"] = metadata["source_file_sha256"]
            output.with_suffix(".result.json").write_text(json.dumps(result, indent=2) + "\n")
            return result, 0 if result["proved"] else 1
        case "fep-demo":
            from rikishi.fep import demo

            return demo(), 0
        case "fep-evaluate":
            from rikishi.fep import evaluate_model

            return evaluate_model(args.model, logarithmic=args.logarithmic), 0
        case "fep-inspect":
            from rikishi.fep import inspect_formalization

            repo = args.repo or Path(
                os.environ.get(
                    "RIKISHI_FEP_REPO",
                    str(root.parents[2] / "ActiveInferenceInstitute/Public/fep_formal"),
                )
            )
            return inspect_formalization(repo), 0
        case "fep-verify":
            from rikishi.formal_verification import verify_formalization

            repo = args.repo or Path(os.environ.get(
                "RIKISHI_FEP_REPO", str(root.parents[2] / "ActiveInferenceInstitute/Public/fep_formal")
            ))
            compiler = args.compiler or Path(os.environ.get(
                "RIKISHI_LEAN", str(root.parents[3] / "Local/runtimes/elan/toolchains/"
                                   "leanprover--lean4---v4.35.0/bin/lean")
            ))
            output = args.output or root / "output/formalization" / f"verification-{time.time_ns()}"
            return verify_formalization(repo, compiler, output, packages=args.packages,
                                        timeout=args.timeout), 0
        case "dashboard":
            import uvicorn

            from rikishi.dashboard import create_app

            if not 1 <= args.port <= 65535:
                raise ValueError("port must be between 1 and 65535")
            uvicorn.run(create_app(index.path), host="127.0.0.1", port=args.port)
            return None, 0
        case "report":
            from rikishi.reports import build_report

            corpus = index.export(root / "output/data")
            return {"corpus": corpus, "report": build_report(index.path, root / "output")}, 0
        case "mcp":
            from rikishi.mcp_server import create_server

            create_server(root).run(transport="stdio")
            return None, 0
        case _:
            raise ValueError(f"Unknown command: {args.command}")


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        result, status = execute(args)
    except (
        OSError,
        ValueError,
        KeyError,
        RuntimeError,
        sqlite3.Error,
        subprocess.SubprocessError,
    ) as error:
        sys.stderr.write(json.dumps({"error": type(error).__name__, "message": str(error)}) + "\n")
        return 1
    if result is not None:
        sys.stdout.write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    return status

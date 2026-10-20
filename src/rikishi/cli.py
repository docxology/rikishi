import argparse
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

from rikishi.ontology import OntologyIndex


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="rikishi", description="Operate the real SUMO corpus")
    result.add_argument("--root", type=Path, default=Path(os.environ.get("RIKISHI_ROOT", ".")))
    commands = result.add_subparsers(dest="command", required=True)
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
    commands.add_parser("stats", help="Measure indexed corpus")
    commands.add_parser("report", help="Export corpus manifest, dashboard, and figures")
    commands.add_parser("fep-demo", help="Run a finite variational free-energy example")
    inspect = commands.add_parser("fep-inspect", help="Inspect proposed Lean/SUMO source mappings")
    inspect.add_argument("--repo", type=Path)
    dashboard = commands.add_parser("dashboard", help="Serve the workbench on loopback")
    dashboard.add_argument("--port", type=int, default=8765)
    proof = commands.add_parser("prove", help="Run the installed ATP on a TPTP problem")
    proof.add_argument("problem", type=Path)
    proof.add_argument("--timeout", type=int, default=10)
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
        case "index":
            stats = index.build(args.source or root / ".rikishi/upstream/sumo")
            index.export(root / "output/data")
            return stats, 1 if stats["parse_errors"] else 0
        case "stats":
            return index.stats(), 0
        case "search":
            return index.search(args.query, args.limit), 0
        case "term":
            return index.term(args.name), 0
        case "graph":
            return index.neighborhood(args.name, args.limit), 0
        case "doctor" | "bootstrap":
            from rikishi import runtime

            return (
                runtime.status(root) if args.command == "doctor" else runtime.bootstrap(root)
            ), 0
        case "prove":
            from rikishi.runtime import prove

            result = prove(args.problem, root, args.timeout)
            return result, 0 if result["proved"] else 1
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
        case "fep-inspect":
            from rikishi.fep import inspect_formalization

            repo = args.repo or Path(
                os.environ.get(
                    "RIKISHI_FEP_REPO",
                    str(root.parents[2] / "ActiveInferenceInstitute/Public/fep_formal"),
                )
            )
            return inspect_formalization(repo), 0
        case "dashboard":
            import uvicorn

            from rikishi.dashboard import create_app

            if not 1 <= args.port <= 65535:
                raise ValueError("port must be between 1 and 65535")
            uvicorn.run(create_app(index.path), host="127.0.0.1", port=args.port)
            return None, 0
        case "report":
            from rikishi.dashboard import build_report

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

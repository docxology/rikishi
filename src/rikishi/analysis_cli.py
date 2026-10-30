from __future__ import annotations

import argparse

from rikishi.corpus_query import FileQuery, FormulaQuery
from rikishi.ontology import OntologyIndex
from rikishi.ontology_analysis import TaxonomyQuery
from rikishi.taxonomy_paths import TaxonomyPathQuery


def register(commands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    files = commands.add_parser("files", help="Page indexed source files and SHA-256 identities")
    files.add_argument("--path", default="", help="Literal filename substring")
    files.add_argument("--sort", choices=("path", "formulas"), default="path")
    files.add_argument("--descending", action="store_true")
    formulas = commands.add_parser("formulas", help="Search complete source formulas with locations")
    for name in ("text", "head", "path", "term"):
        formulas.add_argument(f"--{name}", default="")
    commands.add_parser("relations", help="Inventory all direct binary relations and multiplicity")
    taxonomy = commands.add_parser("taxonomy", help="Measure a direct source taxonomy graph")
    path = commands.add_parser("taxonomy-path", help="Find a bounded, source-backed taxonomy path")
    path.add_argument("source")
    path.add_argument("target")
    path.add_argument("--max-depth", type=int, default=20)
    path.add_argument("--max-visited", type=int, default=10_000)
    for command in (taxonomy, path):
        command.add_argument("--relation", choices=("subclass", "subrelation"), default="subclass")
        command.add_argument("--path", default="", help="Exact source file, or all indexed files")
    for command in (files, formulas, taxonomy):
        command.add_argument("--limit", type=int, default=50)
        command.add_argument("--offset", type=int, default=0)


def execute(index: OntologyIndex, args: argparse.Namespace) -> object:
    match args.command:
        case "files":
            return index.corpus_files(FileQuery(
                path=args.path, sort=args.sort, descending=args.descending,
                limit=args.limit, offset=args.offset,
            ))
        case "formulas":
            return index.formula_search(FormulaQuery(
                text=args.text, head=args.head, path=args.path, term=args.term,
                limit=args.limit, offset=args.offset,
            ))
        case "relations":
            return index.relation_inventory()
        case "taxonomy":
            return index.taxonomy_analysis(TaxonomyQuery(
                relation=args.relation, path=args.path, limit=args.limit, offset=args.offset,
            ))
        case "taxonomy-path":
            return index.taxonomy_path(TaxonomyPathQuery(
                source=args.source, target=args.target, relation=args.relation, path=args.path,
                max_depth=args.max_depth, max_visited=args.max_visited,
            ))
        case _:
            raise ValueError(f"Unknown analysis command: {args.command}")

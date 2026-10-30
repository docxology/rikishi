"""Run source-bound demonstrations using the repository's locked environment."""

import argparse
import json
from pathlib import Path

from rikishi.ontology import OntologyIndex
from rikishi.sumo_demonstrations import demonstrate_sumo, prove_sumo_taxonomy


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--index", type=Path, default=Path(".rikishi/ontology.sqlite"))
    parser.add_argument("--output", type=Path, help="Fresh root-relative report JSON path")
    parser.add_argument("--proof-directory", type=Path, help="Fresh root-relative native proof directory")
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    index = OntologyIndex(root / args.index)
    report = demonstrate_sumo(index, root)
    if args.output:
        output = root / args.output
        output.resolve().relative_to(root)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as stream:
            stream.write(report.model_dump_json(indent=2) + "\n")
    else:
        print(report.model_dump_json(indent=2))
    if args.proof_directory:
        proof = prove_sumo_taxonomy(index, root, args.proof_directory)
        with (root / args.proof_directory / "demonstration.json").open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(proof, indent=2) + "\n")


if __name__ == "__main__":
    main()

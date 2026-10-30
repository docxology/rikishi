import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from rikishi.reports import build_report


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Export the measured SUMO corpus dashboard")
    parser.add_argument("--index", type=Path, default=Path(".rikishi/ontology.sqlite"))
    parser.add_argument("--output", type=Path, default=Path("output/web"))
    args = parser.parse_args(argv)
    print(json.dumps(build_report(args.index, args.output), indent=2))


if __name__ == "__main__":
    main()

import argparse
import json
from pathlib import Path

from rikishi.dashboard import build_report

parser = argparse.ArgumentParser(description="Export the measured SUMO corpus dashboard")
parser.add_argument("--index", type=Path, default=Path(".rikishi/ontology.sqlite"))
parser.add_argument("--output", type=Path, default=Path("output/web"))
args = parser.parse_args()
print(json.dumps(build_report(args.index, args.output), indent=2))

# Rikishi manuscript source

The [offline companion](00_abstract.md) documents the asserted-edge
index using a reproducible local catalog. Its
[methods](02_methods.md), [results](03_results.md), [configuration](config.yaml)
and [bibliography](references.bib) are in this directory.

The [native research manuscript](native/rikishi.md.in) retains the full
scientific narrative, [bibliography](native/references.bib),
[publication configuration](native/manuscript.yaml), and
[citation style](native/references.csl). Its `.md.in` suffix identifies the authored
input that the native renderer hydrates before rendering. Follow the
[native recipe](../publication/manuscript.md) to render and verify
its research editions against the required campaigns and receipts.
Previously rendered native editions should be replayed using the
source revision and input paths recorded in their own receipts.

## Build the offline companion

Run from a Rikishi source checkout with Git, uv, Python 3.12,
Graphviz, Pandoc 3.14, XeLaTeX, BibTeX and Poppler available.
The fixture uses the source package directly with the Python standard
library. Template installs its own locked renderer dependencies in
the temporary checkout.

```bash
set -e
source_checkout=$(pwd -P)
commit=$(git rev-parse HEAD)
scratch=$(mktemp -d)
renderer="$scratch/template"
git clone https://github.com/docxology/template.git "$renderer"
git -C "$renderer" checkout --detach 87704feae0a4490ef7dad9c931d268e8c30273c2
mkdir -p "$renderer/projects/working"
git clone "$source_checkout" "$renderer/projects/working/rikishi"
cd "$renderer/projects/working/rikishi"
git checkout --detach "$commit"

PYTHONPATH=src uv run --no-project --python 3.12 python - <<'PYTHON'
import hashlib
import json
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from rikishi.ontology import OntologyIndex

catalog = (
    b"(subclass Cup Container)\n"
    b"(instance SampleCup Cup)\n"
    b'(documentation Cup EnglishLanguage "A vessel for a drink")\n'
    b"(forall (?X) (=> (instance ?X Cup) (instance ?X Container)))\n"
)
with TemporaryDirectory() as scratch:
    workspace = Path(scratch)
    source = workspace / "source"
    source.mkdir()
    (source / "Catalog.kif").write_bytes(catalog)
    index = OntologyIndex(workspace / "catalog.sqlite")
    stats = index.build(source)
    cup = index.term("Cup")
    sample = index.term("SampleCup")

rule = next(record for record in cup["formulas"] if record["predicate"] == "forall")
assert stats["formulas"] == 4 and stats["edges"] == 2 and not stats["parse_errors"]
assert (rule["path"], rule["line"]) == ("Catalog.kif", 4)
assert (cup["documentation"][0]["path"], cup["documentation"][0]["line"]) == ("Catalog.kif", 3)
assert sample["parents"] == [{"name": "Cup", "relation": "instance"}]
assert cup["parents"] == [{"name": "Container", "relation": "subclass"}]
report = {
    "source_file": "Catalog.kif",
    "source_sha256": hashlib.sha256(catalog).hexdigest(),
    "formulas": stats["formulas"],
    "asserted_edges": stats["edges"],
    "implication": rule,
    "documentation": cup["documentation"],
    "parents": {"SampleCup": sample["parents"], "Cup": cup["parents"]},
}
data = Path("output/data/catalog-index.json")
image = Path("output/figures/catalog-index.png")
data.parent.mkdir(parents=True, exist_ok=True)
image.parent.mkdir(parents=True, exist_ok=True)
data.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
lines = [
    "digraph asserted {",
    'graph [rankdir=LR, dpi=180, bgcolor="white"];',
    'node [shape=box, style=rounded, fontname="DejaVu Sans"];',
    'edge [fontname="DejaVu Sans"];',
]
for child, parents in report["parents"].items():
    for parent in parents:
        target = json.dumps(parent["name"])
        label = json.dumps(parent["relation"])
        lines.append(f"{json.dumps(child)} -> {target} [label={label}];")
lines.append("}")
subprocess.run(["dot", "-Tpng", "-o", str(image)],
               input="\n".join(lines), text=True, check=True)
PYTHON

cd "$renderer"
uv sync --locked
uv run --no-sync python scripts/pipeline/stage_03_render.py --project working/rikishi
uv run --no-sync python scripts/pipeline/stage_04_validate.py --project working/rikishi
printf '%s\n' "$renderer/projects/working/rikishi/output"
```

Under that output directory, `data/catalog-index.json` holds the
observations, `figures/catalog-index.png` visualizes the retrieved
edges, `pdf/` and `web/` hold the rendered editions, and `reports/`
contains validation and provenance records.

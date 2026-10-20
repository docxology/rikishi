# CLI, Python, HTTP, and MCP interfaces

All examples run from the checkout after `source scripts/env.sh` and
`uv sync --locked`. `--root PATH` precedes the CLI subcommand; `RIKISHI_ROOT`
supplies its default. Local state is under `.rikishi/`, generated exports under
`output/`. The complete environment requires `uv run rikishi bootstrap`.

| CLI | Operation |
| --- | --- |
| `bootstrap` | Check out pinned upstream sources and build the local runtime |
| `doctor` | Inspect actual source revisions and installed artifacts |
| `index [--source DIR]` | Recursively parse `.kif`, build SQLite atomically, export manifest |
| `stats` | Counts, per-file formula totals, predicates, parse errors, revision |
| `search Organism [--limit 30]` | Case-insensitive substring search of term names |
| `term Organism` | Documentation, first 100 referencing formulas, asserted taxonomy |
| `graph Organism [--limit 80]` | Bounded adjacent asserted binary relationships |
| `taxonomy-proof Human AutonomousAgent` | Run E on an explicit first-order projection of `Merge.kif` |
| `prove problem.p [--timeout 10]` | Run installed E on a TPTP problem with CPU and wall limits |
| `fep-demo` | Finite inference model, independent decomposition, and objective scan |
| `fep-inspect [--repo DIR]` | Read committed Lean declarations at the recorded FEP pin |
| `dashboard [--port 8765]` | Serve the workbench on `127.0.0.1` |
| `report` | Corpus JSON and source manifest, standalone HTML and PNG/SVG chart |
| `mcp` | Serve read-only MCP over standard input/output |

Finite commands return JSON. Missing terms, malformed probabilities, absent
artifacts, and failed subprocesses return nonzero status and a JSON error on
stderr. `index` returns nonzero if any source file fails structural parsing;
its result retains the complete diagnostic list. A malformed file contributes
no partially parsed formulas. `prove` and `taxonomy-proof` return zero only for
the SZS `Theorem` outcome. `doctor` is an inspection, not a running-service gate.

`taxonomy-proof` emits `output/reasoning/taxonomy.p`, its source/line manifest
`taxonomy.json`, and full prover output `taxonomy.result.json`. It selects direct
`subclass` facts from `Merge.kif` and explicitly adds subclass transitivity. This
is a restricted first-order projection: a countermodel there is not a claim that
the corresponding full SUMO query is false. Running a subsequent query replaces
these working files; copy an experiment to a named evidence directory to retain it.

## Python

```python
from pathlib import Path
from rikishi.ontology import OntologyIndex
from rikishi.fep import free_energy

index = OntologyIndex(Path(".rikishi/ontology.sqlite"))
organism = index.term("Organism")
result = free_energy([0.5, 0.5], [0.8, 0.2], [0.8, 0.2])
assert abs(result["free_energy"] - result["surprise"]) < 1e-12
```

`build(source)` indexes nested domain, translation, development, and test KIF
files. These structural counts differ from Sigma's selected knowledge-base
profile. Numeric literals, strings, logical connectives, and variables are not
counted as term symbols. Repeated formulas contribute separate source occurrences.
Only top-level binary atomic assertions become edges; expressions inside
implications and quantified bodies remain available as formula text.

## HTTP

The read-only workbench exposes `/api/stats`, `/api/search?q=Organism`,
`/api/terms/Organism`, `/api/graph?term=Organism&limit=40`, and `/api/fep?q=0.8`.
OpenAPI is available at `/docs`. Invalid bounds produce HTTP 422 and unknown
terms produce HTTP 404. HTTP has no bootstrap, filesystem-write, proof-execution,
or upstream-publication endpoint. Source strings are rendered as text.

## MCP

Run `uv run --locked rikishi mcp` or `uv run --locked rikishi-mcp` in the
checkout. Configure a client's supported process environment and working directory.
`config/mcp.example.json` is an illustrative configuration: replace the
`${RIKISHI_ROOT}` placeholders with your actual path because not all MCP clients
expand environment variables in configuration values. Source `scripts/env.sh`
before launching a client to retain external cache bindings.

| Tool | Arguments | Result |
| --- | --- | --- |
| `corpus_stats` | None | Measured counts, source revision, parse errors |
| `search_terms` | `query`, `limit` 1–200 | Term names and documentation preview |
| `inspect_term` | Exact `name` | Source-bound definition and formulas |
| `relation_graph` | Exact `name`, `limit` 1–500 | Asserted neighboring edges |
| `finite_free_energy` | `prior`, `likelihood`, `posterior` | Evidence, F, surprise, KL, residual |

Resources: `sumo://corpus` and `rikishi://fep-example`. MCP startup performs no
download or index mutation. Tool failures remain protocol error results; stdout
is reserved for MCP frames. `tests/test_mcp_transport.py` launches an actual
stdio client/server and checks initialization, results, and invalid requests.

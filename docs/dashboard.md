# Ontology workbench

Run `rikishi serve` after building the ontology index. The default server binds
to loopback. The dashboard reads the same SQLite index used by the CLI and MCP.
It does not download, edit, or infer ontology assertions through HTTP.

Search a term name, select a result, then follow a graph node.
Each term shows its documentation, a bounded direct-relationship neighborhood,
and source formulas with relative file paths and starting line numbers. The
accessible relationship list provides the same navigation without interpreting
the graph. Source formulas expand with native keyboard-operable disclosure controls.

The graph shows direct indexed edges; it is not an inferred closure. Arrows run
from subject to object. The graph is capped at 40 edges to keep the view usable.
Search results are capped at 30. Empty searches, missing terms, and HTTP failures
have explicit visible states. Concurrent navigation discards stale responses.

## Measurements

The overview counts indexed source files, top-level KIF formulas, terms, and
direct relationship edges. The bar chart measures formulas per source file.
These counts are not counts of independent facts, consistency evidence, or
proved theorems. The source commit and parser errors are included in the JSON
measurements and portable report.

Export a portable report and manuscript figures:

```sh
uv run python scripts/build_dashboard.py --index .rikishi/ontology.sqlite --output output/web
```

Outputs are `dashboard.html` (embedded CSS and measured JSON, offline filtering
and theme switching), `corpus.json`, `corpus-files.svg`, and `corpus-files.png`.
The portable report summarizes the indexed top-file list; live term search
requires the server. It loads no CDN resources. Its JSON escapes less-than
characters so corpus metadata cannot terminate the embedded data element.

## HTTP API

| Route | Behavior |
| --- | --- |
| `GET /api/stats` | Corpus counts, per-file counts, provenance, parse errors |
| `GET /api/search?q=Agent&limit=30` | Search results; limit 1–100 |
| `GET /api/terms/Agent` | Documentation, source formulas, parents, children |
| `GET /api/graph?term=Agent&limit=40` | Direct graph; limit 1–100 |
| `GET /api/fep?q=0.8` | Finite example with candidate belief q in [0,1] |
| `GET /docs` | Generated OpenAPI documentation |

Unknown terms return HTTP 404. Invalid limits and empty queries return HTTP 422.
Missing database files prevent startup. Tests use real indexed KIF files and
FastAPI's HTTP client; no mocked ontology responses are used.

## Finite inference explorer

The slider calls the shared `rikishi.fep.free_energy` implementation with prior
`[0.5, 0.5]` and observation likelihoods `[0.8, 0.2]`. It reports free energy,
surprisal, KL divergence, and evidence, with the decomposition residual shown
explicitly. The minimum occurs at q=0.8. Values use natural logarithms (nats).
The example illustrates a finite identity; it does not claim SUMO entails the
Free Energy Principle or that a numerical calculation verifies a Lean proof.

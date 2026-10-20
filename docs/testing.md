# Test suites and quality gates

Run from the checkout with `source scripts/env.sh` and `uv sync --locked`.
All test temporaries use the external `TMPDIR`. The session-level `project_root`
fixture locates source independently of test nesting. The shared `git_commit`
fixture creates real commits with repository-local identity; `corpus_factory`
creates actual KIF files and SQLite indexes. No mocking framework is used.

| Suite | Behavior exercised |
| --- | --- |
| `tests/unit/` | Parsing, finite arithmetic, indexing, source audit, coverage-gate rejection |
| `tests/inference/` | Projection manifests and actual E theorem/countermodel controls |
| `tests/interfaces/` | CLI dispatch, subprocess entrypoint, real MCP stdio protocol |
| `tests/dashboard/` | HTTP contracts, exact analytics, source-backed report artifacts |
| `tests/runtime/` | Acquisition preservation, strict ATP results, native tools and adapters |
| `tests/manuscript/` | Real Git snapshots, hydration, artifact integrity, native render/verify |

Portable development gate:

```bash
uv run pytest -m 'not integration'
uv run ruff check src tests scripts
uv build
```

The `integration` marker declares dependencies on installed ontology/native tools
or canonical renderer inputs. Portable success does not establish the native
runtime or manuscript results. Native cases fail explicitly when prerequisites
are absent; they do not silently skip a missing installation.

Full workstation gate:

```bash
uv run pytest --cov=rikishi --cov-report=term-missing \
  --cov-report=json:output/coverage.json --junitxml=output/tests.xml
uv run python scripts/check_coverage.py --output output/coverage-gates.json
uv run ruff check src tests scripts
uv build
```

The second command is mandatory. It sums covered executable lines and covered
branch destinations, divided by executable lines plus branch destinations, for
two disjoint scopes. Core code must reach 90%; native setup, server/query
orchestration, and rendering infrastructure must reach 60%. Exact infrastructure
paths are versioned in `config/coverage.toml`. All other package Python files
enter the core scope automatically. The general report's 60% floor is a coarse
guard only. No package source file may be omitted or have excluded lines.

Coverage-gate tests deliberately reduce each scope below its floor, omit source
files, inject excluded lines, supply impossible counts, and corrupt policy paths.
These must fail. Probability tests compare independent logarithmic values;
inference tests require both theorem and countermodel outcomes; runtime tests
reject log-echo spoofing, stale invocation identifiers, malformed sidecars, and
unsuccessful ATP exits. Renderer tests alter real source/artifact bytes and
require rejection. Passing a positive fixture alone is insufficient evidence.

The full native suite regenerates manuscript artifacts. Retain
`output/manuscript/render-receipt.json` with the matching visual inspection.
The GitVault repository-operation lease serializes shared workstation gates and
publication; it is a workstation coordination mechanism, not a package dependency.

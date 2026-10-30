# Rikishi development contract

Implement in `src/rikishi/`; scripts and CLI commands orchestrate those methods.
Use Python 3.12 and `uv sync --locked`. Keep source, environments, caches, temporary
files and outputs on mounted GitVault; source `scripts/env.sh` and verify both
Python prefixes before work.

Run `make check` for lint, static types, the full native test suite, coverage gates,
and package builds. `make portable` excludes installed-tool cases. Tests use real
files, Git repositories, HTTP and subprocesses, with no mocking frameworks.
Core coverage must reach 90% including branches; the exact native infrastructure
scope in `config/coverage.toml` must reach 60%. Both gates are mandatory.
A check must reject its negative control; retain failed executions as evidence.

Keep SUMO, Sigma and dependency revisions pinned. Preserve source file/line and
input hashes with results. Parsed formulas, asserted edges, ATP outcomes, finite
calculations and Lean proofs have distinct acceptance scopes. Read
[method contracts](docs/architecture.md) before changing those scopes and
[runtime findings](docs/runtime.md) before interpreting native inference.
For alignment experiments, read [the finite study contract](docs/research.md)
before changing its encoding, expected polarities or numerical tolerances.
For corpus filters, pagination, graph diagnostics or source paths, read
[ontology analysis](docs/ontology-analysis.md); share its methods across transports.

Use the verified canonical template snapshot for rendering; regenerate reports
before the manuscript. See [testing](docs/testing.md) for gates and
[manuscript methods](docs/manuscript.md) for artifact verification.
Keep canonical upstream and `fep_formal` checkouts unchanged. Upstream reports need
an independently reproduced finding and reviewed public evidence; private research
stays private. Record current acceptance evidence under `.omo/evidence/`.

Author skills in `.agents/skills/`; `skills/` is its distribution projection.
Run `uv run python scripts/sync_skills.py --write` after edits; `make check`
rejects drift, missing copies and unexpected distribution entries.

# Rikishi operator instructions

The active package is `src/rikishi/`. `template_reference/` preserves the original
optimization exemplar; it is provenance, not the SUMO test suite. Its instructions
apply inside that reference tree. `_template_resources/` preserves the template's
rendering infrastructure. Do not attribute its optimization results or DOI to Rikishi.

Use Python 3.12 and `uv sync --locked`, `uv run pytest`, and `uv run ruff check`.
The project coverage gate is 90% including branches. Tests use real files, local
HTTP, and subprocesses, with no mocking frameworks. Negative controls must reject
malformed KIF, missing terms, invalid probability inputs, and unsuccessful proofs.

SUMO sources live under `.rikishi/upstream/`; keep upstream revisions pinned and
source file/line references attached to results. A parsed formula, asserted edge,
theorem-prover result, and Lean theorem are different kinds of evidence. The FEP
alignment is a proposed interpretation, not a proof of semantic equivalence.

Keep source, runtime, caches, environments, temporary files, and outputs on the
mounted GitVault. Check both Python prefixes. Use `scripts/env.sh` to bind caches.
Do not edit `fep_formal` or upstream clones as part of normal operation. Upstream
issue and PR workflows require a reproducible, independently reviewed finding.
Never publish private research into an upstream report.

Scripts orchestrate; importable modules implement. Regenerate `output/` with the
documented commands. Read `docs/runtime.md` for actual Sigma/ATP capabilities and
`docs/verification.md` for observed acceptance evidence.

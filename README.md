# Rikishi

A private SUMO ontology operator and research workbench. **Rikishi** is a sumo
wrestler; this package operates the Suggested Upper Merged Ontology.

Rikishi checks out the real [ontologyportal/SUMO](https://github.com/ontologyportal/sumo)
corpus at a recorded revision, indexes SUO-KIF with source provenance, serves an
interactive local workbench, runs theorem-prover examples, exposes read-only MCP
tools, and explores explicitly proposed links to
[fep_formal](https://github.com/ActiveInferenceInstitute/fep_formal).

**Observed inference limitation:** the current Sigma-translated core returned
`ContradictoryAxioms` in a negative control. Treat full-core inference as diagnostic
until its cause is resolved. Rikishi retains the raw status and logs. Source
browsing, the restricted taxonomic projection, and finite numerical examples have
separate checks. See [verification evidence](docs/verification.md).

## Start

From this checkout on the mounted GitVault:

```bash
source scripts/env.sh
uv sync --locked
uv run rikishi bootstrap
uv run rikishi index
uv run rikishi search Organism
uv run rikishi term Organism
uv run rikishi taxonomy-proof Human AutonomousAgent
uv run rikishi dashboard --port 8765
```

Open `http://127.0.0.1:8765`. The dashboard reads the actual local ontology index.
It includes corpus measurements, source-linked term inspection, asserted relation
graphs, and a finite free-energy explorer. See [runtime setup](docs/runtime.md)
for Java, SigmaKEE, and ATP installation and capability boundaries.

```bash
uv run rikishi doctor
uv run rikishi fep-demo
uv run rikishi fep-inspect --repo ../../../ActiveInferenceInstitute/Public/fep_formal
uv run rikishi report
uv run python scripts/render_manuscript.py
uv run rikishi mcp
uv run pytest --cov=rikishi --cov-report=term-missing
uv run ruff check src tests scripts
```

The `fep-inspect` path may instead be supplied with `RIKISHI_FEP_REPO`.
Read [the operator documentation](docs/README.md), [API and MCP](docs/API.md),
[dashboard](docs/dashboard.md), and [verification evidence](docs/verification.md).
Project skills are under [`skills/`](skills/).

## Evidence boundaries

The corpus index is a structural reader, not a complete SUO-KIF semantic validator.
Asserted graph edges are not inferred theorems. A bounded ATP example does not
establish consistency or completeness of the whole ontology. FEP crosswalks are
research proposals tied to source declarations, not Lean-to-SUMO translations.

The package is derived from `docxology/template_code_project` at the revision in
[`config/template-origin.json`](config/template-origin.json). The original
optimization exemplar is preserved under `template_reference/`; the shared
template infrastructure is under `_template_resources/`. Rikishi has its own
source, tests, manuscript, metadata, and generated results. Original template
DOIs and optimization outputs do not describe this project.

## Licensing

Rikishi operator code uses the MIT license in `LICENSE`. Upstream SUMO and Sigma
retain their own notices and licenses; they are downloaded into ignored local
storage and are not relicensed by Rikishi. Source references and attribution are
preserved in generated manifests and documentation. Nothing publishes to Zenodo,
PyPI, or upstream SUMO automatically.

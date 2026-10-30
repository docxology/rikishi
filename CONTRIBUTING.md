# Contributing to Rikishi

Rikishi keeps source expressions, inference outcomes, finite calculations and
formal statements as separate evidence objects. Contributions should make those
boundaries easier to inspect and reproduce. Start with the
[documentation map](docs/README.md), [installation guide](docs/installation.md),
[method architecture](docs/architecture.md), and [prioritized backlog](docs/TODO.md).

## Make one coherent change

Describe the observed problem, expected behavior and actual evidence before
changing a method. Reproduce a defect with real inputs and a check that can fail;
retain the failing result and demonstrate that an incorrect implementation or
input is rejected. Do not adjust expected values, budgets, source pins or
assertions merely to obtain a green run.

Put reusable methods in `src/rikishi/`; scripts and command-line interface (CLI) commands orchestrate
them. Keep interfaces, types, guides and tests consistent with the actual
behavior. Use Python 3.12, uv and the committed lockfile. Tests use real files,
local Hypertext Transfer Protocol (HTTP) and subprocesses; mocking frameworks cannot substitute for these
boundaries. Seed simulations and state their finite-model assumptions. Clearly
label deliberately synthetic test fixtures and never present them as native or
reported scientific evidence.

Preserve unrelated dirty work, failed outputs, source snapshots and sealed
records. Keep upstream Suggested Upper Merged Ontology (SUMO)/Sigma/dependency pins explicit and leave canonical
upstream and formalization checkouts unchanged. Upstream issue reports need an
independently reproduced finding and a reviewed public reproducer, not private
logs or an inferred diagnosis.

## Workstation admission and isolated tests

On the managed GitVault workstation, source `scripts/env.sh`, verify that both
Python prefixes are external, and acquire the supported repository lease for
commands that mutate or test canonical state. From the vault root, for example:

```bash
./_tools/vault --wait with-repo --label rikishi-full-check docxology/rikishi -- \
  bash -c '
    set -euo pipefail
    source scripts/env.sh
    unset PYTHONPATH VIRTUAL_ENV
    export UV_PROJECT_ENVIRONMENT="$PWD/.venv"
    export UV_PYTHON="$PWD/.venv/bin/python"
    task_tmp=$(mktemp -d "${TMPDIR%/}/rikishi-check.XXXXXX")
    export PYTEST_ADDOPTS="--basetemp=$task_tmp/pytest -p no:cacheprovider"
    export PYTHONDONTWRITEBYTECODE=1 UV_FROZEN=1 UV_NO_SYNC=1 UV_OFFLINE=1
    make check
  '
```

This example assumes prerequisites and the locked environment are already
prepared. Select and verify the actual `RIKISHI_CHROMIUM` executable, stop only
the Rikishi Sigma instance you own through its supported lifecycle, and follow
the full [testing prerequisites](docs/testing.md). Keep the selected temporary
tree after failure for inspection; do not prune shared pytest roots or another
owner's artifacts.

Different repositories can proceed concurrently. The same repository identity
or shared Git store serializes. Never remove `index.lock`, ref locks or held
GitVault lock files; request the correct admission rather than bypassing it.
An unrelated repository's tests do not gate this project's work. Collection-wide
configuration, migration and shared-tool deployment retain their genuine
exclusive-admission requirements.

## Validate and submit

During development, run the focused checks for the changed behavior and
`make portable` with its public source inputs and a unique external `--basetemp`.
The complete candidate requires `make check`: skill projection, lint, types,
the full native suite, both branch-inclusive coverage floors (90% core and
60% infrastructure), and package builds. Preserve warnings and raw exits.
Missing native prerequisites are failures or explicit unverified scopes, not
fabricated successes or silently removed tests.

For manuscript changes, regenerate from the declared packets and pinned
renderer, then inspect every actual page and figure. Read the
[review protocol](docs/review.md). Match documentation links, public CLI/application programming interface (API)
examples, package data and citation metadata to the resulting source. Author
agent skills under `.agents/skills/` and update their `skills/` projection with
the repository's checked synchronization method.

Submit a bounded description of the resulting behavior, relevant before/after
evidence, actual tests and remaining limitations. Keep independent review
separate from the builder's verification. A contribution or local test pass does
not authorize a release, visibility change, digital object identifier (DOI) deposit or scientific claim;
those follow the [release process](docs/release.md).

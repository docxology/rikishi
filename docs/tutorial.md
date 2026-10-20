# From ontology source to a reproducible result

This walkthrough starts in the Rikishi repository with its `uv` environment.
Follow [runtime setup](runtime.md) first to install the pinned SUMO, Sigma, and E
components. Keep the shell's cache and temporary bindings on the project storage
volume as described in the README.

## Establish the environment

```bash
uv run rikishi doctor
uv run rikishi index
uv run rikishi stats
uv run rikishi report
```

Inspect the doctor's actual capabilities rather than assuming a checkout implies
a compiled prover or running web server. Indexing scans the corpus and reports
parse failures. A clean parse is a structural result, not a semantic consistency
check. The report writes `output/data/corpus.json`, a source manifest, and chart
and dashboard artifacts. Preserve those exports alongside the query results.

## Find an ontology concept

```bash
uv run rikishi search Human --limit 10
uv run rikishi term Human
uv run rikishi graph Human --limit 30
```

Use search for discovery, then inspect complete term formulas with source locations.
The graph is bounded and presents selected asserted relationships; it is not a
complete entailment graph. Read the defining expressions before interpreting an
edge. A source location refers to the installed revision, so record that revision
before comparing results with someone else's environment.

## Prove a restricted taxonomy statement

```bash
uv run rikishi taxonomy-proof Human AutonomousAgent
```

This command takes direct `subclass` facts from `Merge.kif`, supplies an explicit
first-order transitivity axiom, writes a TPTP problem, and runs the installed E
prover. Inspect all three outputs:

- `output/reasoning/taxonomy.json`: the original facts, lines, revision, and scope.
- `output/reasoning/taxonomy.p`: the exact generated problem and conjecture.
- `output/reasoning/taxonomy.result.json`: command, SZS status, exit code, stdout,
  stderr, and the bounded result.

`Theorem` establishes that conjecture in that projected problem. It does not
establish a general translation of SUMO or use every axiom. `CounterSatisfiable`
describes the supplied first-order problem; `Timeout` and `GaveUp` are inconclusive.
Repeated taxonomy commands use the same filenames, so copy a completed run into
a distinct evidence directory before another query if comparison matters.

## Explore interactively

```bash
uv run rikishi dashboard --port 8765
```

Open the loopback address printed by the command. Explore a term, inspect its
source, and compare corpus charts with exported statistics. The separate Sigma
application has its own launcher and knowledge-base profile; use
`uv run python scripts/runtime-sigma.py start` and follow [runtime.md](runtime.md).
Rikishi's index and Sigma's loaded KB are distinct views with different file
selection policies. Compare them only after checking those policies.

For agent access, configure `rikishi-mcp` as a stdio server using the example in
[API.md](API.md). Stdio protocol output must remain machine-readable; diagnostics
belong on stderr. Begin with source and statistics tools before invoking a larger
agent workflow.

## Reproduce the mathematical illustration

```bash
uv run rikishi fep-demo
uv run rikishi fep-inspect
uv run python scripts/render_manuscript.py
uv run python scripts/verification-manuscript.py
```

The numerical example calculates finite variational free energy. Source inspection
reports pinned Lean declaration locations without compiling Lean. The manuscript
renderer requires the report exports from the first step, then produces PDF,
DOCX, and HTML through the actual template adapters. Inspect
`output/manuscript/render-receipt.json` and the resulting artifacts.

Finish by recording what was observed, which command established it, and what was
not tested. A useful research handoff includes source revision, corpus selection,
query, input/output hashes, reasoner scope, and reproducible commands.

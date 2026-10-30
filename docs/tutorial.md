# From ontology source to a reproducible result

This walkthrough starts in the Rikishi repository with its `uv` environment.
Follow [runtime setup](runtime.md) first to install the pinned Suggested Upper
Merged Ontology (SUMO), Sigma, and E components. SUMO source uses the Standard
Upper Ontology Knowledge Interchange Format (SUO-KIF). Automated theorem proving
(ATP) runs are separate from parsing and graph inspection. Keep the shell's cache and temporary bindings on the project storage
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
first-order transitivity axiom, writes a Thousands of Problems for Theorem Provers
(TPTP) problem, and runs the installed E
prover. Inspect all three outputs:

- `output/reasoning/taxonomy.json`: the original facts, lines, revision, and scope.
- `output/reasoning/taxonomy.p`: the exact generated problem and conjecture.
- `output/reasoning/taxonomy.result.json`: command, status from the
  [SZS result ontology](https://szs.tptp.org/), exit code, stdout,
  stderr, and the bounded result.

`Theorem` establishes that conjecture in that projected problem. It does not
establish a general translation of SUMO or use every axiom. `CounterSatisfiable`
describes the supplied first-order problem; `Timeout` and `GaveUp` are inconclusive.
Repeated taxonomy commands use the same filenames, so copy a completed run into
a distinct evidence directory before another query if comparison matters.

## Learn inference through controlled source examples

```bash
uv run --locked --no-sync rikishi inference-catalog
uv run --locked --no-sync rikishi inference-run output/inference --prover both --timeout 10
```

The destination must be new. Follow the [inference laboratory tutorial](inference-tutorial.md)
to inspect each selected source rule, the conjecture, the generated first-order
logic (FOL) problem, and its controls. Read the report before choosing the next
query: a successful theorem should be accompanied by a satisfiable background;
a premise-removal case should explain what assumption was necessary. Do not
interpret an exhausted search as a countermodel or an unproved conjecture as its
negation. Retain the complete output directory and a separately obtained report
digest before replaying it.

With that independently retained digest in `REPORT_SHA256`, verify and register
the report before opening its published dashboard view:

```bash
uv run --locked --no-sync rikishi inference-verify output/inference/inference-report.json --sha256 "$REPORT_SHA256"
uv run --locked --no-sync rikishi inference-publish output/inference/inference-report.json --sha256 "$REPORT_SHA256"
```

Registration performs strict replay before atomically writing the local
`output/inference/published.json` descriptor. Any differing previous descriptor
is preserved. This command never invokes a prover.

## Explore interactively

```bash
uv run rikishi dashboard --port 8765
```

Open the loopback address printed by the command. Explore a term, inspect its
source, and compare corpus charts with exported statistics. The separate Sigma
application has its own launcher and knowledge-base profile; use
`uv run python scripts/runtime-sigma.py start` and follow [runtime.md](runtime.md).
Rikishi's index and Sigma's loaded knowledge base (KB) are distinct views with different file
selection policies. Compare them only after checking those policies.

For agent access, configure the Model Context Protocol (MCP) server `rikishi-mcp`
over standard input/output using the example in
[API.md](API.md). Stdio protocol output must remain machine-readable; diagnostics
belong on stderr. Begin with source and statistics tools before invoking a larger
agent workflow.

## Reproduce the mathematical illustration

```bash
uv run rikishi fep-demo
uv run rikishi fep-inspect
uv run rikishi fep-verify
uv run rikishi fep-evaluate --help
```

The numerical example calculates finite variational free energy as an illustration
related to the Free Energy Principle (FEP). Source inspection
reports pinned Lean declaration locations without compiling Lean; `fep-verify`
separately compiles the pinned finite modules in isolation and reports their
declaration axioms. It requires the external Lean toolchain and pinned compiled
dependency libraries. `fep-evaluate MODEL --logarithmic` accepts explicit log
inputs: null denotes exact zero support. A null returned linear evidence value
denotes positive underflow while finite logarithms retain the result. Follow the
[manuscript prerequisite recipe](manuscript.md) after the campaign below. It
requires fresh E and Vampire (E/V) finite-alignment campaigns, the separate
both-prover source-kernel inference packet introduced above, a shared-witness
bridge packet, and cache evidence
before rendering Portable Document Format (PDF), Word, and Hypertext Markup
Language (HTML) editions. These campaign populations answer different questions;
none substitutes for another. Verify the source-kernel and bridge reports against
their own independently retained digests before rendering, and check each staged
copy against its unchanged digest afterward, as the recipe shows. Preserve any packet
already produced during this tutorial before starting a fresh reproduction.
Inspect the receipt and actual artifacts after generation.

Finish by recording what was observed, which command established it, and what was
not tested. A useful research handoff includes source revision, corpus selection,
query, input/output hashes, reasoner scope, and reproducible commands.

## Connect one finite witness across representations

The shared study connects a rational finite model to the actual pinned
`fep_formal` definitions and selected SUMO representation questions. Inspect its
design before executing it:

```bash
uv run --locked --no-sync rikishi bridge-catalog
```

The prior, candidate and complete observation kernel share stable model,
representation, calculation and result identifiers. Vector order is **false,
true**: index 0 is the Boolean value `false`, and index 1 is `true`. The selected
observation is `true`; that is an observation value, not the first hidden state.
The explorer's `q(false)` is the candidate mass at index 0. The selected
likelihood column need not sum to one across hidden states; each kernel row sums
to one across observations.

The numerical branch computes an exact rational posterior with `Fraction` and
compares finite-precision objective values with an 80-digit `Decimal` reference.
The generated Lean driver constructs the same prior, kernel and candidate and
states normalization, positive evidence, posterior reconstruction and finite
Kullback-Leibler (KL) obligations at the pinned definitions. The native SUMO
problems test representation, calculation and result consequences under explicit
local assumptions. These are distinct obligations with common inputs, not a
general SUMO-to-Lean preservation theorem. Read the [bridge contract](bridge-methods.md)
and [scholarship ledger](scholarship.md) for their source and support boundaries.

Use a fresh destination whose parent already exists on mounted project storage:

```bash
uv run --locked --no-sync rikishi bridge-run output/bridge --prover both --timeout 10
shasum -a 256 output/bridge/bridge-report.json
```

`--prover` accepts `both` (the default), `e` or `v`; `--timeout` defaults to 10
seconds. Inspect completion of a locally produced run, retain the full packet,
and record its Secure Hash Algorithm 256-bit (SHA-256) digest in a separately
controlled operator record. A transferred packet needs its expected digest from
a trusted source; hashing received bytes only identifies what was received.
Use the retained value for all subsequent inspection:

```bash
read -r -p 'Independently retained bridge report SHA-256: ' BRIDGE_REPORT_SHA256
: "${BRIDGE_REPORT_SHA256:?Supply the independently retained bridge report digest}"
readonly BRIDGE_SHA256="$BRIDGE_REPORT_SHA256"
uv run --locked --no-sync rikishi bridge-verify output/bridge/bridge-report.json --sha256 "$BRIDGE_SHA256"
uv run --locked --no-sync rikishi bridge-case output/bridge/bridge-report.json CASE_ID --prover e --sha256 "$BRIDGE_SHA256"
uv run --locked --no-sync rikishi bridge-figures output/bridge/bridge-report.json output/bridge-figures --sha256 "$BRIDGE_SHA256"
```

Replace `CASE_ID` with a registered case identifier from the packet. The case
command defaults to E; choose `--prover v` only when that family is retained.
Replay, case inspection and figure export require the external digest and do not
start a prover or compile Lean. The figure destination must be new. Its
`bridge-explorer.html` exposes retained cases, complete source context and Lean
source alongside finite candidate-belief exploration. Moving a belief control
changes an illustration of the objective; it creates no new proof result.

Each native scenario has a background, positive, unsupported-query,
premise-removal and refutation control. The source-required existential result
does not identify that output with a named numerical record; their tests keep
separate assumptions. Read actual statuses and totals from the verified report.
Lean declaration totals include definitions, so they are not theorem counts.
The read-only web and agent [interfaces](API.md) inspect retained evidence;
new native execution stays an explicit command-line interface (CLI) action.

## Investigate an Active Inference alignment

Start from the [published alignment precedent](https://doi.org/10.5281/zenodo.11463326)
and its [source and interpretation guide](precedent-alignment.md). Select a topic
and sense, retain the page or spreadsheet row, and identify whether the proposed
target is an existing class, a relation, or a suggested new term. Inspect the
selected revision directly:

```bash
uv run rikishi term agent
uv run rikishi term AutonomousAgent
uv run rikishi term ProbabilityFn
uv run rikishi verify-source
```

The lowercase `agent` is a relation with argument types, rather than a class
synonym. `ProbabilityFn` takes a formula; it does not itself define the packaged
finite probability vector. Those distinctions must survive any extension.
Write proposed axioms separately from the upstream source and specify intended
and unwanted consequences before running a prover. Record the exact background,
translation and expected polarity for each competency question. A restricted
taxonomy proof cannot validate an arbitrary probabilistic or process-level
alignment. [Modeling](modeling.md) describes the additional proof obligations.

Execute the declared [finite study](research.md) after acquiring its original
workbook with that guide's pinned fetch-and-hash recipe. The workbook is not
bundled. These destinations must be fresh; preserve existing campaigns and use
distinct names for an additional experiment.

```bash
mkdir -p output/research
uv run rikishi research-run output/research/e --prover e --workbook source-inputs/active-inference-sumo.xlsx
uv run rikishi research-run output/research/v --prover v --workbook source-inputs/active-inference-sumo.xlsx
uv run rikishi research-verify output/research/e/alignment-report.json
uv run rikishi research-verify output/research/v/alignment-report.json
uv run rikishi cache-diagnostic output/research/fresh-cache --timeout 60
```

`research-run` freshly audits the live index by default; `--source-report PATH`
explicitly selects a frozen source report. `research-verify --sha256 HASH`
accepts a separately trusted outer report hash. Both commands exit zero for a
complete declared campaign and two for an incomplete one; malformed input is an
error. Cache diagnosis exits zero for `observed`, two for `failed`.
Read logical matches, numerical cases, boundary cases, and invalid-input
rejections from the newly generated campaign reports. The five cache controls
cover an isolated fragment and complete Merge, not the four-file core or a
repair. Use [verification](verification.md) to keep these results separate from
whole-alignment, general translation-preservation and empirical obligations.

## Separate inference from choosing an action

After `fep-demo`, run the standalone action example:

```bash
uv run --locked rikishi active-demo
```

Inspect the complete input matrices and the two identical outcome predictions.
The `sense` action resolves the hidden state; `noise` supplies no state
information. Their risk terms agree but their ambiguity and information-gain
terms differ. The retained minimizer follows the declared one-step objective.
No observation is generated or fitted by this command.

Follow the [Active Inference guide](active-inference.md) to change the channels
or preferences through the Python application programming interface (API) and condition on a supplied actual
outcome. Belief updating, prospective decision-making, ontology consequences,
formal guarantees and empirical validation each require their own evidence.

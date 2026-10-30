# Rikishi

A source-bound operator and research workbench for the
[Suggested Upper Merged Ontology (SUMO)](https://github.com/ontologyportal/sumo).
Rikishi installs Sigma and an automated theorem proving (ATP) environment,
indexes real Standard Upper Ontology Knowledge Interchange Format (SUO-KIF)
source with provenance, provides a local dashboard and read-only Model Context
Protocol (MCP) tools, and develops explicitly scoped connections to the
Free Energy Principle (FEP), finite variational free energy, and
[fep_formal](https://github.com/ActiveInferenceInstitute/fep_formal).

For a conceptual introduction, read [how SUMO, FEP_Formal and simulations connect](docs/sumo-fep-simulations.md).
It follows one finite model through ontology roles, Lean statements, numerical
calculations and synthetic observations, identifying what each can establish.

Active Inference connects inference to prospective action under a generative
model. Rikishi now includes a separate [one-step action planner](docs/active-inference.md):
`uv run rikishi active-demo` compares explicit transitions, observation channels
and outcome preferences, retaining both pragmatic and information-seeking terms.
The existing variational example and fixed-state simulations retain their own
scope; the planner adds no ontology theorem, Lean proof or empirical validation.

[Aligning Active Inference Ontology to SUMO](https://doi.org/10.5281/zenodo.11463326)
is direct precedent for the alignment agenda. Rikishi provides an environment to
inspect and test such proposals. The [precedent guide](docs/precedent-alignment.md)
distinguishes proposed correspondences from executable axioms and verified results.

The [current-state guide](docs/current-state.md) describes implemented methods,
qualification requirements and remaining limits. The [prioritized backlog](docs/TODO.md)
separates completed implementation from the next minor, medium and major work.

## Install and choose a workflow

The proposed first public release is **1.0.0**. Preparation does not mean a
GitHub release or Zenodo record has been published. Use the
[review guide](docs/review.md) and [release checklist](RELEASE_CHECKLIST.md) to
identify actual source, artifact and verification records.

Start with the [installation/support guide](docs/installation.md). Installing
the wheel supplies the Python package; a source checkout is required for the
configuration, scripts, manuscript and documented native workflows. Native
bootstrap currently enforces the mounted-workspace policy and has
Apple-Silicon-specific provisioning. Portable methods and catalog inspection
have a separate scope from a full native installation.

From a prepared source checkout, these commands inspect finite methods and
catalogs without launching a native theorem prover:

~~~bash
uv sync --locked
uv run rikishi fep-demo
uv run rikishi bridge-catalog
uv run rikishi inference-catalog
~~~

For the documented native workstation layout, from this checkout on mounted
GitVault:


```bash
source scripts/env.sh
uv sync --locked
uv run rikishi bootstrap
uv run rikishi index
uv run rikishi verify-source
uv run rikishi dashboard --port 8765
```

Open <http://127.0.0.1:8765/#corpus>. The white workbench supports complete paginated
file and formula search, source hashes and lines, relation inventories, taxonomy
diagnostics and bounded paths, downloadable results, and a finite inference
explorer. [Ontology analysis](docs/ontology-analysis.md) defines its populations.
[Runtime setup](docs/runtime.md) covers native Sigma, prover operation,
profiles and diagnostic evidence.

```bash
uv run rikishi taxonomy-proof Human AutonomousAgent
uv run rikishi files --path Merge
uv run rikishi formulas --head subclass --term Human
uv run rikishi taxonomy --path Merge.kif
uv run rikishi taxonomy-path Human Entity
uv run rikishi inference-catalog
uv run rikishi inference-run output/inference --prover both --timeout 10
uv run python scripts/demonstrate_sumo.py --help
uv run rikishi fep-demo
uv run rikishi bridge-catalog
uv run rikishi bridge-run --help
uv run rikishi report
uv run rikishi research-run --help
uv run rikishi mcp
make check
```

Use a fresh destination for each inference laboratory run. The
[inference tutorial](docs/inference-tutorial.md) explains how the catalog's real
source premises become explicit first-order logic (FOL) problems, how E and Vampire
are run, and how countermodels and premise-removal controls test the proposed
consequences. The dashboard's `#proof-lab` workspace and agent tools inspect the
catalog and replay retained reports; they never launch a prover.

After retaining the report digest separately as `REPORT_SHA256`, verify and
register the run for the dashboard:

```bash
uv run --locked --no-sync rikishi inference-verify output/inference/inference-report.json --sha256 "$REPORT_SHA256"
uv run --locked --no-sync rikishi inference-publish output/inference/inference-report.json --sha256 "$REPORT_SHA256"
```

Registration strictly replays the report, then atomically writes the local
`output/inference/published.json` descriptor, preserving any differing previous
descriptor. It is required for the dashboard's published-run view and never
invokes a prover.

The full gate requires installed native prerequisites; `make portable` runs the
portable suite. [Testing](docs/testing.md) defines both coverage scopes and failure
controls. Native template editions are `output/pdf/rikishi_combined.pdf`,
`output/docx/rikishi.docx`, and `output/web/index.html`; their shared inputs and
receipt are under `output/manuscript/`. The manuscript includes SUMO scholarship,
an author cover, three dense graphical abstracts on physical pages 2–4, and
source-derived body figures. Its measurements, model
parameters, metadata and numbered references are generated from checked authorities.
Word export retains the exact Pandoc native-default reference and a minimally
modified publication reference in that directory. Its receipt binds both hashes
and the reference/final page geometry. The reference policy permits only two
page-geometry insertions in `word/document.xml`, explicit `Hyperlink` color
`#005EA8` and `ImageCaption` line retention in `word/styles.xml`; native
`CaptionedFigure` keep-with-next is required and preserved. All remaining style and
member payload bytes stay exact. This policy requires fresh native propagation,
LibreOffice contrast and pagination review against the changed edition.
A separate content projection retains
`output/manuscript/rikishi-native.docx` and adds row keep-together properties to
produce `output/docx/rikishi.docx`, preserving repeated headers and all other
document content. The verifier independently recomputes that projection and
checks the supported complete manuscript math sequence. Actual section geometry, bounded
content checks and office pagination have separate evidence requirements. The
review bundle must identify its actual Portable Document Format (PDF)/LibreOffice
page inspections and independent visual reviews. Historical reviews do not qualify
changed editions; Microsoft Word pagination and physical printing require their
own observations. See the [qualification guide](docs/current-state.md).
[Office methods](docs/manuscript.md#final-word-content-projection-and-math-checks)
explain the custody and verification boundaries.
Before rendering, execute the fresh E and Vampire research campaigns,
source-kernel inference campaign, shared-witness bridge campaign and cache
diagnostic using the [manuscript prerequisite recipe](docs/manuscript.md).
The original workbook is not bundled; its pinned acquisition recipe is in
[research methods](docs/research.md).
The [SUMO demonstrations](docs/sumo-demonstrations.md) inspect actual source
axioms, argument signatures and the graph projection, with an optional restricted
native proof and countermodel control. [Visualization methods](docs/visualizations.md)
explain the source-backed cover and publication figures.

## Interpret results

The manuscript now develops exact representation experiments from the shared
finite witnesses: stochastic state channels, observation degradation, unchanged
posteriors with changed evidence, and explicitly assumed predictive/model-odds
comparisons. Two source-bound figures and `witness-research.json` make these
distinctions inspectable. The sequential extension adds exact repeated
conditioning, next-observation prediction and model weights, alongside 65,536
seeded persistent-state trajectories per model in `witness-dynamics.json` and
its four-panel figure. See the [method contract](docs/bridge-methods.md#derived-finite-representation-experiments)
and [exact Python methods](docs/API.md#exact-finite-channels-and-derived-witness-research).
These derived calculations add no new native SUMO or Lean proof claim.

Mixed-history methods now accept complete Boolean observation sequences,
retain exact joint/evidence/posterior and next-observation laws, and separately
normalize explicit prior model weights. The paper's mixed-history atlas shows
all eight length-three histories rather than only all-true prefixes. See
[the method contract](docs/bridge-methods.md#mixed-histories-and-model-uncertainty)
and [Python interfaces](docs/API.md#mixed-observations-and-model-uncertainty).

Read a result through its evidence scope:

| Evidence | What to conclude |
| --- | --- |
| Source formula or direct graph edge | The selected pinned file contains that expression; inspect its full context |
| Laboratory theorem with background and removal controls | The submitted explicit kernel entails its conjecture under the declared encoding |
| Countermodel for a conjecture | That kernel permits the conjecture to be false; this does not prove its negation |
| Native Sigma query | A result about the retained translated profile and query, subject to background diagnostics |
| Agreement between E and Vampire | Both native runs classified identical submitted problems alike; semantic interpretation remains a separate obligation |
| Finite variational calculation or Lean elaboration | The recorded numerical or formal finite object passed its own checks |
| Shared finite-witness bridge report | The same authored finite inputs bind separate numerical comparisons, Lean obligations and controlled SUMO representation questions; read each observed outcome from the verified packet |

The inference laboratory and the [selected alignment study](docs/research.md)
answer different questions. Laboratory scenarios explain selected ontology rules;
the study tests a declared interpretation of alignment proposals. Derive current
counts and statuses from the exact retained reports and their replay, rather than
treating a previous acceptance receipt as evidence for newly edited source.
Arithmetic remains separate from the declared logical fragment.

The shared-witness bridge uses rational Boolean-carrier models with the same
prior, observation kernel, candidate law and entity identifiers across Python,
Lean and the selected SUMO scenarios. State vectors use false, true order;
the selected observation is `true`, and the explorer varies `q(false)`.
It adds actual finite theorem
instantiation obligations to the earlier [alignment study](docs/research.md).
Its catalog describes the design; it cannot establish that a native campaign
completed. The Lean inventory includes definitions as well as theorems.

From the prepared environment, run into a new destination:

```bash
uv run --locked --no-sync rikishi bridge-run output/bridge --prover both --timeout 10
```

For a locally produced run, inspect its completion, preserve the entire packet
and record its Secure Hash Algorithm 256-bit (SHA-256) digest in separately
controlled custody. For a received packet, obtain the expected digest through a
trusted record or channel; computing a new hash of untrusted received bytes does
not supply that trust. With the retained digest in `BRIDGE_SHA256`:

```bash
uv run --locked --no-sync rikishi bridge-verify output/bridge/bridge-report.json --sha256 "$BRIDGE_SHA256"
uv run --locked --no-sync rikishi bridge-figures output/bridge/bridge-report.json output/bridge-figures --sha256 "$BRIDGE_SHA256"
```

The figure destination must also be new. It contains three report-derived plots,
their data and an offline explorer for retained native cases, Lean source and
finite candidate-belief exploration. Read-only web and agent interfaces inspect
the packet without executing proofs. [Interfaces](docs/API.md) lists the exact
commands and routes; [the tutorial](docs/tutorial.md#connect-one-finite-witness-across-representations)
walks through the distinction between execution and inspection.

The [fresh cache experiment](docs/cache-inheritance.md) observes five controls
using source ingestion and `buildCaches()` in isolated knowledge bases, including complete
pinned `Merge.kif`. It extends the historical seeded diagnostic and localized
translated refutation in the [runtime record](docs/runtime-upstream-report.md).
It establishes neither complete four-file-core consistency nor source-ontology
inconsistency or repair. Sigma supplies its own native translation path; the
laboratory supplies a declared fragment compiler. Neither establishes a general
source-to-target preservation guarantee. There is no general SUMO-to-Lean source-formula preservation
theorem or biological validation. Acceptance requires matching frozen
source, full-gate, native-edition and independent-review receipts;
[verification](docs/verification.md) defines those requirements and their limits.

[The glossary](docs/glossary.md) defines terminology, result statuses, and common
category errors. [Documentation](docs/README.md) links interfaces, visualization methods,
scholarship and reproducibility. [Verification](docs/verification.md) defines the required records
and how to interpret their scope. Author skills in `.agents/skills/`; `skills/` is the checked
distribution projection.

Operator code is [MIT licensed](LICENSE). The original manuscript and figures
are [CC BY 4.0 licensed](LICENSE-PAPER.md). Downloaded ontology, formalization,
runtime, citation-style and quoted materials retain their own terms; read
[third-party notices](THIRD_PARTY_NOTICES.md). [Project origin](config/template-origin.json) records template
provenance. No command automatically publishes to upstream SUMO, PyPI or Zenodo.

## Review, cite and contribute

- [Review the actual PDF and artifacts](docs/review.md).
- [Reproduce the manuscript](docs/manuscript.md) and
  [understand verification scopes](docs/verification.md).
- [Cite the software](CITATION.cff); cite the manuscript's real record separately
  once published. The alignment-precedent digital object identifier (DOI) above is not Rikishi's DOI.
- [Read the changes](CHANGELOG.md),
  [contribute](CONTRIBUTING.md), or
  [report a security concern](SECURITY.md).
- [Prepare the GitHub/Zenodo release](docs/release.md).

Public release assets and DOI links will be recorded only after they exist.
A local output path, badge, version string or old build receipt is not evidence
that the current candidate is published or qualified.

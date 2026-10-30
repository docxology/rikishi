# Reproduce the manuscript

After environment setup, prepare the pinned sources/index and verified finite
Lean receipt using [runtime](runtime.md) and [Free Energy Principle (FEP) methods](fep.md). Acquire the
original workbook using the official fetch-and-hash recipe in
[research methods](research.md); no workbook is bundled.

Rendering requires three distinct campaign populations: the finite-alignment
study's fresh E and Vampire (E/V) campaigns under `output/research/{e,v}/`,
the separate [source-kernel inference laboratory](inference-methods.md)
with both provers under `output/inference/`, and the shared finite-witness bridge
with both provers under `output/bridge/`. The source-only cache diagnostic
is another required input. Corpus export with `rikishi report` creates none of
these campaigns. Each packet has its own study and evidence obligations; none
can replace another.

Preserve previous campaign/cache packets, staged publication inputs and native
editions before starting a fresh reproduction. The guard below stops on occupied
destinations, including symlinks. Keep completed or failed evidence intact in a
separate evidence location; do not delete it or merge a new run into an old tree.
The renderer reads these fixed canonical paths; choosing a different campaign
destination or dashboard registration does not redirect it.

First generate all prerequisites, stopping before rendering:

```bash
set -e
source scripts/env.sh
for destination in output/research/e output/research/v \
  output/research/fresh-cache output/inference output/bridge output/manuscript \
  output/pdf output/docx output/web; do
  if [[ -e "$destination" || -L "$destination" ]]; then
    printf 'Preserve existing evidence before reproducing: %s\n' "$destination" >&2
    exit 1
  fi
done
uv run --locked rikishi report
mkdir -p output/research
uv run --locked rikishi research-run output/research/e --prover e --workbook source-inputs/active-inference-sumo.xlsx
uv run --locked rikishi research-run output/research/v --prover v --workbook source-inputs/active-inference-sumo.xlsx
uv run --locked rikishi research-verify output/research/e/alignment-report.json
uv run --locked rikishi research-verify output/research/v/alignment-report.json
uv run --locked rikishi cache-diagnostic output/research/fresh-cache --timeout 60
uv run --locked rikishi inference-run output/inference --prover both --timeout 10
uv run --locked rikishi bridge-run output/bridge --prover both --timeout 10
shasum -a 256 output/inference/inference-report.json
shasum -a 256 output/bridge/bridge-report.json
```

For each newly executed local run, inspect completion and independently record
its printed Secure Hash Algorithm 256-bit (SHA-256) digest in a separately
controlled operator record outside `output/inference/`, `output/bridge/` and
`output/manuscript/`. Identify each producer run in that record and preserve both
complete packets. A checksum inside or beside a mutable packet is not independent custody.
For a transferred, untrusted packet, freshly hashing the received report only
identifies those received bytes; obtain its expected digest through a separately
trusted record or channel before verification. Local hashing does not supply
external trust in the producer or authenticate historical execution.

Then enter each digest from its independently retained record at `read`, before
verification or rendering. No digest for a new run is supplied by this guide.

```bash
set -e
source scripts/env.sh
read -r -p 'Independently retained inference report SHA-256: ' INFERENCE_REPORT_SHA256
: "${INFERENCE_REPORT_SHA256:?Supply the independently retained report digest}"
readonly REPORT_SHA256="$INFERENCE_REPORT_SHA256"
read -r -p 'Independently retained bridge report SHA-256: ' BRIDGE_REPORT_SHA256
: "${BRIDGE_REPORT_SHA256:?Supply the independently retained bridge report digest}"
readonly BRIDGE_SHA256="$BRIDGE_REPORT_SHA256"
uv run --locked rikishi inference-verify output/inference/inference-report.json --sha256 "$REPORT_SHA256"
uv run --locked rikishi bridge-verify output/bridge/bridge-report.json --sha256 "$BRIDGE_SHA256"
uv run --locked python scripts/render_manuscript.py
uv run --locked rikishi inference-verify output/manuscript/inference/inference-report.json --sha256 "$REPORT_SHA256"
uv run --locked rikishi bridge-verify output/manuscript/bridge/bridge-report.json --sha256 "$BRIDGE_SHA256"
uv run --locked python -O scripts/verification-manuscript.py
```

Here `INFERENCE_REPORT_SHA256` is the supplied inference digest and `REPORT_SHA256`
is its immutable alias. `BRIDGE_REPORT_SHA256` supplies the separate bridge digest,
bound once as immutable `BRIDGE_SHA256`. Each alias is passed explicitly through
`--sha256` for both its source report and staged copy. These shell values are not
read by the renderer or manuscript verifier. Their internal replay computes
the staged report's digest; the explicit command-line interface (CLI) checks above bind both the source
packet before rendering and its staged copy afterward to the independently
retained values. The manuscript substitutions `INFERENCE_REPORT_SHA256` and
`BRIDGE_REPORT_SHA256` are generated from staged inputs, rather than read from
the shell. Retain the separate operator records to supply external custody.

Campaign/cache destinations must be new, and the inference destination's parent
must already exist; `rikishi report` creates `output/` before that campaign.
Rendering requires complete finite-alignment E/V campaigns and passed two-prover
source-kernel and shared-witness bridge campaigns. The bridge includes its actual
Lean witness elaboration, numerical comparisons and native ontology controls;
a catalog or generated proof source alone is insufficient. For the finite-alignment campaigns,
`--source-report PATH` explicitly selects a frozen source input; by default each
campaign audits the live index and creates a fresh source report. Missing or
incomplete inputs are errors. See the [inference tutorial](inference-tutorial.md)
for source selection, controls and interpretation. The renderer invokes the
canonical template's Portable Document Format (PDF), web and Word renderers.
This recipe is not a report of a new render or full-gate pass.

For the local dashboard's published inference view, optionally register the
verified source packet afterward, using the same independently retained digest:

```bash
uv run --locked rikishi inference-publish output/inference/inference-report.json \
  --sha256 "${REPORT_SHA256:?Supply the independently retained report digest}"
```

Registration strictly replays the packet and writes the local
`output/inference/published.json` descriptor, preserving any differing prior
descriptor. It never invokes a prover or publishes to an external service.
It is not required for manuscript rendering. Do not register a different packet
before generating the canonical campaign: registration creates `output/inference/`,
which must be absent for a fresh run.

The default renderer repository is the sibling `../../Public/template`. Set
`RIKISHI_TEMPLATE_ROOT` to another complete checkout when relocating. Rikishi
exports committed infrastructure and pyproject.toml at its pinned renderer
revision using git archive, then imports only the verified snapshot under
`.rikishi/template-renderer/<revision>/`. Existing snapshots must match every
archive file hash. The canonical checkout's dirty files are neither imported nor
modified. [Project origin](../config/template-origin.json) records provenance.

Pandoc, pandoc-crossref, BibTeX, XeLaTeX and Poppler are required. Missing or failing
tools are errors. The full test gate additionally requires the explicitly selected
`RIKISHI_CHROMIUM` executable for real typography checks, as described in
[testing](testing.md). Rendering and those browser checks are distinct operations.
The configured PDF cover replaces the template's title page;
the template also generates a table of contents. Word and Hypertext Markup
Language (HTML) receive matching
source-derived affiliations and an unlabeled graphical abstract before the body.
PDF margins come from `publication.margin_mm` in the publication configuration.
Three ordered `paper.graphical_abstracts` records define a visual introduction:
source commitments, exact shared finite witnesses, and the separate
model/representation/calculation/result evidence roles. The figures come from
the verified bridge report. PDF inserts them immediately before the native
table of contents, so physical pages 2–4 carry one graphical abstract each.
Word and HTML receive the same ordered images, titles, summaries and alternative
text; Word has explicit page breaks. They are unnumbered front matter and do not
renumber the body figures. Verification checks actual PDF page images and all
canonical image copies, not merely the configuration or generated LaTeX.
The current policy is 12 mm on each side, with prose using the full remaining
page width. HTML uses the configured padding on larger viewports and 17 px body
text, with no additional prose-width cap. At browser viewport widths of
600 pixels or below, padding is capped at four percent of viewport width, keeping
phone gutters small. Code text has a 15 px minimum at every viewport width;
code blocks use a contrasting palette on their dark background.
This publication policy is
distinct from the live dashboard's own layout. Verification checks actual page
coordinates and rendered structure; updating configuration does not rehabilitate
a stale edition. Inspect paragraphs, lists, tables, references and figures at
their actual edition width.

Native editions are `output/pdf/rikishi_combined.pdf`, `output/docx/rikishi.docx`,
and `output/web/index.html`. Shared inputs, projected Markdown, configuration,
bibliography, style, numerical JavaScript Object Notation (JSON), figures and render-receipt.json live under
`output/manuscript/`. The receipt records actual edition paths and each
materialized artifact's size and hash. Every HTML image copy has its own record;
verification requires the actual image reference and equality with its canonical
figure. Word must contain the same image bytes. HTML figures work offline;
MathJax enhancement may require network access.

## Explicit Word geometry and retained reference

Word export uses `render_docx(..., reference_doc=office_reference)` through the
canonical adapter. `publication_office.write_office_reference` obtains the
invoked Pandoc executable's native `reference.docx`, retains those exact bytes,
and derives the publication reference with a bounded geometry-plus-style policy.
In `word/document.xml`, only `w:pgSz` and `w:pgMar` are inserted into section
properties; all other document Extensible Markup Language (XML) bytes remain
exact. In `word/styles.xml`, the only changes are an explicit `#005EA8`
`Hyperlink` color atom, removing its `themeColor`, `themeTint` and `themeShade`
selectors, and the insertion for `ImageCaption` of
`w:pPr/w:keepLines`. The native `CaptionedFigure` enabled `w:keepNext` and the
caption's `Caption` base are required and preserved; no figure property is added.
All other style/XML bytes, member payloads, inventory/order, archive comment
and public member metadata remain exact. Changed payloads have derived sizes,
checksums and offsets. No arbitrary theme, font, prose or mathematics rewrite is
permitted. These invariants concern the two reference packages; the final
manuscript has its own content and hash.

The current policy is portrait Letter, 215.9 × 279.4 mm, with 12 mm body margins,
zero gutter and a single full-width text column. Word records geometry in twips
(1440 twips = 25.4 mm): decimal half-up conversion yields 12240 × 15840 twips
and 680-twip margins, within 0.01 mm of the requested margin. Every final section
must have explicit page size and all four margins; header/footer distances must
be explicit and no greater than the body margin. Missing geometry is rejected
rather than inferred from a viewer's defaults.

Retain both files under `output/manuscript/`:

- `office-reference.native-default.docx`: the exact unmodified native export;
- `office-reference.docx`: the minimally changed reference passed to Word export.

The render receipt's `office_reference` record contains `reference_doc`,
`default_reference_doc`, their `reference_sha256` and
`default_reference_sha256`, `pandoc_executable`, `pandoc_sha256`, `pandoc_version`,
the reference `geometry`, and the final document's independently read `actual`
geometry. Each geometry report records the document hash, dimensions and margin
in millimetres and twips, plus `section_count`.

Pandoc's native-default export can vary in outer ZIP timestamps between calls.
Bind the exact retained default archive used for that reference; do not replace
it with a repeat export or require repeat-export archive hash equality.
Reference acceptance requires both retained hashes, independently inspected
reference/final geometry and recomputation of the exact approved reference from
that retained default. The additional pure byte method
`verify_office_reference_policy` returns the existing frozen geometry report;
the writer/page-verifier signatures and record fields remain unchanged. Removing
only the two geometry elements from document Extensible Markup Language (XML)
and inverting only the approved style atoms must recover all remaining native
bytes. Whole-reference equality also binds ZIP metadata. Rebinding a receipt
hash cannot authorize wrong or implicit geometry, a different style or another
member payload. See the [exact interface](API.md#office-page-policy).

Ordinary digital document text requires at least 4.5:1 contrast on its actual
background, with no inherited-palette waiver. `themeColor="accent1"` can override
the fallback, so the selected explicit `#005EA8` must propagate without that
selector. This states the reference method. Independent LibreOffice contrast
and complete figure-caption pagination review of the new manuscript edition
remain required.

These package and XML checks do not establish Word pagination, line breaking or
visual layout. A separate compatible office renderer and inspection of its
actual output are required for that claim. Each changed reference or final
content projection requires fresh native propagation, final editions and
visual review. Identify actual bounded PDF/LibreOffice inspections in the
release verification summary; Microsoft Word pagination needs its own direct
observation. The [qualification guide](current-state.md) distinguishes these scopes. A reference-propagation fixture cannot replace complete manuscript
acceptance; see
[verification status](verification.md#word-geometry-and-pagination-status).

## Final Word content projection and math checks

The reference policy above is separate from final manuscript content. A separate
[`publication_office_content`](../src/rikishi/publication_office_content.py)
method operates on the rendered manuscript, not on either reference package.
The canonical adapter first writes `output/manuscript/rikishi-native.docx`.
`project_office_content(native_docx: bytes)` performs no file or process work:
it returns an `OfficeContentProjection` with final `docx: bytes` and a frozen
`OfficeContentReceipt`. The orchestrator retains the native file and writes the
projected bytes to `output/docx/rikishi.docx`.

For supported ordinary, unmerged text tables, the projection inserts
`w:cantSplit` into each row that lacks it, in row-property schema order. An
existing valid enabled property is retained. Repeated-header properties,
text, mathematics, styles, geometry and every other document XML byte remain
unchanged. Other ZIP member payloads, member order and checked metadata are
preserved. Nested tables, merged cells, drawings in rows, unsupported native
row syntax and an explicit disabled split policy are errors; this is not a
general Word-package rewriting method. The property requests intact rows;
actual office pagination still needs inspection.

The render receipt's `office_content` binds native/projected package and main
document hashes, actual table/row/enabled repeated-header counts, and the tuple of changed
rows. Each `OfficeRowChange` records a zero-based document row index and exact
before/after row hashes. These observations are derived from the packages, not
fixed publication totals. `office_math` records `gathered_sha256`,
`atomic_non_entailments` and `entailments_of_negation`. The
[Python interface](API.md#office-content-projection-and-math) lists every field
and signature.

The mathematical serialization uses the same canonical manuscript body for all
editions: `gathered` displays for taxonomy sets, finite-objective decompositions
and Lean finite definitions, a repeated `F(q)=` on the objective's
continuation rows, and the atomic `\nvDash` non-entailment symbol. There is no Word-only
mathematical source fork. `verify_office_content_math(docx: bytes)` checks the
supported complete manuscript math sequence, including operators, bounds,
scripts and full expression envelopes, and the distinct `T⊭q` / `T⊨¬q` pair.
The canonical body has five gathered displays: those three and
the `sumo-translated-core` and `logarithmic-normalization` displays.
Only the supported native equation-number suffix may surround a display.
Producer and verifier require the returned `gathered_sha256` inventory length to
equal the canonical hydrated body's gathered count. An isolated three-display
fixture is not the full-document inventory. The check rejects literal alignment markers and
combining-negation artifacts. This is a bounded serialization check, not general
mathematical equivalence, theorem checking or scientific validation.

`manuscript_verification` independently reads the retained native and actual
final packages, reconstructs the permitted row inserts, checks the final math
structures and compares both recomputed records with `office_content` and
`office_math`. This supplements the separate geometry and artifact-hash checks;
rebinding a receipt hash cannot authorize a changed formula, prose or other
payload. Keep the native and final packages with the receipt and both references.
Code review, successful final rendering and visual acceptance require separate
records bound to the frozen source and actual edition hashes. The
[current-state register](current-state.md) identifies completed evidence; the
[TODO](TODO.md) tracks remaining scopes. Preserve rejected candidates without
crediting them as accepted outputs.

## Staged research packets and figures

Publication stages the complete E/V report trees under
`output/manuscript/research/{e,v}/`, including source, study, workbook, problems
and captures; the fresh-cache tree is staged alongside them. The receipt's
`research_inputs` field binds the two primary alignment-report hashes. The
publication context requires complete campaigns with matching study/source
claims, numerical matrices and problem hashes. It injects all campaign counts,
statuses, tolerances and measured-error tables from those reports. No result
number is independently transcribed into manuscript prose.

The separate source-kernel packet is staged from `output/inference/` into
`output/manuscript/inference/`, including its study, complete retained source,
lock, implementation and executable bytes, generated problems and captures.
The receipt's `inference_inputs` field binds `inference-report.json` to its
SHA-256 digest; the artifact inventory records each staged file's size and hash.
Publication requires a passed two-prover campaign and replays its selected
source claims, generated problems, invocation captures, observed statuses,
background controls and summary. Native manuscript verification repeats that
staged replay and compares the input digest with the receipt. The explicit
digest-bound CLI checks in the recipe additionally bind the source and staged
packets to the separately retained record. These checks do not rerun the provers,
authenticate historical execution, independently check proof steps or establish
whole-source consistency. See [inference methods](inference-methods.md) for the
source-kernel scope, distinct from the [finite-alignment study](research.md).

The shared-witness packet is staged from `output/bridge/` into
`output/manuscript/bridge/`. Preserve its study, rational inputs, complete source
claims, generated Lean source and compiled evidence, numerical comparisons,
native problems and captures together. Publication derives bridge populations
and tables from the replayed report; a declaration total includes definitions as
well as theorems. A count of generated scenarios is not a count of completed
native executions. State-vector and posterior display order is false, true;
observed `true` denotes the selected observation. The explorer's `q(false)` is
the first candidate mass. Source and staged `bridge-verify` commands above must use the
same independently retained bridge digest, separate from the inference digest.

Bridge figures are generated from that verified packet and staged under
`output/manuscript/figures/`, with web copies under `output/web/figures/`:

- `bridge-evidence.png`, `bridge-free-energy.png`, `bridge-native-controls.png`
  and their Scalable Vector Graphics (SVG) counterparts;
- `bridge-figure-inputs.json`, containing the measured inputs and report binding;
- `bridge-explorer.html`, a standalone interactive view of retained cases,
  shared finite inputs and Lean proof source.

The explorer's finite candidate-belief controls illustrate the objective for the
retained model; moving a control starts neither a Lean elaboration nor a prover.
They do not add proof results to the packet. To generate a separate figure set,
choose a new directory whose parent already exists on mounted project storage:

```bash
uv run --locked rikishi bridge-figures output/bridge/bridge-report.json \
  output/bridge-figures --sha256 "${BRIDGE_SHA256:?Supply the independently retained bridge report digest}"
```

This optional export does not redirect publication's canonical source packet or
replace its staged figures. Matched witness inputs connect the finite layers;
the report does not establish a general SUMO-to-Lean preservation theorem.

Cache replay requires the current packaged schema 2 authority, reconciles the
before, adapter and case-input manifests against the complete after manifest,
and rehashes retained source, input, adapter-class and Sigma archive bytes. It
reconstructs controlled Knowledge Interchange Format (KIF) inputs and checks saved commands, process results
and raw observations. The [archive policy](cache-inheritance.md#archive-identity-and-custody)
binds executable content across supported rebuilds while retaining exact archive
hashes for each invocation. These offline checks establish internal consistency;
they do not authenticate a historical process or a coherently replaced bundle.

## Authorities and numbering

`manuscript/rikishi.md` owns scientific prose, symbolic equations and stable labels;
`manuscript/references.bib` owns literature metadata. `config/manuscript.yaml` owns
title, authors, affiliations, typography and rendering policy. Software version
comes from pyproject.toml, publication date from the recorded Coordinated Universal Time (UTC) rendering time,
corpus quantities from output/data/corpus.json, and Lean metadata from
output/formalization/verification.json. The packaged
`src/rikishi/data/fep-example.json` supplies model probabilities, state labels and
scan resolution. No manuscript result is independently transcribed.
Optional author ORCID identifiers are declared in the same configuration and
projected into each edition. The native PDF cover and Office/Web frontmatter
therefore use the same identifier; malformed identifier strings reject before
rendering. The configured author record was checked against the public ORCID
registry and the pinned formalization repository's citation metadata.

`publication.load_publication_context` loads and hashes those authorities, computes
the example once, and supplies explicit substitutions. Unknown tokens, changed
inputs, incompatible formal receipts and missing styles reject. The shared body
is retained separately from the PDF and Office/Web projections. Source report
figures and the graphical abstract's exact numerical and taxonomic inputs are
also retained. See [reproducibility](reproducibility.md).
The Suggested Upper Merged Ontology (SUMO) worked examples are injected from an audited `Merge.kif` snapshot through
`sumo_demonstrations`. Its portable report retains the full source text,
Secure Hash Algorithm 256-bit (SHA-256) fingerprints,
selected formula locations and exact excerpts. Verification reparses those bytes
and rederives every reported selection and structural observation without the
original checkout. This checks internal agreement; the live source audit supplies
the binding to the acquired Git revision. See [source demonstrations](sumo-demonstrations.md).

Section headings, display equations, definitions, propositions and body figures
use stable labels with native cross-references. Native filters assign numbers on
export; inserting an item updates subsequent numbers and references. Word numbers
are generated during export, rather than live Word fields. Mathematical constants
and publication dates in bibliography records retain their ordinary meaning;
measured results and configurable model values are injected.

PDF citations use native natbib/BibTeX with plainnat; HTML and Word use citeproc
with the pinned Harvard Cite Them Right Citation Style Language (CSL) in
[config/references.csl](../config/references.csl). The style retains its Creative Commons Attribution-ShareAlike 3.0
license and upstream attribution. Its repository revision and SHA-256 are checked
against config/manuscript.yaml. The bibliography's formal-source revision is
injected from the same checked Lean authority. Native filter order is formalism,
crossref, then citeproc. Source checks parse actual Pandoc abstract syntax tree (AST) and BibTeX, rejecting
unknown citations, duplicate or missing labels, unlabeled display equations and
manually numbered section/equation tags.

## Methods and checks

`rikishi.manuscript.render_manuscript(root)` orchestrates checked publication
context, source checks, numerical figures and native adapters. These methods live
in publication, publication_checks, manuscript_figures and manuscript_provenance.
The manuscript rendering and verification entrypoint scripts defer execution until called.

`ontology-structure.json` is rederived from the retained complete Merge source
in `sumo-demonstrations.json`, using the ordinary read-only index and taxonomy
methods in an isolated workspace. Its SHA-256 is mandatory in the render receipt.
The generated taxonomy table, figure metadata, all native figure copies and
actual PDF/HTML/DOCX use are checked against that source-derived report. No
live source/index access is required to replay this publication observation.
`rikishi.manuscript_verification.verify_manuscript(root)` inspects actual
PDF/DOCX/HTML using explicit exceptions, including with Python assertions disabled.
Input and output hashes prevent stale documents from passing.

The graphical abstract shows selected indexed direct subclass assertions,
operator evidence boundaries and finite variational inference. It does not claim
a SUMO interpretation theorem. The corpus plots describe their populations and
denominators; see [metrics](metrics.md). [Scholarship](scholarship.md) maps
SUMO-specific claims to primary sources and records inspection limits.
The separate SUMO system figure derives its category, argument-signature and
modal-context panels from the same validated source report as the worked KIF
blocks. Native verification requires every canonical image in PDF, Word and HTML,
and checks the actual injected source formulas in all three editions.
The separate `research-controls.png` image is generated with its SVG,
source JSON and `research-dashboard.html` explorer by `src/rikishi/research_figures.py`.
Its inputs are the replay-validated E/V reports; the explorer remains a separate
offline artifact. [Research visualization methods](research-visualizations.md)
defines its populations, scales and evidence boundaries.
Paper links use `../figures/research-dashboard.html` and
`../figures/bridge-explorer.html`, resolving to the shared `output/figures/`
directory from the sibling PDF, Word and HTML edition directories. The final
verifier checks the actual local targets and their retained figure copies;
relative link text alone is insufficient.
The direct Active Inference–SUMO precedent is cited in the abstract and discussed
with concrete modeling differences in the body. Its record, PDF and spreadsheet
are documented in the [alignment guide](precedent-alignment.md). The bibliography
uses the cited release's metadata; embedded document identifiers are retained as
source observations rather than silently substituted for the release digital object identifier (DOI).

Run focused controls after generation:

```bash
source scripts/env.sh
uv run pytest tests/manuscript
uv run python -O scripts/verification-manuscript.py
```

The native integration fixture regenerates all formats through the actual
`scripts/render_manuscript.py` production entrypoint in a separate process.
It explicitly excludes only pytest's `PYTEST_CURRENT_TEST` metadata from that
child environment, so the pinned dependency uses its normal production deadlines
(including 600 seconds for Markdown-to-LaTeX Pandoc conversion), rather than its
eight-second smoke-test limit. The parent environment is unchanged. The caller
has a separate 1800-second wall limit and terminates the child process group on
timeout; a failed or timed-out child fails the test with retained logs.
Official coverage subprocess tracing records the child producer's execution,
and the parent still applies the same publication, byte-custody and pixel checks.
The shared fixture qualifies fresh production before dependent edition controls.
It needs the pinned renderer checkout,
corpus exports, analytics, native publishing tools and pinned sibling fep_formal.
Other controls use real temporary files, Git repositories and direct Pandoc/filter
executions. Installed-tool cases carry the integration marker and are excluded
by `make portable`. They do not substitute for native rendering or visual review.

Inspect every PDF page, open HTML and examine Word content after generation.
A receipt establishes which bytes were rendered, not scientific validity or
visual perfection. This is a software methods manuscript, with explicit proposed
FEP correspondences and verification limits.

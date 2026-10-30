# Reproduce observations, not just installation

A reproducible run identifies source bytes, environment, commands, and outputs.
Rikishi separates the pinned ontology checkout, generated index, Sigma's writable
knowledge base (KB), bounded proof problems, numerical examples, and publication artifacts.

## What to retain

| Evidence | Why it matters |
| --- | --- |
| `config/sumo.lock.json` | Upstream revisions and acquisition identities |
| `uv.lock` and Python prefix information | Python package resolution and interpreter location |
| `output/data/source-manifest.json` | Source-file inventory and integrity metadata |
| `output/data/corpus.json` | Measured counts, source revision, and parser diagnostics |
| `output/reasoning/taxonomy.p` | Exact restricted first-order problem |
| `output/reasoning/taxonomy.json` | Mapping from projected facts to original source |
| `output/reasoning/taxonomy.result.json` | Actual prover command, status, and output |
| `output/research/{e,v}/` | Complete alignment reports, original workbook, source/study/extension bytes, problems and native captures |
| `output/research/fresh-cache/` | Five source-only isolated cache controls, input/tool bindings and raw Java observations |
| `output/manuscript/render-receipt.json` | Template revision, substitutions, source/output hashes |
| `output/manuscript/office-reference.native-default.docx` | Exact native Pandoc reference bytes used in this run, including that export's archive identity |
| `output/manuscript/office-reference.docx` | Approved projection of that exact default: two section-geometry insertions plus only the Hyperlink color and ImageCaption keep-lines style atoms |
| `office_reference` in the render receipt and final Word artifact | Both reference hashes, Pandoc identity, reference geometry and independently observed final geometry |
| `output/manuscript/rikishi-native.docx` and `output/docx/rikishi.docx` | Exact native renderer output and the separately projected final manuscript; neither replaces a reference package |
| `office_content` and `office_math` in the render receipt | Native/final package and main-document hashes, actual row changes/counts and the bounded declared math-structure checks |
| Versioned precedent record, Portable Document Format (PDF) and alignment spreadsheet | Literature identity, mapping sense and original proposal |
| `.omo/evidence/` | Test output, visual inspection, and negative controls |

Preserve these together before changing source revision, query, configuration, or
dependencies. Do not assume a report generated earlier describes the current index.
Run `rikishi stats` and regenerate `rikishi report` when inputs change.

## Deterministic manuscript hydration

The manuscript contains explicit data placeholders and stable labels. Checked
authorities supply publication metadata, corpus observations, model parameters,
software version and formalization metadata. The renderer requires a clean corpus
export and verifies that it matches the index supplying the cover taxonomy.
Unresolved substitutions reject. The shared body is retained as
`output/manuscript/rikishi-body.md`; PDF and Office/Web receive separate projections
with the same body. The receipt binds all authorities, substitutions and rendering
time. [Manuscript methods](manuscript.md) describes the authority and numbering contracts.

Run both fresh E and Vampire (E/V) campaigns and the cache diagnostic before rendering, following
that guide's prerequisite recipe. The workbook is not bundled; acquire and check
the pinned original using [research input preparation](research.md). Publication
stages complete campaign trees under `output/manuscript/research/{e,v}/` and the
cache tree beside them. `render-receipt.json` records the two primary report
hashes in `research_inputs` and inventories retained artifacts. All manuscript
campaign quantities are injected from the validated reports. The campaign
image `research-controls.png` and `research-dashboard.html` derive from those
same reports through `research_figures`; see [research visualizations](research-visualizations.md).

The corpus chart is copied from the report output into the manuscript figure set.
Regenerate the report before rendering so chart and counts describe the same run.
The finite-example JavaScript Object Notation (JSON), plot and graphical abstract use one checked calculation
from the packaged model parameter authority. The abstract retains its exact input
JSON, including the selected direct subclass neighborhood.
The canonical docxology/template adapters then generate PDF, Word, and Hypertext
Markup Language (HTML).
They are imported from a verified Git-archive snapshot of the pinned template
commit, not the active checkout's working files. The receipt identifies the archive
and every imported infrastructure module by Secure Hash Algorithm 256-bit
(SHA-256); the outside origin manifest
records all archived source hashes. The active checkout may be dirty, and its
cleanliness is recorded explicitly without treating unrelated edits as renderer input.

Byte-identical PDF and Word files are not promised across tool versions or runs:
archive timestamps, font libraries, and PDF metadata can differ. The receipt
identifies actual output bytes. Numerical and semantic agreement should be checked
separately from byte equality.

The Word reference has a narrower preservation contract. The producer retains
the exact `office-reference.native-default.docx` returned by its Pandoc call,
then produces `office-reference.docx` through the approved reference policy.
`word/document.xml` receives only `w:pgSz` and `w:pgMar`; all remaining document
Extensible Markup Language (XML) bytes stay exact. `word/styles.xml` receives
only explicit `Hyperlink` color `#005EA8` (with that atom's theme color/tint/shade
selectors removed) and `ImageCaption` `w:pPr/w:keepLines`. The native
`CaptionedFigure` enabled `w:keepNext` and caption base `Caption` are checked and
preserved, without a new figure property. All other style/XML bytes, member
payloads, inventory/order, archive comment and public member metadata must match
the retained original; derived sizes/checksums/offsets reflect changed payloads.
There is no arbitrary theme, font, prose or mathematical rewrite. The final
manuscript is a separate package; it is not required to have identical content
to the reference.

Keep both references with the final Word file and `office_reference` receipt,
including the executable/version/hash identity and `geometry`/`actual` reports.
Do not substitute another native-default export: outer ZIP timestamps may differ
between invocations even with the same executable. Verification binds the exact
retained archive, recomputes the approved two-geometry-plus-targeted-style
projection with `verify_office_reference_policy`, and independently reads all
final sections' geometry. Whole-reference equality includes ZIP metadata;
rehashing wrong styles or geometry cannot authorize them. The existing writer
and page-verifier signatures and frozen record fields remain unchanged.
Matching these checks establishes no Word pagination or
visual-layout result. A separate office-rendering record must identify the actual
input and rendered output hashes before those claims can be made; executable
discovery alone is insufficient. Ordinary digital document text requires at
least 4.5:1 contrast with no native-palette waiver; account for theme precedence,
then measure the actual changed LibreOffice edition. The reviewed release bundle must identify its actual propagation, gate and
bounded edition records, as described in the [qualification guide](current-state.md).
Those records identify their own source and artifact bytes; they do not clear
later changes or establish native Microsoft Word pagination. See [office methods](manuscript.md#explicit-word-geometry-and-retained-reference).

## Native and final Word content custody

Retain the exact `output/manuscript/rikishi-native.docx` passed to the pure-byte
`project_office_content` method and its final `output/docx/rikishi.docx` together.
This pair has a separate preservation contract from the two references: only
enabled row keep-together properties may be inserted into supported ordinary
table rows. Repeated headers and all remaining document XML bytes stay unchanged;
all other ZIP payloads and checked member metadata/order remain bound to the
native package. A fresh renderer invocation cannot replace the retained native
bytes used for this projection.

`office_content` records both package hashes and both main-document hashes,
observed table/row/enabled repeated-header counts and zero-based changed-row hash pairs.
The verifier reconstructs the projection from the retained native bytes and
requires the actual final package and receipt to agree. `office_math` separately
binds the supported complete manuscript math sequence, including the three
gathered displays, the two named companion displays and the atomic
non-entailment/entailment-of-negation pair. Producer and verifier require the
returned matrix inventory length to equal the canonical hydrated body's gathered
count, rather than the isolated fixture's inventory. All editions use the shared canonical
mathematical source; this projection changes no mathematical content or prose.
These bounded checks do not prove mathematical validity or pagination.

Retain office-rendered previews with their exact final-input and output hashes,
renderer identity and page-inspection evidence. A preview clears only the exact
projected final edition it inspected. Preserve the original reports and link
subsequent reviews rather than overwriting findings. See the
[content method](manuscript.md#final-word-content-projection-and-math-checks) and
[current visual boundary](verification.md#word-geometry-and-pagination-status).
Failed candidates remain retained evidence and cannot substitute for an accepted
final artifact. The [prioritized TODO](TODO.md) tracks unverified platform and
interaction scopes separately from completed artifact checks.

## Negative controls and failure interpretation

Tests reject an unnormalized prior, impossible observation, mismatched vectors,
nonfinite values, and positive candidate mass outside joint support. The source
inspection tests use real temporary Git repositories, including missing declarations
and dirty working trees. Prover tests require both a theorem and a nonentailed query
to have distinguishable outcomes. Missing tools and malformed inputs remain errors.

Run the complete project gate described in [verification.md](verification.md).
Capture command exit statuses directly; piping output through a logger without
checking the command's status can turn a failure into apparent success. The
manuscript verifier checks nonempty artifacts, hashes, embedded image bytes,
extracted PDF content, and local HTML figures. Visual inspection remains a separate
step and should record which artifact hash was actually viewed.

## Reproducing an alignment proposal

The [precedent guide](precedent-alignment.md) distinguishes the cited Zenodo
release from identifiers embedded in its files. Retain the exact record metadata,
downloaded file hashes, sheet and row or page locator, and the author's intended
sense before translating a table entry into a local proposal. Record whether its
target already exists at the pinned Suggested Upper Merged Ontology (SUMO) revision and which formal relation is
intended. A prose suggestion or topic label is not an executable axiom.

Keep extension axioms outside the upstream checkout. Give competency questions
an expected polarity and preserve the selected background and exact translated
inputs, including negative controls and inconclusive outcomes. Do not combine a
literature citation, a successful restricted proof, and finite Lean elaboration
into an unproved claim that the whole alignment has been formally verified.

The [executed finite study](research.md) retains original workbook cells and
selected complete source formulas, a declared first-order logic (FOL) kernel and expected polarities.
Each E/V report currently records 12 matched logical cases, 144 numerical passes,
four boundary passes and eight invalid-input rejections. Portable replay
rederives those inputs and results; `research-verify REPORT --sha256 HASH` adds a
separately trusted outer binding. Replay does not authenticate historical process
execution or independently check automated theorem proving (ATP) proof objects. Preserve raw native captures
and their report tree, not just summary counts. Log-input null means exact zero;
returned null linear evidence means positive evidence below float range, with
finite log evidence retained. These are separate states.

## Limits of a receipt

A receipt establishes an observed execution and its inputs. It does not establish
ontology consistency, prove arbitrary SUMO entailments, validate an empirical Free Energy Principle (FEP)
claim, or certify an ontology-to-Lean translation. State those acceptance scopes
separately, and retain inconclusive results as inconclusive.

The observed native Sigma core run illustrates this distinction. With four core
constituents and the versioned compound-type guard patch, `(subclass Human Animal)`
returned `SZSTheorem`, while the negative control `(subclass Human Artifact)`
returned `SZSContradictoryAxioms`. The retained four-premise refutation and
historical seeded Java diagnostic localize a generated cache classification.
The newer [fresh experiment](cache-inheritance.md) uses real KB construction,
source ingestion and `buildCaches()` without seeded maps. Its five controls
cover an isolated fragment and complete pinned Merge: parent-classification and
edge removal eliminate generated partial classification; a synthetic inheritable
class link leaves it present. It does not reconstruct or test consistency of
the complete four-file core. Intended inheritance semantics, repair and corrected
full-profile acceptance remain open. This does not assign inconsistency to the
source ontology. Preserve both query logs and do not treat the positive result
as semantic validation.
The separate restricted taxonomy proof retains its own axiom set and acceptance
scope. See the current runtime and verification guides for the retained evidence.

Native context disclosure has a separate identity from raw ATP input custody.
Supported Sigma regeneration can place the invocation-local profile directory
in standalone source comments, changing the raw background hash while leaving
every complete statement unchanged. After verifying the exact capture bytes,
Rikishi compares the entire ordered statement-text fingerprint and registered
executable, Sigma-class, lock and configuration bindings. Only standalone
comments and layout are omitted by the structural parser; formula text, roles,
names, order and annotations remain bound. A mismatch or invalid input reports
`unknown`. The raw input hashes remain retained and required for replay. Context
matching does not alter a timeout, establish source-ontology inconsistency, or
validate an arbitrary translation. See [runtime contracts](runtime.md).

# Finite research visualizations

`rikishi.research_figures` exports the finite alignment campaign as a print
figure, exact-input receipt and self-contained offline explorer. It reads the
retained directory through `validate_alignment_report`; it never runs a solver,
rebuilds an index or fetches a resource. See [research.md](research.md) for the
study, original-source preparation and saved-evidence trust boundary.

```python
from pathlib import Path
from rikishi.research_figures import render_research_figures

paths = render_research_figures(
    Path("fresh-research-figures"),
    Path("output/research/e/alignment-report.json"),
    comparison_path=Path("output/research/v/alignment-report.json"),
    dpi=300,
    decimal_places=3,
)
```

The application programming interface (API) is `render_research_figures(output: Path, report_path: Path, *,
comparison_path: Path | None = None, dpi: int, decimal_places: int) -> list[Path]`.
Paths are returned in this deterministic order:

1. `research-controls.png`
2. `research-controls.svg`
3. `research-controls.json`
4. `research-dashboard.html`

Dots per inch (DPI) is an integer from 72 through 1200. Decimal places is an integer from 0
through 8 and affects displayed scientific notation only. Exact report values
remain in the JavaScript Object Notation (JSON). Existing artifact names are refused, preserving their bytes.
Validation, pair checks and print-layout checks happen before output creation.
An input/output (I/O) failure during export can leave partial artifacts; preserve and inspect
them, then use a fresh output directory.

A second report must use a distinct prover family and agree on the complete
study, authority, source claims, lock bindings and numerical data. Retained
study, complete source report, original workbook, local extension and every
generated logical problem must also have identical bytes. Different logical
outcomes remain visible. A single-family export contains only that family.

The figure is fixed at 174 × 210 mm, with source text of at least 7.5 pt.
Publication must independently join both placement axes to the original figure
and retain the required 7.5 pt nominal minimum after scaling; source font size
alone cannot qualify a reduced image. A concise footer explicitly labels Secure Hash Algorithm 256-bit (SHA-256)
fingerprint prefixes and points to the
companion JSON and Hypertext Markup Language (HTML). Full source paths, hashes, source quotations and the
complete figure custody footer remain in JSON and accessible HTML
provenance. Visible labels outside the canvas raise `ResearchFigureError`.
The logical matrix keeps every declared case in study order,
distinguishes backgrounds from queries, and shows expected and observed
polarities separately. `=`, `!` and `?` identify matched, mismatched and
unresolved observations without relying on color. Finite campaign completion
and semantic validation are distinct fields; the latter remains false.

Numerical points are actual row errors divided by each predeclared tolerance.
The threshold is 1. Reference, permutation and rescaling use distinct marker
shapes in navy, teal and burnt orange. Symmetric-logarithmic scaling (symlog) is linear below 0.001; zero
errors stay zero. Ordinary rows, support boundaries and invalid-input
rejections retain their own denominators. Arithmetic remains separate from the
first-order logic (FOL) fragment and supplies no Suggested Upper Merged Ontology
(SUMO) preservation or biological validation claim.

The JSON's `provenance` list retains the complete custody text. It also contains
each complete validated report, the SHA-256 of its original
report-file bytes, original report paths, measured case IDs and solver statuses,
all numerical ratios, and dimension/candidate aggregates with row counts,
maxima and exact-zero counts. It also records rendering policy, the ratio
threshold and the original numerical rows, errors and tolerances. The embedded
JSON in the HTML is the same structured input, with HTML delimiters escaped.

Open `research-dashboard.html` locally. All Cascading Style Sheets (CSS), JavaScript,
Scalable Vector Graphics (SVG) and input data
are embedded. A content security policy blocks external resources and network
connections. Native labeled filters select observed logical status,
disposition, numerical dimension, candidate and population. Visible counts
report both the filtered rows and the full denominator; population totals stay
visible. Empty results have explicit messages. Original source files, revision,
hashes, Uniform Resource Locators (URLs), access date, exact sheet/cell values, full source-language citations, local
sense choices, complete inputs, errors and capture bindings are inspectable.
Source strings enter the Document Object Model (DOM) through `textContent`; no evaluation or HTML
interpolation of user strings is used. A grayscale control changes the print
figure while retaining its text and marker distinctions.

## Focused verification and integration boundary

Run `tests/manuscript/test_research_figures.py` with the declared uv environment
and a fresh GitVault `--basetemp` beneath the assigned evidence directory. Its
module fixture runs real E and Vampire campaigns once per invocation. For a
layout-only followup, `RIKISHI_RESEARCH_FIGURE_TEST_REPORTS` can supply a JSON
array of two existing E/V report paths; both must pass portable validation before
reuse. Tests
exercise actual captures, deterministic repeat exports, single-family export,
pair rejection, rehashed source changes, altered numerical data and policy,
empty populations, invalid arguments, bounded print dimensions and minimum type
size, complete long-provenance preservation, layout refusal, artifact preservation,
script injection and a JavaScript syntax negative control. Mutated saved
baseline controls are explicitly labeled as synthetic and retain incomplete
summaries; they are not live solver observations.

`tests/manuscript/research_browser_scenarios.js` is a browser-evaluable function
for the generated HTML. It checks real DOM rows against embedded source inputs,
all observed statuses, matched/mismatch/unresolved filters, dimension/candidate
combinations including empty results, full-population totals, boundary controls,
labels, live count announcements, grayscale behavior, inert source strings and
the absence of network resource loads. Its return value includes page overflow
and viewport dimensions. Run it on both desktop and mobile, and inspect the
visible layout; a syntax check alone does not establish browser behavior.

Root owns publication integration, canonical output generation, actual browser
inspection and the repository gate. This module's focused evidence does not
certify native manuscript editions or full repository acceptance.

## Word placement and pagination boundary

The print figure's canvas, type-size and clipping checks concern the figure
itself. Word publication uses a separate retained Pandoc reference to specify
portrait Letter, 215.9 × 279.4 mm, and 12 mm body margins. The reference records
12240 × 15840-twip pages and nearest-twip 680 margins; 1440 twips equal 25.4 mm.
The final verifier checks explicit geometry in every actual Word section.
These dimensions do not establish where a figure falls on a page or whether
its caption, surrounding paragraphs and references paginate well.

Retain `office-reference.docx`, the exact
`office-reference.native-default.docx` and the `office_reference` render-receipt
record with the exported Word file. Within `word/document.xml`, reference
generation inserts only the two page-geometry elements; all remaining document
Extensible Markup Language (XML) bytes stay exact. Within `word/styles.xml`, it
replaces only the `Hyperlink` color atom with explicit `#005EA8`, removing its
theme color/tint/shade selectors, and inserts only `ImageCaption`
`w:pPr/w:keepLines`. Native `CaptionedFigure` enabled `w:keepNext` and caption
base `Caption` are required and preserved, without an added figure property.
Other style/XML bytes and member payloads stay exact, with inventory/order,
archive comment and public member metadata preserved; changed payloads have
derived sizes/checksums/offsets. Pure reference verification recomputes that
exact approved projection from the retained default; rehashing cannot waive
wrong styles or geometry. No arbitrary theme/font, prose or math rewrite is allowed.
Do not compare a newly exported default archive's hash as a substitute: outer
ZIP timestamps may vary between calls. The final manuscript is a separate
package, whose geometry and embedded figure bytes have their own checks.

The native manuscript is retained separately as
`output/manuscript/rikishi-native.docx`. The byte-only content projection adds
row keep-together properties to produce `output/docx/rikishi.docx`; it preserves
repeated headers, figure payloads, captions, mathematics and all remaining
document XML. Its `office_content` receipt and independently recomputed check
bind that native/final pair, separately from the two reference packages.
`office_math` checks the supported complete manuscript math sequence, including
the three gathered displays, two named companion displays and the distinct
atomic non-entailment/entailment-of-negation pair. Its returned matrix inventory
must match the canonical hydrated body's gathered count in both producer and
verifier. The math source is shared by
all editions; these checks supply no general mathematical validation.

Image-byte agreement, XML geometry, row properties and the standalone explorer's
browser layout remain distinct from office pagination. Inspect entire rows,
repeated headers, math displays, captions and neighboring page boundaries against
the exact final-input hash. A preview or bounded package check cannot clear a
different edition, and LibreOffice pagination does not establish Microsoft Word
pagination. Ordinary digital document text requires at least 4.5:1 contrast with
no inherited-palette waiver; resolve theme precedence before measuring the
selected explicit color in actual LibreOffice output. The release verification summary must identify actual native propagation,
edition and independent visual checks with their remaining limits. The
[qualification guide](current-state.md) does not substitute for those records.
Changed artifacts require fresh evidence under the
[content method](manuscript.md#final-word-content-projection-and-math-checks).
The [prioritized TODO](TODO.md) separates remaining presentation refinements from
unverified native and device scopes.

Paper explorer links use `../figures/research-dashboard.html` and
`../figures/bridge-explorer.html`. Each resolves from a sibling Portable Document
Format (PDF), Word or HTML edition directory to `output/figures/`; actual targets
and retained copies are verified. Keep this offline artifact relationship when
moving a publication tree; the explorer's numerical interactions execute no new proof.

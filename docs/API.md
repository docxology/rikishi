# Command-line, Python, web, and agent interfaces

The command-line interface (CLI), Hypertext Transfer Protocol (HTTP) application
programming interface (API) routes, and
Model Context Protocol (MCP) tools adapt shared operator methods. They inspect the
Suggested Upper Merged Ontology (SUMO), whose Standard Upper Ontology Knowledge
Interchange Format (SUO-KIF) source remains distinct from automated theorem
proving (ATP) inputs. Responses use JavaScript Object Notation (JSON); offline
reports include Hypertext Markup Language (HTML), Portable Network Graphics (PNG),
and Scalable Vector Graphics (SVG) artifacts. Numerical divergence fields use
Kullback-Leibler (KL) divergence.
The finite variational example is a separately scoped Free Energy Principle
(FEP) connection, rather than a consequence of ontology inference.
Secure Hash Algorithm 256-bit (SHA-256) digests bind retained report bytes to a
separately recorded authority.

All examples run from the checkout after `source scripts/env.sh` and
`uv sync --locked`. `--root PATH` precedes the CLI subcommand; `RIKISHI_ROOT`
supplies its default. Local state is under `.rikishi/`, generated exports under
`output/`. The complete environment requires `uv run rikishi bootstrap`.

| CLI | Operation |
| --- | --- |
| `bootstrap` | Check out pinned upstream sources and build the local runtime |
| `doctor` | Inspect actual source revisions and installed artifacts |
| `index [--source DIR]` | Recursively parse `.kif`, build SQLite atomically, export manifest |
| `stats` | Counts, per-file formula totals, predicates, parse errors, revision |
| `verify-source` | Read-only comparison of current SUO-KIF bytes/revision against indexed snapshot |
| `metrics` | Exact formula-head composition, file concentration, unique-edge degree distribution |
| `files [--path TEXT] [--sort path\|formulas] [--descending] [--limit 50] [--offset 0]` | Page indexed files and hashes; literal path substring |
| `formulas [--text TEXT] [--head NAME] [--path FILE] [--term NAME] [--limit 50] [--offset 0]` | Full retained formulas with original source lines and hashes |
| `relations` | Complete direct binary relation inventory with assertion multiplicity |
| `taxonomy [--relation subclass\|subrelation] [--path FILE] [--limit 50] [--offset 0]` | Source graph endpoints, roots, multiple parents, components and cycle diagnostics |
| `taxonomy-path SOURCE TARGET [--relation subclass\|subrelation] [--path FILE] [--max-depth 20] [--max-visited 10000]` | Bounded shortest child-to-parent path with exact source evidence |
| `search Organism [--limit 30]` | Case-insensitive substring search of term names |
| `term Organism` | Documentation, first 100 referencing formulas, asserted taxonomy |
| `graph Organism [--limit 80] [--relation subclass]` | Bounded adjacent asserted binary relationships |
| `taxonomy-proof Human AutonomousAgent` | Run E on an explicit first-order projection of `Merge.kif` |
| `prove problem.p [--prover e\|v] [--timeout 10] [--output DIR]` | Run a selected installed prover with retained input and processor-time/wall-clock limits |
| `compare-provers problem.p [--timeout 10] [--output DIR]` | Run E and Vampire (E/V) on identical retained problem/include bytes and report bounded status agreement |
| `inference-catalog` | Inspect registered source-bound scenarios, conjectures, controls, and scope without launching a prover |
| `inference-run OUTPUT [--prover both\|e\|v] [--timeout N]` | Run selected native families on the declared laboratory into a fresh directory |
| `inference-verify REPORT --sha256 DIGEST` | Replay retained laboratory evidence against a separately trusted report digest |
| `inference-publish REPORT --sha256 DIGEST` | Strictly replay, then atomically register the local dashboard descriptor; preserve any differing previous descriptor; no prover execution |
| `bridge-catalog` | Inspect the shared finite witness design without a prover or compiler |
| `bridge-run OUTPUT [--prover both\|e\|v] [--timeout 10]` | Produce a fresh repository-local Lean, numerical, and selected SUMO packet; default prover selection is `both` |
| `bridge-verify REPORT --sha256 DIGEST` | Strictly replay the retained bridge packet against a required independently supplied digest; no native execution |
| `bridge-case REPORT CASE_ID [--prover e\|v] --sha256 DIGEST` | Inspect one verified case with its shared numerical witness and retained Lean source; default prover is `e` |
| `bridge-figures REPORT OUTPUT --sha256 DIGEST` | Replay the packet, then export report-derived figures and an offline explorer into a fresh directory |
| `research-run OUTPUT [--prover e\|v] [--workbook PATH] [--source-report PATH]` | Execute the declared finite study into a fresh repository-local directory |
| `research-verify REPORT [--sha256 HASH]` | Portably replay the retained study; optionally require a separately trusted outer report hash |
| `cache-diagnostic OUTPUT [--timeout 60]` | Run five source-only isolated Sigma cache controls with stable input/tool bindings |
| `fep-demo` | Finite inference model, independent decomposition, and objective scan |
| `active-demo` | Standalone synthetic one-step action comparison; complete matrices, exact predictions and decimal score strings; no index or native runtime required |
| `fep-evaluate MODEL.json [--logarithmic]` | Evaluate a strict explicit finite model; log mode retains underflowed support and log evidence |
| `fep-inspect [--repo DIR]` | Read committed Lean declarations at the recorded FEP pin |
| `fep-verify [--repo DIR] [--compiler FILE] [--packages DIR] [--output DIR]` | Compile pinned finite modules in a new isolated workspace and inspect declaration axioms |
| `dashboard [--port 8765]` | Serve the workbench on `127.0.0.1` |
| `report` | Corpus JSON and source manifest, standalone HTML and PNG/SVG chart |
| `mcp` | Serve read-only MCP over standard input/output |

Finite commands return JSON. Missing terms, malformed probabilities, absent
artifacts, and failed subprocesses return nonzero status and a JSON error on
stderr. `index` returns nonzero if any source file fails structural parsing;
its result retains the complete diagnostic list. A malformed file contributes
no partially parsed formulas. `prove` and `taxonomy-proof` return zero only for
the `Theorem` outcome in the [SZS result ontology](https://szs.tptp.org/). `doctor` is an inspection, not a running-service gate.

`prove --output` and `compare-provers --output` require fresh repository-local
directories; existing captures are preserved. Comparison returns zero for agreement
on conclusive statuses and two for disagreement or inconclusive runs. Its output
sets `semantic_validation=false`; matching prover statuses do not establish source
ontology consistency, translation soundness or a scientific interpretation.

The installed Sigma script is a separate interface:
`uv run --locked --no-sync python scripts/runtime-query.py QUERY
[--prover e|v] [--timeout 15] [--prover-wall-timeout N] [--output LOG]`.
Its importable function is
`runtime_query.run_query(root, query, *, prover="e", timeout=15, output=None, prover_wall_timeout=None)`.
The native limit is a strict integer from 1–300; an explicit wall allowance is a
strict integer from 1–3600. It does not change the native limit. Without an
override, prover wall time remains `timeout + 5` and Java wall time remains
`600 + timeout`; explicit wall mode uses `600 + prover_wall_timeout` for Java.
The frozen `QueryBudgets` value reports `mode`, `native_limit_seconds`,
`prover_wall_seconds` and `java_wall_seconds`. The report includes this value and
`budgets_path`; exact saved budget bytes and the numeric values are bound into
invocation provenance and checked by the live runner. The generic saved-result
reader does not independently reopen the separate budget document. See the
[runtime contract](runtime.md) for output custody and timeout interpretation.

The inference laboratory uses explicit first-order logic (FOL) kernels selected
from pinned source formulas. Its [walkthrough](inference-tutorial.md) distinguishes
positive conjectures, countermodels, background satisfiability, and premise-removal
controls. Native execution writes `inference-report.json` within the selected fresh
output directory. Retain that directory as a unit, including problems, source
records, and native captures. `inference-verify` checks the saved report and its
dependencies; it neither runs a prover nor checks every proof inference with an
independent proof checker. A matching digest binds the selected report's bytes;
it does not establish trust in the person or system that supplied the digest.

After `inference-run` and `inference-verify`, use `inference-publish` with the same
independently retained digest to register the run for the dashboard. It writes
the local `output/inference/published.json` descriptor only after strict replay
and preserves any differing previous descriptor. This is local registration,
with no native prover invocation or external publication.

### Finite witness bridge

The bridge shares three strictly positive rational Boolean (`Bool`) witnesses
across exact Python `Fraction` posterior calculations, an independent 80-digit
`Decimal` reference, concrete Lean instantiations at revision
`9a0694f16b8e89b66b2f7f8cc7426c650dd2c4de`, and selected SUMO role scenarios.
Each witness binds its prior, complete observation kernel, candidate distribution,
observation `True`, and authored entity identifiers. Every hidden-state tuple is
ordered `(false, true)`: index 0 is `Bool.false`, index 1 is `Bool.true`, and the
explorer varies `q(false)=q0`. Observed `True` is the observation value, not the
first hidden state. The Lean kernel includes both Boolean observations; the
numerical likelihood selects observation `True`.
The [architecture contract](architecture.md#shared-finite-witness-obligations)
separates these obligations and their controls. This is no general SUMO-to-Lean
semantic-preservation result.

Native production requires an available runtime lane: wait for its current owner
to finish before launching another campaign. Preserve active jobs and failed
evidence. `bridge-run` accepts an integer timeout of 1–300 seconds, default 10,
and an existing symlink-free parent for its fresh output directory. The timeout
is the native prover budget; it does not bound the entire Lean/prover campaign.
The canonical invocation, when `output/bridge` does not yet exist, is:

```sh
uv run --locked --no-sync rikishi bridge-run output/bridge --prover both --timeout 10
shasum -a 256 output/bridge/bridge-report.json
```

For your own fresh completed producer run, record the printed digest separately
with the producer's custody evidence. Preserve the entire packet, including
`study.json`, `source/`, `extension.kif`, `numerical.json`, locks, implementation
and executable bytes, problems, captures, and Lean receipts/artifacts. Computing
a hash of a received untrusted report only fingerprints the received bytes; it
does not establish producer custody. A recipient must obtain the expected digest
from a separately trusted record or channel.

With that external digest in `BRIDGE_REPORT_SHA256` and a case identifier from
the report in `BRIDGE_CASE_ID`, inspect the packet without native execution:

```sh
: "${BRIDGE_REPORT_SHA256:?Supply the independently trusted report digest}"
: "${BRIDGE_CASE_ID:?Select a case identifier from the retained report}"
uv run --locked --no-sync rikishi bridge-verify output/bridge/bridge-report.json --sha256 "$BRIDGE_REPORT_SHA256"
uv run --locked --no-sync rikishi bridge-case output/bridge/bridge-report.json "$BRIDGE_CASE_ID" --prover e --sha256 "$BRIDGE_REPORT_SHA256"
uv run --locked --no-sync rikishi bridge-figures output/bridge/bridge-report.json output/bridge-figures --sha256 "$BRIDGE_REPORT_SHA256"
```

Select `--prover v` for a Vampire-only packet; the default case selection does not
silently substitute a missing E run. Figure output must be a new directory under
an existing symlink-free parent on mounted GitVault. The exporter declares
`bridge-evidence.png`, `bridge-free-energy.png`, and `bridge-native-controls.png`,
their `.svg` counterparts, `bridge-explorer.html`, and `bridge-figure-inputs.json`.
The offline explorer presents retained case/Lean evidence and finite candidate
exploration; changing a numerical candidate does not execute a new proof.

`bridge-run` returns 0 when its observed `summary.passed` is true and 2 for a
returned incomplete summary; caught input, replay, and runtime errors return 1.
Strict replay rejects failed required obligations. Read counts, statuses,
selected prover families, and completion from the actual retained report, never
from the catalog. Lean's declaration inventory includes definitions as well as
theorems. Replay rederives inputs, arithmetic and capture interpretation without
running Lean, E, or Vampire; it does not authenticate historical execution,
independently check prover proof steps, or retain/authenticate every external
compiler/dependency artifact. A documented command or export name is not evidence
that a native campaign or figure export has completed.

`research-run` defaults to E, newly audits the live index and creates its source
report; `--source-report PATH` explicitly selects a frozen input. `--workbook PATH`
changes only acquisition location: the original workbook hash remains pinned.
The workbook is not bundled; fresh installations must supply `--workbook` with
the acquired, hash-verified file. Omitting it retains the study's historical
default location and does not acquire or substitute inputs. See
[input preparation](research.md). The command
retains complete report/source/study/workbook/extension bytes, problems and native
captures. Both research commands exit 0 for a complete declared campaign and 2
for an incomplete campaign. `research-verify` rederives saved source claims,
problems, arithmetic and status interpretation without running a native solver;
it does not authenticate historical execution or independently check proof objects.

`cache-diagnostic` requires a fresh repository-local directory and a 1–120 second
shared deadline. It exits 0 for `status="observed"`, 2 for `status="failed"`;
caught input/runtime errors exit 1, as for the research commands. It uses real knowledge base (KB)
construction, source ingestion and `buildCaches()` without seeded maps, covering
the declared fragment and complete Merge only. It does not check the four-file
core's consistency or implement a repair. See [cache contracts](cache-inheritance.md).

`verify-source` fails for added, missing, changed, escaping, or previously rejected
SUO-KIF sources and for a changed recorded Git revision. File agreement and revision
agreement are separate fields; unversioned input has `revision_matches: null`.
A dirty unrelated non-KIF file is reported by `current_clean` independently.

`taxonomy-proof` emits `output/reasoning/taxonomy.p`, its source/line manifest
`taxonomy.json`, and full prover output `taxonomy.result.json`. It selects direct
`subclass` facts from `Merge.kif` and explicitly adds subclass transitivity. This
is a restricted first-order projection: a countermodel there is not a claim that
the corresponding full SUMO query is false. Running a subsequent query replaces
these working files; copy an experiment to a named evidence directory to retain it.

## Python

```python
from pathlib import Path
from rikishi.ontology import OntologyIndex
from rikishi.fep import free_energy

index = OntologyIndex(Path(".rikishi/ontology.sqlite"))
organism = index.term("Organism")
result = free_energy([0.5, 0.5], [0.8, 0.2], [0.8, 0.2])
assert abs(result["free_energy"] - result["surprise"]) < 1e-12
```

`build(source)` indexes nested domain, translation, development, and test SUO-KIF
files. These structural counts differ from Sigma's selected knowledge-base
profile. Numeric literals, strings, logical connectives, and variables are not
counted as term symbols. Repeated formulas contribute separate source occurrences.
Only top-level binary atomic assertions become edges; expressions inside
implications and quantified bodies remain available as formula text.

Importable research methods are
`alignment.run_alignment(root, output, *, study=None, source_report=None,
workbook_path=None, prover="e")` and
`alignment.validate_alignment_report(path, *, trusted_report_sha256=None)`.
Fresh cache execution is
`cache_inheritance.diagnose_cache_inheritance(root, output, *, timeout=60)`.
Their [study](research.md) and [cache](cache-inheritance.md) guides define the
retained evidence and trust boundaries; transports delegate to these methods.

### Office page policy

[`publication_office`](../src/rikishi/publication_office.py) exposes these Python
methods; manuscript rendering calls them through the existing renderer workflow:

```text
write_office_reference(output: Path, *, margin_mm: float,
    page_width_mm: float = 215.9, page_height_mm: float = 279.4,
    pandoc_path: str = "pandoc") -> OfficeReferenceReceipt
verify_office_reference_policy(default_docx: bytes, reference_docx: bytes, *,
    margin_mm: float, page_width_mm: float = 215.9,
    page_height_mm: float = 279.4) -> OfficePagePolicyReport
verify_office_page_policy(docx: Path, *, margin_mm: float,
    page_width_mm: float = 215.9, page_height_mm: float = 279.4) -> OfficePagePolicyReport
```

The writer invokes native Pandoc for its version and default `reference.docx`.
It requires an existing symlink-free parent and refuses either occupied output
with `FileExistsError`. It retains the exact default archive beside the reference
as `<output.stem>.native-default.docx`. `OfficePagePolicyError(detail: str)`, a
`ValueError`, reports package, tool and page-policy failures; filesystem errors
also propagate. `verify_office_page_policy` only reads the supplied document
package. The additional `verify_office_reference_policy` accepts bytes and
performs no filesystem or native-tool access; it returns the existing
`OfficePagePolicyReport` without adding fields. The writer and page-verifier
signatures and both frozen record field lists below are unchanged.

The returned records are frozen dataclasses with these fields:

| Record | Fields |
| --- | --- |
| `OfficeReferenceReceipt` | `reference_doc: Path`, `default_reference_doc: Path`, `reference_sha256: str`, `default_reference_sha256: str`, `pandoc_executable: Path`, `pandoc_sha256: str`, `pandoc_version: str`, `geometry: OfficePagePolicyReport` |
| `OfficePagePolicyReport` | `docx_sha256: str`, `margin_mm: float`, `page_width_mm: float`, `page_height_mm: float`, `margin_twips: int`, `page_width_twips: int`, `page_height_twips: int`, `section_count: int` |

The policy uses portrait Letter paper, 215.9 × 279.4 mm, by default. Decimal
half-up rounding converts millimetres to twips (1440 twips = 25.4 mm) within 0.01 mm:
the configured 12 mm margin becomes 680 twips; Letter becomes 12240 × 15840 twips.
Every actual section must have explicit page size and four body margins, zero
gutter, one text column, and explicit header/footer distances within the margin.

The approved reference projection has two distinct payload targets:

| Target | Permitted change from the exact retained native default |
| --- | --- |
| `word/document.xml` | Insert only `w:pgSz` and `w:pgMar`; all remaining document Extensible Markup Language (XML) bytes stay exact. |
| `word/styles.xml` | Replace only the `Hyperlink` character style's color atom with `<w:color w:val="005EA8"/>`, removing `themeColor`, `themeTint` and `themeShade` selectors from that atom. Insert only `<w:pPr><w:keepLines/></w:pPr>` in the `ImageCaption` paragraph style, before any run properties. |
| Native figure linkage | Require `ImageCaption` to derive from `Caption` and the native `CaptionedFigure` paragraph style to have enabled `w:keepNext`; preserve that linkage without inserting a figure property. |
| All remaining content | Preserve every other style/XML byte and member payload, member inventory/order, archive comment and public member metadata. Derived checksums, sizes and offsets reflect the approved changed payloads. |

The styles part must be bound by the native document's internal styles
relationship and content-type declaration. Missing, ambiguous or unsupported
native targets fail with `OfficePagePolicyError`; no arbitrary theme, font,
prose or mathematics rewrite is allowed. `themeColor="accent1"` can override a
fallback color, so changing the fallback alone does not establish the effective
link color. The ordinary digital-text policy requires at least 4.5:1 contrast
against its actual background; inherited palette is no waiver. `#005EA8` is the
selected policy color. Actual contrast and complete caption grouping in a new
manuscript edition require separate independent review.

`verify_office_reference_policy` reconstructs the approved reference from the
exact supplied default and requires whole-archive equality with the supplied
reference, including its metadata. An inverse check must restore only the changed
native color atom and remove only the approved inserted elements, recovering
the original bytes. Rebinding a receipt
hash cannot authorize a different style, geometry or member. Archive timestamps
can vary between Pandoc invocations; re-exporting the default need not reproduce
its archive digest and cannot replace the exact retained input. A reference
that supplies geometry without the required styles fails this policy.

The manuscript workflow retains `output/manuscript/office-reference.docx` and
`output/manuscript/office-reference.native-default.docx`, passes the former as
`reference_doc` to `render_docx`, and records both paths/digests and the Pandoc
executable path/version/digest in `render-receipt.json`'s `office_reference`.
Its `geometry` describes the reference; its added `actual` field describes the
final Word file using the same `OfficePagePolicyReport` fields. The final verifier
must independently read both geometries and recompute the approved reference
projection from the exact retained default, including the targeted styles.
These checks establish no Word pagination or visual acceptance. Native
propagation, final editions and LibreOffice contrast/page review have separate
evidence requirements. The release verification summary must identify their
actual bounded results; changed editions require new matching evidence. See the
[qualification guide](current-state.md).
See the [manuscript recipe](manuscript.md).

## Office content projection and math

[`publication_office_content`](../src/rikishi/publication_office_content.py)
exposes three pure byte interfaces for the Office Open XML Word package
(`.docx`). They perform no filesystem access or native execution:

```text
project_office_content(native_docx: bytes) -> OfficeContentProjection
verify_office_content_projection(native_docx: bytes, projected_docx: bytes) -> OfficeContentReceipt
verify_office_content_math(docx: bytes) -> OfficeMathReport
```

All four returned record types are frozen dataclasses with slots. Their complete
field order and annotations are:

| Record | Fields |
| --- | --- |
| `OfficeRowChange` | `row_index: int`, `before_sha256: str`, `after_sha256: str` |
| `OfficeContentReceipt` | `schema_version: int`, `native_sha256: str`, `projected_sha256: str`, `native_document_sha256: str`, `projected_document_sha256: str`, `table_count: int`, `row_count: int`, `repeated_header_count: int`, `changes: tuple[OfficeRowChange, ...]` |
| `OfficeContentProjection` | `docx: bytes`, `receipt: OfficeContentReceipt` |
| `OfficeMathReport` | `gathered_sha256: tuple[str, ...]`, `atomic_non_entailments: int`, `entailments_of_negation: int` |

`project_office_content` inserts enabled `w:cantSplit` in every supported ordinary
table row, including header rows, that lacks it. Existing enabled properties
remain byte-identical. It splices row bytes in schema order without serializing
the whole XML tree: repeated `w:tblHeader` properties, text, math, geometry,
styles, every other document XML byte, and every other ZIP member payload are
preserved. Member order, archive comment and public member metadata are also
preserved, excluding derived sizes, checksums and offsets. Repacking may change
compressed archive bytes; the contract concerns exact payload bytes and that
metadata. If no insertion is
needed, it returns the original archive bytes.

Support is limited to ordinary unmerged text table rows with the admitted native
`<w:tr>` serialization and supported row-property syntax/order. Nested tables,
vertical/horizontal merges, grid spans, drawings within rows, duplicate or unknown
row properties, comments, character-data sections and explicit disabled
`cantSplit` policies are rejected. Unsafe,
ambiguous or malformed packages are rejected by the existing bounded package
parser. `OfficeContentError(detail: str)` is a `ValueError` with a `detail: str`
attribute; it also wraps that parser's `OfficePagePolicyError`. These are genuine
unsupported-layout errors, not permission to rewrite content. A row taller than
the usable page needs a separate layout decision: `cantSplit` alone cannot
establish pagination or visual acceptance.

`verify_office_content_projection` independently reconstructs the permitted
inserts from the supplied native package and requires exact projected document
bytes, other member payloads, inventory/order, archive comment and checked
metadata. It computes schema version 1, both whole-package and document XML
digests, observed table/row/enabled repeated-header counts, and the changed rows' exact
before/after hashes. `row_index` is a zero-based document-order row ordinal;
`changes` contains only rows that received an insertion. Counts are derived
from supplied packages, not fixed manuscript totals.

`verify_office_content_math` checks the supported complete manuscript math
sequence: the three `gathered` displays for taxonomy sets, finite-objective
decompositions and Lean finite definitions, and the two companion displays
(`sumo-translated-core` and `logarithmic-normalization`). Complete display
expressions must match the supported structure, with only the exact native
equation-number suffix permitted. It rejects literal alignment `&` and
combining slash U+0338 in math text, and requires the ordered structural pair of
distinct atomic `T⊭q` and `T⊨¬q` expressions, with one non-entailment glyph in
math text. The complete-publication contract requires `gathered_sha256` to
inventory that supported complete sequence; both producer and verifier compare
its length with the canonical hydrated body's gathered count. An isolated
three-display fixture cannot satisfy the complete-body requirement. The relation
fields retain the two required occurrence counts. This is a manuscript-specific serialization check, not a general math
verifier, scientific validation or theorem proof.

The shared canonical [`manuscript/rikishi.md`](../manuscript/rikishi.md) uses
`gathered` displays, repeats `F(q)=` on each decomposition row, and uses atomic
`\nvDash` for non-entailment. All editions use that shared source; the row
projection neither repairs math nor creates a Word-only mathematical fork.

The reference-policy API above is separate from this final-content projection;
its existing writer/page-verifier signatures and frozen record fields are unchanged.
[`manuscript`](../src/rikishi/manuscript.py) first retains the native renderer's
`output/manuscript/rikishi-native.docx`, projects its bytes, checks the resulting
math and writes `output/docx/rikishi.docx`. Both packages are artifact-bound in
`output/manuscript/render-receipt.json`; `office_content` stores the
`OfficeContentReceipt` fields and `office_math` stores the `OfficeMathReport`
fields. Tuple fields become JSON arrays and row-change records become objects.
`office_reference.actual` continues to describe the final file's geometry.
[`manuscript_verification`](../src/rikishi/manuscript_verification.py) requires
the staged native artifact, recomputes the projection and math reports from the
retained native/final bytes, and compares them with the receipt. Its result uses
`office_content_projection` and `office_math` for those recomputed reports.

Changed final editions require a new visual review. Code review and final visual
acceptance have separate source- and artifact-bound records; rejected candidates
remain preserved evidence rather than accepted outputs. These interfaces assert
no completed native campaign or final acceptance. The
[qualification guide](current-state.md) defines the required current records. See
the [final Word recipe](manuscript.md#final-word-content-projection-and-math-checks)
and [custody contract](architecture.md#final-word-content-custody).

## HTTP

The read-only workbench exposes `/api/stats`, `/api/analytics`, `/api/search?q=Organism`,
`/api/terms/Organism`, `/api/graph?term=Organism&limit=40`, and `/api/fep?q=0.8`.
Corpus inspection adds `/api/corpus/files`, `/api/corpus/formulas`,
`/api/corpus/relations`, `/api/taxonomy` and `/api/taxonomy/path`.
The inference workspace adds these read-only routes:

| Route | Contract |
| --- | --- |
| `GET /api/inference/catalog` | Registered source-bound laboratory design; no native execution |
| `GET /api/inference/published` | Locally published descriptor, validated report, and explicit local-digest authority boundary |
| `GET /api/inference/report?report=output/inference/inference-report.json&sha256=DIGEST` | Replay an existing repository-contained report using the independently supplied 64-character lowercase hexadecimal digest |
| `GET /api/inference/case?report=RELATIVE&sha256=DIGEST&case_id=REGISTERED_CASE_ID&prover=e` | Verified case, exact submitted problem, native stdout/stderr and command; `prover` accepts `e` or `v` |

The report route returns HTTP 404 for a missing artifact and HTTP 422 for invalid
inputs or failed replay. Paths must satisfy the server's containment rules.
These routes do not install tools, write evidence, or start a prover. The
published response has `descriptor: {report, sha256}`, `report`, and `authority`.
Its descriptor records local publication authority; independently retain the
digest when transferring evidence. Case inspection exposes native proof output
without independently checking each proof inference.

Bridge inspection adds the following read-only routes:

| Route | Contract |
| --- | --- |
| `GET /api/bridge/catalog` | Shared witness and scenario design; no compiler or prover execution |
| `GET /api/bridge/report?report=output/bridge/bridge-report.json&sha256=DIGEST` | Strict replay of the retained bridge packet against the independently supplied digest |
| `GET /api/bridge/case?report=RELATIVE&sha256=DIGEST&case_id=ID&prover=e` | Verified case, scenario, shared rational/numerical witness, selected source claims, Lean declaration names/source/hash, submitted problem, native command and standard output/error |
| `GET /api/bridge/explorer?report=RELATIVE&sha256=DIGEST` | Self-contained interactive view of verified saved evidence and local finite calculations; no native execution |

Bridge `report` paths must be nonempty repository-relative paths without `..`
components or symlink traversal. `sha256` is required and must contain exactly
64 lowercase hexadecimal characters. Case `prover` accepts `e` or `v` and defaults
to `e`. Missing reports or cases return HTTP 404; invalid inputs and failed replay
return HTTP 422. These routes write no evidence and start no native process.
The explorer applies the same path and digest requirements. Case inspection also
distinguishes active assumptions (including rational labels), omitted source or
assumption controls, the submitted conjecture, and a refutation's negated premise.

The [analysis contract](ontology-analysis.md) defines literal versus exact filters,
complete versus selected populations, paging fields and traversal outcomes.
OpenAPI is available at `/docs`. Invalid bounds produce HTTP 422 and unknown
terms produce HTTP 404. HTTP has no bootstrap, filesystem-write, proof-execution,
or upstream-publication endpoint. Source strings are rendered as text.

## MCP

Run `uv run --locked rikishi mcp` or `uv run --locked rikishi-mcp` in the
checkout. Configure a client's supported process environment and working directory.
`config/mcp.example.json` is an illustrative configuration: replace the
`${RIKISHI_ROOT}` placeholders with your actual path because not all MCP clients
expand environment variables in configuration values. Source `scripts/env.sh`
before launching a client to retain external cache bindings.

| Tool | Arguments | Result |
| --- | --- | --- |
| `corpus_stats` | None | Measured counts, source revision, parse errors |
| `corpus_analytics` | None | Complete composition, concentration, and unique-edge degree metrics |
| `corpus_files` | `path`, `sort`, `descending`, `limit`, `offset` | Paged file hashes, formula counts and complete/filtered totals |
| `formula_search` | `text`, `head`, `path`, `term`, `limit`, `offset` | Complete source formulas with line/hash identity |
| `relation_inventory` | None | All direct relation types and assertion/distinct-triple counts |
| `taxonomy_analysis` | `relation`, `path`, `limit`, `offset` | Endpoint-only structural diagnostics and paged node rows |
| `taxonomy_path` | `source`, `target`, `relation`, `path`, `max_depth`, `max_visited` | Found, exhausted, or budget-limited source path |
| `search_terms` | `query`, `limit` 1–200 | Term names and documentation preview |
| `inspect_term` | Exact `name` | Source-bound definition and formulas |
| `relation_graph` | Exact `name`, `limit` 1–500, optional `relation` | Asserted neighboring edges with complete totals and relation inventory |
| `inference_catalog` | None | Declared source-bound scenarios and their evidence scope |
| `inference_verify_report` | `report`, `sha256` | Read-only replay of an existing contained laboratory report against the supplied digest |
| `inference_inspect_case` | `report`, `sha256`, `case_id`, optional `prover="e"` | Verified case, submitted problem, native streams, command, and proof-step-checking boundary; no process execution |
| `bridge_catalog` | None | Shared finite witnesses, selected source scenarios, and declared scope; no native execution |
| `bridge_verify_report` | `report`, `sha256` | Strict read-only bridge replay using a required independently supplied digest and a contained relative report path |
| `bridge_inspect_case` | `report`, `sha256`, `case_id`, optional `prover="e"` | Verified case joined to shared rational/numerical inputs, selected source claims, retained Lean source/declarations, problem and native streams; `e` or `v`, no compiler or prover execution |
| `finite_free_energy` | `prior`, `likelihood`, `posterior` | Evidence, F, surprise, KL, residual |
| `finite_free_energy_log` | `log_prior`, `log_likelihood`, `posterior` | Log evidence/posterior, explicit linear underflow, F, KL and residual |

Resources: `sumo://corpus` and `rikishi://fep-example`. MCP startup performs no
download or index mutation. Tool failures remain protocol error results; stdout
is reserved for MCP frames. `tests/interfaces/test_mcp_transport.py` launches an
actual stdio client/server and checks initialization, results, and invalid requests.

The log tool accepts nonpositive finite log probabilities and null for exact zero
mass. Its output null evidence denotes positive mass below the linear float range;
null log-posterior atoms denote exact zeros. See [numerical contracts](fep.md) for
support, projection and finite-range rules. The CLI model reader rejects unknown
fields, Boolean probabilities and nonfinite JSON values without replacing them
with defaults.

`graph` and MCP `relation_graph` accept an optional exact relation filter. Graph
results include the complete incident relation inventory, `total_edges` after
filtering, `returned_edges`, and `truncated`; limits never masquerade as complete
neighborhoods. Unknown relation names yield an empty filtered graph.

`fep-verify` reads the recorded Git revision, checks dependency Git pins and tracked
source cleanliness, and runs the selected compiler outside the canonical checkout.
`RIKISHI_LEAN` overrides its default external compiler; `--timeout` is 1–600 seconds
per compiler process. The output directory must be new. A receipt records source,
compiler, imported artifacts, compiled modules, and the three declaration axiom
reports. Conservative fingerprints cover the complete compiled dependency caches
and compiler library before and after compilation, including transitive inputs.
Proof admission, cache drift, or an unapproved axiom fails verification. The command
refuses symlinked cache entries and output directories inside canonical inputs.
It does not translate a SUMO formula or certify the entire `fep_formal` catalogue.

## Exact finite channels and derived witness research

```python
from fractions import Fraction as F
from rikishi.finite_channels import FiniteChannel, apply_channel, exact_bayes, channel_information

channel = FiniteChannel("noisy-quarter", ((F(3, 4), F(1, 4)), (F(1, 4), F(3, 4))))
answer = exact_bayes((F(1, 2), F(1, 2)), (F(1, 4), F(3, 4)))
coarse = apply_channel(answer.posterior, channel)  # (3/8, 5/8), exactly
comparison = channel_information((F(1, 2), F(1, 2)), answer.posterior, channel)
```

`FiniteChannel(name, rows)` is frozen. Laws and rows must be nonempty immutable
tuples containing only exact `Fraction` entries in `[0,1]`; law and channel-row
sums must equal one exactly. Floats, Boolean values, strings, ragged matrices
and wrong dimensions reject with `FiniteChannelError`. Selected likelihood
entries need not sum across hidden states to one. `exact_bayes` returns frozen
`joint`, `evidence` and `posterior`; zero-evidence observations reject.

`relative_entropy(candidate, reference, *, precision=100)` returns Decimal nats.
Zero candidate terms contribute zero; positive candidate mass outside reference
support rejects. Precision is a strict integer from 40 through 200. Calculations
use an isolated Decimal context, guard digits and an explicit tolerance.
`channel_information` returns exact transformed laws, signed KL before/after,
loss, residual and tolerance. Residuals are never silently clamped. This is a
finite numerical comparison, not interval certification or a Lean theorem.

`build_witness_research(report, report_sha256)` consumes a report already obtained
through trusted bridge replay. It returns a frozen `WitnessResearch` with 12
channel rows, three likelihood scalings, three noisy-observation comparisons,
the biased-to-uniform Bayes factor and the equal-prior model posterior.
`verify_witness_research(raw, report, report_sha256)` purely reconstructs that
data. It does not authenticate historical native execution. The renderer
`render_witness_research(data, output)` refuses occupied output paths and exports
two 191.9 × 185 mm PNG/SVG pairs plus exact JSON, at 300 DPI for PNG.

`sequential_conditioning(prior, likelihood, steps)` returns exact rational
prefix evidence, posterior and next-observation probabilities from n=0. It
requires normalized Fraction laws, a Boolean-completable observation column,
a nonnegative integer step count and positive conditioning evidence. Direct
products and iterative Bayes must agree exactly. The hidden state persists;
this is not the independent-state redraw model.

`build_witness_dynamics(report, report_sha256)` returns frozen `WitnessDynamics`
for n=0..12 and 65,536 reproducible forward trajectories per witness. The export
records each simulation seed, generator, all-true prefix counts and false-state
counts, exact answers and equal-prior uniform/biased model weights. The caller
must supply a validated `BridgeReport`; the method does not authenticate native
execution. `verify_witness_dynamics(raw, report, report_sha256)` reconstructs all
exact and seeded fields. `dynamics_table(data)` produces the n=2 publication
table; `render_witness_dynamics(data, output)` creates the 191.9 × 205 mm
`witness-sequential` PNG/SVG pair and `witness-dynamics.json` without overwriting.
Simulation agreement is a synthetic numerical observation, not additional
Lean/SUMO or scientific acceptance.

### Mixed observations and model uncertainty

`witness_sequences.condition_sequence(prior, kernel, observations)` accepts an
exact `Fraction` law, a complete `FiniteChannel` with columns `(False, True)`,
and an immutable tuple of actual Boolean observations (at most 1,024). It
returns frozen prefix records including the joint, cumulative evidence,
posterior, observation probability and complete next-observation law. Direct
joint powers and iterative Bayes agree at every prefix. An impossible sequence
rejects; the empty sequence has evidence one. `redrawn_evidence` separately
records the model that redraws its state before each observation.

`SequenceModel(name, prior, kernel)` supplies a named model.
`compare_sequence_models(models, observations, *, model_prior=None)` normalizes
each model's evidence with its declared prior model probability. The default
is uniform over the supplied models. The result keeps model weights separate
from state posteriors and supplies the model-averaged next-observation law.
An impossible component has zero weight and no invented conditional law;
zero total evidence rejects. Inputs reject Boolean-as-number coercion, nonfinite
or inexact probability values and inconsistent dimensions.

`binomial_frequency_diagnostic(successes, trials, probability)` retains an exact
frequency, signed error and model-based variance `p(1-p)/N`. It assumes independent
Bernoulli trials; it is neither a confidence interval nor a pass/fail test or
empirical validation.

`witness_sequence_atlas.build_sequence_atlas(witnesses, report_sha256)` enumerates
all eight length-three histories for the three registered witnesses, with exact
state/evidence/predictive values and a separately declared equal-prior U/B
comparison. Its PNG/SVG/JSON export is create-only; verification reconstructs
all values from the source witnesses rather than accepting a rebound checksum.
The caller must obtain those witnesses from a trusted bridge report. The atlas
adds derived arithmetic, not new bridge declarations or native case outcomes.

Run the mixed-history example without a compiler, solver or canonical outputs:

```bash
uv run --locked --no-sync python examples/witness_sequences.py
```

For the history `(True, False)`, it reports evidence `3/16` and posterior
`(1/2,1/2)` for the uniform model, and evidence `5/24` and posterior
`(2/5,3/5)` for the biased model. Equal initial model weights update to
`(9/19,10/19)`, with mixture next-true probability `11/19`. The example prints
its exact priors and complete kernels alongside those answers.

### Finite event transport

`event_transport.FiniteStateMap(source, target, images)` validates explicit,
finite, named carriers and a total deterministic mapping. Its `direct_image`,
`inverse_image`, `pushforward`, `is_injective` and `is_surjective` operations
retain the carrier direction and exact probability order. Events must be
immutable subsets of their declared carrier; laws remain normalized exact
`Fraction` tuples. The [event contract](semantic-transport.md) separates the
executable checks and four local Lean statements from the still-open general
SUMO interpretation/preservation problem.

## One-step action planning

`rikishi.active_inference` is a pure finite decision module. It performs no file,
network, native-tool or environment execution. The [mathematical contract](active-inference.md)
defines the adopted outcome-preference functional and its scientific limits.

```python
Action(name: str, transition: FiniteChannel, observation: FiniteChannel)
score_action(belief: Law, action: Action, preferences: Law, *, precision: int = 80) -> ActionScore
plan_actions(belief: Law, actions: tuple[Action, ...], preferences: Law, *,
             precision: int = 80) -> ActionPlan
condition_action(belief: Law, action: Action, observation: int) -> BayesResult
demo() -> dict[str, object]
```

`Law` is an immutable nonempty tuple of exact `Fraction` values, normalized to
one. `Action` is a frozen record: its transition maps current states to next
states, and its observation channel maps next states to outcomes. Both channels
are row-stochastic `FiniteChannel` values. Every action in a plan must accept
the current belief and produce the same outcome alphabet as `preferences`.
The caller is responsible for the shared meanings of those coordinates.
Preferences must be strictly positive, including at unreachable outcomes.

`ActionScore` is frozen and records `name`, exact `predicted` next-state and
`outcomes` laws; Decimal `risk`, `ambiguity`, `expected_surprisal`,
`information_gain`, `expected_free_energy`, `decomposition_residual`, `tolerance`;
and integer `precision`. Scores use natural-log units, 40–200 digits (default
80), and an isolated context with 20 guard digits. `ActionPlan` records `scores`,
`minimizers` and `precision`. All actions within the larger of their own and the
best score's tolerance are retained, in input order. No tie-break is applied.

`condition_action` advances through the transition and then conditions on an
actually supplied integer outcome index; Boolean indices and impossible
observations reject. Its `BayesResult` contains exact `joint`, `evidence` and
`posterior` for that next-state observation. Hypothetical outcomes considered
during scoring never change the current belief.

Dimension, normalization, support, type, precision and decomposition failures
raise `FiniteChannelError` (a `ValueError`). The CLI adapter `active-demo` returns
complete synthetic inputs and outputs as JSON; probabilities and Decimal
quantities are strings preserving their representation. There is no HTTP/MCP
planner endpoint. Existing FEP transport behavior and registered campaign
schemas retain their original meaning.

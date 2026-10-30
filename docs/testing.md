# Test suites and quality gates

Run from the checkout with `source scripts/env.sh` and `uv sync --locked`.
All test temporaries use the external `TMPDIR`. The session-level `project_root`
fixture locates source independently of test nesting. The shared `git_commit`
fixture creates real commits with repository-local identity and disables inherited
filesystem monitors only in its temporary repositories. A real monitor-hook
calibration checks this isolation while retaining commit and dirty-file checks;
it does not establish the cause of a historical interrupted Git invocation. `corpus_factory`
creates actual Standard Upper Ontology Knowledge Interchange Format (SUO-KIF)
files and SQLite indexes. No mocking framework is used.

The full native gate also requires a real Chromium executable. Set
`RIKISHI_CHROMIUM` to the installed Chrome/Chromium executable before `make check`;
the typography tests invoke that exact file in a private headless profile and
reject a missing setting. For example, select an executable with
`export RIKISHI_CHROMIUM="$(command -v chromium)"` on a system that provides
`chromium`, then invoke it with `"$RIKISHI_CHROMIUM" --version` to verify it works.
Use the actual application executable on macOS. These tests are integration
cases and are excluded by `make portable`; a source-only pass does not establish
browser behavior. Give concurrent pytest runs distinct external `--basetemp`
directories so their retention cleanup cannot interfere.

| Suite | Behavior exercised |
| --- | --- |
| `tests/unit/` | Parsing, finite arithmetic, indexing, source audit, coverage-gate rejection |
| `tests/inference/` | Projection manifests, registered source-bound E and Vampire (E/V) cases, shared-witness Lean/numerical/native obligations, background/countermodel/removal/refutation controls, and replay mutation rejection |
| `tests/interfaces/` | Command-line interface (CLI) dispatch, subprocess entrypoint, real Model Context Protocol (MCP) standard input/output protocol |
| `tests/dashboard/` | Hypertext Transfer Protocol (HTTP) contracts, exact analytics, source-backed report artifacts |
| `tests/runtime/` | Acquisition preservation, strict automated theorem proving (ATP) results, native tools and adapters |
| `tests/manuscript/` | Real Git snapshots, hydration, artifact integrity, native render/verify |

Prepare the two public source inputs before tests which inspect the packaged
alignment study. Acquisition uses the exact Suggested Upper Merged Ontology
(SUMO) revision and workbook Secure Hash Algorithm 256-bit (SHA-256)
digests in `src/rikishi/data/alignment-study-v1.json`:

```bash
mkdir -p .rikishi/portable-inputs
uv run --locked --no-sync python scripts/prepare_portable_inputs.py \
  --output .rikishi/portable-inputs/default
export RIKISHI_PORTABLE_INPUTS=.rikishi/portable-inputs/default
```

The output directory must be new. An explicit `--reuse` revalidates an existing
receipt, both complete source files and the recomputed report without downloading
replacement bytes. Tampered or incomplete inputs fail; there is no historical
output fallback. The shared fixture requires `RIKISHI_PORTABLE_INPUTS`; relative
paths are resolved from the checkout. `make test` and `make portable` run the same
setup with verified reuse. Override their destination with
`PORTABLE_INPUTS=NEW_DIRECTORY` when a separate acquisition is needed.

A portable receipt binds the complete alignment-authority digest, including its
dependency pins. After an authority revision, use a new destination; do not edit
the old receipt or silently fall back to it. The release-authority regressions in
`tests/unit/test_version_metadata.py` compare both packaged studies with actual
checkout lock bytes and reject a real tampered temporary lock before output or
native execution. Run these portable preflights before an expensive native gate;
they do not replace its actual campaigns or complete coverage requirements.

[`portable_inputs.py`](../src/rikishi/portable_inputs.py) implements acquisition
and verification; the [script](../scripts/prepare_portable_inputs.py) is its thin
entrypoint. Requests have bounded time and response sizes. Network errors, partial
transfers, wrong hashes and occupied destinations fail explicitly. Source bytes
and a receipt are retained in the selected directory. They are not package data.
The report preserves the study's logical source path and pinned revision; its
`clean=null` records that acquisition observed no local Git checkout. It rederives
source formulas and workbook cells, not a fresh index audit or ATP result.

SUMO's pinned source carries its Institute of Electrical and Electronics Engineers
(IEEE) notice, and the version-specific
[workbook record](https://zenodo.org/records/11463326) identifies Creative Commons Attribution 4.0.
Keep source/version attribution when using those inputs; they are not relicensed
as Rikishi MIT data. Downloaded inputs, native archives and research results must
not be added to the source distribution merely to make tests pass.

Portable selector:

```bash
RIKISHI_PORTABLE_INPUTS=.rikishi/portable-inputs/default \
  uv run pytest -c pyproject.toml -m 'not integration'
uv run ruff check src tests scripts
uv run basedpyright
uv build
```

The selector is evaluated after
[`tests/fixtures/prerequisites.py`](../tests/fixtures/prerequisites.py) classifies
resolved fixture dependencies. Every direct or transitive `bridge_packet`
consumer requires either a native Lean/E/V campaign or an authenticated retained
packet. Module-scoped cache, native-manuscript and Pandoc package fixtures are
classified by both path and fixture name, so unrelated fixtures with names such
as `packet` or `package` remain portable. Exact direct Pandoc/JavaScript cases
are classified individually; their pure siblings remain selected.

The hook adds `integration` before pytest applies `-m`; it never drops tests or
skips missing prerequisites. The unfiltered full gate retains every assertion,
including all saved-cache replay, native-packet, installed-tool and live
snapshot-custody cases. Explicitly selecting one of those cases without its
prerequisites still fails. The source-only bridge compilation tests consume the
verified public `Merge.kif` bytes from `portable_inputs`, with the same complete
digest and formula checks used for the installed copy.

Real isolated pytest controls exercise direct/transitive prerequisite selection,
same-name fixtures in unrelated modules, exact parameterized installed-tool
cases, full-gate failure on absent prerequisites, and a deliberately disabled
classifier. Portable and integration collections must partition the full node
inventory. Local selector qualification is distinct from an actual hosted Linux
run; hosted execution must be recorded separately.

Offline cache replay uses Python files/ZIPs and treats recorded absolute paths,
including a Darwin Java virtual machine (JVM) library identity, as lexical data. It does not need a live
JVM. Its packet must satisfy the unchanged packaged authority and all source,
archive, process-record, input and observation checks. No approved distributable
packet web address or transport contract is supplied here. The local
`RIKISHI_CACHE_REPLAY_PACKET` override supplies the 33 replay cases only; the seven
wrapper cases retain their `output/research/fresh-cache` prerequisite.

The supported fresh producer is:

```bash
uv run --locked --no-sync rikishi cache-diagnostic \
  NEW_REPOSITORY_LOCAL_DIRECTORY --timeout 60
```

Its parent must exist and its destination must be new. Production requires the
installed pinned SUMO/Sigma/dependency authority, mounted GitVault storage,
external Python and Java runtimes, Sigma configuration and the actual JVM library
expected by the current producer. Success requires five observed cases, stable
bindings and `semantic_validation=false`; exit status alone is insufficient.
The live snapshot test also compares retained bytes to the installed originals.
A downloaded packet cannot replace that comparison. A supported hosted-Linux
producer or approved authentic packet acquisition remains a separate requirement.

The `integration` marker also declares other installed-tool and canonical
renderer cases. Classification changes no expected scientific outcome or
assertion. Missing prerequisites cause failures when such a test is selected.

The two required-field receipt-schema tests use a positively validated synthetic
value with no editions or artifacts. That fixture is supplied directly in memory
and never written to canonical manuscript output or accepted as rendered evidence.

Full workstation gate (the same explicit public-input environment is required
when invoking pytest directly):

Stop a running Sigma web server before this gate or before repeating bootstrap,
and wait for its tracked `run` process to exit:

```bash
uv run --locked --no-sync python scripts/runtime-sigma.py stop
```

The bootstrap test rebuilds the deployed web application. A live Tomcat server
automatically reloads that build and regenerates profile caches and translations.
A query overlapping that reload is correctly rejected by the source-profile
freshness guard. Keep the web server stopped throughout the native gate; do not
relax that guard or accept the overlapping query's prover status as verified.
The installed-query tests also distinguish native resource limits from an
explicit prover wall allowance. The native E `ResourceOut` control retains its
five-second processor-time limit and requires completed exit 8 before any
status/custody mutations use its packet. Its separate wall allowance is 300
seconds. A wall-killed process cannot qualify that fixture. The full-profile
positive E regression uses an explicit 60-second native limit; the Vampire
positive and negative controls retain their five-second native limits and the
negative control must still be an inconclusive native timeout. These invocations
record their exact budget documents and provenance. A retained timeout remains
inconclusive; a separate longer invocation may produce a theorem only through
its own completed native execution and separately retained evidence.
After the gate, restore the supported `scripts/runtime-sigma.py run` lifecycle in
its own terminal or tracked job, wait for initialization to complete, and check
`scripts/runtime-sigma.py status` from another terminal. See [runtime](runtime.md).

```bash
uv run pytest --cov=rikishi --cov-report=term-missing \
  --cov-report=json:output/coverage.json --junitxml=output/tests.xml
uv run python scripts/check_coverage.py --output output/coverage-gates.json
uv run ruff check src tests scripts
uv run basedpyright
uv build
```

The second command is mandatory. It sums covered executable lines and covered
branch destinations, divided by executable lines plus branch destinations, for
two disjoint scopes. Core code must reach 90%; native setup, server/query
orchestration, and rendering infrastructure must reach 60%. Exact infrastructure
paths are versioned in `config/coverage.toml`. All other package Python files
enter the core scope automatically. The general report's 60% floor is a coarse
guard only. No package source file may be omitted or have excluded lines.

Coverage-gate tests deliberately reduce each scope below its floor, omit source
files, inject excluded lines, supply impossible counts, and corrupt policy paths.
These must fail. Probability tests compare independent logarithmic values;
inference tests require both theorem and countermodel outcomes; runtime tests
reject log-echo spoofing, stale invocation identifiers, malformed sidecars, and
unsuccessful ATP exits. Renderer tests alter real source/artifact bytes and
require rejection. Passing a positive fixture alone is insufficient evidence.

The [source-bound inference laboratory](inference-tutorial.md) derives its native
case population from the registered catalog and selected prover families; read
the actual run total and statuses from the fresh report. Its
[method contract](inference-methods.md) separates background satisfiability,
positive entailment, deliberately unsupported queries, premise removal, and
explicit refutation. Retained-artifact mutations must fail portable replay.
Catalog-derived expected outcomes are not substitutes for native observations,
and a copied or rehashed report does not authenticate historical execution.

The full native suite regenerates manuscript artifacts. Retain
`output/manuscript/render-receipt.json` with the matching visual inspection.
The GitVault repository-operation lease serializes shared workstation gates and
publication; it is a workstation coordination mechanism, not a package dependency.

`make check` prepares/reverifies the public inputs and runs the full sequence above.
Both coverage floors and every native/manuscript assertion remain mandatory.
Static checking covers all package
modules in standard mode, with strict checking for finite arithmetic, SUO-KIF
parsing, and coverage accounting. The pinned native-renderer stubs describe
only the pinned adapter methods Rikishi actually calls; they do not implement a
renderer. The native integration test exercises those methods against the verified
canonical archive. A real type-checker negative control changes a correct integer
assignment to a string and requires an assignment diagnostic.

Finite Lean integration tests compile the pinned modules and inspect their axiom
reports. Real incorrect proofs, admitted proofs, toolchain drift, dependency drift,
and occupied output directories must fail. The accepted run's receipt is
`output/formalization/verification.json`; it identifies the isolated workspace,
compiler, source Git objects, imported artifacts, and commands. No test writes to
the canonical formalization checkout. Isolated module verification alone does
not establish the shared-witness bridge; that study adds the obligations below.

## Fresh native-test workspaces

The session-scoped `native_workspace` fixture creates a new directory under
`.rikishi/native-tests-<unique-id>/` after checking its existing parent for
symbolic paths. Native alignment, CLI, publication-pair, research-figure,
direct prover-family, core-query and fresh-cache controls retain their outputs
there. Shared-witness production uses
the same session workspace. These fixtures do not recreate dated development
directories or require an old campaign to exist.

Alignment and research-figure producers explicitly consume the workbook from
the revalidated `portable_inputs` bundle. This changes its acquisition location,
not its pinned bytes, worksheet/cell interpretation, study authority, numerical
tolerances or expected native polarities. The source report is still generated
through the live audited source method. Fresh workspace allocation does not
replace native execution or make a saved packet authentic.

## One-step action-planning controls

`tests/unit/test_active_inference.py` and
`tests/interfaces/test_active_inference_cli.py` exercise the separate finite
planner without native prerequisites. Exact-channel examples distinguish state
information from equal outcome marginals, reverse choices under changed
preferences, apply action-dependent transitions before conditioning, and retain
numerical ties. An independent joint-sum expression checks the objective;
support, dimension, invalid-type, impossible-observation and caller-context
controls test the mathematical boundary. The actual module subprocess command
requires no index or native tools. A deliberately corrupted objective must fail
its decomposition check; preserve that failure with the positive observations.
These checks establish neither a Lean proof nor empirical action performance.

## Shared finite-witness bridge controls

The [bridge method contract](bridge-methods.md) adds a packet separate from
isolated finite-module compilation and the earlier alignment campaign. Its
registered rational Boolean witnesses use the same prior, complete observation
kernel, candidate and entity identifiers across numerical, Lean and selected
SUMO problems. State arrays are ordered false, true; observing `true` selects an
observation column rather than changing that hidden-state order.

The bridge controls have distinct acceptance obligations:

| Layer | Required checks and failure evidence |
| --- | --- |
| Study and source | Match the packaged study, exact rational inputs, complete pinned formulas and local assumptions; reject source, study or generated-problem mutations. |
| Numerical | Recompute exact rational posterior and independent 80-digit Decimal comparisons, normalization, support and decomposition residuals; retain tolerances with observations. |
| Lean | Elaborate the actual witness laws and theorem instantiations against pinned source/dependencies; reject invalid normalization, wrong posterior proofs and admitted proofs. Declaration inventories include definitions as well as theorems. |
| Native ontology | Retain the satisfiable-background, positive, unsupported-query, premise-removal and explicit-refutation problems for each selected family. Generated cases alone establish no observed outcome. |
| Replay and custody | Require an independently supplied outer digest and retained packet inputs. Reject changed source, numerical values, proof evidence, captures and implementation bindings. Hashing a received packet does not establish trust in its producer. |
| Publication and figures | Derive counts, status categories and plots from the verified report; bind the canonical and staged packet to the same external digest; reject stale or altered inputs rather than substituting an older report. |

The implementation's controls are in `tests/inference/test_bridge_*.py` and
`tests/manuscript/test_bridge_figures.py`. Read actual observations from the new
`output/bridge/bridge-report.json`, not a generated population or a historical
acceptance receipt. The native campaign, isolated Lean elaboration, numerical
agreement and full gate remain distinct results. A matched finite witness does
not establish a general SUMO-to-Lean preservation theorem or an empirical
Free Energy Principle (FEP) result.

The manuscript recipe in [manuscript.md](manuscript.md) generates a fresh bridge
before rendering, retains its digest as `BRIDGE_REPORT_SHA256`, binds
`BRIDGE_SHA256` once with `readonly`, and uses that unchanged alias for source
and staged `bridge-verify` calls. The independent inference `REPORT_SHA256` alias
keeps its original role. Workflow regressions must check both ordered paths and
reject a missing campaign, missing staged verification, mutable alias or changed
digest. This is the intended regression contract, not a report that such a test
or a new native campaign passed during documentation editing.

Publication layout controls examine the actual Portable Document Format (PDF)
and Hypertext Markup Language (HTML) editions: the current configuration uses
12 mm desktop margins/padding, full usable prose width and 17 px HTML body text.
At browser widths of 600 pixels or below, HTML padding is the smaller of the
configured margin and four percent of viewport width, and code text has a 15 px
minimum. Publication prose has no additional fixed-width or character-count cap.
Check
paragraphs, lists, tables and references after wide elements; inspect all native
figures and their web copies. A source-style assertion is distinct from rendered
geometry or human visual inspection. Preserve the workstation quiescence and
full-gate requirements above when running these native controls.

## Word reference and geometry controls

The complete native manuscript integration uses the actual
`scripts/render_manuscript.py` entrypoint in a separate production process.
Only `PYTEST_CURRENT_TEST` is excluded from its copied child environment: this
prevents the pinned renderer's eight-second smoke-test deadline from replacing
its normal production Pandoc deadline of 600 seconds. The parent test environment
and pinned renderer bytes remain unchanged. A separate 1800-second caller wall
limit bounds the process group; actual failure or timeout fails the fixture and
retains the invocation, timing and raw output. There are no automatic retries.
The shared fixture supplies freshly produced editions to dependent controls.

Native mutation fixtures copy those closed, regular-file inputs with create-only
APFS `clonefile` calls on macOS, using NOFOLLOW and NOFOLLOW_ANY. A requested clone
failure propagates its errno; there is no ordinary-copy fallback. Other platforms
explicitly use an ordinary create-only copy. Both methods preserve file mode and
nanosecond modification time, require distinct single-link inodes, and reject
symbolic inputs or existing destinations. The separately created formal-library
link keeps its original role and is not traversed by this copier. Real-file
controls check both-direction write isolation, metadata, occupied destinations
and symbolic paths. This reduces duplicated fixture storage; it does not establish
a PDF timeout cause, cure, native-pass result or cross-platform qualification.
Coverage's supported `patch = ["subprocess"]` traces the real child and pytest-cov
combines its data. The same branch floors, source and artifact checks, actual
pixel comparisons and rejecting controls remain mandatory. An isolated branch
probe must detect missing child coverage when this tracing is omitted; successful
subprocess exit alone is not coverage evidence.

`publication_office` supplies the bounded reference-generation and actual-package
geometry checks used by the renderer and final verifier, plus a pure byte
reference-policy check. Its control file is
`tests/manuscript/test_office_layout.py`; reading or passing a source-only check
does not establish that its native cases ran.

| Check | Required failure or acceptance boundary |
| --- | --- |
| Actual section geometry | Reject missing or duplicate page-size/margin elements, wrong edges or paper size, landscape orientation, nonzero gutter, invalid header/footer distances, multiple columns and malformed section placement/order. Recomputed hashes do not waive these conditions. |
| Package boundary | Reject unsafe or duplicate ZIP members, symlink paths, corrupt or oversized archives and unsafe Extensible Markup Language (XML). |
| Reference preservation | Retain the exact Pandoc native-default archive. Require only `w:pgSz`/`w:pgMar` insertions in `word/document.xml`, the explicit `Hyperlink` color atom and `ImageCaption` keep-lines insertion in `word/styles.xml`, and exact remaining XML/style/member bytes. Preserve inventory/order, archive comment and public member metadata; sizes/checksums/offsets derive from changed payloads. |
| Reference recomputation | `verify_office_reference_policy` must reconstruct the approved reference from the exact retained default and require whole-archive equality. Reject rehashed wrong colors/theme selectors, missing/disabled caption or native figure linkage, unrelated style/font/header/media changes, wrong geometry, changed ZIP metadata and unbound/ambiguous/unsupported native style targets. |
| Digital text and figure-caption policy | Require explicit `Hyperlink` color `#005EA8` without `themeColor`/`themeTint`/`themeShade` on that atom; fallback-only changes cannot waive theme precedence. Insert only `ImageCaption` `w:pPr/w:keepLines`; require and preserve native `CaptionedFigure` enabled `w:keepNext` and caption base `Caption`. Ordinary digital document text requires at least 4.5:1 contrast; measure actual LibreOffice output and inspect the complete figure-caption unit at neighboring page boundaries. |
| Final Word artifact | Independently read every section's geometry from the actual exported `.docx` and compare it with the receipt; do not infer propagation merely because a reference file was created. |
| Custody | Bind both retained reference hashes, Pandoc identity and reference/final geometry in `render-receipt.json` under `office_reference`. A fresh native-default export is not a byte-identity oracle because its outer ZIP timestamps may differ. |
| Pagination and appearance | Require separate office rendering and actual page inspection. XML, hashes, geometry and executable discovery cannot supply this evidence. |

The current 12 mm policy rounds half-up to 680 twips; portrait Letter is
12240 × 15840 twips (215.9 × 279.4 mm). Those are geometry expectations, not a
page-count result. Preserve the exact default archive used in a run alongside
its generated reference and final output. Every changed source or edition needs
matching reference-policy controls, the applicable gate, artifact checks and
independent LibreOffice contrast/pagination review. Completed observations for
the [latest sealed build](current-state.md) do not transfer to later changes.
Writer/page-verifier signatures, frozen records, table-row projection and
complete math inventory retain their documented contracts. See
[manuscript methods](manuscript.md#explicit-word-geometry-and-retained-reference)
and [verification status](verification.md#word-geometry-and-pagination-status).

## Final Word content and bounded math controls

`publication_office_content` receives bytes only; it does not launch a renderer
or proof process. Test its content projection separately from reference geometry
and separately from an office-rendered visual review. Retain the exact native
renderer file, projected final file and both receipt records with any regression
evidence; a newly generated native package cannot stand in for that input.

| Check | Required failure or acceptance boundary |
| --- | --- |
| Row projection | Insert enabled `w:cantSplit` only where absent in supported ordinary rows; retain an existing valid enabled property and repeated headers. Reject an explicit disabled property, malformed/duplicate/out-of-order row properties, unsupported serialization, nested tables, merged cells and drawings in rows. |
| Content custody | Independently reconstruct the projection from `output/manuscript/rikishi-native.docx` and compare the actual `output/docx/rikishi.docx`. Reject any other document XML change, changed non-target ZIP payload, member inventory/order, checked member metadata or archive comment; rebinding hashes cannot waive these conditions. |
| Receipt | Compare recomputed package/document hashes, actual table/row/enabled-header counts and zero-based row-change hashes with `office_content`; no fixed count is a substitute for inspection. |
| Math serialization | Require the supported complete manuscript math sequence, including the five named gathered displays, their operators/scripts/bounds/full expression envelopes, and the distinct atomic `T⊭q` and `T⊨¬q` expressions. Changed structures, literal alignment markers, combining negation or a changed relation pair must reject. Producer and verifier must compare the returned matrix inventory length with the canonical hydrated body's gathered count and compare the recomputed report with `office_math`. An isolated fixture cannot substitute for the complete body. |
| Scope and visual review | These checks prove neither arbitrary mathematical equivalence nor correct page placement. Render and inspect the exact projected final file, including complete rows, repeated headers and every affected display. Preserve the shared canonical source for all editions. |

Integration must check the actual methods with real rejecting inputs and retain
their results; static documentation checks supply no such execution evidence.
Render and visually review the exact final artifact after any content or layout
repair, preserving failed candidates without crediting them as accepted outputs.
Source-bound code review, native checks and visual review have separate evidence
records. See the
[content contract](manuscript.md#final-word-content-projection-and-math-checks)
and [prioritized TODO](TODO.md) for the remaining scopes.

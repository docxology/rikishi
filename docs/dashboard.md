# Ontology workbench

This workbench inspects the Suggested Upper Merged Ontology (SUMO), its Standard
Upper Ontology Knowledge Interchange Format (SUO-KIF) source, and retained automated
theorem proving (ATP) evidence. The command-line interface (CLI), Model Context
Protocol (MCP) tools, and Hypertext Transfer Protocol (HTTP) service share methods.

Run `uv run rikishi dashboard` after building the ontology index. The default server binds
to loopback. The dashboard reads the same SQLite index used by the CLI and MCP.
It does not download, edit, or infer ontology assertions through HTTP.

Search a term name, select a result, then follow a graph node.
Each term shows its documentation, a bounded direct-relationship neighborhood,
and source formulas with relative file paths and starting line numbers. The
accessible relationship list provides the same navigation without interpreting
the graph. Source formulas expand with native keyboard-operable disclosure controls.

The directed diagram shows one asserted subject–relation–object triple per row,
with native keyboard-operable endpoint buttons and eight edges per page. Choose
a relation type and an edge budget of 20, 40 (default), or 100. Filtering happens
before the budget is applied. Counts disclose matching, loaded, and omitted edges,
plus the total across all relation types; paging the loaded set does not fetch the
omitted edges. The full loaded set also appears in a disclosure list. Triples are
deduplicated and ordered by relation, subject, then object. This is not an inferred closure.
Search results are capped at 30. Missing terms and HTTP failures have explicit
visible states. Concurrent navigation discards stale responses.

## Corpus workspace

`/#corpus` opens the corpus workspace. The compact, sticky navigation links to
corpus sections, term relationships, and finite inference. Every fresh page uses
a white light theme, including when the system prefers dark. Dark appearance is
an explicit, session-only choice through the theme button.

File bars and formula-head rows open **Indexed evidence** with an exact file or
head filter. The formula table queries the complete index before pagination;
it is ordered by source path, starting line, and formula ID. Formula text matches
a literal, case-sensitive substring. Head, file, and indexed-symbol filters match
exactly. Symbol matching uses the occurrence inventory, including nested symbol
occurrences. Blank fields mean all. Whitespace-only fields are rejected.

The source-file dataset supports a literal, case-sensitive filename substring,
filename or formula-count sorting, and ascending/descending order before paging.
Its rows include source file Secure Hash Algorithm 256-bit (SHA-256) hashes and
formula counts. Select a file to
open its formulas. Both datasets show unfiltered and matching populations,
returned rows, and whether matching rows remain outside the current page.
Paging reaches the full matching population; no top-N subset is presented as complete.

Select a formula's file/line action to inspect the exact indexed SUO-KIF text, source
path, starting line, formula ID, indexed file hash, and source revision. A pinned
upstream source link appears only when the index records a clean source and a
40-character commit. The hash/revision describe the source at index build time;
the browser does not assert that current upstream or local files remain identical.
The source notebook's initial excerpts remain bounded; **Browse all formula
references** opens a complete paged query for the selected symbol.

Native checkboxes select rows on the displayed page. Copy and export produce
JavaScript Object Notation (JSON) containing only those checked records, their applied query, page and full
population counts, scope, and index provenance. Changing the query or page clears
selection. Clipboard denial exposes a selected text area for keyboard copying.
The downloaded filename identifies the selected dataset; exported text and hashes
remain exact. Empty results and HTTP errors clear stale rows; failed queries offer
a retry action and disable paging/export.

The complete relation inventory can be filtered, ordered by name or distinct
edge count, and paged. Each row distinguishes source assertions, distinct labeled
directed triples, repeated assertions, and endpoint symbols. A relation opens
top-level formula evidence by head; this formula population may include formulas
that do not satisfy the atomic binary-triple extraction rule.

Taxonomy diagnostics operate only on `subclass` or `subrelation` child-to-parent
edges, optionally restricted to an exact source file. Their symbol population is
the selected relation's endpoints. They report roots (zero asserted parents),
multiple parents, weak components, directed cyclic components, symbols in cycles,
and self-loops. Node rows page independently of the full graph counts. Component
evidence states when its member/component lists are truncated. Selecting a symbol
opens its term workspace with keyboard focus on the term heading.

Shortest-path queries report `found`, exhaustive `not_found`, `max_depth`, or
`max_visited`. Budget exhaustion never establishes path absence. Every returned
edge links to an exact source formula. A zero-edge path is possible when source
and target are the same indexed symbol. These diagnostics describe direct source
structure and do not establish logical consistency, entailment, or inferred closure.

Controls have native labels and at least 44px targets. Query/source navigation
hands focus to a heading; statuses announce loading, populations, and errors.
Wide tables have labeled, keyboard-focusable scrolling regions rather than
overflowing the page. There is no decorative motion. The interface is verified
at phone and desktop widths against the running FastAPI service.

Metrics, the finite-model canvas, and the evidence table reserve their geometry
before application programming interface (API) responses arrive. Analytics has an initial semantic loading section.
Direct hash navigation keeps its destination aligned while ancestor data fills,
without moving focus. Wheel, keyboard, pointer/touch, or activation input stops
that initial preservation immediately; later responses do not restart it. Initial
preservation also ends once requests settle. A real delayed-response fixture
checks both anchors, unchanged reserved dimensions, and user interruption.

## Measurements

The overview counts indexed source files, top-level SUO-KIF formulas, terms, and
edge assertions. The file chart searches all indexed files, sorts by count or
filename, and shows 12 files per page. Its matching-file and formula populations
remain explicit, and the bar scale stays fixed when filtering or paging.
These counts are not counts of independent facts, consistency evidence, or
proved theorems. The source commit and parser errors are included in the JSON
measurements and portable report.

Export a portable report and manuscript figures:

```sh
uv run python scripts/build_dashboard.py --index .rikishi/ontology.sqlite --output output/web
```

Outputs are `dashboard.html` (embedded Cascading Style Sheets (CSS) and measured JSON, offline filtering
and theme switching), `corpus.json`, `corpus-files.svg`, and `corpus-files.png`.
The page uses Hypertext Markup Language (HTML); charts use Scalable Vector Graphics
(SVG) and Portable Network Graphics (PNG). Additional outputs are `analytics.json`, `measurements.md`, and
`corpus-composition.svg` / `.png`. The report implementation lives in
`rikishi.reports`; the FastAPI module only adapts requests.
Both live and offline reports show formula-head composition, file concentration,
and the complete population of symbols grouped by direct-edge degree. Read
[measurement definitions](metrics.md) for denominators, duplicates, self-loops,
empty populations, and interpretation limits.
The portable report embeds every indexed file count and complete analytics record;
its file/head filters and degree-detail controls work offline. Live term search
requires the server. It loads no content delivery network resources. Its JSON escapes less-than
characters so corpus metadata cannot terminate the embedded data element.
Template expansion is one pass, preserving placeholder-like text in source labels.
Theme controls start light, with an explicit dark override for the current page.

## HTTP API

The application programming interface (API) is read-only.

| Route | Behavior |
| --- | --- |
| `GET /api/stats` | Corpus counts, per-file counts, provenance, parse errors |
| `GET /api/analytics` | Exact formula-head composition, concentration and degree distribution |
| `GET /api/corpus/files?path=Merge&sort=formulas&descending=true&limit=50&offset=0` | Complete file page; literal path substring; order `path` or `formulas`; matching/unfiltered file and formula totals, hashes, provenance |
| `GET /api/corpus/formulas?text=Human&head=subclass&path=Merge.kif&term=Human&limit=50&offset=0` | Complete formula page; literal case-sensitive text, exact head/path/term, fixed path/line/ID order, source hashes |
| `GET /api/corpus/relations` | Complete atomic binary relation inventory with assertions, distinct edges, repeated assertions, endpoint counts |
| `GET /api/taxonomy?relation=subclass&path=Merge.kif&limit=50&offset=0` | Endpoint node page and full selected direct-graph diagnostics; relation `subclass` or `subrelation`; exact optional source path |
| `GET /api/taxonomy/path?source=Human&target=Entity&relation=subclass&max_depth=20&max_visited=10000` | One shortest direct source-backed path, exhaustive absence, or explicit depth/visited budget exhaustion; optional exact `path` |
| `GET /api/search?q=Agent&limit=30` | Search results; limit 1–100 |
| `GET /api/terms/Agent` | Documentation, source formulas, parents, children |
| `GET /api/graph?term=Agent&limit=40&relation=subclass` | Distinct incident triples; optional relation filter before limit 1–100; matching/returned/truncated counts and complete relation inventory |
| `GET /api/fep?q=0.8` | Finite example with candidate belief q in [0,1] |
| `GET /api/inference/catalog` | Source-bound laboratory scenarios and controls without running a prover |
| `GET /api/inference/published` | Local report descriptor, validated report, and local-digest authority boundary |
| `GET /api/inference/report?report=output/inference/inference-report.json&sha256=DIGEST` | Read-only replay with a separately supplied report digest; missing report 404, failed validation 422 |
| `GET /api/inference/case?report=RELATIVE&sha256=DIGEST&case_id=REGISTERED_CASE_ID&prover=e` | Exact verified problem, native output, and command for one registered case; `e` or `v`, no execution |
| `GET /api/bridge/catalog` | Declared shared rational witnesses and selected SUMO scenarios; no native execution |
| `GET /api/bridge/report?report=output/bridge/bridge-report.json&sha256=DIGEST` | Strict read-only bridge packet replay against the independently supplied digest |
| `GET /api/bridge/case?report=RELATIVE&sha256=DIGEST&case_id=ID&prover=e` | Verified native case joined to its shared rational/numerical witness, selected source claims and retained Lean source; `e` or `v`, default `e` |
| `GET /docs` | Generated OpenAPI documentation |

Unknown terms return HTTP 404. Invalid limits and empty queries return HTTP 422.
An unknown nonempty relation returns zero edges and the selected center node,
with the unfiltered relation inventory retained. Empty and whitespace-only relation
filters return HTTP 422.
Missing database files prevent startup. Tests use real indexed Knowledge Interchange Format (KIF) files and
FastAPI's HTTP client; no mocked ontology responses are used.
Corpus/taxonomy pages accept `limit` 1–500 and `offset` 0–1,000,000. Query text
allows at most 2,048 characters and excludes NUL and whitespace-only supplied
values. Path depth is 0–100 and visited-symbol budget is 1–100,000. Invalid controls
return HTTP 422; missing path endpoints return HTTP 404. These routes adapt shared
`OntologyIndex` methods and query dataclasses; the dashboard contains no analysis Structured Query Language (SQL).

`uv run pytest tests/dashboard` checks real index/report generation, relation-filter
boundaries, hostile metadata and placeholder collisions. The native JavaScript
check invokes Node on every static and generated executable script and confirms
that invalid JavaScript fails. `tests/dashboard/browser_scenarios.js` provides
assertions for the real live or offline Document Object Model (DOM), without intercepted network responses.
`tests/dashboard/test_corpus_api.py` exercises complete paging, literal hostile
text, index immutability, source-backed paths, budget boundaries, and empty syntax
populations against real KIF files. The browser scenario additionally checks live
evidence tables, selection resets, exact source inspection, real HTTP 422 recovery,
file drill-down, taxonomy path states, focus handoff, and viewport overflow.
`tests/dashboard/browser_delayed_scenarios.mjs` uses a real fixture service with
delayed HTTP responses to check loading geometry, initial anchor visibility,
immediate user cancellation, and preservation of keyboard focus.

## Inference laboratory workspace

After a native run, retain its digest separately as `REPORT_SHA256`, then verify
and register the report:

```bash
uv run --locked --no-sync rikishi inference-verify output/inference/inference-report.json --sha256 "$REPORT_SHA256"
uv run --locked --no-sync rikishi inference-publish output/inference/inference-report.json --sha256 "$REPORT_SHA256"
```

Registration is required for the published-run view. It strictly replays the
report before atomically writing the local `output/inference/published.json`
descriptor, preserving any differing previous descriptor. It never invokes a
prover.

Open `/#proof-lab` to read the registered laboratory and its separately pinned
published report. The catalog describes intended experiments; the report records
one retained execution. A catalog entry alone is not evidence that a native run
has completed. The page's evidence scope must accompany any status copied into a
research note.

Click a scenario to inspect its registered case's actual submitted problem and
native proof output. The verified case view includes the native command and
standard output/error, with its proof-assurance boundary. Reading a prover's
proof text is distinct from independently checking each proof step. The published
report response includes `{descriptor: {report, sha256}, report, authority}`;
the authority text identifies the local digest's scope.

Use the [inference tutorial](inference-tutorial.md) to follow source formulas,
conjectures, controlled background variants, native captures, and portable replay.
Report verification requires a path and an independently supplied SHA-256 digest
(a Secure Hash Algorithm 256-bit content fingerprint). Changing the report or
losing one of its required retained inputs must fail replay. A digest embedded in
the report itself cannot supply independent trust in that report.

This workspace does not submit arbitrary ontology text to a prover. Execute a
new experiment through the CLI, preserve its complete directory, and then inspect
it through the read-only interface. Compare E and Vampire only when their retained
problem bytes match. Their agreement does not certify the source-to-target
interpretation; their disagreement must remain visible and unresolved until the
captured commands, inputs, statuses, and diagnostics explain it.

## Shared finite witness inspection

The bridge joins three strictly positive rational Boolean (`Bool`) witnesses
across Python arithmetic, concrete Lean instantiations, and selected SUMO role
scenarios. Each witness binds its prior, complete observation kernel, candidate,
observation `True`, and authored entity identifiers. Hidden-state tuples use
`(false, true)`: index 0 is `Bool.false` and index 1 is `Bool.true`. Observed `True`
is the observation value, not the first hidden state. Exact `Fraction` posteriors
and an independent 80-digit `Decimal` reference share those inputs with the Lean
instances at revision `9a0694f16b8e89b66b2f7f8cc7426c650dd2c4de`.

The canonical report is `output/bridge/bridge-report.json`. Inspect it through
the bridge HTTP routes above with its repository-relative path and independently
supplied SHA-256 digest. Paths cannot contain `..` or traverse symlinks; the
digest must be 64 lowercase hexadecimal characters. Missing reports or selected
cases return HTTP 404; invalid inputs or failed replay return HTTP 422. A case
view returns the retained problem, native command and standard output/error,
scenario, source claims, shared rational/numerical witness, and Lean source,
declaration names and source hash. For a Vampire-only report choose `prover=v`;
the default `e` selection does not substitute a missing run. These are read-only
inspection routes and run no compiler or prover.

For a fresh run you produced yourself, record its outer digest separately with
the producer's custody evidence. For a received packet, obtain that digest from
an independently trusted record or channel: hashing untrusted received bytes
does not establish producer custody. Retain the complete packet. The
[interface guide](API.md#finite-witness-bridge) gives the native production,
strict replay, case inspection, and figure export commands. Wait for the active
runtime owner to finish before scheduling new native work; preserve active jobs
and failed captures.

The declared figure export contains `bridge-evidence.png`,
`bridge-free-energy.png`, `bridge-native-controls.png`, their three `.svg`
counterparts, `bridge-explorer.html`, and `bridge-figure-inputs.json`. Figure
generation requires strict report replay and a fresh output directory with an
existing symlink-free parent on mounted GitVault. The offline explorer exposes
retained cases and Lean source alongside finite candidate exploration. Its
candidate coordinate is `q(false)=q0`, with `q(true)=1-q0`; moving it computes
numerical values without executing a new proof. A display of retained proof
output does not independently check its inference steps.

Open `GET /api/bridge/explorer?report=RELATIVE&sha256=DIGEST` for the verified
interactive view. It applies the same explicit report/digest selection as report
and case inspection, and performs no native execution.
The live dashboard retains its own text measure; manuscript HTML layout settings
do not describe the live workbench's width.

Catalog entries describe the design. Native counts, observed statuses, prover
families, Lean control rejection, and completion must come from the actual
retained report; no completed native pass is asserted here. Lean's declaration
inventory includes definitions as well as theorems. Portable replay performs no
new Lean checking, authenticates no historical process execution, and does not
retain/authenticate every external dependency artifact. Shared inputs and
separate obligations do not establish general SUMO-to-Lean semantic preservation.

## Finite inference explorer

The slider calls the shared `rikishi.fep.free_energy` implementation with prior
`[0.5, 0.5]` and observation likelihoods `[0.8, 0.2]`. It reports free energy,
surprisal, Kullback-Leibler (KL) divergence, and evidence, with the decomposition residual shown
explicitly. The minimum occurs at q=0.8. Values use natural logarithms (nats).
The example illustrates a finite identity; it does not claim SUMO entails the
Free Energy Principle (FEP) or that a numerical calculation verifies a Lean proof.

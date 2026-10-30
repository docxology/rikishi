# Architecture and method contracts

Rikishi is an operator package around the upstream Suggested Upper Merged Ontology
(SUMO), with independently reusable
source indexing, numerical examples, service interfaces, and manuscript rendering.
Its Standard Upper Ontology Knowledge Interchange Format (SUO-KIF) source remains
distinct from selected reasoning problems and their native evidence.
Figure formats are Portable Network Graphics (PNG) and Scalable Vector Graphics
(SVG); retained structured reports use JavaScript Object Notation (JSON).

| Layer | Input | Observable result | What it establishes |
| --- | --- | --- | --- |
| Upstream acquisition | pinned Git revision | local ontology files and revision receipt | source identity |
| SUO-KIF parsing/indexing | ontology files | expressions, terms, relationships, diagnostics | lexical and structural inventory |
| Reasoning runtime | explicit axioms and conjecture | prover status and retained stdout | the stated query under that runtime |
| Source-bound inference laboratory | registered source formulas, explicit assumptions and conjectures | native cases, controls and replay-checked captures | the declared selected kernels and observed outcomes |
| Dashboard and Model Context Protocol (MCP) | index and operator functions | Hypertext Transfer Protocol (HTTP) or MCP responses | interface behavior |
| Free Energy Principle (FEP) example | finite prior, likelihood, candidate | evidence, Kullback-Leibler (KL) divergence, objective, residual | finite numerical calculation |
| One-step action planning | belief, action-dependent transitions/observations, positive outcome preferences | exact predictions, numerical risk/ambiguity/information gain and all minimizing actions | the declared one-step decision functional, not an empirical agent or a formal proof |
| Finite alignment campaign | versioned study, pinned workbook/source, explicit first-order logic (FOL) kernel | logical polarities, Decimal comparisons, replayable captures | completion of the selected experiment |
| Shared finite witness bridge | rational Boolean inputs, pinned Lean modules, selected SUMO formulas and local assumptions | exact posterior, independent numerical reference, concrete Lean evidence and controlled native role scenarios | separately checked obligations bound to the same witness identifiers and inputs |
| Fresh cache diagnostic | pinned source fragment or complete Merge, installed Sigma | five isolated source-ingestion/cache-build controls | generated classifications under those inputs |
| Formal source inspection | committed Lean objects | declaration locations | source provenance only |
| Isolated finite elaboration | pinned Lean modules, compiler and dependency caches | compiled modules and declaration axiom reports | elaboration of the stated finite modules against recorded local inputs |
| Manuscript renderer | Markdown and generated figure | Portable Document Format (PDF), Word, Hypertext Markup Language (HTML), receipt | artifact production |

Indexing does not prove consistency. Term counts do not quantify truth. A graph
edge extracted from a sentence does not necessarily represent an unconditional
logical assertion: quantifiers, implications, negation, and higher-order context
matter. Preserve formula context when interpreting relationships.

The service should run on loopback for local research. MCP clients can invoke the
tools registered by the server; examine tool schemas before connecting an agent.
Treat ontology documentation and retrieved text as data, never as instructions.
Do not expose a local operator service to a public network without a separate
authentication, request-limiting, and threat-model review.

Keep upstream code, downloaded executables, generated indexes, reports, and build
outputs distinct. The ontology corpus retains its upstream license and provenance;
the operator's license does not replace upstream terms. Query results should identify
which installed revision supplied their source. A changed ontology revision requires
rebuilding the index and repeating reasoning checks.

## Importable methods and thin entrypoints

| Module | Interface and failure contract |
| --- | --- |
| `kif` | Parse complete source expressions with file/line attribution; reject malformed syntax |
| `ontology` | Atomically replace a complete SQLite index; never publish partially parsed bad files |
| `source_audit` | Compare recorded source hashes and revision with disk without changing the index |
| `sumo_demonstrations` | Audit and freeze selected SUMO examples; replay exact source bytes and formula locations portably; optional proof delegates to the existing restricted taxonomy method |
| `analytics` | Read-only exact aggregation over the indexed population; undefined ratios are null |
| `corpus_query` | Literal bounded file/formula queries with complete and filtered totals and retained source identities |
| `ontology_analysis` / `ontology_graph` / `taxonomy_paths` | Distinct direct-taxonomy diagnostics and shortest source-backed paths; graph budgets remain explicit |
| `ontology_observations` / `ontology_figures` | Recompute complete retained-file taxonomy counts and render their source-bound publication figure |
| `reports` | Export numerical measurements, plots, and self-contained HTML using shared analytics |
| `projection` | Emit explicit subclass facts plus transitivity with exact problem/source hashes |
| `runtime` / `runtime_results` | Bound real prover execution; decode actual structured automated theorem proving (ATP) results and reject stale invocations |
| `inference_models` / `inference_study` / `inference_compiler` | Validate the registered source selection, derive complete source claims and compile the supported function-free fragment; reject unsupported syntax |
| `inference_runner` / `inference_replay` | Execute registered native cases and controls; rederive problems, capture interpretation and summary from retained inputs without silently accepting mutations |
| `inference_views` / `inference_cli` | Adapt catalog, native-run and read-only report/case inspection methods; browser and agent inspection never launch a prover |
| `runtime_diagnostics` | Replay frozen inputs and complete named premise exports with the captured prover family, E or Vampire (E/V); no automatic minimality claim |
| `alignment` / `competency` | Execute the versioned finite FOL/numerical campaign; portable replay rederives sources, problems, values and status interpretation |
| `bridge_models` / `bridge_study` | Validate the rational witness authority, shared identities, selected source claims and explicit local interpretation; derive exact posteriors and independent Decimal references |
| `bridge_compiler` | Generate concrete Lean finite laws, complete kernels and posterior/KL instances; compile in isolation with declaration-axiom inspection and rejected controls |
| `bridge_runner` / `bridge_replay` | Produce a fresh Lean/numerical/native packet; strictly rederive its retained evidence against an independently supplied report digest without new native execution |
| `bridge_views` / `bridge_cli` | Join verified native cases to their rational/numerical witness, selected source claims and Lean source; adapt catalog, production, replay, inspection and figure export |
| `bridge_figures` | Derive three PNG/SVG figures, retained figure inputs and an offline case/Lean/numerical explorer after strict bridge replay; no new proof execution |
| `cache_inheritance` | Construct isolated knowledge bases from source and run full cache building without seeded maps; preserve controlled observations and stable bindings |
| `runtime_setup` | Preserve existing source/runtime files, verify pins and patch hashes, install native environment |
| `runtime_query` / `runtime_server` | Orchestrate native processes explicitly, without process work on import |
| `fep` | Validate linear/log finite models; share logarithmic objective/support calculations; retain explicit projection underflow and decomposition residual |
| `active_inference` | Compose exact action/observation channels, score outcome risk plus ambiguity against an independent information-gain decomposition, retain ties, and condition on supplied actual outcomes; see [Active Inference contract](active-inference.md) |
| `finite_channels` / `witness_research` | Compute exact state/observation transformations and independently checked Decimal information quantities from validated shared witnesses; make no additional native or Lean proof claim |
| `witness_dynamics` | Derive persistent-state sequential conditioning by exact products and iterative Bayes, plus reproducible seeded forward trajectories and declared model weights |
| `witness_research_figures` / `witness_dynamics_figures` | Render the representation experiments and four-panel sequential figure from their checked numerical exports; preserve inputs and refuse occupied destinations |
| `witness_abstracts` / `publication_abstracts` | Derive three dense source/witness/evidence abstracts from the verified bridge and project their ordered frontmatter into the editions |
| `formal_verification` | Compile pinned finite modules in isolation, check dependencies, and inspect declaration axioms |
| `manuscript_provenance` | Validate inputs, hydrate explicit tokens, freeze and verify renderer sources/artifacts |
| `manuscript_verification` | Verify actual edition artifacts, including canonical image equality and the three abstracts' physical PDF pages 2–4 |
| `publication` | Derive author metadata, model values and native configuration from hashed authorities |
| `publication_research` | Require complete E/V campaigns with matching study, source claims, numerical matrix and problem hashes; derive publication values from reports |
| `publication_bridge` | Replay the shared-witness report, stage its bound artifacts and derived representation/sequential exports, and verify their complete tables and figure copies across editions |
| `publication_checks` | Parse actual Pandoc documents and bibliography; reject missing citations, labels and manual numbering |
| `publication_office` | Retain the exact native Pandoc default; project only two geometry elements and approved Hyperlink/ImageCaption style atoms; purely recompute reference policy and independently check every actual Word section |
| `publication_office_content` | Pure byte projection adds only ordinary table-row `cantSplit`; independently reconstruct permitted inserts and check the supported complete manuscript math sequence and distinct atomic relation pair |
| `manuscript_figures` | Generate the graphical abstract and finite-model figure from checked numerical and indexed inputs |
| `research_figures` | Derive campaign control figures and an offline explorer from portable replay, with report hashes and measured denominators |
| `manuscript` / `manuscript_verification` | Invoke canonical renderers and inspect actual PDF, Word (`.docx`), and HTML output |
| `quality` | Reject incomplete coverage observations; enforce core and infrastructure floors separately |

`cli`, `dashboard`, and `mcp_server` adapt these methods to their transports.
The runtime and manuscript scripts select the checkout root and call importable
entrypoints. They contain no installation, numerical, hashing, rendering, or
result-classification implementation. No runtime script starts processes merely
because it is imported; isolated subprocess tests check this with invalid argv.

The index's SQLite schema and read-only connection are package-internal seams
shared by indexing and analytics. Public consumers use method results rather than
depending on tables. Test fixtures cross the same methods with actual files and
repositories; they do not replace methods with mocked return values.

The [finite study](research.md) declares its FOL interpretation and exclusions;
it does not translate arbitrary SUO-KIF or encode probability arithmetic as FOL.
The [fresh cache experiment](cache-inheritance.md) loads a selected fragment and
complete Merge separately, not the four-file core. The historical seeded cache
step and translated refutation remain distinct evidence. None supplies a
SUMO-to-Lean preservation theorem or empirical validation.

The [inference laboratory tutorial](inference-tutorial.md) and
[method contract](inference-methods.md) distinguish selected source kernels from
Sigma's full-profile path. Scenario and native-run totals come from the registered
catalog and retained report. Background, positive, countermodel, premise-removal,
and refutation controls test different obligations; portable replay is separate
from new native execution and independent proof-step checking.

## Office reference custody and page policy

`publication_office.write_office_reference` invokes native Pandoc and retains its
exact default archive. Within `word/document.xml`, it inserts only `w:pgSz`
and `w:pgMar`, preserving all other document Extensible Markup Language (XML)
bytes. Within `word/styles.xml`, it replaces only the `Hyperlink` color atom
with explicit `#005EA8`, removing that atom's theme color/tint/shade selectors,
and inserts only `w:pPr/w:keepLines` for `ImageCaption`. It requires that caption
to derive from `Caption` and the native `CaptionedFigure` to retain enabled
`w:keepNext`; that figure property is checked, not added. Every other style/XML
byte and ZIP member payload remains exact, with member order, archive comment
and public member metadata preserved. Derived sizes, checksums and offsets
reflect the approved payload changes. No arbitrary theme/font rewrite or
prose/math change is authorized. Unbound, ambiguous or unsupported native style
and section targets fail explicitly. Preserve the exact native bytes: archive
timestamps can vary across Pandoc exports, so repeat-export digest equality is
not a custody requirement.

`manuscript` stages `output/manuscript/office-reference.docx` and
`output/manuscript/office-reference.native-default.docx`, passes `reference_doc`
to the canonical Word renderer, and records both digests and the invoked Pandoc
executable/version/digest in `render-receipt.json`'s `office_reference`. Its
`geometry` and `actual` records describe the reference and final Word package.
Final verification must independently check both packages' explicit geometry
in every section, including one text column and zero gutter, and recompute the
approved geometry-plus-style reference from the retained default. The pure
`verify_office_reference_policy` requires the generated archive to match exactly,
including metadata; a fresh receipt hash cannot waive wrong styles or geometry. The
configured 12 mm margin rounds half-up to 680 twips within 0.01 mm; portrait
Letter paper is 215.9 × 279.4 mm, or 12240 × 15840 twips; 1440 twips = 25.4 mm.
The [Python interface contract](API.md#office-page-policy) lists signatures,
record fields and errors. XML and geometry verification establish no Word
pagination, visual acceptance, or completed manuscript pass. Ordinary digital
document text has a 4.5:1 contrast policy; native palette inheritance is no waiver,
and a fallback color alone does not resolve theme precedence. Native
propagation, final editions and LibreOffice contrast/pagination review are
separate evidence identified in the release verification summary.
Changed artifacts require a new matching review; a bounded LibreOffice result
cannot establish native Microsoft Word pagination. See the
[qualification guide](current-state.md).

## Final Word content custody

The Office Open XML Word package (`.docx`) has a second, separate custody
boundary after native rendering. The `publication_office` reference policy
above operates before rendering; its existing writer/page-verifier application
programming interface (API) signatures and frozen fields remain unchanged, and
the retained native default is exact. `manuscript` renders through that reference into
`output/manuscript/rikishi-native.docx`, calls
`publication_office_content.project_office_content` on its bytes, checks the
projected math, and writes the final `output/docx/rikishi.docx`. The byte methods
perform no file access, rendering, prover execution or geometry repair.

The sole document-byte edit is insertion of enabled `w:cantSplit` in every
supported ordinary table row that lacks it, including header rows. Already
enabled rows remain unchanged. Repeated `w:tblHeader` properties, every other
XML byte, text, math, geometry, styles and every other ZIP payload are preserved.
The verifier also requires member inventory/order, archive comment and public
member metadata to match, excluding derived sizes, checksums and offsets.
Compressed archive bytes may differ after repacking; both package hashes
are retained. This contract does not reserialize the document tree.

Only ordinary unmerged text rows with the supported native serialization and
row-property syntax/order are admitted. Nested tables, vertical/horizontal merges,
grid spans, drawings in rows, comments, character-data sections,
malformed/duplicate/unknown properties and explicit
disabled `cantSplit` policies fail with `OfficeContentError`; unsafe packages fail
through the same typed error. Existing enabled policies need no edit. A row
taller than the usable page needs a separate authored layout decision; neither
an insertion nor a green XML check establishes actual pagination.

`render-receipt.json` binds both staged native and final packages as artifacts.
Its `office_content` records schema version, package/document hashes, observed
table/row/enabled repeated-header counts and zero-based changed-row indices with exact
before/after row hashes. `office_math` records ordered gathered-structure hashes,
atomic non-entailment count and entailment-of-negation count. The
[interface contract](API.md#office-content-projection-and-math) lists the exact
signatures and all frozen dataclass fields. `manuscript_verification` requires
the native artifact, independently reconstructs the permitted projection from
its bytes, checks the final math, and compares both recomputed reports with the
receipt. Reference/final geometry remains independently checked under the
existing `office_reference` contract; recorded counts alone establish nothing.

The mathematical source belongs to the shared canonical
[`manuscript/rikishi.md`](../manuscript/rikishi.md): three `gathered` displays,
repeated `F(q)=` on finite-objective rows, and atomic `\nvDash`. It feeds every
edition without a Word-only math fork. The row projection never edits math.
`verify_office_content_math` binds the supported complete manuscript math sequence:
the three serialized displays for taxonomy sets, finite-objective
decompositions and Lean finite definitions, and the two companion gathered
displays (`sumo-translated-core` and `logarithmic-normalization`). Complete
expression envelopes admit only the supported native numbering suffix. Producer
and verifier require the returned matrix inventory length to match the canonical
hydrated body's gathered count; the isolated fixture does not replace that
full-body obligation. It rejects altered structural digests,
literal alignment `&` or combining slash U+0338, and requires the ordered atomic
`T⊭q` / `T⊨¬q` structural pair with one non-entailment glyph in math text.
This bounded serialization contract supplies no general scientific validation,
semantic-preservation theorem or mathematical proof.

Changed final editions require a new visual review; byte custody and geometry
checks cannot establish pagination or clear a visual finding. Code review,
final rendering and visual acceptance are separately recorded gates. Rejected
candidates and refuted allegations remain in their original evidence capsules;
they do not qualify a changed release candidate. The
[qualification guide](current-state.md) defines the required current records.
No final success or completed native campaign is asserted here. See the
[final Word recipe](manuscript.md#final-word-content-projection-and-math-checks).

## Shared finite witness obligations

The versioned authority
[`fep-sumo-bridge-v1.json`](../src/rikishi/data/fep-sumo-bridge-v1.json) declares
three strictly positive rational Boolean (`Bool`) witnesses. Each binds one prior,
complete observation kernel, candidate distribution, observed value `True`, and
authored model/representation/calculation/result/agent identifiers. Every
hidden-state tuple uses `(false, true)`: index 0 is `Bool.false` and index 1 is
`Bool.true`. Observation `True` is the selected observation value, not the first
hidden state. The explorer coordinate is `q(false)=q0`, with `q(true)=1-q0`.

| Obligation | Shared-input binding | Evidence boundary |
| --- | --- | --- |
| Exact posterior | Python `Fraction` products and normalization from rational prior/likelihood inputs | Exact finite arithmetic; no floating-point correctness theorem |
| Numerical comparison | Existing finite objective compared with independently computed 80-digit `Decimal` products/logarithms, exact posterior and reconstruction residuals | Reported tolerance and residuals apply to these witnesses |
| Concrete Lean instantiation | `FEP.FiniteLaw Bool` prior/candidate, `FEP.FiniteKernel Bool Bool`, and predictive/posterior/positivity/reconstruction/KL declarations at revision `9a0694f16b8e89b66b2f7f8cc7426c650dd2c4de` | Generated source uses the actual finite application programming interfaces; string entity definitions bind authored labels only |
| Selected SUMO scenarios | Source-bound model, representation, calculation, named-record result and existential-result consequences with explicit local assumptions | Restricted FOL role obligations; no ontology arithmetic or general translation theorem |

The complete Lean kernel assigns the manifest likelihood to observation `True`
and its complement to observation `False` for each hidden state. Prior and
candidate sum exactly to one. Rational `bridgeRationalMass` source labels record
inputs and exact posterior values; their numerators and denominators are
uninterpreted labels in the FOL problems, not arithmetic axioms. A SUMO result
role therefore does not prove the numerical posterior or a Lean theorem.

Each registered source scenario has background, positive, negative-query,
premise-removal, and refutation controls for the selected native families E and
Vampire (E/V). Background satisfiability must accompany a matched positive
outcome. Lean control inputs exercise invalid normalization, a wrong posterior,
and an admitted proof; rejection must be observed in their retained compiler
logs. A declaration inventory includes definitions as well as theorems and
cannot be reported as a theorem count. All observed counts, statuses, family
selections, rejection results and completion come from the actual report;
the catalog is design evidence only. No completed native pass is asserted here.

`bridge-run` produces `bridge-report.json` in a fresh repository-local directory;
the canonical location is `output/bridge/bridge-report.json`. Native work waits
for the active runtime owner to finish; preserve running jobs and failed evidence.
Record the digest of your own fresh completed producer output separately with
its custody evidence. Replay and inspection require that independently supplied
Secure Hash Algorithm 256-bit (SHA-256) digest. Hashing a received untrusted
packet does not establish trust in its producer.

Strict replay rederives the study, retained source claims, extension, numerical
values, generated Lean source, problems, captured status interpretation and
summary. It checks retained Lean artifacts, commands, logs, declaration axioms
and dependency-identity receipts for consistency. Replay does no new Lean
checking, authenticates no historical process execution, retains/authenticates
no complete external compiler/dependency artifact set, and independently checks
no prover proof-calculus steps. The report keeps `semantic_validation=false`.
These obligations supply no general SUMO-to-Lean semantic preservation,
whole-ontology consistency, or empirical FEP result.

The command-line bridge supports production, replay, inspection and figure
export. HTTP and MCP expose only catalog and existing report/case inspection;
neither starts a compiler or prover. Figure export derives three PNG/SVG pairs,
`bridge-explorer.html`, and `bridge-figure-inputs.json` after strict replay into a
fresh directory with an existing symlink-free parent on mounted GitVault. The
offline explorer exposes retained cases/Lean source and finite candidate
calculations; interactive numerical exploration executes no new proof.
`GET /api/bridge/explorer` derives that view from the same explicit saved-report
path and supplied digest, without running native tools. The
[interface guide](API.md#finite-witness-bridge) specifies arguments, defaults,
digest custody, output names, and transport errors.

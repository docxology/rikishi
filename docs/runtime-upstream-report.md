# Local Sigma findings and reproducible limits

This report is local; no upstream issue, message, or publication was made.
Observations use the Suggested Upper Merged Ontology (SUMO)
`efcd059f8feebfe3488a09f575f88d4d009b1e5c`, Sigma
`d3cc7b43b38b0b45692291a1b33fe2b1a3de0095`, and E
`3b7afc70fe77d3118bb95144c4735ca45f5f31cf`.

## Compound class guards

`FormulaPreprocessor.buildTypeGuardExpr` originally wrapped compound types such
as `(ExtensionFn Oval)` in `Expr.Atom`, emitting invalid Thousands of Problems
for Theorem Provers (TPTP) syntax
`s__(ExtensionFn Oval)`. E rejected the generated input at line 840, column 188;
it remains at `.omo/evidence/runtime/SUMO-unpatched.tptp`.

The existing `config/patches/sigma-compound-type-guards.patch` parses compound
types as expression trees for both instance and subclass guards and keeps
atomic types atomic. The lock binds the patch and before/after source hashes.
`RuntimeTypeGuardRegression.java` tests both compound branches and an atomic
control against real Java. Its test also compiles the actual pinned unpatched
source into a temporary classpath and requires the same regression to fail.
No SUMO assertion or canonical checkout changes for that negative control.

## Query capture

`EProver.submitQuery` deletes its generated input in `finally`. The former
status-only sidecar could not establish which problem was proved, and mixed
logs contain user echoes without recoverable proof dependencies.

Rikishi now captures exact input and transitive includes before execution,
raw streams, argument arrays, process state, and hashes. An invocation-local
executable adapter uses Sigma's existing translation path without source edits.
`runtime_results` compares the saved evidence to the actual Java `ATPResult`;
status-only and stale/tampered records fail closed. Synchronous first-order form
(FOF) generation continues to avoid the native command-line interface (CLI) startup race.

Inspection also requires trusted caller bindings to the executable/hash,
invocation, input/query and source context before granting proof authority.
Without them it records an unverified status. A real Python process printing
`Theorem` for a problem with an actual E countermodel cannot certify entailment.
The shared structural TPTP parser captures includes regardless of physical line
layout and exports complete premises; every nonempty export is replay-validated
with the same bound native family before diagnostic success.

Round-two native checks exposed a further lexical boundary. An include path
containing two literal backslashes names a different macOS file from the
one-backslash path produced by ordinary atom unescaping. Actual E reads the
two-backslash filename; the former capture parser froze the other file. The
corrected supported subset rejects every backslash in include paths before
launch and during strict receipt inspection. Ordinary unescaped paths retain
the existing replay workflow.

Proof-source names now come from structural `file(path, name)` annotations,
including quoted, spaced, numeric, and doubled-backslash names. Escaped
apostrophes in names are explicitly unsupported. Real E emits the same proof
name for distinct inputs `'premise\'s name'` and `'premise\\s name'` at this pin;
normalizing to that corrupted output would lose identity. Native collision,
countermodel, and exported-subset replay controls establish this boundary.
No upstream source change was made for either lexical correction.

Round three also reproduced a file-symlink boundary: E resolves a nested include
from the lexical containing directory, while resolving the linked file first
made capture use its target directory. Contrasting p/q backgrounds produced an
actual theorem and a frozen countermodel from the same invocation. Capture now
rejects all symlink components in root-problem and include paths before
normalization, with a post-run recheck. A required path-policy version invalidates
earlier potentially lossy captures. Saved expansion compares lexical normalized
identities using retained metadata only, so it neither follows a current source
symlink nor requires the original inputs to remain present. This restriction
does not change ontology or cache semantics.

Round three also reproduced extra positional E inputs: the actual two-file
invocation proved the goal, while replaying only the saved final problem produced
a countermodel. Launch and strict saved readers now share a single-problem option
allowlist, with a required command-policy version and trusted prover-family
binding. Extra inputs, stdin and unsupported options cannot certify a proof even
when a historical receipt is relabeled with the current policy.

Actual Vampire 5.1.0 runs confirm matching nested-relative-include resolution for
ordinary paths, using contrasting root/nested leaf axioms, theorem/countermodel
controls and frozen replay after original inputs move. Pinned Sigma's additional
`--output_axiom_names on` option is rejected with exit 4 by the installed binary
Secure Hash Algorithm 256-bit (SHA-256) fingerprint
`470529c41026e8f2844340e726bdc026406ced0b3afaaab72de7428456c84ec6`.
The actual pre-fix translated query and strict adapter failure remain in
`.omo/evidence/corpus-vampire-upgrade-20261021/vampire/sigma-before.log` and its
stderr/report. This is an observation about that exact executable and command,
not a compatibility assertion about other Vampire builds.

The managed fix changes only the local Java adapter's final invocation dispatch.
A small subclass retains inherited `askVampire`, preprocessing, query translation,
background generation, user assertions and include assembly, then delegates
`run(File)` to existing `runCustom(File)`. Fixed `VAMPIRE_OPTS` selects
`--proof tptp --mode casc`; Sigma adds the bounded time and final absolute input.
Unsupported option strings and repeated submission fail. No upstream source,
Java archive (JAR), lock, cache algorithm, ontology axiom, or shared command grammar changed.

The query runner clones the complete configured profile, preserving every input
byte and freshness timestamp. Its bound manifest includes the serialized cache,
lexicons, constituents and configuration, alongside the exact JAR and adapter
hashes. Original profile stability and copied input stability are checked across
execution. Only copied directory preferences change in memory; original and
copied constituent bytes must match the configured source. Links, special files,
external mutable roots, unsupported constituent paths, duplicate preferences,
and incomplete copies cannot produce an accepted result. Generated automated theorem proving (ATP) inputs
remain independently captured with transitive includes. Two simultaneous
preparations demonstrate isolated outputs.

Actual native Sigma translations from isolated finite test profiles return
Theorem and CounterSatisfiable through this dispatch. Their stdout counts,
exits, frozen replay after profile relocation, diagnostic subset replay, and
forged executable/family/query/invocation/profile bindings are checked. The
canonical Human/Animal query returns a verified Theorem. Its earlier translated
background was byte-identical to the prior E background
`3af8bbb0023ce53c65b6504a025cc0f30ff2132667bbd1f8cd249e2e1967e3ed`.
A later supported bootstrap rebuilt the JAR without changing its class-content
binding. Sigma's cache freshness check then selected fresh loading rather than
the copied serialized cache. Generated source comments use each invocation's
copied constituent paths. In six retained captures, all 36,697 complete parsed
statements, their order, roles and annotations match exactly; replacing 11,133
standalone-comment path prefixes explains every raw byte difference. The copied
input manifests are identical. The complete comparison is retained in
`.omo/evidence/corpus-vampire-upgrade-20261021/context-fix/capture-comparison.json`.

The registered context now accepts that exact complete statement sequence after
verifying the supplied bytes against their raw SHA-256 receipts and the existing
prover/classes/lock/configuration bindings. Its ordered statement-text fingerprint
is `ab478bdfc42d614399c8e016a3bfbfc36f9a4578d029e8ac56bbf23144c959df`.
The parser omits standalone layout/comments only; every character inside each
complete statement remains bound. A subset, changed statement, role, annotation,
inner comment or order cannot match. Malformed inputs or missing provenance
remain unknown. The historical pure raw-hash application programming interface (API) still recognizes only the
original digest; supplied invalid bytes never fall back to that path. Native
JavaScript Object Notation (JSON) identifies this comparison separately as
`negative_control_context_binding.scope="complete_translated_background_statement_sequence"`.
Exact raw capture hashes and trusted invocation proof custody are unchanged.
This comparison supplies neither source-ontology equivalence nor independent
proof-step checking. The E route retains its native query and context contract.

The canonical Human/Artifact query at five seconds returns Timeout with native
exit 1. `ProverTimeoutException` is caught only to retain the actual finalized
`ATPResult`; exact stdout/status/exit receipts classify it as inconclusive,
never a countermodel. Separately, four complete named axioms extracted from that
exact frozen background match `path-contradiction.p`, contain no conjecture, and
return Unsatisfiable under the pinned Vampire. Structural proof extraction and
exported-subset replay retain all four premises and again return Unsatisfiable.
That evidence justifies the registered Vampire background-context binding without
claiming the timed-out full query succeeded. These controls retain
`semantic_validation=false`; no ontology consistency repair follows.

The direct `runtime.prove` API selects E or Vampire independently of the managed
Sigma dispatch. Direct captures bind the family, executable, invocation and exact
input; `runtime.compare` requires identical retained problem/include bytes and
reports only statuses and agreement or inconclusiveness. Diagnostics replay the
saved bytes with the same executable and family, preserve supported search
options, and change only the time limit and required proof flags. E-default
extraction still uses `CNFRefutation`; explicit Vampire extraction requires one
complete matching `Proof for NAME` block. Complete named statements are exported
through the existing structural parser and replayed with that family. A
countermodel has no proof-premise set; these exports establish no automatic
minimality, translation equivalence, or full-profile consistency. The cache and
ontology semantics are unchanged.

## Four-premise translated contradiction

A native `(subclass Human Artifact)` query with a five-second processor-time limit returned
`ContradictoryAxioms`. Frozen-input replay with the original search options plus
`--tstp-format --proof-object` reproduced it. The conjunctive normal form (CNF) refutation uses these
premises; the conjecture is absent:

| Premise | Content | Generated source annotation |
| --- | --- | --- |
| `kb_SUMO_3638` | Disjoint classes have no common instance | `Merge.kif:441` |
| `kb_SUMO_5666` | Total and partial valued relations are disjoint | `Merge.kif:2866` |
| `kb_SUMO_14277` | `path` is a partial valued relation | `SUMO_Cache.kif:1` |
| `kb_SUMO_14280` | `path` is a total valued relation | `Merge.kif:14141` |

The exact formulas are in `tests/runtime/fixtures/path-contradiction.p`. Real E
with `--auto`, proof flags, and a five-second processor-time limit returns `Unsatisfiable`
for those four axioms alone. Removing each one independently returns
`Satisfiable` (exit 1). This establishes inclusion-minimality for this saved
subset; it establishes neither uniqueness nor minimum cardinality over the knowledge base (KB).

The source trace is specific:

- `Merge.kif:5096` asserts `(instance eventPartlyLocated PartialValuedRelation)`.
- `Merge.kif:14144` asserts `(subrelation path eventPartlyLocated)`.
- `KBcache.buildTransInstOf`, Sigma lines 1212–1269, copies parent instance
  classifications through recorded subrelations, adding the parent's partial
  classification to `path`.
- `KBcache.storeCacheAsFormulas`, lines 2108–2148, asserts the derived cached
  classification.

The historical `RuntimeCacheDiagnostic.java` reproduces that step in an isolated three-formula
KB using installed Sigma classes. A partial parent gives `path` both partial
and total classifications. Replacing only the parent's partial classification
with `Relation` removes the derived partial classification while preserving the
direct total classification. This localizes the generated premise to cache
inheritance. The diagnostic seeds the subrelation parent map explicitly; it is
a focused cache-step reproduction. Its seeded setup remains evidence of that
earlier diagnostic only.

## Fresh source-only cache experiment

The current `output/research/fresh-cache/result.json` records `status="observed"`,
five successful controls, stable bindings and `semantic_validation=false`.
`FreshCacheDiagnostic.java` uses the real KB constructor, Knowledge Interchange Format (KIF) ingestion and
`KBcache.buildCaches()` without seeding cache maps. It separately loads the
declared 39-formula fragment and complete pinned `Merge.kif` in isolated KBs.
Both generate PartialValuedRelation for `path`, whose direct classifications are
CaseRole and TotalValuedRelation.

Replacing the parent's partial classification with Relation or removing the
subrelation edge removes the generated partial classification. Adding a synthetic
PartialValuedRelation-to-InheritableRelation superclass link changes positive
cache membership but leaves the generated classification present. Absence of
that positive chain is not a logical negative assertion. Exact source selections,
input changes, tool hashes, formula counts and raw warnings are documented in
[fresh cache methods](cache-inheritance.md).

This source-only experiment extends the earlier seeded diagnostic. Complete
Merge is one file, not the full four-file core; no new full-core consistency
result or repair follows. The four-premise translated refutation and deletion
controls above retain their own historical scope.

No cache or ontology axiom was silently removed. Intended inheritance semantics,
an upstream correction, and checking the complete profile after such a
correction remain open. This generated-theory result does not establish that
the original ontology is inconsistent.

## Historical bounded results and query classification

The earlier full-background no-conjecture run with `--auto --cpu-limit=15`
returned `ResourceOut` (exit 8), preserved at
`.omo/evidence/improvements/translated-core-consistency.log`. It established
neither satisfiability nor inconsistency. The later exact capture and proof supply
the previously missing localized contradiction; exhaustion under one strategy
does not override a refutation under another recorded strategy.

`(subclass Human Animal)` retains actual query entailment with
`semantic_validation=false`, scope `translated_query_only`, and query
consistency `not_established`. Matching core/source/patch/prover/background
bindings attach the recorded negative context; other profiles report `unknown`.
Neither query validates a scientific interpretation or Free Energy Principle (FEP) equivalence.

Compact evidence: `.omo/evidence/next-pass/runtime.md`. Earlier patch/build
evidence: `.omo/evidence/runtime/README.md`.

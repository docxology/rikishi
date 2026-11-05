# Sigma findings and reproducible limits

These methods inspect pinned Suggested Upper Merged Ontology (SUMO)
`efcd059f8feebfe3488a09f575f88d4d009b1e5c`, Sigma
`d3cc7b43b38b0b45692291a1b33fe2b1a3de0095`, and E theorem prover
`3b7afc70fe77d3118bb95144c4735ca45f5f31cf`. The observed results below are
the 1.0.0 baseline; changed release candidates require fresh source-bound runs.
No upstream issue or message is claimed. See [runtime operation](runtime.md),
[source-only cache methods](cache-inheritance.md) and [release notes](release-notes-1.1.0.md).

## Compound class guards

`config/patches/sigma-compound-type-guards.patch` parses compound instance and
subclass guard types as expression trees, while keeping atomic types atomic.
The lock binds the patch and before/after source hashes.
`RuntimeTypeGuardRegression.java` exercises both compound branches and an atomic
control against real Java, then compiles the pinned unpatched source in a
separate temporary classpath and requires that negative control to fail.
The patch changes no SUMO assertion.

## Captured query contract

Sigma's `EProver.submitQuery` deletes its generated input in `finally`.
Rikishi captures the exact submitted bytes and transitive includes before
execution, together with raw streams, arguments, process state and hashes.
The saved capture must agree with Java's actual `ATPResult` and independently
trusted bindings to the executable, invocation, query and source context.
A status string or checksum agreement alone cannot certify entailment.

The structural Thousands of Problems for Theorem Provers (TPTP) parser handles
complete statements and proof-source annotations. Accepted include paths are
unescaped single-quoted names with no symlink component. Unsupported escaping,
include selections and ambiguous proof names are rejected. Launch and replay
share a single-problem option allowlist and bind the native prover family.
Every nonempty exported proof-premise set is replayed with that same family.
This checks a submitted subset, rather than every step of a proof calculus.

The query runner copies the complete configured profile into a fresh invocation
directory. Its manifest binds constituent and configuration bytes, lexicons,
serialized caches, the Sigma Java archive (JAR), class content and adapters.
Original and copied inputs are checked before and after execution. Only copied
directory preferences change in memory. Unsafe paths, links, special files,
duplicate preferences and incomplete profiles fail explicitly.

## Managed Vampire dispatch

Pinned Sigma emits `--output_axiom_names on`, which the installed Vampire 5.1.0
binary rejects with exit 4. That binary's Secure Hash Algorithm 256-bit (SHA-256)
fingerprint is
`470529c41026e8f2844340e726bdc026406ced0b3afaaab72de7428456c84ec6`.
The local `RikishiQuery.java` subclass retains inherited preprocessing,
translation, background generation, user assertions and include assembly,
then delegates final `run(File)` dispatch to inherited `runCustom(File)`.
The fixed options are `--proof tptp --mode casc`, with Sigma's bounded time
and final absolute input. Unsupported options and repeated submission fail.
No upstream source, JAR, ontology axiom or cache algorithm is rewritten.

The direct `runtime.prove` application programming interface (API) selects E
or Vampire independently of Sigma. `runtime.compare` requires identical
retained problem/include bytes and reports statuses, agreement and
inconclusiveness. Family-specific diagnostics preserve supported search options
while changing only time limits and required proof-output flags. Countermodels
have no proof-premise export.

## Registered translated-background context

A registered context requires complete supplied background bytes, their exact
raw SHA-256 binding, and matching prover, Sigma class, source-lock and profile
identities. Digest-only recognition is unsupported. The structural comparison
requires all 36,697 complete statements in their original order, with fingerprint
`ab478bdfc42d614399c8e016a3bfbfc36f9a4578d029e8ac56bbf23144c959df`.
Policy `tptp-statement-text-newline-join-v1` hashes statement text joined by one
newline, with no final newline. Names, roles, formulas, inner whitespace,
comments and annotations remain bound. Only standalone layout and comments
outside parsed statements are excluded from this comparison.

Missing/invalid bytes, changed statements or order, and missing provenance
produce unknown context. `negative_control_context_binding` records this
statement-sequence comparison separately from exact capture custody. A matching
sequence supplies no source-ontology equivalence or independent proof checking.

## Four-premise translated contradiction

The retained E `(subclass Human Artifact)` query returned
`ContradictoryAxioms`. Its conjunctive normal form (CNF) refutation used these
four premises and no conjecture:

| Premise | Content | Generated source annotation |
| --- | --- | --- |
| `kb_SUMO_3638` | Disjoint classes have no common instance | `Merge.kif:441` |
| `kb_SUMO_5666` | Total and partial valued relations are disjoint | `Merge.kif:2866` |
| `kb_SUMO_14277` | `path` is a partial valued relation | `SUMO_Cache.kif:1` |
| `kb_SUMO_14280` | `path` is a total valued relation | `Merge.kif:14141` |

The complete formulas are retained in
[`tests/runtime/fixtures/path-contradiction.p`](../tests/runtime/fixtures/path-contradiction.p).
E returns `Unsatisfiable` for those axioms alone. Each single-premise deletion
returns `Satisfiable`, establishing inclusion-minimality for that saved subset,
without proving uniqueness or minimum cardinality over the knowledge base (KB).

`Merge.kif:5096` classifies `eventPartlyLocated` as `PartialValuedRelation`;
line 14144 makes `path` its subrelation. Sigma's
`KBcache.buildTransInstOf` at lines 1212–1269 copies parent classifications
through subrelations, and `storeCacheAsFormulas` at lines 2108–2148 emits the
generated assertion. This source trace localizes the conflicting classification.

The corresponding five-second Vampire query returns `Timeout`, exit 1.
Its four extracted background premises independently refute under Vampire,
including diagnostic subset replay. This discloses a translated-background
contradiction while leaving the actual timed-out query inconclusive.

## Source-only cache experiment

`FreshCacheDiagnostic.java` uses the actual KB constructor, source ingestion
and `KBcache.buildCaches()`. The five-case schema separately loads a declared
39-formula fragment and complete pinned `Merge.kif`, without seeded cache maps.
Both generate `PartialValuedRelation` for `path` in addition to its direct
`CaseRole` and `TotalValuedRelation` classifications.

Replacing the parent's partial classification or removing the subrelation edge
eliminates the generated partial classification. Adding a synthetic
`PartialValuedRelation`-to-`InheritableRelation` subclass link changes positive
superclass membership while leaving the generated classification present.
Absence of a positive chain is not an asserted logical negation. Exact source
selections, input changes, tool hashes, counts and raw warnings belong to the
[five-control experiment](cache-inheritance.md).

Complete Merge is one file rather than the four-file core. Intended inheritance
semantics, upstream correction and checking a corrected complete profile remain
open. No cache or ontology axiom is silently removed; the generated-theory
finding does not establish inconsistency of the original source ontology.

## Result interpretation

`(subclass Human Animal)` has a retained translated-query entailment result with
`semantic_validation=false`, scope `translated_query_only`, and query
consistency `not_established`. Matching background and runtime bindings attach
the registered negative context; other profiles report unknown. Timeouts and
resource exhaustion remain inconclusive. Selected native outcomes, finite
calculations and named Lean statements supply no general semantic-preservation
theorem or empirical Free Energy Principle (FEP) validation.

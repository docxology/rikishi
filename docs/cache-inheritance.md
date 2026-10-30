# Fresh Sigma cache inheritance diagnostic

The pinned installed Sigma Java archive (JAR) reconstructs the generated partial classification
of `path` from fresh source ingestion. This was observed in a declared
39-formula fragment and, separately, the complete pinned `Merge.kif` loaded into
an isolated knowledge base (KB). `path` has direct `CaseRole` and `TotalValuedRelation`
classifications before cache construction. After `buildCaches()`, its additional
`PartialValuedRelation` classification appears as an in-memory formula with
source label `FreshCache_Cache.kif`.

These are observations of generated classifications. Every receipt carries
`semantic_validation=false`. Loading one complete file is **not** loading the
four-file core profile, proving a query, checking consistency, or repairing the
ontology. The existing full-profile resource limit remains unresolved.

## Source authority and method

The versioned input authority is
[`src/rikishi/data/fresh-cache-v1.json`](../src/rikishi/data/fresh-cache-v1.json).
Its schema 2 fixes source selections, exact text and original line numbers,
installed source/dependency hashes, complete JAR content identities, resource
policy, and controlled input changes. The filename is retained for application programming interface (API) stability;
schema 1 historical packets are not accepted as schema 2 evidence.
The Suggested Upper Merged Ontology (SUMO) is pinned to `efcd059f8feebfe3488a09f575f88d4d009b1e5c`; Sigma is pinned to
`d3cc7b43b38b0b45692291a1b33fe2b1a3de0095`, as recorded in
`config/sumo.lock.json` and the installed JAR's `build.commit=d3cc7b4` stamp.

The complete `Merge.kif` Secure Hash Algorithm 256-bit (SHA-256) fingerprint is
`2e4c3d6b8392a4cb6fbeccb6eb7441e11d6b45592082333285c951fd7c7d3e14`.
The three target assertions are
[`eventPartlyLocated`'s partial classification, line 5096](https://github.com/ontologyportal/sumo/blob/efcd059f8feebfe3488a09f575f88d4d009b1e5c/Merge.kif#L5096),
[`path`'s direct total classification, line 14141](https://github.com/ontologyportal/sumo/blob/efcd059f8feebfe3488a09f575f88d4d009b1e5c/Merge.kif#L14141),
and [the subrelation edge, line 14144](https://github.com/ontologyportal/sumo/blob/efcd059f8feebfe3488a09f575f88d4d009b1e5c/Merge.kif#L14144).
These links identify pinned sources; the experiment reads verified installed
bytes locally and performs no network requests.

[`FreshCacheDiagnostic.java`](../scripts/runtime/FreshCacheDiagnostic.java)
uses the real `KB(String, String)` constructor, `KIF.readFile`, and
`KB.addConstituentInfoAST`, then creates `KBcache` and calls `buildCaches()`.
It never seeds `insts`, `instTransRels`, `parents`, or `instanceOf`. Sigma itself
discovers the transitive relations, signatures, parents, direct instances, and
generated formulas. Relevant pinned implementation locations are
[`KB.java:232`](https://github.com/ontologyportal/sigmakee/blob/d3cc7b43b38b0b45692291a1b33fe2b1a3de0095/src/java/com/articulate/sigma/KB.java#L232),
[`KIF.java:75`](https://github.com/ontologyportal/sigmakee/blob/d3cc7b43b38b0b45692291a1b33fe2b1a3de0095/src/java/com/articulate/sigma/KIF.java#L75),
[`KBcache.java:1212`](https://github.com/ontologyportal/sigmakee/blob/d3cc7b43b38b0b45692291a1b33fe2b1a3de0095/src/java/com/articulate/sigma/KBcache.java#L1212),
[`KBcache.java:2108`](https://github.com/ontologyportal/sigmakee/blob/d3cc7b43b38b0b45692291a1b33fe2b1a3de0095/src/java/com/articulate/sigma/KBcache.java#L2108),
and [`KBcache.java:2310`](https://github.com/ontologyportal/sigmakee/blob/d3cc7b43b38b0b45692291a1b33fe2b1a3de0095/src/java/com/articulate/sigma/KBcache.java#L2310).
The complete relevant Java sources are also retained in each run's `sources/`.

## Controlled observations

| Case | Source formulas loaded | Formulas after cache build | Generated partial classification | Partial class has an InheritableRelation superclass chain |
| --- | ---: | ---: | --- | --- |
| Original fragment | 39 | 117 | yes | no |
| Parent partial classification replaced with Relation | 39 | 115 | no | no |
| Synthetic subclass link to InheritableRelation added | 40 | 118 | yes | yes |
| Subrelation edge removed | 38 | 115 | no | no |
| Complete original Merge.kif | 5519 | 13693 | yes | no |

The direct total classification remains present in all five cases. The parent
and edge changes localize the generated partial classification to inheritance
through the subrelation edge. The synthetic subclass addition changes the
cache's positive superclass-membership answer while leaving the generated
partial classification present. “No” here means that the cache found no such
positive superclass chain; it is not an asserted logical negation or a new
`NonInheritableRelation` category.

`generated_path` includes all cache-generated classifications, including
superclasses of direct types. It is not a list exclusively of classifications
inherited from `eventPartlyLocated`. The controlled comparison specifically
localizes the generated `PartialValuedRelation` classification.

The complete-file parser reports one duplicate axiom at line 17879. The two
raw warning messages are retained in its observation; no source bytes or
classifications are filtered. The complete file contains 5520 parsed source
statements and 5519 unique formulas after Sigma's normal duplicate handling.

## Reproduction and API

Run from the mounted checkout after sourcing the external environment:

```bash
source scripts/env.sh
uv run --no-sync python -c 'import sys; print(sys.prefix); print(sys.base_prefix)'
uv run --no-sync python -c 'from pathlib import Path; from rikishi.cache_inheritance import diagnose_cache_inheritance; print(diagnose_cache_inheritance(Path.cwd(), Path(".omo/evidence/research-agenda-20261021/fresh-cache-reproduction")))'
```

`diagnose_cache_inheritance(root: Path, output: Path, *, timeout: int = 60)`
requires a fresh repository-local directory whose parent already exists. It
rejects occupied destinations, symlinks, traversal, off-vault environments, and
timeouts outside 1–120 integer seconds before writing. Source/authority/tool
failures after directory creation return `status="failed"`, an error, and the
retained receipts. `observed_case_count` counts observations that passed their
declared controls. `status="observed"` requires all declared controls and stable
bindings; `freshcache_scope="minimal_fragment_and_full_merge_only"` describes
the five-case authority above. Partial completed observations remain available
after failure with `freshcache_scope="none"`.

The wall-clock deadline is shared across version checks, compilation and all
five Java processes through existing `run_bounded`. Each Java virtual machine
(JVM) has a 768 MiB heap,
192 MiB metaspace cap, 64 MiB code cache cap, 2 MiB thread stack and two active
processors. These are JVM limits, not an operating-system resident set size (RSS) cap. Each case
has its own `SIGMA_HOME`, configuration, home, temporary directory and KB.
No KB-manager initialization, serialized cache loading, native automated theorem proving (ATP) invocation,
Tomcat startup, bootstrap, installation or network access is used.

The adapter is compiled into an otherwise empty class directory. Compilation
disables annotation processing and implicit source compilation. Runtime
classpath entries are only that unique adapter and the explicitly hashed
installed JARs; dependency entries with the adapter's class name are refused.
Inherited Java injection options and canonical Sigma path environment variables
are removed. No upstream class is shadowed or modified.

Each run preserves complete input Knowledge Interchange Format (KIF), every non-JAR authority source (including
`Merge.kif`), source authority and Java/Python source copies, exact command
arrays, raw stdout/stderr, exit/timeout receipts,
observations and a final result. Source, lock, patch, active-profile configuration,
JARs, dependencies and toolchain are hashed before and after. `jar-content.json`
records complete executable archive identities, including non-class resources;
`jar-classes.json` is supplementary historical comparison data. The generated
adapter class has its own digest. Inputs
and isolated configuration have per-case pre-execution hashes and final
rechecks. Toolchain bindings include Java, javac, Java Development Kit (JDK) release, modules and JVM
library. These identify this installed toolchain, not an entire operating-system
or JDK installation attestation.

## Archive identity and custody

`cache_jar_identity.jar_content_identity(path, source_revision=None)` returns a
strict `JarContentIdentity`: `policy`, `content_sha256`, `source_revision`,
`archive_sha256`, and `entry_count`. Authority `jar_contents` maps every
repository-relative classpath JAR to its first three fields. Dependencies retain
their exact archive digests in authority `bindings` as well. Sigma binds its
full pinned source revision and complete normalized content instead of one
build's ZIP bytes. Each invocation still records the actual Sigma archive SHA
in both binding manifests and copies that exact 1.4 MB archive beneath
`sources/.rikishi/upstream/sigmakee/build/sigmakee.jar` for portable rehashing.
Large dependency archives are not duplicated; their exact declared and observed
digests identify the archived execution, without attesting to an entire host.

The `complete-jar-content-v1` algorithm hashes its policy and full source
revision (or empty dependency revision), then every non-directory entry sorted
by filename. Each UTF-8 filename and uncompressed content is prefixed with its
unsigned 8-byte big-endian length. All classes, licenses, service descriptors,
configuration and other resources are bound. ZIP ordering, compression,
directory records, timestamps, comments and file permissions are packaging
metadata. Duplicate/unsafe names, unsupported encodings, special files, missing
source stamps, invalid stamps and oversized archives are rejected.

Only the pinned Sigma archive permits one manifest normalization. Its main
`Implementation-Version` must equal the `version.properties` version followed
by ` built on ` and a valid English Ant timestamp. The timestamp is replaced
with `<ANT-BUILD-TIME>`; manifest continuations and line endings are normalized.
Every other manifest value remains bound, including `Main-Class`, classpath,
version, toolchain and vendor fields. Pinned `build.xml:212,433–439` generates
this suffix from the build clock, so it is deliberately volatile across Ant
`dist` repacks. This exception does not authorize changes to other resources.

`version.properties` is **not normalized or omitted**. Its complete bytes remain
bound. Its `build.commit` must identify the full pinned revision and agree with
`build.version`. Its `build.date` is the source commit date generated by
`git log -1 --format=%cs` (`build.xml:359–382`), not a volatile build-clock
timestamp. Sigma reads these properties in `KBmanager.java:69–98`; changing
their values changes runtime-visible version semantics and fails identity.

The earlier schema 1 authority pinned archive
`5791274c5773616386e16295fa8f30e628ef3375bb0540a467db280716ff6593`.
The unchanged installed archive observed during the F2 reproduction was
`1c8054cb05a0f6fc1780e5c801e1c34daaadcd6c539aa6112fe5c6744f1eb27a`,
which the old operation rejected before executing any case. Matching historical
class digests alone does not establish matching resources or valid acceptance.
Those failed and historical receipts retain their original status and identity;
they are never silently relabeled. New schema 2 observations require a fresh
execution and complete custody checks. The pinned Sigma complete content digest
is `b75282c03fa007c2d10366dd832e3e07ff03cf09dc122093c74cebb280dc3a93`.

## Verification and limits

The focused suite uses real Java, real files and subprocesses. It checks the
original and changed inputs, malformed KIF, malformed authority, source/binding
changes, unsafe/occupied output, receipt corruption, actual deadline expiry,
and replacement/removal of a bound file during a running experiment. A real
Python subprocess applies the original expectation to the reclassified-parent
Java observation and exits unsuccessfully; its failed receipt and traceback
are retained. No mocking framework is used.

Evidence is under `.omo/evidence/research-agenda-20261021/fresh-cache*`.
`fresh-cache-probe-1` retains an early adapter serialization defect: Java exited
successfully but JSON-simple serialized sets as non-JSON text. This probe is
not accepted evidence. Probe 2 corrected this with explicit lists, and subsequent
observations are schema-validated. The separate fresh complete-file probe also
succeeded. `fresh-cache-verification-1` retains 26 passing focused tests and
100% statement/branch coverage for the new Python module, together with its
initial import-order lint failure. Final verification receipts accompany the
source/evidence freeze.

The first coverage invocation wrote the shared ignored `.coverage` file; its
output was copied to `fresh-cache-verification-1/earlier-default.coverage`.
Subsequent coverage output used that verification directory's dedicated file.
No prior coverage file was restored over concurrent work.

The earlier manually seeded diagnostic and four-premise refutation/deletion
experiments remain separate context. No cache semantics, ontology assertion,
existing runtime implementation, lock, patch or canonical cache was changed.
No complete-core consistency result, correction, scientific interpretation,
upstream acceptance or manuscript readiness follows from this experiment.

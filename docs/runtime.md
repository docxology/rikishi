# Native Sigma and automated theorem proving

The Suggested Upper Merged Ontology (SUMO) is distributed in Standard Upper
Ontology Knowledge Interchange Format (SUO-KIF). Sigma reads that source and
prepares automated theorem proving (ATP) queries. Its separately scoped Free
Energy Principle (FEP) research connection does not change native logical scope.
A direct prover run and a
Sigma-mediated query use different input preparation paths; identify the path
before interpreting a status. The [inference tutorial](inference-tutorial.md)
develops the logical distinctions with controlled source-bound examples.

Run from the mounted repository with both Python prefixes on GitVault:

```bash
source scripts/env.sh
uv sync --locked
uv run python -c 'import sys; print(sys.prefix); print(sys.base_prefix)'
bash scripts/bootstrap-sumo.sh
uv run python scripts/runtime-sigma.py start
uv run python scripts/runtime-sigma.py status
```

Sigma is at <http://127.0.0.1:8085/sigma/KBs.jsp>; its local default login is
`admin` / `admin`. `runtime-sigma.py run` keeps Tomcat in the foreground;
`runtime-sigma.py stop` stops it. Logs remain under `.rikishi/runtime/`.

The bootstrap pins the complete SUMO source corpus, Sigma, its Java dependencies,
and E using `config/sumo.lock.json`. It installs native tools under ignored
`.rikishi/`, refuses incompatible repository pins, and applies only the
checksum-guarded compatibility patch. It does not change SUMO assertions.
On Apple Silicon it provisions the pinned Java Development Kit (JDK), Ant, Tomcat, WordNet, and Vampire;
other hosts need a suitable external Java installation and a C build toolchain.

The default core profile contains `Merge.kif`, `Mid-level-ontology.kif`,
`english_format.kif`, and `domainEnglishFormat.kif`. To change profiles, stop
Sigma, bootstrap with `--core-only` or `--all-domains`, then restart it. The
latter loads every top-level SUO-KIF file, including overlapping demonstration
subsets; it has no established consistency guarantee. Native queries permit a
10 GB Java heap. Stop Sigma first on a memory-constrained host.

## Query evidence

These commands use the configured Sigma profile, including its translation and
cache behavior. They are not interchangeable with a laboratory kernel extracted
from selected source formulas. A positive response is not enough to dismiss the
known contradictory-background diagnostic below. Keep the query outcome and the
background interpretation together.

```bash
uv run python scripts/runtime-query.py '(subclass Human Animal)' --timeout 5
uv run python scripts/runtime-query.py '(subclass Human Artifact)' --timeout 5
```

`--prover v` selects the managed Sigma/Vampire path. Pinned Sigma's ordinary
launcher emits `--output_axiom_names on`, rejected by the installed binary
Secure Hash Algorithm 256-bit (SHA-256) fingerprint
`470529c41026e8f2844340e726bdc026406ced0b3afaaab72de7428456c84ec6`.
`RikishiQuery.java` retains inherited `askVampire` preprocessing, translation,
user assertions and include assembly. Its small subclass changes only the final
`run(File)` dispatch to inherited `runCustom(File)`, with fixed
`VAMPIRE_OPTS="--proof tptp --mode casc"` and Sigma's own `-t N FINAL_ABSOLUTE`.
It rejects other option strings and repeated submission. No option is filtered
from an arbitrary command, and the shared strict command grammar is unchanged.
This uses existing Sigma application programming interfaces (APIs) without
changing upstream source or the Java archive (JAR).
The native theorem, countermodel, timeout, frozen-replay and diagnostic controls
are recorded under `.omo/evidence/corpus-vampire-upgrade-20261021/vampire/`.
`--output` names a fresh repository-local log;
existing output and evidence directories are refused. The importable interface is
`runtime_query.run_query(root, query, prover="e", timeout=15, output=None, prover_wall_timeout=None)`.
The command-line interface (CLI) prints JavaScript Object Notation (JSON) and exits 0 for verified query entailment or a countermodel,
and 2 for contradiction diagnostics, inconclusive runs, or invalid evidence.

Each invocation retains:

- A mixed application log and separate Java stderr log.
- A strict Java sidecar with invocation ID and actual `ATPResult` status,
  exit code, and stdout line count.
- `<log>.artifacts/problem.p`, the exact submitted bytes captured before Sigma
  deletes its temporary input, plus frozen copies of all transitive includes.
- Exact prover stdout/stderr, argument array, process state, and SHA-256/size
  receipts in `<log>.artifacts/capture.json`.
- Bindings to the prover, JAR, JAR class bytes, lockfile, profile configuration,
  Java adapter, Python query/profile adapters, and query. Changed bindings during
  execution invalidate a result.
- `profile-inputs.json`, binding every initial profile file's exact bytes, size
  and freshness timestamp, including serialized caches and lexicons. Its hash is
  part of the trusted invocation provenance.

Every query first copies the complete profile to
`<log>.artifacts/sigma-profile/`; Java home, temporary files and generated ATP
files stay inside that invocation. The original configuration bytes and file
timestamps are preserved. Only the copied profile's directory preferences are
redirected in memory before Sigma's existing cache initialization. The copied
cache remains bound to both its exact input hash and the executed JAR hash;
copying it supplies no new cache-validity or ontology claim. The original profile
is checked before and after copying and after execution. Copied cache/source
inputs are checked before and after execution; regenerated ATP files are checked
through the exact problem/include captures. `profile` identifies the original
profile; `execution_profile` and `profile_inputs` identify the retained copy and
its manifest.

Links, special files, escaping or absolute constituent paths, mismatched
configured constituent bytes, duplicate preferences and external VerbNet
profiles fail explicitly. Mutable profile directories must belong to the source
profile. Partial copying never proceeds to Java or produces a successful result;
its incomplete directory remains available for inspection. Two preparations of
the same profile use independent destinations. A full profile copy consumes
additional disk space for each invocation.

An invocation-local executable adapter captures inputs before launching the real
prover. Sigma's existing translator and preprocessing paths remain in use.
`run_bounded` supplies a wall-clock bound and kills its process group on timeout
or interruption. Cleanup signals the group before inspecting the direct child,
so an exited parent does not leave live descendants. A macOS permission error
from an exited zombie is retried after reaping; only an absent group is accepted
without a successful signal. Permission failures for a live child or on the
retry propagate promptly without an implicit context-manager wait. If the
operating system denies termination, the group may remain alive and the call
fails explicitly. The deadline still reports a timeout if natural exit races
permitted cleanup. Without an override, the prover's wall bound remains its
native query limit plus five seconds, and the Java wall bound remains 600 seconds
plus the native limit. `--prover-wall-timeout N` independently selects 1–3600
seconds of prover wall time; it preserves the native `--timeout` limit and gives
Java a wall bound of 600 seconds plus that explicit allowance. Both inputs must
be integers; booleans, fractional values and nonfinite values are rejected before
environment or artifact access. The native limit remains 1–300 seconds.

For example, a contended host can use an explicit wall allowance without raising
E's processor-time limit:

```bash
uv run --locked --no-sync python scripts/runtime-query.py \
  '(subclass Human Animal)' --timeout 15 --prover-wall-timeout 300 \
  --output .rikishi/results/NEW_QUERY.log
```

The returned `budgets` records the mode, `native_limit_seconds`,
`prover_wall_seconds` and `java_wall_seconds`. An explicit allowance equal to the
default prover wall value still has a distinct mode and Java bound. Exact
`budgets.json` bytes are hashed into invocation provenance; numeric values and
mode are recorded there too, and the live runner rechecks the file with its other
bindings after execution. The generic saved-result reader compares trusted
provenance and captured inputs/output; it does not independently reopen this
separate budget document or authenticate historical elapsed time. An outer kill
remains `Timeout` and inconclusive. No automatic retry or result relabeling occurs.

The reader requires the live runner's pre-execution executable, input/query,
invocation and source bindings as well as matching hashes, sizes, status in the
[SZS result ontology](https://szs.tptp.org/),
stdout count, and process exits. Inspection without trusted bindings returns
`unverified` and never `proved=true`; checksum agreement alone has no proof
authority. It rejects status-only sidecars, stale IDs, unsafe
paths, links, FIFOs, oversized files, tampering, and incomplete runs. Mixed logs
and echoed query text never certify a proof. Earlier status-only records remain
historical evidence in Git but cannot pass the current gate.

`Theorem` reports entailment for the translated query, with
`outcome="entailed"`, `validation_scope="translated_query_only"`,
`semantic_validation=false`, and query consistency `not_established`.
`ContradictoryAxioms` becomes `inconsistent_translated_axioms`, with `proved=false`.
Timeout and resource exhaustion are inconclusive, not countermodels.

Historical negative-control context requires matching profile configuration,
source/patch lock, prover, Sigma class bytes, and the complete registered
translated background. Class content supplies a stable comparison across JAR
repacking; exact archive hashes are still retained per invocation. The historical
raw-hash API recognizes only the original exact background digest. Native queries
also supply the checksum-verified background bytes to the unchanged structural
Thousands of Problems for Theorem Provers (TPTP) parser. They require all **36,697** complete statements, in their original
order, with fingerprint
`ab478bdfc42d614399c8e016a3bfbfc36f9a4578d029e8ac56bbf23144c959df`.
Policy `tptp-statement-text-newline-join-v1` hashes UTF-8 statement text joined by
one newline, without a trailing newline. Names, roles, formulas, inner whitespace,
inner comments and annotations remain bound. Only standalone layout and comments
omitted by the parser are outside this fingerprint's scope. Missing or changed
statements, changed order, invalid bytes or missing provenance report `unknown`;
invalid supplied bytes never fall back to the historical raw-hash path.

`negative_control_context_binding` is null for unknown context. A recognized
native result records the scope `complete_translated_background_statement_sequence`,
fingerprint policy, digest and count separately from the unchanged exact raw
capture receipts. This comparison establishes complete translated statement
identity under the recorded policy; it supplies no source-ontology equivalence
or independent proof-step verification.

A supported bootstrap can rebuild the JAR with identical class bytes but a newer
modification time than the copied serialized cache. Sigma then rebuilds the cache
from copied constituent paths. Its generated standalone source comments contain
those invocation-local paths, so raw background hashes differ between queries.
Six retained pre/post-bootstrap captures have identical complete statement text
and order; literal comment-path substitutions explain every changed byte.
These comparisons are retained under
`.omo/evidence/corpus-vampire-upgrade-20261021/context-fix/`.

The exact installed Vampire binding has its own observed context, with the
existing E binding preserved. The five-second core Human/Artifact Vampire query
returns `Timeout`, exit 1, and a verified inconclusive result; the Java adapter
retains the real `ATPResult` even when Sigma throws its timeout exception.
Independently, the four complete known contradiction premises extracted from
that invocation's frozen background refute under Vampire without any
conjecture, and the diagnostic exported subset also refutes. Matching queries
therefore disclose that historical translated-background contradiction without
turning the timed-out query into a countermodel or a proof.
This does not label the original SUMO ontology inconsistent.

## Replay and localized contradiction

```bash
uv run python -m rikishi.runtime_diagnostics \
  .rikishi/results/query.log.artifacts/capture.json \
  --timeout 5 --output .rikishi/results/query-diagnostic
```

`runtime_diagnostics.diagnose(capture_path, root, timeout=5, output=directory)`
accepts a fresh repository-local output directory and 1–30 seconds of central processing unit (CPU) time. It expands
saved includes without consulting current Sigma caches, retains original search
options, adds proof-output flags, and writes a replay receipt, proof block, and
named premises. One structural statement parser handles include discovery,
replay and complete premise extraction across whitespace, comments, quoted
strings, and multiline or same-line statements. Unsupported forms fail closed.
The recorded prover family selects its bound installed executable and native
options. E uses `CNFRefutation`; explicit Vampire extraction accepts exactly one
complete `Proof for NAME` block with matching opening and closing names.
`proof_premises(stdout)` retains its E default; use
`proof_premises(stdout, prover="v")` for Vampire. Countermodels export no proof
premises. The exported subset must pass a real replay with the same family
before diagnostics report success.
Extracted premises have no automatic minimality claim.

Supported include syntax is one **unescaped single-quoted pathname**. Every
backslash in an include path is rejected before launch and during strict receipt
inspection, including doubled backslashes and escaped apostrophes. The pinned E
opens escaped filenames differently from generic quoted atoms; rejecting that
ambiguity prevents capture from freezing a different file than the prover reads.
Include selections remain unsupported.

Problem and include paths must also have **no symlink component**, including
directory symlinks and a symlinked root problem. The producer checks lexical
components before normalizing parent steps, then checks them again after the
run. It never resolves a linked file into another directory for capture while
leaving E to resolve nested includes from the lexical directory.

Every accepted capture requires `path_policy="lexical-absolute-no-symlinks-v1"`,
`command_policy="single-problem-allowlist-v1"`, and its native prover family.
Older captures remain historical evidence but are invalid for current proof
gates and require a fresh native invocation. Frozen replay matches normalized
lexical directive paths to
recorded source identities without resolving or reading the original inputs.
Ordinary captures therefore remain replayable after those inputs change, move,
or disappear; only the retained evidence and expected executable bindings are
read. Adding a policy label to an old capture does not repair mismatched paths.

Launch and saved-receipt inspection share an explicit command grammar: exactly
one final absolute problem filename, with no stdin, extra positional input, or
unknown option. E permits `--auto`, `--tstp-format`, `--proof-object`,
`--conjectures-are-questions`, positive inline `--answers=N`, and exactly one
positive inline `--cpu-limit=N`. Vampire permits the native pairs
`--proof tptp --mode casc -t N`, optionally `-qa plain`,
with positive integer `N` and no duplicate pairs. Other flags and alternative
option spellings require a separately verified extension before acceptance.
The trusted invocation also binds the prover family to its expected executable.
This boundary rejects E commands that load another problem before the final one;
binding only that final input's hash cannot freeze the additional theory.

Proof-leaf `file(path, name)` annotations are parsed structurally using the same
name parser as saved formulas. Ordinary names, quoted names with spaces, numeric
names, and quoted names with doubled backslashes are supported and exported as
complete original statements. Escaped apostrophes and unknown escapes in formula
names are rejected: this pinned E maps an escaped apostrophe and a distinct
doubled-backslash name to the same printed proof name. The adapter does not guess
which original name that ambiguous output meant.
Unsupported flags, an executable outside the recorded family, or a changed
executable are refused.

The saved Human/Artifact negative query reproduces `ContradictoryAxioms`. Its E
proof uses four translated premises about `path`, without the conjecture. The
four-line fixture is unsatisfiable without a conjecture; every single-premise
deletion is satisfiable. This establishes an inclusion-minimal contradictory
translated subset. A real Java diagnostic reproduces the cache step adding the
conflicting partial classification. The [fresh source-only diagnostic](cache-inheritance.md)
extends that observation to isolated fragment and complete Merge inputs using
real knowledge base (KB) construction and `buildCaches()`, without manually seeded maps. It does
not reconstruct the complete four-file core or repair inheritance semantics.
See [the source trace and limits](runtime-upstream-report.md).

`runtime.prove(problem, root, timeout=10, *, prover="e", output=None)` runs E by
default, or pinned Vampire with `prover="v"`. Existing positional arguments and
result keys remain; the result also identifies `prover`. It accepts 1–300 CPU
seconds and rejects special-file inputs before launch. `output` is a fresh
repository-local **directory**, with a unique default under `.rikishi/results/`.
The result is read from a capture checked against the pre-execution executable,
family, invocation and input hash. Both families retain their exact supported
command grammar and the existing command/path policies.

`runtime.compare(problem, root, timeout=10, *, output=None)` runs both direct
families into distinct `e/` and `v/` directories. It requires matching retained
problem and transitive include bytes before writing `comparison.json`. It reports
`statuses`, `agreement` (boolean, or null for inconclusive statuses), and
`outcome` (`agreement`, `disagreement`, or `inconclusive`). The comparison certifies
only status agreement on those submitted bytes. It does not establish general
semantic validity of SUMO, full source reasoning, or the proposed FEP
interpretation. Direct parity is separate from the managed Sigma/Vampire route
described above. The ordinary upstream command containing the unsupported
`--output_axiom_names on` option remains rejected; Rikishi selects the verified
fixed custom route rather than rewriting arbitrary native commands.

## Source-bound laboratory and interpreting outcomes

The [inference laboratory](inference-tutorial.md) provides a third, deliberately
bounded route: selected real source formulas are compiled into explicit
first-order logic (FOL) kernels and submitted directly to the installed provers.
It does not route arbitrary source through Sigma or replace the full-profile
diagnostic above.

```bash
uv run --locked --no-sync rikishi inference-catalog
uv run --locked --no-sync rikishi inference-run output/inference --prover both --timeout 10
uv run --locked --no-sync rikishi inference-verify output/inference/inference-report.json --sha256 "$REPORT_SHA256"
```

Use a fresh output directory and an independently retained report digest.
The catalog is experiment design; the report is evidence of a specific retained
run. Its background, positive, negative-query, premise-removal, and explicit
refutation cases have different logical roles. Read actual counts and statuses
from the new report, rather than inheriting a previous acceptance claim.

A satisfiable background has at least one model. Entailment requires every model
to satisfy the conjecture; classical refutation therefore tests the background
plus the conjecture's negation. A countermodel shows non-entailment in that
submitted kernel. It does not establish entailment of the negation. A timeout
establishes neither. An inconsistent background classically entails any query,
so the background control and contradiction context must accompany a theorem.

For E/V comparison, matching source names alone are insufficient: compare exact
problem and include bytes. A timeout in one family and a theorem in the other
is not contradictory semantic evidence. Opposed conclusive statuses on identical
inputs require retaining and investigating both captures, commands, and proof or
model evidence. Agreement remains bounded status agreement. Neither outcome
certifies complete SUMO consistency or a FEP interpretation.

Portable report replay reconstructs the declared problems and checks retained
evidence without starting a solver. Native replay starts a new solver execution.
Neither is an independent proof-step checker. The read-only dashboard and Model
Context Protocol (MCP) tools expose catalog and replay operations only; see
[interfaces](API.md).

## Verification

```bash
uv run pytest tests/runtime
uv run pytest -m 'not integration'
```

Native tests use pinned E and Java to check entailment versus countermodel, the
saved contradiction and all four deletions, capture/replay, tampering,
timeout/interrupt cleanup, and compound guards. The guard regression passes on
patched Sigma and fails with the actual pinned unpatched source class compiled
into an isolated temporary classpath. Canonical checkouts remain unchanged.

Portable tests exercise real files, subprocesses, local Git, and local Hypertext
Transfer Protocol (HTTP);
they do not claim native acceptance. Run the full coverage gate after the full
suite. Compact receipts and proof/core are indexed in
`.omo/evidence/next-pass/runtime.md`; large captures remain ignored under
`.rikishi/results/`. Earlier evidence remains preserved in Git history.

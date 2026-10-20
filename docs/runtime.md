# Operating the SUMO environment

Rikishi separates three layers: the complete pinned upstream source corpus, the
Sigma Knowledge Engineering Environment, and bounded automated theorem proving.
Having downloaded a file is not a proof that its axioms are consistent or that a
query follows from them.

## Installation

Run from the repository on mounted GitVault:

```bash
bash scripts/bootstrap-sumo.sh
uv run python scripts/runtime-sigma.py start
uv run python scripts/runtime-sigma.py status
```

Open <http://127.0.0.1:8085/sigma/KBs.jsp>. The dedicated Tomcat binds to loopback.
Upstream Sigma's local default login is `admin` / `admin`; this installation is
for a single trusted local operator. Configure authentication separately before
any remote deployment. Stop with:

```bash
uv run python scripts/runtime-sigma.py stop
```

For supervised terminals and agent tools, `uv run python scripts/runtime-sigma.py run`
keeps Tomcat in the foreground. The bootstrap explicitly expands the WAR before
queries can create the graph directory, preserving generated graphs while
ensuring an existing partial directory cannot prevent Tomcat deployment.

The bootstrap installs the entire SUMO Git tree at the revision recorded in
`config/sumo.lock.json`, including domain ontologies, mappings, tests, and
development files. Git history is shallow. It also pins SigmaKEE, SigmaUtils,
sigmaAntlr, TPTP-ANTLR, and E. Existing checkouts with different revisions cause
an error, never a reset. Generated working data and compiler outputs live under
ignored `.rikishi/`; upstream SUMO itself remains unmodified.

On Apple Silicon, bootstrap downloads checksum-pinned Temurin Java 21, Ant,
Tomcat, WordNet 3.0, and Vampire 5.1 into GitVault. Other hosts require an external `JAVA_HOME` with
Java 21 or newer. A C compiler and `make` build E from source. The Python wrapper
is run with the project's `uv` environment. Ant's Java user directory and temp
directory are redirected to `.rikishi/runtime`.

The default Sigma configuration is the upstream core and mid-level profile.
The optional `--all-domains` broad profile includes **every top-level `.kif` file** from SUMO. This
includes upstream demonstration subsets such as `tinySUMO.kif`, and produces
duplicate-axiom diagnostics. It is an exploratory union, not a verified mutually
consistent composition. A theorem from an inconsistent union would not be useful
evidence: contradictory assumptions entail arbitrary conclusions. Nested
development proposals and test fixtures remain available in the full corpus but
are deliberately not assertions in that knowledge base. To select the
upstream core profile instead, stop Sigma and run:

```bash
bash scripts/bootstrap-sumo.sh --core-only
uv run python scripts/runtime-sigma.py start
```

The core profile consists of `Merge.kif`, `Mid-level-ontology.kif`,
`english_format.kif`, and `domainEnglishFormat.kif`. The full domain profile
requires appreciably more memory and initialization time. The launcher permits
a 10 GB Java heap; the upstream guide recommends at least 16 GB RAM.

To explore the broad profile, stop Sigma, run
`bash scripts/bootstrap-sumo.sh --all-domains`, and restart. Preserve proof
logs and check whether unrelated negative-control conjectures also become
theorems before interpreting results from this union.

## Layout and provenance

| Location | Purpose |
| --- | --- |
| `config/sumo.lock.json` | Exact source revisions and repository URLs |
| `.rikishi/upstream/sumo` | Untouched full source corpus |
| `.rikishi/upstream/sigmakee` | Upstream Java application and compiled JAR |
| `.rikishi/upstream/eprover/PROVER/eprover` | Real compiled E executable |
| `.rikishi/sigma/core/KBs` | Writable official core profile and generated configuration |
| `.rikishi/sigma/all-domains/KBs` | Separate broad-profile data and caches |
| `.rikishi/runtime` | External JDK, Ant, Tomcat, caches, downloads, temporary files |
| `.rikishi/runtime/environment.json` | Generated environment consumed by launcher |
| `.omo/evidence/runtime` | Build logs and verification receipts |

`rikishi.runtime.status(root)` reads the actual revisions and artifact presence.
It also reports working-tree changes: E's configure step changes its tracked
`Makefile.vars`, while SUMO should remain clean. The bootstrap refuses a dirty
SUMO checkout. The Sigma writable copy has a source-revision marker; a new pin
requires a new profile rather than silently relabeling old working data.
An artifact-presence field does not assert a healthy running service. Use the
HTTP status command and inspect the knowledge-base page after initialization.

## Bounded proof execution

`rikishi.runtime.prove(problem, root, timeout=10)` invokes real E against a TPTP
problem. CPU limits are 1–300 seconds; a wall-clock bound adds five seconds and
kills a blocked process. Returned fields include the command, stdout, stderr,
exit status, and SZS outcome. `proved` is true only for `Theorem`.

`CounterSatisfiable` is a countermodel result for that supplied problem.
`Timeout`, `GaveUp`, or resource exhaustion are inconclusive. A malformed input
without an SZS outcome raises an error. None of these results establishes the
consistency of all SUMO axioms or validates a proposed FEP interpretation.

To submit SUO-KIF through the **actual upstream Sigma translator**, use:

```bash
uv run python scripts/runtime-query.py '(subclass Human Animal)' --prover e --timeout 15
```

Select `--prover v` for Vampire. The command loads the configured Sigma KB,
retains upstream diagnostics in a fresh log, and prints a JSON result containing
SZS status, outcome, consistency status, and the log path. Use `--output` to name
a new log inside the repository; existing logs are never overwritten. The native process has
a separate ten-minute initialization allowance plus its query limit; startup
can be expensive. Stop the browser server before running this command on a
memory-constrained host to avoid two simultaneous 10 GB Java heaps. Upstream
Java may log ontology errors without a nonzero process exit; inspect the proof's
SZS outcome, not merely the shell status.

The local Java adapter generates FOF synchronously before asking E, avoiding
the upstream command-line startup race. A checksum-guarded compatibility patch
in `config/patches/sigma-compound-type-guards.patch` fixes two type-guard
construction sites in Sigma: compound class terms such as `(ExtensionFn Oval)`
must remain expression trees rather than becoming a single atom. Both source
before/after hashes and the patch hash are recorded in `config/sumo.lock.json`.
SUMO ontology data is not patched. The real Java regression fails against the
unmodified Sigma JAR and passes after rebuilding it, for both instance and
subclass guards plus an atomic-type control.

### Observed inference limitation

The installed core profile returned `Theorem` for `(subclass Human Animal)`.
The unrelated `(subclass Human Artifact)` control returned
`ContradictoryAxioms`. This is an observed inconsistency in the current translated
core theory, not evidence that humans are artifacts. The result requires further
upstream diagnosis to distinguish ontology axioms, cached axioms, and translation
semantics. Positive theorem results from this core profile must not be presented
as validated scientific conclusions. Rikishi keeps the raw diagnostics and
returns an explicit `inconsistent_translated_axioms` outcome with exit status 2 when the
prover detects the contradiction. No axioms are silently removed to obtain a
passing result. The separate bounded taxonomic projection has its own clearly
stated scope and negative controls.

Query status is read from a separate JSON file written by the Java adapter from
the actual `ATPResult` (including ATP exit code and stdout count). Mixed
application logs and echoed user queries are never searched for proof status;
a query containing the text `SZS status Theorem` cannot create a successful
result. The regression suite includes that exact spoofing control.

Tests execute the installed prover on a real syllogism, then replace its goal
with a nonentailed predicate and require a countermodel. They also supply invalid
TPTP, a nonexistent installation, invalid timeouts, and a FIFO that blocks reads.
These negative controls ensure successful invocation cannot masquerade as proof.

Run bootstrap before the complete test gate. Tests marked `integration` require
the installed, pinned runtime and fail explicitly if it is absent:

```bash
bash scripts/bootstrap-sumo.sh
uv run pytest
```

For development before installation, `uv run pytest -m 'not integration'`
executes the installation-independent subset; passing that subset is not the
full runtime acceptance gate.

## Troubleshooting

Failed builds retain their logs and source directories. Do not delete the
working corpus to resolve a network error. Check the failed download's checksum,
the pinned revision, and the first Ant/C compiler error. A checksum mismatch
requires explicit investigation; bootstrap does not silently replace the file.

Sigma initialization can take several minutes. Tomcat logs are in
`.rikishi/runtime/apache-tomcat-9.0.123/logs/catalina.out`. Ontology parser or type
warnings are upstream data diagnostics and must remain visible. An HTTP 200
login page alone is not evidence that the knowledge base has finished loading.

## Primary references

- [SUMO source](https://github.com/ontologyportal/sumo)
- [SigmaKEE source](https://github.com/ontologyportal/sigmakee)
- [Official macOS installation](https://github.com/ontologyportal/sigmakee/wiki/MacOS-installation)
- [E theorem prover](https://github.com/eprover/eprover)
- [TPTP SZS ontology](https://tptp.org/UserDocs/SZSOntology/)
# Runtime implementation boundaries

The three repository entry points delegate to importable package modules:
`runtime_setup` installs the pinned native environment, `runtime_query` runs the
Java adapter, and `runtime_server` manages Tomcat. Importing them does not parse
command-line arguments or start a process. `runtime_results` owns the strict ATP
wire contract and result interpretation; it remains in the 90% core coverage scope.
The installation and process-orchestration modules have the separately measured
60% infrastructure floor. Full native tests exercise the installed bootstrap and
an actual Sigma query; portable tests do not claim to exercise those installations.

Every query generates a fresh invocation identifier. The Java adapter writes it
into its exclusively created result sidecar, and Python requires an exact match.
Malformed JSON, coercible string/boolean numbers, missing fields, unexpected
fields, stale identifiers, unfinished Java execution, empty ATP output, and
incompatible ATP exit codes cannot certify a proof. Legacy sidecars remain
readable through the inspection API when no expected identifier is supplied;
the live query command always requires the identifier.

`Theorem` records entailment reported by the translated problem. Its consistency
field remains `not_established`: a successful positive query does not establish
the consistency of its premises. A valid `ContradictoryAxioms` result records
`inconsistent_translated_axioms`, sets `proved` to false, and makes the CLI exit 2.
Failure, timeout, and malformed output remain distinct from a countermodel.

The status command accepts `--url` for a real local HTTP test fixture or an
operator-selected native deployment. Tests own their fixture server lifecycle;
they do not depend on a previously running browser session or Tomcat process.

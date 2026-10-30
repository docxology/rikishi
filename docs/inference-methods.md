# Source-bound native inference laboratory

The Suggested Upper Merged Ontology (SUMO) laboratory runs selected, controlled
logical scenarios against the installed E and Vampire theorem provers. It retains
the exact selected source formulas and complete source file, compiled problems,
executable bytes, implementation sources, native output, and invocation captures.
The versioned authority is `src/rikishi/data/inference-study-v1.json`.

This is a bounded fragment experiment. It establishes the measured consequences
of explicitly selected premises under the declared first-order interpretation.
It supplies no arbitrary SUMO translation, complete-corpus consistency result,
ontology-preservation theorem, or empirical validation.

## Source and interpretation

The source is the pinned `Merge.kif` at commit
`efcd059f8feebfe3488a09f575f88d4d009b1e5c`, with complete-byte Secure Hash
Algorithm 256-bit (SHA-256) digest
`2e4c3d6b8392a4cb6fbeccb6eb7441e11d6b45592082333285c951fd7c7d3e14`.
The source retains its upstream license and attribution; the operator package
does not relicense it. Each catalog selector identifies the starting line of a
complete Standard Upper Ontology Knowledge Interchange Format (SUO-KIF) formula.
The producer reparses the complete pinned file and records the formula's original
text, starting and ending lines, source path, and SHA-256 digest.

The compiler admits fixed-arity predicates, object constants, individual
variables, conjunction, disjunction, negation, implication, equivalence,
universal and existential quantification, and equality. Free individual
variables receive universal closure. The output uses the first-order formula
syntax of Thousands of Problems for Theorem Provers (TPTP). An arity conflict,
string, function term, row variable, invalid quantifier, or unsupported atom
fails explicitly. There is no fallback translation.

Predicate names and object constants use separate injective hexadecimal
namespaces. In particular, `(instance part TransitiveRelation)` classifies the
object named `part`; it does not itself apply the predicate `part`. A source
schema containing a predicate variable is accepted only with a recorded finite
substitution, such as `{"?REL": "properPart"}` for the source transitivity schema
at line 3061. The substitution also replaces its corresponding object-position
occurrences. The resulting guarded first-order formula is retained as compiled
input. Unspecialized predicate variables remain unsupported. This finite source
specialization provides no general higher-order semantics.

The source rule at lines 146–150 directly supplies instance inheritance. For
subclass transitivity, the selected premises additionally classify `subclass`
as a partial ordering, inherit its transitive classification, and specialize the
actual transitivity schema. Generic reflexivity is commented out in this source;
the laboratory does not activate it from documentation.

Constants beginning with `Study` denote synthetic witness assumptions. These
assumptions are listed separately from source selections. Other scenarios use
actual source individuals, including `Red`, `North`, and `True`. The language has
no unique-name or closed-world assumption. Explicit inequalities matter, and
existential witnesses need not be named or unique. Integer tokens in domain
metadata are uninterpreted objects; no arithmetic is introduced.

## Competencies and controls

The catalog spans subclass paths, synthetic and source-individual inheritance,
mereology, spatial and family relations, existential consequences, domain and
relation metadata, class disjointness, identity constraints, and finite relation
specializations. For example, source `parent` arguments are child then parent.
The domain scenarios establish metadata propagation; they do not infer an
argument's class membership merely from a domain declaration.

Each scenario generates five problems for each selected prover:

| Problem | Required observed status | Purpose |
| --- | --- | --- |
| Background without conjecture | `Satisfiable` | Establish consistency of the selected premises before crediting entailment |
| Positive query | `Theorem` | Establish the declared consequence of those premises |
| Reversed, unrelated, or opposed query | `CounterSatisfiable` | Reject indiscriminate query success |
| Positive query after one declared premise removal | `CounterSatisfiable` | Demonstrate dependence on a selected premise |
| Background plus negated positive query | `Unsatisfiable` | Observe the corresponding refutation with no conjecture |

The producer executes the background first. It credits a case only when the
expected status matches and the same scenario's background under the same
prover was `Satisfiable`. A timeout or resource outcome is unresolved, never a
countermodel. A contradiction in the unmodified background blocks all successful
case flags. Missing cases, changed expected polarities, and any failed control
block replay acceptance. The failed campaign and its native captures remain on
disk; the runner raises after retaining a completed failing report when possible.

## Running and replaying

Run from the canonical mounted checkout, after the supported environment setup:

```bash
source scripts/env.sh
uv run --locked --no-sync rikishi inference-catalog
uv run --locked --no-sync rikishi inference-run NEW_OUTPUT --prover both --timeout 5
uv run --locked --no-sync rikishi inference-verify NEW_OUTPUT/inference-report.json \
  --sha256 INDEPENDENTLY_RECORDED_REPORT_DIGEST
uv run --locked --no-sync rikishi inference-publish NEW_OUTPUT/inference-report.json \
  --sha256 INDEPENDENTLY_RECORDED_REPORT_DIGEST
```

`inference-publish` registers the run for the dashboard after verification. It
strictly replays the report, then atomically writes the local
`output/inference/published.json` descriptor while preserving any differing
previous descriptor. Registration is required for the published dashboard view
and never invokes a prover.

The output's parent must already exist; the output must be fresh and inside the
repository. Both installed prover families use the existing bounded native
`runtime.prove` and capture application programming interfaces (APIs). Execution binds the source, lock, implementation,
binary, submitted problem, process invocation and captured outputs. The producer
rechecks live inputs after the campaign and verifies its retained report.

Portable replay requires an independently supplied outer report digest. It
rederives the packaged study, complete retained source, all source locators,
every controlled problem, captured output interpretation, per-family background
controls and aggregate counts. It verifies retained implementation and executable
bytes and rejects unsafe paths, changed captures and corrupted stdout or stderr.
The replay implementation must match the campaign's bound implementation.
An altered implementation requires a fresh campaign, not receipt rewriting.

A JavaScript Object Notation (JSON) document is not verified merely because it parses. The importable
`validate_inference_report(path, trusted_report_sha256=...)` requires the digest
and completes all replay checks before returning. A checksum stored beside a
report is a recorded binding; its independence must be supplied by the caller's
custody procedure. Portable replay does not authenticate historical process
execution or independently validate each proof step. E and Vampire agreement
is measured agreement on identical generated inputs, not proof of semantic
preservation or complete SUMO consistency.

The [manuscript reproduction guide](manuscript.md) gives the complete ordered
publication prerequisites, canonical input/staging paths and independent digest
handoff. That source-kernel campaign is separate from the finite-alignment E and
Vampire campaigns and the cache diagnostic. For inspecting individual source
selections and controls, follow the [inference tutorial](inference-tutorial.md).

## Importable interfaces and tests

`inference_study.catalog()` returns the typed authority;
`inference_runner.run_inference(root, output, prover="both", timeout=5)` produces
the retained report; `inference_replay.validate_inference_report` supplies strict
digest-bound portable replay. Thin command-line, dashboard and Model Context
Protocol (MCP) interfaces consume these shared methods.

The focused tests use actual source bytes, real files and native processes.
Compiler and preflight tests exercise unsupported syntax, malformed selectors,
source drift, invalid resource bounds and absent binaries. Native campaign tests
require every polarity and paired background control. Mutation tests operate on
copies of authentic packets and reject changed source, study, problems,
implementation, binary, lock, capture, proof output, status, polarity and summary.
They recompute the outer digest in internal-consistency controls so rejection
cannot be explained only by the outer checksum.

An explicit `RIKISHI_INFERENCE_TEST_PACKET` and
`RIKISHI_INFERENCE_TEST_SHA256` can select a previously produced packet for focused
replay tests. Without them, the native test fixture produces a fresh both-prover
campaign. Missing inputs or native tools fail visibly; no historical-output
fallback, mock prover, or automatic skip is used.

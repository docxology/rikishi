# From a source formula to a defensible inference claim

This laboratory explains selected rules of the Suggested Upper Merged Ontology
(SUMO) using real native prover runs. It retains the Standard Upper Ontology
Knowledge Interchange Format (SUO-KIF) source and constructs explicit first-order
logic (FOL) problems from a declared supported fragment. Automated theorem proving
(ATP) then tests a conjecture and its controls. The laboratory is separate from
Sigma's full-profile preprocessing and translation, the navigation graph, and
the finite Active Inference alignment study.

Read [runtime setup](runtime.md) before executing native commands. For definitions
and common interpretation mistakes, keep the [glossary](glossary.md) nearby.
The study authority is packaged in
[`inference-study-v1.json`](../src/rikishi/data/inference-study-v1.json); the
catalog command reports the current supported selection, assumptions, and scope.
This guide teaches how to inspect results, rather than asserting that a command
has already completed successfully on the reader's machine.

## Start with the question, background, and encoding

An inference experiment needs three distinct objects:

1. **A source selection.** Which pinned files and complete formulas supply the
   intended rule? Preserve their bytes, locations, and revision.
2. **A problem background.** Which translated source formulas and explicit local
   assumptions are submitted to the prover? A teaching witness is an added
   assumption, not a newly discovered source assertion.
3. **A conjecture.** What exact sentence should follow, or should remain
   underdetermined, under that background?

For a background theory `T` and conjecture `q`, satisfiability asks whether at
least one interpretation makes every sentence of `T` true. Entailment asks whether
every model of `T` also makes `q` true. Refutation tests entailment by checking
whether `T` together with `not q` is unsatisfiable. This is a statement about the
submitted problem. A source-to-target preservation argument is a further task.

The distinction matters when the background is inconsistent. If `T` has no
model, it classically entails every conjecture. A prover can therefore derive an
unwanted claim without making an inference error. Testing the background without
the conjecture and retaining the contradiction diagnostic prevents a bare
`Theorem` label from being mistaken for a useful ontology validation.

## Establish the actual environment

Run from the checkout on mounted GitVault:

```bash
source scripts/env.sh
uv run --locked --no-sync python -c 'import sys; print(sys.prefix); print(sys.base_prefix)'
uv run --locked --no-sync rikishi doctor
uv run --locked --no-sync rikishi verify-source
uv run --locked --no-sync rikishi inference-catalog
```

Both Python prefixes must resolve on the external volume. Follow the runtime
guide to install missing pinned tools; a catalog read does not install a prover.
The source audit compares the index snapshot with current files. The laboratory
also binds its own declared source authority; indexing a different corpus does
not silently change the registered experiment.

The command-line interface (CLI) prints JavaScript Object Notation (JSON). Read
the catalog's source identity, semantic scope, supported syntax, selected source
lines, predicate bindings, assumptions, queries, and removal choices before
launching anything. Fixed predicate instantiation is explicit. A selected rule
does not license translation of every higher-order or modal construction.

## Inspect real symbols before using them

```bash
uv run --locked --no-sync rikishi term ProbabilityFn
uv run --locked --no-sync rikishi term UnaryFunction
uv run --locked --no-sync rikishi term agent
uv run --locked --no-sync rikishi term AutonomousAgent
uv run --locked --no-sync rikishi formulas --path Merge.kif --term ProbabilityFn
uv run --locked --no-sync rikishi graph ProbabilityFn --relation instance
```

A symbol is a token occurring in source expressions; the index's symbol count is
not a count of individuals or independently true facts. The pinned source
classifies `ProbabilityFn` as an instance of `UnaryFunction` and makes
`UnaryFunction` a subclass of `Function`. The membership rule can consequently
propagate that classification. It would be a different assertion to make
`ProbabilityFn` a subclass of `Function`.

SUMO also uses class and relation symbols as arguments of other relations. This
metamodeling is why an ontology entity can be discussed both through its members
and through its own classification. Do not force every token into exactly one
of “class,” “relation,” or “individual” based on its spelling. In particular,
lowercase `agent` names a relation; `AutonomousAgent` names a class. Their similar
English vocabulary does not make their arguments interchangeable.

## Follow the inference path

| Stage | What to inspect | What it does not establish |
| --- | --- | --- |
| Pinned source | Complete formula, file, line, revision, content fingerprint | Correctness of a translation |
| Declared kernel | Selected formulas, fixed predicate bindings, local assumptions | The complete source theory |
| Generated problem | Named axioms and conjecture in Thousands of Problems for Theorem Provers (TPTP) syntax | General preservation of SUO-KIF semantics |
| Native execution | E or Vampire, executable identity, arguments, time budget, stdout and stderr | Independent correctness of every proof step |
| Checked capture | Input and include bytes, invocation binding, status and hashes | Background consistency without its own control |
| Portable replay | Rederived problems, retained dependencies, interpreted outcomes | A new native execution or authenticated history |

For a **full Sigma query**, the path instead includes its configured source
profile, serialized inputs, cache initialization, preprocessing, translation, and
include assembly before E or Vampire executes. Those inputs can differ from
both the indexed corpus and the laboratory kernel. The [runtime guide](runtime.md)
documents their capture and the known contradictory-background investigation.
An index search or shortest source path is a separate navigation operation; it
does not invoke either reasoning path.

## Run and read the laboratory

```bash
uv run --locked --no-sync rikishi inference-run output/inference --prover both --timeout 10
```

Use a new destination for another run, such as `output/inference-repeat`.
`--prover e` selects E alone; `--prover v` selects Vampire alone. The timeout is
a per-problem native budget, not an assurance that the entire campaign finishes
within that many seconds. Inspect the retained `inference-report.json`, source
claims, generated problems, and captures together. Derive current scenario and
native-run counts from that report, including mismatched and unresolved cases.

The catalog defines related controls around each selected consequence:

| Control | Question | Expected kind of evidence |
| --- | --- | --- |
| Background | Can the selected premises jointly hold without a conjecture? | `Satisfiable` |
| Positive | Do those premises entail the declared query? | `Theorem` |
| Negative query | Can a deliberately stronger, reversed, or otherwise unsupported query be false? | `CounterSatisfiable` |
| Removed premise | Does the positive query cease to follow after the declared premise is removed? | `CounterSatisfiable` |
| Explicit refutation | Are the premises plus the negated positive query inconsistent? | `Unsatisfiable` |

These expected polarities are study design, not substitutes for observed native
statuses. A negative query need not be the logical negation of the positive query;
read its actual formula. Removing one premise tests the registered dependency.
It does not establish that the entire selected theory is globally minimal.

### Membership is different from specialization

The source membership rule has the form:

```lisp
(=> (and (subclass ?C ?D) (instance ?X ?C)) (instance ?X ?D))
```

This display explains the rule's shape; the retained full source formula and its
explicit quantifiers are authoritative. Inspect the selected classification facts
and the generated positive conjecture. Then compare its removed-premise problem:
which membership or inclusion link was removed, and why can a model now fail the
conjecture? If the positive remains entailed, that removal has not demonstrated
the intended dependency.

### Argument domains constrain uses of a relation

The source signature for `agent` constrains its process argument and its
autonomous-agent argument. A laboratory assumption using a teaching process and
agent can exercise the selected domain rule. The local witness names are not
asserted upstream entities. Verify that the generated consequence concerns
membership of the appropriate argument. Reversing the arguments or replacing
membership with subclassing changes the obligation.

This `agent` inspection explains source signatures; it is not a claim that the
laboratory executes that particular function- or relation-application example.
The registered `daughter-domain` and `son-domain` scenarios instead test source
metadata inheritance through `subrelation` and the parent's `domain` assertions.
Inspect those actual catalog entries before interpreting their native results.

Signature declarations do not create all possible relation tuples, and a missing
tuple does not mean its negation holds. Likewise, `domainSubclass` constrains an
argument as a subclass rather than as an ordinary instance; flattening the two
relations into a generic “type” edge would change the problem.

### Relation properties and existential witnesses need their own rules

The `proper-part-forward`, `proper-part-asymmetry`, and `proper-part-converse`
scenarios separate different consequences of the retained mereological formulas.
The `mother-parent` scenario uses the source order: child first, mother second.
The `proper-part-transitivity` and `ancestor-transitivity` scenarios record a
fixed predicate binding for the selected source schema. Read those bindings and
the local assumptions rather than assuming every visible relation is transitive.

The `organism-parent-witness` case distinguishes a required existential parent
from an arbitrary named parent. Its positive query asks whether some parent
exists; its negative query names an otherwise unconstrained individual. The
`contains-witness` and `physical-spacetime-witness` cases make analogous
existential obligations explicit. A proof of existence need not identify a
particular source name.

Functions require another boundary. `range` and `rangeSubclass` distinguish
ordinary result membership from subclass constraints, but this laboratory's
target is function-free. It does not execute arbitrary function terms or
validate their general translation. Inspecting `ProbabilityFn` as a source
entity is different from compiling a term that applies it to a formula.
Numerals are uninterpreted constants; no arithmetic or unique-names convention
is silently imported. None of these distinctions is obtained merely by drawing
neighboring symbols in a diagram.

## Interpret non-entailment under an open-world reading

A countermodel of `T` with `not q` establishes that `T` does not entail `q`.
It does **not** establish that `T` entails `not q`: some other model may satisfy
both `T` and `q`. To investigate entailment of the negation, submit that separate
conjecture with its own evidence. Failure to find a proof within a budget
establishes neither conclusion.

Similarly, an absent source edge, an empty search result, or a missing direct
taxonomy path establishes no negated assertion about the complete ontology.
Another rule or file may matter. A graph traversal that exhausts its budget
does not even establish absence in the selected direct graph. The
[analysis contract](ontology-analysis.md) distinguishes exhaustive graph absence
from traversal limits.

Result labels follow the [standardized SZS result ontology](https://szs.tptp.org/).
`Theorem` and `CounterSatisfiable` are conjecture-oriented; `Satisfiable` and
`Unsatisfiable` concern a problem without a conjecture. `Timeout`, `GaveUp`, a
process failure, or invalid evidence must remain inconclusive or failed. Do not
relabel them as the desired polarity.

## Compare E with Vampire

Compare matching case identifiers and retained problem hashes first. Different
problems or backgrounds cannot establish prover disagreement about one theory.
For identical problems, a timeout from one prover and a theorem from the other
is unequal search performance, not contradictory semantic answers. A theorem
and a countermodel claim on those same bytes require investigation of captures,
status interpretation, commands, tool versions, and ultimately proof/model
evidence. Do not choose the answer that fits the intended example.

Agreement adds a bounded independent implementation comparison. It does not
prove both implementations correct, validate Sigma translation, or establish
consistency of all SUMO. Preserve disagreement and unresolved cases in the
summary rather than dropping their denominator.

## Preserve the result and replay it

Obtain the report's Secure Hash Algorithm 256-bit (SHA-256) fingerprint, retain it
outside the mutable report bundle, and preserve the complete output directory.
For a locally created run:

```bash
shasum -a 256 output/inference/inference-report.json
read -r REPORT_SHA256
uv run --locked --no-sync rikishi inference-verify output/inference/inference-report.json --sha256 "$REPORT_SHA256"
uv run --locked --no-sync rikishi inference-publish output/inference/inference-report.json --sha256 "$REPORT_SHA256"
```

Enter the independently retained hexadecimal digest at `read`. Computing a new
digest from an untrusted received bundle only identifies those received bytes;
it does not authenticate the original producer. Portable verification reconstructs
the declared problems and checks retained evidence. It does not rerun E or
Vampire, and it does not independently certify every native proof inference.

`inference-publish` registers the verified run for the dashboard. It performs
strict replay, then atomically writes the local `output/inference/published.json`
descriptor while preserving any differing previous descriptor. This local
registration is required after a new run for the published dashboard view;
it never invokes a prover or publishes to an external service.

For a new native reproduction, run the same study into another fresh output
directory and compare source, study, tool, problem, status, and invocation records.
For an adversarial evidence test, work only on a separate copy: change a retained
problem while keeping the original trusted report digest. Replay must reject the
alteration. Preserve accepted evidence unchanged.

## Inspect through the read-only interfaces

Open the dashboard at `/#proof-lab`. Its catalog describes the experiment; a
separately pinned published report describes a retained run. The Hypertext
Transfer Protocol (HTTP) routes are `/api/inference/catalog` and
`/api/inference/report?report=output/inference/inference-report.json&sha256=DIGEST`.
The Model Context Protocol (MCP) tools are `inference_catalog` and
`inference_verify_report(report, sha256)`. Report paths must remain contained in
the repository. Missing reports and failed replay remain explicit errors.
None of these interfaces starts a prover.

Click a scenario in `#proof-lab` to inspect the actual submitted problem and
retained native proof output for its registered cases. The read-only route
`/api/inference/case?report=RELATIVE&sha256=DIGEST&case_id=REGISTERED_CASE_ID&prover=e`
returns the verified case, exact problem text, native stdout/stderr, command,
and proof-step-checking boundary; choose `e` or `v`. The corresponding agent tool
is `inference_inspect_case(report, sha256, case_id, prover="e")`.
`/api/inference/published` returns the descriptor `{report, sha256}`, validated
report, and local-digest authority text. Its locally published fingerprint does
not replace independent digest custody when transferring a bundle.

A useful handoff states the conjecture, background, selected source revision,
encoding, expected and observed statuses, controls, native family and budget,
report fingerprint, and replay boundary. Keep that bounded claim attached when
moving from a worked example to a research interpretation.

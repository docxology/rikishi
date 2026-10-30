# Concrete finite mathematical and ontology bridge

The Free Energy Principle (FEP) bridge uses one declared set of rational, two-state witnesses in three
different obligations: concrete Lean definitions and proofs, finite Python
calculations, and selected Suggested Upper Merged Ontology (SUMO) reasoning
problems. Stable witness and entity identifiers join these observations. A join
records which inputs were used; it supplies no theorem that the interpretations
preserve one another.

The authority is
[`fep-sumo-bridge-v1.json`](../src/rikishi/data/fep-sumo-bridge-v1.json).
`bridge_study.catalog()` returns its frozen `BridgeStudy`. Each witness declares
an exact rational prior, likelihood for the observed outcome, and candidate law.
Vector index 0 denotes `Bool.false`; index 1 denotes `Bool.true`. The observed
outcome is `true`. The binary observation kernel assigns the complementary
likelihood to `false`, so each row is a normalized law. All declared masses and
complements are strictly positive.

For an accessible walkthrough before these method details, read
[how SUMO, FEP_Formal and simulations connect](sumo-fep-simulations.md).
The example separates ontology roles, finite mathematics, numerical execution
and the persistent-state generator without adding an execution claim.

## Concrete formal obligations

The existing FEP_Formal pin is
`9a0694f16b8e89b66b2f7f8cc7426c650dd2c4de`. Its committed
`finite_probability.lean` defines `FEP.FiniteLaw`, `FEP.FiniteKernel`, predictive
mass, posterior, and `posterior_mul_predictive`. Its committed
`finite_information.lean` supplies `finiteKL_nonneg`, `finiteKL_self`, and
`finiteKL_eq_crossEntropy_sub_entropy`. The compiler reads committed bytes at
that revision even when the canonical checkout has advanced.

The producer generates `lean/BridgeWitnesses.lean` with a namespace for each
witness. It constructs actual normalized `FiniteLaw Bool` priors and candidates,
and `FiniteKernel Bool Bool` likelihood kernels. Concrete proofs establish the
rational evidence and every posterior atom, positive evidence and posterior
support, posterior reconstruction, nonnegative Kullback-Leibler (KL) divergence,
self-divergence zero, and the supported cross-entropy decomposition. The latter
uses the actual pinned theorem with its positive-reference assumption proved
for the generated posterior. Identifier definitions retain the same model,
source representation, calculation, result-record, and agent labels used in the
logical scenarios.

Compilation uses `formal_verification.verify_formalization` and isolated compiler
workspaces. The canonical formalization, compiler installation, and dependency
caches remain read-only inputs. The packet retains committed finite-module
bytes, generated source, compiled module artifacts, compiler output, exact
commands, declaration-axiom reports, pinned dependency metadata, and complete
compiled-library snapshot digests. Only the existing allowed foundational Lean
axioms are admitted. Invalid normalization, an incorrect posterior assertion,
and an admitted proof are separate real compiler rejection controls.
Each rejection has a paired well-formed proof under the same imports, retained
in `report.lean.environments`; it must compile with exit zero and permitted
axioms. A negative control must produce its specific proof or admission
diagnostic. Missing imports, resource failures, and unrelated compiler errors
are not accepted as proof rejection.
Lean command receipts record their actual elapsed time and compiler timeout;
the base verifier records its per-command timeout and total elapsed time. These
budgets are separate from the E and Vampire (E/V) processor time limit selected
by `run_bridge(timeout=...)`.

The generated proofs concern rationally defined real laws and the stated Lean
expressions. They do not prove Python floating-point rounding, the execution of
a historical compiler process, a SUMO translation theorem, or biological claims.
The pinned real-valued KL definition has totalized division conventions at zero
reference atoms. This study proves strict reference support before using its
logarithmic identity; it makes no claim about an extended-real divergence on
disjoint support.

## Numerical obligations

`bridge_study.exact_posterior` uses rational arithmetic to derive evidence and
posterior atoms. `bridge_study.numerical` executes the existing
`fep.free_energy` implementation on the float projections of those inputs. An
independent high-precision Decimal calculation starts from the exact rational
fractions and directly evaluates products, normalization, and natural logarithms.

Each numerical row retains both results, exact rational evidence and posterior,
maximum reference error, exact posterior reconstruction residuals, and the
authority's tolerance. The free-energy decomposition residual is measured in
Python and independently in Decimal. A positive-support KL check and the
free-energy bound are additional finite numerical checks. These measurements
are distinct from the generated Lean obligations; numerical agreement does not
turn the Python implementation into verified Lean code.

## Exact source kernels and local interpretation

### Shared witnesses as a publication interface

The manuscript's three visual introductory pages are derived from the verified
bridge export, not separately typed scientific results. `witness_abstracts`
renders source commitments, exact finite examples, and the distinct
model/representation/calculation/result roles. The retained
`witness-abstracts.json` records the outer report digest, every rational witness,
the actual source claims, and numerical records. Publication verification
independently compares these with the replayed bridge packet. Native page checks
require the three actual canonical images on physical Portable Document Format
(PDF) pages 2, 3 and 4.

For example, the uniform and biased prior witnesses both produce posterior
`(1/4, 3/4)`, while their evidences are respectively `1/2` and `2/3`. Equal
posteriors do not identify equal models. The exact-candidate witness has posterior
`(6/7, 1/7)` and evidence `7/12`; its candidate already equals that posterior.
The source report, exact Fraction products, Lean instances and independent
Decimal comparisons retain different obligations for the same case.

The concrete representation consequence uses the two source rules below the
`representsInLanguage` and `representsForAgent` declarations. An existentially
supplied representing agent need not be the study's named agent; neither the
reverse representation nor equality of referents follows. Similarly, source
`ContentDevelopment` guarantees some content-bearing output under that local
premise, rather than the study's particular named numerical record. These
distinctions are illustrated by the existing unsupported-query and
premise-removal scenarios, not new unexecuted outcome claims.

The expanded manuscript compares this claim/evidence interface with
[PROV-O's qualified provenance](https://www.w3.org/TR/2013/REC-prov-o-20130430/)
and [ologs' typed paths](https://doi.org/10.1371/journal.pone.0024274).
These are scholarly design comparisons. No cross-ontology equivalence, PROV
implementation or commuting semantic interpretation is claimed.

The complete retained `Merge.kif` is pinned at SUMO revision
`efcd059f8feebfe3488a09f575f88d4d009b1e5c`, Secure Hash Algorithm 256-bit (SHA-256)
`2e4c3d6b8392a4cb6fbeccb6eb7441e11d6b45592082333285c951fd7c7d3e14`.
Each selected complete formula retains its original path, start and end lines,
raw text, and digest. `extension.kif` separately retains the authored local
interpretation and witness facts. Every generated problem also contains the
same witness's exact rational numerator and denominator labels. These labels
are uninterpreted objects in first-order logic (FOL); they assert no arithmetic.

Each witness has five source-constrained scenarios:

| Scenario | Source obligation | Explicit local input |
| --- | --- | --- |
| Model | Instance inheritance at 146–150 and `Proposition` beneath `Abstract` at 4506 | A finite model is assigned the local `Proposition` interpretation |
| Representation | 5589–5592 yields an existential representing agent; 5572–5574 yields `represents` | The generated source representation is declared to represent the model in a local language |
| Calculation | 15484, 13421, 13390 and instance inheritance derive `Process` | The calculation is assigned the local `Calculating` interpretation |
| Named result role | 3264 disjoins `result` and `instrument`; 3132, 4409, 3304, 3209 and inheritance classify the relations as predicates | The declared numerical result record is related to its calculation, and a local binary disjointness rule is supplied |
| Output existence | 16326–16331 requires some content-bearing result of a `ContentDevelopment` process | The same calculation is explicitly classified as `ContentDevelopment` in this scenario |

The named result-role rule is a manually authored, fixed binary instance of the
row-variable disjointness schema at 489–495. That complete upstream schema is
retained as context. The existing strict compiler rejects row variables; it
compiles only the explicit local binary rule. This experiment therefore does
not claim a general row-variable translation.

The output-existence scenario has its own assumptions. It includes neither the
named `result(calculation, record)` tuple nor the local rule deriving that tuple.
Its unsupported alternative asks whether the source identifies its existential
output with the named numerical record. A countermodel establishes that this
identification does not follow. The other scenarios' assumptions are never
implicitly pooled with this scenario's background. SUMO does not make an
arbitrary Python computation a psychological or content-development process;
those classifications are visible local choices.

All problems reuse `inference_compiler.Compiler` and the existing controlled
inference-case generator. Unsupported terms, function applications, strings,
arities, row variables and unspecialized predicate variables fail explicitly.
The bridge adds no permissive translator. It equates neither SUMO
`conditionalProbability` with the numerical posterior nor SUMO `LogFn` with
Lean/Python natural logarithms. Calculus and logarithm arithmetic are outside
these FOL kernels.

For every scenario and each selected E or Vampire theorem prover, the retained campaign requires:

| Case | Expected observed status |
| --- | --- |
| Background without conjecture | `Satisfiable` |
| Declared consequence | `Theorem` |
| Unsupported alternative | `CounterSatisfiable` |
| Consequence after one declared source-premise removal | `CounterSatisfiable` |
| Background with negated consequence, without conjecture | `Unsatisfiable` |

A case is credited only with a satisfiable background for the same scenario
and prover family. `CounterSatisfiable` establishes non-entailment, not
entailment of the negation. A timeout or resource outcome remains unresolved.
E/V agreement concerns identical submitted bytes, not complete SUMO consistency
or preservation of SUMO's intended semantics.

## Execution and portable replay

After the repository's external environment setup, native production is explicit:

```python
from pathlib import Path
from rikishi.bridge_runner import run_bridge

report = run_bridge(Path.cwd(), Path("output/bridge"), prover="both", timeout=10)
```

The output must be fresh and repository-local, with an existing parent. The
producer writes `bridge-report.json`, retained inputs, numerical manifest,
generated Lean evidence, problems, and strict native captures. It binds the
implementation, source and dependency locks, and prover executable bytes, then
rechecks live inputs before final replay. Failed executions remain available
for inspection. Report summary counts derive from retained rows and outcomes;
catalog sizes alone are not successful-run counts.

Portable replay requires a separately retained SHA-256 digest:

```python
from rikishi.bridge_replay import validate_bridge_report

checked = validate_bridge_report(
    Path("output/bridge/bridge-report.json"),
    trusted_report_sha256=independently_retained_digest,
)
```

Replay rederives the authority, exact source claims, rational and numerical
manifests, authored extension, generated Lean and control source, all FOL
problems, captured status interpretation, paired backgrounds, polarities, and
summary. Changing a reported numerical value or generated proof and supplying a
new outer digest does not bypass these reconstruction checks. Exact native
command grammars, problem bytes, executable bindings, captured stdout/stderr,
resource limits, and status/exit agreement use the existing runtime rules.

Saved Lean artifacts, logs, commands, axiom reports, and dependency-identity
receipts are checked for internal consistency. Portable replay does not run
Lean again. Full external imported-artifact and compiler bytes are not retained
in the portable packet, and their recorded historical identities are not
independently authenticated by replay. It also does not authenticate historical
process execution or independently check automated theorem proving (ATP) proof steps. The outer digest's
independence comes from the caller's custody procedure.

The full native test fixture creates a new both-prover campaign by default.
Only an explicit `RIKISHI_BRIDGE_TEST_PACKET` and matching
`RIKISHI_BRIDGE_TEST_SHA256` pair selects an existing packet for scoped replay
tests. Reuse does not exercise the producer or constitute a fresh native run.
The pure study tests use no native fixture. Root-owned interface, figure,
publication and repository acceptance gates remain separate.

## Derived finite representation experiments

`finite_channels` adds exact `Fraction` laws and row-stochastic channels, exact
Bayesian conditioning, and Decimal relative entropy. These are mathematical
methods with their own tests; they do not extend the registered v1 native
scenario count or the retained Lean declaration list. `witness_research` derives
four state-channel experiments per existing witness, half-evidence observation
models, noisy-observation posteriors, and an explicitly conditional repeated
observation prediction. `witness_research_figures` produces two Portable Network
Graphics (PNG) and Scalable Vector Graphics (SVG) figure pairs and
`witness-research.json`, a JavaScript Object Notation (JSON) data export.

Rows index input states, columns output states. For a common channel `T`, the
analysis checks `p'=pT`, `j'=(pK)T`, `K'=j'/p'` on positive prior support, and
`posterior'=posterior*T`, with unchanged evidence. The induced likelihood uses
the prior weights. Identity and state swap preserve KL; noise can reduce it;
erasure can make a wrong fine candidate indistinguishable from its reference.
This is not an inference-improvement certificate. A channel on observations
instead changes the conditioning event and generally changes the posterior.

Half-evidence scaling changes only the selected likelihood column and completes
the other Boolean observation outcome. It halves evidence and preserves the
posterior, while surprise and free energy for a fixed candidate increase by
`log(2)`. Repeated-observation predictions additionally assume the same latent
state and conditionally independent observations given that state and model.
Those assumptions are explicit constructed analyses, not inherited native facts.

`verify_witness_research` reconstructs every exact and Decimal field against the
caller-supplied, replay-verified bridge report and its independently retained
digest. It rejects altered posterior, evidence and source identity even when
the JSON is well formed. Publication verification also requires every generated
table row in all editions and exact PNG/SVG/JSON copies across publication roots.
The existing ATP polarities, source contexts, native deadlines, proof custody,
and 90/60 coverage floors remain unchanged.

## Sequential dynamics and forward simulation

`witness_dynamics` derives a second explicit experiment from the same validated
three witnesses. A hidden state persists within a trajectory; the fixed kernel
generates conditionally independent observations. For an all-true prefix of
length `n`, direct rational products give `Z_n=sum(p_s*L_s**n)` and
`r_n(s)=p_s*L_s**n/Z_n`. A separate iterative Bayes route must give exactly the
same posterior and product of predictive probabilities for every `n=0..12`.
Redrawing the state would give a different experiment (`Z_1**n`).

For each witness, 65,536 seeded forward trajectories retain integer prefix and
false-state counts. State is sampled once per trajectory, and all twelve
observation draws are consumed even when the prefix has failed. The algorithm
uses integer Bernoulli draws against exact rational probabilities; the export
records the generator, seed and each witness's seed offset. It reports observed
Monte Carlo ratios without confidence bounds or an empirical-validity claim.

`verify_witness_dynamics` recomputes both the exact route and the complete seeded
simulation. The publication verifier requires the n=2 table in every edition,
the bound `witness-dynamics.json`, and byte-identical PNG/SVG/data copies across
all three publication figure roots. The new `witness-sequential` figure displays
state posteriors, next-observation probabilities, exact versus simulated prefix
evidence and equal-prior uniform/biased model weights. It does not add a SUMO
scenario or a Lean declaration. The dense three frontmatter abstracts retain
their physical page order, exact source/case bindings and print typography.

## Mixed histories and model uncertainty

`witness_sequences` accepts the complete Boolean observation kernel and any
declared Boolean history up to 1,024 observations. For each prefix, it compares
direct joint powers with iterative Bayes and retains the exact evidence,
posterior and both next-observation probabilities. False outcomes use the
kernel's actual false column. The empty history is not an observation; impossible
conditioning rejects instead of inventing a law.

`compare_sequence_models` accepts explicit model priors or a documented uniform
prior. It normalizes prior-weighted history evidence, separately from each
model's hidden-state posterior. Individually impossible models have zero weight;
an impossible overall mixture rejects. The predictive mixture uses the updated
model weights. This is conditional inference within the supplied model set,
not a calibration result or an empirical endorsement of that set.

The publication atlas enumerates all eight length-three histories for the
registered three models. Its complete JSON retains all 24 rows, the original
witnesses, exact redrawn-state alternatives and the declared U/B comparison.
All histories with equal outcome counts have the same final answers under the
fixed-state model, although their intermediate updates can differ. Numerical
verification rederives all fields and requires each checkpoint table row and
every PNG/SVG/JSON copy in the actual editions.

The optional binomial diagnostic supplies a model-based variance `p(1-p)/N`,
not a confidence interval or pass threshold. Separate trajectories provide
independent indicators for a fixed prefix; multiple prefixes of one trajectory
are correlated. Simulation, mathematical identities, source-role consequences
and formal proof receipts retain their distinct scopes.

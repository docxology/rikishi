# Glossary and evidence interpretation

Use this guide with the [inference tutorial](inference-tutorial.md). Definitions
describe Rikishi's interfaces and evidence boundaries; they do not assert that
every installed ontology profile is consistent or semantically preserved.

## Names and abbreviations

| First-use form | Meaning in this project |
| --- | --- |
| Suggested Upper Merged Ontology (SUMO) | The pinned upstream ontology distribution; distinguish its entire source tree from selected reasoning profiles |
| Standard Upper Ontology Knowledge Interchange Format (SUO-KIF) | The source authoring language; a `.kif` filename is not evidence that its content has a sound first-order translation |
| automated theorem proving (ATP) | Native automated proof search over a specified problem; it requires an explicit background, conjecture, tool identity, and budget |
| first-order logic (FOL) | The laboratory's declared logical target; its selected supported fragment is smaller than unrestricted source-language expressiveness |
| Thousands of Problems for Theorem Provers (TPTP) | The problem-language ecosystem used for retained prover inputs; inspect the actual generated syntax and formula roles |
| Model Context Protocol (MCP) | Agent transport for read-only source inspection and report verification |
| command-line interface (CLI) | Shell entrypoint adapting shared methods; errors and incomplete campaigns remain nonzero outcomes |
| Hypertext Transfer Protocol (HTTP) | Transport for the loopback dashboard and its read-only application programming interface (API) |
| JavaScript Object Notation (JSON) | Structured format for catalogs, reports, and receipts; valid syntax alone does not validate the contained claims |
| Free Energy Principle (FEP) | The broader research connection motivating a separate finite variational illustration; no ontology equivalence is established |
| Kullback-Leibler (KL) divergence | Distribution-relative information divergence; always name both distributions and the logarithm convention |
| Java Development Kit (JDK) | The pinned Java runtime and development tools used by the native Sigma environment |
| Java archive (JAR) | Packaged Java classes; capture identity must distinguish the executed archive and relevant class bytes |
| knowledge base (KB) | A configured collection of source and generated inputs; its selection can differ from the indexed source corpus |
| Secure Hash Algorithm 256-bit (SHA-256) | Content fingerprint used to bind exact bytes; a fingerprint supplies integrity relative to an authority, not trust in an unknown producer |
| Portable Document Format (PDF) | One rendered manuscript edition requiring inspection of the actual output |
| Hypertext Markup Language (HTML) | The web manuscript and dashboard document format |
| Scalable Vector Graphics (SVG) | Vector figure format; rendered content still needs layout review |
| Portable Network Graphics (PNG) | Raster figure format; exact image bytes and legibility are separate checks |
| Boolean (`Bool`) | The two-value Lean type used for hidden states and observations in the finite witness bridge; their roles remain distinct |

E and Vampire are prover product names. “E/V” denotes their comparison, with V
standing for Vampire in command options. Sigma is the reasoning environment.
Lean is the separate formal proof system. Word's `.docx` extension identifies an
Extensible Markup Language (XML)-based Office Open XML document, rather than a
distinct inference method.
The [standardized SZS result ontology](https://szs.tptp.org/) names semantic and
unsuccessful-search statuses; treat SZS as its established name rather than
inventing an expansion.

## Source objects and modeling distinctions

| Term | Meaning | Frequent mistake |
| --- | --- | --- |
| Symbol | Eligible token occurring in parsed expressions | Counting symbols as individuals, truths, or proofs |
| Formula | Complete source expression with its quantifiers and logical context | Treating a nested predicate occurrence as an asserted fact |
| Instance | An entity belonging to a class through `instance` | Replacing membership with subclass inclusion |
| Subclass | A class related to another class by inclusion of its instances | Reading the arrow as ordinary individual membership |
| Metamodeling | Using class or relation entities as arguments of other relations | Assuming “class,” “relation,” and “individual” are mutually exclusive spelling categories |
| Relation signature | Constraints on argument positions, including `domain` and `domainSubclass` | Treating all restrictions as the same untyped graph edge |
| Function range | Constraint on a function result, through `range` or `rangeSubclass` | Confusing the returned entity with the function symbol |
| Direct graph | Declared projection of eligible asserted binary formulas | Calling graph reachability full logical entailment |
| Kernel | Explicit selected and translated premises plus declared assumptions | Claiming it contains every source axiom |
| Teaching witness | Local assumed entity or tuple used to exercise a selected rule | Reporting it as an upstream source fact |
| Predicate binding | Declared replacement of a selected predicate variable for one supported instance | Claiming unrestricted higher-order translation |
| Profile | The files, preferences, caches and resources supplied to Sigma | Equating it with every file visited by the source index |

## Shared finite witness bridge

The bridge authority declares three strictly positive rational witnesses shared
by finite arithmetic, concrete Lean instantiations at revision
`9a0694f16b8e89b66b2f7f8cc7426c650dd2c4de`, and selected SUMO role scenarios.
Hidden-state tuples use `(false, true)`: index 0 is `Bool.false`, index 1 is
`Bool.true`. Observed `True` denotes the observation value, not the first hidden
state. The explorer coordinate is `q(false)=q0`, with `q(true)=1-q0`.

| Term | Meaning | Remaining boundary |
| --- | --- | --- |
| Shared witness | One declared prior, complete kernel, candidate, observation `True`, and authored entity identifiers used across the bridge obligations | Shared inputs do not prove semantic equivalence between SUMO and Lean |
| Complete observation kernel | A normalized law over both Boolean observations at each hidden state; observation `False` uses the complement of the manifest `True` likelihood | A two-entry observation likelihood is a selected slice of this kernel |
| Exact rational posterior | Bayes normalization computed using Python `Fraction` values | Does not make the floating-point objective exact |
| Independent numerical reference | Direct rational-to-`Decimal` products and natural logarithms at 80-digit precision, compared with the finite implementation | A finite numerical comparison at the report's tolerance, not a Python-correctness proof |
| Concrete Lean instantiation | Actual prior/candidate `FEP.FiniteLaw Bool`, complete `FEP.FiniteKernel Bool Bool`, and finite posterior/KL obligations using the shared values | Source generation, native compilation evidence and portable replay are distinct |
| Lean declaration inventory | Generated public declarations, including entity definitions, laws, the kernel, and theorems | Its length is not a theorem count |
| Declaration-axiom inspection | Checks the dependencies printed for each named declaration against the admitted axiom policy | Does not authenticate an absent compiler or historical process |
| Lean negative control | An invalid normalization, wrong posterior, or admitted-proof input intended to be rejected | Rejection requires the actual retained compiler evidence; a catalog entry is not an observed rejection |
| Representation scenario | Selected source rules and local assumptions relating an authored representation to its model | The entity label does not establish that SUMO verified Lean semantics |
| Calculation scenario | Selected source rules classifying an authored calculation | Does not perform or prove probability arithmetic inside SUMO |
| Named-record result | A selected consequence about the particular authored result entity | Distinct from an existential consequence that some result exists |
| Existential result | A selected consequence asserting existence of a result under the submitted premises | Does not identify its numerical value or certify a Lean theorem |
| Rational source label | `bridgeRationalMass` numerator/denominator labels retaining exact input identity | The FOL encoding treats these labels as uninterpreted, not arithmetic axioms |
| Fresh producer custody | Separate recording of your own completed run's report digest with its production evidence | Hashing a received untrusted report supplies no independent producer authority |
| Bridge explorer | Offline retained-case/Lean-source inspection with finite candidate exploration | Moving `q(false)` executes numerical calculations, not a new proof |

`output/bridge/bridge-report.json` is the canonical report location. Strict replay
requires an independently supplied outer digest and the complete retained
packet. HTTP/MCP bridge catalog, report and case inspection are read-only;
`GET /api/bridge/explorer` serves the retained explorer without launching a prover.
The
[interfaces](API.md#finite-witness-bridge) and
[architecture](architecture.md#shared-finite-witness-obligations) specify the
command and custody contracts.

Witness/scenario declarations describe the design; observed run counts,
statuses, selected prover families, control rejection and completion come from
the actual report. No completed native pass is asserted by this guide. Portable
replay does no new Lean checking, authenticates no historical execution, and
does not retain/authenticate every external dependency artifact. There is no
general SUMO-to-Lean semantic-preservation result.

## Logical outcomes

| Term or status | Licensed reading |
| --- | --- |
| Satisfiable background | At least one model satisfies the submitted premises |
| Entailment | Every model of the background satisfies the conjecture |
| `Theorem` | The conjecture is reported entailed by the submitted problem; inspect background and capture validity |
| `CounterSatisfiable` | A model of the submitted background can falsify the conjecture; this establishes non-entailment in that kernel |
| `Satisfiable` | A conjecture-free problem is reported to have a model |
| `Unsatisfiable` | A conjecture-free problem is reported to have no model |
| `ContradictoryAxioms` | The axioms are contradictory; a query cannot be justified as a useful intended-model result merely by proving it there |
| `Timeout` or `GaveUp` | Search did not establish a conclusive semantic result within the run's conditions |
| Invalid capture | Evidence failed its custody or interpretation checks; no successful proof claim follows |
| Non-entailment | At least one background model falsifies the query; this does not entail its negation |
| Open-world reading | Missing information is not automatically false; a missing source edge is not a negated assertion |
| Classical explosion | An inconsistent classical background entails every sentence; positive theorem labels alone cannot establish usefulness |

For example, if a restricted kernel omits a required membership premise, it may
permit both a model where the query is true and another where it is false. Its
countermodel therefore establishes a limit of that kernel, not falsity in the
entire ontology. Adding axioms can change the outcome; record which theory was
actually submitted.

## Controls, comparison, and custody

| Term | What it contributes | Remaining boundary |
| --- | --- | --- |
| Positive control | Tests the declared consequence | Must be interpreted with background satisfiability and valid capture |
| Negative-query control | Tests a deliberately unsupported conjecture | Its formula need not be the negation of the positive query |
| Premise-removal control | Tests the consequence after one registered dependency is removed | Does not establish global minimality |
| Background control | Submits the selected premises without a conjecture | Concerns that selection, not the entire source distribution |
| Refutation control | Adds the negated positive query as a premise and tests inconsistency | Must not be confused with an inconsistent unmodified background |
| E/V agreement | Matching classifications on matching retained problem bytes | Does not prove translation correctness or general solver soundness |
| E/V disagreement | Different classifications requiring investigation | Does not by itself identify a faulty solver or ontology |
| Native replay | Runs a recorded problem again with a native prover | A new execution, with its own identity and budget |
| Portable replay | Rederives problems and revalidates retained artifacts without a new solver process | Does not authenticate history or independently check every proof step |
| Proof-step checking | Independent checking of a native proof calculus | Separate from captured status, checksums, and native repetition |
| Trusted outer digest | Separately retained fingerprint selecting the report bytes | Only as trustworthy as the authority supplying it |
| Receipt | Record of exact inputs, tools, outputs, and checks | Establishes the stated custody scope, not scientific truth |
| Theorem scope | The exact submitted background, encoding, conjecture and accepted evidence | Does not automatically transfer to all source formulas, a new revision, or a biological interpretation |

The strongest responsible claim names its scope: which source, which encoding,
which conjecture, which controls, which native execution, and which verification.
The [runtime guide](runtime.md), [interfaces](API.md), and
[architecture](architecture.md) define the corresponding implementation contracts.

## Active Inference and one-step decisions

See the [worked mathematical guide](active-inference.md) for equations and an
executable example. These definitions concern the standalone finite planner.

| Term | Meaning here | Boundary |
| --- | --- | --- |
| Active Inference | Research framework connecting generative-model inference with action | A finite variational identity alone supplies no action-selection model |
| Variational free energy | Candidate-belief objective given a fixed observation | Distinct from the prospective action score and thermodynamic free energy |
| Outcome preference | Strictly positive normalized law expressing desired outcomes | Distinct from an observation likelihood or predicted outcome frequency |
| Outcome risk | KL divergence from predicted outcomes to the preference law | Direction and reference distribution matter |
| Ambiguity | Expected conditional outcome entropy given the next state | Distinct from marginal outcome entropy |
| State information gain | Expected KL from hypothetical next-state posteriors to the predicted next-state law | Does not measure parameter learning or empirical truth |
| One-step expected free energy | The adopted outcome-risk-plus-ambiguity functional | Not a claim of equivalence with every state-preference or approximate formulation |
| Numerical minimizers | All actions within the declared tolerance of the best score | Neither a hidden tie-break nor certified interval ordering |

# Abstract {.unnumbered}

The Suggested Upper Merged Ontology (SUMO) supplies general categories,
relations and axioms for knowledge representation. Its source language,
Standard Upper Ontology Knowledge Interchange Format (SUO-KIF), and its reasoning
environment, Sigma Knowledge Engineering Environment (KEE), have different roles.
Rikishi is a source-bound workbench for inspecting those commitments,
submitting selected reasoning problems, and retaining their inputs and evidence.
This paper asks how that infrastructure can make a scientific modeling
connection inspectable. Prior Active Inference–SUMO alignment provides a direct
precedent [@douglass2024alignment].

One shared finite witness connects selected ontology expressions to probability
models, numerical evaluation, pinned FEP_Formal Lean statements and synthetic
observation histories. The ontology lane investigates declared model,
representation, calculation and result roles. The mathematical lane supplies
finite normalization, conditioning and information identities under stated
hypotheses. The computational lane checks numerical outputs and generates
trajectories from an explicit persistent-state model. Stable identifiers and
common inputs join these lanes without treating their claims as interchangeable.

Worked source formulas, direction-sensitive queries, numerical references and
formal controls make the connections testable. Exact conditioning is separated
from simulated frequencies, and variational inference from action selection
and empirical model assessment. The resulting interface supports reproducible
inspection of particular examples; it does not establish full-SUMO consistency,
a general SUMO-to-Lean interpretation, verification of all Python execution,
or biological validity of the Free Energy Principle (FEP).

# SUMO foundations and scholarship {#sec:sumo}

The research question is how an ontology operator can make a proposed scientific
alignment inspectable and executable without conflating its different objects.
A source formula states an ontological commitment; a mathematical law specifies
a finite probability model; a program evaluates that model; and a proof concerns
a proposition under hypotheses. The alignment precedent supplies candidate
senses [@douglass2024alignment], while SUMO translation work shows that the target
logic and its treatment of types are substantive parts of an interpretation
[@pease2023translation; @brown2023sumok]. Rikishi connects these objects through
explicit inputs and evidence, rather than treating a shared label as a semantic
correspondence.

## A reader's map: ontology, mathematics and execution {#sec:reader-map}

An upper ontology provides reusable commitments about kinds of entities and
their relations. SUMO can help two applications state whether they mean an
individual, a class, a process, a representation or a result, and which axioms
constrain those choices. Its value is both organizational and inferential:
compatible definitions support integration, while axioms can support queries
whose answers require more than finding a matching word
[@niles2001sumo; @pease2014sigma]. The precise consequence still depends on the
selected theory and its interpretation.

The components used here have different jobs:

| Component | What it supplies | Question it addresses here |
| --- | --- | --- |
| SUMO | General classes, relations, signatures and axioms | What is the proposed referent, and which consequences follow from the selected commitments? |
| SUO-KIF | The language of the source expressions | What exactly is asserted, with which quantifiers, argument roles and contexts? |
| Sigma KEE | Ontology browsing, management, translation and prover integration | How is a configured theory operated and submitted to a reasoning system? |
| FEP_Formal | Pinned Lean definitions and mathematical statements | Which finite laws and identities hold under the stated hypotheses? |
| Rikishi's evaluators and simulator | Numerical calculations and synthetic trajectories from declared inputs | What does this implementation return or generate for this particular model? |
| Rikishi's evidence records | Source, input, command, output and role bindings | Which observation supports which claim about which artifact? |

SUMO is therefore not interchangeable with its source language, a theorem
prover, or a simulator. Likewise, a vocabulary correspondence is a proposal
about meaning; a numerical equality, a checked Lean term and a synthetic
trajectory supply different tests of that proposal. The running connection is
a *shared finite witness*: one explicitly specified probability model is
represented in each lane, with stable identifiers and a separate obligation at
every connection. The ontology foundations below establish the source side;
[@sec:bridge-walkthrough] follows one witness through the mathematical and
computational sides.

## SUMO as an axiomatized upper ontology {#sec:sumo-as-an-axiomatized-upper-ontology}

The Suggested Upper Merged Ontology (SUMO) supplies general categories, relations,
and axioms intended to support more specialized theories. Its original proposal
addressed the Institute of Electrical and Electronics Engineers (IEEE) Standard Upper Ontology working group and sought a common
foundation for knowledge representation and integration. The construction method
distinguished a syntactic merge, converting selected prior representations into
SUO-KIF, from a semantic merge, reconciling their conceptual commitments. A merged
upper structure based on Sowa's and Russell and Norvig's ontologies organized
additional content, including temporal and mereotopological theories. Integration
could require inserting intermediate categories, rejecting unsuitable content,
recognizing equivalent axioms, or revising partially overlapping theories. This
was an explicit modeling and reconciliation process; its consistency goal is not
a proof about every subsequent SUMO revision [@niles2001sumo].

The distribution preserves a layered organization. `Merge.kif` contains the upper
ontology; the Mid-Level Ontology (MILO), distributed as
`Mid-level-ontology.kif`, bridges abstract categories and domain detail. Domain
files extend this vocabulary for particular subject areas. Natural-language
formatting and lexical resources add another operational layer. Consequently,
the indexed source corpus, a configured reasoning profile, and an all-domain load
must be identified separately. Loading additional files changes the theory under
investigation. Rikishi's source lock, file manifest, and runtime profile make that
selection inspectable [@sumoSource].

## Modeling commitments and source interpretation {#sec:modeling-commitments-and-source-interpretation}

SUMO distinguishes membership from specialization. An `instance` assertion places
an entity in a class, whereas `subclass` relates classes through inclusion of
their instances; multiple classification is permitted. Relations themselves have
classifications and signatures. `domain` constrains an argument to instances of a
class, while `domainSubclass` constrains it to subclasses. Function result
restrictions likewise distinguish `range` from `rangeSubclass`. Disjointness
constrains shared membership and can therefore interact with inherited relation
classifications. These distinctions affect admissible substitutions and generated
typing conditions, not merely the arrangement of labels in a hierarchy
[@sumoSource; @pease2009suokif].

The upstream formalization guidance combines taxonomic placement, documentation,
lexical presentation, and axioms describing the relevant properties of a concept
[@sumoFormalizingTerms]. A proposed research term therefore needs more than a
plausible name or a nearby superclass. Its intended referents, argument roles,
constraints, and inferential consequences require explicit justification.
Rikishi's graph is a declared projection for navigation: binary assertions do not
stand in for the complete quantified theory. A predicate occurrence within a
negation, conditional, or contextual formula cannot be interpreted as an
unconditional edge merely because the same symbols appear.

The modeling guidance is explicit: "Add axioms that describe the relevant
properties of the concept" [@sumoFormalizingTerms]. A superclass and an English
description support discovery; the property axioms determine which consequences
an intended interpretation must admit. SUMO's use of classes and relations as
arguments makes those commitments visible in the source itself.

::: {.axiom #thm:sumo-membership title="Source membership propagation"}

Write $I(x,C)$ for `instance` and $S(C,D)$ for `subclass`. The pinned
source includes the following rule, expressed here with explicit quantifiers:

$$
\forall C,D,x\;\bigl(S(C,D)\land I(x,C)\bigr)\Rightarrow I(x,D).
$$ {#eq:sumo-membership}

This is a rendering of a source axiom, not a new theorem establishing the
semantics of the whole ontology. Multiple membership and specialization remain
different relations [@sumoSource].

:::

The signature theory contains further axioms. For example, the source requires
comparable class restrictions when `domain` assigns different classes to the same
relation position. Its `range` and `rangeSubclass` rules conclude membership and
subclass inclusion respectively. Replacing either with an undifferentiated
"type" arrow would erase a consequence that matters to an actual query
[@sumoSource]. [@thm:sumo-membership] therefore illustrates one inferential
commitment rather than licensing a generic graph interpretation of all typing.

A symbol inventory must also be distinguished from a population of individuals.
The index counts eligible tokens in formulas; it does not decide that every token
is an ordinary object, a class, or a relation in one mutually exclusive syntactic
category. In the pinned source, `ProbabilityFn` is an instance of `UnaryFunction`,
and `UnaryFunction` is a subclass of `Function`. Membership propagation classifies
the function entity; it does not turn `ProbabilityFn` into a subclass. Similarly,
the lowercase `agent` relation and the `AutonomousAgent` class play different
argument roles despite their related English names [@sumoSource].

This use of class and relation entities inside other assertions is metamodeling.
A relation can have a classification, argument restrictions, and instances of its
use, with different formulas governing each aspect. A source-level constant used
to talk about a relation must not silently become an unrestricted predicate
variable in the target logic. The declared laboratory below keeps object symbols
and fixed predicate symbols in separate target namespaces and records any finite
predicate specialization explicitly. Its representational choice is a bounded
encoding decision, not a theorem that all source metamodeling is preserved.

## SUO-KIF and reasoning translations {#sec:suo-kif-and-reasoning-translations}

SUO-KIF provides authoring constructs that require care when mapped to an automated
prover's language. Its manual discusses predicate-position variables, row
variables, variable arity, and embedded formulas, including the difference
between higher-order interpretation and quotation as data. Bounded macro
expansion is an implementation choice with a different reach from unbounded
sequence-variable interpretation [@pease2009suokif]. Benzmüller and Pease examine
temporal, epistemic, and doxastic contexts and show why a classical treatment of
embedded propositions can produce unintended consequences. Their proposed modal
embedding makes the contextual interpretation explicit [@benzmueller2012higherorder].

First-order translation is thus a substantive dependency. Pease describes
predicate-variable instantiation, row-variable expansion, variable-arity
specialization, and inferred type restrictions in the path to prover input.
The typed first-order extension gives numerical expressions access to built-in
arithmetic, but disjoint target sorts do not directly reproduce SUMO's multiple
inheritance; much of the ontology's type structure remains axiomatic. The paper
explicitly identifies loss of strictly higher-order content in first-order
translations [@pease2023translation]. Brown, Pease, and Urban instead interpret
the SUMO-K fragment in higher-order set theory, handling sequence arguments,
relation quantification, class formation, and selected arithmetic. Their
interactive proofs and derived automated theorem proving (ATP) problems concern that interpretation. The
fragment excludes temporal, modal, and probabilistic operations, so it does not
establish a universal translation of SUMO [@brown2023sumok]. Rikishi accordingly
retains source formulas and submitted problem bytes as separate evidence objects.

Scope also depends on the use of a sentence. The manual gives free variables in
assertions an outer universal interpretation, while free query variables receive
an existential interpretation. Its practical advice is: "To be certain of the
usage in all contexts, use explicit quantifiers" [@pease2009suokif, p. 11].
Quantifier order distinguishes a witness that may vary with each object from a
single witness shared by all objects. Predicate-position variables and argument
sequences require their own interpretation. The actual subrelation rule applies
the same argument sequence to both relations and retains predicate guards;
`partition` is explicitly classified as a variable-arity relation. Neither
construction is an unrestricted binary edge [@sumoSource].

The translation paper states that "all the strictly higher-order content in
SUMO is lost in translation to first-order" [@pease2023translation, sec. 1].
The alternative SUMO-K treatment states its boundary equally clearly: "Elements
of SUMO not included in SUMO-K are temporal, modal and probabilistic operations"
[@brown2023sumok, sec. 2]. These are limits on different constructions, rather
than contradictory assessments of a single interchangeable target theory. A
proof in a selected target must identify that target and its translation policy.

The alternatives address different research problems:

| Approach | Construction and mathematical target | Consequence for comparison |
| --- | --- | --- |
| Sigma's first-order translations | Predicate specialization, row expansion and inferred guards prepare first-order prover input; typed translation additionally interprets numerical expressions in target arithmetic [@pease2023translation]. | A result depends on that preprocessing and target theory. |
| SUMO-K | A defined fragment receives a higher-order set-theoretic interpretation, with interactive proofs and extracted automated problems [@brown2023sumok]. | Its semantic account concerns that fragment; probabilistic operations are excluded. |
| Adimen-SUMO | Reengineering translates and revises studied upper and middle levels for first-order reasoning [@alvez2012adimen]. | Its repaired axiom set is a distinct ontology variant. |
| Rikishi's selected kernels | Complete pinned formulas and separately identified local assumptions are compiled into the declared function-free fragment in [@sec:inference-kernels]. | Controlled consequences concern the submitted kernel; vocabulary, arithmetic, and proof transport require additional interpretations. |

This comparison explains the design choice to retain both source and target
problems. Reusing a prover does not make these constructions interchangeable;
changing the axiom set or interpretation changes the question being answered.

## Sigma engineering and lexical mappings {#sec:sigma-engineering-and-lexical-mappings}

Sigma integrates ontology browsing, natural-language paraphrase, lexical
resources, static checks, translation, and theorem-prover interaction. The Sigma
Knowledge Engineering Environment (KEE) system description explains the engineering value of retaining and indexing
a relatively stable background theory across queries, and of linking proof steps
back to premises. It also documents the practical evolution of prover integration
[@pease2014sigma]. Such architecture motivates recording the translator, generated
caches, selected constituents, prover invocation, and result together. A
historical system description cannot certify that a particular installed pair
of tools accepts the same command grammar or produces the intended semantics.

WordNet provides a lexical route into SUMO. The original mapping work distinguishes
equivalence of meaning, subsumption, and instantiation. Its `=`, `+`, and `@`
markers record different alignments between a synset and an ontology concept
[@niles2003wordnet]. The distributed headers additionally document complementary
mapping relations, and the README explains that mappings may target MILO and
domain terms as well as the upper ontology [@sumoWordnetMappings]. These are
sense-specific mapping assertions. They do not identify every spelling or synonym
with an ontology entity, and a subsumption mapping does not assert synonymy.
Lexical alignment can guide term discovery and test generation while still
requiring examination of the chosen sense, mapping relation, and formal axioms.

## Competency questions, reengineering, and benchmarks {#sec:competency-questions-reengineering-and-benchmarks}

Adimen-SUMO provides an instructive comparison because it is an ATP-oriented
reengineering of studied SUMO upper and middle levels. Its developers translate,
debug, repair, and augment axiomatization to obtain a usable first-order theory.
The resulting ontology must be identified as a derived artifact. Its treatment
of second-order constructions through finite reflection does not establish
unrestricted second-order equivalence, and the original paper leaves a proof of
consistency outside its scope [@alvez2012adimen]. Rikishi operates the pinned
OntologyPortal distribution and Sigma path; it does not silently substitute
Adimen-SUMO or inherit its validation results.

Competency-question testing turns intended capabilities into explicit conjectures
and expected outcomes. Work on Adimen-SUMO combines manually designed questions
with tests generated from lexical mappings and semantic patterns, then uses ATP
feedback to improve the ontology. A crucial distinction is between a demonstrated
consequence and an unknown result after bounded search [@alvez2015competency].
The associated ATP benchmark also includes negated questions: solving an expected
falsity-test may reveal an unwanted consequence rather than successful ontology
behavior [@alvez2017atp]. White-box testing adds tests derived from axiom structure
to expose redundancies and other defects. Its correction iterations support
specific improvements, not complete correctness or satisfiability certification
[@alvez2019whitebox]. Benchmark conclusions therefore require the ontology
variant, test construction, expected polarity, prover configuration, and resource
limits. Published benchmark performance is not evidence that Rikishi has executed
the same campaign.

## Active Inference alignment as direct precedent {#sec:alignment-precedent}

Douglass and collaborators' *Aligning Active Inference Ontology to SUMO* explicitly
proposes aligning Active Inference topics with SUMO [@douglass2024alignment]. The
preprint and accompanying spreadsheet provide scaffolding for later rigorous
mapping. They distinguish conceptual topics from linguistic terms, discuss broad
and narrow senses, and organize candidate SUMO locations, more general categories,
argument domains, and proposed relationships. An asterisk marks terms proposed
for addition rather than existing SUMO identifiers. Rikishi therefore builds on
an established alignment agenda; its contribution is a reproducible environment
for investigating proposals and recording the scope of their evidence.

The alignment tables expose questions that an operator must preserve. The Agent
entry discusses the lowercase SUMO `agent` relation and its argument types. That
case role relates a process to an autonomous agent; matching the English word
does not make the relation a class of inference systems. The Generative Model
entry proposes placement beneath `Process`, whereas Rikishi's illustrative SUO-KIF
represents its finite model beneath `Proposition`. These are different modeling
choices requiring an account of the represented object, its description, and the
process that uses it. SUMO places `Process` under `Physical` and `Proposition`
under `Abstract`, making the distinction a formal category commitment
[@sumoSource]. Neither placement is validated here. The preprint itself
questions a proposed placement of abstract inference beneath learning because of
the temporal distinction [@douglass2024alignment]. Its tables should therefore
be read as reviewable proposals, not imported as an already validated axiom set.

SUMO's own signatures constrain the next step. In the pinned source, `agent`
has process and autonomous-agent argument domains, while `ProbabilityFn` is a
unary function on formulas with a real-valued range [@sumoSource]. The latter does
not by itself supply the finite carrier, probability mass vector, or normalization
used in [@sec:finite-example]. A semantic alignment must specify how such
mathematical objects are represented and which axioms connect them. Source lookup,
lexical resemblance, successful parsing, and proof of a separate numerical
identity each answer different questions.

# Operator architecture and evidence {#sec:architecture}

## Provenance and thin orchestration {#sec:provenance}

Rikishi operates the OntologyPortal distribution rather than a replacement
demonstration ontology. Its name refers to a sumo wrestler and distinguishes the
operator from SUMO itself. Importable methods own indexing, numerical calculation,
native reasoning, and rendering. The command-line interface (CLI), dashboard, and
Model Context Protocol (MCP) entrypoints adapt those
methods to their transports.

A source lock identifies upstream Git objects and the runtime. The index retains
formulas, files, and line locations alongside a narrower directed navigation
projection. A source audit compares current SUO-KIF bytes with the indexed manifest.
Term lookup and interactive graphs preserve the distinction between asserted
relations and the quantified theory described in [@sec:sumo]. Predicate selection,
truncation, assertion multiplicity, and distinct triples are explicit observations.

Native execution preserves submitted Thousands of Problems for Theorem Provers
(TPTP) problems, transitive includes, executable
identity, command grammar, stdout, stderr, and hashes. Proof-bearing results
require trusted invocation expectations. Unsupported syntax, ambiguous paths,
extra problem inputs, stale captures, and mismatched receipts reject. Frozen
replay uses retained inputs after originals change or move. These controls
establish custody of an invocation, not translation correctness.

::: {.definition #def:sumo-source-projection title="Restricted asserted-edge projection"}

Let $\mathcal T$ be the parsed top-level source expressions and $N$ the
indexer's eligible symbol tokens, excluding numbers, variables and reserved
logical syntax. The distinct edge set is

$$
E(\mathcal T)=\{(a,r,b)\mid (r\;a\;b)\in\mathcal T,
\ r,a,b\text{ are atomic},\ a,b\in N\}.
$$ {#eq:sumo-projection}

The stored assertion population retains repetitions; this set removes identical
triples. Nested expressions are not recursively asserted as edges. A relation
filter restricts this population before the requested output limit is applied.

:::

[@def:sumo-source-projection] describes Rikishi's index, not a model theory for
SUMO. A ternary domain assertion, a partition with several arguments, and a modal
formula can all matter to the ontology while falling outside this projection.
Conversely, a recorded edge is a syntactic observation; its presence does not
independently prove an intended semantic interpretation.

## Quantification and interfaces {#sec:interfaces}

The dashboard and MCP tools expose source inspection, bounded graphs, finite
calculations, and operator methods. Quantities describe a selected population and
indexing policy; they do not estimate truth, independent facts, completeness, or
empirical validity. The cover abstract therefore separates SUMO source, operator
evidence, and the finite probabilistic example.

A failed parser, translator, or prover remains a failed observation. The
standardized result ontology named for Sutcliffe, Zimmer and Schulz (SZS) separates
semantic outcomes from unsuccessful search [@tptpSZS]. Exhausted search does not
prove non-entailment, and contradictory premises cannot validate their intended
model.

# Corpus and native reasoning observations {#sec:observations}

## Source-derived measurements {#sec:corpus}

The indexed source revision is `{{SUMO_COMMIT}}`. Its checked export reports:

| Structural observation | Exported value |
| --- | ---: |
| Indexed Knowledge Interchange Format (KIF) files | {{CORPUS_FILES}} |
| Parsed top-level formulas | {{CORPUS_FORMULAS}} |
| Distinct indexed symbols | {{CORPUS_TERMS}} |
| Asserted binary edges, including multiplicity | {{CORPUS_EDGES}} |
| Parse errors | {{CORPUS_PARSE_ERRORS}} |

These values are injected from the corpus export. Nested files belong to the
index population, whereas a configured Sigma profile selects its own
constituents. An all-domain load is another theory and another experiment.

![Largest indexed Suggested Upper Merged Ontology (SUMO) files, with exact formula counts and full-population shares. Source structure does not measure logical importance or proof coverage.](figures/corpus-files.png){#fig:corpus-files}

The distribution in [@fig:corpus-files] is heterogeneous. Geographical and
language-related files contribute many formulas; revision and selection policy
change the population. Redundancy and development proposals can contribute to
counts, which do not measure independent meanings.

![Suggested Upper Merged Ontology (SUMO) formula-head composition with an exact remainder, and direct-edge degree distribution including zero-degree symbols. Deduplication concerns identical predicate-subject-target triples; graph absence is absence from this restricted projection.](figures/corpus-composition.png){#fig:corpus-composition}

File concentration uses each file's share of parsed formulas. The Herfindahl sum
of squared shares summarizes the population, not ontology quality. The graph
denominator in [@fig:corpus-composition] includes every indexed symbol, including
zero-degree terms. The analytics export defines denominators and distinguishes
assertion multiplicity from distinct triples.

## Direct taxonomy structure and source navigation {#sec:taxonomy-structure}

SUMO's class hierarchy and relation hierarchy are different source graphs.
For each selected relation $r$, an indexed top-level atomic statement
$(r\;s\;t)$ supplies the directed pair $(s,t)$, oriented from child to parent.
The projection deduplicates those pairs. Its node population consists of their
endpoints. Variables and assertions nested inside
implications or quantifiers remain in their complete source formulas rather
than becoming unconditional graph edges. The same read-only methods power the
corpus dashboard, command-line inspection and MCP tools.

Let $E_r$ denote the selected directed pairs and $V_r$ their endpoints.
The structural summaries use

$$
\begin{gathered}
\mathcal{R}_r = \{v\in V_r:\deg_r^{+}(v)=0\},\\
\mathcal{M}_r = \{v\in V_r:\deg_r^{+}(v)>1\},\\
\mathcal{C}_r = \{S\in\operatorname{SCC}(V_r,E_r):
 \lvert S\rvert>1\;\lor\;\exists v\in S\;(v,v)\in E_r\}.
\end{gathered}
$$ {#eq:taxonomy-structure}

Here out-degree counts distinct direct parents. Roots, multiple inheritance and
strongly connected components in [@eq:taxonomy-structure] describe this restricted
source graph. A directed cycle is an inspection target; its presence does not
establish inconsistency, and its absence does not establish consistency. SUMO
constraints and quantified axioms extend beyond this projection [@sumoSource;
@pease2023translation].

The following values are recomputed from the complete retained `Merge.kif` bytes,
using the same index and taxonomy analysis methods as the dashboard. They are
file-specific populations and therefore differ from whole-corpus totals.

{{ONTOLOGY_STRUCTURE_TABLE}}

![Suggested Upper Merged Ontology (SUMO) subclass and subrelation graph populations in complete retained Merge.kif, with endpoint counts and structural diagnostics. Source provenance uses the Secure Hash Algorithm 256-bit (SHA-256) fingerprint. The figure and table are replayed from source; cycle counts carry no logical-consistency conclusion.](figures/ontology-structure.png){#fig:ontology-structure}

The white corpus workbench separates complete population totals from filtered
and paginated rows. Selecting a file or formula head opens complete SUO-KIF
formulas with original file, line and source Secure Hash Algorithm 256-bit
(SHA-256) fingerprint. A breadth-first traversal
returns a deterministic shortest child-to-parent path and the source formula
for every step. Reaching a depth or visit budget is reported separately from
exhausting reachable nodes. These source paths support inspection, while ATP
entailment remains a separate operation. The exact-input report accompanying
[@fig:ontology-structure] retains assertion multiplicity separately from distinct
graph edges.

## Worked inspection of the pinned SUMO theory {#sec:sumo-demonstrations}

The demonstration method audits the current index against source bytes, freezes
the complete `Merge.kif`, and selects formulas structurally through the existing
parser. The retained source path is `{{SUMO_SOURCE_PATH}}` at revision
`{{SUMO_SOURCE_COMMIT}}`. Its computed SHA-256 is
`{{SUMO_SOURCE_SHA256}}`. The file contains **{{SUMO_SOURCE_FORMULAS}}** parsed
top-level formulas and **{{SUMO_PROJECTED_BINARY_EDGES}}** binary edge assertions
under [@def:sumo-source-projection]. The worked cases cite
**{{SUMO_CITED_FORMULAS}}** distinct source formulas; reused formulas count once.
These are file-specific populations rather than the full-corpus totals above.

The following blocks are injected from the checked source, preserving their
logical context. SUMO excerpts acknowledge the Institute of Electrical and
Electronics Engineers, Inc. (IEEE), copyright 2004, as source and copyright owner,
under the distribution's copying and attribution terms [@sumoSource]. Formula
locations, excerpt hashes and the full source bytes are retained in the
demonstration report. Changing an excerpt, its line range or a derived observation
causes portable replay to reject it.

### Categories and relation signatures {#sec:sumo-worked-categories}

![Suggested Upper Merged Ontology (SUMO) source commitments: subclass structure, relation and function signatures, and a complete modal example. Arrow and role labels distinguish specialization, membership and argument constraints. Secure Hash Algorithm 256-bit (SHA-256) provenance binds the frozen source. The diagram is not a full inference or translation result.](figures/sumo-system.png){#fig:sumo-system}

[@fig:sumo-system] provides a map for the worked source blocks below.

The selected taxonomic commitments are:

```lisp
{{SUMO_HIERARCHY_KIF}}
```

This is more specific than a general-purpose label hierarchy. `Process` belongs
on the physical branch; `Proposition` belongs on the abstract branch. Under the
partition's decomposition axioms, the branches exclude a common instance. For
$P=\mathrm{Physical}$ and $A=\mathrm{Abstract}$, the relevant condition is

$$
\neg\exists x\;\bigl(I(x,P)\land I(x,A)\bigr).
$$ {#eq:sumo-category-disjointness}

This is an explanatory consequence of the stated partition semantics, not an ATP
result produced by the source-inspection method. A class placed below incompatible
categories may be forced to be empty; a contradiction additionally needs a
commitment supplying a common instance. Likewise, a model's mathematical content,
the file that describes it and the process that executes it require distinct
referents. The competing generative-model placements in
[@sec:alignment-precedent] cannot be reconciled by matching their English names.

The membership/specialization distinction is directly inspectable:

```lisp
{{SUMO_TYPING_KIF}}
```

`agent` here is an instance of a relation class, whereas `Process` is a subclass
of a category. Its argument order is also a substantive commitment:

```lisp
{{SUMO_AGENT_SIGNATURE_KIF}}
```

The first role is a process and the second an autonomous agent. A posterior
vector or an abstract model description does not supply those referents merely
because an implementation is called an agent. A proposed extension must say what
performs the process, what that process is, and how the source role applies.
These source signatures are not a claim that every installed translator enforces
their intended consequences in the same way.

### Probability and modal context {#sec:sumo-worked-probability}

The probability vocabulary has its own representational commitments:

```lisp
{{SUMO_PROBABILITY_SIGNATURE_KIF}}
```

`Formula` is a source class beneath `Sentence`. Its instances must not silently
be identified with `Proposition`, a Python list or a probability tensor.
`ProbabilityFn`'s unary signature and real-valued range do not exhaust its
probabilistic axiomatization or automatically supply the finite model below.

::: {.remark #rem:sumo-finite-interpretation title="An interpretation obligation"}

For a proposed finite interpretation, let $e:S\to\mathcal F$ represent latent
alternatives by event formulas. An intended correspondence would require

$$
p(s)=\operatorname{ProbabilityFn}(e(s)),\qquad
p(s)\geq0,\qquad\sum_{s\in S}p(s)=1.
$$ {#eq:sumo-event-interpretation}

This stipulates obligations for a proposed representation. It derives neither
normalization nor event exclusivity/exhaustiveness from the unary signature.
Formula identity, conditioning, support and the target arithmetic still need
definitions and preservation arguments.

:::

Conditioning illustrates why argument roles must be read from source. The
complete signature assertions at `Merge.kif:3348–3352` are:

```lisp
(instance conditionalProbability ProbabilityRelation)
(instance conditionalProbability TernaryPredicate)
(domain conditionalProbability 1 Formula)
(domain conditionalProbability 2 Formula)
(domain conditionalProbability 3 RealNumber)
```

The accompanying documentation at lines 3354–3362 interprets
`(conditionalProbability A B r)` as the probability of `B` given `A` being `r`.
An event encoding of $\ell(s)=p(o\mid s)$ must therefore put the state condition
first and the observation second. This is a proposed interpretation of two
formulas, not an equality between the source predicate and a Python array
[@sumoPinnedMerge, lines 3348–3362].

Arithmetic also needs an explicit interpretation. Two complete signature
selections from `Merge.kif:5880–5885` and `6139–6142` are:

```lisp
(instance DivisionFn BinaryFunction)
(instance DivisionFn PartialValuedRelation)
(domain DivisionFn 1 RealNumber)
(domain DivisionFn 2 RealNumber)
(range DivisionFn RealNumber)

(instance LogFn BinaryFunction)
(domain LogFn 1 RealNumber)
(domain LogFn 2 PositiveInteger)
(range LogFn RealNumber)
```

The division documentation explicitly leaves a zero denominator undefined
(lines 5887–5894). The logarithm documentation assigns its second argument the
base (lines 6144–6148). Thus this binary, integer-base signature cannot simply be
substituted for Lean's unary natural logarithm in a quantity measured in nats.
The declared first-order laboratory has an even narrower boundary: its numeral
symbols are uninterpreted constants. Neither those constants nor a function's
name execute real arithmetic. The finite numerical and Lean layers below supply
their own stated arithmetic semantics [@sumoPinnedMerge, lines 5880–5894,
6139–6148; @pease2023translation;
@fepFormalPinned].

A complete contextual formula supplies a contrasting source example:

```lisp
{{SUMO_NESTED_FORMULA_KIF}}
```

The existential statement appears inside `modalAttribute` and is conditioned on
the antecedent. It is not an assertion of an observed process-agent event. The
structural demonstration preserves the full formula and records that it is not a
ground binary edge. No modal theorem is inferred by stripping away those
operators [@sumoSource; @benzmueller2012higherorder].

### Thin orchestration and separate proof controls {#sec:sumo-worked-orchestration}

From the repository root, the orchestration script can retain a fresh report and
optionally run the existing restricted taxonomy method:

```bash
uv run python scripts/demonstrate_sumo.py \
  --output output/demonstrations/source-report.json \
  --proof-directory output/demonstrations/taxonomy
```

The destinations must be fresh. The script selects paths and delegates to
importable methods; it does not implement another parser, ontology engine or
prover. The default report makes no ATP invocation. Its portable verifier hashes
and reparses the frozen bytes, rederives the selections and observations, and
checks exact agreement. That establishes internal agreement of the retained
snapshot. The acquisition/source-audit record supplies the binding to the Git
revision; a self-contained digest alone cannot authenticate a claimed revision.

The optional operation separately submits the selected hierarchy's direct
`subclass` assertions plus transitivity. It checks `Process` beneath `Entity` and contrasts `Process` beneath
`Abstract`, retaining exact problems and native outcomes. A countermodel to the
latter applies to that restricted projection, which omits the partition's full
axiomatization; it is not a countermodel of the complete SUMO theory. This
separation keeps the successful source inspection, restricted proof and native
Sigma diagnostic in [@sec:native-reasoning] from acquiring each other's claims.

## Source-bound inference laboratory {#sec:inference-laboratory}

### Questions, theories, and interpretations {#sec:inference-meaning}

The inference laboratory turns selected pinned source formulas into explicit
first-order logic (FOL) problems. It complements the source demonstrations by
asking which consequences actually follow under a declared encoding, then testing
the dependencies that make those consequences possible. It is separate from the
finite alignment study in [@sec:alignment-campaign] and from Sigma's configured
full-profile translation. A theorem in one of these settings does not silently
transfer to another.

Let $T$ denote the submitted premises and $q$ the conjecture. Satisfiability of
$T$ means that some interpretation satisfies every premise. Entailment,
$T\models q$, means that every model of $T$ satisfies $q$. Classical refutation
tests the latter through the unsatisfiability of $T\cup\{\neg q\}$. The prover's
problem therefore needs both the selected background and the exact conjecture;
an isolated query string is insufficient to identify the inference experiment.

Non-entailment is also a positive logical finding when a countermodel is supplied.
A model satisfying $T\cup\{\neg q\}$ establishes $T\nvDash q$. It does not
establish $T\models\neg q$: another model may satisfy both $T$ and $q$. This
distinction supports an open-world reading of incompletely specified knowledge.
An absent source assertion or graph path does not automatically become a negative
fact. A bounded search that produces no proof establishes neither a countermodel
nor entailment of the negation.

Background satisfiability must be considered independently. If $T$ is inconsistent,
it has no models and classically entails every conjecture. The implication
“all models of $T$ satisfy $q$” then holds vacuously. Consequently, a successful
refutation can be diagnostically correct while providing no useful validation of
the intended ontology model. The laboratory submits a conjecture-free background
control alongside each positive obligation. This does not certify consistency of
the full source distribution; it tests the premises actually used in that case.

### Declared source selection and supported fragment {#sec:inference-kernels}

The packaged study identifies the complete pinned *Merge.kif* file, its revision
and content fingerprint, selected formula start lines, explicit local assumptions,
queries, and one registered removal choice per scenario. Source extraction requires
the expected full-file identity before recovering complete formulas. Reused source
formulas remain source claims; generated problems and teaching assumptions remain
separate objects.

The target fragment is function-free and first-order. It admits fixed-arity
predicates, object constants, individual variables, explicit quantifiers, Boolean
connectives, implication, biconditional, and equality. Free assertion variables
are universally closed. Where a selected source schema uses a predicate variable,
the study records a finite substitution to a fixed predicate before compilation.
This is one declared schema instance, not unrestricted quantification over
relations. Function applications, unrestricted row-variable expansion, modal
interpretation, and general higher-order translation are outside this laboratory.
Numerals are uninterpreted object constants. No arithmetic, unique-names rule,
or closed-world completion is added implicitly.

These choices matter to interpreting the worked problems. A synthetic witness
such as `StudyHuman` names an assumed teaching entity, not an entity discovered
in the source. Its membership assumption must appear in the retained background.
A countermodel after that assumption is removed demonstrates underdetermination
in the reduced kernel; it does not assert that humans are absent from the intended
source interpretation. Likewise, a class constant and a predicate used to express
a relation occupy distinct syntactic roles in the target language.

### Worked consequence families {#sec:inference-worked}

The taxonomy scenarios use actual source class links with selected source rules.
For example, the `human-taxonomy` case asks for the declared `Human`-to-`Animal`
consequence, while its negative query reverses the direction. A corresponding
membership scenario assumes a teaching witness is a `Human` and asks whether it
inherits `Animal` membership. These are different obligations: a class inclusion
statement and an instance classification. Removing the registered class link or
witness assumption tests the appropriate dependency, rather than merely changing
an expected output label.

Mereological scenarios exercise `properPart`, `part`, and `piece` rules. The
forward proper-part consequence, the exclusion of reverse parthood, and the
converse condition are separate source obligations. Family-relation scenarios
exercise the source argument order: `mother` and `father` relate a child to a
parent, so copying an English subject–object intuition can reverse the query.
Separate attribute consequences concern the relevant parent argument. These
examples show why a generic unlabeled edge cannot stand in for the full formula.

Existential scenarios test whether selected source rules require some witness
without requiring a particular named object. The containment case asks for a
hole and appropriate filling relation; the organism case asks for a parent; the
physical-object case asks for location and time witnesses. The negative queries
can ask for a specific otherwise unconstrained name. Existence of some witness
does not identify that witness with an arbitrary constant. The generated target
must retain this quantifier distinction.

Domain-inheritance scenarios derive selected argument metadata for `daughter`
and `son` from their source subrelation and parent-domain premises. A separate
classification scenario concerns the `subclass` relation entity itself.
Specialized relation-schema cases exercise declared transitivity instances.
Disjointness cases derive explicit negative membership consequences when the
required disjointness rule, source classification, and witness assumption are
present. Those are proofs of a negation under stated premises, unlike a mere
failure to prove positive membership [@sumoSource].

### Adversarial controls and native evidence {#sec:inference-controls}

Each scenario generates related problems with different roles. The background
control contains premises without a conjecture. The positive problem retains
the declared conjecture. The negative-query problem asks a deliberately
unsupported consequence, which need not be the logical negation of the positive
query. The premise-removal variant omits the registered source selection or local
assumption. Finally, the explicit refutation control adds the negated positive
query as an axiom, creating a conjecture-free satisfiability obligation. These
roles prevent conflating an inconsistent background with the intended refutation
of a conjecture's negation.

Expected outcomes are part of the study design; observed outcomes come only from
native execution and valid capture. A desired `Theorem` cannot stand in for a
timeout, missing executable, failed process, or invalid receipt. A removal
countermodel demonstrates necessity relative to that selected comparison. It
does not establish uniqueness of a proof, global premise minimality, or complete
independence of all source axioms. The result vocabulary follows the standardized
SZS result ontology [@tptpSZS].

The runner submits generated problem bytes to E, Vampire, or both, retaining
per-case problem and capture identities. Comparison first requires the same
source selection and problem bytes. A theorem from one prover and a timeout from
the other records a search difference, not contradictory model-theoretic answers.
A theorem and a countermodel claim for identical inputs require investigation of
the native commands, status parsing, tool identities, and proof or model evidence.
Agreement supplies bounded implementation corroboration; it proves neither
general prover correctness nor preservation of the ontology's intended semantics.

The retained laboratory report supplies **{{INFERENCE_SCENARIOS}}** scenarios and
**{{INFERENCE_NATIVE_RUNS}}** native case executions. The following summary is
derived from that report, including its control categories and observed outcomes:

{{INFERENCE_SUMMARY_TABLE}}

### Reproduction and evidence transfer {#sec:inference-reproduction}

The catalog command exposes design without launching a prover. A native run
requires a fresh repository-local destination and a declared per-case budget:

```bash
uv run --locked --no-sync rikishi inference-catalog
uv run --locked --no-sync rikishi inference-run \
  output/inference --prover both --timeout 10
```

Preserve the complete directory rather than copying only the summary. The report
binds selected source formulas, study identity, generated problems, native
captures, implementation and tool identities, expected polarities, and observed
statuses. Portable verification requires the separately retained report digest:

```bash
uv run --locked --no-sync rikishi inference-verify \
  output/inference/inference-report.json \
  --sha256 "$REPORT_SHA256"
```

Here `REPORT_SHA256` is the independently retained expected content fingerprint.
An outer fingerprint identifies the bytes selected by its authority; computing a
fresh fingerprint from an untrusted bundle does not authenticate its history.
Portable replay rederives the supported problems and validates retained evidence
without launching the native prover. Native repetition is a new execution.
Neither operation independently checks every native proof inference, which
remains a separate proof-assurance objective [@reger2017proof].

The dashboard's proof laboratory and read-only agent tools expose the same catalog
and report-verification methods. Source inspection, evidence replay, and new proof
execution remain distinct operations. A claim transferred to a research note must
therefore retain its theory, conjecture, encoding, controls, native execution, and
verification boundary, rather than carrying only a successful status label.

## Restricted proofs and native diagnostics {#sec:native-reasoning}

The taxonomy-proof operation projects direct subclass assertions from *Merge.kif*,
adds explicit transitivity, and submits a conjecture to E. Its result concerns
that restricted obligation. It neither translates arbitrary SUO-KIF nor imports
every domain axiom. Source assertions, projected problem, command, process status,
and output remain separate artifacts.

The native Sigma path supplies a diagnostic case. Saved negative-control
evidence identifies a contradiction in translated cached premises independently
of the conjecture. The retained subset is unsatisfiable, while each single-premise
deletion is satisfiable. This establishes inclusion-minimality for that saved
subset, not uniqueness or minimum cardinality over the complete background.

The localized path combines a source assertion classifying *path* as total, a
generated cache assertion classifying it as partial, and disjointness conditions.
An initial Java diagnostic seeded cache maps before exercising the inheritance
step. A subsequent isolated experiment instead constructs a real fresh knowledge base (KB),
ingests source-only KIF, and calls `KBcache.buildCaches()` without seeded maps.
Both its declared minimal fragment and complete pinned *Merge.kif* input produce
the additional partial classification while retaining the direct total one.
Removing the parent's partial classification or the subrelation edge removes
the generated classification. Adding a synthetic superclass link to
`InheritableRelation` changes the cache's positive membership observation while
leaving the generated classification present. These controls concern generated
classification, not the intended truth of an inheritance rule.

The fresh experiment retains its versioned selections, raw Java warnings,
commands, observations and pre/post source, Java archive (JAR) and toolchain bindings under the
manuscript's research artifacts. It reconstructs the complete Merge file, not
the complete multi-file core profile. Intended inheritance semantics, a
source-to-target argument, and acceptance of a corrected full profile remain
open. Inconsistency of the original ontology is not established.

Positive native statuses remain diagnostic in that context. Rikishi's invocation
adapter now selects Sigma's existing custom Vampire execution route with a fixed
supported option set, preserving upstream preprocessing, translation and assembled
background bytes. Invocation-local profile copies retain the configured source
and serialized-cache inputs with pre/post hashes. The executable, query, profile,
adapter and exact submitted TPTP remain bound to the result. Tiny real Sigma
profiles exercise a theorem and a countermodel; a full-core query that exhausts
its budget remains inconclusive. Refutation of an extracted conjecture-free
translated subset is a separate observation. These outcomes do not establish
consistency of the configured profile or validity of a SUMO interpretation.

Historical contradiction context is checked separately from the query outcome.
After strict capture verification, Rikishi compares the complete ordered TPTP
statement sequence against its registered background under pinned executable,
Sigma-class, lock and profile-configuration identities. Sigma's regenerated
source comments contain invocation-local profile paths, so identical statements
can have different raw file hashes. The existing structural parser omits only
standalone comments and layout; statement text, names, roles, order and any
annotations remain part of the fingerprint. The exact submitted bytes and raw
hashes remain in each capture. Missing or changed statements, changed bindings,
or an invalid capture leave context unknown. This recognizes the registered
translated background; it supplies no equivalence procedure for arbitrary
theories and does not change the query's status or scientific scope.

Readable proof output, premise extraction and independent proof-step checking
are distinct engineering goals [@reger2017proof]. Rikishi structurally extracts
complete named input premises and requires native same-family replay of an
exported subset; it does not independently check every inference in the prover's
proof calculus. Local observations remain distinct from the published campaigns
in [@sec:competency-questions-reengineering-and-benchmarks].

For the translated object $t$ and total/partial classes $T,U$, the retained core
has the following schematic form:

$$
\begin{gathered}
\operatorname{disjoint}(T,U),\quad I(t,T),\quad I(t,U),\\
\forall C,D\;\left(\operatorname{disjoint}(C,D)\Rightarrow
\neg\exists x\,[I(x,C)\land I(x,D)]\right).
\end{gathered}
$$ {#eq:sumo-translated-core}

The saved TPTP premises own the exact replay bytes; this display explains the
refutation's structure. It contains no conjecture. The source inheritance rule
guards propagated relation classifications with `InheritableRelation`, while
the fresh diagnostic observes generated classifications for explicitly retained
inputs. That distinction localizes a question for engineering review without
establishing intended inheritance semantics [@sumoSource].

# A finite variational example {#sec:finite-example}

The example implements the negative evidence lower bound (ELBO) identity used in
variational inference [@blei2017variational, sec. 2.2]. Friston, Kilner and
Harrison connect a variational objective to perception, learning and action by
relating an encoded density to a system that exchanges with its environment
[@friston2006brain, secs. 3–5]. That modeling step supplies the FEP motivation;
the identity alone does not identify an executing system with an organism
[@friston2010principle]. The alignment precedent likewise groups several
free-energy senses [@douglass2024alignment]. Here the modeled object is a finite
variational objective, with natural-log units and a fixed observation. Its
Kullback-Leibler (KL) decompositions specify the reference law explicitly.

::: {.definition #def:finite-model title="Finite generative model"}

Let $S$ be a finite latent carrier, $p(s)$ a normalized prior, and
$\ell(s)=p(o\mid s)$ the selected observation's likelihood. Require positive
evidence. Define the joint, evidence, and exact posterior by

$$
p(s,o)=p(s)\ell(s),\qquad
Z=p(o)=\sum_{s\in S}p(s)\ell(s),\qquad
p(s\mid o)=\frac{p(s,o)}{Z}.
$$ {#eq:finite-model}

:::

The configured example has **{{MODEL_STATE_COUNT}} latent states**. Its parameters
and derived quantities are injected from the packaged model and calculation:

| Quantity | Configured or computed value |
| --- | --- |
| Prior $p$ | {{MODEL_PRIOR}} |
| Observation likelihood $\ell$ | {{MODEL_LIKELIHOOD}} |
| Candidate $q$ | {{MODEL_CANDIDATE}} |
| Joint mass $p(s,o)$ | {{MODEL_JOINT}} |
| Evidence $Z$ | {{FEP_EVIDENCE}} |
| Exact posterior $p(s\mid o)$ | {{MODEL_POSTERIOR}} |

::: {.definition #def:free-energy title="Supported finite variational objective"}

For normalized $q$, require $q(s)>0$ only where $p(s,o)>0$. Define

$$
F(q)=\sum_{s\in S:\,q(s)>0}q(s)\log\frac{q(s)}{p(s,o)}.
$$ {#eq:free-energy}

:::

::: {.proposition #prop:decomposition title="Finite free-energy decomposition"}

On the domain of [@def:finite-model; @def:free-energy],

$$
F(q)=D_{\mathrm{KL}}\!\left(q\Vert p(\cdot\mid o)\right)-\log p(o).
$$ {#eq:decomposition}

Substitution of $p(s,o)=p(s\mid o)p(o)$ into [@eq:free-energy], with normalization
of $q$, gives [@eq:decomposition]. This elementary identity concerns the stated
finite model and support assumptions.

:::

The same objective has a prior-relative decomposition. Write
$H(q)=-\sum_s q(s)\log q(s)$, with zero-mass terms interpreted as zero. Then

$$
\begin{gathered}
F(q)=-H(q)-\mathbb E_q[\log p(s,o)]\\
F(q)=D_{\mathrm{KL}}(q\Vert p)-\mathbb E_q[\log\ell(s)]\\
F(q)=D_{\mathrm{KL}}(q\Vert p(\cdot\mid o))-\log Z.
\end{gathered}
$$ {#eq:finite-objective-forms}

These are decompositions of the same supported finite sum
[@blei2017variational, eqs. 12–14; @friston2006brain, sec. 5]. Logarithmic
expectations are restricted to states with positive $q$, as in
[@def:free-energy]. The prior-relative
term measures departure from prior belief; the posterior-relative term is the
gap above surprise. Calling both simply “the KL term” would confuse their
references. Nonnegativity gives $F(q)\geq-\log Z$, with equality at the exact
posterior. For an approximate family $\mathcal Q$, equality is available only
if that posterior belongs to the family. This example can enumerate its exact
posterior, so it exposes the bound without benchmarking an approximate inference
algorithm [@blei2017variational, secs. 2.1–2.2].

Natural logarithms give nats. At the configured candidate, direct evaluation gives
**{{FEP_FREE_ENERGY}}**, surprise **{{FEP_SURPRISE}}**, and posterior KL
**{{FEP_KL}}**. The floating-point decomposition residual is **{{FEP_RESIDUAL}}**.
At the exact posterior, the computed objective is **{{FEP_OPTIMUM_F}}** and
posterior divergence **{{FEP_OPTIMUM_KL}}**. Display values use the publication
configuration; JavaScript Object Notation (JSON) retains the computed floating-point values.

![Finite inference from one model authority. Model and belief bars distinguish prior, likelihood, posterior and candidate. The objective panel marks the candidate and analytical posterior at {{FEP_POSTERIOR_FIRST}}; the dashed line is surprise. The decomposition compares the surprise bound and posterior divergence in nats.](figures/fep-free-energy.png){#fig:free-energy}

The curve in [@fig:free-energy] and the cover abstract use the same authority as
the parameter table and [@eq:finite-model]. No plotting literal fixes the posterior
location. Changing valid parameters changes the numerical result, prose, and
marker through the same calculation.

Nonfinite, negative, nonnormalized, mismatched, and unsupported inputs reject.
Zero candidate probability contributes zero. Positive candidate mass at zero
joint mass would give an infinite extended-real objective; this finite JSON
interface reports a domain error. Real negative controls exercise those failures.

## Logarithmic evaluation and numerical support {#sec:logarithmic-evaluation}

The numerical kernel now accepts logarithmic prior and likelihood inputs. For
the supported states $T$, write $a_s=\log p(s)$ and $b_s=\log\ell(s)$. A shifted
normalization can be expressed as

$$
\begin{gathered}
b_*=\max_{s\in T} b_s,\qquad r_s=a_s+(b_s-b_*),\qquad
r_*=\max_{s\in T}r_s,\\
L=\log\sum_{s\in T}\exp(r_s-r_*),\\
\log Z=b_*+r_*+L,\qquad
\log p(s\mid o)=r_s-r_*-L.
\end{gathered}
$$ {#eq:logarithmic-normalization}

Shifted weights supply the rounded posterior, while log posterior values retain
support when a positive linear projection underflows. This follows established
shifted-normalization practice; finite-precision error still requires controls
[@blanchard2019logsumexp]. The objective and posterior KL are evaluated separately
from the same supported log inputs, and their decomposition residual is retained.

In the log interface, an input null denotes exact zero mass. An output null
evidence denotes positive evidence below the linear floating-point range; null
log-posterior entries instead denote exact zero support. Rounded positive atoms
are explicitly identified when their linear projections underflow. Impossible
evidence and positive candidate mass on exact zero support reject. The linear
facade preserves arithmetic evidence/posterior projections and directs callers
to the log interface when the evidence itself cannot be represented. No epsilon
replaces a zero-support event.

The explicit JSON-model command provides a thin entrypoint:

```bash
uv run rikishi fep-evaluate \
  examples/fep-log-model.json --logarithmic
```

This numerical extension expands the executable input range while retaining the
same finite objective and support contract.

# Connections to formalization {#sec:formalization}

## What connects SUMO to FEP_Formal? {#sec:bridge-walkthrough}

FEP_Formal is a formalization project; the Free Energy Principle is the broader
scientific and mathematical research programme that motivates it. This paper
uses two pinned finite modules and named instantiations, rather than treating
the repository's name as evidence that every FEP claim has been formalized.
The useful connection is concrete: a probability law and observation kernel
become typed mathematical objects, while selected SUMO expressions describe
their model, representation, calculation and result roles
[@fepFormalProbabilityPinned; @fepFormalPinned; @sumoPinnedMerge].

Consider the registered uniform-prior witness. In state order `(false, true)`,
its prior is ${{NUM_UNIFORM_PRIOR}}$ and the likelihood of observation `true` is
${{NUM_UNIFORM_LIKELIHOOD}}$. The state labels name the two finite alternatives; they do not
assert the truth values of an arbitrary SUMO sentence. One observation leads
to the following connected but distinct questions:

| Lane | Question about the same witness | Specific answer or obligation |
| --- | --- | --- |
| Ontology | What does the named Lean expression represent? | The selected representation rules connect its declared language-relative role to a `represents` consequence; they do not calculate a posterior. |
| Mathematics | What follows from the finite law and kernel? | Joint masses ${{NUM_UNIFORM_JOINT}}$ give evidence ${{NUM_UNIFORM_EVIDENCE}}$ and posterior ${{NUM_UNIFORM_POSTERIOR}}$; Lean checks the stated instances under their hypotheses. |
| Numerical execution | Did the evaluator compute that case correctly? | Bound inputs, exact/reference comparisons and residuals check the returned values, separately from the Lean proof. |
| Simulation | What observations does the specified process generate? | Sampling the persistent state and its kernel produces synthetic histories to compare with exact probabilities. |
| Scientific interpretation | Does the model describe a target system? | Measurement semantics and suitable observations must be supplied in an additional study. |

The exact arithmetic, complete source rules and controlled queries are developed
in [@sec:shared-bridge]; the temporal assumptions are made explicit in
[@sec:witness-sequential]. These connections permit inspection and criticism
of a common case. They supply neither an automatic SUMO-to-Lean translator
nor a transfer of correctness from a representation label to a program.

## Finite elaboration and semantic scope {#sec:finite-elaboration}

The inspected *fep_formal* revision is `{{FORMAL_COMMIT}}`
[@fepFormalPinned]. Source inspection and compilation are distinct observations.
The retained finite elaboration records:

| Formalization observation | Receipt-derived value |
| --- | --- |
| Compiler version | {{LEAN_VERSION}} |
| Pinned finite source modules | {{FORMAL_MODULE_COUNT}} |
| Inspected declaration axiom reports | {{FORMAL_DECLARATION_COUNT}} |
| Compiled dependency artifacts fingerprinted | {{FORMAL_CACHE_FILES}} |

Lean distinguishes elaboration and proof construction from the kernel's checking
of the resulting terms; its extensible automation does not itself identify the
mathematical meaning of an imported domain model [@demoura2021lean4, secs. 2, 5].
Here “formalized” refers to named declarations with explicit types and hypotheses.
The execution claim is narrower still: the receipt identifies which pinned
modules were elaborated and which declarations had their axioms inspected.
Compiler, source, dependency revisions, imported artifacts, outputs, and commands
are recorded.
Complete compiled-library fingerprints are compared before and after elaboration
as a conservative superset of transitive imports. Admitted proofs and unapproved
axioms reject. Existing Mathlib artifacts are inputs; this is not a fresh
dependency build or certification of the complete formalization catalogue.

The pinned `FiniteLaw` carrier contains a real-valued mass function, a proof of
nonnegativity at every atom and a proof that the finite sum is one. A
`FiniteKernel` supplies a normalized output law for each input. Its
`posterior_mul_predictive` theorem reconstructs joint mass from posterior and
positive evidence. These are mathematical real-valued objects, whereas the
Python evaluator uses finite-precision numbers. The mathematical connection must
identify both the carriers and the numerical representation
[@fepFormalProbabilityPinned, lines 28–32, 153–156,
263–281].

For candidate $a$ and reference $b$ on that finite carrier, the information module
defines

$$
\begin{gathered}
H_L(a)=\sum_s\operatorname{negMulLog}(a_s),\\
C_L(a,b)=-\sum_s a_s\log b_s,\\
D_L(a,b)=\sum_s b_s\operatorname{klFun}(a_s/b_s).
\end{gathered}
$$ {#eq:lean-finite-definitions}

These are the definitions `entropy`, `crossEntropy` and `finiteKL`, not an
informal replacement of the last definition by a logarithmic ratio
[@fepFormalPinned, lines 24–34]. The named theorem
`finiteKL_eq_crossEntropy_sub_entropy` assumes $b_s>0$ for **every** state. Its
pointwise helper contributes a correction $b_s-a_s$; normalization cancels the
sum of those corrections, yielding $D_L(a,b)=C_L(a,b)-H_L(a)$
[@fepFormalPinned, lines 135–154]. On that domain, setting $a=q$ and
$b=p(\cdot\mid o)$ connects the pinned KL theorem to the posterior-relative term
in [@eq:decomposition].

Zero reference mass reveals why the hypothesis matters. For the disjoint Boolean
point masses, the pinned declarations state $C_L(\delta_{\mathrm{true}},
\delta_{\mathrm{false}})=0$ and $D_L(\delta_{\mathrm{true}},
\delta_{\mathrm{false}})=1$, using totalized real operations
[@fepFormalPinned, lines 56–72]. Rikishi rejects the corresponding positive
candidate mass on zero joint support. These source-level witnesses distinguish
definitions; they are not new numerical observations in this study. Requiring
strictly positive posterior mass for the shared witnesses below meets the pinned
logarithmic theorem's full-reference-support condition, which is stronger than
the numerical evaluator's candidate-support condition.

Proposed vocabulary mappings identify probability, functions, real-valued
quantities, reasoning, processes, and agents as candidate SUMO connections.
SUMO's distinctions between instance, subclass, relation signature, and function
range make these obligations substantive
[@sec:modeling-commitments-and-source-interpretation]. The author-created FEP
ontology extension remains separate from upstream and from the prior alignment
tables in [@sec:alignment-precedent]. It neither enforces normalization nor
transports a Lean proof.

## From proposed alignment to a tested interpretation {#sec:alignment-method}

A reproducible extension should preserve the original topic and sense, the
versioned alignment row, the proposed mapping relation, and the defining SUMO
axioms. A superclass candidate, an individual classification, a subrelation, and
a merely related concept impose different logical commitments. Their direction
and argument types must be checked before generating axioms. Historical table
entries must also be rechecked against the selected source revision.

Formalization maturity is assessed here per claim and per artifact. The following
ledger distinguishes the evidence already produced by the methods from the
additional obligation needed to enlarge a conclusion:

| Claim and evidence object | Warranted conclusion | Additional obligation |
| --- | --- | --- |
| A pinned, complete source formula and its locator | Identity and context of the inspected commitment [@sec:sumo-demonstrations]. | An interpretation and a submitted problem to assess a consequence. |
| A selected kernel, explicit assumptions and native controls | Observed entailment or counter-satisfiability for that submitted problem [@sec:inference-laboratory]. | A preservation argument to transfer the conclusion to a richer source semantics. |
| Supported numerical inputs, an independent reference and residuals | Agreement of the implemented finite calculation on the measured inputs [@sec:finite-example]. | An error argument or further tests for a wider numerical domain. |
| Pinned Lean declarations, elaboration and inspected axioms | Checking of the named finite mathematical obligations against recorded imports [@sec:finite-elaboration]. | An interpretation connecting other representations to those definitions. |
| One witness authority shared across Lean, numerical and SUMO artifacts | The matched finite study in [@sec:shared-bridge], with each layer's obligations reported separately. | A general translation and proof of preservation to transport arbitrary statements. |
| A proposed biological interpretation | A hypothesis motivated by the FEP literature [@friston2006brain; @friston2010principle]. | Observations, estimation and model criticism for the claimed empirical system. |

Competency questions should include intended consequences and unwanted ones,
following the testing distinctions in
[@sec:competency-questions-reengineering-and-benchmarks]. A syntactically valid
mapping that admits an unintended consequence remains a modeling problem.
The older finite campaign and isolated elaboration remain separate
experiments; the shared-witness study below adds an explicit common input binding.

## Executed finite interpretation and controls {#sec:alignment-campaign}

The packaged study authority `{{ALIGNMENT_AUTHORITY_SHA256}}` fixes the selected
workbook rows, source formulas, sense decisions, resource limits, expected
polarities and numerical tolerances before execution. It retains
{{ALIGNMENT_SOURCE_ROWS}} source rows from the precedent [@douglass2024alignment].
The local content sense places the model beneath `Proposition`; a separate
execution is beneath `Process`. The ordered relation
`abstractCounterpart(model, execution)` uses its selected abstract-first,
physical-second domain commitments. This makes the content/execution distinction
explicit rather than treating every use of “model” as the same ontological sense.

The finite FOL interpretation has a nonempty untyped carrier, class constants,
binary `instance` and `subclass`, selected subclass edges, instance inheritance,
subclass transitivity, Physical/Abstract exclusion and the selected argument
types of `abstractCounterpart`. It omits general SUO-KIF translation, partition
exhaustiveness, universal Entity membership and Sigma cache construction. No
unique-name assumption is added: disjoint inhabited types themselves force the
two local individuals to differ. An empty class may be beneath disjoint branches
without an inhabitant; the inhabited control tests the additional commitment.

{{ALIGNMENT_LOGICAL_TABLE}}

E matched {{ALIGNMENT_LOGICAL_MATCHED}} of {{ALIGNMENT_LOGICAL_CASES}} declared
outcomes; Vampire matched {{ALIGNMENT_V_LOGICAL_MATCHED}} on identical problem
hashes. The {{ALIGNMENT_NATIVE_INVOCATIONS}} retained invocations agree on
{{ALIGNMENT_CROSS_FAMILY_AGREEMENT}} cases. A satisfiable background is required
before campaign completion. Timeout, unknown and mismatched outcomes would
prevent that condition. Agreement is a comparison of statuses for these frozen
problems, not a proof of general solver correctness or full-SUMO consistency.

Separately, the numerical design generated {{ALIGNMENT_MODEL_COUNT}} models in
dimensions {{ALIGNMENT_DIMENSIONS}}, evaluated across prior, uniform, independently
computed posterior and posterior-mode candidates. All
{{ALIGNMENT_NUMERICAL_PASSED}} of {{ALIGNMENT_NUMERICAL_ROWS}} rows passed.
The independent reference uses {{ALIGNMENT_REFERENCE_PRECISION}}-digit Decimal
arithmetic on the exact supplied binary-float log inputs. The following maxima
are absolute errors; permutation reverses the state order, and rescaling checks
the declared likelihood shift and posterior invariance.

{{ALIGNMENT_NUMERICAL_TABLE}}

The ordinary tolerance is {{ALIGNMENT_ORDINARY_TOLERANCE}} and the extreme-case
tolerance is {{ALIGNMENT_EXTREME_TOLERANCE}}. The run passed
{{ALIGNMENT_EXTREME_PASSED}} of {{ALIGNMENT_EXTREME_CASES}} boundary cases and
rejected {{ALIGNMENT_INVALID_REJECTED}} of {{ALIGNMENT_INVALID_CASES}} invalid
inputs. Structural zeros and positive masses below linear floating-point range
remain distinct. Arithmetic and posterior update are checked numerically; they
are not axiomatized by these FOL problems. [@fig:research-controls] shows
all logical polarities and numerical error-to-tolerance ratios. Its
[offline research explorer](../figures/research-dashboard.html) retains individual
rows and complete source provenance.

![Finite first-order logic (FOL) controls, with no full Suggested Upper Merged Ontology (SUMO) consistency claim. Solver keys: E = E theorem prover; V = Vampire. Logical panels show declared polarities and observed outcomes. Numerical panels compare independent-reference, permutation and rescaling errors with their tolerances; exact zeros remain zero. Complete inputs accompany the offline explorer.](figures/research-controls.png){#fig:research-controls}

`research-run` delegates native execution to the same capture methods as direct
prover operation. `research-verify` rederives the retained source selections,
problems, numerical matrix and status interpretation without a live source
index. Saved replay checks internal consistency; a separately trusted outer hash
is needed to detect coherent replacement of a whole evidence bundle. Neither
replay nor cross-family agreement supplies a Lean interpretation, preservation
theorem or empirical validation.

## Shared finite witnesses across representations {#sec:shared-bridge}

The bridge study addresses a concrete gap in running a numerical example beside
an unrelated ontology query: all layers must identify the same finite case.
Its authority fixes Boolean state and observation carriers, strictly positive
rational prior and candidate laws, a complete normalized observation kernel,
the observation `true`, and stable identifiers for the model, its
representation, calculation and result roles. The likelihood in
[@def:finite-model] is the selected column of that kernel; row normalization
concerns observations conditional on each state, not a sum down the selected
column [@fepFormalProbabilityPinned, lines 153–156, 237–243].

The completed campaign instantiates the registered method below. The population
and outcomes are injected from its verified bridge report:
**{{BRIDGE_WITNESSES}}** shared witnesses,
**{{BRIDGE_SCENARIOS}}** SUMO scenarios, **{{BRIDGE_NATIVE_RUNS}}** native
executions and **{{BRIDGE_LEAN_DECLARATIONS}}** **Lean declarations audited
(definitions included)**. A native execution may be a satisfiability or
countermodel control rather than a theorem result; the declaration inventory
also includes entity names, laws and kernel definitions.

{{BRIDGE_SUMMARY_TABLE}}

The numerical columns are floating-point measurements. Scientific notation
preserves nonzero round-off residuals at the exact candidate rather than
displaying them as signed zero; they do not contradict the real-valued
nonnegativity theorem.

### Four referents and the claims attached to them {#sec:bridge-roles}

A shared witness is a common case, not a claim that its artifacts are one
object. The mathematical model specifies a probability law. A Lean expression
represents that model in a language. A calculation is an identified activity
using declared inputs. A result is a record produced by that activity. Keeping
these referents separate allows a reader to ask a more useful question than
whether two vocabularies share a label: *which assertion about which object is
supported by which evidence?*

| Role | Concrete uniform-prior referent | Checkable claim | Evidence that does not replace it |
| --- | --- | --- | --- |
| Model | `BridgeUniformPriorModel`, the declared finite probability specification | The registered prior and every observation-kernel row normalize; the selected evidence is positive. | Classification as `Proposition` or `Abstract` does not prove normalization. |
| Representation | `BridgeUniformPriorLean`, the authored Lean expression | The retained program elaborates the intended finite laws and the named theorem instances. | SUMO `represents` does not certify the expression's denotation or the correctness of a compiler. |
| Calculation | `BridgeUniformPriorCalculation`, the identified evaluation | The retained invocation consumes the matching finite inputs and its numerical values meet the declared reference comparison. | A local `Calculating` classification does not establish that an arbitrary computer execution is a psychological process. |
| Result | `BridgeUniformPriorResult`, the named numerical record | Its exact posterior and measured objective agree with the specified witness. | A `result` role does not make a false number true, and an existential result need not be this named record. |

These are authored referents in the experiment. Calling the first role a
mathematical model does not assert an untested SUMO `MathematicalModel`
classification. The local bridge rule assigns it `Proposition`; the pinned
`(subclass Proposition Abstract)` assertion and membership propagation support
the narrower tested conclusion. Likewise, the three retained state-space
instances are mathematical examples, not observations of an organism. Their
value is that the proposed interpretation can be examined in full, including
the premises that would have to change for a different scientific use.

The diagram in [@fig:bridge-evidence] makes these evidence lanes explicit. Its
shared identifier is an index into obligations; it is not an arrow that
automatically transports truth between logical systems.

![Shared finite witnesses and the evidence attached to their mathematical model, representation, calculation and result roles. Solver keys: E = E theorem prover; V = Vampire. Connections identify common inputs and identifiers; each layer retains its own proof or measurement obligation.](figures/bridge-evidence.png){#fig:bridge-evidence}

### Exact examples that distinguish a model from its posterior {#sec:bridge-exact-examples}

The graphical abstracts on physical pages 2–4 provide a visual introduction;
the following table exposes their exact inputs. Every ordered pair uses state
order `(false, true)`. Values are derived from the retained rational witness
records, rather than rounded from a plotted curve.

The compact row labels correspond to the retained identifiers:
{{BRIDGE_WITNESS_LABELS}}

{{BRIDGE_EXACT_TABLE}}

For the uniform-prior witness, multiplication gives joint masses
${{NUM_UNIFORM_JOINT}}$. Their sum is $Z={{NUM_UNIFORM_EVIDENCE}}$; dividing each mass by $Z$ gives posterior
${{NUM_UNIFORM_POSTERIOR}}$. The complete observation kernel is
$K(s,\mathrm{false})=1-K(s,\mathrm{true})$ together with the displayed
true column. Thus each *row* sums to one, while the selected likelihood column
is not required to sum to one. This distinction separates an observation law
from a distribution over hidden states.

Bayes' rule also exposes what changes between witnesses. With positive entries,
posterior odds factor into prior odds and a likelihood ratio:

$$
\frac{p(S=\mathrm{true}\mid O=\mathrm{true})}{p(S=\mathrm{false}\mid O=\mathrm{true})}
=\frac{p(S=\mathrm{true})}{p(S=\mathrm{false})}
\frac{K(\mathrm{true},\mathrm{true})}{K(\mathrm{false},\mathrm{true})}.
$$ {#eq:bridge-posterior-odds}

In the uniform-prior case the two factors are ${{NUM_UNIFORM_PRIOR_ODDS}}$ and ${{NUM_UNIFORM_LIKELIHOOD_RATIO}}$. In the biased-prior
case they are ${{NUM_BIASED_PRIOR_ODDS}}$ and ${{NUM_BIASED_LIKELIHOOD_RATIO}}$. Both give posterior odds ${{NUM_UNIFORM_POSTERIOR_ODDS}}$, yet the joint masses
and evidences differ. Equal posteriors therefore do not identify equal
generative models or equal surprise. The biased example has $Z={{NUM_BIASED_EVIDENCE}}$ rather
than ${{NUM_UNIFORM_EVIDENCE}}$, and its candidate ${{NUM_BIASED_CANDIDATE}}$ is farther from the common posterior
than the uniform candidate in the measured divergence. Each statement is a
comparison of the declared finite cases, not an ontology entailment about
probability arithmetic.

The exact-candidate witness supplies a complementary test: joint masses
${{NUM_EXACT_JOINT}}$ give $Z={{NUM_EXACT_EVIDENCE}}$ and posterior ${{NUM_EXACT_POSTERIOR}}$, already equal to the
candidate. Over the reals, its posterior divergence is zero and free energy
equals surprise. The retained tiny floating residual is reported rather than
relabelled a negative real divergence. This example tests the equality case
of the finite identity, while the other two expose the gap from a nonoptimal
candidate. Together they distinguish a correct formula, a concrete theorem
instance, a numerical evaluation and its precision boundary
[@fepFormalPinned; @blei2017variational; @blanchard2019logsumexp].

For each witness, the compiled Lean source constructs `FiniteLaw` and
`FiniteKernel` values and proves normalization, positive-evidence and
pointwise exact-posterior obligations. It applies `posterior_mul_predictive`,
`finiteKL_nonneg`, `finiteKL_self` and the full-support
`finiteKL_eq_crossEntropy_sub_entropy` theorem at the pinned definitions
[@fepFormalProbabilityPinned, lines 263–281; @fepFormalPinned, lines 43–54,
146–154]. The numerical branch consumes the same rational model through its
declared floating-point representation and compares the objective and
decomposition with a Decimal reference. Kernel checking establishes the stated
real-valued identities; numerical agreement concerns the declared finite-precision
inputs and tolerance. The retained commands and declaration-axiom audits cover
the concrete module and paired well-formed control environments. Invalid
normalization, a wrong posterior and an admitted proof are rejected by the
registered diagnostic-specific controls; a timeout or unrelated import failure
cannot satisfy those controls. The driver does not prove the complete Python
evaluator correct.

![Finite free-energy measurements for the shared witnesses, derived from the bridge report's numerical comparisons. The decomposition separates surprise from posterior divergence; agreement and residuals concern the declared numerical inputs and reference.](figures/bridge-free-energy.png){#fig:bridge-free-energy}

The SUMO branch makes representation commitments explicit. Two complete source
rules at `Merge.kif:5572–5574` and `5589–5592` are:

```lisp
(=>
  (representsForAgent ?REP ?ENTITY ?AGENT)
  (represents ?REP ?ENTITY))

(=>
  (representsInLanguage ?REP ?ENTITY ?LANGUAGE)
  (exists (?AGENT)
    (representsForAgent ?REP ?ENTITY ?AGENT)))
```

They support representation consequences under the selected local assumptions
[@sumoPinnedMerge, lines 5545–5592]. Their conclusion concerns what stands for
what; `represents` does not state equality of mathematical denotations, a
normalization identity, or preservation of a Lean theorem. The source
`Calculating` subclass assertion at line 15484 and membership rule at lines
146–150 separately support a classification question. Assigning a synthetic
calculation that type is an explicit modeling assumption; the prover does not
infer intentional psychological activity from running a numerical function
[@sumoPinnedMerge, lines 146–150, 15484–15490].

### A source-bound derivation and its counterexamples {#sec:bridge-derivation}

The representation case can be followed without treating the plot as evidence
of logical entailment. Its local premise is

```lisp
(representsInLanguage BridgeUniformPriorLean
                     BridgeUniformPriorModel BridgeLeanLanguage)
```

The second source rule above produces an agent-relative representation for
*some* agent. Applying the first rule to that witness gives

```lisp
(represents BridgeUniformPriorLean BridgeUniformPriorModel)
```

The shared spelling of `BridgeUniformPriorAgent` elsewhere in the study does
not identify the existential agent with that constant. The first-order query
only needs existence. Nor do these premises establish the reverse
representation, that the representation is its referent, or that all formulas
in its language have the same meaning. The registered unsupported query
reverses the arguments; its countermodel control is a concrete test of this
missing converse. Removing the relevant source rule tests dependence on the
derivation, rather than merely checking whether the target sentence appears
somewhere in the file.

The calculation chain is equally specific. Under the local `Calculating`
premise, the retained source subclass chain through
`IntentionalPsychologicalProcess` and `IntentionalProcess` reaches `Process`.
The positive query asks for this inherited membership; the unsupported query
asks for `Abstract`. The three selected subclass premises are at
`Merge.kif:15484`, `13421`, and `13390`, in derivation order. The full source also
links `IntentionalPsychologicalProcess` to `PsychologicalProcess` at line 13423;
that separate axiom is not selected in this kernel and is not credited to this
executed derivation. These separately submitted backgrounds are not combined
into a single full SUMO theory. The type vocabulary brings intentional and
psychological commitments that would require additional justification before
reusing this interpretation for an actual software agent or biological system.
The method makes that scientific modeling choice visible instead of hiding it
behind the word "calculation".

The named-result scenario starts from an additional **local** rule that assigns
the witness model to `Proposition`, the calculation to `Calculating`, and the
named record to its `result` role. It combines the source assertion

```lisp
(disjointRelation result instrument)
```

with a locally authored binary instance of the source disjoint-relation schema.
The intended query excludes the same
record's being an instrument of that calculation. The schema at
`Merge.kif:489–495` contains a row variable; the strict compiler does not translate
that general schema, so the binary instance is identified as a study assumption
[@sumoPinnedMerge, lines 489–495, 3264]. This tests a declared role distinction,
not the correctness of the record's numerical contents.

Source-required result production asks a different question. The complete
source rule is:

```lisp
(=>
  (instance ?DEVELOP ContentDevelopment)
  (exists (?OBJ)
    (and
      (instance ?OBJ ContentBearingObject)
      (result ?DEVELOP ?OBJ))))
```

Under the declared `ContentDevelopment` assumption, it requires some
content-bearing result [@sumoPinnedMerge, lines 16326–16331]. It does not identify
that existential object with the study's named numerical record. The study tests
existence and named-result identification separately, with unsupported-query
and removed-premise controls. Reusing a stable calculation identifier across
scenarios binds their subject without combining their separately declared
backgrounds or adding a unique-name assumption.

Every scenario has a conjecture-free satisfiable-background requirement, a
positive query, an unsupported query, a registered premise removal and an
explicit refutation control for each selected prover. The observed statuses
and denominators come from the report, following the result distinctions in
[@sec:inference-controls].

![Native bridge controls grouped by their declared problem roles and observed statuses. Satisfiable backgrounds, theorem queries, countermodel controls and explicit refutations have separate meanings; counts are derived from retained executions.](figures/bridge-native-controls.png){#fig:bridge-native-controls}

The canonical packet is `output/bridge/bridge-report.json`. Read-only inspection
exposes the catalog, report and individual case evidence; executing a campaign is
a separate operator action. Portable verification requires an independently
supplied outer report fingerprint. The [offline bridge explorer](../figures/bridge-explorer.html) presents the
same report-derived inputs and case evidence without starting a prover.

The shared study connects these representations through matched inputs, checked
finite theorem instantiations and source-bound representation controls. Its
completed report records which obligations were met and retains the generated
sources, exact native problems, commands, diagnostics and numerical references.
Its SUMO theory still contains no probability arithmetic or interpretation
equating `LogFn` with natural logarithms. These experiments do not compose into a
general SUMO-to-Lean preservation theorem; their distinct claims are the rows of
the ledger in [@sec:alignment-method].

### Evidence roles as a research interface {#sec:bridge-research-interface}

The connection suggests a practical unit of scientific integration: a claim
with a typed subject, an explicit interpretation, and the evidence needed to
challenge it. A future probability vocabulary bridge would need a map from
finite events to the propositions accepted by `ProbabilityFn`, together with
normalization, conditioning and arithmetic compatibility. Its real-valued
range alone supplies none of those laws. A logarithm bridge would also need
to relate SUMO's binary positive-integer-base operation to Lean's unary
natural logarithm on its declared domain. Reusing the same identifier is the
beginning of such work, not its preservation proof.

This emphasis connects the study to two complementary traditions. The World
Wide Web Consortium's provenance ontology distinguishes entities, activities
and agents, with qualified usage and generation able to record roles and other
attributes [@lebo2013provo]. It offers a useful design comparison for attaching
the input model, executed calculation and generated record to one case. A
PROV assertion describes provenance; it is not an independent proof that a
computation returned the right value. No equivalence between PROV and the SUMO
case roles is asserted here.

Ologs provide a second comparison: typed arrows and commuting paths express
constraints that an interpretation must satisfy [@spivak2012ologs]. For this
bridge, the relevant future question is whether following "source expression
to finite semantics to result" agrees with an independently defined route
through a target representation. The present study checks named endpoints
and obligations, but has not constructed such a functor or proved a commuting
semantic interpretation. The diagram is an agenda for that theorem, not a
picture of a theorem already established.

| Next experiment | Concrete example | Required evidence before claiming success |
| --- | --- | --- |
| Representation adequacy | An event encoding for the two Boolean states and the observed outcome. | An injective event interpretation where needed, the intended proposition semantics, and positive and collision controls. |
| Operation preservation | Conditioning the uniform-prior model through both SUMO-oriented and Lean-oriented representations. | A stated map for multiplication, summation, division and conditioning, plus a proof that the two routes agree on the declared domain. |
| Result provenance | A posterior record with a model identifier, evaluator version and numerical reference. | Exact input/output custody, declared precision, comparison controls and an explicit distinction between generation and value correctness. |
| Intervention sensitivity | Swap the likelihoods while preserving the prior and separately change the candidate. | Newly registered witnesses, predicted posterior/energy changes, independent arithmetic and fresh native/proof evidence before reporting outcomes. |
| Scientific application | A separately justified observation model for a real agent. | Measurement semantics, empirical design and model criticism in addition to the logical and numerical obligations above. |

These experiments turn an ambitious alignment into falsifiable work. A wrong
representation direction, a nonnormalizing kernel, a mismatched result record
and an unsupported named existential each fail for a different reason. The
current campaign already separates those kinds of obligation; extending its
scientific reach requires retaining that separation while adding the missing
interpretations and evidence.

### A connection atlas with distinct tests at each arrow {#sec:witness-connection-atlas}

The most useful connection is a path that can be challenged at intermediate
steps. For the uniform witness, the representation is
`BridgeUniformPriorLean`, the model is `BridgeUniformPriorModel`, and the
calculation and result have their own identifiers. The following atlas places
the actual expressions beside the mathematical work they do, rather than
using an undifferentiated "verified" label.

| Connection | Actual expression or object | Consequence or calculation | Control that distinguishes the claim |
| --- | --- | --- | --- |
| Source language to representation role | `representsInLanguage(BridgeUniformPriorLean, BridgeUniformPriorModel, BridgeLeanLanguage)` plus the two complete selected SUMO rules | Some representing agent exists, and the expression represents this model. | Reversing the representation query or removing the required rule must not preserve entailment; the existential does not name an agent. |
| Finite specification to a Lean value | `UniformPrior.prior`, `UniformPrior.kernel`, and their `FiniteLaw`/`FiniteKernel` obligations | The prior and each conditional observation row normalize. | The retained wrong-normalization program must fail for its designated obligation, rather than for an unrelated import error. |
| Conditioning to a concrete theorem instance | `UniformPrior.posterior_reconstruction`, using `posterior_mul_predictive` | For each state, posterior mass times positive evidence equals prior mass times selected likelihood: false, ${{NUM_UNIFORM_RECONSTRUCTION_FALSE}}$; true, ${{NUM_UNIFORM_RECONSTRUCTION_TRUE}}$. | The retained wrong-posterior program is rejected; dropping the positive-evidence hypothesis changes the problem. |
| Real-valued objective to evaluated numbers | The full-support finite KL decomposition and the registered numerical evaluator | Joint masses, evidence, free energy, divergence and signed residual are compared with the independent Decimal route. | A result-role statement with a changed numerical tuple is still a role statement, but fails the arithmetic comparison. |
| Result record to a later prediction | Posterior-weighted use of the same kernel, with persistent state and conditional independence made explicit | A second true observation has probability ${{NUM_UNIFORM_NEXT_PREDICTION}}$ for the uniform model and ${{NUM_BIASED_NEXT_PREDICTION}}$ for the biased model. | Redrawing the state instead gives their initial marginal probabilities ${{NUM_UNIFORM_EVIDENCE}}$ and ${{NUM_BIASED_EVIDENCE}}$; these are different experiments. |

The source-to-language arrow merits particular care. Verified compilation
provides a useful methodological comparison: Leroy relates source and target
states through a simulation invariant and matches transitions and observable
effects, including initial and final states [@leroy2009verified, §4.3]. A
future translation of the finite event language would likewise need a stated
relation between interpretations and proofs that relevant operations respect
it. Our endpoint comparisons and selected theorem instances do not constitute
such a general semantic-preservation result. They expose tractable obligations
for attempting one.

There is also an arithmetic boundary inside the apparent numerical arrow.
Exact rational joint masses, a real logarithmic identity and a finite-precision
returned value are three different objects. Harrison's verified floating-point
examples supplement exact reasoning with explicit rounding bounds, and
separate function-approximation error from evaluation error
[@harrison2006floating, §4.2 and the trigonometric-function discussion]. Here
the reference comparisons test the actual retained inputs; no theorem bounds
every execution of the Python evaluator. This is why the tiny signed residual
at the exact candidate remains visible alongside the real equality case.

## Changing representations without confusing the evidence {#sec:witness-channels}

The shared cases support a further executable experiment: change the finite
representation while keeping explicit track of the information it discards.
This derived analysis uses the same rational inputs, but does not add cases to
the historical SUMO campaign or declarations to its Lean receipt. Its exact
masses, {{NUM_RESEARCH_PRECISION}}-digit Decimal logarithms and source report digest are exported in
`witness-research.json`. Exact arithmetic establishes the displayed rational
equalities; numerical residuals and their declared tolerances remain separate.

Let $T_{sa}$ be a nonnegative, row-stochastic channel from fine states $s$ to
reported states $a$. With joint mass $j_s=p_sK(s,\mathrm{true})$, define

$$
p'_a=\sum_s p_sT_{sa},\qquad
j'_a=\sum_s j_sT_{sa},\qquad
K'(a,\mathrm{true})=j'_a/p'_a.
$$ {#eq:coarse-state-model}

The last expression is defined on positive coarse prior support, which all
outputs of the four channels used here satisfy. It is a **prior-weighted**
induced observation model, not an unweighted average of likelihood entries.
Because the channel rows sum to one, $\sum_a j'_a=Z$ and the coarse posterior
is $r'=rT$. Thus conditioning the induced model agrees exactly with pushing
the original posterior forward. The candidate must pass through the *same*
channel, $q'=qT$, for the information comparison below.

This calculation connects concretely to the pinned FEP_Formal application
programming interface (API). Its
`FiniteKernel.comp later earlier` multiplies and sums kernel masses, supplies
nonnegativity and row-normalization proofs, and `predictive_comp` identifies
the two routes through sequential prediction
[@fepFormalProbabilityPinned, lines 190–209, 246–254]. These source declarations
motivate the typed comparison; this new Python experiment does not claim that
the retained Lean execution proved its channel contraction or its induced
conditioning construction. Markov-kernel scholarship provides a broader
language for composition and conditioning while retaining their different
types [@fritz2020synthetic].

For the uniform case, the noisy state channel has rows ${{NUM_UNIFORM_NOISY_CHANNEL_FALSE}}$ and
${{NUM_UNIFORM_NOISY_CHANNEL_TRUE}}$. It gives $p'={{NUM_UNIFORM_COARSE_PRIOR}}$, $j'={{NUM_UNIFORM_COARSE_JOINT}}$,
$K'(\cdot,\mathrm{true})={{NUM_UNIFORM_COARSE_LIKELIHOOD}}$ and $r'={{NUM_UNIFORM_COARSE_POSTERIOR}}$, with unchanged
$Z={{NUM_UNIFORM_EVIDENCE}}$. For the singleton erasure channel the coarse likelihood is simply
$Z$. Its three values are therefore ${{NUM_UNIFORM_EVIDENCE}}$, ${{NUM_BIASED_EVIDENCE}}$ and ${{NUM_EXACT_EVIDENCE}}$. Unweighted
averaging would instead give ${{NUM_UNIFORM_UNWEIGHTED_LIKELIHOOD}}$, ${{NUM_BIASED_UNWEIGHTED_LIKELIHOOD}}$ and ${{NUM_EXACT_UNWEIGHTED_LIKELIHOOD}}$: the uniform case alone
would conceal that error, while the other two cases expose it.

### A smaller divergence need not mean better inference {#sec:witness-information-loss}

For a common stochastic channel, the classical data-processing inequality
states $D(qT\Vert rT)\leq D(q\Vert r)$ [@vanerven2014renyi, Theorem 9,
order one]. In the finite supported setting, the log-sum inequality applied
at each output to $q_sT_{sa}$ and $r_sT_{sa}$ yields this bound. Summing the
right-hand terms uses $\sum_aT_{sa}=1$. Terms with zero candidate mass
contribute zero; positive candidate mass outside reference support requires
an explicit support treatment. The new evaluator rejects that unsupported
finite-log calculation rather than emitting an infinite value as a JSON number.

{{WITNESS_CHANNEL_TABLE}}

Uniform, Biased and Exact refer to the registered witness identifiers already
defined above. Identity and state-label permutation preserve divergence;
the noisy channel reduces the first two gaps; singleton erasure makes all
coarse candidate/posterior pairs equal. In particular, the uniform case falls
from approximately ${{NUM_UNIFORM_KL_BEFORE}}$ to ${{NUM_UNIFORM_KL_AFTER}}$ nats under noise, and to zero under
erasure. Its original candidate has not been repaired. The exact-candidate
case remains equal without needing loss. This distinguishes optimization of
the original inference problem from loss of the ability to tell two answers
apart. With evidence unchanged, the induced coarse objective is
$F'(qT)=-\log Z+D(qT\Vert rT)$; it belongs to a changed state description.

![Changing a finite state representation can hide candidate error. Identity, label swap, shared noisy channel and singleton erasure are applied to both candidate and posterior. Kullback-Leibler (KL) divergence uses natural-log nats; a smaller coarse divergence is not improved inference on the original state space. Exact inputs and numerical tolerances accompany the source-bound data export.](figures/witness-channels.png){#fig:witness-channels}

### State aggregation and observation degradation are different experiments {#sec:witness-observation-noise}

The previous channel changes what hidden state is reported. A channel on the
**observation** instead changes the event being conditioned on. Suppose the
Boolean observation is flipped with probability $e={{NUM_UNIFORM_OBSERVATION_ERROR}}$. The likelihood of
the newly observed true output is $e+(1-2e)K(s,\mathrm{true})$. Exact conditioning
now gives the uniform posterior ${{NUM_UNIFORM_NOISY_POSTERIOR}}$ at evidence ${{NUM_UNIFORM_NOISY_EVIDENCE}}$; the biased
posterior ${{NUM_BIASED_NOISY_POSTERIOR}}$ at evidence ${{NUM_BIASED_NOISY_EVIDENCE}}$; and the exact-candidate model's
posterior ${{NUM_EXACT_NOISY_POSTERIOR}}$ at evidence ${{NUM_EXACT_NOISY_EVIDENCE}}$. The last model's old candidate
${{NUM_EXACT_CANDIDATE}}$ is no longer its posterior. This changes a hypothesis, not the
truth of its earlier equality instance. Completely erasing observations
would recover the hidden-state prior; completely erasing hidden-state
identity gives a singleton posterior. The domains and codomains of the arrows
explain why those answers differ.

## Posterior identity, observation evidence and model comparison {#sec:witness-model-evidence}

There is another controlled way to preserve a posterior. Multiply only the
selected likelihood column by $c>0$ while keeping it in $[0,1]$, and complete
each Boolean observation row with $1-cK(s,\mathrm{true})$. Then

$$
Z_c=cZ,\qquad r_c=r,\qquad
F_c(q)=F(q)-\log c.
$$ {#eq:likelihood-scaling}

For $c={{NUM_UNIFORM_EVIDENCE_SCALE}}$ all three current models remain valid and their exact posteriors
remain unchanged. This is a changed observation kernel, not multiplication
of every entry of a normalized row by the same constant. Posterior KL stays
the same for the same candidate; surprise and absolute free energy rise by
$\log {{NUM_UNIFORM_SCALE_RECIPROCAL}}$. Consequently a posterior record alone cannot identify its evidence,
its complete generative model or its absolute variational objective.

{{WITNESS_SCALING_TABLE}}

![Identical posteriors can accompany different observation evidence. Scaling the selected likelihood column by {{NUM_UNIFORM_EVIDENCE_SCALE}} and completing the other Boolean outcome preserves each posterior while increasing surprise and free energy by log {{NUM_UNIFORM_SCALE_RECIPROCAL}} for a fixed candidate. Model, representation, calculation and result provenance remain distinct obligations. The transformed models are derived finite experiments, not new native ontology or Lean proof results.](figures/witness-evidence-scaling.png){#fig:witness-evidence-scaling}

Model comparison introduces a different random variable, $M$. Treating the
uniform and biased toy models as alternatives for the same observation, with
equal prior model probabilities, gives Bayes factor
$Z_{\mathrm{biased}}/Z_{\mathrm{uniform}}={{NUM_BAYES_FACTOR}}$ and posterior model probability
$P(M=\mathrm{biased}\mid\mathrm{true})={{NUM_BIASED_MODEL_POSTERIOR}}$. These are ratios of declared
marginal observation probabilities, not posterior-state divergences; unequal
prior model odds would multiply the factor [@kass1995bayes]. No empirical
evidence-strength label is attached to this synthetic comparison.

Equal state posteriors also need not imply equal predictions. **If** a second
observation uses the same hidden state and the same kernel, with observations
conditionally independent given that state and model, its true probability is
$\sum_s r_sK(s,\mathrm{true})$. The three exact values are ${{NUM_UNIFORM_NEXT_PREDICTION}}$, ${{NUM_BIASED_NEXT_PREDICTION}}$ and
${{NUM_EXACT_NEXT_PREDICTION}}$. The first two differ despite their common current state posterior.
Redrawing a new hidden state would define another model and another prediction.
The added assumption is stated here and in the method contract; it is not
silently attributed to the original native campaign.

## Sequential inference, simulation and prediction {#sec:witness-sequential}

The next experiment makes the additional temporal assumptions executable.
One latent Boolean state is drawn once and retained within each trajectory;
the observation kernel is unchanged, and observations are conditionally
independent given that state and model. We condition on a prefix of $n$ true
observations. With $\ell_s=K(s,\mathrm{true})$, its exact probability is
$Z_n=\sum_s p_s\ell_s^n$, its state posterior is
$r_n(s)=p_s\ell_s^n/Z_n$, and the next true-observation probability is
$a_n=\sum_s r_n(s)\ell_s=Z_{n+1}/Z_n$. At $n=0$, $Z_0=1$ and $r_0=p$.
These quantities are computed for every $n$ from zero through twelve using
rational arithmetic. An independent iterative route updates the preceding
posterior and multiplies the successive predictive probabilities; it must
agree exactly with the direct products.

{{WITNESS_SEQUENTIAL_TABLE}}

The first observation makes the uniform and biased posteriors identical,
${{NUM_UNIFORM_POSTERIOR}}$, but their second updates separate them. At $n=2$ the uniform
posterior is ${{NUM_UNIFORM_STEP2_POSTERIOR}}$ with $Z_2={{NUM_UNIFORM_STEP2_EVIDENCE}}$, whereas the biased posterior is
${{NUM_BIASED_STEP2_POSTERIOR}}$ with $Z_2={{NUM_BIASED_STEP2_EVIDENCE}}$. For the third model it is
${{NUM_EXACT_STEP2_POSTERIOR}}$ with $Z_2={{NUM_EXACT_STEP2_EVIDENCE}}$. A candidate that was exact after one
observation is therefore not automatically exact after a new observation.
The kernels, not just the current posterior vectors, determine these
trajectories. The equations also identify the persistence assumption as
testable: independently redrawing the state before every observation would
instead give prefix probability $Z_1^n$. For the uniform model at $n=2$ that
would be ${{NUM_UNIFORM_REDRAWN_STEP2_EVIDENCE}}$, rather than the persistent-state value ${{NUM_UNIFORM_STEP2_EVIDENCE}}$.

The forward simulation provides a separate, deliberately less exact view.
For each model it generates {{NUM_SIMULATION_TRIALS}} trajectories with a recorded fixed seed,
samples the state once per trajectory, then samples the {{NUM_SIMULATION_STEPS}} observations
from that state's kernel. At each prefix it retains the integer number of
surviving all-true trajectories and how many have latent state false.
Dividing those counts gives an empirical prefix probability and, when the
survivor count is positive, an empirical posterior. The exported
`witness-dynamics.json` retains the counts, generator identity and exact
rational answers. The plotted simulation marks are observations of this
synthetic generator, not extra Lean declarations, new ontology outcomes,
confidence bounds or biological data. Rare long prefixes have fewer surviving
trajectories, so a deterministic and internally consistent simulation record
still does not replace exact conditioning.

The direction of this procedure matters. Forward generation starts with a
specified model and produces synthetic observations. Conditioning starts with
a specified observation history and computes a distribution over its possible
hidden causes. The simulator implements the former, then uses surviving
histories to estimate quantities that the exact calculation obtains by the
latter. It is not a Markov chain Monte Carlo sampler of an unknown posterior.
Generating replications from a posterior and checking them against actual data
would be a further model-assessment step [@gelman2020workflow, §§2.4, 4.1, 6.1].
Here the observations are generated by the very model being examined, so
agreement with exact conditioning checks implementation and assumptions rather
than empirical fit.

Nor does the changing posterior imply that the simulated hidden state moves:
the state remains fixed within a trajectory. Discrete active-inference models
add action-dependent transitions, policy evaluation and action selection;
their expected-free-energy objective concerns prospective courses of action
[@dacosta2020discrete, arXiv v2, §§3, 6–7]. Those components are not implemented
by the present fixed-state simulation. Its role is to make a tractable
inference ingredient, and the evidence attached to it, inspectable before
claiming a larger agent model.

![Sequential inference links exact mathematics to a seeded forward simulation. Each trajectory holds its hidden state fixed; observations are conditionally independent given that state and model. Exact posterior and next-observation paths are distinguished from empirical prefix counts, and the uniform/biased model comparison uses cumulative observation evidence. All values are derived from the same three registered witnesses; no new native SUMO or Lean proof result is claimed.](figures/witness-sequential.png){#fig:witness-sequential}

The model-comparison path is different again. With equal prior probabilities
on the uniform and biased models, their probability after an all-true prefix
is obtained by normalizing their two $Z_n$ values. The biased-model
probability changes from ${{NUM_BIASED_MODEL_POSTERIOR}}$ after one observation to ${{NUM_BIASED_MODEL_POSTERIOR_STEP2}}$ after two.
For a fixed model, the chain identity
$\log Z_n=\sum_{t=0}^{n-1}\log a_t$ expresses the sequence probability as
a sum of conditional log scores. Thus the difference of those cumulative
scores is a log Bayes factor. This compares probabilities of an observation
history; it is not the KL divergence between a variational candidate and a
state posterior. Gneiting and Raftery explain logarithmic scoring and its
connection to Bayes factors, including the distinction between forecasts
specified before assessment and models fitted using the scored data
[@gneiting2007proper, §§4, 7.1]. Here the cases are fixed synthetic models,
not a model-selection claim about measured organisms.

### Mixed histories expose the observation model {#sec:witness-mixed-sequences}

An all-true prefix is only one possible observation history. The complete
kernel also assigns probabilities to false outcomes. For an ordered history
$y_{1:n}$, define the unnormalized state mass
$j_n(s)=p_s\prod_{t=1}^{n}K(s,y_t)$, its evidence $Z_n=\sum_s j_n(s)$,
and posterior $r_n(s)=j_n(s)/Z_n$ when $Z_n>0$. The next-observation law
is $a_n(y)=\sum_s r_n(s)K(s,y)$. Sequential Bayes updates and the direct
joint products must agree exactly at every prefix, including the empty one.
An impossible history is rejected rather than assigned a fabricated posterior.

{{WITNESS_SEQUENCE_ATLAS_TABLE}}

The atlas enumerates all eight length-three histories for all three models.
Within a fixed persistent-state model, histories with the same counts of true
and false outcomes have equal evidence and final posterior: multiplication of
the same likelihood factors commutes. Their intermediate posteriors need not
coincide. This is an exchangeability property of the declared model, not a
claim that time order can be ignored in arbitrary dynamical systems.

Model uncertainty adds another normalization. With declared model probabilities
$\pi_m$, the weight after the history is
$w_m=\pi_m Z_{m,n}/\sum_k\pi_k Z_{k,n}$, and the model-averaged next law is
$\sum_m w_m a_{m,n}(y)$. This denominator differs from a state posterior's
denominator. A model that makes the history impossible receives zero weight;
if every positive-prior model makes it impossible, the comparison is undefined
and rejects. The default atlas compares only uniform and biased models with
equal prior weights; the third model is displayed separately, not silently
added to that comparison. Independently redrawing the hidden state gives
$\prod_t\sum_s p_sK(s,y_t)$ instead of the persistent-state joint sum, providing
a concrete model-assumption counterexample for the same symbols.

![All eight mixed Boolean observation histories connect complete kernels to exact joint probabilities, state posteriors, next-observation laws and two-model posterior weights. Every fraction is generated from the registered witnesses; identical-count histories expose the fixed-state exchangeability assumption. Model E is not included in the uniform/biased comparison. The source JSON also retains the distinct redrawn-state probabilities; these are derived mathematical examples, not additional Lean declarations, ontology outcomes or empirical observations.](figures/witness-sequences.png){#fig:witness-sequences}

### Model checking has several different meanings {#sec:witness-model-checking}

A well-formed kernel, a successful theorem instance, a reproduced simulation
and a good empirical forecast answer different questions. Predictive
calibration concerns the relation between forecasts and realized outcomes;
sharpness concerns concentration of the forecasts themselves
[@gneiting2007calibration, p. 243]. Neither normalization nor an increasingly
concentrated posterior establishes calibration. Similarly, computational
science distinguishes adjusting parameters against selected data from
assessing predictive capability for a specified application
[@trucano2006calibration, §1]. The latter requires empirical commitments that
the three toy models do not supply.

The distinction matters for selecting diagnostics. Gneiting, Balabdaoui and
Raftery's probability-integral-transform characterization assumes continuous,
strictly increasing forecast distributions and stated dependence conditions;
their examples show why a visually uniform histogram alone is not a universal
certificate of forecast quality [@gneiting2007calibration, §§2.1, 2.4, 3.1].
Our Boolean examples do not satisfy that continuous-outcome setup. Evaluating
them empirically would instead require an appropriate binary-event protocol
and observations kept separate from model fitting. No such empirical assessment
is supplied by the exact atlas or seeded trajectories.

| Question | Evidence available here | Additional evidence needed for a scientific application |
| --- | --- | --- |
| Does the expression select the intended referent? | Pinned source formulas, local premises and direction-sensitive native controls. | A justified interpretation of measured events and model entities. |
| Is the finite update mathematically well formed? | Rational normalization and conditioning; the retained concrete Lean obligations. | Formalization of any new state, observation or temporal assumptions. |
| Does this implementation compute the declared example? | Direct/iterative exact agreement, retained simulation counts and independent numerical comparisons. | Error bounds for broader arithmetic regimes and implementation-level assurance as required. |
| Does the forecast predict observations well? | Declared synthetic predictive probabilities, with no empirical success claim. | Outcomes withheld from fitting, suitable proper scores, calibration diagnostics and uncertainty analysis. |
| Does the model explain the target system? | An explicit, inspectable example of the inferential architecture. | Domain-specific measurement semantics, comparison models, model-discrepancy analysis and empirical validation. |

The research opportunity is to make these obligations composable at the level
of a particular claim. A SUMO expression can identify an event or a calculation;
a Lean value can state its finite semantics; exact algebra can expose an
invariant; simulation can reveal consequences of a specified generative
process; and subsequent observations can challenge its predictions. A useful
connection records which of those steps has evidence and which still needs it.

## What an ontology expression would have to preserve {#sec:witness-interpretation-contract}

The SUMO distinction remains substantive. In the pinned source,
`ProbabilityFn` is a unary function with domain `Formula` and range
`RealNumber` [@sumoPinnedMerge, lines 3334–3338]. A finite state's mass is not
automatically an application of that function. A proposed bridge must first
assign each finite event a proposition, specify its probability semantics,
and preserve the operations needed by the intended claim. The current
uninterpreted mass labels in the selected first-order kernels do not do that.

A two-state collision demonstrates the missing obligation. Let
$A=\{\mathrm{false}\}$ and $B=\{\mathrm{true}\}$, and map both states to a
single coarse state. Direct images of $A$ and $B$ are the same nonempty event,
so their intersection is nonempty although the image of $A\cap B$ is empty.
This map preserves total mass but not the intersection structure of fine
events. Inverse images preserve Boolean event operations in the other
direction, but cannot recover every fine distinction from a coarse event.
Thus a `represents` assertion and matching posterior values do not establish
faithfulness of an event interpretation.

This obstruction is now executable in a separate, deliberately small event
interface. `FiniteStateMap` validates explicit finite carriers, total state
assignments and event membership; it computes exact direct images, inverse
images and probability pushforwards. Bijective relabeling and many-to-one
coarsening therefore have different, testable operation-preservation behavior.
The companion [Lean source](../figures/EventTransport.lean) states inverse-image
preservation of union, intersection and complement, together with the concrete
Boolean-to-unit intersection failure. These four statements are separate from
the retained bridge declaration population. They concern event operations,
not the semantics of arbitrary SUMO sentences, verified Python execution or
the empirical interpretation of a hidden state.

A precise future restricted goal would pair a sentence translation $\tau$
with a target-model interpretation $R$ and require compatibility of
satisfaction, $M'\models\tau(\varphi)$ exactly when
$R(M')\models\varphi$. Institution theory makes that compatibility central
to change of notation [@goguen1992institutions]. Here it is a proposed
contract for a deliberately small event language, not an institution morphism
between complete SUMO and Lean. The direction of the model map, admissible
sentences, support assumptions and operation-preservation proofs would all
need to be supplied.

Finally, evidence about a result is itself represented and generated.
An evaluator may produce a posterior entity; a separate checking activity
uses that entity, the exact input and an independent reference to produce a
checking receipt. PROV-DM bundles support descriptions of provenance, while
PROV constraints check consistent histories rather than numerical truth
[@moreau2013provdm; @cheney2013provconstraints]. Replacing the uniform result
by $(1/3,2/3)$ can leave an otherwise identical role graph well formed, yet
fail the exact arithmetic check. Conversely, a correct tuple without a bound
execution record does not establish that a claimed activity occurred.
PROV responsibility, SUMO's existential representing agent, and an empirical
cognitive agent therefore remain different commitments. These distinctions
make the shared-witness interface useful for scientific model criticism
without making a new biological claim.

# Reproducibility and contribution {#sec:reproducibility}

## Publication from declared authorities {#sec:publication}

The scientific body is authored once. A checked context injects corpus
measurements, model values, version, source revisions, compiler information,
and author metadata from their authorities. Bibliography keys resolve through
native citation processing. Template filters generate section, formalism,
equation, and figure labels. References such as [@def:finite-model],
[@prop:decomposition], [@eq:decomposition], and [@fig:free-energy] are generated labels,
not manually assigned numbers.

Actual docxology/template combined Portable Document Format (PDF) and Hypertext
Markup Language (HTML) adapters and the native Word (.docx)
adapter render the editions from a verified Git archive. PDF uses its configured
image cover and author block; HTML and Word receive a source-derived frontmatter
projection. All editions share the body, bibliography, substitutions, and labels.
The unnumbered cover image does not advance body-figure numbering.

A receipt binds source inputs, staged projections, graphical data, imported
renderer modules, and final hashes. Preflight rejects unresolved substitutions,
missing citations, invalid labels, and conflicting measurements. Output checks
inspect actual references, author metadata, equations, and image bytes. These
controls establish artifact integrity, not scientific validity or perfect
typography.

## Operator workflow and limits {#sec:workflow}

1. Prepare the declared Python environment and external storage bindings.
1. Acquire the pinned SUMO sources and runtime, then record identities.
1. Index and audit source bytes; regenerate measurements and graphics.
1. Retain queries, exact prover inputs, diagnostics, and outputs together.
1. Run finite numerical and formal checks with their explicit scope.
1. Render the manuscript and inspect every PDF page and native edition.

Upstream issues and pull requests require a minimal independently reproduced
finding and a precise claim. Unknown search status is not falsity. An unexpected
consequence can expose an intended-model problem even when the prover succeeds.
Private research remains private unless deliberately released.

The claim ledger in [@sec:alignment-method] specifies the remaining mathematical,
semantic and empirical obligations. Public hosting additionally requires a
separately evaluated deployment.

## Licensing and attribution {#sec:licensing}

Copyright © 2026 Daniel Ari Friedman. Original manuscript text and figures are
licensed under [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).
Software, figure-generating code and original code/Lean listings remain MIT
licensed. Quoted or reproduced third-party material retains its own attribution
and terms; this grant covers only the author's original contributions.

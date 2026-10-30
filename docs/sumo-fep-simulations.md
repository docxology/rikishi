# How the Suggested Upper Merged Ontology (SUMO), FEP_Formal and simulations connect

SUMO provides an axiomatized vocabulary for describing entities and their
relations. FEP_Formal supplies mathematical definitions and statements in Lean.
Rikishi binds selected examples from both to numerical calculations and
synthetic simulations. A useful connection identifies the same model and
inputs across those activities while keeping their claims distinct.

## What SUMO is and what it does

The Suggested Upper Merged Ontology (SUMO) is an upper ontology: reusable
categories, relations and axioms intended to support more specialized domain
theories. It helps make modeling commitments explicit and supports reasoning
about their consequences. Its source is more than a list of names or a graph
of parent classes.

For example, `instance` relates an individual to a class, whereas `subclass`
relates classes. A membership-propagation rule can connect those assertions
to a further classification. A `domain` assertion constrains a relation's
argument, and a representation rule can constrain what an expression stands
for. Whether a particular conjecture follows requires the relevant source
formulas, local assumptions and reasoning interpretation.

Keep four names separate:

| Name | Role |
| --- | --- |
| SUMO | The ontology's vocabulary and axioms |
| Standard Upper Ontology Knowledge Interchange Format (SUO-KIF) | The language used to express its source formulas |
| Sigma Knowledge Engineering Environment (KEE) | An environment for browsing, developing, translating and querying the ontology |
| Rikishi | A workbench for pinned source inspection, selected experiments, reusable methods and retained evidence |

Primary sources: [Niles and Pease (2001)](https://doi.org/10.1145/505168.505170),
[Pease and Schulz (2014)](https://doi.org/10.1007/978-3-319-08587-6_40),
and the [pinned source distribution](https://github.com/ontologyportal/sumo/tree/efcd059f8feebfe3488a09f575f88d4d009b1e5c).
See [worked SUMO demonstrations](sumo-demonstrations.md) for actual source examples.

## What FEP_Formal contributes

The Free Energy Principle (FEP) is a broader research programme. FEP_Formal is
a versioned formalization project; its name is not a claim that every FEP
statement or biological interpretation has been proved.

Rikishi selects two committed Lean modules at revision
`9a0694f16b8e89b66b2f7f8cc7426c650dd2c4de`:

- [`finite_probability.lean`](https://github.com/ActiveInferenceInstitute/fep_formal/blob/9a0694f16b8e89b66b2f7f8cc7426c650dd2c4de/lean/FepSketches/finite_probability.lean)
  defines normalized `FiniteLaw` and `FiniteKernel` objects and finite
  conditioning/reconstruction statements.
- [`finite_information.lean`](https://github.com/ActiveInferenceInstitute/fep_formal/blob/9a0694f16b8e89b66b2f7f8cc7426c650dd2c4de/lean/FepSketches/finite_information.lean)
  defines information quantities and proves named identities under their hypotheses.

The logarithmic cross-entropy identity requires strictly positive reference
mass at every atom. The source's totalized zero conventions and the numerical
evaluator's support policy have different boundaries. The
[finite FEP guide](fep.md) and [formal method contract](bridge-methods.md#concrete-formal-obligations)
explain those conditions and the separate compilation evidence.

## One case, five questions

Use the existing `uniform-prior` witness from the
[registered authority](../src/rikishi/data/fep-sumo-bridge-v1.json).
Both state and observation carriers have order `(false, true)`.
These are finite alternative labels, not a translation of arbitrary logical
truth into probability.

The prior is `(1/2, 1/2)`. The complete observation kernel is:

| Hidden state | Observation false | Observation true |
| --- | --- | --- |
| false | 3/4 | 1/4 |
| true | 1/4 | 3/4 |

Each row sums to one. After observing true, use the true column as likelihoods
across states. Such a selected likelihood column is not generally required to
sum to one, even though this particular column happens to do so.

| Step | Exact result | Role |
| --- | --- | --- |
| Multiply prior and selected likelihood | `(1/8, 3/8)` | Joint masses |
| Sum joint masses | `1/2` | Observation evidence |
| Normalize joint masses | `(1/4, 3/4)` | State posterior |
| Average the true likelihood under that posterior | `5/8` | Next-observation probability if the state persists |
| Multiply first evidence by that prediction | `5/16` | Probability of two true observations with the same hidden state |

The ontology lane asks what the named objects represent and which role
consequences follow from declared premises. Lean checks named mathematical
statements about the finite law. Numerical checks assess the returned values
against independent references. Simulation samples the declared model. A
scientific application must additionally relate the states and observations
to a target system and suitable measurements.

A local SUO-KIF premise such as

```lisp
(representsInLanguage BridgeUniformPriorLean
                     BridgeUniformPriorModel BridgeLeanLanguage)
```

can participate in the selected representation derivation. It does not
calculate the fractions above or establish that a particular result record
contains the correct numbers. Similarly, classifying a synthetic calculation
as `Calculating` is an explicit local modeling choice, not a conclusion that
every Python evaluation is a psychological process.

The [bridge contract](bridge-methods.md#exact-source-kernels-and-local-interpretation)
retains the actual SUO-KIF, local premises and native controls. The
[scholarship ledger](scholarship.md) separates a source citation from evidence
that a command actually ran.

## What the simulations show

The implemented forward simulator draws a hidden state from the prior once
per trajectory. It then samples observations from that state's kernel.
Conditioning on an all-true prefix selects surviving trajectories; their
state counts can be compared with exact Bayesian conditioning.

The persistence assumption is consequential. Drawing a new state before every
observation changes the two-true probability in the uniform example from
`5/16` to `1/4`. These are two generative models, even if they reuse the same
single-observation prior and likelihood.

The registered biased-prior witness illustrates another distinction: its
one-observation posterior is also `(1/4, 3/4)`, but its evidence is `2/3` and
its next true-observation probability is `11/16`. Equal current posteriors do
not identify the same generative model or the same future predictions.

The retained simulation is a reproducible synthetic check, not MCMC,
simulation-based calibration or an empirical validation study. Posterior
predictive assessment would additionally compare suitable model replications
with observed data. [Bayesian Workflow](https://arxiv.org/html/2011.01808v1)
distinguishes these tasks. A fixed random seed provides repeatability; it does
not supply confidence bounds, good calibration or an appropriate model.

## How this relates to active inference

The finite free-energy identity is an inference ingredient. A simulated
active-inference agent additionally needs a generative model with actions,
policies and their consequences. The present simulator has no action-selection
loop; see [Da Costa et al.'s discrete-state synthesis](https://arxiv.org/html/2001.07203v2).
The separate [one-step planner](active-inference.md), exposed by `active-demo`,
now supplies explicit action transitions, observation channels, outcome preferences
and numerical selection. Its filtering method can consume an actual supplied
outcome. It does not retrofit an agent loop or new proof into this fixed-state
simulation; the two methods answer different questions.

A longer-horizon agent would have to declare the state/observation meaning, temporal and
action assumptions, mathematical obligations, implementation checks and
measurement protocol. Shared identifiers could then attach evidence to those
specific commitments. SUMO contributes representational structure; Lean
contributes stated mathematical guarantees; simulation exposes consequences
of the chosen assumptions; observations can test the resulting predictions.

## Continue by question

- Source formula, typing or reasoning: [SUMO demonstrations](sumo-demonstrations.md)
  and [inference tutorial](inference-tutorial.md).
- Objective, support or numerical conventions: [finite FEP](fep.md).
- Same-witness Lean, ontology and numerical evidence: [bridge methods](bridge-methods.md).
- Channels, sequential inference and simulation: [research visualizations](research-visualizations.md).
- Citations, access limits and claim scope: [scholarship](scholarship.md).

These explanations introduce no new native campaign, theorem instance or
empirical result. Current release and artifact qualification remain separately
recorded in [current state](current-state.md).

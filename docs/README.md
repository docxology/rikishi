# Rikishi documentation

Rikishi is a workbench for the Suggested Upper Merged Ontology (SUMO). Begin
with the ontology's commitments and its Standard Upper Ontology Knowledge
Interchange Format (SUO-KIF) source language, then choose the system or workflow
that answers your question. The source theory, a graph projection, a translated
reasoning problem and a finite calculation each carry different information.

## Learn the ontology and its language

Read these three guides in order:

1. [Ontology commitments](sumo/ontology.md): entities, classes, membership,
   specialization, signatures, metamodeling and incomplete knowledge.
2. [Reading the source language](sumo/language.md): prefix notation, logical
   scope, ordinary and row variables, functions, relation arguments and contexts.
3. [Systems and translations](sumo/systems.md): Sigma Knowledge Engineering
   Environment (KEE), native provers, target logics, lexical mappings and related
   ontology representations.

Continue with the [pinned source demonstrations](sumo/sumo-demonstrations.md)
to connect those ideas to complete formulas and source locations. The
[ontology-analysis guide](sumo/ontology-analysis.md) explains formula search and
Rikishi's restricted asserted-edge projection. The [modeling guide](sumo/modeling.md)
helps turn a domain idea into explicit assumptions and competency questions.

## Choose a working path

| Your aim | Start here | Continue with |
| --- | --- | --- |
| Install and complete a first workflow | [Getting started](getting-started/README.md) | [Installation](getting-started/installation.md), [tutorial](getting-started/tutorial.md), [glossary](getting-started/glossary.md) |
| Understand and extend SUMO | [Ontology and source](sumo/README.md) | [Modeling](sumo/modeling.md), [metrics](sumo/metrics.md), [upstream contributions](sumo/contributing-upstream.md) |
| Run or diagnose native reasoning | [Runtime](runtime/README.md) | [Installed systems](runtime/runtime.md), [inference tutorial](runtime/inference-tutorial.md), [fresh cache controls](runtime/cache-inheritance.md) |
| Understand method contracts | [Methods](methods/README.md) | [Architecture](methods/architecture.md), [inference](methods/inference-methods.md), [bridge](methods/bridge-methods.md), [semantic transport](methods/semantic-transport.md) |
| Connect ontology modeling to finite probability and action | [Research](research/README.md) | [Worked conceptual connection](sumo/sumo-fep-simulations.md), [finite study](research/research.md), [Active Inference](research/active-inference.md) |
| Inspect results through software interfaces | [Interfaces](interfaces/README.md) | [Dashboard](interfaces/dashboard.md), [interface reference](interfaces/api.md) |
| Reproduce or review the manuscript and release | [Publication](publication/README.md) | [Manuscript recipe](publication/manuscript.md), [review guide](publication/review.md), [release methods](publication/release.md) |
| Contribute and run quality gates | [Development](development/README.md) | [Testing](development/testing.md), [current state](development/current-state.md), [roadmap](development/roadmap.md), [contributing](../CONTRIBUTING.md) |

## Follow a claim to its evidence

For a source assertion, inspect its complete formula and revision. For a logical
consequence, inspect the submitted premises, translation, conjecture and native
result. For a finite calculation, inspect its numerical inputs, independent
reference and support conditions. For a Lean theorem, inspect its hypotheses,
source, dependencies and elaboration. The [verification guide](methods/verification.md)
and [primary-source ledger](research/scholarship.md) explain the corresponding
authorities and limits.

The [manuscript source](../manuscript/rikishi.md) and
[rendering recipe](publication/manuscript.md) bind prose, figures and editions to
their actual inputs. The [reproducibility guide](methods/reproducibility.md)
explains retained reports and independent digests. The final release's
verification summary identifies the exact source, artifacts and completed gates.

Rikishi software uses the [MIT license](../LICENSE). Original manuscript text and
figures use [Creative Commons Attribution 4.0 International](../LICENSE-PAPER.md).
Third-party source excerpts, tools, styles and fonts retain the terms listed in
[the attribution inventory](../THIRD_PARTY_NOTICES.md).

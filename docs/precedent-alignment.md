# Active Inference precedent and a bounded Rikishi alignment

This guide concerns alignment with the Suggested Upper Merged Ontology (SUMO).

Douglass and colleagues' *Aligning Active Inference Ontology to SUMO* is direct
prior work for Rikishi's proposed vocabulary bridge. Cite the
[June 3, 2024 v2 preprint](https://doi.org/10.5281/zenodo.11463326) as
`[@douglass2024alignment]`. Its abstract presents a tentative scaffold toward
later rigorous mapping. The paper identifies candidate ontology files, broader
and narrower concepts, and possible relationships for selected topics (Portable Document Format (PDF) p. 1).
Rikishi therefore should not claim the first Active Inference--SUMO alignment.
Its operational work can help test a specified interpretation, but reproducible
indexing, numerical evaluation, and proof execution each have narrower meanings
than a validated semantic correspondence.

## Sources and citation decision

The version-specific record contains the
[PDF](https://zenodo.org/records/11463326/files/Aligning%20Active%20Inference%20Ontology%20to%20SUMO.pdf?download=1)
and
[workbook](https://zenodo.org/records/11463326/files/Active%20Inference%20Topics%20Aligned%20to%20SUMO.xlsx?download=1).
Physical PDF page numbers are used below. Workbook locators preserve the exact
sheet name, `'ActInfOntology_SUMO '`, including its trailing space, and Excel row
numbers; they are not a count of accepted mappings. Original bytes, Hypertext Transfer Protocol (HTTP) headers,
Secure Hash Algorithm 256-bit (SHA-256) hashes,
application programming interface (API) checksum comparisons,
and access date are retained in
`.omo/evidence/precedent-upgrade/sources/source-manifest.json`. The accompanying
`.omo/evidence/precedent-upgrade/research.md` identifies the machine-readable cell
extraction and metadata. These are checkout-only evidence paths, excluded from
source distributions; use the public source and export links in this guide when
reading a distributed copy. The files were accessed on 2026-10-20. Retaining them
fixes the inspected source, not its scientific validity.

The [JavaScript Object Notation (JSON) export](https://zenodo.org/records/11463326/export/json) labels the
resource a preprint, gives publication date `2024-06-03`, and exposes the following
ordered creators and roles. The separately retained API response omits that role
detail. Both the
[BibTeX export](https://zenodo.org/records/11463326/export/bibtex) and
[Citation Style Language (CSL) export](https://zenodo.org/records/11463326/export/csl) explicitly put all these
names in their author field, in this order.

| Exported name | Record role |
|---|---|
| David S. Douglass | Contact person |
| Adam Pease | Producer |
| Daniel Ari Friedman | Project member |
| Jessica Angeli Balbuena | Project member |
| Rhea Chokhalingam | Project member |
| Ana Magdalena Hurtado | Project member |
| Maria Luiza Iennaco | Project member |
| V. Bleu Knight | Project member |
| Scott Ryan Maybell | Project member |
| Ali Rahmjoo | Project member |
| Paulo Duare Andrade Sayeg | Project member |
| Jakub Smékal | Project member |
| Dean Tickles | Project member |
| Alex Vyatkin | Project member |

Rikishi's BibTeX follows that explicit record citation, without asserting equal
contributions or deriving authorship from role labels. The PDF's p. 1 byline lists
13 people, omitting Maybell; some given names/spellings also differ. Its pp. 1 and
16 print `10.5281/zenodo.11459323`, whereas this v2 record and its exported
citations identify `10.5281/zenodo.11463326`. The concept digital object identifier (DOI) is
`10.5281/zenodo.11459322`. Use the v2 record DOI for the inspected package, retain
the discrepancy, and do not silently repair the downloaded PDF. The record's
technical creation timestamp on June 4 is not the June 3 publication date.

## What the proposed alignment actually contains

The paper separates topics from linguistic terms, permits multiple proposed
senses, and treats modules and teaching lists as informal organizational aids
(PDF pp. 2-3). Its SUMO notes distinguish subclass, instance, subrelation, argument
domains, and other relationships (pp. 4-5). An asterisk often flags a term not yet
in SUMO (p. 4). Some other-relation entries motivate a proposal rather than assert
a formal equivalence (p. 5). These qualifications must travel with reused rows.

| Topic and source locator | Actual proposal or recorded gap | Consequence for a Rikishi study |
|---|---|---|
| `abstractCounterpart`, PDF p. 6; workbook row 13, D:E and I:K | An abstract model and a physical entity are related with typed arguments. | Consider separate model and execution objects; sharing an identifier is insufficient. |
| Active Inference, PDF p. 6; row 23, I and L | `Judging` is located under `Selecting`; proposed `*ActiveInference` is internally related to `Judging`. | Do not rewrite an informal internal relationship as identity or subclassing. |
| Agent, PDF p. 7; row 33, I:K | Lowercase `agent` is a relation with `Process` and `AutonomousAgent` arguments. | Distinguish a case-role relation from an agent entity or a finite state variable. |
| Bayesian Inference, PDF pp. 7-8; row 54, I | Proposed `*BayesianInference` is placed under `PhysiologicProcess`. | A posterior calculation alone does not establish a physiological realization. |
| Free Energy, PDF p. 10; row 176, D:E and H:L | Several senses, including variational, expected and Helmholtz free energy, are grouped with proposed physical-dimension and relational-attribute placements. | Specify the mathematical sense and units before evaluating a quantity; the finite objective does not implement every listed sense. |
| Expected Free Energy, PDF p. 10; row 155, H:L | A proposed new file and `RelationalAttribute` placement are suggested, with an information-measure relationship. | No claim that Rikishi's present variational calculation implements policy selection or expected free energy. |
| Free Energy Principle, PDF p. 10; row 177, I | Proposed `*FreeEnergyPrinciple` is an **instance** of `Proposition`. | Distinguish a proposition expressing a principle from a class of finite models and from evidence for its biological truth. |
| Generative Model, PDF p. 11; row 190, I | Proposed `*GenerativeModel` is a **subclass** of `Process`. | Reconcile with Rikishi's separate proposition-based model representation before claiming agreement. |
| Generative Process, PDF p. 11; row 192, I | Proposed subclasses of `ProbabilityRelation`, `Proposition`, and `Process` appear together. | Resolve senses and category commitments; do not mechanically import all placements as one populated class. |
| Inference, PDF p. 11; row 217, I | Proposed `*AbstractInference` under `Learning` includes the authors' own concern about non-temporal abstraction versus temporal change. | Preserve the open issue; distinguish a mathematical inference relation from an execution that learns or reasons. |
| Variational Free Energy, workbook row 431, D and H:L | A prose description is present; H:L contain no populated mapping cells in this row. | A finite VFE interpretation must supply its own axioms and obligations. A blank row segment proves no mapping coverage claim about the whole workbook. |

This is a focused reading of relevant rows, not a validation or coverage audit of
the whole alignment. The PDF's selected table and the workbook are not identical
presentations; for example, the workbook gives the focused VFE row above.

## Relationship to Rikishi

The local authorities are
[`config/fep_mappings.json`](../config/fep_mappings.json),
[`examples/fep-ontology.kif`](../examples/fep-ontology.kif), and the separate
[finite numerical and formal contracts](fep.md). They propose probability-law,
divergence, and inference vocabulary. The Knowledge Interchange Format (KIF) example classifies a
`RikishiFiniteGenerativeModel` beneath `Proposition` and an inference class beneath
`Process`, with separate content/execution instances linked by `abstractCounterpart`;
its comments and names impose no numerical axioms. Those are
Rikishi modeling choices, not an implementation of the preprint's rows.

The category difference is material. At the revision in Rikishi's source lock,
SUMO partitions `Entity` into `Physical` and `Abstract`
([`Merge.kif:911`](https://github.com/ontologyportal/sumo/blob/efcd059f8feebfe3488a09f575f88d4d009b1e5c/Merge.kif#L911)).
`Process` is physical
([2134-2147](https://github.com/ontologyportal/sumo/blob/efcd059f8feebfe3488a09f575f88d4d009b1e5c/Merge.kif#L2134));
`Proposition` is abstract, with documentation distinguishing information from its
physical representations
([4506-4524](https://github.com/ontologyportal/sumo/blob/efcd059f8feebfe3488a09f575f88d4d009b1e5c/Merge.kif#L4506)).
An interpretation should therefore distinguish the model's mathematical/content
object from a process that runs it, with an explicit representation relationship
where justified. `abstractCounterpart` provides a candidate relation with an
abstract first argument and a physical second argument
([7546-7559](https://github.com/ontologyportal/sumo/blob/efcd059f8feebfe3488a09f575f88d4d009b1e5c/Merge.kif#L7546)).
The [executed finite study](research.md) now tests a declared interpretation of
this model/execution distinction using selected source formulas and workbook
cells. It is not a checked equivalence, and the
preprint's multiple placements alone are not a reproduced inconsistency result:
class non-emptiness, sense distinctions, and the actual loaded axioms matter.

Two further SUMO constraints guide a useful small experiment. `ProbabilityFn` is
a unary function from a `Formula` to a `RealNumber`; its signature alone supplies
neither a finite carrier nor a normalized mass-vector encoding
([3334-3346](https://github.com/ontologyportal/sumo/blob/efcd059f8feebfe3488a09f575f88d4d009b1e5c/Merge.kif#L3334)).
`Reasoning` belongs to `IntentionalPsychologicalProcess`, with a documented
evidential-conclusion sense and an agent capability involving `CognitiveAgent`
([15351-15360](https://github.com/ontologyportal/sumo/blob/efcd059f8feebfe3488a09f575f88d4d009b1e5c/Merge.kif#L15351)).
Mapping a numerical function to these terms requires an account of what its
arguments denote and which process/agent assumptions are intended. Name matching,
taxonomy traversal, or successful arithmetic cannot supply that account.

## Executed finite study and further evidence

The versioned [study authority](../src/rikishi/data/alignment-study-v1.json)
fixes selected workbook senses, complete source formulas, a local model/execution
extension, explicit first-order logic (FOL) kernel and numerical design. Current reports under
`output/research/{e,v}/` each match 12 declared logical outcomes, pass 144 numerical
and four boundary cases, and reject eight invalid inputs. Corresponding problem
hashes and statuses agree across families. The baseline is satisfiable; aliasing,
empty-class and inhabited-class controls delimit the local interpretation.
Probability arithmetic, posterior updates and free energy are evaluated
separately against an independent Decimal reference, not proved in the FOL kernel.

This is completion of a selected experiment. It does not measure whole-workbook
coverage, validate the preprint's mappings or establish a SUMO-to-Lean bridge.
The [reproduction guide](research.md) includes the official workbook acquisition
recipe because original XLSX bytes are not bundled. The following obligations
remain applicable when extending the selected study.

| Evidence to retain | Acceptance boundary |
|---|---|
| Preprint DOI/version, PDF page or workbook cell, intended sense, source bytes/hash, candidate relation type | A traceable proposal; no inference of equivalence from a common label or blank field. |
| Pinned SUMO file/line, complete defining formulas, arity, domain/range, subclass/instance choice, and separate extension file | A type-aware encoding. Recheck disjointness and distinguish abstract content from a physical execution. Parse acceptance proves syntax only. |
| Finite state/observation carriers, normalized prior and candidate, likelihood interpretation, positive evidence, units and zero-support convention | A mathematical model whose terms and admissible inputs are specified. Keep the objective's posterior-relative Kullback-Leibler (KL) divergence distinct from the preprint's prior/posterior complexity wording (row 86, E). |
| Analytic positive examples plus invalid normalization, impossible evidence, and zero-reference-support cases | Numerical behavior on declared inputs. Agreement on supported inputs does not erase the difference between Rikishi's rejection policy and Lean's totalized arithmetic. |
| Explicit SUMO axioms and competency questions, expected answers, counterexamples or falsity-tests, prover input hashes, versions, resources and raw status | A conclusion about those axioms and queries. A timeout/unknown is not non-entailment; a theorem from contradictory assumptions is not semantic validation. See [runtime contracts](runtime.md) and the existing competency-testing sources in [scholarship](scholarship.md). |
| Interpretation of carriers, formulas, functions, arithmetic/logarithms and probability support; named Lean statements and a preservation argument | A bridge theorem only after the actual correspondence is proved. Isolated Lean compilation verifies the cited Lean fragment, not the SUMO encoding or the preprint's whole mapping. |
| Independent ontology and domain review, recorded revisions and rejected alternatives | A reviewed modeling proposal. Biological adequacy still needs an operational empirical hypothesis and relevant observations; no organism-level validation follows from these software artifacts. |

The useful contribution is thus source-bound operational support for examining a
small interpretation in an existing research direction. Claims of verified
cross-ontology equivalence, complete alignment coverage, or biological verification
require evidence beyond the present Rikishi methods and this source review.

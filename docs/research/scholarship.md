# Scholarship and claim-to-evidence ledger

[`manuscript/references.bib`](../../manuscript/references.bib) owns publication
metadata and Pandoc citation keys. Primary sources explain theories and
published methods. Pinned source files establish what Rikishi inspected.
Source-bound execution records establish what the implementation actually
ran. These authorities are complementary.

The Suggested Upper Merged Ontology (SUMO) uses Standard Upper Ontology
Knowledge Interchange Format (SUO-KIF). This ledger covers those sources and
their connection to the Free Energy Principle (FEP), numerical methods and
formal verification.

Start with [SUMO's modeling approach](../sumo/ontology.md),
[SUO-KIF](../sumo/language.md) and [related systems](../sumo/systems.md).
The [qualification guide](../development/current-state.md) describes the actual
release gates. This ledger supplies scholarly interpretation, not an assertion
of native success.

## Source identities

The [source lock](../../config/sumo.lock.json) records SUMO revision
`efcd059f8feebfe3488a09f575f88d4d009b1e5c` and Sigma revision
`d3cc7b43b38b0b45692291a1b33fe2b1a3de0095`, together with the declared local
preprocessing patch. The complete pinned
[`Merge.kif`](https://github.com/ontologyportal/sumo/blob/efcd059f8feebfe3488a09f575f88d4d009b1e5c/Merge.kif)
has Secure Hash Algorithm 256-bit (SHA-256) fingerprint
`2e4c3d6b8392a4cb6fbeccb6eb7441e11d6b45592082333285c951fd7c7d3e14`.
Historical ontology size estimates and system descriptions do not authenticate
this later source/runtime combination.

The formal source uses FEP_Formal revision
`9a0694f16b8e89b66b2f7f8cc7426c650dd2c4de`. The pinned
[`finite_probability.lean`](https://github.com/ActiveInferenceInstitute/fep_formal/blob/9a0694f16b8e89b66b2f7f8cc7426c650dd2c4de/lean/FepSketches/finite_probability.lean)
and
[`finite_information.lean`](https://github.com/ActiveInferenceInstitute/fep_formal/blob/9a0694f16b8e89b66b2f7f8cc7426c650dd2c4de/lean/FepSketches/finite_information.lean)
identify mathematical declarations. Their file/dependency/compiler identities
and actual elaboration belong to the separate
[isolated compilation receipt](fep.md#isolated-lean-compilation).

## SUMO, language and reasoning claims

| Claim supported | Primary source and locator | Interpretation boundary |
| --- | --- | --- |
| SUMO supplies general concepts and axioms through explicit merging and modeling. | Niles and Pease (2001), `niles2001sumo`, [author paper, §§2–3](https://adampease.com/FOIS.pdf). | Its design objectives do not prove consistency of the current revision. |
| Membership, specialization and signatures have different roles. | `sumoSource`: pinned [membership/subclass, 83–150](https://github.com/ontologyportal/sumo/blob/efcd059f8feebfe3488a09f575f88d4d009b1e5c/Merge.kif#L83-L150), [domain, 216–265](https://github.com/ontologyportal/sumo/blob/efcd059f8feebfe3488a09f575f88d4d009b1e5c/Merge.kif#L216-L265), [range, 320–383](https://github.com/ontologyportal/sumo/blob/efcd059f8feebfe3488a09f575f88d4d009b1e5c/Merge.kif#L320-L383). | Documentation, active axioms and generated type guards need separate identification. A graph does not execute the signature theory. |
| Functions can be discussed as entities and used to form terms. | Pinned [ProbabilityFn, 3334–3346](https://github.com/ontologyportal/sumo/blob/efcd059f8feebfe3488a09f575f88d4d009b1e5c/Merge.kif#L3334-L3346) and [function classes, 4230–4270](https://github.com/ontologyportal/sumo/blob/efcd059f8feebfe3488a09f575f88d4d009b1e5c/Merge.kif#L4230-L4270). | One function input and a binary relational graph are compatible. The signature does not encode a numerical probability array. |
| Free-variable closure depends on assertion/query use; richer constructs need declared semantics. | Pease (2009), `pease2009suokif`, [pinned manual](https://github.com/ontologyportal/sigmakee/blob/d3cc7b43b38b0b45692291a1b33fe2b1a3de0095/suo-kif.pdf); active [Sigma closure method](https://github.com/ontologyportal/sigmakee/blob/d3cc7b43b38b0b45692291a1b33fe2b1a3de0095/src/java/com/articulate/sigma/Formula.java#L2296-L2317). | Keep explicit quantifier scope. Predicate variables, row variables and formula arguments do not become unrestricted first-order constructs by renaming. |
| Sigma is an engineering environment and prover integration layer. | Pease and Schulz (2014), `pease2014sigma`, [system paper, §§2–4](https://adampease.com/pe_sch_sigma.pdf). | Historical integration does not verify current executable, cache or background bytes. |
| First-order preprocessing and typed arithmetic require interpretation choices. | Pease (2023), `pease2023translation`, [version 1, §§1–2](https://arxiv.org/html/2303.04148v1). | Predicate/row expansion, arity specialization and numerical sorts have specific limits; the paper identifies loss of strictly higher-order content in first-order translation. |
| Embedded formulas require a context interpretation. | Benzmüller and Pease (2012), `benzmueller2012higherorder`, [author paper, §§3–6](https://christoph-benzmueller.de/papers/J27.pdf). | Their multimodal treatment addresses specified contexts; Rikishi does not implement that embedding. |
| SUMO-K gives a higher-order set-theoretic interpretation of a defined fragment. | Brown, Pease and Urban (2023), `brown2023sumok`, [version 1, §§2–3](https://arxiv.org/html/2305.07903v1). | Temporal, modal and probabilistic operations are outside that reported fragment; its proofs are not a SUMO-to-Lean preservation theorem. |
| Adimen-SUMO is a distinct first-order reengineering. | Álvez, Lucio and Rigau (2012), `alvez2012adimen`, [author manuscript](https://adimen.ehu.eus/~rigau/publications/ijswis12-alr.pdf); [2015 competency paper, §2](https://adimen.ehu.eus/web/files/AdimenSUMO/k-cap2015.alrA.pdf). | Translation and repairs change the studied theory. Published percentages and performance apply to those versions, not the current SUMO pin. |
| Competency questions evaluate selected consequences and defects. | `alvez2015competency`, [method, §3](https://adimen.ehu.eus/web/files/AdimenSUMO/k-cap2015.alrA.pdf); bibliography entries `alvez2017atp`, `alvez2019whitebox`. | Inconclusive search is not non-entailment; no detected defect is not a consistency proof. |
| WordNet mappings distinguish lexical relationships. | Niles and Pease (2003), `niles2003wordnet`, [§3](https://adampease.com/Niles-IKE.pdf); `sumoWordnetMappings`, [pinned header](https://github.com/ontologyportal/sumo/blob/efcd059f8feebfe3488a09f575f88d4d009b1e5c/WordNetMappings/WordNetMappings30-noun.txt#L1-L29). | Preserve the synset/version and equivalence, subsumption, instantiation or complementary label; a word match gives neither global coverage nor logical identity. |
| Thousands of Problems for Theorem Provers (TPTP) roles and SZS outcomes describe particular target problems. | `tptpSZS`, [SZS specification](https://szs.tptp.org/); [official language reference](https://tptp.org/UserDocs/TPTPLanguage/TPTPLanguage.shtml). | Exact premises and target logic matter; axiom-like roles do not certify consistency. Capturing a status differs from independently checking each proof inference. |

The source-guide claims were checked against the named active formulas,
documentation and implementation passages. The manual link identifies the
locked reference; a fresh whole-manual reading is not claimed. The 2012
Adimen-SUMO full-text endpoint was unavailable during this revision, so the
updated comparison uses the accessible primary competency paper and retains
the original publication identity. The version-specific translation and
SUMO-K sections, author-hosted SUMO/Sigma/WordNet papers, official TPTP
documentation and pinned source passages support these bounded descriptions.
No paper is presented as an independently reproduced software experiment.

## Mathematical, numerical and scientific claims

| Claim supported | Primary source and locator | Rikishi boundary |
| --- | --- | --- |
| Variational free energy is the negative evidence lower bound (ELBO) and decomposes into posterior-relative Kullback-Leibler (KL) divergence plus surprise. | Blei, Kucukelbir and McAuliffe (2017), `blei2017variational`, [§2.2, equations 12–14](https://arxiv.org/html/1601.00670v9#S2.SS2). | Normalization, positive evidence and support are explicit. Prior-relative complexity uses a different KL second argument. |
| Related objectives motivate the FEP account of perception and action. | Friston, Kilner and Harrison (2006), `friston2006brain`, §5, equations 1–2; Friston (2010), `friston2010principle`, [Box 1](https://doi.org/10.1038/nrn2787). | A finite identity does not establish embodied dynamics, biological adequacy or empirical agency. |
| Discrete Active Inference distinguishes inference from prospective action/policy evaluation. | Da Costa and colleagues (2020), `dacosta2020discrete`, [version 2, §§4.1,6.5,7 and Appendix C](https://arxiv.org/html/2001.07203v2). | Rikishi's one-step outcome-risk-plus-ambiguity planner uses known finite channels and exact within-model hypothetical posteriors. Longer policies, learning and environment loops are separate work. |
| Stable log-sum-exp addresses exponential range problems without removing rounding error. | `blanchard2019logsumexp`, equations 1.3–1.5, Algorithm 4.1 and §6. | Null log inputs denote exact zero; null linear evidence can denote positive underflow. Independent Decimal controls concern declared inputs. |
| A formal prover's architecture differs from an actual theorem instantiation. | de Moura and Ullrich (2021), `demoura2021lean4`, [§§1–2,5](https://lean-lang.org/papers/lean4.pdf); pinned finite Lean modules above. | Actual source/dependencies/toolchain, hypotheses and axiom reports are required. Totalized finite KL differs from the numerical operator's rejection domain. |
| Semantic preservation needs a relation between source and target meanings. | Leroy (2009), `leroy2009verified`, §4.3; Harrison (2006), `harrison2006floating`, §4.2. | Methodological precedents do not prove Rikishi's translation or floating-point implementation. |
| Bayesian workflow separates model construction, simulation and predictive assessment. | Gelman and colleagues (2020), `gelman2020workflow`, [version 1, §§2.4–2.5,4.1–4.2,6.1](https://arxiv.org/html/2011.01808v1). | A fixed-seed synthetic experiment is not empirical validation or simulation-based calibration. |
| Scoring, calibration and application validation have different conditions. | `gneiting2007proper`, §4 and §7.1; `gneiting2007calibration`, [§§2.1,2.4,3.1](https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jrssb.pdf); `trucano2006calibration`, abstract/introduction. | Distributional assumptions are not silently transferred to Boolean examples. Trucano full-text access was unavailable; no detailed uninspected result is attributed. |

These locators identify selected material supporting the manuscript's argument;
they do not assert fresh whole-paper verification. Exact sequential rows,
finite references and simulation observations come from Rikishi's registered
witnesses, not results borrowed from these papers. See [finite methods](fep.md),
[Active Inference](active-inference.md) and the
[shared-witness bridge](../methods/bridge-methods.md).

## Direct alignment precedent

Douglass and colleagues' *Aligning Active Inference Ontology to SUMO* is a
direct prior proposal, identified by the
[version 2 Zenodo record](https://doi.org/10.5281/zenodo.11463326),
`douglass2024alignment`. The record's exported citation includes 14 ordered
creators; the Portable Document Format (PDF) byline and its printed digital
object identifier (DOI) differ. Preserve that distinction
and cite the inspected versioned package. The
[precedent guide](precedent-alignment.md) retains the exact source/workbook
locators for the focused comparison.

That work establishes precedent for the research direction. Its proposed
placements and Rikishi's content/execution separation require explicit
interpretation. Neither source supports a claim that Rikishi is the first
alignment or implements the entire earlier mapping. Local terms, accepted
syntax and a common English label do not prove scientific equivalence.

## Match the conclusion to its owning evidence

| Conclusion | Evidence needed | Scope |
| --- | --- | --- |
| Source content or asserted edge | Pinned complete formula, location/hash and extraction policy. | What the source asserts or the projection retains. |
| Selected logical consequence | Complete premises, translation/conjecture, actual native invocation, background and negative controls. | The submitted problem; unknown stays inconclusive. |
| Finite numerical result | Declared model/support, independent reference, tolerances/residuals and invalid-input controls. | Arithmetic on the stated inputs. |
| Exact Lean instantiation | Hashed theorem/dependency sources, hypotheses, elaboration and axiom report. | The formal statement and its trusted basis. |
| Common-witness connection | Same rational laws/carrier/order bound to source representation, numerical inputs and concrete Lean obligations, with report custody. | The chosen representations and witnesses. |
| General semantic preservation | An interpretation of objects, classes, relations, formulas, functions, partiality and arithmetic, plus a correspondence argument. | A proved source/target fragment; agreement on examples is insufficient. |
| Empirical adequacy | Operational hypotheses, observations and domain-appropriate validation. | The specified application or scientific system. |

Report hashes provide custody bindings; they do not alone authenticate a past
native process or validate every proof step. Actual observed counts and outcomes
belong to the bound records described in
[verification](../methods/verification.md), [inference](../methods/inference-methods.md)
and [reproducibility](../methods/reproducibility.md).

When a claim changes, update its owning source locator or operation. A changed
pin requires relevant measurement/proof validation; changed manuscript source
requires a fresh canonical rendering and artifact verification. Bibliographic
accuracy, provenance, execution acceptance and scientific interpretation each
retain their own obligations throughout the release.

# Scholarship and claim-to-evidence ledger

The manuscript uses author-date hyperlinks with an explicit reference list, so the
three native template adapters render the same citations without a hidden citeproc
configuration. `manuscript/references.bib` supplies reusable bibliographic metadata;
the renderer copies and hashes it. The references support the specific claims below.
They do not authenticate a local run or prove the proposed SUMO-to-Lean bridge.

## Primary-source reading record

Sources were checked on 2026-10-20. The Niles and Pease FOIS record identifies the
original SUMO proposal; the former author-hosted PDF host is no longer served and the
full-text fetch failed through the research browser, so no detailed argument from that
paper is attributed here. The current ontology's actual definitions are pinned Git source, not this
historical paper. Blei et al.'s author-hosted full text was inspected at Section 2.2,
equations 12-14. Friston's publisher metadata and university-hosted full paper were
checked, specifically Box 1 and the distinction between information-theoretic and
thermodynamic free energy. The TPTP project's SZS documentation and Pease's arXiv
abstract were inspected directly. The Lean declarations were read using `git show`
at the exact revision, without importing or modifying the active checkout.

| Claim | Primary source and locator | Local evidence and boundary |
|---|---|---|
| SUMO is an upper ontology expressed through formal categories and axioms | [Niles and Pease 2001](https://doi.org/10.1145/505168.505170); [upstream modeling guidance](https://github.com/ontologyportal/sumo/wiki/SUO%E2%80%90KIF-Formalizing-Terms) | Actual operator vocabulary comes from pinned `.rikishi/upstream/sumo`, not a historical vocabulary snapshot. |
| Translation must be tracked independently from source | [Pease 2023](https://arxiv.org/abs/2303.04148), abstract describing typed first-order translation | `config/sumo.lock.json`, native problem hashes, and the versioned type-guard patch; this paper does not validate Rikishi's patch. |
| F is negative ELBO and equals posterior KL plus surprise | [Blei et al. 2017](https://www.cs.columbia.edu/~blei/papers/BleiKucukelbirMcAuliffe2017.pdf), equations 12-14 | `src/rikishi/fep.py`, independent logarithmic test values, `output/manuscript/fep-example.json`; finite normalized supported inputs only. |
| A related variational objective appears in the FEP account of perception and action | [Friston 2010](https://doi.org/10.1038/nrn2787), Box 1; [accessible full text](https://www.uab.edu/medicine/cinl/images/KFriston_FreeEnergy_BrainTheory.pdf) | Motivates terminology. Rikishi does not simulate action, neurons, or biological dynamics. |
| Theorem, contradictory axioms, counter-satisfiability, and inconclusive search are different outcomes | [TPTP SZS documentation](https://szs.tptp.org/) | Actual native core negative control reported contradictory translated axioms. This does not locate the cause in source versus translation. |
| Lean uses a totalized finite KL convention | [pinned finite information source](https://github.com/ActiveInferenceInstitute/fep_formal/blob/9a0694f16b8e89b66b2f7f8cc7426c650dd2c4de/lean/FepSketches/finite_information.lean), `finiteKL`, disjoint point-mass witnesses, `finiteKL_eq_crossEntropy_sub_entropy` | Source inspection only. Positive-reference support is explicit in the logarithmic identity. No Lean kernel run occurs here. |
| Corpus counts and concentration describe a source selection policy | `output/data/corpus.json`, `output/analytics.json`, [metric definitions](metrics.md) | Measured locally; never inferred from literature or represented as independent facts or semantic completeness. |
| Proposed FEP terms can be investigated in SUMO | `config/fep_mappings.json`, `examples/fep-ontology.kif` | Author-created modeling proposal. No preservation theorem or equivalence has been proved. |

## Reproduction and revision policy

For an updated scientific statement, first identify whether it is literature,
source inspection, measured output, theorem-prover output, or an interpretation.
Retain the relevant source locator or executable receipt. Updating a Git pin requires
rerunning its measurement or proof operation. Updating prose requires rerendering
and verifying the source hash. A valid bibliography entry cannot substitute for
the missing proof obligation of a cross-language interpretation.

The finite bridge would require a carrier map, normalized probability laws,
support conditions, interpretation of arithmetic and logarithms, and a proof that
the selected SUMO fragment preserves the target Lean statements. The present
package records those obligations rather than claiming their completion.

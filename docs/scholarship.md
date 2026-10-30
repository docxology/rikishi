# Scholarship and claim-to-evidence ledger

`manuscript/references.bib` supplies the publication metadata for Pandoc `[@key]`
citations. Citation numbering belongs to the publication pipeline, not a manually
maintained reference list. The bibliography's `{{FORMAL_COMMIT}}` token is hydrated
from the checked publication context. A source citation identifies scholarship;
run receipts separately establish what Rikishi executed.

The source theory is the Suggested Upper Merged Ontology (SUMO), authored in
Standard Upper Ontology Knowledge Interchange Format (SUO-KIF). Automated theorem
proving (ATP), selected first-order logic (FOL) interpretations, and the separate
Free Energy Principle (FEP) illustration require different evidence.

## Scholarship and execution have separate authorities

This ledger supplies source identities, historical context and interpretation
obligations for the implemented scholarship bridge. The
[qualification guide](current-state.md) identifies the required bounded
execution, artifact and review evidence; the
[prioritized TODO](TODO.md) separates remaining research obligations and source
access gaps. Bibliographic readings do not establish native execution or
scientific acceptance. Finite-alignment campaigns, shared-witness obligations
and isolated Lean compilation remain separate evidence under the
[architecture](architecture.md), [bridge](bridge-methods.md) and
[finite-study](research.md) contracts.

A **common finite witness** makes a selected
representation and theorem instantiation inspectable. It can connect particular
inputs across methods without proving that arbitrary SUMO sentences preserve
their meaning in Lean. State each translation choice, numerical convention, and
theorem hypothesis before presenting a result. The translation literature below
owns claims about its specified encodings; source-bound run receipts own
claims about this implementation.

### Reader orientation and simulation scholarship, 2026-10-29

The [SUMO–FEP_Formal–simulation guide](sumo-fep-simulations.md) introduces the
components before the detailed source ledger. SUMO supplies axiomatized
categories and relations; SUO-KIF expresses its source; Sigma Knowledge Engineering Environment (KEE) operates and
translates a selected theory. FEP_Formal supplies pinned mathematical objects
and statements, and Rikishi binds those objects to selected numerical and
synthetic experiments. This is a claim/evidence connection for particular
models, not an equivalence of whole theories.

| Primary source | Specific contribution | Reading and claim boundary |
| --- | --- | --- |
| Niles and Pease (2001), `niles2001sumo`; Pease and Schulz (2014), `pease2014sigma` | Shared ontology commitments and the separate Sigma engineering environment. | Author-hosted selected §§1–3 and §2 respectively were checked; historical descriptions do not verify the installed runtime. |
| Pinned `finite_probability.lean` and `finite_information.lean`, `fepFormalProbabilityPinned`/`fepFormalPinned` | Normalized finite laws/kernels, conditioning and named information identities. | Existing byte-file hashes and actual-file locators were rechecked. Strict reference support remains required for the logarithmic identity; no whole-project formalization claim. |
| Gelman et al. (2020), `gelman2020workflow`, [Bayesian Workflow v1](https://arxiv.org/html/2011.01808v1) | Separates forward simulation, inference checks and posterior-predictive assessment. | Selected §§2.4–2.5, 4.1–4.2 and 6.1; this is not a whole-paper reading. Fixed-seed survivor counts are not the repeated posterior-fitting/rank procedure of simulation-based calibration. |
| Da Costa et al. (2020), `dacosta2020discrete`, [arXiv v2](https://arxiv.org/html/2001.07203v2), [journal metadata](https://discovery.ucl.ac.uk/id/eprint/10115398/) | Distinguishes variational state inference from prospective policy/action objectives in discrete active inference. | Root selected reading of v2 §§1, 3, 6–7, with journal metadata checked separately. The UCL published Portable Document Format (PDF) fetch timed out; no fresh reading of that complete PDF is claimed. The current fixed-state simulator has no action-selection loop. |

Gelman, Meng and Stern's [1996 primary paper, §2.1](https://sites.stat.columbia.edu/gelman/research/published/A6n41.pdf)
was also consulted for the posterior-replication/observed-data distinction;
this is corroborating selected-section reading, not a new mandatory citation
or a claim that Rikishi has performed empirical posterior-predictive checking.
Exact values in the reader's running example are derived from the existing
registered witness. No new experimental result, native campaign or Lean
declaration is added by this editorial clarification.

### Active Inference decision methods, 2026-10-30

The separate [Active Inference guide](active-inference.md) now distinguishes
fixed-observation variational inference from prospective action evaluation and
implements a bounded one-step outcome-preference planner. This is an addition
to the operator methods, not a revision of the manuscript's registered
shared-witness experiments or a claim of empirical agency.

The current selected reading is Da Costa et al. (2020), `dacosta2020discrete`,
[arXiv v2](https://arxiv.org/html/2001.07203v2), §4.1 equations (1)–(3), §6.5,
§7 equations (13)–(16), and Appendix C equations (42)–(50). The Hypertext Markup Language (HTML) was consulted
on 2026-10-30. No whole-paper reading, fresh published Portable Document Format (PDF) reading or independent
verification of that paper's software is claimed.

The source distinguishes state-risk and outcome-risk formulations and the
posterior-approximation terms that relate them. Rikishi directly adopts the
outcome-risk-plus-ambiguity functional, with known finite channels and exact
within-model hypothetical posteriors. It derives the identity between that
functional and expected preference surprisal minus state information gain
for its stated finite model. It does not erase the source's approximation terms
or claim that the identity covers every active-inference formulation.

The planner enumerates one-step actions and retains numerical minimizers.
It does not implement a posterior over longer policies, habitual priors,
precision learning, parameter information gain, steady-state dynamics or a
sampled environment loop. Its tests check the declared arithmetic and decision
behavior; ontology alignment, Lean guarantees and empirical adequacy retain
their separate obligations. The existing `dacosta2020discrete` bibliography
entry continues to identify the journal work; the version-specific link above
identifies the selected text actually read.

### Publication additions and reading limits

The manuscript's sequential experiment and connection atlas distinguish formal
transport, exact arithmetic, numerical evaluation, predictive scoring and
empirical adequacy. The following table records the selected sections inspected
and access gaps, alongside public primary-source locators. These reading
boundaries do not establish a new full-text reading or native execution.

| Primary work | Contribution to the manuscript's argument | Retained reading boundary |
| --- | --- | --- |
| Leroy (2009), `leroy2009verified`, [digital object identifier (DOI) 10.1145/1538788.1538814](https://doi.org/10.1145/1538788.1538814) | State relations, corresponding transitions and observable traces make semantic preservation a stated obligation, beyond matching examples. | Author Portable Document Format (PDF) §4.3, physical pp. 7–8; methodological comparison, not a Rikishi preservation result. |
| Harrison (2006), `harrison2006floating`, [DOI 10.1007/11757283_8](https://doi.org/10.1007/11757283_8) | Exact mathematical statements and finite numerical evaluation require separate approximation and rounding analysis. | Author PDF §4.2, physical pp. 18–21, and physical p. 30; no proof of Rikishi floating-point execution. |
| Gneiting and Raftery (2007), `gneiting2007proper`, [DOI 10.1198/016214506000001437](https://doi.org/10.1198/016214506000001437) | Proper logarithmic scoring motivates the declared model-evidence comparison; prior specification is distinct from fitting on scored outcomes. | Author PDF §4, printed pp. 365–366, and §7.1, p. 372; synthetic comparisons are not empirical model-selection success. |
| Gneiting, Balabdaoui and Raftery (2007), `gneiting2007calibration`, [DOI 10.1111/j.1467-9868.2007.00587.x](https://doi.org/10.1111/j.1467-9868.2007.00587.x), [author PDF](https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jrssb.pdf) | Distinguish predictive calibration, concentration and assumptions of a diagnostic. | The author-hosted file was retained and selected §2.1, §2.4 and §3.1 passages, pp. 246–253, were read. The continuous-CDF/mixing hypotheses are not silently transferred to the Boolean examples. This is a selected-section reading, not whole-paper verification. |
| Trucano et al. (2006), `trucano2006calibration`, [DOI 10.1016/j.ress.2005.11.031](https://doi.org/10.1016/j.ress.2005.11.031) | Parameter calibration and application-specific predictive validation are different obligations. | Abstract, introduction and exposed section snippets; full-paper access was unavailable and no full-paper result is attributed. |

The exact sequential rows and reproducible simulation are constructed from the
registered finite witnesses, not results borrowed from these publications.
Their assumptions and controls are specified in
[sequential dynamics](bridge-methods.md#sequential-dynamics-and-forward-simulation).
The calibration reading uses the [author-hosted paper](https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jrssb.pdf),
with the exact selected sections stated above. Trucano full-text access remains
unresolved. No empirical validation is inferred from either source.

### Retained reading dossier, 2026-10-23

The source acquisitions, export metadata, source checks and access limitations
from the `2026-10-23` reading pass are retained under
`.omo/evidence/scholarship-bridge-20261023/scholarship/dossier/` in this checkout.
These private evidence files are not publication links. The primary links below
remain usable independently of that directory. That reading pass supplied
scholarship rather than a native bridge execution or a manuscript acceptance.
The `primary-sumo-sigma-research-20261023.md` register there records the inspected
SUMO/Sigma metadata and access limits. In particular, the Adimen-SUMO 2012
full text was not refreshed; its earlier page-specific readings in the retained
ledger remain historical rather than newly verified.

### Exact source identity versus historical description

The [source lock](../config/sumo.lock.json) names SUMO revision
`efcd059f8feebfe3488a09f575f88d4d009b1e5c` [@sumoPinnedMerge]. The canonical local
`.rikishi/upstream/sumo/Merge.kif` and a fresh download from the
[revision-specific raw source](https://raw.githubusercontent.com/ontologyportal/sumo/efcd059f8feebfe3488a09f575f88d4d009b1e5c/Merge.kif)
were byte-identical, with Secure Hash Algorithm 256-bit (SHA-256) fingerprint
`2e4c3d6b8392a4cb6fbeccb6eb7441e11d6b45592082333285c951fd7c7d3e14`.
This verifies the inspected file against that public revision's Uniform Resource
Locator (URL); it does not
audit the entire checkout or Git history. The lock separately names Sigma revision
`d3cc7b43b38b0b45692291a1b33fe2b1a3de0095` and a local preprocessing patch.
A historical Sigma paper cannot authenticate that installed combination.

For the finite formal source, the corporate author is the Active Inference
Institute and the source artifact has no assigned publication year (`fepFormalPinned`).
The inspected committed-snapshot identity is FEP_Formal revision
`9a0694f16b8e89b66b2f7f8cc7426c650dd2c4de`,
[`lean/FepSketches/finite_information.lean`](https://github.com/ActiveInferenceInstitute/fep_formal/blob/9a0694f16b8e89b66b2f7f8cc7426c650dd2c4de/lean/FepSketches/finite_information.lean),
SHA-256 `6827f3ceeee21c9312c5166aefdd4a6cbc50579229813992c3e5a05cadb71d65`.
The root supplied the committed-object snapshot at
`.omo/evidence/scholarship-bridge-20261023/scholarship/pinned-finite_information.lean.txt`;
the reading pass independently checked its digest and matched both snapshots against
fresh downloads from their revision-specific public raw URLs. The companion finite-probability
snapshot has SHA-256
`d99ae05fec4d012ecbb83601d1e361b01b22458790a316bb2ba3e360dfa11380`
[@fepFormalProbabilityPinned].
The later live canonical file is not evidence for these pinned bytes. Neither
snapshot hashing nor the source link establishes successful native elaboration.

### Verified variational and formal-method sources

All entries in this table have accessdate `2026-10-23`. The digital object
identifier (DOI) identifies the cited publication. Publication year and
version date are kept separate. The manuscript owner integrated `friston2006brain`,
`demoura2021lean4`, `fepFormalProbabilityPinned`, and `sumoPinnedMerge` into the
bibliography separately from the reading dossier.

| Source identity and primary link | Owning content and use in this study |
| --- | --- |
| Karl Friston, James Kilner, Lee Harrison (2006), *A free energy principle for the brain*, Journal of Physiology–Paris 100(1–3), 70–87; [DOI 10.1016/j.jphysparis.2006.10.001](https://doi.org/10.1016/j.jphysparis.2006.10.001); [author-hosted paper](https://www.fil.ion.ucl.ac.uk/~karl/A%20free%20energy%20principle%20for%20the%20brain.pdf). Integrated citation: [@friston2006brain]. | Section 5, equations (1)–(2), printed p. 73: variational free energy and its posterior-divergence decomposition. The paper's account also assumes an embodied system and an environment; a finite arithmetic witness supplies neither. |
| Karl Friston (2010), *The free-energy principle: a unified brain theory?*, Nature Reviews Neuroscience 11, 127–138; [DOI 10.1038/nrn2787](https://doi.org/10.1038/nrn2787); [author-hosted paper](https://www.fil.ion.ucl.ac.uk/~karl/The%20free-energy%20principle%20A%20unified%20brain%20theory.pdf). Existing key: `friston2010principle`. | Box 1 and printed pp. 128–129 distinguish the recognition density, generative model, perception/action, posterior divergence, and complexity relative to a prior. This is the FEP-facing interpretation, not a study result or validation of SUMO vocabulary. |
| David M. Blei, Alp Kucukelbir, Jon D. McAuliffe (2017), *Variational Inference: A Review for Statisticians*, Journal of the American Statistical Association 112(518), 859–877; [DOI 10.1080/01621459.2017.1285773](https://doi.org/10.1080/01621459.2017.1285773); [author-deposited arXiv v9](https://arxiv.org/html/1601.00670v9#S2.SS2). Existing key: `blei2017variational`. | Section 2.2, equations (12)–(14), owns the evidence lower bound (ELBO) and posterior-relative Kullback-Leibler (KL) decomposition. The journal year is 2017; v9 was submitted in May 2018. The inspected v9 Portable Document Format (PDF) is not mislabeled as the publisher's 2017 PDF. |
| Leonardo de Moura, Sebastian Ullrich (2021), *The Lean 4 Theorem Prover and Programming Language*, Automated Deduction–CADE 28, Lecture Notes in Computer Science (LNCS) 12699, 625–635; [DOI 10.1007/978-3-030-79876-5_37](https://doi.org/10.1007/978-3-030-79876-5_37); [project-hosted paper](https://lean-lang.org/papers/lean4.pdf). Integrated citation: [@demoura2021lean4]. | Sections 1–2 and 5 explain the theorem prover, extensible elaboration, and trusted kernel. This system paper establishes no particular Rikishi theorem, source translation, compilation receipt, or scientific adequacy. |

The finite calculation must specify normalized prior and candidate laws, its
likelihood interpretation, positive observation evidence, and support conditions.
On that declared domain, the negative ELBO convention and the posterior-relative
KL decomposition follow the cited Blei section. A divergence from the candidate
to the **prior**, used in a complexity/accuracy decomposition, has a different
second argument from the divergence to the **posterior**; Friston's Box 1 supplies
the relevant distinction. The [numerical contract](fep.md) separately owns
Rikishi's use of natural logarithms and dimensionless nats. Expected free energy,
policy selection, and thermodynamic free energy require their own definitions and
evidence; the present finite calculation does not supply them.

### SUMO signatures and metamodeling obligations

The primary historical sources below have accessdate `2026-10-23`. Their
metadata and translation limits were refreshed through primary-source browsing.
They describe their studied versions, independently of the pinned file above.
Sigma's software environment is the Knowledge Engineering Environment (KEE)
[@pease2014sigma].

| Verified source identity | Owning scope and locator |
| --- | --- |
| Ian Niles and Adam Pease (2001), *Towards a Standard Upper Ontology*, Formal Ontology in Information Systems, 2–9; [DOI 10.1145/505168.505170](https://doi.org/10.1145/505168.505170); [author-hosted paper](https://adampease.com/FOIS.pdf). `niles2001sumo`. | Sections 2–3: ontology construction and merging. Engineering objectives do not establish consistency or semantic preservation for a later source pin. |
| Adam Pease and Stephan Schulz (2014), *Knowledge Engineering for Large Ontologies with Sigma KEE 3.0*, Automated Reasoning, LNCS 8562, 519–525; [DOI 10.1007/978-3-319-08587-6_40](https://doi.org/10.1007/978-3-319-08587-6_40); [author-hosted paper](https://adampease.com/pe_sch_sigma.pdf). `pease2014sigma`. | Sections 2–3 describe the Sigma Knowledge Engineering Environment (KEE), ontology management and reasoning integration. This is historical system scholarship, not evidence of the installed runtime's correctness. |
| Adam Pease (2023), *Converting the Suggested Upper Merged Ontology to Typed First-order Form*; [DOI 10.48550/arXiv.2303.04148](https://doi.org/10.48550/arXiv.2303.04148); [author-deposited preprint](https://arxiv.org/abs/2303.04148). `pease2023translation`. | Sections 1–5 describe first-order preprocessing and type/numeric translation. Strictly higher-order content is outside the first-order target's retained scope. |
| Chad E. Brown, Adam Pease, Josef Urban (2023), *Translating SUMO-K to Higher-Order Set Theory*, Frontiers of Combining Systems, LNCS 14279, 255–274; [DOI 10.1007/978-3-031-43369-6_14](https://doi.org/10.1007/978-3-031-43369-6_14). `brown2023sumok`. | Sections 2–5 specify a higher-order set-theoretic treatment of a selected SUMO language. Temporal, modal, and probabilistic operations are excluded. It supplies no general probability-vector or SUMO-to-Lean preservation result. |

Use the exact pinned [Merge source](https://github.com/ontologyportal/sumo/blob/efcd059f8feebfe3488a09f575f88d4d009b1e5c/Merge.kif)
for this table. These are source-inspection statements, not newly proved
consequences. A declaration and its accompanying documentation are identified
separately from whatever the selected theorem-proving translation implements.

| Pinned source locator | Interpretation obligation |
| --- | --- |
| `Merge.kif:83–95`, `135–150`; `216–265`, `316–369` | Keep instance membership, subclass inclusion, argument-instance restrictions, argument-subclass restrictions, and the corresponding range forms distinct. Class-valued arguments require an explicit representation policy; treating every class as a Lean type is an additional choice. |
| `Merge.kif:3334–3346` | `ProbabilityFn` has a formula argument and real result. Its signature does not select a finite event algebra or enforce a normalized vector representation. |
| `Merge.kif:3348–3362` | `conditionalProbability` places the conditioning formula first, conditioned formula second, numerical value third. A translation must preserve this order rather than infer it from mathematical notation alone. |
| `Merge.kif:5880–5894` | `DivisionFn` is marked `PartialValuedRelation`; its documentation leaves a zero divisor undefined. An encoding with totalized real division requires explicit nonzero-denominator hypotheses or an account of definedness. |
| `Merge.kif:6139–6148` | `LogFn` is binary: a real argument and a positive-integer base. Its signature does not directly identify it with unary natural `Real.log`. Any base conversion and admissibility conditions belong to the interpretation. |
| `Merge.kif:5572–5574`, `5589–5592` | An agent-relative representation entails `represents`. A language-relative representation entails existence of an agent-relative representation, with the antecedent at line 5590. The existential rule does not supply a chosen named agent. |
| `Merge.kif:15484` | `Calculating` is a subclass of `IntentionalPsychologicalProcess`. This classification supplies neither a particular calculation's correctness nor an identified numerical output. |
| `Merge.kif:16326–16331` | A `ContentDevelopment` instance entails existence of a `ContentBearingObject` in its `result` relation. Existence does not identify that object with the study's named numerical record. |
| `Merge.kif:911`, `2134–2147`, `4506–4524`, `7546–7559` | The physical/abstract distinction, process/proposition placements, and typed `abstractCounterpart` relation constrain content/execution modeling. They do not themselves identify a probability law with an embodied inference process. |

The [typed first-order translation](https://arxiv.org/abs/2303.04148) and
[SUMO-K higher-order set-theoretic translation](https://doi.org/10.1007/978-3-031-43369-6_14)
are relevant because they make translation decisions explicit. Their target
semantics and exclusions must accompany any borrowed construction. Historical
translation success does not imply that Rikishi translates arbitrary SUO-KIF,
that a selected first-order kernel implements every signature, or that a
SUMO-to-Lean interpretation preserves the source theory.

### Precedent citation authority and representational differences

The [Zenodo v2 record](https://zenodo.org/records/11463326) identifies *Aligning
Active Inference Ontology to SUMO* (2024-06-03), DOI
`10.5281/zenodo.11463326`, as a preprint. Its
[BibTeX](https://zenodo.org/records/11463326/export/bibtex) and
[Citation Style Language (CSL) export](https://zenodo.org/records/11463326/export/csl)
agree on all 14 ordered author names retained in `douglass2024alignment`;
the [JavaScript Object Notation (JSON) export](https://zenodo.org/records/11463326/export/json)
separately gives creator roles. This is citation-export authority, not a judgment
of equal contributions. Fresh downloads preserve those identities. The PDF
byline omits Scott Ryan Maybell and prints `10.5281/zenodo.11459323` on its first
page. Preserve that discrepancy; cite the inspected v2 package by its record DOI.

The precedent's proposed `GenerativeModel` process placement differs from
Rikishi's content/execution separation. The detailed page and workbook-cell
locators remain in [precedent alignment](precedent-alignment.md). Those focused
row readings are retained scholarship, not a new workbook-wide coverage audit.
Do not claim a first Active Inference–SUMO alignment, or treat a tentative
mapping as a theorem of semantic equivalence.

### Formalization maturity and the claim/evidence ladder

The `2026-10-23` reading dossier inspected FEP_Formal's canonical `AGENTS.md`,
`README.md` and maintained `config/theorem_maturity.yaml` read-only in
`Username/ActiveInferenceInstitute/Public/fep_formal` on GitVault. Those inspected
records distinguish
exact Lean statements from scientific concepts and maintain semantic dispositions
separately from compilation. The generated `docs/theorem-maturity-audit.md`
defines `formalized`, `proxy`, `conditional_proxy`, `structural_proxy`,
`scope_gap`, and `assumption_gap`. These are that project's reviewed scope labels,
not labels awarded by this dossier. Their inspected file hashes are retained in
the retained evidence manifest; no whole-project maturity count or native success is
inferred here.

For the committed finite-information snapshot, the root's declaration map is:
`entropy:25`, `crossEntropy:29`, `finiteKL:33`, `finiteKL_nonneg:43`,
`finiteKL_self:49`, totalized point-mass witnesses at lines 60 and 69,
the equality characterization `finiteKL_eq_zero_iff:78`, and
`finiteKL_eq_crossEntropy_sub_entropy:146–154`. The pinned link above owns these
locations; [formal-method documentation](fep.md) explains their limited scope.
The full-support identity must retain its hypotheses. Totalized finite KL and
Rikishi's rejection of unsupported positive mass must not be identified over
their entire domains. This pass does not certify the declaration proofs.

| Claim level | Necessary owning evidence | Conclusion boundary |
| --- | --- | --- |
| Historical proposal or published method | Primary publication, version, author/year, page or equation | Establishes precedent and the author's stated method, not present source bytes or an execution. |
| Exact ontology or formal-source inspection | Pinned revision URL, complete source bytes/hash, precise declaration or formula locators | Establishes what was inspected. Parsing, indexing, graph extraction, and hashing do not prove the represented mathematics. |
| Selected ontology inference | Explicit premises, translation policy, conjecture, native invocation and raw status; satisfiable-background and premise/countermodel controls | Supports only the submitted logical problem. Unknown is not non-entailment; contradictory premises cannot validate a mapping. See [inference methods](inference-methods.md). |
| Finite numerical calculation | Fixed model, admissible support, independent reference, error/residual bounds and invalid-input controls | Supports arithmetic on the declared inputs. It is not exact real equality or an ontology theorem. See [finite study](research.md). |
| Exact Lean theorem or instantiation | Hashed source/dependencies/toolchain, named theorem, hypotheses, actual elaboration and axiom report | Supports that formal statement under its trusted basis. A system paper or declaration name is insufficient. See [isolated verification](fep.md#isolated-lean-compilation). |
| Common-witness bridge | The same strictly positive Boolean-carrier rational laws bound to numerical inputs, an actual Lean instantiation, explicit SUMO representation, controls, and a trusted report digest | Connects the chosen witnesses and their separately checked representations in the retained run. It does not prove general translation preservation; completed outcomes require the source-bound report and review evidence. |
| Semantic preservation | Defined interpretation of carriers, membership, formulas, functions, probability, partiality and logarithms, with a soundness/preservation argument for the selected fragment | Requires an actual correspondence theorem beyond agreement on examples. No general preservation is claimed. |
| Biological adequacy | Operational empirical hypothesis, appropriate observations, and domain review | Neither ontology placement nor a proved finite identity establishes organism-level FEP behavior. |

The bridge contract keeps model, representation, calculation, and result roles
distinct. The source rules above motivate selected representation consequences;
they do not prove a mathematical identity from the fact that an event has some
result. Unsupported named-result and removed-premise controls are separate
scenarios, whose outcomes require their own retained native evidence.

The implemented method contract names `catalog`, `run_bridge`, and
`validate_bridge_report`; the validator requires an independently supplied
trusted report digest. The [bridge method contract](bridge-methods.md) describes
production and validation; the reading dossier does not replace their receipts.
A trusted digest supplies an external custody
binding; it does not itself authenticate a historical native process or check
every proof step. Each result must identify whether it is source inspection,
ontology representation, calculation, native theorem instantiation, or replay.
Alignment and isolated Lean receipts cannot substitute for the common-witness
report. Observed counts and outcomes belong to their bound execution records,
not to the bibliographic dossier.

## Primary-source reading record

The SUMO reading and bibliographic checks are recorded in the checkout-only file
`.omo/evidence/manuscript-upgrade/sumo-scholarship.md`.
That file contains the Uniform Resource Locators (URLs), publication metadata checks, access failures,
source locators, and ready-to-integrate prose using Pandoc citations. The original
Formal Ontology in Information Systems (FOIS) paper and WordNet paper were read in accessible author-hosted full text;
the older `nlp.ontologyportal.org` Portable Document Format (PDF) URLs failed in the recorded reading pass. Historical
papers describe their studied ontology and software versions. Current definitions
come from the locally pinned source, not historical size or coverage estimates.

The locked SUMO revision and the fresh file-byte comparison are recorded above. Earlier inspection
covered `Merge.kif`, the Mid-Level Ontology (MILO) header in `Mid-level-ontology.kif`, the WordNet mapping
README and noun-file header, and Sigma's SUO-KIF manual. The manual is explicitly
dated June 18, 2009; undated evolving documentation has no invented publication
year or bibliography retrieval date. Metadata dates in the bibliography are
publication facts, independent of runtime/version tokens in manuscript prose.

A deeper source reading is frozen in the checkout-only
`.omo/evidence/visual-sumo-upgrade/sumo-research.md`. It supplies a substantive
manuscript insertion, complete selected Knowledge Interchange Format (KIF) formulas, four short quotations with
per-source word budgets, labeled mathematical interpretations, and proposed
thin demonstrations. Raw official `Merge.kif` and SUO-KIF-manual downloads matched
the pinned local Secure Hash Algorithm 256-bit (SHA-256) hashes. Other Hypertext Transfer Protocol (HTTP) byte identities and access limits are
recorded separately; a browser-readable paper is not represented as a retained
local PDF. This research pass ran source/document checks only, without rerunning
native inference, the canonical renderer, or the full test suite.

The direct Active Inference--SUMO precedent is Douglass and colleagues'
[2024 v2 preprint](https://doi.org/10.5281/zenodo.11463326)
(`douglass2024alignment`). The complete PDF and relevant companion-workbook rows
were read for the focused comparisons in [precedent alignment](precedent-alignment.md).
Exact downloaded bytes, metadata from the record, application programming interface
(API) and exports, checksums, access dates, and
the citation decision are retained in the checkout-only
`.omo/evidence/precedent-upgrade/research.md` and its source manifest. These local
evidence files are excluded from source distributions; the alignment guide links
the public primary files and citation exports. The record's exported citation includes 14 creators with differing
roles; the PDF byline and printed digital object identifier (DOI) differ from that record. These differences
are documented rather than silently resolved by guessing authorship.

The ledger distinguishes knowledge base (KB) inputs from submitted Thousands of
Problems for Theorem Provers (TPTP) problems. Its numerical discussion uses
Kullback-Leibler (KL) divergence and the evidence lower bound (ELBO).

| Claim | Primary source and locator | Local evidence and boundary |
|---|---|---|
| Original design and merge strategy | `niles2001sumo`, sections 2-3; `sumoFormalizingTerms` | Syntactic conversion and semantic reconciliation are different operations. The original standards proposal and engineering aim are not a present consistency or interoperability proof. |
| Upper, middle and domain layers | `sumoSource`; pinned `Merge.kif` and `Mid-level-ontology.kif` header | MILO bridges upper concepts to domain detail. Structural indexing, the configured core and all-domain loading select different populations. |
| Membership, subclassing, relation/function signatures and disjointness | `sumoSource`, pinned `Merge.kif:83-151`, `216-254`, `321-369`, `430-446`, `4242-4257` | `instance` and `subclass` differ; class-valued arguments/results differ from instance-valued ones. Graph edges retain narrower extraction semantics. |
| Class names and relation names can occur as object-level arguments | `sumoSource`, pinned `Merge.kif:135-150`, `3334-3338`, `4253-4265` | `ProbabilityFn` is an instance of `UnaryFunction`; `UnaryFunction` is a subclass of `Function`. Neither statement licenses replacing membership by subclassing. The older `Class` discussion at `2827-2841` is commented out and is not an active source axiom. |
| Quantifier scope depends on assertion/query context | `pease2009suokif`, physical PDF pp. 6, 11 | Free assertion variables default to outermost universal quantification; free query variables default to existential quantification. The manual recommends explicit quantifiers. An existential witness is not a named source assertion. |
| Row variables and variable arity have concrete source examples | `sumoSource`, pinned `Merge.kif:201-207`, `647-670`; `pease2009suokif`, physical PDF pp. 13-14; `brown2023sumok`, sections 2.1-2.2 | `@ROW` denotes an argument sequence; predicate-variable expansion and fixed-arity specialization require a declared translation policy. Finite expansion does not prove unrestricted higher-order equivalence. |
| Domains and ranges constrain interpretations and preprocessing | `sumoSource`, pinned `Merge.kif:195-199`, `216-265`, `331-368`, `3162-3166`; `pease2023translation`, sections 1-2; `brown2023sumok`, section 2.1 | `domain` differs from `domainSubclass`, and `range` from `rangeSubclass`. Complete range/comparability axioms are retained. Intended signature conditions, generated type guards and observed ATP entailments must be identified separately; a graph does not execute those constraints. |
| SUO-KIF expressiveness and first-order preprocessing | `pease2009suokif`, expressiveness section; `pease2023translation`, sections 1-5 | Predicate/row variables, variable arity, quotation and implicit guards require explicit treatment. Typed numeric sorts do not simply reproduce SUMO multiple inheritance. |
| Higher-order contexts and bounded semantic interpretations | `benzmueller2012higherorder`, sections 3-6; `brown2023sumok`, sections 2-5 | The modal embedding and SUMO-K set-theoretic translation address specified interpretations/fragments; neither is implemented or validated by Rikishi. SUMO-K excludes temporal, modal and probabilistic operations. |
| Sigma engineering and query provenance | `pease2014sigma`, sections 2-4 | Browsing, lexical resources, translation, static analysis and ATP integration explain operator dependencies; historical integration does not certify the installed runtime. |
| WordNet mappings distinguish equivalence, subsumption and instantiation | `niles2003wordnet`, section 3; `sumoWordnetMappings`, pinned headers | `=`, `+`, `@` are mapping relations, not permission to identify every lexical item with an ontology entity. Headers also define complement markers. No contemporary global coverage estimate is asserted. |
| Adimen-SUMO is a separate reengineering | `alvez2012adimen`, translation/reengineering sections, especially author-manuscript pp. 7, 9-10 | Repairs and added axiomatization distinguish this derived first-order ontology from the pinned original SUMO. Its finite reflection treatment does not establish unrestricted second-order equivalence. |
| Competency questions, white-box tests and ATP benchmarks have bounded conclusions | `alvez2015competency`, section 3; `alvez2017atp`, sections 3-6; `alvez2019whitebox`, sections 6, 8-9 | Unknown is not non-entailment; solved falsity-tests can reveal defects; no detected redundancy is not consistency. Published performance is not a Rikishi measurement. |
| Direct prior work proposes a tentative Active Inference--SUMO alignment | `douglass2024alignment`, PDF pp. 1-5, 10-11; workbook `'ActInfOntology_SUMO '!I177`, `I190`, `I192`, `I217` | The authors propose candidate locations and relations, including proposed new terms marked with an asterisk. This establishes precedent, not executable alignment coverage, biological verification, or a preservation theorem. |
| A mathematical model, a process, and a probability-bearing formula need distinct interpretations | `sumoSource`, pinned `Merge.kif:911`, `2134-2147`, `2216-2234`, `3334-3346`, `4506-4524`, `7546-7559`; `douglass2024alignment`, PDF p. 11 | SUMO partitions physical and abstract entities; a process is physical and a proposition abstract. `ProbabilityFn` takes a formula, not an unspecified array of probabilities. The preprint's model/process proposals and Rikishi's proposition-based example require an explicit reconciliation. |
| Lowercase `agent` is a typed case-role relation | `sumoSource`, pinned `Merge.kif:3158-3174` | The relation has first domain `Process`, second domain `AutonomousAgent`, and is a subrelation of `involvedInEvent`. It is neither a class of agents nor evidence that a numerical array implements an autonomous agent. |
| `ProbabilityFn` signatures do not specify a finite probability-vector encoding | `sumoSource`, pinned `Merge.kif:3334-3346`, `2000`; `brown2023sumok`, section 2 | Its unary argument is `Formula`, its range `RealNumber`; `Formula` is a subclass of `Sentence`. A finite event map, normalization and support conditions remain explicit interpretation obligations. SUMO-K's reported translation excludes probabilistic operations. |
| F is negative ELBO and equals posterior KL plus surprise | [Blei et al. 2017](https://www.cs.columbia.edu/~blei/papers/BleiKucukelbirMcAuliffe2017.pdf), equations 12-14 | `src/rikishi/fep.py`, independent logarithmic test values, `output/manuscript/fep-example.json`; finite normalized supported inputs only. |
| Shifted normalization reduces harmful exponential range failures without eliminating rounding error | Blanchard, Higham and Higham, `blanchard2019logsumexp`, equations 1.3-1.5, Algorithm 4.1 and section 6 | The log-input method uses shifted weights and explicit support, with independent Decimal controls. Null log inputs mean exact zero; null linear evidence means positive underflow with finite log evidence. The paper's error analysis is not a certification of Rikishi's whole numerical implementation. |
| A related variational objective appears in the FEP account of perception and action | [Friston 2010](https://doi.org/10.1038/nrn2787), Box 1; [accessible full text](https://www.uab.edu/medicine/cinl/images/KFriston_FreeEnergy_BrainTheory.pdf) | Motivates terminology. Rikishi does not simulate action, neurons, or biological dynamics. |
| Theorem, contradictory axioms, counter-satisfiability, and inconclusive search are different outcomes | `tptpSZS`, [official status documentation](https://szs.tptp.org/) | The retained negative control localizes an inclusion-minimal contradictory translated subset. Current E and Vampire (E/V) campaign statuses concern the declared finite kernel. Neither result establishes original-SUMO inconsistency. |
| Proof presentation and independent proof checking have different obligations | `reger2017proof`, [publisher record and original paper](https://easychair.org/publications/paper/1DlL), pp. 46–60 | Reger discusses informative proof output and decomposition into separately checkable TPTP problems. Rikishi's complete premise extraction and native subset replay do not independently validate every inference in a proof calculus. Installed executable options are established by pinned native controls, rather than inferred from this historical paper. |
| Cache-generated classifications can be localized by source-input controls | Pinned Sigma `KBcache.java:1212-1269`, `2108-2148`; `Merge.kif:209-214`, `2866`, `5096`, `14141-14144`; [fresh cache methods](cache-inheritance.md); [historical runtime report](runtime-upstream-report.md) | The earlier seeded diagnostic and four deletion controls remain historical. Five current fresh controls use KB construction, source ingestion and full cache building without seeded maps. Parent/edge removal eliminates generated partial classification; a synthetic inheritable-class link leaves it present. Fragment and complete Merge observations are not full-core consistency, intended-semantics or repair evidence. |
| A selected interpretation and finite arithmetic can be executed reproducibly | [Versioned finite study](research.md), retained `output/research/{e,v}/alignment-report.json` | Campaign observations and denominators must be derived from their bound reports. Bibliographic readings do not rerun or independently revalidate those reports. The campaigns are separate from the shared-witness bridge and concern selected rows, with arithmetic separate from FOL. |
| Lean uses a totalized finite KL convention | `fepFormalPinned`; `finiteKL`, disjoint point-mass witnesses, `finiteKL_eq_crossEntropy_sub_entropy` | `output/formalization/verification.json` records isolated elaboration of finite probability/information modules and declaration-axiom inspection. This source reference is distinct from that execution receipt. Positive-reference support is explicit in the logarithmic identity; neither all of `fep_formal` nor a SUMO preservation theorem is certified. |
| Corpus counts and concentration describe a source selection policy | `output/data/corpus.json`, `output/analytics.json`, [metric definitions](metrics.md) | Measured locally; never inferred from literature or represented as independent facts or semantic completeness. |
| Proposed FEP terms can be investigated in SUMO | `config/fep_mappings.json`, `examples/fep-ontology.kif`; compare `douglass2024alignment`, PDF pp. 10-11 and workbook rows 177, 190, 192, 217, 431 | Rikishi's local proposal follows an established alignment research direction. It does not implement or validate the full earlier mapping, and no preservation theorem or equivalence has been proved. |

## Reproduction and revision policy

For an updated scientific statement, first identify whether it is literature,
source inspection, measured output, theorem-prover output, or an interpretation.
Retain the relevant source locator or executable receipt. Updating a Git pin requires
rerunning its measurement or proof operation. Updating prose requires rerendering
and verifying the source hash. A valid bibliography entry cannot substitute for
the missing proof obligation of a cross-language interpretation.

A common-witness bridge binds normalized finite laws, source representations,
numerical calculations and exact Lean instantiations for selected inputs.
Identify its actual bounded evidence in the release verification summary;
the reading dossier supplies no substitute execution claim. General semantic
preservation additionally requires a carrier and formula interpretation,
support/definedness conditions, arithmetic and logarithm semantics, and a proof
that the chosen source fragment preserves the target statements. Completion of
the bounded witness study does not discharge that separate obligation.

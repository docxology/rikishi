# Source-backed publication figures

The publication combines three frontmatter abstracts, a connection atlas and
source-backed body figures. This guide describes their rendering methods; the
[current qualification guide](current-state.md) defines the evidence required for
each changed artifact. The [prioritized backlog](TODO.md) tracks remaining layout
and platform work without asserting a completed review.

## Dense frontmatter and shared-witness experiments

`witness_abstracts` derives `abstract-source`, `abstract-witness` and
`abstract-evidence` Portable Network Graphics (PNG)/Scalable Vector Graphics (SVG) assets from the verified bridge export. Their
retained `witness-abstracts.json` binds literal Suggested Upper Merged Ontology (SUMO) source rules, local premises,
queries and controls to the rational witnesses, named Lean obligations and
model/representation/calculation/result roles. `publication_abstracts` projects
the configured order into the editions; `manuscript_verification` checks actual
Portable Document Format (PDF) images on physical pages 2–4. Word receives matching page breaks and Hypertext Markup Language (HTML)
receives the same ordered figures.
Source font bounds do not replace inspection of the actual embedded images.

The manuscript connection atlas joins selected source expressions, authored
interpretations, Lean objects and evaluated arithmetic. The joins identify
shared inputs and separate obligations; they are not a semantic-preservation
theorem. The [bridge methods](bridge-methods.md) retain the complete source and
control boundaries.

`witness_research_figures` renders two 191.9 × 185 mm PNG/SVG pairs from
`witness-research.json`: exact state-channel information changes and observation,
evidence and predictive/model-comparison experiments. Those calculations use
the same replay-verified bridge witnesses, with exact rational inputs and
independent Decimal quantities. A state channel, changed observation law and
changed evidence normalization are different operations.

`witness_dynamics_figures` renders the 191.9 × 205 mm four-panel
`witness-sequential` PNG/SVG pair from `witness-dynamics.json`. The panels show
state posteriors, next-observation predictions, exact versus simulated all-true
prefix probabilities, and equal-prior uniform/biased model weights. The hidden
state persists for each trajectory; observations are independent only
conditional on that state and model. The export retains exact n=0..12 answers,
65,536 seeded trajectories per witness, integer counts and generator metadata.
Line styles and marker shapes distinguish models without color alone. Synthetic
simulation is neither an additional Lean/SUMO result nor empirical validation.

`witness_sequence_atlas` adds a 191.9 × 205 mm mixed-history figure. Its 24
model/history rows enumerate all eight three-observation Boolean paths for the
three registered witnesses. Four panels show exact history evidence, false-state
posterior, next-true probability, and the separate equal-prior uniform/biased
model weights. The third model is not silently included in that comparison.
Persistent-state and independently redrawn-state probabilities remain distinct
in the retained data. The exporter binds every numerical SVG cell to its exact
model/history/role and rejects altered or ambiguous labels. Actual raster and
embedded-placement inspection remain required; source verification alone does
not establish readability. See the [mixed-history interface](API.md#mixed-observations-and-model-uncertainty)
and [finite-event contract](semantic-transport.md) for the mathematical and
formal scopes.

## Source overview and finite free-energy figure

`rikishi.manuscript_figures.render_manuscript_figures` writes, in order,
`fep-free-energy.png`, `graphical-abstract.png`, `graphical-abstract.svg`, and
`graphical-abstract.json`. Its arguments and return type are unchanged. The JavaScript Object Notation (JSON)
retains the exact supplied model, corpus measurement, taxonomy, and rendering
settings; displayed rounding never changes the calculations.

The body overview `graphical-abstract.png` is distinct from the three frontmatter
abstracts. It is 7.2 × 6.4 inches and shows the supplied complete direct
`subclass` neighborhood of `Entity`, with arrows from child to parent. No classes
are inferred or added for visual symmetry. The hierarchy, measured corpus,
Rikishi operator boundary, and finite example have separate visual regions.
The operator workflow is schematic; drawing an automated theorem proving (ATP) stage does not certify a
prover execution. Its source revision is printed beside the exact-input receipt.
The caller must bind the neighborhood and corpus counts to the same index.

The 7.2 × 5.8 inch Free Energy Principle (FEP) figure contains three panels:

- The actual prior, observation likelihood, exact posterior, and supplied
  candidate, with a shared [0, 1] scale. The likelihood is conditional on the
  state; its two entries need not sum to one. Paired position and hatching
  distinguish the states without relying on color.
- The supplied uniform scan of `F(q)`, the analytical posterior optimum, the
  supplied candidate, and the surprise bound. The optimum comes from the
  validated analytical posterior, rather than the smallest sampled value.
- The exact decomposition of candidate and posterior free energy into surprise
  and posterior Kullback-Leibler (KL) divergence, in nats. This is a finite numerical example,
  without an asserted equivalence between the Suggested Upper Merged Ontology (SUMO) and Lean or transported proofs.

The renderer recomputes and checks results and scan energies before creating any
output. It rejects incomplete or reversed taxonomy edges, inconsistent inventory
counts, dirty or rejected source files, invalid probabilities, and altered
numerical results. Layout capacity remains explicit: at most seven children,
with printable labels of at most 28 characters. Unsupported inputs fail instead
of being silently omitted.

`rikishi.reports.build_report` retains its eight artifact keys: `html`, `data`,
`svg`, `png`, `analytics`, `summary`, `composition_svg`, `composition_png`.
The Hypertext Markup Language (HTML), numerical payloads, and measurement definitions retain their existing
meaning. The static plotting layouts are:

- `corpus-files.svg/png` is 7.2 × 5.7 inches. The twelve largest indexed files
  have direct count and percentage labels. Every percentage, including the
  displayed total, divides by all indexed formulas.
- `corpus-composition.svg/png` is 7.2 × 6.7 inches. The ten largest formula heads
  and exact remainder reconcile to the full formula denominator. The remainder
  remains visible when its count is zero. The second panel plots every exact
  degree-frequency row from `measure_corpus`, retaining degree zero on explicit
  symmetric-log axes. It identifies the full symbol denominator, distinct-triple
  count, zero-degree count and share, and a most frequent nonzero degree (the
  smallest degree in a tie). These are descriptive counts, without a fitted
  distribution. Empty denominators are labeled `share undefined`.

The navy, teal, and copper palette, white backgrounds, direct labels, and numeric
ticks are shared across these static figures. Source revision, source cleanliness,
rejected-file count, and the analytical data filename appear on report figures.
No plot treats syntactic formula counts as independent facts, restricted graph
degree as semantic importance, or an index as a consistency proof. See
[measurement definitions](metrics.md) and [method boundaries](architecture.md).

`rikishi.sumo_figures.render_sumo_system` adds a separate body figure from a
validated portable SUMO report. It derives the selected category arrows,
`instance` classifications, `domain`/`range` constraints and complete modal
source example from actual citations, with file/line locations and derived
file-level counts. It writes `sumo-system.png`, vector `sumo-system.svg` and an
exact-input JSON receipt. Layout bounds are explicit; a report that cannot fit
without truncating its modal formula rejects before output creation. This is
source analysis, with no full-SUMO proof or consistency claim.

For integration, render these assets at their intended full text width. Reducing
the two-panel composition figure to a narrow column also reduces its 9 point
labels. Portable Document Format (PDF) margins, title-page composition, and canonical manuscript rendering
belong to the manuscript configuration and renderer, outside these plotting
methods. Every changed figure requires actual embedded-image and two-axis
placement checks, followed by independent inspection of the changed editions.
Earlier isolated previews cannot substitute for that evidence.

`rikishi.ontology_figures.render_ontology_structure` adds the complete retained
`Merge.kif` subclass/subrelation comparison. `measure_source_structure` rebuilds
an isolated index from the checked frozen source bytes and invokes the same
taxonomy methods as the dashboard. Assertion multiplicity, distinct edges,
endpoint nodes, roots, multiple parents, components, cycle nodes and self-loops
remain separate values. The figure uses direct labels and hatching, an explicit
zero baseline and a diagnostic table. Its Portable Network Graphics (PNG), vector
Scalable Vector Graphics (SVG) and exact-input JSON
are copied into each native edition's figure tree. The verifier rederives its
counts and checks all copies and actual image use. Graph cycles and graph absence
carry no logical consistency conclusion.

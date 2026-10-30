# Free energy: computation, vocabulary, and proof boundaries

The Suggested Upper Merged Ontology (SUMO) supplies categories, relations and
axioms; the Free Energy Principle (FEP) motivates a family of mathematical and
scientific models. [`FEP_Formal`](https://github.com/ActiveInferenceInstitute/fep_formal)
is a formalization project, from which Rikishi selects pinned finite Lean
definitions and statements. Its numerical evaluator and forward simulator are
separate implementations with separate evidence.

Start with [how SUMO, FEP_Formal and simulations connect](sumo-fep-simulations.md)
for one exact model carried through each role. A numerical identity requires
arithmetic checks; an ontology correspondence needs an interpretation; a theorem
claim needs a checked statement and hypotheses; a simulation additionally needs
a generative process and declared temporal assumptions. A supplied finite model
does not by itself implement an action-selection agent or an empirical study.

The separate [Active Inference guide](active-inference.md) develops the
prospective action question. `active-demo` evaluates a declared one-step
outcome-preference objective using exact transition/observation laws and numerical
information quantities. It does not change this fixed-observation evaluator,
the registered bridge studies or their formal evidence.

## Run the example

From the project environment, run `uv run python examples/fep_demo.py`. The public
Python entrypoints include `rikishi.fep.demo`, `free_energy`, `free_energy_log`,
`evaluate_model`, and `inspect_formalization`. Calculations use natural-log units
(nats); unavailable linear projections are explicit JavaScript Object Notation
(JSON) nulls in log-mode output.

The packaged [model authority](../src/rikishi/data/fep-example.json) owns the prior,
selected observation likelihood, candidate law, state labels, and scan resolution.
The command calculates joint mass, evidence, exact posterior, free energy, and
posterior Kullback-Leibler (KL) divergence from that input. The likelihood vector is conditional on state and
need not sum to one. To inspect the current parameters without transcribing them:

```python
from rikishi.fep import demo, load_demo_parameters

parameters = load_demo_parameters()
print(parameters)
print(demo(parameters))
```

For state `s`, observation `o`, and candidate law `q`:

$$F(q)=\sum_s q(s)\log\frac{q(s)}{p(s,o)}
      =D_{KL}(q\Vert p(\cdot\mid o))-\log p(o).$$

The code separately calculates both sides and reports their residual. A grid with
the configured resolution visualizes the objective; the exact posterior is an
analytically computed marker rather than a grid-search estimate.
This is variational inference in a supplied finite model. It supplies no empirical
evidence that an organism minimizes this objective and does not establish the
Free Energy Principle as a universal statement.

## Input and numerical contract

Prior and candidate must be normalized nonnegative finite vectors; likelihood
entries must lie in `[0,1]`. Equal dimensions and positive observation evidence are
required. Zero candidate mass contributes zero. Positive candidate mass on a zero
joint atom is rejected because its objective is infinite; this avoids invalid JSON
or a misleading finite sentinel. Objectives, support checks and posterior KL share
one logarithmic kernel. Positive prior/likelihood factors retain their support even
when their product rounds to zero. The linear facade retains direct arithmetic
evidence and posterior projections; those projections can round tiny atoms to zero.
If all linear joint mass underflows, it refuses the linear result and directs the
caller to the log interface.

## Logarithmic inputs and retained support

```bash
uv run rikishi fep-evaluate examples/fep-log-model.json --logarithmic
```

`evaluate_model(path, logarithmic=False)` reads a strict JSON object with `prior`,
`likelihood` and `posterior` vectors. With `logarithmic=True`, the first two fields
are `log_prior` and `log_likelihood`. Unknown fields, Boolean probabilities and
nonfinite values reject. Direct Python callers can use
`free_energy_log(log_prior, log_likelihood, posterior)`; the candidate remains a
normalized linear vector.

Log probabilities must be finite and nonpositive. An input null denotes an exact
zero probability, rather than a very small positive atom. The calculation shifts
likelihoods before forming relative joint logs, then normalizes shifted weights.
This retains prior ratios under a common extreme likelihood scale. Shifted
log-sum-exp and softmax evaluation has an established numerical-analysis literature;
it does not remove finite-precision error
([Blanchard, Higham and Higham, 2019](https://arxiv.org/abs/1909.03469v1)).

The log result includes finite `log_evidence`, `log_exact_posterior`, the objective,
posterior KL and decomposition residual. A null output `evidence` means positive
evidence below the linear float range. A null `log_exact_posterior` atom means exact
zero support. Rounded posterior atoms that underflow are listed in
`posterior_underflow_indices`; their finite log values remain available. Impossible
evidence, positive candidate mass on exact zero support, and calculations beyond
finite logarithmic range reject. No epsilon replaces zero or impossible support.

Independent high-precision Decimal examples, seeded multistate calculations,
likelihood-scale and structural-zero controls exercise this contract. They test
the supplied finite calculation, not an organism or a SUMO interpretation theorem.

## Pinned source and semantic mismatch

Source inspection reads committed Git objects at
`9a0694f16b8e89b66b2f7f8cc7426c650dd2c4de` and reports declaration line links.
It does not run Lean, modify the checkout, or treat uncommitted files as pinned
evidence. `working_tree_clean` describes the inspected repository's current status,
independently of the pinned object's contents.

The finite-information source uses `Real.log`, real division, and the `klFun`
integrand with totalized behavior at zero reference atoms. Its logarithmic
cross-entropy identity requires strict reference support. Rikishi rejects infinite
support cases, so the two definitions must not be called equivalent over all inputs.
See the pinned declarations:

- [`finiteKL_nonneg`](https://github.com/ActiveInferenceInstitute/fep_formal/blob/9a0694f16b8e89b66b2f7f8cc7426c650dd2c4de/lean/FepSketches/finite_information.lean#L43).
- [`finiteKL_self`](https://github.com/ActiveInferenceInstitute/fep_formal/blob/9a0694f16b8e89b66b2f7f8cc7426c650dd2c4de/lean/FepSketches/finite_information.lean#L49).
- [`finiteKL_eq_crossEntropy_sub_entropy`](https://github.com/ActiveInferenceInstitute/fep_formal/blob/9a0694f16b8e89b66b2f7f8cc7426c650dd2c4de/lean/FepSketches/finite_information.lean#L146).

## Proposed SUMO correspondence

[Douglass and collaborators' alignment preprint](https://doi.org/10.5281/zenodo.11463326)
is direct prior work on connecting Active Inference vocabulary to SUMO. Read the
[precedent guide](precedent-alignment.md) before interpreting the local proposal.
The source document's tentative correspondences, Rikishi's exploratory source extension, the
finite calculation, and Lean elaboration have separate evidence requirements.

`config/fep_mappings.json` stores candidates and outstanding obligations. Search
the installed SUMO index for each candidate, inspect its defining axioms, and record
source locations before adopting it. `ProbabilityFn` can anchor probability-related
vocabulary; `Function` and `NonnegativeRealNumber` can describe numerical outputs;
`Reasoning`, `Process`, and `Agent` can locate inference-related descriptions.
These are candidate vocabulary anchors, not imported FEP axioms.

To make a correspondence formal, define a finite carrier interpretation, translate
types and arguments explicitly, preserve normalization and support assumptions,
state which logic and arithmetic semantics the target supports, and prove
soundness on the chosen fragment. A SUMO theorem-prover result and a Lean theorem
need separate receipts. Neither can replace the other.
## Scholarly interpretation

The finite objective is the negative evidence lower bound (ELBO) in the convention of
[Blei, Kucukelbir, and McAuliffe (2017), Section 2.2](https://www.cs.columbia.edu/~blei/papers/BleiKucukelbirMcAuliffe2017.pdf).
[Friston (2010), Box 1](https://doi.org/10.1038/nrn2787) motivates the FEP connection,
but the binary example implements no agent dynamics or action selection.
The [claim ledger](scholarship.md) records this distinction and the exact
source-inspection boundary for Lean's totalized finite KL definition.

## Isolated Lean compilation

`uv run rikishi fep-verify` now provides a separate compilation workflow. It reads
`finite_probability.lean` and `finite_information.lean` from the pinned Git object,
checks dependency revisions from its Lake manifest, and compiles in a new output
directory with the pinned external Lean toolchain. The compiler version, modules,
declarations and dependency inventory are recorded in
`output/formalization/verification.json`. It uses the existing compiled dependency
libraries; it does not rebuild all of Mathlib. The verifier fingerprints all
compiled dependency and toolchain library artifacts before and after execution,
and requires stability. This complete cache snapshot is a superset of transitive
imports; immediate-import hashes are also retained. Symlinked cache entries and ancestors are
refused because directory traversal would otherwise omit inputs Lean can load.
Outputs inside the canonical source checkout, dependency caches, or toolchain
directory are refused before workspace creation. Cache inventory validation also
precedes workspace creation. The canonical checkout and its
build tree remain unchanged.

The generated axiom driver follows the freshly compiled module format. Split
module sidecars select Lean's modern module imports while preserving native
per-declaration axiom inspection, the compiler timeout and complete public,
private, server and intermediate representation (IR) artifact bindings. Real split-module controls require
rejection of a private axiom used by a public theorem and warning-suppressed
`sorryAx`; changing import loading does not waive admission checks.

The retained run compiled the stated finite modules and inspected their named
declaration axiom reports. Their basis was `propext`, `Classical.choice`, and `Quot.sound`.
The verifier rejects `sorryAx`, unapproved axioms, wrong toolchain/dependency pins,
and occupied output directories. Tests supply incorrect and admitted Lean proofs
to the actual compiler and require rejection. This establishes elaboration of
those pinned modules against the recorded local dependency artifacts. The proposed
SUMO mapping still needs an interpretation and a preservation theorem.

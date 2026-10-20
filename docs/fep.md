# Free energy: computation, vocabulary, and proof boundaries

Rikishi includes a finite probabilistic example and a source inspection bridge to
[`fep_formal`](https://github.com/ActiveInferenceInstitute/fep_formal). These have
different evidence requirements. A numerical identity can be checked by arithmetic;
an ontology correspondence needs an interpretation; a theorem claim needs a checked
proof and a statement of assumptions.

## Run the example

From the project environment, run `uv run python examples/fep_demo.py`. The public
Python entrypoints are `rikishi.fep.demo`, `free_energy`, and
`inspect_formalization`. Results are finite JSON numbers in natural-log units (nats).

The state prior is `(0.5, 0.5)` and the likelihood of one observed outcome is
`(0.8, 0.2)`. The likelihood vector is conditional on state and need not sum to one.
Joint mass is `(0.4, 0.1)`, evidence is `0.5`, and exact posterior is `(0.8, 0.2)`.
For candidate posterior `(0.5, 0.5)`, free energy is `log(2.5)` and KL to the exact
posterior is `log(1.25)`. At the exact posterior, free energy equals `log(2)`.

For state `s`, observation `o`, and candidate law `q`:

$$F(q)=\sum_s q(s)\log\frac{q(s)}{p(s,o)}
      =D_{KL}(q\Vert p(\cdot\mid o))-\log p(o).$$

The code separately calculates both sides and reports their residual. A 101-point
grid visualizes how the objective changes, including the exact minimum at `q(0)=0.8`.
This is variational inference in a supplied finite model. It supplies no empirical
evidence that an organism minimizes this objective and does not establish the
Free Energy Principle as a universal statement.

## Input and numerical contract

Prior and candidate must be normalized nonnegative finite vectors; likelihood
entries must lie in `[0,1]`. Equal dimensions and positive observation evidence are
required. Zero candidate mass contributes zero. Positive candidate mass on a zero
joint atom is rejected because its objective is infinite; this avoids invalid JSON
or a misleading finite sentinel. Underflow of a positive product to zero is treated
as unsupported floating-point support. Extremely small probabilities should be
handled by a future log-domain implementation before drawing numerical conclusions.

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

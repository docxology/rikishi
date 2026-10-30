---
name: rikishi-fep
description: Use for Rikishi finite or logarithmic free energy, shared-witness SUMO and Lean execution, interpretation experiments, and pinned Lean inspection or compilation.
---

# Rikishi FEP investigation

All paths and commands below are relative to the repository root.

Read `docs/fep.md` and `config/fep_mappings.json` first. Consult
`docs/scholarship.md` when interpreting or changing scientific claims.

For Active Inference action questions, read `docs/active-inference.md`. Run
`uv run rikishi active-demo` for the standalone one-step outcome-preference
planner. Inspect the complete transition/observation inputs, risk, ambiguity,
state information gain, signed decomposition residual, tolerance and all
minimizing names. `condition_action` consumes an actually supplied outcome after
prediction; scoring does not observe or simulate it. Distinguish this bounded
decision method from fixed-observation variational inference, existing witness
simulations, registered native campaigns, Lean theorems and empirical agency.

1. Run `uv run rikishi fep-demo` for the packaged model or `fep-evaluate MODEL.json`
   for explicit inputs. Add `--logarithmic` for log probabilities. Retain the JSON
   and distinguish exact zeros from underflow using the log-result fields.
2. Check normalization, support, units and the independently evaluated decomposition.
   For a selected interpretation campaign, follow `docs/research.md`; retain the
   study authority, source formulas, competency polarities, background controls,
   numerical references and raw prover captures in a fresh directory.
   Acquire and verify the original workbook using `docs/research.md`, then use
   `research-run NEW_DIRECTORY --prover e --workbook ACQUIRED_WORKBOOK.xlsx`;
   a fresh installation must not depend on the historical default workbook path.
   `research-verify REPORT --sha256 TRUSTED_DIGEST` replays saved evidence.
   Use a separate Vampire campaign to compare the same declared problems.
3. Use `inspect_formalization(Path(...))` to inspect pinned committed Lean source.
   Report its scope as source inspection, not a successful Lean build.
   For compilation, run `uv run rikishi fep-verify --output NEW_DIRECTORY` with
   the matching external compiler and pinned dependency caches. Retain its receipt:
   it binds source objects, compiler, complete compiled-cache fingerprints and
   declaration axiom reports. Dependency-cache drift fails the run; the canonical
   formalization checkout remains an input.
4. For the same finite witness across the numerical, Lean and ontology layers,
   read `docs/bridge-methods.md` and inspect `bridge-catalog` first. Run
   `bridge-run NEW_DIRECTORY --prover both` in the exclusive native slot and
   retain the report digest separately. Require the concrete Lean compilation,
   paired positive environments, diagnostic-specific invalid-proof controls,
   numerical references and every native problem role before crediting completion.
   `bridge-verify REPORT --sha256 TRUSTED_DIGEST` replays the retained packet;
   `bridge-case REPORT CASE_ID --prover e|v --sha256 TRUSTED_DIGEST` joins a native
   outcome to its source selections, assumptions and mathematical witness.
   Export the verified figures and offline explorer with
   `bridge-figures REPORT NEW_DIRECTORY --sha256 TRUSTED_DIGEST`.
   Preserve Boolean vector order `(false, true)`, the observation `true`, and the
   distinction between a source-required existential output and the named numeric
   result record. Replay checks retained evidence; it runs no Lean compiler or prover.
5. Retrieve candidate SUMO terms and their defining axioms before proposing an
   interpretation. Record the SUMO revision and each source location.
6. State remaining translation obligations. Explicitly address totalized Lean
   division/logarithm versus positive-support numerical KL.
7. Reproduce the manuscript through `docs/manuscript.md` when changing
   the example or its explanation; inspect the resulting artifacts. Run
   `scripts/verification-manuscript.py` to check current inputs and output hashes.

Do not infer SUMO/Lean equivalence, organism-level empirical support, or a theorem
proof from a plot or an imported declaration name.

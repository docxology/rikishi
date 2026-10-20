---
name: rikishi-fep
description: Use for rikishi finite free-energy examples, source-pinned Lean inspection, or proposed SUMO and Free Energy Principle vocabulary mappings.
---

# Rikishi FEP investigation

All paths and commands below are relative to the repository root.

Read `docs/fep.md` and `config/fep_mappings.json` first.

1. Run `uv run python examples/fep_demo.py` and retain the JSON.
2. Check the identity residual, units, normalization, evidence, and support.
3. Use `inspect_formalization(Path(...))` to inspect pinned committed Lean source.
   Report its scope as source inspection, not a successful Lean build.
4. Retrieve candidate SUMO terms and their defining axioms before proposing an
   interpretation. Record the SUMO revision and each source location.
5. State remaining translation obligations. Explicitly address totalized Lean
   division/logarithm versus positive-support numerical KL.
6. Reproduce the manuscript through `scripts/render_manuscript.py` when changing
   the example or its explanation; inspect the resulting artifacts.

Do not infer SUMO/Lean equivalence, organism-level empirical support, or a theorem
proof from a plot or an imported declaration name.

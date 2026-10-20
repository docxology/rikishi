# Model with SUMO without erasing logical context

SUMO source expressions carry more information than their names or a graph view.
When extending a model, first identify the intended entities, processes,
relationships, and assumptions, then inspect candidate terms in the installed
ontology. Use `rikishi term` to read formulas and documentation together.

## Distinguish modeling operations

`(subclass A B)` places class A beneath class B. `(instance a A)` classifies an
individual. Those are different statements; substituting one for the other changes
the model. Domain/range constraints, quantification, and implication also matter.
An expression appearing inside a conditional does not become a freestanding fact
merely because a parser finds its symbols.

Do not infer scientific adequacy from parser acceptance. A syntactically valid
class assertion may represent the wrong concept, admit unintended models, or
conflict with other commitments. Inspect relevant axioms and state your intended
interpretation before adding constraints.

## The illustrative FEP extension

[`examples/fep-ontology.kif`](../examples/fep-ontology.kif) is a separate proposal
containing six formulas: three classification statements and three documentation
statements. Its principal assertion is:

```lisp
(subclass RikishiVariationalInference Reasoning)
```

The proposal also introduces a finite-generative-model class under `Proposition`
and an instance representing the binary inference example. This is an exploratory
choice of representation, not a claim that every generative model is appropriately
modeled this way. Whether a model should instead be treated as an information
artifact, mathematical object, or proposition is a reviewable ontology decision.

The documentation explains the numerical example, but English documentation does
not impose executable probability constraints. Normalization, positive evidence,
and support are enforced by `rikishi.fep.free_energy`. The KIF file does not prove
those properties and does not import the Lean declarations.

## Inspect the proposal safely

Read and parse the file as a separate input before considering a combined KB.
The upstream checkout stays unmodified. To inspect the local syntax directly:

```python
from pathlib import Path
from rikishi.kif import parse

source = Path("examples/fep-ontology.kif")
formulas = list(parse(source.read_text(), str(source)))
print(len(formulas))
```

To compare candidate vocabulary, run `uv run rikishi term Reasoning` and inspect its source
axioms. A taxonomy proof over upstream `Merge.kif` does not automatically include
this separate extension. Loading it into a Sigma working KB is a distinct,
deliberate experiment with its own profile and evidence.

## Obligations for a formal bridge

An actual SUMO/Lean connection needs a precise interpretation of carriers, types,
relations, functions, and proof statements. Specify finite-state normalization,
observation likelihoods, and zero-support behavior. The pinned Lean source's
totalized arithmetic differs from the numerical operator's domain rejection.
Restrict domains explicitly before attempting a correspondence theorem.

Record each proposed mapping's source term, defining axioms, Lean declaration,
assumptions, and unresolved obligation. The structured starting point is
[`config/fep_mappings.json`](../config/fep_mappings.json). Have the interpretation
reviewed independently before presenting it as a mathematical or scientific result.

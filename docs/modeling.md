# Model without erasing logical context

Suggested Upper Merged Ontology (SUMO) source expressions carry more information
than their names or a graph view. Their authoring language is the Standard Upper
Ontology Knowledge Interchange Format (SUO-KIF).
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

## The illustrative Free Energy Principle (FEP) extension

[`examples/fep-ontology.kif`](../examples/fep-ontology.kif) is a separate proposal
containing local class, instance and relation assertions. Its inference-class assertion is:

```lisp
(subclass RikishiVariationalInference Process)
```

The proposal also introduces a finite-generative-model class under `Proposition`,
separate model/content and binary-execution instances, and an `abstractCounterpart`
relation between them. This is an exploratory choice of representation, not a
claim that every generative model is appropriately
modeled this way. Whether a model should instead be treated as an information
artifact, mathematical object, or proposition is a reviewable ontology decision.

The SUO-KIF extension imposes no numerical probability axioms. Normalization,
positive evidence and support are enforced separately by `rikishi.fep.free_energy`
and `free_energy_log`. The source file does not prove those properties or import
Lean declarations.

Active Inference–SUMO alignment has an explicit scholarly precedent in
[Douglass and collaborators](https://doi.org/10.5281/zenodo.11463326).
The local extension is an illustrative modeling choice rather than a validated
implementation of that work. The [alignment guide](precedent-alignment.md)
explains how to retain source provenance, justify the mapping relation, and define
competency questions before asserting a correspondence.

The separate [versioned finite study](research.md) now executes one declared
model/content and physical-execution interpretation with typed
`abstractCounterpart` arguments. It retains original workbook cells, selected
complete SUMO formulas, local extension and explicit first-order logic (FOL) kernel. E and Vampire
each match all 12 logical cases, including baseline and alias/inhabitation
controls. Its 144 numerical rows, four boundary cases and eight invalid-input
rejections are a separate arithmetic experiment. This checks selected obligations;
it neither translates arbitrary SUO-KIF nor validates the whole earlier alignment.

## Inspect the proposal safely

Read and parse the file as a separate input before considering a combined knowledge base (KB).
The upstream checkout stays unmodified. To inspect the local syntax directly:

```python
from pathlib import Path
from rikishi.kif import parse

source = Path("examples/fep-ontology.kif")
formulas = list(parse(source.read_text(), str(source)))
print(len(formulas))
```

To compare candidate vocabulary, run `uv run rikishi term Process` and inspect its source
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

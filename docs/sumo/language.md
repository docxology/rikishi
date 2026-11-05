# Read the source language from the outside in

Standard Upper Ontology Knowledge Interchange Format (SUO-KIF) is the language
used to author the Suggested Upper Merged Ontology (SUMO). SUMO supplies the vocabulary and axioms; SUO-KIF supplies
the notation in which they are written. Sigma is software that reads and
translates selected content. Keeping these roles separate makes a source file
easier to read and a prover result easier to interpret.

Read the [ontology introduction](ontology.md) for the modeling distinctions and
the [systems guide](systems.md) for the translation pipeline. The versioned
[SUO-KIF manual](https://github.com/ontologyportal/sigmakee/blob/d3cc7b43b38b0b45692291a1b33fe2b1a3de0095/suo-kif.pdf)
is the language reference corresponding to Rikishi's Sigma pin.

## Parentheses express logical structure

SUO-KIF uses parenthesized prefix expressions: the operator or relation comes
first, followed by its arguments. Read the outer expression before reading any
inner occurrence. In an implication, the antecedent gives the condition under
which the consequent is asserted. In a negation, the enclosed formula is being
denied. In a quantified expression, the variable list and body determine scope.

One of Rikishi's existing source examples is:

```lisp
(domain agent 1 Process)
```

Here `domain` is the predicate, `agent` names the relation being described,
`1` identifies an argument position, and `Process` supplies the restriction.
The declaration concerns the first argument of `agent`; it is not an assertion
that `agent` itself is a process. The companion source declaration restricts
the second argument to `AutonomousAgent`. Both belong to the
[pinned passage](https://github.com/ontologyportal/sumo/blob/efcd059f8feebfe3488a09f575f88d4d009b1e5c/Merge.kif#L3158-L3174)
already selected by the [source demonstration](sumo-demonstrations.md).

| Form or feature | How to read it | Practical implication |
| --- | --- | --- |
| Predicate application | A relationship is asserted of the supplied arguments, subject to its enclosing scope. | It forms a formula; free variables still need their declared closure or bindings. |
| Function application | A term is interpreted with the function's declared definedness and result conditions. | It is not an instruction to execute a Python or Java function; do not assume every source function is total. |
| `and`, `or`, `not` | Conjunction, disjunction and logical negation. | Negation is explicit; a failed lookup is a different event. |
| `=>`, `<=>` | Implication and equivalence of formulas. | Reversing an implication generally changes the statement. |
| `forall`, `exists` | Universal and existential quantification. | Locate the body of each quantifier and keep their order. |
| `equal` | Equality between denoted terms in the selected interpretation. | It is not variable assignment and does not imply that different spellings denote different entities. |
| A quoted string | Source text used as an argument, commonly in documentation or presentation. | English explanations do not automatically become executable property axioms. |
| A semicolon comment | Source commentary outside the parsed assertion. | Commented expressions do not belong to the active theory. |

Capitalization and common suffixes are useful conventions, but the source
assertions supply the actual classifications. The same symbol may be discussed
as an entity in one formula and used as a predicate or function in another.
That usage needs a representation policy in a target that separates object
constants from predicate symbols.

## A unary function can have a binary relational graph

SUMO's function vocabulary makes the term/sentence distinction concrete.
`UnaryFunction` is a subclass of both `Function` and `BinaryRelation`, while
the active valence rule gives its instances one explicit function argument.
The two classifications describe different views: one input in term-forming
notation, or an input–output pair in the function's relational graph. They
do not make it a two-input function. Read the
[declarations and valence rule together](https://github.com/ontologyportal/sumo/blob/efcd059f8feebfe3488a09f575f88d4d009b1e5c/Merge.kif#L4230-L4270).

`ProbabilityFn` is such a unary function. Its declared input is a `Formula`
and its range is `RealNumber`; it is also explicitly classified as
`TotalValuedRelation`. Its application denotes a probability value under the
stated source interpretation.
The nearby `conditionalProbability` is instead a `TernaryPredicate`, with
two formula arguments and a third numerical argument. Its source documentation
specifies that the second formula is conditioned on the first. The order
therefore matters. See the [probability declarations](https://github.com/ontologyportal/sumo/blob/efcd059f8feebfe3488a09f575f88d4d009b1e5c/Merge.kif#L3334-L3364).
These source signatures do not by themselves define Rikishi's finite
probability-vector encoding, normalization or numerical implementation.

## Variables, closure and quantifier order

An ordinary variable starts with `?`. Its occurrences are bound by the
applicable explicit quantifier or handled according to the assertion/query
policy. The pinned Sigma implementation makes unbound assertion variables
universally quantified and unbound query variables existentially quantified;
see [Formula.makeQuantifiersExplicit](https://github.com/ontologyportal/sigmakee/blob/d3cc7b43b38b0b45692291a1b33fe2b1a3de0095/src/java/com/articulate/sigma/Formula.java#L2296-L2317)
and the corresponding [Thousands of Problems for Theorem Provers (TPTP) query/axiom closure](https://github.com/ontologyportal/sigmakee/blob/d3cc7b43b38b0b45692291a1b33fe2b1a3de0095/src/java/com/articulate/sigma/trans/SUMOformulaToTPTPformula.java#L565-L590).
The checked implementation is identified in the [source lock](../../config/sumo.lock.json).

For a worked query, state quantifiers explicitly before submitting it. “For
every object there is a suitable witness” permits a different witness for each
object. “There is a witness suitable for every object” requires one common
witness. Exchanging those scopes can change whether a consequence follows.
An existential result also need not supply a source-named or unique object.

Rikishi's selected kernel compiler has its own explicit contract: it universally
closes free variables after the recorded finite predicate specialization. It
does not infer the complete Sigma query policy from a formula's typography.
The declared study records the intended conjectures and assumptions. See the
[inference methods](../methods/inference-methods.md) and
[compiler source](../../src/rikishi/inference_compiler.py).

## Features beyond ordinary fixed-arity first-order notation

| Source construct | Additional meaning needed | What a selected target must identify |
| --- | --- | --- |
| A variable in predicate position | Application of a relation whose identity varies. | Whether a finite set of named relations is instantiated, a relation-application encoding is used, or a higher-order interpretation is supplied. |
| A row variable beginning with `@` | An argument sequence rather than one ordinary argument. | The admitted sequence lengths and arities, or a semantic representation of sequences. |
| A variable-arity relation or function | Uses with different numbers of arguments. | Any fixed-arity renamed symbols and the rule relating their meanings. |
| A formula in argument position | A proposition, quotation, or context-bearing expression according to the construct. | How its content and any temporal, modal or epistemic context are interpreted. |
| A class-forming expression | A class specified using a condition. | The class-formation mechanism and its restrictions in the chosen target. |

The active subrelation rule uses the same row sequence in both predicate
applications, under predicate guards. Its source is
[Merge.kif201–207](https://github.com/ontologyportal/sumo/blob/efcd059f8feebfe3488a09f575f88d4d009b1e5c/Merge.kif#L201-L207).
Understanding the whole rule matters more than extracting its two head names.

Sigma's first-order preprocessing may instantiate predicate variables, expand
row variables and specialize variable arities. Pease's
[typed-translation paper, §1](https://arxiv.org/html/2303.04148v1#S1)
describes these steps and explicitly bounds the higher-order content retained
in a first-order target. That is different from the sequence and
class-formation interpretation in [SUMO-K, §§2–3](https://arxiv.org/html/2305.07903v1#S2).
Neither account establishes that arbitrary nested source expressions can be
flattened into ordinary predicates without changing the intended question.

## What Rikishi reads and what it reasons about

The source parser retains complete formulas and source locations. The graph
projection selects eligible top-level binary assertions. The kernel compiler
supports a narrower function-free first-order language with explicit equality,
quantifiers, connectives and recorded finite predicate substitutions. It rejects
function terms, strings and unresolved predicate/row variables instead of
silently pretending to translate them.

Numeral tokens in that kernel are uninterpreted object constants. They do not
acquire arithmetic operations or an ordering merely because they look like
numbers. The separate finite numerical methods perform the declared
probability calculations. The [semantic-transport guide](../methods/semantic-transport.md)
explains what would be needed to prove a stronger correspondence.

When reading a result, follow the same sequence: inspect the complete source
formula; identify its quantifier and contextual scope; inspect the translation
policy and actual submitted target problem; then interpret the captured status.
The [inference tutorial](../runtime/inference-tutorial.md) walks through those
evidence objects.

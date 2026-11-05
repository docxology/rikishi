# How an upper ontology models a domain

The Suggested Upper Merged Ontology (SUMO) is a theory of categories and
relationships expressed through logical axioms. It provides vocabulary for
describing things such as objects, processes, propositions, quantities and
participants, together with constraints on how those descriptions fit together.
An upper ontology supplies general commitments that a domain theory can reuse.
It does not supply the observations or empirical validation for that domain.
Its authoring language is Standard Upper Ontology Knowledge Interchange Format
(SUO-KIF).

Start here for the modeling ideas, continue with [reading SUO-KIF](language.md)
for the source notation, and use [systems and translations](systems.md) to
understand what Sigma and the provers do with it. The [modeling guide](modeling.md)
applies these distinctions to Rikishi's proposed Free Energy Principle (FEP) extension.

## Vocabulary, statements and models

A vocabulary is a collection of symbols. An axiom uses those symbols to make a
logical statement. An interpretation gives the symbols meanings in a domain;
it is a model of the selected axioms when it satisfies them. These three levels
explain why finding a term, parsing a file and proving a consequence are different
achievements.

In SUMO, a familiar English name is a clue to investigate. Its classifications,
argument roles and active axioms determine how the ontology uses it. In
particular, lowercase `agent` names a relation between a process and a
participant; `AutonomousAgent` names a class. A scientific account of an agent
needs to choose its intended entity and behavior before choosing a matching
label. See the pinned [agent signatures and documentation](https://github.com/ontologyportal/sumo/blob/efcd059f8feebfe3488a09f575f88d4d009b1e5c/Merge.kif#L3158-L3174).

The original SUMO construction distinguished converting source representations
into a common syntax from reconciling their conceptual commitments. These remain
different tasks when an application adds its own vocabulary: using the same
language does not establish agreement about meaning. The historical account is
in Niles and Pease's [original paper, §§2–3](https://adampease.com/FOIS.pdf).

## Membership is different from specialization

| Concept | What the statement concerns | What to preserve |
| --- | --- | --- |
| An entity | Something in the domain of discourse, which may be ordinary or abstract. | The broad logical use of “entity” does not identify it with SUMO's specific `Object` class. |
| An `instance` relationship | An entity's membership in a class. | Membership may hold for several classes; it does not automatically assert membership in one most specific class. |
| A `subclass` relationship | Inclusion between classes through their instances. | It relates classes; it is not an assertion that the first class is an ordinary member of the second. |
| A class treated as an entity | A class can itself occupy an argument position in a source assertion. | Being mentioned as an argument does not turn the class's instances into the class itself. |
| A class of classes | A modeling role in which the members are themselves classes. | Membership at that level and subclass inclusion still need separate statements; there is no automatic lift from one to the other. |
| A relation or function entity | A named relationship/operator can itself be classified and given a signature. | Its use in predicate/function position and its occurrence as an object-level argument have different roles. |

The pinned source's [membership and subclass documentation and propagation
axiom](https://github.com/ontologyportal/sumo/blob/efcd059f8feebfe3488a09f575f88d4d009b1e5c/Merge.kif#L83-L150)
give a concrete reading: membership in a subclass propagates to its superclass.
This supports multiple classification. It does not make every class a
programming-language type or prescribe one universal encoding of classes.

For an existing example, `ProbabilityFn` is classified as an instance of
`UnaryFunction`, while `UnaryFunction` is a subclass of `Function`. The former
describes a function entity; the latter describes inclusion between function
classes. Replacing membership by subclassing would change the claim. Inspect the
[function's declarations](https://github.com/ontologyportal/sumo/blob/efcd059f8feebfe3488a09f575f88d4d009b1e5c/Merge.kif#L3334-L3346)
and [function hierarchy](https://github.com/ontologyportal/sumo/blob/efcd059f8feebfe3488a09f575f88d4d009b1e5c/Merge.kif#L4242-L4265).

## Signatures say which role an argument plays

| Signature relation | Intended restriction | Distinction that matters |
| --- | --- | --- |
| `domain` | A relation argument is an instance of the indicated class. | It classifies the argument entity. |
| `domainSubclass` | A relation argument is a subclass of the indicated class. | The argument supplies a class; ordinary membership is a different constraint. |
| `range` | A function's value is an instance of the indicated class. | It constrains values denoted by applications of the function. |
| `rangeSubclass` | A function's value is a subclass of the indicated class. | The value is class-valued under that restriction. |

These readings come from active documentation assertions and, for the range
forms, explicit value-conclusion axioms in the pinned source:
[argument restrictions](https://github.com/ontologyportal/sumo/blob/efcd059f8feebfe3488a09f575f88d4d009b1e5c/Merge.kif#L216-L265)
and [function results](https://github.com/ontologyportal/sumo/blob/efcd059f8feebfe3488a09f575f88d4d009b1e5c/Merge.kif#L320-L383).
The source also imposes comparability conditions on multiple restrictions of
the same kind at one position. A signature therefore belongs to a logical
theory and to the tools' preprocessing policy; it is not simply a column type
that Rikishi's graph automatically enforces.

## Source context controls the meaning

SUMO includes quantified rules, disjointness conditions, nested formulas and
documentation. A relation appearing inside a rule's antecedent is being used
under that condition. A sentence inside a temporal or epistemic context has
that context. Neither occurrence can be copied into a graph as an unconditional
fact without an additional justification.

There is a second distinction between source text and active source content.
In this pin, the older `Class` discussion near lines2827–2841 and its adjacent
subclass declaration are commented out. They cannot establish an active axiom
about extensionality or self-membership. The active `Set` documentation and
`Relation` declarations must be read in their own right. See the
[complete passage](https://github.com/ontologyportal/sumo/blob/efcd059f8feebfe3488a09f575f88d4d009b1e5c/Merge.kif#L2817-L2873).
Documentation gives an intended interpretation; it is not a substitute for the
axioms that a selected reasoning translation actually implements.

## Incomplete knowledge and bounded reasoning

For the classical first-order interpretation used by Rikishi's selected
kernels, a consequence must hold in every model of the submitted axioms. A
missing source assertion does not establish its negation. A bounded search
that finds no proof also does not establish non-entailment. Explicit negation,
a countermodel and a timeout convey different information.

Adding axioms preserves existing classical consequences while reducing the
permitted models. If no model remains, the theory is inconsistent and ordinary
classical entailment cannot discriminate intended positive from negative
claims. Background satisfiability and premise-removal controls therefore have
an operational purpose, explained in the [inference method](../methods/inference-methods.md).

Likewise, a list of names does not by itself state that all entities are named
or that different names denote different entities. Rikishi's selected kernel
adds no implicit domain closure or unique-names rule. Such assumptions must
come from the identified axioms or an explicitly documented target policy.
This is a claim about the declared kernel, rather than an audit of every
possible SUMO-derived system.

The distinction between open-world reasoning and an explicit completion policy
also appears in Álvez, Gonzalez-Dios and Rigau's
[study of closed-world extensions, introduction](https://www.ixa.eus/sites/default/files/dokumentuak/13095/FAIA-325-FAIA200142.pdf).
Their extension changes the theory; its reported outcomes are not measurements
of Rikishi.

## From a domain idea to a reviewable extension

Describe the intended referents first: model content, a physical execution,
an observation, an agent or a relationship. Then inspect candidate terms and
their complete source formulas. State argument order and signature choices,
the assumptions needed for the proposed consequence, and questions that should
remain unsupported. The [upstream formalization guidance](https://github.com/ontologyportal/sumo/wiki/SUO%E2%80%90KIF-Formalizing-Terms)
calls for property axioms as well as taxonomic placement and documentation.

For Rikishi's FEP work, ontology representation, finite probability arithmetic,
Lean theorem instantiation and synthetic simulation each have their own
acceptance conditions. A shared term or one successful query does not collapse
those conditions into one result. Continue with the
[SUMO–FEP–simulation guide](sumo-fep-simulations.md) for the concrete connection.

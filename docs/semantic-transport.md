# A restricted event-transport contract

The executable `rikishi.event_transport.FiniteStateMap` makes one small part of
the representation question precise. It does not interpret complete Suggested Upper Merged Ontology (SUMO) or
prove that Python execution is equivalent to Lean. The
[bridge contract](bridge-methods.md) retains the distinct ontology, numerical,
formal and native-execution scopes.

## Carriers, maps and events

`FiniteStateMap(source, target, images)` is immutable. The two carriers are
nonempty tuples of distinct trimmed string identities; `images[i]` supplies
exactly one declared target for `source[i]`. A target can contain unreachable
states. An event is a `frozenset` contained in the correct carrier. Numbers,
ordinary sets and unknown names are not silently coerced.

`direct_image(A)` collects targets reached by the source event. `inverse_image(B)`
collects source states mapping into the target event. `pushforward(p)` transports
a normalized exact `Fraction` law in declared carrier order; unreachable target
states receive zero. `is_injective` and `is_surjective` describe different facts.

For every target event pair, inverse images preserve union, intersection and
carrier-relative complement. Direct images preserve unions, but a many-to-one
map can lose intersections. Even an injective map need not preserve complements
relative to the full target if some target state is unreachable. A bijection
preserves these event distinctions in both directions.

The simplest counterexample maps `false` and `true` to one target. The images of
the two singleton events overlap although their source intersection is empty.
The transported total probability is still one. Mass preservation therefore
does not establish preservation of every event operation.

## Exact checks and separate Lean statements

The Python tests enumerate all maps and event pairs over declared small
carriers, including invalid inputs, injective/non-surjective and coarsening
controls. They also independently check the probability identity
`pushforward(p)(B) = p(inverse_image(B))`. This is a finite executable check,
not a proof of arbitrary Python execution.

The [Lean example](../examples/EventTransport.lean) contains:

- `RikishiEventTransport.pullback_union`
- `RikishiEventTransport.pullback_intersection`
- `RikishiEventTransport.pullback_complement`
- `RikishiEventTransport.collapse_intersection_failure`

The first three concern general set inverse images; the fourth is the explicit
Boolean-to-unit counterexample. A separate integration test elaborates the
actual example with the existing pinned compiler/cache authority, checks each
reported axiom inventory, compiles a same-import paired positive and requires
the false-event claim to fail for its intended type mismatch. Dependency
caches remain inputs and are compared before and after. Missing prerequisites
fail that test; they do not become a successful proof rejection.

These four statements are **not** added to the bridge's existing 51-declaration
population. The manuscript distributes exact proof-source copies, verifies them
against the example, and keeps actual compilation receipts in the corresponding
build evidence. General semantic transport remains [MAJ-01](TODO.md).

## What remains before a SUMO preservation claim

Specify the supported sentence fragment, event/proposition interpretation,
source-to-target direction, function membership and equality, probability and
conditioning semantics, support/partiality and required logarithm operations.
Then state and prove the appropriate satisfaction/operation correspondence,
with false-case controls that fail for the intended semantic reason. A
`represents` assertion, matching posterior or successful set identity alone
does not discharge those obligations. Empirical meaning requires additional
measurement and domain evidence.

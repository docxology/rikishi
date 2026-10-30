from __future__ import annotations

from dataclasses import FrozenInstanceError
from fractions import Fraction
from itertools import combinations, product

import pytest

from rikishi.event_transport import EventTransportError, FiniteStateMap
from rikishi.finite_channels import FiniteChannelError


def _events(carrier: tuple[str, ...]) -> tuple[frozenset[str], ...]:
    return tuple(frozenset(items) for count in range(len(carrier) + 1)
                 for items in combinations(carrier, count))


def test_coarsening_loses_intersection_while_preserving_total_mass() -> None:
    # Given two distinct fine states collapsed into one coarse state.
    mapping = FiniteStateMap(("false", "true"), ("unit",), ("unit", "unit"))
    left, right = frozenset({"false"}), frozenset({"true"})
    # When taking their direct images.
    intersection_of_images = mapping.direct_image(left) & mapping.direct_image(right)
    image_of_intersection = mapping.direct_image(left & right)
    # Then distinct disjoint events collide, despite normalized mass transport.
    assert intersection_of_images == frozenset({"unit"})
    assert image_of_intersection == frozenset()
    assert mapping.pushforward((Fraction(1, 4), Fraction(3, 4))) == (Fraction(1),)
    assert mapping.is_surjective and not mapping.is_injective


@pytest.mark.parametrize("source,target", [
    (("a",), ("x",)), (("a",), ("x", "y")),
    (("a", "b"), ("x",)), (("a", "b"), ("x", "y")),
    (("a", "b", "c"), ("x", "y")),
])
def test_all_small_maps_pull_back_boolean_operations(source, target) -> None:
    # Given every map between these finite carriers and every target event pair.
    universe = frozenset(source)
    target_universe = frozenset(target)
    for images in product(target, repeat=len(source)):
        mapping = FiniteStateMap(source, target, images)
        for left, right in product(_events(target), repeat=2):
            # When pulling back union, intersection and target-relative complement.
            union = mapping.inverse_image(left | right)
            intersection = mapping.inverse_image(left & right)
            complement = mapping.inverse_image(target_universe - left)
            # Then membership truth is preserved for each Boolean operation.
            assert union == mapping.inverse_image(left) | mapping.inverse_image(right)
            assert intersection == mapping.inverse_image(left) & mapping.inverse_image(right)
            assert complement == universe - mapping.inverse_image(left)


def test_bijection_transports_each_event_and_its_complement() -> None:
    # Given a relabeling that is both injective and surjective.
    mapping = FiniteStateMap(("false", "true"), ("zero", "one"), ("one", "zero"))
    # When transporting every fine event and every event pair.
    for left, right in product(_events(mapping.source), repeat=2):
        # Then inverse transport recovers the event and direct Boolean operations agree.
        assert mapping.inverse_image(mapping.direct_image(left)) == left
        assert mapping.direct_image(left & right) == (
            mapping.direct_image(left) & mapping.direct_image(right))
        assert mapping.direct_image(frozenset(mapping.source) - left) == (
            frozenset(mapping.target) - mapping.direct_image(left))
    assert mapping.is_injective and mapping.is_surjective


@pytest.mark.parametrize("source,target", [
    (("a",), ("x",)), (("a",), ("x", "y")),
    (("a", "b"), ("x",)), (("a", "b"), ("x", "y")),
    (("a", "b"), ("x", "y", "z")), (("a", "b", "c"), ("x", "y")),
])
def test_direct_boolean_operation_conditions_on_all_small_maps(source, target) -> None:
    # Given every total map between each small pair of named carriers.
    events = _events(source)
    for images in product(target, repeat=len(source)):
        mapping = FiniteStateMap(source, target, images)
        # When exhaustively checking each source event and event pair.
        unions = all(mapping.direct_image(a | b) == mapping.direct_image(a) | mapping.direct_image(b)
                     for a, b in product(events, repeat=2))
        intersections = all(
            mapping.direct_image(a & b) == mapping.direct_image(a) & mapping.direct_image(b)
            for a, b in product(events, repeat=2))
        complements = all(mapping.direct_image(frozenset(source) - a)
                          == frozenset(target) - mapping.direct_image(a) for a in events)
        # Then union always survives, intersection needs injection and full complement a bijection.
        assert unions
        assert intersections == mapping.is_injective
        assert complements == (mapping.is_injective and mapping.is_surjective)


def test_injection_without_surjection_does_not_preserve_full_target_complement() -> None:
    # Given an injective map with an unreachable target state.
    mapping = FiniteStateMap(("a",), ("x", "unused"), ("x",))
    # When comparing complements relative to the declared full carriers.
    direct_complement = mapping.direct_image(frozenset())
    target_complement = frozenset(mapping.target) - mapping.direct_image(frozenset({"a"}))
    # Then injectivity alone is insufficient for this full-codomain complement claim.
    assert direct_complement == frozenset()
    assert target_complement == frozenset({"unused"})
    assert mapping.is_injective and not mapping.is_surjective


def test_pushforward_event_mass_equals_inverse_image_mass() -> None:
    # Given a many-to-one map and a nonuniform exact law.
    source, target = ("a", "b", "c"), ("x", "y", "unused")
    law = (Fraction(1, 6), Fraction(1, 3), Fraction(1, 2))
    mapping = FiniteStateMap(source, target, ("x", "y", "x"))
    # When transporting the law and evaluating all target events.
    transported = mapping.pushforward(law)
    # Then event mass equals the original mass on the event's full inverse image.
    assert transported == (Fraction(2, 3), Fraction(1, 3), Fraction(0))
    for event in _events(target):
        expected = sum((mass for state, mass in zip(source, law, strict=True)
                        if state in mapping.inverse_image(event)), Fraction(0))
        actual = sum((mass for state, mass in zip(target, transported, strict=True)
                      if state in event), Fraction(0))
        assert actual == expected


@pytest.mark.parametrize("source,target,images", [
    ((), ("x",), ()), (("a",), (), ("x",)),
    (("a", "a"), ("x",), ("x", "x")), (("a",), ("x", "x"), ("x",)),
    (("",), ("x",), ("x",)), (("a",), (" x",), (" x",)),
    (("a ",), ("x",), ("x",)), (("a",), ("\t",), ("\t",)),
    ((True,), ("x",), ("x",)), (("a",), (1,), (1,)),
    (["a"], ("x",), ("x",)), (("a",), ["x"], ("x",)),
    (("a",), ("x",), ["x"]), (("a",), ("x",), ()),
    (("a",), ("x",), ("x", "x")), (("a",), ("x",), ("other",)),
    (("a",), ("x",), (True,)), (("a",), ("x",), (["x"],)),
])
def test_invalid_state_map_is_rejected_before_evaluation(source, target, images) -> None:
    # Given a malformed carrier or an incomplete/out-of-domain map.
    # When parsing the public immutable boundary, then it rejects without coercion.
    with pytest.raises(EventTransportError):
        FiniteStateMap(source, target, images)


@pytest.mark.parametrize("event", [{"a"}, ("a",), "a", frozenset({"other"}), frozenset({1})])
def test_invalid_source_event_is_rejected(event) -> None:
    mapping = FiniteStateMap(("a",), ("x",), ("x",))
    with pytest.raises(EventTransportError):
        mapping.direct_image(event)


@pytest.mark.parametrize("event", [{"x"}, ("x",), "x", frozenset({"other"}), frozenset({True})])
def test_invalid_target_event_is_rejected(event) -> None:
    mapping = FiniteStateMap(("a",), ("x",), ("x",))
    with pytest.raises(EventTransportError):
        mapping.inverse_image(event)


@pytest.mark.parametrize("law", [
    (), (Fraction(1),), (Fraction(1), Fraction(1)),
    (Fraction(-1), Fraction(2)), (0.5, 0.5), (True, False), [Fraction(1, 2)] * 2,
])
def test_invalid_probability_law_is_rejected(law) -> None:
    mapping = FiniteStateMap(("a", "b"), ("x",), ("x", "x"))
    with pytest.raises(FiniteChannelError):
        mapping.pushforward(law)


@pytest.mark.parametrize("field", ["source", "target", "images"])
def test_state_map_is_immutable(field: str) -> None:
    # Given a fully validated map.
    mapping = FiniteStateMap(("a",), ("x",), ("x",))
    # When attempting to replace any public field, then the frozen value rejects it.
    with pytest.raises(FrozenInstanceError):
        setattr(mapping, field, ("other",))

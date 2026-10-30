"""Exact event images and probability transport on explicitly named finite carriers.

Inverse images preserve Boolean event operations for every map. Direct images
can lose intersections under coarsening; full-codomain complements additionally
depend on which target states are reached. These methods implement finite set
operations, not an interpretation or preservation theorem for SUMO sentences.
"""

from dataclasses import dataclass
from fractions import Fraction

from rikishi.finite_channels import FiniteChannel, FiniteChannelError, Law, apply_channel

type Event = frozenset[str]


class EventTransportError(FiniteChannelError):
    """A carrier, map or event lies outside the declared finite contract."""


def _carrier(values: tuple[str, ...], label: str) -> None:
    if type(values) is not tuple or not values:
        raise EventTransportError(f"{label} must be a nonempty immutable tuple")
    if any(type(value) is not str or not value or value.strip() != value for value in values):
        raise EventTransportError(f"{label} identities must be nonblank trimmed strings")
    if len(set(values)) != len(values):
        raise EventTransportError(f"{label} identities must be unique")


def _event(event: Event, carrier: tuple[str, ...]) -> None:
    if type(event) is not frozenset:
        raise EventTransportError("event must be an immutable frozenset")
    if any(type(state) is not str for state in event) or not event <= frozenset(carrier):
        raise EventTransportError("event contains an identity outside its declared carrier")


@dataclass(frozen=True, slots=True)
class FiniteStateMap:
    """A total deterministic map; ``images[i]`` is the image of ``source[i]``.

    The target may contain unreachable states. Events are relative to their
    explicit source or target carrier; no strings, sets or numbers are coerced.
    Probability vectors follow the declared carrier orders.
    """

    source: tuple[str, ...]
    target: tuple[str, ...]
    images: tuple[str, ...]

    def __post_init__(self) -> None:
        _carrier(self.source, "source")
        _carrier(self.target, "target")
        if type(self.images) is not tuple or len(self.images) != len(self.source):
            raise EventTransportError("images must supply exactly one immutable entry per source")
        if any(type(image) is not str or image not in self.target for image in self.images):
            raise EventTransportError("every map image must name a declared target state")

    @property
    def is_injective(self) -> bool:
        return len(set(self.images)) == len(self.images)

    @property
    def is_surjective(self) -> bool:
        return frozenset(self.images) == frozenset(self.target)

    def direct_image(self, event: Event) -> Event:
        """Collect target states reached by an admitted source event."""
        _event(event, self.source)
        return frozenset(image for state, image in zip(self.source, self.images, strict=True)
                         if state in event)

    def inverse_image(self, event: Event) -> Event:
        """Select every source state whose image belongs to an admitted target event."""
        _event(event, self.target)
        return frozenset(state for state, image in zip(self.source, self.images, strict=True)
                         if image in event)

    def pushforward(self, law: Law) -> Law:
        """Transport exact normalized mass; unused target states receive zero mass."""
        channel = FiniteChannel("finite-event-map", tuple(
            tuple(Fraction(int(image == target)) for target in self.target)
            for image in self.images))
        return apply_channel(law, channel)

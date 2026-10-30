"""Exact mixed-history examples and a source-bound, fully labeled sequence atlas."""

from __future__ import annotations

from fractions import Fraction
from itertools import product
from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal

from defusedxml import ElementTree
from pydantic import Field

from rikishi.bridge_figures import _check_geometry
from rikishi.bridge_models import FiniteWitness
from rikishi.finite_channels import FiniteChannel, FiniteChannelError
from rikishi.inference_models import Frozen
from rikishi.witness_sequences import SequenceModel, compare_sequence_models, condition_sequence

if TYPE_CHECKING:
    from matplotlib.figure import Figure

_IDS: Final = ("uniform-prior", "biased-prior", "exact-candidate")
_LABELS: Final = ("U", "B", "E")
_SCOPE: Final = "Derived mixed-sequence arithmetic; no new Lean or native SUMO results"


class SequenceAtlasRow(Frozen):
    witness_id: str
    pattern: str
    evidence: str
    posterior_false: str
    next_true: str
    redrawn_evidence: str


class SequenceAtlas(Frozen):
    schema_version: Literal[1] = 1
    report_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    scope: Literal["Derived mixed-sequence arithmetic; no new Lean or native SUMO results"] = _SCOPE
    patterns: tuple[str, ...]
    source_witnesses: tuple[FiniteWitness, ...]
    rows: tuple[SequenceAtlasRow, ...]
    biased_model_weights: tuple[str, ...]


def build_sequence_atlas(witnesses: tuple[FiniteWitness, ...], report_sha256: str) -> SequenceAtlas:
    """Enumerate every length-three history of the three caller-validated witnesses."""
    if tuple(witness.id for witness in witnesses) != _IDS:
        raise FiniteChannelError("Sequence atlas requires the three registered witnesses in order")
    sequences = tuple(product((False, True), repeat=3))
    patterns = tuple("".join("T" if value else "F" for value in path) for path in sequences)
    models = tuple(SequenceModel(
        witness.id, tuple(map(Fraction, witness.prior)),
        FiniteChannel(witness.id, tuple((1 - ell, ell) for ell in map(Fraction, witness.likelihood))),
    ) for witness in witnesses)
    rows: list[SequenceAtlasRow] = []
    for model in models:
        for path, pattern in zip(sequences, patterns, strict=True):
            result = condition_sequence(model.prior, model.kernel, path)
            final = result.steps[-1]
            rows.append(SequenceAtlasRow(
                witness_id=model.name, pattern=pattern,
                evidence=str(final.cumulative_evidence),
                posterior_false=str(final.posterior[0]), next_true=str(final.next_predictive[1]),
                redrawn_evidence=str(result.redrawn_evidence),
            ))
    weights = tuple(str(compare_sequence_models(models[:2], path).posterior[1])
                    for path in sequences)
    return SequenceAtlas(report_sha256=report_sha256, patterns=patterns,
                         source_witnesses=witnesses, rows=tuple(rows),
                         biased_model_weights=weights)


def verify_sequence_atlas(raw: bytes, witnesses: tuple[FiniteWitness, ...],
                          report_sha256: str) -> None:
    """Recompute exact values and their source binding, not merely a payload checksum."""
    actual = SequenceAtlas.model_validate_json(raw)
    if actual != build_sequence_atlas(witnesses, report_sha256):
        raise FiniteChannelError("Sequence atlas differs from source-bound exact histories")


def sequence_atlas_table(data: SequenceAtlas) -> str:
    """Render one mixed-history checkpoint without copying values into manuscript prose."""
    lines = ["| Witness | P(TTF) | P(false state given TTF) | P(next true given TTF) | Redrawn-state P(TTF) |",
             "| --- | ---: | ---: | ---: | ---: |"]
    for row in data.rows:
        if row.pattern == "TTF":
            lines.append(f"| {row.witness_id} | {row.evidence} | {row.posterior_false} | "
                         f"{row.next_true} | {row.redrawn_evidence} |")
    return "\n".join(lines)


def verify_sequence_atlas_svg(raw: bytes, data: SequenceAtlas) -> None:
    """Bind each actual vector cell to its named model, history and numerical role."""
    expected = {
        f"sequence-cell-{field}-{row.witness_id}-{row.pattern}": value
        for row in data.rows
        for field, value in (("evidence", row.evidence),
                             ("posterior_false", row.posterior_false), ("next_true", row.next_true))
    }
    expected.update({f"sequence-cell-model-weight-{pattern}": weight
                     for pattern, weight in zip(data.patterns, data.biased_model_weights, strict=True)})
    root = ElementTree.fromstring(raw)
    cells = [node for node in root.iter()
             if node.attrib.get("id", "").startswith("sequence-cell-")]
    observed: dict[str, str] = {}
    for node in cells:
        identifier = node.attrib["id"]
        labels = list(node.iter("{http://www.w3.org/2000/svg}text"))
        if identifier in observed or len(labels) != 1:
            raise FiniteChannelError("Sequence atlas plotted cell identity is ambiguous")
        observed[identifier] = "".join(labels[0].itertext()).strip()
    if observed != expected:
        raise FiniteChannelError("Sequence atlas plotted values differ from exact model/history cells")


def _draw_atlas(data: SequenceAtlas) -> Figure:
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    figure = Figure(figsize=(191.9 / 25.4, 205 / 25.4), facecolor="white")
    FigureCanvasAgg(figure)
    figure.text(.055, .975, "What changes when an observation is false?",
                fontsize=14, weight="bold", va="top", color="#193449")
    figure.text(.055, .932,
                "All eight ordered histories, the same three rational models, exact answers.\n"
                "T = observed true; F = observed false. One hidden state persists for the whole history.",
                fontsize=9.2, va="top", linespacing=1.45)
    panels = (
        (.85, "A  Probability of the complete history", "evidence"),
        (.66, "B  Posterior probability of the false hidden state", "posterior_false"),
        (.47, "C  Probability that the next observation is true", "next_true"),
    )
    for top, title, field in panels:
        figure.text(.055, top, title, fontsize=10.5, weight="bold", va="top", color="#193449")
        for column, pattern in enumerate(data.patterns):
            x = .19 + column * .103
            figure.text(x, top - .045, pattern, fontsize=9, weight="bold", ha="center", va="top")
            for index, (witness_id, label) in enumerate(zip(_IDS, _LABELS, strict=True)):
                row = next(item for item in data.rows
                           if item.witness_id == witness_id and item.pattern == pattern)
                y = top - .082 - index * .032
                if column == 0:
                    figure.text(.08, y, label, fontsize=9.5, weight="bold", ha="center", va="top")
                value = getattr(row, field)
                figure.text(x, y, value, fontsize=9, ha="center", va="top",
                            color="#176b62" if index == 0 else "#193449",
                            gid=f"sequence-cell-{field}-{witness_id}-{pattern}")
    figure.text(.055, .275, "D  Model probability: B versus U, equal prior model weights",
                fontsize=10.5, weight="bold", va="top", color="#193449")
    for column, (pattern, weight) in enumerate(zip(data.patterns, data.biased_model_weights, strict=True)):
        x = .19 + column * .103
        figure.text(x, .23, pattern, fontsize=9, weight="bold", ha="center", va="top")
        figure.text(x, .192, weight, fontsize=9, ha="center", va="top", color="#176b62",
                    gid=f"sequence-cell-model-weight-{pattern}")
    figure.text(.055, .13,
                "U = uniform-prior; B = biased-prior; E = exact-candidate (excluded from D).\n"
                "Histories with the same T/F counts have equal final answers in this fixed-state model.\n"
                "Their intermediate updates can differ. Redrawing a state defines a different model.\n"
                "Exact laws, source inputs and redrawn controls: witness-sequences.json\n"
                "Derived mathematics, not empirical data or a new Lean/SUMO proof. Packet "
                + data.report_sha256[:12], fontsize=9, va="top", linespacing=1.45)
    return figure


def render_sequence_atlas(data: SequenceAtlas, directory: Path) -> tuple[Path, ...]:
    """Export actual vector/raster figures and exact source data without overwriting."""
    import matplotlib

    targets = tuple(directory / name for name in (
        "witness-sequences.png", "witness-sequences.svg", "witness-sequences.json"))
    if any(path.exists() or path.is_symlink() for path in targets):
        raise FileExistsError("Sequence atlas export requires unused target paths")
    directory.mkdir(parents=True, exist_ok=True)
    with matplotlib.rc_context({"font.family": "DejaVu Sans", "font.size": 9,
                                "text.usetex": False, "text.parse_math": False,
                                "svg.fonttype": "none", "svg.hashsalt": data.report_sha256}):
        figure = _draw_atlas(data)
        _check_geometry(figure)
        for path in targets[:2]:
            metadata: dict[str, str | None] = {
                "Description": data.scope + "; bridge packet SHA-256 " + data.report_sha256}
            if path.suffix == ".svg":
                metadata["Date"] = None
            figure.savefig(path, dpi=300, metadata=metadata)
        figure.clear()
    verify_sequence_atlas_svg(targets[1].read_bytes(), data)
    with targets[-1].open("x", encoding="utf-8") as stream:
        stream.write(data.model_dump_json(indent=2) + "\n")
    return targets

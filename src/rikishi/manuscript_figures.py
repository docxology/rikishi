from __future__ import annotations

import json
import math
import textwrap
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from rikishi.fep import DemoResult, EnergyResult, ScanPoint, free_energy
from rikishi.graph_types import Neighborhood
from rikishi.manuscript_provenance import CorpusMeasurement

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

_NAVY: Final = "#193449"
_TEAL: Final = "#176b62"
_COPPER: Final = "#a35e38"
_IVORY: Final = "#faf8f2"
_MUTED: Final = "#536570"
_GRID: Final = "#dce4e5"


@dataclass(frozen=True, slots=True)
class FigureDataError(ValueError):
    reason: str

    def __str__(self) -> str:
        return self.reason


class _Example(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, allow_inf_nan=False)
    units: Literal["nats"]
    prior: list[float]
    likelihood: list[float]
    candidate: list[float]
    result: EnergyResult
    optimum: EnergyResult
    scan: list[ScanPoint] = Field(min_length=2)
    state_labels: list[str] = Field(default_factory=lambda: ["state 0", "state 1"])
    scan_points: int | None = None


def _check_energy(actual: EnergyResult, expected: EnergyResult) -> None:
    for key in ("evidence", "surprise", "free_energy", "kl_to_posterior", "identity_residual"):
        if not math.isclose(actual[key], expected[key], rel_tol=1e-10, abs_tol=1e-12):
            raise FigureDataError(f"Model/result mismatch: {key}")
    if len(actual["exact_posterior"]) != len(expected["exact_posterior"]) or any(
        not math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-12)
        for a, b in zip(actual["exact_posterior"], expected["exact_posterior"])
    ):
        raise FigureDataError("Model/result mismatch: exact posterior")


def _validate_example(example: DemoResult) -> _Example:
    checked = _Example.model_validate(example)
    if any(len(vector) != 2 for vector in (checked.prior, checked.likelihood, checked.candidate)):
        raise FigureDataError("The FEP figure requires a binary model")
    if (
        len(checked.state_labels) != 2
        or len(set(checked.state_labels)) != 2
        or any(
            not name.strip() or len(name) > 28 or not name.isprintable()
            for name in checked.state_labels
        )
    ):
        raise FigureDataError(
            "Two distinct, printable state labels of at most 28 characters required"
        )
    result = free_energy(checked.prior, checked.likelihood, checked.candidate)
    _check_energy(checked.result, result)
    _check_energy(
        checked.optimum, free_energy(checked.prior, checked.likelihood, result["exact_posterior"])
    )
    if checked.scan_points is not None and checked.scan_points != len(checked.scan):
        raise FigureDataError("Configured scan count differs from supplied scan")
    for index, point in enumerate(checked.scan):
        q = point["q_state_zero"]
        if not math.isclose(q, index / (len(checked.scan) - 1), rel_tol=0, abs_tol=1e-12):
            raise FigureDataError("FEP scan must be a complete ordered inclusive uniform grid")
        energy = free_energy(checked.prior, checked.likelihood, [q, 1 - q])["free_energy"]
        if not math.isclose(point["free_energy"], energy, rel_tol=1e-10, abs_tol=1e-12):
            raise FigureDataError("Model/scan free energy mismatch")
    return checked


def _validate_taxonomy(taxonomy: Neighborhood, corpus: CorpusMeasurement) -> Neighborhood:
    graph = TypeAdapter(Neighborhood).validate_python(taxonomy, strict=True)
    edges, nodes = graph["edges"], graph["nodes"]
    if (
        graph["truncated"]
        or not edges
        or not (graph["total_edges"] == graph["returned_edges"] == len(edges))
    ):
        raise FigureDataError("A complete, nonempty Entity subclass neighborhood is required")
    ids = {node["id"] for node in nodes}
    triples = {(edge["source"], edge["relation"], edge["target"]) for edge in edges}
    if len(ids) != len(nodes) or len(triples) != len(edges) or "Entity" not in ids:
        raise FigureDataError("Taxonomy contains duplicate nodes/edges or lacks Entity")
    if any(
        edge["relation"] != "subclass"
        or edge["target"] != "Entity"
        or edge["source"] == "Entity"
        or edge["source"] not in ids
        for edge in edges
    ) or ids != {"Entity", *(edge["source"] for edge in edges)}:
        raise FigureDataError("Taxonomy must contain exactly the direct child -> Entity assertions")
    inventory = graph["relations"]
    if (
        len({row["relation"] for row in inventory}) != len(inventory)
        or any(row["count"] <= 0 for row in inventory)
        or next((row["count"] for row in inventory if row["relation"] == "subclass"), 0)
        != len(edges)
    ):
        raise FigureDataError("Subclass inventory disagrees with the complete taxonomy")
    if len(edges) > 7 or any(
        not node["id"].strip()
        or not node["label"].strip()
        or len(node["label"]) > 28
        or not node["label"].isprintable()
        for node in nodes
    ):
        raise FigureDataError(
            "Cover layout supports at most seven children and 28-character labels"
        )
    if corpus.terms < len(nodes) or corpus.edges < sum(row["count"] for row in inventory):
        raise FigureDataError("Corpus counts cannot contain the supplied taxonomy")
    return graph


def _vector(values: Sequence[float], places: int) -> str:
    return "[" + ", ".join(f"{value:.{places}f}" for value in values) + "]"


def _energy_axes(ax: Axes, example: _Example, places: int) -> None:
    posterior = example.result["exact_posterior"][0]
    coordinates = [p["q_state_zero"] for p in example.scan]
    energies = [p["free_energy"] for p in example.scan]
    surprise = example.result["surprise"]
    ax.fill_between(coordinates, surprise, energies, color=_TEAL, alpha=0.10)
    ax.plot(
        coordinates,
        energies,
        color=_NAVY,
        linewidth=2.2,
        label="Free energy F(q)",
    )
    ax.axhline(
        surprise,
        color=_COPPER,
        linestyle="--",
        linewidth=1.4,
        label="Surprise -log p(o)",
    )
    ax.scatter(
        [posterior],
        [example.optimum["free_energy"]],
        color=_TEAL,
        edgecolors="white",
        linewidths=0.8,
        s=48,
        zorder=4,
        label=f"Analytical q* = {posterior:.{places}f}",
    )
    ax.scatter(
        [example.candidate[0]],
        [example.result["free_energy"]],
        color=_COPPER,
        marker="D",
        s=32,
        edgecolors="white",
        linewidths=0.6,
        zorder=5,
        label="Supplied candidate q",
    )
    ax.axvline(posterior, color=_TEAL, linewidth=0.8, alpha=0.5)
    span = max(energies) - surprise
    padding = max(span * 0.12, abs(surprise) * 0.04, 0.01)
    ax.set(
        xlim=(0, 1),
        ylim=(surprise - padding, max(energies) + padding),
        xlabel=f"q({example.state_labels[0]})",
        ylabel="Free energy / nats",
        xticks=[0, 0.5, 1],
    )
    ax.xaxis.label.set_parse_math(False)
    ax.tick_params(labelsize=9)
    ax.xaxis.label.set_fontsize(9)
    ax.yaxis.label.set_fontsize(9)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_axisbelow(True)
    ax.grid(axis="y", color=_GRID, linewidth=0.6)


def _finite_model_figure(fig: Figure, example: _Example, places: int) -> None:
    fig.text(
        0.055,
        0.945,
        "Finite inference, with an explicit evidence bound",
        fontsize=15,
        weight="bold",
        color=_NAVY,
    )
    fig.text(0.055, 0.911, "Kullback-Leibler divergence (KL)", fontsize=8.5, color=_MUTED)
    fig.text(0.055, 0.875, "F(q) = KL(q || p(s|o)) − log p(o)", fontsize=12, color=_NAVY)
    fig.text(0.055, 0.838, "A  Model and beliefs", fontsize=10, weight="bold", color=_NAVY)
    fig.text(0.60, 0.838, "B  Variational objective", fontsize=10, weight="bold", color=_NAVY)
    probabilities = fig.add_axes((0.19, 0.525, 0.29, 0.27))
    vectors = [
        example.prior,
        example.likelihood,
        example.result["exact_posterior"],
        example.candidate,
    ]
    for state, color in enumerate((_NAVY, _TEAL)):
        y = [row + (state - 0.5) * 0.32 for row in range(4)]
        probabilities.barh(
            y,
            [values[state] for values in vectors],
            height=0.28,
            color=color,
            label=textwrap.fill(example.state_labels[state], 23),
            hatch="///" if state else None,
            edgecolor="white",
            linewidth=0.4,
        )
    probabilities.set(
        yticks=range(4),
        yticklabels=["Prior p(s)", "p(o|s)", "Posterior", "Candidate q"],
        xlim=(0, 1),
        xticks=[0, 0.5, 1],
        xlabel="Probability / likelihood",
    )
    probabilities.invert_yaxis()
    probabilities.tick_params(axis="y", length=0, labelsize=9)
    probabilities.tick_params(axis="x", labelsize=9)
    probabilities.spines[["top", "right", "left"]].set_visible(False)
    probabilities.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.34),
        fontsize=8.5,
        frameon=False,
        ncol=1,
        handlelength=1.2,
    )
    objective = fig.add_axes((0.61, 0.525, 0.345, 0.27))
    _energy_axes(objective, example, places)
    fig.text(
        0.61,
        0.405,
        f"Analytical q* = {example.result['exact_posterior'][0]:.{places}f}",
        fontsize=9,
        color=_TEAL,
    )
    fig.text(0.61, 0.37, "● posterior optimum   ◆ candidate", fontsize=8.5, color=_MUTED)
    fig.text(
        0.055, 0.296, "C  Bound + posterior divergence", fontsize=10, weight="bold", color=_NAVY
    )
    decomposition = fig.add_axes((0.22, 0.13, 0.73, 0.115))
    surprise = example.result["surprise"]
    results = [example.result, example.optimum]
    decomposition.barh([1, 0], [surprise, surprise], color=_TEAL, height=0.5)
    decomposition.barh(
        [1, 0],
        [r["kl_to_posterior"] for r in results],
        left=[surprise, surprise],
        color=_COPPER,
        height=0.5,
    )
    maximum = max(r["free_energy"] for r in results)
    for y, result in zip([1, 0], results):
        decomposition.text(
            result["free_energy"] + max(maximum * 0.025, 0.005),
            y,
            f"F = {result['free_energy']:.{places}f}",
            va="center",
            fontsize=9,
            color=_NAVY,
        )
    decomposition.set(
        yticks=[1, 0],
        yticklabels=["Candidate q", "Posterior q*"],
        xlim=(0, max(maximum * 1.7, 0.1)),
        xlabel="nats",
    )
    decomposition.tick_params(labelsize=9)
    decomposition.spines[["top", "right", "left"]].set_visible(False)
    fig.text(0.55, 0.296, "■ surprise", fontsize=9, color=_TEAL)
    fig.text(0.77, 0.296, "■ KL gap", fontsize=9, color=_COPPER)
    fig.text(
        0.055,
        0.035,
        f"p(o) = {example.result['evidence']:.{places}f}  ·  "
        f"KL(q || p(s|o)) = {example.result['kl_to_posterior']:.{places}f} nats",
        fontsize=9,
        color=_MUTED,
    )


def _cover(
    fig: Figure, example: _Example, corpus: CorpusMeasurement, graph: Neighborhood, places: int
) -> None:
    from matplotlib.backends.backend_agg import RendererAgg
    from matplotlib.font_manager import FontProperties
    from matplotlib.patches import FancyArrowPatch, Rectangle

    fig.text(0.045, 0.927, "SUMO", fontsize=34, weight="bold", color=_NAVY)
    fig.text(0.35, 0.957, "Suggested Upper Merged Ontology", fontsize=12, color=_NAVY)
    fig.text(0.35, 0.914, "Source → structure → bounded evidence", fontsize=11, color=_TEAL)
    fig.text(
        0.045,
        0.858,
        f"{corpus.files:,} files  ·  {corpus.formulas:,} formulas  ·  "
        f"{corpus.terms:,} terms  ·  {corpus.edges:,} edge assertions",
        fontsize=9.5,
        color=_NAVY,
    )
    fig.text(
        0.045, 0.817, "01  DIRECT SUBCLASS ASSERTIONS", fontsize=10, weight="bold", color=_TEAL
    )
    hierarchy = fig.add_axes((0.045, 0.54, 0.91, 0.26))
    hierarchy.set(xlim=(0, 1), ylim=(0, 1))
    hierarchy.axis("off")
    labels = {node["id"]: node["label"] for node in graph["nodes"]}
    children = sorted(edge["source"] for edge in graph["edges"])
    renderer = RendererAgg(1, 1, 72)
    font = FontProperties(size=9.5)
    available_width = fig.get_figwidth() * 72 * 0.91 / len(children) - 12
    node_texts = []
    for index, child in enumerate(children):
        x = (index + 0.5) / len(children)
        wrapped = labels[child]
        for width in range(len(wrapped), 0, -1):
            wrapped = textwrap.fill(labels[child], width=width)
            if all(
                renderer.get_text_width_height_descent(line, font, False)[0] <= available_width
                for line in wrapped.splitlines()
            ):
                break
        node = hierarchy.text(
            x,
            0.21,
            wrapped,
            ha="center",
            va="center",
            fontsize=9.5,
            color=_NAVY,
            parse_math=False,
            bbox={"boxstyle": "round,pad=0.45", "fc": _IVORY, "ec": _GRID},
        )
        node_texts.append(node)
    axis_height = fig.get_figheight() * 72 * 0.26
    heights = [node.get_window_extent(renderer).height + 2 * 0.45 * 9.5 for node in node_texts]
    child_y = max(0.21, (max(heights) / 2 + 4) / axis_height)
    for index, (node, height) in enumerate(zip(node_texts, heights)):
        node.set_y(child_y)
        edge = FancyArrowPatch(
            (node.get_position()[0], child_y + height / (2 * axis_height)),
            (0.5, 0.72),
            arrowstyle="-|>",
            mutation_scale=11,
            color=_COPPER,
            linewidth=1.5,
        )
        edge.set_gid(f"subclass-edge-{index}")
        hierarchy.add_patch(edge)
    hierarchy.text(
        0.5,
        0.83,
        labels["Entity"],
        ha="center",
        va="center",
        fontsize=13,
        color="white",
        parse_math=False,
        bbox={"boxstyle": "round,pad=0.4", "fc": _NAVY, "ec": _NAVY},
    )
    fig.text(
        0.045,
        0.522,
        "Arrows: child → Entity. Complete direct neighborhood; no inferred closure.",
        fontsize=9,
        color=_MUTED,
    )
    boundary = Rectangle(
        (0.045, 0.345),
        0.91,
        0.142,
        transform=fig.transFigure,
        facecolor=_IVORY,
        edgecolor=_GRID,
        linewidth=1,
        zorder=-1,
    )
    fig.add_artist(boundary)
    fig.text(0.063, 0.457, "02  RIKISHI OPERATOR BOUNDARY", fontsize=10, weight="bold", color=_TEAL)
    workflow = fig.add_axes((0.063, 0.355, 0.875, 0.082))
    workflow.axis("off")
    for x, title, detail in (
        (0.13, "Source + query", "Selected premises"),
        (0.50, "Translation", "Explicit problem"),
        (0.87, "Automated theorem\nproving", "E · Vampire"),
    ):
        workflow.text(
            x,
            0.5,
            f"{title}\n{detail}",
            ha="center",
            va="center",
            fontsize=10,
            color=_NAVY,
            linespacing=1.6,
        )
    for start, end in ((0.27, 0.35), (0.65, 0.73)):
        workflow.annotate(
            "",
            xy=(end, 0.5),
            xytext=(start, 0.5),
            arrowprops={"arrowstyle": "-|>", "color": _COPPER, "lw": 1.4},
        )
    fig.text(
        0.045, 0.315, "03  FINITE VARIATIONAL EXAMPLE", fontsize=10, weight="bold", color=_TEAL
    )
    fig.text(0.045, 0.285, "Kullback-Leibler divergence (KL)", fontsize=8, color=_MUTED)
    fig.text(0.045, 0.255, "F(q) = KL(q || p(s|o)) − log p(o)", fontsize=11, color=_NAVY)
    for y, name, values in (
        (0.221, "p(s)", example.prior),
        (0.183, "p(o|s)", example.likelihood),
        (0.145, "q(s)", example.candidate),
    ):
        fig.text(0.045, y, f"{name} = {_vector(values, places)}", fontsize=9, color=_NAVY)
    ax = fig.add_axes((0.64, 0.185, 0.31, 0.135))
    _energy_axes(ax, example, places)
    fig.text(
        0.57,
        0.104,
        f"Analytical q* = {example.result['exact_posterior'][0]:.{places}f}",
        fontsize=9,
        color=_TEAL,
    )
    fig.text(
        0.045,
        0.104,
        f"Surprise bound = {example.result['surprise']:.{places}f} nats",
        fontsize=9,
        color=_COPPER,
    )
    fig.text(
        0.045,
        0.055,
        f"SUMO revision {corpus.source_commit[:12]}  ·  exact inputs: graphical-abstract.json",
        fontsize=8.5,
        color=_MUTED,
    )
    fig.text(
        0.045,
        0.021,
        "Finite calculation only; no SUMO–Lean equivalence or proof transport is asserted.",
        fontsize=8.5,
        color=_MUTED,
    )


def render_manuscript_figures(
    output: Path,
    example: DemoResult,
    corpus: CorpusMeasurement,
    taxonomy: Neighborhood,
    *,
    dpi: int,
    decimal_places: int,
) -> list[Path]:
    """Write the FEP PNG, cover PNG/SVG and exact-input JSON into ``output``.

    The caller supplies a complete, subclass-filtered Entity neighborhood from
    the same index as ``corpus``. Neighborhood has no revision field: identity
    binding to that index remains the caller's responsibility. Invalid evidence
    is rejected before any output directory or plot is created. Layout capacity
    is explicit; classes are never silently dropped to fit the cover.
    """
    if type(dpi) is not int or dpi < 72 or dpi > 1200:
        raise FigureDataError("Figure dpi must be an integer between 72 and 1200")
    if type(decimal_places) is not int or not 0 <= decimal_places <= 9:
        raise FigureDataError("Figure decimal_places must be an integer between zero and nine")
    checked = _validate_example(example)
    measured = CorpusMeasurement.model_validate(corpus.model_dump())
    if (
        not measured.source_clean
        or measured.parse_errors
        or measured.formulas <= 0
        or (measured.edges > measured.formulas)
    ):
        raise FigureDataError("Figures require a clean, nonempty corpus with consistent counts")
    graph = _validate_taxonomy(taxonomy, measured)
    payload = (
        json.dumps(
            {
                "example": example,
                "corpus": measured.model_dump(),
                "taxonomy": graph,
                "rendering": {"dpi": dpi, "decimal_places": decimal_places},
                "scope": "Selected direct subclass assertions; finite FEP illustration. "
                "No SUMO-Lean equivalence or ATP execution is asserted.",
            },
            indent=2,
            allow_nan=False,
        )
        + "\n"
    )
    import matplotlib
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    output.mkdir(parents=True, exist_ok=True)
    paths = [
        output / name
        for name in (
            "fep-free-energy.png",
            "graphical-abstract.png",
            "graphical-abstract.svg",
            "graphical-abstract.json",
        )
    ]
    with matplotlib.rc_context(
        {
            "font.family": "DejaVu Sans",
            "text.usetex": False,
            "text.parse_math": False,
            "svg.fonttype": "none",
            "axes.labelcolor": _NAVY,
            "xtick.color": _MUTED,
            "ytick.color": _MUTED,
            "axes.edgecolor": "#b1babc",
        }
    ):
        energy = Figure(figsize=(7.2, 5.8), facecolor="white")
        FigureCanvasAgg(energy)
        try:
            _finite_model_figure(energy, checked, decimal_places)
            energy.savefig(paths[0], dpi=dpi)
        finally:
            energy.clear()
        cover = Figure(figsize=(7.2, 6.4), facecolor="white")
        FigureCanvasAgg(cover)
        try:
            _cover(cover, checked, measured, graph, decimal_places)
            cover.savefig(paths[1], dpi=dpi)
            cover.savefig(paths[2])
        finally:
            cover.clear()
    paths[3].write_text(payload, encoding="utf-8")
    return paths

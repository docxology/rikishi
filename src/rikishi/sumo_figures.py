"""Print-scale SUMO source inspection, with portable exact-input provenance."""

from __future__ import annotations

import json
import textwrap
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING, Final

from rikishi.kif import parse
from rikishi.sumo_demonstrations import FormulaCitation, SumoReport, validate_sumo_report

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

_NAVY: Final = "#193449"
_TEAL: Final = "#176b62"
_COPPER: Final = "#a35e38"
_MUTED: Final = "#536570"
_WIDTH_MM: Final = 174
_HEIGHT_MM: Final = 190


@dataclass(frozen=True, slots=True)
class SumoFigureError(ValueError):
    reason: str

    def __str__(self) -> str:
        return self.reason


def _atoms(citation: FormulaCitation) -> tuple[str, ...]:
    return tuple(str(atom) for atom in next(parse(citation.raw_kif)).expression)


def _citation(citations: list[FormulaCitation], source_name: str) -> str:
    lines = ", ".join(
        str(c.line) if c.line == c.end_line else f"{c.line}-{c.end_line}" for c in citations
    )
    return f"{source_name}: {lines}"


def _panel(fig: Figure, bounds: tuple[float, float, float, float], title: str,
           color: str) -> Axes:
    ax = fig.add_axes(bounds)
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.set_axis_off()
    ax.axhline(1, color=color, lw=2.4, clip_on=False)
    ax.text(0, 0.96, title, va="top", fontsize=9.4, weight="bold", color=color)
    return ax


def _node(ax: Axes, x: float, y: float, label: str, color: str, *, size: float = 8.2) -> None:
    ax.text(x, y, label, ha="center", va="center", fontsize=size, color=color,
            bbox={"boxstyle": "square,pad=0.34", "fc": "white", "ec": color, "lw": 0.8},
            zorder=3)


def _arrow(ax: Axes, start: tuple[float, float], end: tuple[float, float], color: str,
           gid: str, *, dashed: bool = False) -> None:
    annotation = ax.annotate("", xy=end, xytext=start,
                             arrowprops={"arrowstyle": "-|>", "color": color, "lw": 1.0,
                                         "linestyle": "--" if dashed else "-"})
    assert annotation.arrow_patch is not None
    annotation.arrow_patch.set_gid(gid)


def _hierarchy(ax: Axes, report: SumoReport) -> None:
    citations = report.cases["hierarchy"]
    partition = next(c for c in citations if c.predicate == "partition")
    _, parent, left, right = _atoms(partition)
    edges = [_atoms(c) for c in citations if c.predicate == "subclass"]
    positions = {parent: (0.50, 0.79), left: (0.24, 0.57), right: (0.77, 0.57)}
    for _, child, superclass in edges:
        if child not in positions:
            positions[child] = (positions[superclass][0], 0.33)
    for _, child, superclass in edges:
        x, y = positions[child]
        px, py = positions[superclass]
        _arrow(ax, (x, y + 0.055), (px, py - 0.055), _NAVY,
               f"subclass-{child}-to-{superclass}")
    for label, (x, y) in positions.items():
        _node(ax, x, y, label, _NAVY)
    ax.text(0.50, 0.445, "subclass", ha="center", fontsize=7.8, color=_NAVY)
    ax.text(0.50, 0.68, "subclass", ha="center", fontsize=7.8, color=_NAVY)
    ax.text(0, 0.19, "Source constraint (separate from the arrows)", fontsize=7.5, color=_MUTED)
    ax.text(0, 0.12, partition.raw_kif, fontsize=8, color=_NAVY, family="DejaVu Sans Mono")
    ax.text(0, 0.035, "Child → parent; only the selected subclass assertions.",
            fontsize=7.5, color=_MUTED)
    ax.text(0, -0.03, textwrap.fill(_citation(citations, report.source.ontology_path), 48),
            fontsize=8, color=_MUTED, va="top")


def _signatures(ax: Axes, report: SumoReport) -> None:
    instance = next(c for c in report.cases["typing"] if c.predicate == "instance"
                    and _atoms(c)[1] == _atoms(report.cases["agent_signature"][0])[1])
    probability = report.cases["probability_signature"]
    for top, classification, constraints in (
        (0.79, instance, report.cases["agent_signature"]),
        (0.37, probability[0], probability[1:]),
    ):
        relation, term, category = _atoms(classification)
        _node(ax, 0.23, top, term, _TEAL)
        _node(ax, 0.79, top, category, _TEAL)
        _arrow(ax, (0.43, top), (0.60, top), _TEAL,
               f"instance-{term}-to-{category}", dashed=True)
        ax.text(0.515, top + 0.055, relation, ha="center", fontsize=7.6, color=_TEAL)
        for x, citation in zip((0.23, 0.79), constraints, strict=True):
            predicate, _, *arguments = _atoms(citation)
            label = " ".join((predicate, *arguments[:-1]))
            _node(ax, x, top - 0.22, arguments[-1], _NAVY, size=7.8)
            _arrow(ax, (0.23, top - 0.045), (x, top - 0.17), _NAVY,
                   f"constraint-{term}-{'-'.join(arguments)}")
            ax.text(x + (-0.13 if x < 0.5 else -0.03), top - 0.12, label,
                    fontsize=8, ha="center", color=_NAVY,
                    bbox={"fc": "white", "ec": "none", "pad": 0.8}, zorder=4)
    ax.text(0, 0.08, "Solid: argument constraints.\nDashed: instance classification.",
            fontsize=8, color=_MUTED, va="top")
    used = [instance, *report.cases["agent_signature"], *probability]
    ax.text(0, -0.03, textwrap.fill(_citation(used, report.source.ontology_path), 50),
            fontsize=8, color=_MUTED, va="top")


def _context(ax: Axes, report: SumoReport) -> None:
    citation = report.cases["nested_formula"][0]
    ax.text(0, 0.83, citation.raw_kif, va="top", fontsize=7.9, linespacing=1.35,
            family="DejaVu Sans Mono", color=_NAVY, gid="complete-modal-formula")
    ax.text(0, 0.19, _citation([citation], report.source.ontology_path),
            fontsize=8, color=_MUTED)
    ax.axvline(0.64, ymin=0.19, ymax=0.84, color="#c5cfce", lw=0.7)
    ax.text(0.69, 0.83, f"{report.source.ontology_path} inventory", fontsize=8,
            weight="bold", color=_COPPER)
    for y, count, label, name in (
        (0.68, report.observations.source_formulas, "top-level formulas", "source_formulas"),
        (0.47, report.observations.projected_binary_edges, "binary-edge projection\nassertions",
         "projected_binary_edges"),
        (0.24, report.observations.cited_formulas, "distinct cited formulas", "cited_formulas"),
    ):
        ax.text(0.69, y, f"{count:,}", fontsize=17, color=_COPPER, weight="bold",
                gid=f"inventory-{name}")
        ax.text(0.69, y - 0.045, label, va="top", fontsize=7.7, color=_NAVY)
    ax.text(0, 0.08, "Implication, quantification and modality remain in their source context.",
            fontsize=8, color=_NAVY)
    ax.text(0, 0, "Source inspection + restricted projection; no full-SUMO proof or consistency claim.",
            fontsize=7.7, color=_COPPER)


def render_sumo_system(output: Path, report: SumoReport, *, dpi: int) -> list[Path]:
    """Write ``sumo-system.png``, ``.svg`` and an exact-input ``.json`` receipt.

    Replay is pure: no index, source checkout, subprocess or ATP execution is needed.
    Invalid reports, DPI outside 72..1200, and excerpts exceeding the print layout's
    capacity are rejected before creating output. The complete modal excerpt is
    never shortened. Width is 174 mm; text stays vector text in the SVG.
    """
    if type(dpi) is not int or not 72 <= dpi <= 1200:
        raise SumoFigureError("Figure dpi must be an integer between 72 and 1200")
    checked = validate_sumo_report(report)
    nested = checked.cases["nested_formula"][0].raw_kif
    if len(nested.splitlines()) > 10 or max(map(len, nested.splitlines())) > 50:
        raise SumoFigureError("Complete modal excerpt exceeds the 10-line, 50-column print layout")
    if len(checked.source.path) > 90:
        raise SumoFigureError("Source path exceeds the print layout")
    serialized = checked.model_dump_json()
    digest = sha256(serialized.encode("utf-8")).hexdigest()
    payload = json.dumps({"report": checked.model_dump(), "rendering": {
        "dpi": dpi, "width_mm": _WIDTH_MM, "height_mm": _HEIGHT_MM,
    }}, indent=2, allow_nan=False) + "\n"

    import matplotlib
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    with matplotlib.rc_context({"font.family": "DejaVu Sans", "text.usetex": False,
                                "text.parse_math": False, "svg.fonttype": "none",
                                "svg.hashsalt": digest}):
        fig = Figure(figsize=(_WIDTH_MM / 25.4, _HEIGHT_MM / 25.4), facecolor="white")
        FigureCanvasAgg(fig)
        fig.text(0.045, 0.965, "SUMO: source commitments and context", fontsize=13.2,
                 color=_NAVY, weight="bold")
        fig.text(0.045, 0.932, "Selected assertions from the retained source; arrows retain their relation labels.",
                 fontsize=8.1, color=_MUTED)
        _hierarchy(_panel(fig, (0.045, 0.51, 0.425, 0.375), "A  Class hierarchy", _NAVY), checked)
        _signatures(_panel(fig, (0.52, 0.51, 0.435, 0.375), "B  Signatures and classification", _TEAL), checked)
        _context(_panel(fig, (0.045, 0.16, 0.91, 0.30), "C  Modal source and projection boundary", _COPPER), checked)
        footer = (f"Source: {checked.source.path}\n"
                  f"Recorded revision: {checked.source.commit}\n"
                  f"SHA-256: {checked.source.sha256}\n"
                  "Portable replay checks retained bytes, not Git authenticity. Exact inputs: sumo-system.json")
        fig.text(0.045, 0.115, footer, va="top", fontsize=8, color=_MUTED, linespacing=1.5,
                 family="DejaVu Sans Mono")
        output.mkdir(parents=True, exist_ok=True)
        paths = [output / f"sumo-system.{suffix}" for suffix in ("png", "svg", "json")]
        description = f"{checked.scope} Report SHA-256: {digest}"
        fig.savefig(paths[0], dpi=dpi, metadata={"Title": "SUMO system", "Description": description})
        fig.savefig(paths[1], metadata={"Title": "SUMO system", "Description": description, "Date": None})
        paths[2].write_text(payload, encoding="utf-8")
        fig.clear()
    return paths

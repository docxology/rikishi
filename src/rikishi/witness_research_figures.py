"""Deterministic visual experiments for exact finite representation changes."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Final

from rikishi.bridge_figures import _check_geometry
from rikishi.witness_research import WitnessResearch

if TYPE_CHECKING:
    from matplotlib.figure import Figure

RESEARCH_FIGURES: Final = ("witness-channels", "witness-evidence-scaling")
_INK: Final = "#193449"
_TEAL: Final = "#176b62"
_BLUE: Final = "#325e85"
_COPPER: Final = "#94542f"


def _base(data: WitnessResearch, title: str, subtitle: str) -> Figure:
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    figure = Figure(figsize=(191.9 / 25.4, 185 / 25.4), facecolor="white")
    FigureCanvasAgg(figure)
    figure.text(.04, .97, title, fontsize=14, weight="bold", color=_INK, va="top")
    figure.text(.04, .915, subtitle, fontsize=10, color=_INK, va="top", linespacing=1.4)
    figure.text(.04, .025,
                "Free Energy Principle (FEP); Kullback–Leibler (KL) divergence; natural-log nats.\n"
                "Suggested Upper Merged Ontology (SUMO); derived analysis, no new Lean/SUMO proof.\n"
                "Secure Hash Algorithm 256-bit (SHA-256) packet: " + data.report_sha256[:16]
                + "\nExact inputs and 100-digit Decimal values: witness-research.json",
                fontsize=9, color=_INK, va="bottom", linespacing=1.35)
    return figure


def _channels(data: WitnessResearch) -> Figure:
    figure = _base(data, "What a representation change can erase",
                   "A shared state channel acts on both candidate q and posterior r.\n"
                   "Relabeling preserves their distinction; coarse observations can conceal it.")
    figure.text(.04, .805,
                "Exact commuting route: p′ = pT;  j′ = (pK)T;  r′ = j′/Z = rT\n"
                "Derived likelihood K′ = j′/p′ on positive coarse prior support. Evidence Z is unchanged.",
                fontsize=10, color=_TEAL, va="top", linespacing=1.4)
    axis = figure.add_axes((.13, .385, .82, .30))
    ids = ("identity", "swap-labels", "noisy-quarter", "erase-state")
    witnesses = [row.witness_id for row in data.scalings]
    for index, (witness, color, marker) in enumerate(zip(
        witnesses, (_TEAL, _BLUE, _COPPER), ("o", "s", "D"), strict=True
    )):
        rows = {row.channel_id: row for row in data.channels if row.witness_id == witness}
        x = [position + (index - 1) * .16 for position in range(4)]
        y = [float(Decimal(rows[name].kl_after)) for name in ids]
        axis.plot(x, y, marker=marker, color=color, linestyle="--" if index == 1 else "-",
                  linewidth=1.5, label=witness)
    axis.set_xticks(range(4), ("Identity", "Swap labels", "Noise 1/4", "Erase state"))
    axis.set_ylabel("KL(qT || rT) / nats", fontsize=10)
    axis.tick_params(labelsize=9)
    axis.set_ylim(bottom=-.015)
    axis.grid(axis="y", alpha=.2)
    axis.legend(fontsize=9, frameon=False)
    figure.text(.04, .285,
                "Uniform example: q = (1/2, 1/2), r = (1/4, 3/4).\n"
                "Noise gives qT = (1/2, 1/2), rT = (3/8, 5/8); KL falls, not inference error repaired.\n"
                "Erasure gives qT = rT = (1): zero coarse KL can hide a wrong fine candidate.\n"
                "Identity and state swap retain all distinctions. The exact candidate stays exact.",
                fontsize=10, color=_INK, va="top", linespacing=1.5)
    return figure


def _scaling(data: WitnessResearch) -> Figure:
    figure = _base(data, "The same posterior can carry different evidence",
                   "Replace the selected observation likelihood K(s,true) by K(s,true)/2.\n"
                   "Complete each Boolean observation row with 1 − K(s,true)/2.")
    axis = figure.add_axes((.13, .50, .82, .29))
    x = range(len(data.scalings))
    original = [float(Decimal(row.original_surprise)) for row in data.scalings]
    scaled = [float(Decimal(row.scaled_surprise)) for row in data.scalings]
    axis.bar([i - .17 for i in x], original, width=.32, color=_TEAL, label="Original observation")
    axis.bar([i + .17 for i in x], scaled, width=.32, color=_BLUE, hatch="//",
             label="Half-likelihood observation")
    axis.set_xticks(list(x), [row.witness_id for row in data.scalings])
    axis.set_ylabel("Surprise −log Z / nats", fontsize=10)
    axis.tick_params(labelsize=9)
    axis.legend(fontsize=9, frameon=False)
    axis.grid(axis="y", alpha=.2)
    figure.text(.04, .405,
                "All three exact posteriors are unchanged, while Z becomes Z/2.\n"
                "For the same q: posterior KL is unchanged; surprise and free energy rise by log 2.\n"
                "Uniform: Z 1/2 → 1/4; biased: 2/3 → 1/3; exact candidate: 7/12 → 7/24.",
                fontsize=10, color=_INK, va="top", linespacing=1.5)
    figure.text(.04, .255,
                "Provenance obligations remain separate:\n"
                "MODEL: which p, K, observation?  REPRESENTATION: which expression and interpretation?\n"
                "CALCULATION: which executed algorithm?  RESULT: which values and independent check?\n"
                "A correctly linked result can still be wrong; equal posterior does not identify a model.",
                fontsize=9.5, color=_TEAL, va="top", linespacing=1.5)
    return figure


def render_witness_research(data: WitnessResearch, output: Path) -> tuple[Path, ...]:
    """Create two publication PNG/SVG pairs and exact data without overwriting."""
    import matplotlib

    targets = [output / f"{name}.{suffix}" for name in RESEARCH_FIGURES
               for suffix in ("png", "svg")]
    targets.append(output / "witness-research.json")
    if any(path.exists() or path.is_symlink() for path in targets):
        raise FileExistsError("Witness research export requires unused target paths")
    output.mkdir(parents=True, exist_ok=True)
    description = "Derived finite witness research; bridge packet SHA-256 " + data.report_sha256
    with matplotlib.rc_context({"font.family": "DejaVu Sans", "text.usetex": False,
                                "text.parse_math": False, "svg.fonttype": "none",
                                "svg.hashsalt": data.report_sha256}):
        for name, draw in zip(RESEARCH_FIGURES, (_channels, _scaling), strict=True):
            figure = draw(data)
            _check_geometry(figure)
            for suffix in ("png", "svg"):
                metadata: dict[str, str | None] = {"Description": description}
                if suffix == "svg":
                    metadata["Date"] = None
                figure.savefig(output / f"{name}.{suffix}", dpi=300, metadata=metadata)
            figure.clear()
    with targets[-1].open("x", encoding="utf-8") as stream:
        stream.write(data.model_dump_json(indent=2) + "\n")
    return tuple(targets)

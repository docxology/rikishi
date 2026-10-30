"""Create-only publication plot of repeated evidence and a seeded model simulation."""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import TYPE_CHECKING, Final

from rikishi.bridge_figures import _check_geometry
from rikishi.witness_dynamics import WitnessDynamics

if TYPE_CHECKING:
    from matplotlib.figure import Figure

DYNAMICS_FIGURES: Final = ("witness-sequential",)
_COLORS: Final = ("#176b62", "#325e85", "#94542f")
_LABELS: Final = ("Uniform (U)", "Biased (B)", "Exact-candidate (E)")
_LINESTYLES: Final = ("-", "--", ":")
_MARKERS: Final = ("o", "s", "D")


def _draw(data: WitnessDynamics) -> Figure:
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    figure = Figure(figsize=(191.9 / 25.4, 205 / 25.4), facecolor="white")
    FigureCanvasAgg(figure)
    figure.text(.07, .97, "Repeated evidence changes state beliefs and model weights",
                fontsize=13, weight="bold", va="top", color="#193449")
    figure.text(.07, .93,
                "One persistent Boolean state; a fixed observation kernel for each model.\n"
                "Observations are independent given state/model. Condition on n true observations.",
                fontsize=9.5, va="top", linespacing=1.5)
    axes = [figure.add_axes(rect) for rect in (
        (.13, .565, .33, .255), (.64, .565, .31, .255),
        (.13, .205, .33, .255), (.64, .205, .31, .255))]
    for witness, color, label, style, marker in zip(
        data.witnesses, _COLORS, _LABELS, _LINESTYLES, _MARKERS, strict=True,
    ):
        n = [row.n for row in witness.rows]
        axes[0].plot(n, [float(Fraction(row.posterior[0])) for row in witness.rows],
                     color=color, label=label, linestyle=style, linewidth=1.8)
        axes[1].plot(n, [float(Fraction(row.next_predictive)) for row in witness.rows],
                     color=color, linestyle=style, linewidth=1.8)
        evidence = [float(Fraction(row.cumulative_evidence)) for row in witness.rows]
        observed = [float(Fraction(row.simulated_evidence)) for row in witness.rows]
        axes[2].plot(n, evidence, color=color, linestyle=style, linewidth=1.8)
        axes[2].scatter(n, observed, marker=marker, facecolors="none", edgecolors=color,
                        s=22, linewidths=.9)
    axes[0].legend(fontsize=9, frameon=False, loc="center right", handlelength=1.4)
    axes[3].plot(range(data.steps + 1), [float(Fraction(v)) for v in data.model_weights],
                 color="#325e85", marker="o", markersize=3, linewidth=1.8)
    axes[3].axhline(.5, color="#666666", linestyle=":", linewidth=1)
    axes[3].annotate("n = 1: 4/7\nn = 2: 22/37", (.08, .90), xycoords="axes fraction",
                     fontsize=9, va="top", linespacing=1.5)
    titles = ("A  Hidden-state conditioning", "B  Predicting the next observation",
              "C  Exact law and forward simulation", "D  Equal-prior model comparison")
    ylabels = ("Posterior P(state = false)", "P(next = true | n true)",
               "P(n true) · logarithmic scale", "Posterior P(model = B | n true)")
    for axis, title, ylabel in zip(axes, titles, ylabels, strict=True):
        axis.set_title(title, fontsize=9.3, loc="left", pad=10)
        axis.set_xlabel("Number n of true observations", fontsize=9)
        axis.set_ylabel(ylabel, fontsize=9)
        axis.tick_params(labelsize=9)
        axis.set_xticks((0, 3, 6, 9, 12))
        axis.set_xlim(-.3, 12.3)
        axis.grid(alpha=.2)
    axes[0].set_ylim(-.04, 1.04)
    axes[1].set_ylim(.45, .80)
    axes[2].set_yscale("log")
    axes[2].set_yticks((1, .1, .01), ("1", "0.1", "0.01"))
    axes[2].minorticks_off()
    axes[3].set_ylim(.45, 1.02)
    figure.text(.07, .105,
                "C: lines = exact calculation; open markers = simulation (65,536 trajectories/model).\n"
                "U circles, B squares, E diamonds; one state per trajectory across 12 observations.\n"
                "D compares U and B only: weight = Z_B / (Z_U + Z_B); E is excluded.\n"
                "Derived numerical experiment; no new Lean/native SUMO result or empirical claim.\n"
                "Exact inputs, integer counts and seeds: witness-dynamics.json · report "
                + data.report_sha256[:12], fontsize=9, va="top", linespacing=1.4)
    return figure


def render_witness_dynamics(data: WitnessDynamics, directory: Path) -> tuple[Path, ...]:
    """Export full-size PNG/SVG plus source JSON, refusing any existing target."""
    import matplotlib

    targets = tuple(directory / name for name in (
        "witness-sequential.png", "witness-sequential.svg", "witness-dynamics.json"))
    if any(path.exists() or path.is_symlink() for path in targets):
        raise FileExistsError("Witness dynamics export requires unused target paths")
    directory.mkdir(parents=True, exist_ok=True)
    with matplotlib.rc_context({"font.family": "DejaVu Sans", "font.size": 9,
                                "text.usetex": False, "text.parse_math": False,
                                "svg.fonttype": "none", "svg.hashsalt": data.report_sha256}):
        figure = _draw(data)
        _check_geometry(figure)
        for path in targets[:2]:
            metadata: dict[str, str | None] = {
                "Description": data.scope + "; bridge packet SHA-256 " + data.report_sha256}
            if path.suffix == ".svg":
                metadata["Date"] = None
            figure.savefig(path, dpi=300, metadata=metadata)
        figure.clear()
    with targets[-1].open("x", encoding="utf-8") as stream:
        stream.write(data.model_dump_json(indent=2) + "\n")
    return targets

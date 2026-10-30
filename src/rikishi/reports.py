from __future__ import annotations

import json
import re
import textwrap
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

from rikishi.analytics import CorpusAnalytics, measure_corpus
from rikishi.ontology import OntologyIndex

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

STATIC = Path(__file__).with_name("static")
_NAVY = "#193449"
_TEAL = "#176b62"
_COPPER = "#a35e38"
_MUTED = "#536570"
_GRID = "#dce4e5"


class ReportArtifacts(TypedDict):
    html: str
    data: str
    svg: str
    png: str
    analytics: str
    summary: str
    composition_svg: str
    composition_png: str


def _count_label(count: int, denominator: int) -> str:
    share = f"{count / denominator:.1%}" if denominator else "share undefined"
    return f"{count:,}  ({share})"


def _count_axis(ax: Axes) -> None:
    from matplotlib.ticker import MaxNLocator, StrMethodFormatter

    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0, labelsize=9.5)
    ax.tick_params(axis="x", labelsize=9)
    ax.xaxis.set_major_locator(MaxNLocator(nbins=4, integer=True))
    ax.xaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    ax.set_axisbelow(True)
    ax.grid(axis="x", color=_GRID, linewidth=0.6)


def _provenance(measurements: CorpusAnalytics) -> str:
    clean = {True: "clean", False: "modified", None: "unversioned"}[measurements["source_clean"]]
    revision = measurements["source_commit"][:12] or "unrecorded"
    return (
        f"SUMO revision {revision} ({clean})  ·  "
        f"{measurements['rejected_files']:,} rejected files  ·  exact data: analytics.json"
    )


def _file_figure(fig: Figure, rows: list[dict], measurements: CorpusAnalytics) -> None:
    denominator = measurements["formula_denominator"]
    shown = rows[:12]
    fig.text(
        0.045, 0.942, "SUMO | Source-file composition", fontsize=15, weight="bold", color=_NAVY
    )
    fig.text(
        0.045,
        0.89,
        f"{denominator:,} top-level formulas in {measurements['indexed_files']:,} parsed files",
        fontsize=10,
        color=_MUTED,
    )
    ax = fig.add_axes((0.34, 0.225, 0.61, 0.605))
    values = [row["formulas"] for row in shown]
    ax.barh(range(len(shown)), values, color=_TEAL, height=0.60)
    ax.set(
        yticks=range(len(shown)),
        yticklabels=[textwrap.fill(row["path"], 27) for row in shown],
        xlabel="Top-level formulas (counts; bars start at zero)",
        xlim=(0, max(max(values, default=0) * 1.5, 1)),
    )
    ax.invert_yaxis()
    _count_axis(ax)
    for position, count in enumerate(values):
        ax.annotate(
            _count_label(count, denominator),
            (count, position),
            xytext=(5, 0),
            textcoords="offset points",
            va="center",
            fontsize=9,
            color=_NAVY,
        )
    fig.text(
        0.045,
        0.105,
        f"Largest {len(shown)} files shown: "
        f"{_count_label(sum(values), denominator)} of all indexed formulas.",
        fontsize=9,
        color=_MUTED,
    )
    fig.text(
        0.045,
        0.063,
        "Each percentage uses the full corpus; formula counts measure syntax.",
        fontsize=9,
        color=_MUTED,
    )
    fig.text(0.045, 0.025, _provenance(measurements), fontsize=8.5, color=_MUTED)


def _composition_figure(fig: Figure, measurements: CorpusAnalytics) -> None:
    from matplotlib.ticker import StrMethodFormatter

    denominator = measurements["formula_denominator"]
    terms = measurements["term_denominator"]
    fig.text(
        0.045,
        0.953,
        "SUMO | Formula heads and source-graph degree",
        fontsize=14,
        weight="bold",
        color=_NAVY,
    )
    fig.text(
        0.045,
        0.909,
        f"A  All {denominator:,} formulas: ten largest heads + exact remainder",
        fontsize=10,
        weight="bold",
        color=_TEAL,
    )
    predicates = measurements["predicates"][:10]
    remainder = denominator - sum(row["count"] for row in predicates)
    labels = [row["label"] for row in predicates] + ["All remaining heads"]
    counts = [row["count"] for row in predicates] + [remainder]
    composition = fig.add_axes((0.28, 0.55, 0.665, 0.322))
    composition.barh(
        range(len(counts)), counts, height=0.60, color=[_TEAL] * len(predicates) + [_COPPER]
    )
    composition.set(
        yticks=range(len(labels)),
        yticklabels=labels,
        xlim=(0, max(max(counts) * 1.55, 1)),
        xlabel="Top-level formulas",
    )
    composition.invert_yaxis()
    _count_axis(composition)
    for position, count in enumerate(counts):
        composition.annotate(
            _count_label(count, denominator),
            (count, position),
            xytext=(5, 0),
            textcoords="offset points",
            va="center",
            fontsize=9,
            color=_NAVY,
        )
    fig.text(
        0.045,
        0.457,
        f"B  Direct-edge degree: all {terms:,} indexed symbols; "
        f"{measurements['unique_edges']:,} distinct triples",
        fontsize=10,
        weight="bold",
        color=_TEAL,
    )
    degree = fig.add_axes((0.14, 0.17, 0.805, 0.225))
    rows = measurements["degree_distribution"]
    degree.set(
        xscale="symlog",
        yscale="symlog",
        xlabel="In + out degree (symlog; zero retained)",
        ylabel="Indexed symbols (symlog)",
    )
    degree.xaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    degree.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    degree.scatter(
        [row["degree"] for row in rows],
        [row["terms"] for row in rows],
        color=_TEAL,
        s=23,
        alpha=0.85,
        edgecolors="white",
        linewidths=0.4,
    )
    zero = measurements["zero_degree_terms"]
    degree.scatter([0], [zero], color=_COPPER, marker="s", s=40, zorder=5)
    degree.annotate(
        f"Degree 0: {_count_label(zero, terms)}",
        (0, zero),
        xytext=(9, 8),
        textcoords="offset points",
        color=_COPPER,
        fontsize=9,
    )
    nonzero = [row for row in rows if row["degree"] > 0]
    if nonzero:
        peak = max(nonzero, key=lambda row: row["terms"])
        degree.annotate(
            f"Degree {peak['degree']:,}: {peak['terms']:,} symbols",
            (peak["degree"], peak["terms"]),
            xytext=(14, -12),
            textcoords="offset points",
            color=_NAVY,
            fontsize=9,
            arrowprops={"arrowstyle": "-", "color": _MUTED, "linewidth": 0.8},
        )
    degree.set_xlim(left=-0.3)
    degree.set_ylim(bottom=-0.3)
    degree.spines[["top", "right"]].set_visible(False)
    degree.tick_params(labelsize=9)
    degree.set_axisbelow(True)
    degree.grid(color=_GRID, linewidth=0.6)
    fig.text(
        0.045,
        0.063,
        "Self-loops count twice. Nested assertions and inferred closure excluded; no power-law fit.",
        fontsize=9,
        color=_MUTED,
    )
    fig.text(0.045, 0.025, _provenance(measurements), fontsize=8.5, color=_MUTED)


def build_report(index_path: Path, output_dir: Path) -> ReportArtifacts:
    import matplotlib
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    index = OntologyIndex(index_path)
    stats = index.stats()
    measurements = measure_corpus(index)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(stats, indent=2, ensure_ascii=True)
    analytical_payload = json.dumps(measurements, indent=2, ensure_ascii=True)
    (output_dir / "corpus.json").write_text(payload + "\n", encoding="utf-8")
    (output_dir / "analytics.json").write_text(analytical_payload + "\n", encoding="utf-8")
    with matplotlib.rc_context(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "text.parse_math": False,
            "text.usetex": False,
            "svg.fonttype": "none",
            "axes.labelcolor": _NAVY,
            "xtick.color": _MUTED,
            "ytick.color": _NAVY,
            "axes.edgecolor": _GRID,
        }
    ):
        files = Figure(figsize=(7.2, 5.7), facecolor="white")
        FigureCanvasAgg(files)
        try:
            _file_figure(files, stats["top_files"], measurements)
            for suffix in ("svg", "png"):
                files.savefig(output_dir / f"corpus-files.{suffix}", dpi=180)
        finally:
            files.clear()
        composition = Figure(figsize=(7.2, 6.7), facecolor="white")
        FigureCanvasAgg(composition)
        try:
            _composition_figure(composition, measurements)
            for suffix in ("svg", "png"):
                composition.savefig(output_dir / f"corpus-composition.{suffix}", dpi=180)
        finally:
            composition.clear()
    summary = (
        "# Indexed corpus measurements\n\n"
        f"Source revision: `{measurements['source_commit']}`. Clean source: `{measurements['source_clean']}`.\n\n"
        f"{measurements['formula_denominator']:,} top-level formulas in {measurements['indexed_files']:,} parsed files; "
        f"{measurements['rejected_files']:,} rejected files. Formula counts measure syntax.\n\n"
        f"{measurements['edge_assertions']:,} binary edge assertions reduce to {measurements['unique_edges']:,} distinct labeled directed triples. "
        f"{measurements['zero_degree_terms']:,} of {measurements['term_denominator']:,} indexed symbols have zero degree in this restricted graph.\n\n"
        "Degree includes both endpoints (self-loops count twice). The graph excludes nested assertions and inferred closure. "
        "No metric establishes ontology consistency, semantic completeness, or independent factual content. "
        "See docs/metrics.md for denominators and analytics.json for complete distributions.\n"
    )
    (output_dir / "measurements.md").write_text(summary, encoding="utf-8")
    template = (STATIC / "report.html").read_text(encoding="utf-8")
    replacements = {
        "__STYLE__": (STATIC / "style.css").read_text(encoding="utf-8"),
        "__DATA__": payload.replace("<", "\\u003c"),
        "__ANALYTICS__": analytical_payload.replace("<", "\\u003c"),
        "__ANALYTICS_JS__": (STATIC / "analytics.js").read_text(encoding="utf-8"),
        "__REPORT_JS__": (STATIC / "report.js").read_text(encoding="utf-8"),
    }
    html = re.sub(
        "|".join(re.escape(token) for token in replacements),
        lambda match: replacements[match[0]],
        template,
    )
    (output_dir / "dashboard.html").write_text(html, encoding="utf-8")
    return ReportArtifacts(
        html=str(output_dir / "dashboard.html"),
        data=str(output_dir / "corpus.json"),
        svg=str(output_dir / "corpus-files.svg"),
        png=str(output_dir / "corpus-files.png"),
        analytics=str(output_dir / "analytics.json"),
        summary=str(output_dir / "measurements.md"),
        composition_svg=str(output_dir / "corpus-composition.svg"),
        composition_png=str(output_dir / "corpus-composition.png"),
    )

"""Print figures and an offline explorer derived only from portable alignment replay."""

from __future__ import annotations

import json
import textwrap
from decimal import Decimal, localcontext
from hashlib import sha256
from importlib.resources import files
from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal

from rikishi.alignment import AlignmentReport, NumericalRow, validate_alignment_report
from rikishi.competency import Frozen
from rikishi.runtime_artifacts import read_regular

if TYPE_CHECKING:
    from matplotlib.artist import Artist
    from matplotlib.figure import Figure

_NAVY: Final = "#193449"
_TEAL: Final = "#176b62"
_ORANGE: Final = "#a35e38"
_MUTED: Final = "#536570"
_METRICS: Final = ("reference", "permutation", "rescaling")
_STATUS: Final = {"Satisfiable": "SAT", "Unsatisfiable": "UNSAT", "Theorem": "THM",
                  "CounterSatisfiable": "C-SAT", "ContradictoryAxioms": "CONTR",
                  "Timeout": "TIME", "GaveUp": "GAVEUP", "Unknown": "UNKNOWN"}
_BOUNDARY: Final = ("Finite local FOL fragment; arithmetic checked separately. "
                    "No full-SUMO consistency, semantic alignment or biological validation.")


class ResearchFigureError(ValueError):
    reason: str

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


class ReportInput(Frozen):
    path: str
    sha256: str
    report: AlignmentReport


class Ratios(Frozen):
    reference: float
    permutation: float
    rescaling: float


class RatioRow(Frozen):
    id: str
    dimension: int
    candidate: str
    population: Literal["ordinary", "boundary"]
    tolerance: str
    ratios: Ratios
    passed: bool


class ControlAggregate(Frozen):
    dimension: int
    candidate: str
    rows: int
    maxima: Ratios
    zeros: dict[str, int]


class FigureInputs(Frozen):
    schema_version: Literal[1] = 1
    reports: list[ReportInput]
    numerical_rows: list[RatioRow]
    aggregates: list[ControlAggregate]
    provenance: list[str]
    width_mm: int = 174
    height_mm: float
    dpi: int
    decimal_places: int
    ratio_threshold: int = 1
    symlog_linear_threshold: float = 0.001
    boundary: str = _BOUNDARY


def _report_input(path: Path) -> ReportInput:
    raw = read_regular(path)
    digest = sha256(raw).hexdigest()
    report = validate_alignment_report(path, trusted_report_sha256=digest)
    return ReportInput(path=str(path), sha256=digest, report=report)


def _check_pair(left: ReportInput, right: ReportInput) -> None:
    a, b = left.report, right.report
    if a.prover == b.prover:
        raise ResearchFigureError("Comparison requires distinct prover families")
    if (a.study != b.study or a.authority_sha256 != b.authority_sha256
            or a.source_claims != b.source_claims or a.bindings != b.bindings
            or a.numerical != b.numerical):
        raise ResearchFigureError("Comparison study, source, policy or numerical data differ")
    relatives = ["study.json", "source-report.json", "workbook.xlsx", "extension.kif",
                 *(f"problems/{case.id}.p" for case in a.study.cases)]
    for relative in relatives:
        if read_regular(Path(left.path).parent / relative) != read_regular(
                Path(right.path).parent / relative):
            raise ResearchFigureError(f"Comparison retained bytes differ: {relative}")


def _ratio_rows(report: AlignmentReport) -> list[RatioRow]:
    result = []
    populations: list[tuple[Literal["ordinary", "boundary"], list[NumericalRow]]] = [
        ("ordinary", report.numerical.rows), ("boundary", report.numerical.extremes)]
    for population, rows in populations:
        for row in rows:
            with localcontext() as context:
                context.prec = report.study.numerical.decimal_precision
                ratios = [float(Decimal.from_float(error) / Decimal(row.tolerance)) for error in
                          (row.max_reference_error, row.permutation_max_error,
                           row.rescaling_max_error)]
            result.append(RatioRow(id=row.input.id, dimension=row.dimension,
                                   candidate=row.candidate, population=population,
                                   tolerance=row.tolerance, passed=row.passed,
                                   ratios=Ratios(reference=ratios[0], permutation=ratios[1],
                                                 rescaling=ratios[2])))
    return result


def _aggregates(rows: list[RatioRow]) -> list[ControlAggregate]:
    groups = sorted({(row.dimension, row.candidate) for row in rows
                     if row.population == "ordinary"})
    result = []
    for dimension, candidate in groups:
        selected = [r for r in rows if r.population == "ordinary"
                    and (r.dimension, r.candidate) == (dimension, candidate)]
        maxima = {metric: max(getattr(r.ratios, metric) for r in selected) for metric in _METRICS}
        result.append(ControlAggregate(dimension=dimension, candidate=candidate, rows=len(selected),
                                       maxima=Ratios(**maxima), zeros={metric: sum(
                                           getattr(r.ratios, metric) == 0 for r in selected)
                                           for metric in _METRICS}))
    return result


def _provenance(reports: list[ReportInput]) -> list[str]:
    report = reports[0].report
    study = report.study
    lines = [f"{r.report.prover.upper()} report: {r.path}\nSHA-256: {r.sha256}" for r in reports]
    lines.extend([
        f"Study: {study.study_id}; authority SHA-256: {report.authority_sha256}",
        f"SUMO: {study.sumo_path}; lines: " + ", ".join(
            f"{c.line}-{c.end_line}" for c in report.source_claims.citations),
        f"SUMO revision: {study.sumo_commit}; SHA-256: {study.sumo_sha256}",
        f"SUMO URL: {study.sumo_url}",
        (f"Workbook: {study.workbook_path}; sheet: {study.workbook_sheet!r}; "
         f"rows: {study.workbook_rows}; columns: {study.workbook_columns}"),
        f"Workbook SHA-256: {study.workbook_sha256}",
        f"Workbook URL: {study.workbook_url}; accessed: {study.access_date}",
        f"Scope: {study.scope}",
        f"Replay boundary: {report.replay_boundary}",
        "Complete inputs/captures bindings: research-controls.json; explorer: research-dashboard.html",
    ])
    return lines


def _footer(reports: list[ReportInput]) -> list[str]:
    report = reports[0].report
    hashes = "; ".join(f"{r.report.prover.upper()} {r.sha256[:12]}" for r in reports)
    return [
        (f"{report.study.study_id} | SHA-256 prefixes: study {report.authority_sha256[:12]}; "
         f"SUMO {report.study.sumo_sha256[:12]}"),
        f"XLSX {report.study.workbook_sha256[:12]}; reports {hashes}; semantic validation=False",
        "Full custody: research-controls.json + research-dashboard.html",
    ]


def _print_figure(data: FigureInputs, footer: list[str]) -> Figure:
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure
    from matplotlib.ticker import FuncFormatter

    height = data.height_mm
    fig = Figure(figsize=(data.width_mm / 25.4, height / 25.4), facecolor="white")
    canvas = FigureCanvasAgg(fig)

    def text(y: float, value: str, **kwargs) -> None:
        fig.text(0.055, 1 - y / height, value, va="top", fontsize=8, color=_NAVY, **kwargs)

    fig.text(0.055, 1 - 4 / height, "Finite alignment campaign: measured controls", va="top",
             fontsize=10, weight="bold", color=_NAVY)
    text(10, textwrap.fill(data.boundary, 100))
    report = data.reports[0].report
    text(21, "A  Logical outcomes · expected polarity and observed solver status", weight="bold")
    ax = fig.add_axes((0.055, 1 - 78 / height, 0.89, 52 / height))
    ax.set(xlim=(0, 1), ylim=(len(report.logical) + 1, -0.5))
    ax.axis("off")
    for x, heading in ((0, "Declared case"), (0.36, "Kind"), (0.48, "Expected")):
        ax.text(x, 0, heading, fontsize=7.6, weight="bold", color=_NAVY)
    for column, binding in enumerate(data.reports):
        ax.text(0.66 + column * 0.18, 0, binding.report.prover.upper(), weight="bold", fontsize=8)
    for index, (case, run) in enumerate(zip(report.study.cases, report.logical, strict=True), 1):
        ax.axhspan(index - 0.55, index + 0.40, color="#f0f4f4" if index % 2 else "white", zorder=0)
        values = [(0, run.id), (0.36, "B" if case.conjecture is None else "Q"),
                  (0.48, _STATUS[run.expected])]
        for column, binding in enumerate(data.reports):
            observed = binding.report.logical[index - 1]
            marker = {"matched": "=", "mismatch": "!", "unresolved": "?"}[observed.disposition]
            values.append((0.66 + column * 0.18,
                           f"{marker} {_STATUS.get(observed.observed, observed.observed)}"))
        for x, value in values:
            ax.text(x, index, value, fontsize=7.5, va="center", color=_NAVY)
    text(80, "B background / Q query. SAT Satisfiable; UNSAT Unsatisfiable; THM Theorem;\n"
         "C-SAT CounterSatisfiable. = matched; ! mismatch; ? unresolved (never counted as success).")
    summaries = [f"{r.report.prover.upper()}: {r.report.summary.logical_matched}/"
                 f"{r.report.summary.logical_cases} matched; "
                 f"{r.report.summary.logical_mismatched} mismatch; "
                 f"{r.report.summary.logical_unresolved} unresolved; "
                 f"complete={r.report.summary.campaign_complete}" for r in data.reports]
    text(88, "\n".join(summaries))
    text(98, "B  Numerical error / predeclared tolerance · separate arithmetic", weight="bold")
    plot = fig.add_axes((0.14, 1 - 143 / height, 0.80, 33 / height))
    ordinary = [r for r in data.numerical_rows if r.population == "ordinary"]
    dimensions = sorted({r.dimension for r in ordinary})
    for offset, metric, color, marker in zip((-0.22, 0, 0.22), _METRICS,
                                            (_NAVY, _TEAL, _ORANGE), ("o", "^", "s"), strict=True):
        for index, dimension in enumerate(dimensions):
            rows = [r for r in ordinary if r.dimension == dimension]
            values = [getattr(r.ratios, metric) for r in rows]
            xs = [index + offset + (i / max(1, len(rows) - 1) - 0.5) * 0.12
                  for i in range(len(rows))]
            plot.scatter(xs, values, c=color, marker=marker, s=9, alpha=0.45,
                         label=metric if index == 0 else None)
    plot.axhline(data.ratio_threshold, color=_ORANGE, linestyle="--", lw=1, label="threshold = 1")
    plot.set_yscale("symlog", linthresh=data.symlog_linear_threshold)
    plot.yaxis.set_major_formatter(FuncFormatter(lambda value, position: f"{value:g}"))
    plot.set_ylim(-0.0003, max(1.5, max(max(r.ratios.model_dump().values()) for r in ordinary) * 1.4))
    plot.set_xticks(range(len(dimensions)), [str(d) for d in dimensions])
    plot.set_xlabel("Model dimension", fontsize=8)
    plot.set_ylabel("Error / tolerance (dimensionless)", fontsize=7.5)
    plot.tick_params(labelsize=7.5)
    plot.grid(axis="y", color="#dae1e2", lw=0.5)
    plot.legend(loc="upper center", bbox_to_anchor=(0.5, 1.25), ncol=4, fontsize=7.5, frameon=False)
    plot.spines[["top", "right"]].set_visible(False)
    zeros = "; ".join(f"{metric}: {sum(getattr(r.ratios, metric) == 0 for r in ordinary)}"
                      for metric in _METRICS)
    text(153, f"All {len(ordinary)} ordinary rows; tolerance {report.study.numerical.ordinary_tolerance}. "
         f"Zeros ({zeros}).\n"
         f"Symlog axis is linear below {data.symlog_linear_threshold}; no epsilon replaces zero.")
    text(162, "C  Support boundaries and invalid inputs", weight="bold")
    support = [r for r in data.numerical_rows if r.population == "boundary"]
    for x, label in ((0.055, "Boundary case"), (0.43, "Reference"), (0.59, "Permutation"),
                     (0.75, "Rescaling"), (0.91, "Passed")):
        fig.text(x, 1 - 167 / height, label, va="top", fontsize=7.5, weight="bold", color=_NAVY)
    for i, row in enumerate(support):
        y = 1 - (173 + i * 4.5) / height
        fig.text(0.055, y, row.id, va="top", fontsize=7.5, color=_NAVY)
        for x, metric in zip((0.43, 0.59, 0.75), _METRICS, strict=True):
            value = getattr(row.ratios, metric)
            fig.text(x, y, "0" if value == 0 else f"{value:.{data.decimal_places}e}",
                     va="top", fontsize=7.5, color=_NAVY)
        fig.text(0.91, y, str(row.passed), va="top", fontsize=7.5, color=_NAVY)
    summary = report.summary
    tolerances = ", ".join(sorted({row.tolerance for row in support}))
    text(192, f"Boundary {summary.extreme_passed}/{summary.extreme_cases} passed; "
         f"invalid {summary.invalid_rejected}/{summary.invalid_cases} rejected. "
         f"Table values: error / tolerance ({tolerances}).")
    fig.text(0.055, 1 - 197 / height, "\n".join(footer), va="top", fontsize=7.5,
             color=_MUTED, family="DejaVu Sans Mono", linespacing=1.35)
    canvas.draw()
    renderer = canvas.get_renderer()
    artists: list[Artist] = [*fig.texts, *(label for axes in fig.axes for label in (
        *axes.texts, *axes.get_xticklabels(), *axes.get_yticklabels(),
        axes.xaxis.label, axes.yaxis.label, axes.title))]
    artists.extend(legend for axes in fig.axes if (legend := axes.get_legend()) is not None)
    for artist in artists:
        bounds = artist.get_window_extent(renderer)
        if bounds.x0 < 0 or bounds.y0 < 0 or bounds.x1 > fig.bbox.width or bounds.y1 > fig.bbox.height:
            raise ResearchFigureError("Complete text exceeds the print layout")
    return fig


def render_research_figures(output: Path, report_path: Path, *, comparison_path: Path | None = None,
                            dpi: int, decimal_places: int) -> list[Path]:
    """Replay reports, then export PNG/SVG/exact JSON/offline HTML in that order.

    DPI must be 72..1200; decimal_places 0..8 affects presentation only. The
    174 x 210 mm print layout refuses overflowing labels. Full provenance is in
    the companion JSON and HTML; print footers explicitly identify hash prefixes.
    Validation and layout errors occur before creating output. Existing artifact
    names are refused. No solver, network, server or mutable source index is used.
    """
    if type(dpi) is not int or not 72 <= dpi <= 1200:
        raise ResearchFigureError("dpi must be an integer in 72..1200")
    if type(decimal_places) is not int or not 0 <= decimal_places <= 8:
        raise ResearchFigureError("decimal_places must be an integer in 0..8")
    reports = [_report_input(report_path)]
    if comparison_path is not None:
        comparison = _report_input(comparison_path)
        _check_pair(reports[0], comparison)
        reports.append(comparison)
    reports.sort(key=lambda r: r.report.prover)
    footer = _footer(reports)
    rows = _ratio_rows(reports[0].report)
    data = FigureInputs(reports=reports, numerical_rows=rows, aggregates=_aggregates(rows),
                        provenance=_provenance(reports), height_mm=210,
                        dpi=dpi, decimal_places=decimal_places)
    paths = [output / name for name in ("research-controls.png", "research-controls.svg",
                                        "research-controls.json", "research-dashboard.html")]
    if any(path.exists() or path.is_symlink() for path in paths):
        raise FileExistsError("Research figure artifacts already exist")
    payload = data.model_dump_json(indent=2) + "\n"
    import matplotlib

    with matplotlib.rc_context({"font.family": "DejaVu Sans", "text.usetex": False,
                                "text.parse_math": False, "svg.fonttype": "none",
                                "svg.hashsalt": sha256(payload.encode()).hexdigest()}):
        fig = _print_figure(data, footer)
        output.mkdir(parents=True, exist_ok=True)
        description = "\n".join(f"{r.report.prover}: {r.sha256}" for r in reports)
        fig.savefig(paths[0], dpi=dpi, metadata={"Description": description})
        fig.savefig(paths[1], metadata={"Date": None, "Description": description})
        fig.clear()
    paths[2].write_text(payload, encoding="utf-8")
    svg = paths[1].read_text(encoding="utf-8")
    embedded = json.dumps(data.model_dump(mode="json"), allow_nan=False).replace(
        "&", "\\u0026").replace("<", "\\u003c").replace(
        ">", "\\u003e").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    template = files("rikishi").joinpath("data/research-explorer.html").read_text(encoding="utf-8")
    # Split once before inserting either value; source text cannot become a template token.
    before, after = template.split("<!--RESEARCH-SVG-->")
    body, end = after.split("<!--RESEARCH-DATA-->")
    paths[3].write_text(before + svg[svg.index("<svg "):] + body + embedded + end, encoding="utf-8")
    return paths

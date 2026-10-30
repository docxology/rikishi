"""Digest-bound publication figures for the shared finite witness experiment.

SIZE_OK: one owned module is required by the integration boundary; the frozen
export model and three renderers deliberately share the same verified inputs.
"""

from __future__ import annotations

import json
import os
import re
import textwrap
from fractions import Fraction
from hashlib import sha256
from importlib.resources import files
from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal

from pydantic import Field

from rikishi.bridge_models import (
    BridgeError,
    BridgeReport,
    BridgeStudy,
    FiniteWitness,
    LeanCommand,
    LeanEvidence,
)
from rikishi.bridge_replay import validate_bridge_report
from rikishi.bridge_study import mass_facts
from rikishi.bridge_views import inspect_cases
from rikishi.fep import free_energy
from rikishi.inference_models import CaseKind, Frozen
from rikishi.runtime_artifacts import ProverKind, checked_source_path, read_regular

if TYPE_CHECKING:
    from matplotlib.figure import Figure

_NAVY: Final = "#193449"
_TEAL: Final = "#176b62"
_COPPER: Final = "#a35e38"
_KINDS: Final[tuple[CaseKind, ...]] = (
    "background", "positive", "negative", "removed-premise", "refutation")
_STATUSES: Final = {
    "Satisfiable": ("SAT", "#dcebe4"), "Theorem": ("THM", "#cbdce8"),
    "CounterSatisfiable": ("C-SAT", "#f1dfc5"), "Unsatisfiable": ("UNSAT", "#dfd4e9"),
    "ContradictoryAxioms": ("CONTR", "#efc9c9"), "Timeout": ("TIME", "#efc9c9"),
    "GaveUp": ("GAVEUP", "#efc9c9"), "Unknown": ("UNKNOWN", "#efc9c9"),
}


class BridgeFigureError(ValueError):
    """A requested export or artist geometry violates the figure contract."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


class ExplorerCase(Frozen):
    case_id: str
    scenario_id: str
    witness_id: str
    prover: ProverKind
    kind: CaseKind
    command: tuple[str, ...]
    problem: str
    stdout: str
    stderr: str


class LeanLog(Frozen):
    kind: Literal["main", "positive-environment", "negative-control"]
    evidence_id: str
    path: str
    sha256: str
    text: str
    command: tuple[str, ...]
    returncode: int
    timeout_seconds: int = Field(ge=1, le=600)
    elapsed_seconds: float = Field(ge=0, allow_inf_nan=False)
    timed_out: Literal[False]


class LeanSource(Frozen):
    id: str
    kind: Literal["positive-environment", "negative-control"]
    path: str
    sha256: str
    text: str


class EnergyCurve(Frozen):
    witness_id: str
    q: tuple[float, ...]
    free_energy: tuple[float, ...]
    kl: tuple[float, ...]
    surprise: float


class WitnessFacts(Frozen):
    witness_id: str
    assumptions: tuple[str, ...]


class BridgeFigureInputs(Frozen):
    """Portable, immutable export of a verified packet; no native execution."""

    schema_version: Literal[1] = 1
    report_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    report: BridgeReport
    study: BridgeStudy
    cases: tuple[ExplorerCase, ...]
    lean_source: str
    lean_proofs: tuple[str, ...]
    lean_logs: tuple[LeanLog, ...]
    lean_sources: tuple[LeanSource, ...]
    extension: str
    witness_facts: tuple[WitnessFacts, ...]
    curves: tuple[EnergyCurve, ...]
    dpi: int = Field(ge=72, le=1200)
    decimal_places: int = Field(ge=0, le=8)
    width_mm: float = 191.9


def _retained(directory: Path, relative: str, digest: str) -> str:
    path = checked_source_path(directory / relative)
    if not path.is_relative_to(directory):
        raise BridgeError("Figure evidence escapes its packet")
    raw = read_regular(path)
    if sha256(raw).hexdigest() != digest:
        raise BridgeError("Figure evidence changed after packet replay")
    return raw.decode("utf-8")


def _curve(witness: FiniteWitness) -> EnergyCurve:
    prior = tuple(float(Fraction(value)) for value in witness.prior)
    likelihood = tuple(float(Fraction(value)) for value in witness.likelihood)
    q = tuple(index / 200 for index in range(201))
    results = tuple(free_energy(prior, likelihood, (value, 1 - value)) for value in q)
    return EnergyCurve(witness_id=witness.id, q=q,
                       free_energy=tuple(row["free_energy"] for row in results),
                       kl=tuple(row["kl_to_posterior"] for row in results),
                       surprise=results[0]["surprise"])


def _lean_inputs(directory: Path, evidence: LeanEvidence) -> tuple[
    tuple[LeanSource, ...], tuple[LeanLog, ...],
]:
    """Retain main commands plus every paired source, diagnostic and deadline."""
    sources: list[LeanSource] = []
    commands: list[tuple[Literal["main", "positive-environment", "negative-control"],
                         str, LeanCommand]] = [("main", row.log, row) for row in evidence.commands]
    for environment in evidence.environments:
        sources.append(LeanSource(id=environment.id, kind="positive-environment",
                                  path=environment.source, sha256=environment.source_sha256,
                                  text=_retained(directory, environment.source,
                                                 environment.source_sha256)))
        commands.append(("positive-environment", environment.id, environment.command))
    for control in evidence.controls:
        sources.append(LeanSource(id=control.id, kind="negative-control",
                                  path=control.source, sha256=control.source_sha256,
                                  text=_retained(directory, control.source, control.source_sha256)))
        commands.append(("negative-control", control.id, control.command))
    logs = tuple(LeanLog(kind=kind, evidence_id=identity, path=row.log, sha256=row.log_sha256,
                         text=_retained(directory, row.log, row.log_sha256),
                         command=row.command, returncode=row.returncode,
                         timeout_seconds=row.timeout_seconds, elapsed_seconds=row.elapsed_seconds,
                         timed_out=row.timed_out) for kind, identity, row in commands)
    return tuple(sources), logs


def build_bridge_figure_inputs(path: Path, *, trusted_report_sha256: str,
                               dpi: int = 300, decimal_places: int = 6) -> BridgeFigureInputs:
    """Replay against the caller's outer digest, then deduplicate retained evidence."""
    if type(dpi) is not int or not 72 <= dpi <= 1200:
        raise BridgeFigureError("dpi must be an integer in 72..1200")
    if type(decimal_places) is not int or not 0 <= decimal_places <= 8:
        raise BridgeFigureError("decimal_places must be an integer in 0..8")
    path = checked_source_path(path)
    report = validate_bridge_report(path, trusted_report_sha256=trusted_report_sha256)
    directory = path.parent
    study = BridgeStudy.model_validate_json(read_regular(directory / "study.json"))
    if sha256(study.model_dump_json().encode()).hexdigest() != report.study_sha256:
        raise BridgeError("Figure study changed after packet replay")
    views = inspect_cases(directory, path.name, trusted_report_sha256)
    source = _retained(directory, report.lean.source, report.lean.source_sha256)
    proofs = tuple(name for name in report.lean.declarations
                   if re.search(r"(?m)^theorem " + re.escape(name.split(".")[-1]) + r"\b", source))
    sources, logs = _lean_inputs(directory, report.lean)
    return BridgeFigureInputs(
        report_sha256=trusted_report_sha256, report=report, study=study,
        cases=tuple(ExplorerCase(case_id=view.case.id, scenario_id=view.scenario.id,
                                witness_id=view.witness.id, prover=view.case.prover,
                                kind=view.case.kind, command=view.command,
                                problem=view.problem, stdout=view.stdout, stderr=view.stderr)
                    for view in views), lean_source=source, lean_proofs=proofs,
        lean_logs=logs, lean_sources=sources,
        curves=tuple(_curve(witness) for witness in report.witnesses),
        extension=_retained(directory, "extension.kif", report.extension_sha256),
        witness_facts=tuple(WitnessFacts(witness_id=witness.id, assumptions=mass_facts(witness))
                            for witness in report.witnesses),
        dpi=dpi, decimal_places=decimal_places)


def bridge_explorer_html(inputs: BridgeFigureInputs) -> str:
    """Return a self-contained explorer; all embedded evidence remains inert data."""
    payload = json.dumps(inputs.model_dump(mode="json"), allow_nan=False).replace(
        "&", "\\u0026").replace("<", "\\u003c").replace(
        ">", "\\u003e").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    template = files("rikishi").joinpath("data/bridge-explorer.html").read_text(encoding="utf-8")
    before, after = template.split("__BRIDGE_DATA__")
    return before + payload + after


def _figure(inputs: BridgeFigureInputs, height: float, title: str) -> Figure:
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    fig = Figure(figsize=(inputs.width_mm / 25.4, height / 25.4), facecolor="white")
    FigureCanvasAgg(fig)
    fig.text(0.045, 0.975, title, fontsize=12, weight="bold", va="top", color=_NAVY)
    fig.text(0.045, 0.021,
             "Secure Hash Algorithm, 256-bit (SHA-256); packet digest prefix (16 hex): "
             f"{inputs.report_sha256[:16]}\n"
             f"{inputs.report.study_id} | Sources/receipts/captures: bridge-figure-inputs.json / explorer",
             fontsize=7.5, color=_NAVY, va="bottom")
    return fig


def _number(value: float, places: int) -> str:
    """Preserve small nonzero floating residuals instead of printing signed zero."""
    if value != 0 and round(value, places) == 0:
        return f"{value:.{places}e}"
    return f"{value + 0.0:.{places}f}"


def _evidence_figure(inputs: BridgeFigureInputs) -> Figure:
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.font_manager import FontProperties

    report = inputs.report
    witness = report.witnesses[0]
    numerical = next(row for row in report.numerical if row.witness_id == witness.id)
    scenario = next((row for row in report.scenarios
                     if row.witness_id == witness.id and row.role == "result"
                     and row.query.lstrip().startswith("(exists")), None)
    if scenario is None:
        raise BridgeFigureError("Evidence figure requires a source-derived existential result scenario")
    claims = [row for row in report.source_claims
              if row.line in {selection.line for selection in scenario.selections}]
    claim = max(claims, key=lambda row: row.line)
    positive = [row for row in report.cases if row.group == scenario.id and row.kind == "positive"]
    fig = _figure(inputs, 205, "One shared witness, three separate obligations")
    renderer = FigureCanvasAgg(fig).get_renderer()
    font = FontProperties(family="DejaVu Sans", size=8.5)

    def block(y: float, heading: str, body: str) -> None:
        lines: list[str] = []
        for paragraph in body.splitlines():
            current = ""
            for word in paragraph.split():
                proposal = f"{current} {word}" if current else word
                width = renderer.get_text_width_height_descent(proposal, font, ismath=False)[0]
                if current and width > 0.91 * fig.bbox.width:
                    lines.append(current)
                    current = word
                else:
                    current = proposal
            lines.append(current)
        fig.text(0.045, y, heading, fontsize=10, weight="bold", color=_TEAL, va="top")
        fig.text(0.045, y - 0.027, "\n".join(lines), fontsize=8.5, color=_NAVY,
                 linespacing=1.35, va="top")

    fig.text(0.045, 0.925,
             f"Witness {witness.id} · observed outcome true · state order [false, true]\n"
             f"prior = {witness.prior}; likelihood = {witness.likelihood}; candidate = {witness.candidate}",
             fontsize=8.7, color=_NAVY, va="top", linespacing=1.4)
    selected = textwrap.fill(claim.raw_kif, 105)
    query = textwrap.fill(scenario.query, 105)
    observations = "; ".join(f"{row.prover.upper()}: {row.observed}, matched={row.matched}"
                              for row in positive)
    block(0.84, "A  Suggested Upper Merged Ontology (SUMO): selected first-order obligation",
          f"Scenario: {scenario.id}\n{claim.source_path}:{claim.line}-{claim.end_line}\n"
          f"Selected source premise (Knowledge Interchange Format):\n{selected}\n"
          f"Generated query: {query}\nRecorded native outcomes: {observations}")
    names = [name for name in inputs.lean_proofs if name.startswith(witness.namespace + ".")]
    compiled = ", ".join(str(row.returncode) for row in report.lean.commands)
    positives = sum(row.command.returncode == 0 and not row.command.timed_out
                    for row in report.lean.environments)
    negatives = sum(row.rejected and row.command.returncode != 0 and not row.command.timed_out
                    for row in report.lean.controls)
    signature = "theorem posterior_reconstruction" + inputs.lean_source.split(
        "theorem posterior_reconstruction", 1)[1].split(" :=", 1)[0]
    signature = "\n".join(textwrap.fill(line.strip(), 105) for line in signature.splitlines())
    block(0.62, "B  Lean: finite probability and Kullback–Leibler divergence (KL)",
          f"Namespace {witness.namespace}\n{signature}\n" +
          "\n".join(name for name in names if name.endswith((
              ".kl_nonnegative", ".kl_self", ".kl_decomposition"))) + "\n"
          "FiniteLaw normalization; FiniteKernel normalization; positive evidence and posterior.\n"
          f"Source: {report.lean.source}\n"
          "Secure Hash Algorithm, 256-bit (SHA-256) source digest prefix (16 hex): "
          f"{report.lean.source_sha256[:16]}\n"
          f"Main exits [{compiled}]; paired positive zero-exit {positives}/{len(report.lean.environments)}; "
          f"rejected controls {negatives}/{len(report.lean.controls)}.\n"
          f"Audited declarations (includes definitions): {len(report.lean.declarations)}; "
          f"named proofs for this witness: {len(names)}.")
    r, p = numerical.result, inputs.decimal_places
    block(0.32, "C  Free Energy Principle (FEP): independently checked finite arithmetic",
          f"Exact posterior = {numerical.exact_posterior}; evidence = {numerical.evidence}\n"
          f"F(q) = KL(q || posterior) + surprise\n"
          f"{_number(r.free_energy, p)} = {_number(r.kl_to_posterior, p)} + {_number(r.surprise, p)} nats\n"
          f"Identity residual: {r.identity_residual:.2e}; Decimal reference error: "
          f"{numerical.max_reference_error:.2e}; tolerance: {numerical.tolerance:.2e}\n"
          f"Reconstruction residuals: {numerical.reconstruction_residuals}; passed={numerical.passed}")
    fig.text(0.045, 0.105,
             "Authored interpretation links the shared identifiers and rational inputs; these lanes do not transfer proofs.\n"
             "SUMO's existential result need not be the named numerical record. Its binary LogFn differs from\n"
             "Lean's unary natural Real.log. No arithmetic/logarithm encoding or general semantic preservation.",
             fontsize=8.1, color=_NAVY, va="top", linespacing=1.3)
    return fig


def _energy_figure(inputs: BridgeFigureInputs) -> Figure:
    fig = _figure(inputs, 205, "Finite posterior, candidate and energy landscape")
    fig.text(0.045, 0.945, "Kullback–Leibler divergence (KL); energies are measured in nats.",
             fontsize=8.5, va="top", color=_NAVY)
    axes = fig.subplots(len(inputs.report.witnesses), 2, squeeze=False)
    fig.subplots_adjust(left=0.10, right=0.96, top=0.87, bottom=0.15, hspace=0.80, wspace=0.35)
    for index, witness in enumerate(inputs.report.witnesses):
        row = next(item for item in inputs.report.numerical if item.witness_id == witness.id)
        curve = next(item for item in inputs.curves if item.witness_id == witness.id)
        left, right = axes[index]
        for offset, values, label, color in (
            (-0.25, witness.prior, "Prior", "#8195a3"),
            (0.0, row.exact_posterior, "Posterior", _TEAL),
            (0.25, witness.candidate, "Candidate", _COPPER),
        ):
            left.bar([offset, 1 + offset], [float(Fraction(v)) for v in values],
                     width=0.23, label=label, color=color)
        left.set(ylim=(0, 1.14), xticks=(0, 1), xticklabels=("false (0)", "true (1)"),
                 ylabel="Probability", title=f"{witness.id}\n"
                 f"prior {witness.prior}; likelihood {witness.likelihood}\n"
                 f"posterior {row.exact_posterior}")
        left.text(0.02, 0.98, f"Candidate F = {_number(row.result.free_energy, inputs.decimal_places)} nats\n"
                  f"Floating KL {_number(row.result.kl_to_posterior, inputs.decimal_places)} + "
                  f"surprise {_number(row.result.surprise, inputs.decimal_places)}",
                  transform=left.transAxes, fontsize=7.5, va="top")
        right.plot(curve.q, curve.free_energy, color=_NAVY, label="F(q)")
        right.plot(curve.q, curve.kl, color=_TEAL, linestyle=":", label="KL(q || posterior)")
        right.axhline(curve.surprise, color=_COPPER, linestyle="--", label="Surprise")
        posterior = float(Fraction(row.exact_posterior[0]))
        candidate = float(Fraction(witness.candidate[0]))
        right.scatter([posterior], [curve.surprise], color=_TEAL, marker="*", s=70,
                      zorder=4, label="Exact posterior q*")
        right.scatter([candidate], [row.result.free_energy], facecolor="white",
                      edgecolor=_COPPER, marker="o", s=35, zorder=5, label="Candidate")
        right.set(xlim=(-0.035, 1.035), xticks=(0, 0.2, 0.4, 0.6, 0.8, 1),
                  xlabel="q(false) = q₀", ylabel="Energy (nats)")
        for ax in (left, right):
            ax.grid(axis="y", color="#dce4e5", linewidth=0.6)
            ax.set_axisbelow(True)
            ax.tick_params(labelsize=8)
            ax.title.set_fontsize(8)
            ax.xaxis.label.set_fontsize(8)
            ax.yaxis.label.set_fontsize(8)
    left_handles, left_labels = axes[0, 0].get_legend_handles_labels()
    handles, labels = axes[0, 1].get_legend_handles_labels()
    fig.legend([*left_handles, *handles], [*left_labels, *labels], loc="lower center",
               bbox_to_anchor=(0.53, 0.052), ncol=4, fontsize=7.5, frameon=False)
    return fig


def _control_figure(inputs: BridgeFigureInputs) -> Figure:
    from matplotlib.patches import Rectangle

    report = inputs.report
    height = max(175, 64 + 6 * len(report.scenarios))
    fig = _figure(inputs, height, "Native controls: actual observed statuses by scenario")
    ax = fig.add_axes((0.32, 0.27, 0.64, 0.60))
    columns = tuple((prover, kind) for prover in report.provers for kind in _KINDS)
    ax.set(xlim=(-0.5, len(columns) - 0.5), ylim=(len(report.scenarios) - 0.5, -0.5))
    ax.set_xticks(range(len(columns)),
                 [f"{prover.upper()}\n{kind.replace('-premise', '')}" for prover, kind in columns],
                 rotation=45, ha="left", fontsize=7.5)
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(report.scenarios)), [row.id for row in report.scenarios], fontsize=7.5)
    runs = {(row.group, row.prover, row.kind): row for row in report.cases}
    for y, scenario in enumerate(report.scenarios):
        for x, (prover, kind) in enumerate(columns):
            row = runs[(scenario.id, prover, kind)]
            label, color = _STATUSES.get(row.observed, (row.observed, "#efc9c9"))
            ax.add_patch(Rectangle((x - 0.48, y - 0.48), 0.96, 0.96,
                                   facecolor=color, edgecolor=_NAVY if row.matched else "#b42318",
                                   linewidth=0.5 if row.matched else 2))
            ax.text(x, y, label + ("" if row.matched else " !"), ha="center", va="center",
                    fontsize=7.5, color=_NAVY)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0)
    statuses = tuple(dict.fromkeys(row.observed for row in report.cases))
    legend = "\n".join("; ".join(f"{_STATUSES.get(status, (status, ''))[0]} = {status}"
                                 for status in statuses[i:i + 2]) for i in range(0, len(statuses), 2))
    backgrounds = [row for row in report.cases if row.kind == "background"]
    fig.text(0.045, 0.22, legend + "\nE = E theorem prover; V = Vampire. Red border / ! = mismatch.\n"
             "Removed = removed-premise control. Background credit requires the same family to be Satisfiable.\n"
             f"Matched {sum(row.matched for row in report.cases)}/{len(report.cases)}; "
             f"matched Satisfiable backgrounds {sum(row.matched and row.observed == 'Satisfiable' for row in backgrounds)}"
             f"/{len(backgrounds)}.\n"
             "Rows identify scenario selections, assumptions and generated queries in the companion explorer.\n"
             "Native observations apply to the selected first-order fragments; no whole-ontology consistency claim.",
             fontsize=8, va="top", color=_NAVY, linespacing=1.45)
    return fig


def _check_geometry(fig: Figure) -> None:
    """Reject clipped text at the final canvas resolution without shrinking it."""
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.text import Text

    canvas = FigureCanvasAgg(fig)
    canvas.draw()
    renderer = canvas.get_renderer()
    for artist in fig.findobj(Text):
        if artist.get_visible() and artist.get_text():
            bounds = artist.get_window_extent(renderer)
            if (bounds.x0 < -0.5 or bounds.y0 < -0.5
                    or bounds.x1 > fig.bbox.width + 0.5 or bounds.y1 > fig.bbox.height + 0.5):
                raise BridgeFigureError(f"Text exceeds figure bounds: {artist.get_text()!r}")
            if float(artist.get_fontsize()) < 7.5:
                raise BridgeFigureError("Print text must be at least 7.5 points")
    for index, left in enumerate(fig.texts):
        for right in fig.texts[index + 1:]:
            if left.get_window_extent(renderer).overlaps(right.get_window_extent(renderer)):
                raise BridgeFigureError("Figure text blocks overlap")


def render_bridge_figures(path: Path, output: Path, *, trusted_report_sha256: str,
                          dpi: int = 300, decimal_places: int = 6) -> tuple[Path, ...]:
    """Export three source-bound PNG/SVG figures, inputs and an offline explorer.

    The output directory must be new with an existing, symlink-free parent on
    the project's mounted GitVault storage. Failed exports remain for inspection.
    """
    parent = checked_source_path(output.parent)
    vault = next((ancestor for ancestor in Path(__file__).resolve().parents
                  if os.path.ismount(ancestor) and (ancestor / "Username").is_dir()), None)
    if vault is None or not parent.is_dir() or not parent.is_relative_to(vault):
        raise BridgeFigureError("Output parent must exist on mounted project storage")
    output = parent / output.name
    if output.exists() or output.is_symlink():
        raise FileExistsError("Bridge figure output directory must be new")
    data = build_bridge_figure_inputs(path, trusted_report_sha256=trusted_report_sha256,
                                      dpi=dpi, decimal_places=decimal_places)
    payload = data.model_dump_json(indent=2) + "\n"
    html = bridge_explorer_html(data)
    import matplotlib

    output.mkdir()
    paths: list[Path] = []
    with matplotlib.rc_context({"font.family": "DejaVu Sans", "text.usetex": False,
                                "text.parse_math": False, "svg.fonttype": "none",
                                "svg.hashsalt": data.report_sha256}):
        for name, render in (("bridge-evidence", _evidence_figure),
                             ("bridge-free-energy", _energy_figure),
                             ("bridge-native-controls", _control_figure)):
            fig = render(data)
            _check_geometry(fig)
            for extension in ("png", "svg"):
                target = output / f"{name}.{extension}"
                metadata: dict[str, str | None] = {
                    "Description": f"Verified bridge packet SHA-256 {data.report_sha256}"}
                if extension == "svg":
                    metadata["Date"] = None
                fig.savefig(target, dpi=dpi, metadata=metadata)
                paths.append(target)
            fig.clear()
    for name, contents in (("bridge-figure-inputs.json", payload), ("bridge-explorer.html", html)):
        target = output / name
        with target.open("x", encoding="utf-8") as stream:
            stream.write(contents)
        paths.append(target)
    return tuple(paths)

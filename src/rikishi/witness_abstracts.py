"""Source-bound research maps separating ontology, formal and numerical evidence."""

from __future__ import annotations

import json
from collections import Counter
from fractions import Fraction
from pathlib import Path
from typing import TYPE_CHECKING, Final

from rikishi.bridge_figures import BridgeFigureInputs, _check_geometry
from rikishi.publication_abstracts import ABSTRACT_NAMES
from rikishi.publication_witness_numbers import witness_base_numbers
from rikishi.witness_dynamics import sequential_conditioning

if TYPE_CHECKING:
    from matplotlib.figure import Figure

_INK: Final = "#193449"
_TEAL: Final = "#176b62"
_COPPER: Final = "#94542f"
_BLUE: Final = "#325e85"


def _base(inputs: BridgeFigureInputs, title: str, subtitle: str) -> Figure:
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    fig = Figure(figsize=(191.9 / 25.4, 205 / 25.4), facecolor="white")
    FigureCanvasAgg(fig)
    fig.text(.035, .975, title, size=15, weight="bold", color=_INK, va="top")
    _text(fig, .035, .935, subtitle)
    _text(fig, .035, .048, inputs.report.study_id + " | source + receipts: bridge-figure-inputs.json\n"
          "SHA-256 packet prefix: " + inputs.report_sha256[:16], size=9)
    return fig


def _text(fig: Figure, x: float, y: float, text: str, *, size: float = 9.5,
          color: str = _INK) -> None:
    fig.text(x, y, text, size=size, color=color, va="top", linespacing=1.25)


def _block(fig: Figure, y: float, title: str, body: str) -> None:
    fig.text(.035, y, title, size=10.5, weight="bold", color=_TEAL, va="top")
    _text(fig, .035, y - .029, body)


def _table(fig: Figure, bottom: float, height: float, labels: list[str],
           rows: list[list[str]], widths: list[float]) -> None:
    from matplotlib.transforms import Bbox

    ax = fig.add_axes((.035, bottom, .93, height))
    ax.axis("off")
    table = ax.table(cellText=rows, colLabels=labels, colWidths=widths,
                     cellLoc="left", bbox=Bbox.from_bounds(0, 0, 1, 1))
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    for (row, _), cell in table.get_celld().items():
        cell.set_edgecolor("#c9d3da")
        cell.set_facecolor("#e9f0f3" if row == 0 else "white")
        cell.set_text_props(color=_INK, weight="bold" if row == 0 else "normal")


def _source(inputs: BridgeFigureInputs) -> Figure:
    uniform = next(w for w in inputs.report.witnesses if w.id == "uniform-prior")
    numbers = witness_base_numbers(uniform)
    fig = _base(inputs, "From SUMO expressions to a finite witness",
                "SUMO = Suggested Upper Merged Ontology; FEP = Free Energy Principle.\n"
                "One authored interpretation; three independently checked kinds of consequence.")
    _block(fig, .875, "1  Source implication → existential agent → representation",
           "Merge.kif 5589–5592 (complete rule):\n"
           "(=> (representsInLanguage ?REP ?ENTITY ?LANGUAGE)\n"
           "      (exists (?AGENT) (representsForAgent ?REP ?ENTITY ?AGENT)))\n"
           "Merge.kif 5572–5574 (complete rule):\n"
           "(=> (representsForAgent ?REP ?ENTITY ?AGENT) (represents ?REP ?ENTITY))")
    scenario = next(s for s in inputs.report.scenarios if s.id == "uniform-prior-representation")
    fact = next(a for a in scenario.assumptions if a.startswith("(representsInLanguage"))
    _block(fig, .725, "2  Local premise + selected rules ⇒ a controlled first-order query",
           fact.replace(" BridgeUniformPriorModel", "\n     BridgeUniformPriorModel") + "\n"
           + scenario.query + "\n"
           "The existential agent is not identified with the named BridgeUniformPriorAgent.\n"
           "The reverse query exchanges model and representation; it is not entailed.")
    cases = [c for c in inputs.report.cases if c.group == scenario.id
             and c.prover == inputs.report.provers[0]]
    _table(fig, .516, .074, [inputs.report.provers[0].upper() + " prover / case", "Observed statuses, in case order"],
           [["Background / positive", " / ".join(c.observed for c in cases[:2])],
            ["Reverse / rule removed", " / ".join(c.observed for c in cases[2:4])],
            ["Negated consequence", cases[4].observed]], [.34, .66])
    _block(fig, .497, "3  Interpretation arrow := declared data, not a transported proof",
           "s,o : Bool; index order [false,true]; observe o=true. Set L(s)=K(s,true).\n"
           f"UniformPrior: p={numbers['PRIOR']}, L={numbers['LIKELIHOOD']}, q={numbers['CANDIDATE']}.\n"
           f"K(false,·)={numbers['KERNEL_FALSE']}; K(true,·)={numbers['KERNEL_TRUE']}: each row sums to one.\n"
           f"Joint pL={numbers['JOINT']}; evidence Z={numbers['EVIDENCE']}; posterior r={numbers['POSTERIOR']}.")
    _block(fig, .366, "4  Lean arrow := theorem application under typed hypotheses",
           "FEP.FiniteLaw Bool: nonnegative mass + sum_one.\n"
           "FEP.FiniteKernel Bool Bool: nonnegative mass + sum_one for each input.\n"
           "evidence_positive : 0 < predictive prior kernel true permits conditioning.\n"
           "posterior_mul_predictive gives r(s) × Z = p(s) × K(s,true).\n"
           f"Here: {numbers['RECONSTRUCTION_FALSE_PLAIN']} and "
           f"{numbers['RECONSTRUCTION_TRUE_PLAIN']}, for the two states.")
    _block(fig, .215, "5  Identity, measurement and falsification remain separate",
           "UniformPrior.posterior_reconstruction instantiates the reconstruction theorem.\n"
           "kl_nonnegative / kl_self / kl_decomposition concern real finite divergence.\n"
           f"Python + {inputs.study.decimal_precision}-digit Decimal evaluate shared inputs; floating residuals are retained.\n"
           "Wrong normalization, wrong posterior and admitted-proof controls must reject.")
    _text(fig, .035, .09, "No general SUMO → Lean preservation theorem; rational KIF labels are not arithmetic.",
          size=9, color=_COPPER)
    return fig


def _witness(inputs: BridgeFigureInputs) -> Figure:
    fig = _base(inputs, "Exact inputs, objectives and derived experiments",
                "U = uniform-prior; B = biased-prior; E = exact-candidate. State order [false,true].\n"
                "p = prior; L = K(·,true); q = candidate; Z = evidence; r = posterior. Logs are natural.")
    rows = []
    repeated = []
    for key, witness in zip("UBE", inputs.report.witnesses, strict=True):
        row = next(n for n in inputs.report.numerical if n.witness_id == witness.id)
        rows.append([key, ", ".join(witness.prior), ", ".join(witness.likelihood),
                     ", ".join(witness.candidate), row.evidence, ", ".join(row.exact_posterior)])
        weights = [Fraction(p) * Fraction(l) ** 2 for p, l in
                   zip(witness.prior, witness.likelihood, strict=True)]
        repeated.append(f"{key}: r₂(false)={weights[0] / sum(weights)}, Z₂={sum(weights)}")
    _table(fig, .752, .117, ["ID", "Prior p", "L", "Candidate q", "Z", "Posterior r"],
           rows, [.06, .19, .18, .20, .09, .28])
    uniform = inputs.report.numerical[0].result
    exact = inputs.report.numerical[2].result
    numbers = witness_base_numbers(inputs.report.witnesses[0])
    factor = Fraction(inputs.report.numerical[1].evidence) / Fraction(
        inputs.report.numerical[0].evidence)
    _block(fig, .731, "Registered one-observation calculation: exact rationals + checked numerics",
           "Z = Σₛ p(s)L(s) > 0; r(s) = p(s)L(s)/Z; surprise = −ln Z.\n"
           "F(q) = Σₛ q(s) ln[q(s)/(p(s)L(s))] = KL(q || r) − ln Z.\n"
           "KL(q || r) = crossEntropy(q,r) − entropy(q) ≥ 0; the minimum is at q=r.\n"
           f"U: F={uniform.free_energy:.6f} ≈ KL {uniform.kl_to_posterior:.6f} "
           f"+ surprise {uniform.surprise:.6f} nats (rounded).")
    ax = fig.add_axes((.13, .402, .80, .195))
    for key, curve, color, style in zip("UBE", inputs.curves, (_TEAL, _BLUE, _COPPER),
                                        ("-", "--", ":"), strict=True):
        ax.plot(curve.q, curve.free_energy, label=key, color=color, linewidth=1.8, linestyle=style)
    ax.set_xlabel("Candidate mass q(false)", fontsize=9)
    ax.set_ylabel("Free energy F / nats", fontsize=9)
    ax.tick_params(labelsize=9)
    ax.set_xlim(0, 1)
    ax.set_xticks((0, .25, .5, .75, 1))
    ax.legend(fontsize=9, frameon=False, ncol=3, loc="upper center")
    ax.grid(alpha=.2)
    _text(fig, .035, .329,
          f"U and B share r={numbers['POSTERIOR']}, hence identical KL curves at a common q.\n"
          f"Their F curves differ by ln({factor}); registered candidates q are different.")
    _block(fig, .268, "DERIVED experiments: mathematical consequences, not new Lean / ATP runs",
           "Repeat true twice, conditionally independent given s: r₂(s) ∝ p(s)L(s)².\n"
           + "; ".join(repeated[:2]) + ".\n" + repeated[2]
           + ". Z₂ is evidence for the two true observations.\n"
           "U and B agree after one observation but separate after two: r alone loses K.\n"
           "Symmetric observation noise η: Lη(s)=η+(1−2η)L(s), 0≤η≤1/2.\n"
           "At η=1/2 the observation is uninformative: Lη=1/2, Zη=1/2, rη=p.\n"
           "Erase the observation instead: marginalize ΣₒK(s,o)=1, so r=p and Z=1.")
    _text(fig, .035, .089,
          f"E floating KL={exact.kl_to_posterior:.2e} nats; real KL=0. Recorded roundoff is retained.",
          size=9, color=_COPPER)
    return fig


def _evidence(inputs: BridgeFigureInputs) -> Figure:
    report = inputs.report
    fig = _base(inputs, "Four roles, three evidence lanes, explicit limits",
                "Representation → model is a SUMO relation; calculation → result is a distinct relation.\n"
                "Shared identifiers bind provenance. They do not equate a term, a proof and a measurement.")
    _table(fig, .667, .21, ["Role / uniform-prior", "Ontology consequence", "Independent obligation"], [
        ["Representation\nBridgeUniformPriorLean", "represents the model\nfrom language + agent rules", "Lean source + digest;\nno reverse representation"],
        ["Model\nBridgeUniformPriorModel", "Proposition → Abstract\nvia authored bridge rule", "Exact p, K, q; normalization;\nmodel identity exceeds r"],
        ["Calculation\n…PriorCalculation", "Calculating → Process\nvia selected inheritance", "Replay command + inputs;\nno arithmetic from typing"],
        ["Result\n…PriorResult", "result excludes instrument\nvia local fixed-arity rule", "Validate posterior + values;\nrole alone is no certificate"],
    ], [.30, .35, .35])
    _block(fig, .648, "Existence does not name the numerical record (Merge.kif 16326–16331)",
           "(=> (instance ?DEVELOP ContentDevelopment)\n"
           "      (exists (?OBJ) (and (instance ?OBJ ContentBearingObject)\n"
           "                                  (result ?DEVELOP ?OBJ))))\n"
           "Local premise: (instance BridgeUniformPriorCalculation ContentDevelopment).\n"
           "Query ∃OBJ result(Calculation,OBJ): Theorem; named Result: CounterSatisfiable.\n"
           "The bridgeFiniteWitness label alone does not instantiate the local mapping rule.\n"
           "Adding that mapping is a different premise set; only then is the named result asserted.")
    counts = Counter(c.observed for c in report.cases)
    _block(fig, .455, "Recorded evidence: exact denominators from the replay-verified packet",
           f"{len(report.witnesses)} witnesses; {len(report.scenarios)} scenarios; {len(report.cases)} native cases; "
           f"{sum(c.matched for c in report.cases)} matched expected statuses.\n"
           + "; ".join(f"{k}: {v}" for k, v in sorted(counts.items())) + ".\n"
           f"{len(report.lean.declarations)} audited Lean declarations (definitions included); "
           f"{len(inputs.lean_proofs)} named theorem declarations.\n"
           f"{len(report.lean.environments)} paired Lean environments; "
           f"{sum(c.rejected for c in report.lean.controls)}/{len(report.lean.controls)} controls rejected.\n"
           f"{sum(n.passed for n in report.numerical)}/{len(report.numerical)} numerical rows passed; "
           f"exact rational posterior + {inputs.study.decimal_precision}-digit Decimal reference.")
    _block(fig, .303, "Counterexamples identify what the bridge does not preserve",
           "Model identity: U ≠ B despite equal one-step posteriors; prior and kernel differ.\n"
           "Evidence scaling: L′=cL gives Z′=cZ and unchanged r when 0<cL(s)≤1.\n"
           "Thus F′(q)=F(q)−ln c: the posterior alone does not determine evidence or energy.\n"
           "A KIF mass label is uninterpreted data; SUMO LogFn is binary, Real.log unary.\n"
           "No general translation proves arithmetic, logarithms or semantic preservation.")
    _block(fig, .169, "How to read the evidence",
           "Theorem = selected query entailed; CounterSatisfiable = a countermodel exists.\n"
           "Satisfiable backgrounds check the chosen fragment; Unsatisfiable refutations add ¬query.\n"
           "Source rules + local premises ⇒ role consequence; typed hypotheses ⇒ Lean theorem.\n"
           "DERIVED marks further algebra; no whole-SUMO consistency or new native proof claim.")
    return fig


def _check_contrasts(inputs: BridgeFigureInputs) -> None:
    """Reject inputs that would make the diagrams' qualitative statements false."""
    witnesses = inputs.report.witnesses
    if tuple(w.id for w in witnesses) != ("uniform-prior", "biased-prior", "exact-candidate"):
        raise ValueError("Graphical abstracts require their declared witness order")
    values = [witness_base_numbers(witness) for witness in witnesses]
    repeated = [sequential_conditioning(tuple(map(Fraction, w.prior)),
                                       tuple(map(Fraction, w.likelihood)), 2)[2].posterior
                for w in witnesses]
    if (values[0]["POSTERIOR"] != values[1]["POSTERIOR"]
            or repeated[0] == repeated[1]
            or values[0]["EVIDENCE"] == values[1]["EVIDENCE"]
            or values[0]["CANDIDATE"] == values[1]["CANDIDATE"]
            or values[2]["CANDIDATE"] != values[2]["POSTERIOR"]):
        raise ValueError("Graphical abstracts require their stated witness contrasts")


def render_witness_abstracts(inputs: BridgeFigureInputs, directory: Path) -> list[Path]:
    """Render three checked diagrams from an already replay-verified immutable bridge input."""
    import matplotlib

    names = [*(f"{name}.{suffix}" for name in ABSTRACT_NAMES for suffix in ("png", "svg")),
             "witness-abstracts.json"]
    if any((directory / name).exists() or (directory / name).is_symlink() for name in names):
        raise FileExistsError("Preserve existing graphical abstracts before rendering")
    _check_contrasts(inputs)
    directory.mkdir(parents=True, exist_ok=True)
    result: list[Path] = []
    with matplotlib.rc_context({"font.family": "DejaVu Sans", "svg.fonttype": "none",
                                "text.usetex": False, "text.parse_math": False,
                                "svg.hashsalt": inputs.report_sha256}):
        for name, render in zip(ABSTRACT_NAMES, (_source, _witness, _evidence), strict=True):
            fig = render(inputs)
            _check_geometry(fig)
            for suffix in ("png", "svg"):
                target = directory / f"{name}.{suffix}"
                metadata: dict[str, str | None] = {
                    "Description": f"Verified bridge packet SHA-256 {inputs.report_sha256}"}
                if suffix == "svg":
                    metadata["Date"] = None
                fig.savefig(target, dpi=inputs.dpi, metadata=metadata)
                result.append(target)
            fig.clear()
    payload = {"report_sha256": inputs.report_sha256, "study_id": inputs.report.study_id,
               "witnesses": [w.model_dump(mode="json") for w in inputs.report.witnesses],
               "source_claims": [c.model_dump(mode="json") for c in inputs.report.source_claims],
               "numerical": [n.model_dump(mode="json") for n in inputs.report.numerical],
               "width_mm": 191.9, "height_mm": 205, "dpi": inputs.dpi}
    target = directory / "witness-abstracts.json"
    with target.open("x") as stream:
        json.dump(payload, stream, indent=2, allow_nan=False)
        stream.write("\n")
    result.append(target)
    return result

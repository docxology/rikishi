from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from decimal import ROUND_DOWN, Context, localcontext
from fractions import Fraction
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from rikishi.bridge_models import BridgeReport
from rikishi.manuscript_provenance import CorpusMeasurement, ProvenanceError, hydrate_manuscript
from rikishi.ontology import OntologyIndex
from rikishi.publication_witness_numbers import _tex, witness_number_substitutions
from rikishi.witness_dynamics import WitnessDynamics, build_witness_dynamics
from rikishi.witness_research import WitnessResearch, build_witness_research

if TYPE_CHECKING:
    from conftest import BridgePacket

Inputs = tuple[BridgeReport, WitnessResearch, WitnessDynamics]


@pytest.fixture(scope="module")
def prose_inputs(bridge_packet: BridgePacket) -> Inputs:
    return (bridge_packet.report,
            build_witness_research(bridge_packet.report, bridge_packet.sha256),
            build_witness_dynamics(bridge_packet.report, bridge_packet.sha256))


def test_inline_values_reproduce_independent_exact_checkpoints(prose_inputs: Inputs) -> None:
    values = witness_number_substitutions(*prose_inputs, decimal_places=6)
    expected = {
        "NUM_UNIFORM_JOINT": "(1/8,3/8)", "NUM_UNIFORM_POSTERIOR": "(1/4,3/4)",
        "NUM_UNIFORM_PRIOR_ODDS": "1", "NUM_UNIFORM_LIKELIHOOD_RATIO": "3",
        "NUM_BIASED_PRIOR_ODDS": "2", "NUM_BIASED_LIKELIHOOD_RATIO": "3/2",
        "NUM_UNIFORM_COARSE_JOINT": "(3/16,5/16)",
        "NUM_UNIFORM_COARSE_POSTERIOR": "(3/8,5/8)",
        "NUM_EXACT_NOISY_POSTERIOR": "(21/26,5/26)",
        "NUM_UNIFORM_KL_BEFORE": "0.143841", "NUM_UNIFORM_KL_AFTER": "0.032269",
        "NUM_BAYES_FACTOR": "4/3", "NUM_BIASED_MODEL_POSTERIOR": "4/7",
        "NUM_BIASED_MODEL_POSTERIOR_STEP2": "22/37",
        "NUM_UNIFORM_STEP2_EVIDENCE": "5/16", "NUM_BIASED_STEP2_EVIDENCE": "11/24",
        "NUM_EXACT_STEP2_EVIDENCE": "13/36", "NUM_SIMULATION_TRIALS": "65,536",
        "NUM_SIMULATION_STEPS": "12", "NUM_RESEARCH_PRECISION": "100",
        "NUM_UNIFORM_RECONSTRUCTION_FALSE": r"\frac{1}{4}\times\frac{1}{2}=\frac{1}{8}",
    }
    assert {key: values[key] for key in expected} == expected


def test_changed_mathematical_inputs_change_prose_without_new_native_claims(
    prose_inputs: Inputs,
) -> None:
    # This pure mathematical mutation makes no claim to replay or execute its
    # parent report's native scenarios. It tests the formatter's input coupling.
    report, research, _ = prose_inputs
    uniform = report.witnesses[0].model_copy(update={"likelihood": ("1/8", "7/8")})
    changed = report.model_copy(update={"witnesses": (uniform, *report.witnesses[1:])})
    values = witness_number_substitutions(
        changed, build_witness_research(changed, research.report_sha256),
        build_witness_dynamics(changed, research.report_sha256), decimal_places=6)
    assert values["NUM_UNIFORM_JOINT"] == "(1/16,7/16)"
    assert values["NUM_UNIFORM_POSTERIOR"] == "(1/8,7/8)"
    assert values["NUM_UNIFORM_NEXT_PREDICTION"] == "25/32"
    assert values["NUM_UNIFORM_COARSE_JOINT"] == "(5/32,11/32)"


def test_manuscript_uses_only_resolvable_inline_number_tokens(
    prose_inputs: Inputs, project_root: Path, tmp_path: Path,
    corpus_factory: Callable[[Path, Mapping[str, str]], OntologyIndex],
    git_commit: Callable[[Path], str],
) -> None:
    source = (project_root / "manuscript/rikishi.md").read_text()
    required = set(re.findall(r"\{\{(NUM_[A-Z0-9_]+)\}\}", source))
    values = witness_number_substitutions(*prose_inputs, decimal_places=6)
    assert len(required) >= 40
    assert required <= values.keys()
    index = corpus_factory(tmp_path, {"Merge.kif": "(instance Witness Entity)\n"})
    git_commit(tmp_path / "source")
    index.build(tmp_path / "source")
    measurement = CorpusMeasurement.model_validate(index.stats())
    template = "Posterior ${{NUM_UNIFORM_POSTERIOR}}$."
    assert hydrate_manuscript(template, measurement, values=values).text == (
        "Posterior $(1/4,3/4)$.")
    # The actual hydrator must fail when a needed producer entry is removed.
    values.pop("NUM_UNIFORM_POSTERIOR")
    with pytest.raises(ProvenanceError, match="Unresolved manuscript substitutions"):
        hydrate_manuscript(template, measurement, values=values)


@pytest.mark.parametrize("places", [0, 4, 15])
def test_display_precision_does_not_inherit_callers_rounding(
    prose_inputs: Inputs, places: int,
) -> None:
    expected = witness_number_substitutions(*prose_inputs, decimal_places=places)
    with localcontext(Context(prec=3, rounding=ROUND_DOWN, Emax=5, Emin=-5)):
        assert witness_number_substitutions(*prose_inputs, decimal_places=places) == expected
    assert len(expected["NUM_UNIFORM_KL_AFTER"].split(".")[-1]) == (places or 1)


@pytest.mark.parametrize("places", [-1, 16, True, 1.5])
def test_invalid_display_precision_is_rejected(prose_inputs: Inputs, places: int) -> None:
    with pytest.raises(ValueError, match="integer from zero through fifteen"):
        witness_number_substitutions(*prose_inputs, decimal_places=places)


@pytest.mark.parametrize("mutation", ["identity", "binding", "channel", "step", "weight", "order"])
def test_incomplete_or_misjoined_payload_is_rejected(prose_inputs: Inputs, mutation: str) -> None:
    report, research, dynamics = prose_inputs
    match mutation:
        case "identity":
            report = report.model_copy(update={"witnesses": report.witnesses[:-1]})
        case "binding":
            research = research.model_copy(update={"report_sha256": "0" * 64})
        case "channel":
            research = research.model_copy(update={"channels": ()})
        case "step":
            first = dynamics.witnesses[0]
            changed = first.model_copy(update={"rows": first.rows[:2]})
            dynamics = dynamics.model_copy(update={"witnesses": (changed, *dynamics.witnesses[1:])})
        case "weight":
            dynamics = dynamics.model_copy(update={"model_weights": ()})
        case "order":
            first = dynamics.witnesses[0]
            row = first.rows[2].model_copy(update={"n": 3})
            changed = first.model_copy(update={"rows": (*first.rows[:2], row, *first.rows[3:])})
            dynamics = dynamics.model_copy(update={"witnesses": (changed, *dynamics.witnesses[1:])})
    with pytest.raises(ValueError, match="Numerical prose"):
        witness_number_substitutions(report, research, dynamics, decimal_places=6)


@pytest.mark.parametrize("value, expected", [(Fraction(2), "2"), (Fraction(0), "0"),
                                            (Fraction(3, 4), r"\frac{3}{4}")])
def test_exact_latex_products_keep_integer_and_fraction_semantics(
    value: Fraction, expected: str,
) -> None:
    assert _tex(value) == expected

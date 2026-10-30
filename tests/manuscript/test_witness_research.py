from __future__ import annotations

import json
import re
from decimal import ROUND_DOWN, Context, Decimal, localcontext
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from defusedxml import ElementTree
from PIL import Image

from rikishi.witness_research import (
    build_witness_research,
    research_tables,
    verify_witness_research,
)
from rikishi.witness_research_figures import RESEARCH_FIGURES, render_witness_research

if TYPE_CHECKING:
    from conftest import BridgePacket


def test_channel_analysis_preserves_conditioning_but_exposes_information_loss(
    bridge_packet: BridgePacket,
) -> None:
    # Given the actual three-witness packet, not newly asserted native cases.
    result = build_witness_research(bridge_packet.report, bridge_packet.sha256)
    # When the uniform case is passed through the shared noisy state channel.
    row = next(r for r in result.channels
               if r.witness_id == "uniform-prior" and r.channel_id == "noisy-quarter")
    # Then exact transformed joints and conditional posteriors agree independently.
    assert row.coarse_prior == ("1/2", "1/2")
    assert row.coarse_joint == ("3/16", "5/16")
    assert row.coarse_likelihood == ("3/8", "5/8")
    assert row.coarse_posterior == row.pushed_posterior == ("3/8", "5/8")
    with localcontext() as ctx:
        ctx.prec = 100
        assert abs(Decimal(row.kl_after) - (Decimal(16) / 15).ln() / 2) < Decimal("1e-95")
    assert Decimal(row.information_loss) > 0


def test_erasure_masks_wrong_candidate_without_improving_original_inference(
    bridge_packet: BridgePacket,
) -> None:
    result = build_witness_research(bridge_packet.report, bridge_packet.sha256)
    rows = [r for r in result.channels if r.channel_id == "erase-state"]
    assert len(rows) == 3
    assert all(r.coarse_candidate == r.coarse_posterior == ("1",) for r in rows)
    assert all(Decimal(r.kl_after) == 0 for r in rows)
    assert sum(Decimal(r.kl_before) > 0 for r in rows) == 2


def test_evidence_scaling_keeps_posterior_and_records_changed_observation_law(
    bridge_packet: BridgePacket,
) -> None:
    result = build_witness_research(bridge_packet.report, bridge_packet.sha256)
    row = next(r for r in result.scalings if r.witness_id == "uniform-prior")
    assert row.original_evidence == "1/2" and row.scaled_evidence == "1/4"
    assert row.original_posterior == row.scaled_posterior == ("1/4", "3/4")
    assert row.scaled_kernel == (("7/8", "1/8"), ("5/8", "3/8"))
    with localcontext() as ctx:
        ctx.prec = 100
        assert abs(Decimal(row.surprise_shift) - Decimal(2).ln()) < Decimal("1e-95")


def test_observation_noise_and_model_odds_have_distinct_exact_meanings(
    bridge_packet: BridgePacket,
) -> None:
    result = build_witness_research(bridge_packet.report, bridge_packet.sha256)
    assert [(r.noisy_evidence, r.noisy_posterior, r.repeated_true_prediction)
            for r in result.observations] == [
        ("1/2", ("3/8", "5/8"), "5/8"),
        ("7/12", ("2/7", "5/7"), "11/16"),
        ("13/24", ("21/26", "5/26"), "13/21"),
    ]
    assert result.biased_to_uniform_bayes_factor == "4/3"
    assert result.biased_model_posterior_equal_priors == "4/7"


def test_derived_evidence_is_independent_of_callers_decimal_context(
    bridge_packet: BridgePacket,
) -> None:
    original = build_witness_research(bridge_packet.report, bridge_packet.sha256)
    tables = research_tables(original)
    with localcontext(Context(prec=5, rounding=ROUND_DOWN, Emax=5, Emin=-5)):
        changed = build_witness_research(bridge_packet.report, bridge_packet.sha256)
        assert changed == original
        assert research_tables(changed) == tables


@pytest.mark.parametrize("mutation", ["posterior", "evidence", "report"])
def test_rebound_analysis_rejects_changed_mathematical_or_source_identity(
    bridge_packet: BridgePacket, mutation: str,
) -> None:
    data = build_witness_research(bridge_packet.report, bridge_packet.sha256)
    raw = data.model_dump(mode="json")
    match mutation:
        case "posterior":
            raw["channels"][0]["coarse_posterior"] = ["1/2", "1/2"]
        case "evidence":
            raw["scalings"][0]["scaled_evidence"] = "1/3"
        case "report":
            raw["report_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="Witness research differs"):
        verify_witness_research(json.dumps(raw).encode(), bridge_packet.report,
                                bridge_packet.sha256)


def test_actual_research_exports_bind_inputs_and_legible_geometry(
    bridge_packet: BridgePacket, tmp_path: Path,
) -> None:
    data = build_witness_research(bridge_packet.report, bridge_packet.sha256)
    outputs = render_witness_research(data, tmp_path)
    assert {p.name for p in outputs} == {
        *(f"{name}.{suffix}" for name in RESEARCH_FIGURES for suffix in ("png", "svg")),
        "witness-research.json",
    }
    verify_witness_research((tmp_path / "witness-research.json").read_bytes(),
                            bridge_packet.report, bridge_packet.sha256)
    for name in RESEARCH_FIGURES:
        svg = ElementTree.fromstring((tmp_path / f"{name}.svg").read_bytes())
        sizes = [float(n) for node in svg.findall(".//{http://www.w3.org/2000/svg}text")
                 for n in re.findall(r"font-size:\s*([\d.]+)px", node.get("style", ""))]
        assert sizes and min(sizes) >= 9
        with Image.open(tmp_path / f"{name}.png") as image:
            image.load()
            assert image.size == (2266, 2185)
            assert bridge_packet.sha256 in image.info["Description"]


def test_research_export_never_overwrites_existing_owner(
    bridge_packet: BridgePacket, tmp_path: Path,
) -> None:
    data = build_witness_research(bridge_packet.report, bridge_packet.sha256)
    target = tmp_path / "witness-research.json"
    target.write_bytes(b"prior owner")
    with pytest.raises(FileExistsError):
        render_witness_research(data, tmp_path)
    assert target.read_bytes() == b"prior owner"

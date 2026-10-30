from __future__ import annotations

import re
from fractions import Fraction
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pytest
from defusedxml import ElementTree
from PIL import Image

from rikishi.finite_channels import FiniteChannel, apply_channel, exact_bayes
from rikishi.witness_dynamics import (
    build_witness_dynamics,
    dynamics_table,
    sequential_conditioning,
    verify_witness_dynamics,
)
from rikishi.witness_dynamics_figures import render_witness_dynamics

if TYPE_CHECKING:
    from conftest import BridgePacket


def test_model_identity_remains_visible_without_color(bridge_packet: BridgePacket) -> None:
    from rikishi.witness_dynamics_figures import _draw

    data = build_witness_dynamics(bridge_packet.report, bridge_packet.sha256)
    figure = _draw(data)
    try:
        for axis in figure.axes[:3]:
            assert len({line.get_linestyle() for line in axis.lines}) == 3
        shapes = {np.asarray(collection.get_paths()[0].vertices, dtype=np.float64).tobytes()
                  for collection in figure.axes[2].collections}
        assert len(shapes) == 3
    finally:
        figure.clear()


def test_exact_checkpoints_when_conditioning_on_two_true_observations(
    bridge_packet: BridgePacket,
) -> None:
    # Given the original validated witnesses.
    report = bridge_packet.report
    # When repeated conditioning uses a persistent state.
    data = build_witness_dynamics(report, bridge_packet.sha256)
    # Then direct powers and iterative Bayes agree at all steps and these exact checkpoints.
    assert [(w.rows[2].cumulative_evidence, w.rows[2].posterior[0]) for w in data.witnesses] == [
        ("5/16", "1/10"), ("11/24", "2/11"), ("13/36", "12/13")]
    assert data.model_weights[:3] == ("1/2", "4/7", "22/37")
    for witness in data.witnesses:
        posterior = tuple(map(Fraction, witness.prior))
        cumulative = Fraction(1)
        for row in witness.rows:
            assert row.cumulative_evidence == str(cumulative)
            assert row.posterior == tuple(map(str, posterior))
            update = exact_bayes(posterior, tuple(map(Fraction, witness.likelihood)))
            assert row.next_predictive == str(update.evidence)
            posterior, cumulative = update.posterior, cumulative * update.evidence
    assert "5/16" in dynamics_table(data)


def test_persistent_state_differs_from_resampling_and_noisy_state_pushforward() -> None:
    # Given uniform prior, informative observations, and a noisy state channel.
    prior, likelihood = (Fraction(1, 2),) * 2, (Fraction(1, 4), Fraction(3, 4))
    noisy = FiniteChannel("noise", ((Fraction(3, 4), Fraction(1, 4)),
                                  (Fraction(1, 4), Fraction(3, 4))))
    # When a persistent state receives two true observations.
    rows = sequential_conditioning(prior, likelihood, 2)
    # Then resampling and naive repeated coarse conditioning are distinct experiments.
    assert Fraction(rows[2].cumulative_evidence) != exact_bayes(prior, likelihood).evidence ** 2
    coarse_likelihood = (Fraction(3, 8), Fraction(5, 8))
    naive = sequential_conditioning(apply_channel(prior, noisy), coarse_likelihood, 2)
    pushed = apply_channel(tuple(map(Fraction, rows[2].posterior)), noisy)
    assert pushed == (Fraction(3, 10), Fraction(7, 10))
    assert tuple(map(Fraction, naive[2].posterior)) == (Fraction(9, 34), Fraction(25, 34))
    assert pushed != tuple(map(Fraction, naive[2].posterior))


@pytest.mark.parametrize("steps", [-1, True])
def test_invalid_step_count_is_rejected(steps: int) -> None:
    # Given valid probabilities and an invalid sequence length.
    prior = (Fraction(1, 2),) * 2
    # When the public exact API is invoked, then it rejects the length.
    with pytest.raises(ValueError, match="nonnegative integer"):
        sequential_conditioning(prior, prior, steps)


def test_seeded_forward_simulation_is_repeatable_and_retains_integer_counts(
    bridge_packet: BridgePacket,
) -> None:
    # Given a fixed report, algorithm, seed and trial count.
    first = build_witness_dynamics(bridge_packet.report, bridge_packet.sha256)
    # When the complete simulation is independently rerun.
    second = build_witness_dynamics(bridge_packet.report, bridge_packet.sha256)
    # Then every retained observation is exactly reproducible, with no statistical pass threshold.
    assert first == second
    assert [(w.rows[2].success_count, w.rows[2].false_count,
             w.rows[12].success_count, w.rows[12].false_count) for w in first.witnesses] == [
        (20645, 2105, 983, 0), (30123, 5562, 1417, 5), (23749, 21914, 395, 394)]
    for witness in first.witnesses:
        assert witness.rows[0].success_count == first.trials
        for row in witness.rows:
            assert 0 <= row.false_count <= row.success_count <= first.trials
            assert row.simulated_evidence == str(Fraction(row.success_count, first.trials))
            assert row.simulated_posterior_false == (
                str(Fraction(row.false_count, row.success_count)) if row.success_count else None)
        assert all(a.success_count >= b.success_count and a.false_count >= b.false_count
                   for a, b in zip(witness.rows, witness.rows[1:]))


@pytest.mark.parametrize("field", ["exact", "counts", "seed", "weight", "report"])
def test_real_json_tampering_is_rejected(
    bridge_packet: BridgePacket, tmp_path: Path, field: str,
) -> None:
    # Given a genuine payload and an explicit alteration of one retained field.
    data = build_witness_dynamics(bridge_packet.report, bridge_packet.sha256)
    raw = data.model_dump_json()
    replacements = {
        "exact": ('"cumulative_evidence":"5/16"', '"cumulative_evidence":"1/4"'),
        "counts": ('"success_count":65536', '"success_count":65535'),
        "seed": ('"simulation_seed":20261026', '"simulation_seed":20261027'),
        "weight": ('"22/37"', '"1/2"'),
        "report": (bridge_packet.sha256, "0" * 64),
    }
    old, new = replacements[field]
    assert old in raw
    path = tmp_path / "altered.json"
    path.write_text(raw.replace(old, new, 1))
    # When recomputation reads the real altered JSON, then it rejects that artifact.
    with pytest.raises(ValueError, match="differs"):
        verify_witness_dynamics(path.read_bytes(), bridge_packet.report, bridge_packet.sha256)


def test_full_size_export_has_actual_nine_point_svg_text(
    bridge_packet: BridgePacket, tmp_path: Path,
) -> None:
    # Given a report-derived trajectory.
    data = build_witness_dynamics(bridge_packet.report, bridge_packet.sha256)
    # When all three publication artifacts are exported.
    png, svg, payload = render_witness_dynamics(data, tmp_path)
    # Then raster geometry, editable vector text, font floor and JSON recomputation agree.
    with Image.open(png) as image:
        assert image.size == (2266, 2421)
        assert image.info["Description"].endswith(bridge_packet.sha256)
    tree = ElementTree.fromstring(svg.read_bytes())
    texts = list(tree.iter("{http://www.w3.org/2000/svg}text"))
    assert len(texts) >= 30
    sizes = [float(value) for text in texts
             for value in re.findall(r"(?:font-size:\s*|font:\s*)([\d.]+)px", text.get("style", ""))]
    assert len(sizes) == len(texts) and min(sizes) >= 9
    verify_witness_dynamics(payload.read_bytes(), bridge_packet.report, bridge_packet.sha256)


@pytest.mark.parametrize("target", ["witness-sequential.png", "witness-sequential.svg", "witness-dynamics.json"])
def test_export_preserves_existing_owner_files(
    bridge_packet: BridgePacket, tmp_path: Path, target: str,
) -> None:
    # Given an existing owner's export path.
    data = build_witness_dynamics(bridge_packet.report, bridge_packet.sha256)
    path = tmp_path / target
    path.write_bytes(b"prior owner")
    # When export is attempted, then refusal preserves the owner and creates nothing else.
    with pytest.raises(FileExistsError):
        render_witness_dynamics(data, tmp_path)
    assert path.read_bytes() == b"prior owner"
    assert list(tmp_path.iterdir()) == [path]

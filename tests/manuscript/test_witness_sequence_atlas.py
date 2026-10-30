from __future__ import annotations

import json
from fractions import Fraction
from itertools import product
from pathlib import Path
from xml.etree import ElementTree as XML

import pytest
from defusedxml import ElementTree
from PIL import Image

from rikishi.bridge_study import catalog
from rikishi.finite_channels import FiniteChannelError
from rikishi.witness_sequence_atlas import (
    build_sequence_atlas,
    render_sequence_atlas,
    sequence_atlas_table,
    verify_sequence_atlas,
    verify_sequence_atlas_svg,
)


def test_every_observation_history_matches_independent_joint_enumeration() -> None:
    # Given the registered inputs, without executing any native campaign.
    witnesses = catalog().witnesses
    # When all eight three-observation histories are enumerated.
    data = build_sequence_atlas(witnesses, "a" * 64)
    # Then direct joint products independently recover every retained quantity.
    assert len(data.rows) == 24
    for witness in witnesses:
        prior = tuple(map(Fraction, witness.prior))
        likelihood = tuple(map(Fraction, witness.likelihood))
        rows = [row for row in data.rows if row.witness_id == witness.id]
        assert sum((Fraction(row.evidence) for row in rows), Fraction(0)) == 1
        for observations, row in zip(product((False, True), repeat=3), rows, strict=True):
            joint = list(prior)
            redrawn = Fraction(1)
            for observed in observations:
                weights = likelihood if observed else tuple(1 - p for p in likelihood)
                joint = [j * p for j, p in zip(joint, weights, strict=True)]
                redrawn *= sum((p * k for p, k in zip(prior, weights, strict=True)), Fraction(0))
            evidence = sum(joint)
            posterior = joint[0] / evidence
            predictive = sum((j * k for j, k in zip(joint, likelihood, strict=True))) / evidence
            assert row.pattern == "".join("T" if value else "F" for value in observations)
            assert tuple(map(Fraction, (row.evidence, row.posterior_false,
                                        row.next_true, row.redrawn_evidence))) == (
                evidence, posterior, predictive, redrawn)


def test_model_weight_and_exchangeability_have_distinct_denominators() -> None:
    # Given equal prior model weights, not state probabilities.
    data = build_sequence_atlas(catalog().witnesses, "b" * 64)
    rows = {(row.witness_id, row.pattern): row for row in data.rows}
    # When comparing ordered histories with the same number of true outcomes.
    histories = ("FTT", "TFT", "TTF")
    # Then final answers coincide within each persistent-state model.
    for witness in catalog().witnesses:
        assert len({rows[witness.id, h].evidence for h in histories}) == 1
        assert len({rows[witness.id, h].posterior_false for h in histories}) == 1
    for pattern, weight in zip(data.patterns, data.biased_model_weights, strict=True):
        u = Fraction(rows["uniform-prior", pattern].evidence)
        b = Fraction(rows["biased-prior", pattern].evidence)
        assert Fraction(weight) == b / (u + b)
    uniform = rows["uniform-prior", "TTT"]
    assert Fraction(uniform.evidence) != Fraction(uniform.redrawn_evidence)
    assert len(sequence_atlas_table(data).splitlines()) == 5


@pytest.mark.parametrize("field", ["evidence", "posterior_false", "next_true", "redrawn_evidence"])
def test_changed_payload_is_rejected_after_rebinding_json(field: str) -> None:
    # Given genuine source-derived data with one numerically changed cell.
    witnesses = catalog().witnesses
    data = build_sequence_atlas(witnesses, "c" * 64)
    changed = json.loads(data.model_dump_json())
    changed["rows"][0][field] = "1/7"
    # When the actual verifier rederives the model, then changed JSON cannot pass.
    with pytest.raises(FiniteChannelError, match="differs"):
        verify_sequence_atlas(json.dumps(changed).encode(), witnesses, "c" * 64)


def test_export_retains_exact_inputs_and_legible_vector_text(tmp_path: Path) -> None:
    # Given the complete portable authority and unused artifact paths.
    witnesses = catalog().witnesses
    data = build_sequence_atlas(witnesses, "d" * 64)
    # When producing actual PNG, SVG and JSON.
    paths = render_sequence_atlas(data, tmp_path / "atlas")
    # Then the image, literal labels and verifier share the same complete data.
    with Image.open(paths[0]) as image:
        image.load()
        assert image.size == (2266, 2421)
        assert image.info["Description"].endswith("d" * 64)
    svg = ElementTree.fromstring(paths[1].read_bytes())
    labels = list(svg.iter("{http://www.w3.org/2000/svg}text"))
    assert len(labels) >= 90
    sizes = [float(part.split(":", 1)[1].strip().removesuffix("px"))
             for node in labels for part in node.attrib.get("style", "").split(";")
             if part.strip().startswith("font-size:")]
    assert sizes and min(sizes) >= 9
    verify_sequence_atlas(paths[2].read_bytes(), witnesses, "d" * 64)
    verify_sequence_atlas_svg(paths[1].read_bytes(), data)
    cell = svg.find(".//*[@id='sequence-cell-evidence-uniform-prior-FFF']")
    assert cell is not None
    label = cell.find("{http://www.w3.org/2000/svg}text")
    assert label is not None
    assert label.text == "7/32"
    label.text = "1/7"
    with pytest.raises(FiniteChannelError, match="plotted values differ"):
        verify_sequence_atlas_svg(XML.tostring(svg), data)
    label.text = "7/32"
    cell.append(XML.fromstring(XML.tostring(label)))
    with pytest.raises(FiniteChannelError, match="ambiguous"):
        verify_sequence_atlas_svg(XML.tostring(svg), data)
    before = [path.read_bytes() for path in paths]
    with pytest.raises(FileExistsError):
        render_sequence_atlas(data, paths[0].parent)
    assert [path.read_bytes() for path in paths] == before


def test_atlas_binding_and_witness_identity_are_mandatory() -> None:
    # Given an incomplete source-witness population.
    witnesses = catalog().witnesses
    # When trying to label it as the complete atlas, then it must reject.
    with pytest.raises(FiniteChannelError, match="three registered"):
        build_sequence_atlas(witnesses[:2], "e" * 64)

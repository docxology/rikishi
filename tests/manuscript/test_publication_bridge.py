from __future__ import annotations

import re
from fractions import Fraction
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from rikishi.manuscript_provenance import ProvenanceError
from rikishi.publication_bridge import load_bridge_context, verify_bridge_content
from rikishi.runtime_artifacts import ArtifactError

if TYPE_CHECKING:
    from conftest import BridgePacket


@pytest.mark.integration
def test_calculation_description_follows_every_actual_selected_source_kernel(
    bridge_packet: BridgePacket,
) -> None:
    report = bridge_packet.report
    source = (Path(__file__).resolve().parents[2] / "manuscript/rikishi.md").read_text()
    paragraph = source.split("The calculation chain is equally specific.", 1)[1].split(
        "The positive query", 1)[0]
    described = re.findall(r"`([^`]+)`", paragraph)
    claims = {claim.line: claim.raw_kif for claim in report.source_claims}
    assert len(claims) == len(report.source_claims)
    calculations = [scenario for scenario in report.scenarios if scenario.role == "calculation"]
    assert {scenario.witness_id for scenario in calculations} == {w.id for w in report.witnesses}
    assert len(calculations) == len(report.witnesses)
    for scenario in calculations:
        edges: dict[str, str] = {}
        for selection in scenario.selections:
            assert not selection.predicate_bindings
            match = re.fullmatch(r"\(subclass (\w+) (\w+)\)", claims[selection.line])
            if match:
                child, parent = match.groups()
                assert child not in edges
                edges[child] = parent
        selected_path = ["Calculating"]
        while selected_path[-1] in edges:
            parent = edges[selected_path[-1]]
            assert parent not in selected_path
            selected_path.append(parent)
        assert selected_path[-1] == "Process"
        assert len(selected_path) == len(edges) + 1
        assert described == selected_path, scenario.id


@pytest.mark.parametrize("places", [-1, 16, True, 2.5, "6"])
def test_bridge_publication_rejects_invalid_precision(tmp_path, places):
    with pytest.raises(ValueError, match="integer from zero through fifteen"):
        load_bridge_context(tmp_path, decimal_places=places)


def test_bridge_publication_requires_an_actual_packet(tmp_path):
    with pytest.raises(ArtifactError, match="cannot read evidence"):
        load_bridge_context(tmp_path, decimal_places=6)


@pytest.mark.integration
def test_bridge_publication_uses_actual_outcomes_and_false_true_order(bridge_packet):
    context = load_bridge_context(bridge_packet.path.parent, decimal_places=6)
    report = bridge_packet.report
    assert context.report == report
    assert context.input_sha256 == {"bridge-report.json": bridge_packet.sha256}
    assert context.values["BRIDGE_NATIVE_RUNS"] == str(len(report.cases))
    assert context.values["BRIDGE_WITNESSES"] == str(len(report.witnesses))
    assert context.values["BRIDGE_SCENARIOS"] == str(len(report.scenarios))
    assert context.values["BRIDGE_LEAN_DECLARATIONS"] == str(len(report.lean.declarations))
    table = context.values["BRIDGE_SUMMARY_TABLE"]
    assert "Posterior (false, true)" in table
    assert "Posterior (true, false)" not in table
    rows = table.splitlines()[2:]
    for witness, numerical, row in zip(report.witnesses, report.numerical, rows, strict=True):
        assert witness.id == numerical.witness_id
        cells = [cell.strip() for cell in row.strip("|").split("|")]
        prior = tuple(Fraction(value) for value in witness.prior)
        likelihood = tuple(Fraction(value) for value in witness.likelihood)
        joint = tuple(p * l for p, l in zip(prior, likelihood, strict=True))
        posterior = tuple(value / sum(joint) for value in joint)
        assert cells[1] == "(" + ", ".join(str(value) for value in posterior) + ")"
        groups = {scenario.id for scenario in report.scenarios if scenario.witness_id == witness.id}
        cases = [case for case in report.cases if case.group in groups]
        assert cells[-1] == f"{sum(case.matched for case in cases)}/{len(cases)}"
        if numerical.result.kl_to_posterior != 0 and abs(numerical.result.kl_to_posterior) < 0.0000005:
            assert "e" in cells[3]
            assert float(cells[3]) == pytest.approx(numerical.result.kl_to_posterior, rel=0.000001, abs=0)
            assert cells[3] not in {"0.000000", "-0.000000"}
    exact_rows = context.values["BRIDGE_EXACT_TABLE"].splitlines()[2:]
    for witness, row in zip(report.witnesses, exact_rows, strict=True):
        cells = [cell.strip() for cell in row.strip("|").split("|")]
        joint = tuple(Fraction(p) * Fraction(k)
                      for p, k in zip(witness.prior, witness.likelihood, strict=True))
        assert cells[3] == "(" + ", ".join(str(j) for j in joint) + ")"
        assert Fraction(cells[4]) == sum(joint)
    derived_rows = [line for key in ("WITNESS_CHANNEL_TABLE", "WITNESS_SCALING_TABLE",
                                    "WITNESS_SEQUENTIAL_TABLE", "WITNESS_SEQUENCE_ATLAS_TABLE")
                    for line in context.values[key].splitlines()[2:]]
    actual_cells = "\n".join(" ".join(line.strip("|").split("|"))
                             for line in rows + exact_rows + derived_rows)
    verify_bridge_content(actual_cells, context, "retained table cells")
    with pytest.raises(ProvenanceError, match="Bridge result row missing"):
        verify_bridge_content("\n".join(" ".join(line.strip("|").split("|"))
                                      for line in rows + exact_rows),
                              context, "missing derived channel/scaling rows")
    with pytest.raises(ProvenanceError, match="Bridge result row missing"):
        verify_bridge_content(actual_cells.replace(rows[0].split("|")[1].strip(), "altered-witness"),
                              context, "altered table cells")
    with pytest.raises(ProvenanceError, match="Bridge result row missing"):
        verify_bridge_content(actual_cells.replace("1/8", "1/9"), context, "wrong exact joint")
    with pytest.raises(ProvenanceError, match="Bridge result row missing"):
        verify_bridge_content(actual_cells.replace("5/16", "1/4"), context,
                              "redrawn-state evidence substituted for persistent-state evidence")

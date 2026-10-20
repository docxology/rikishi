import json
from pathlib import Path

import pytest

from rikishi.kif import parse
from rikishi.ontology import OntologyIndex
from rikishi.projection import taxonomy_problem
from rikishi.runtime import prove


@pytest.mark.integration
def test_real_taxonomy_projection_and_countermodel(tmp_path):
    source = tmp_path / "sumo"
    source.mkdir()
    (source / "Merge.kif").write_text(
        "(subclass Human CognitiveAgent)\n(subclass CognitiveAgent Agent)\n(instance Rock Class)"
    )
    (source / "excluded.kif").write_text("(subclass Human Rock)")
    index = OntologyIndex(tmp_path / "index.sqlite")
    index.build(source)
    output = tmp_path / "proof.p"
    metadata = taxonomy_problem(index, "Human", "Agent", output)
    assert len(metadata["assertions"]) == 2
    assert len(metadata["source_file_sha256"]) == 64
    assert metadata["source_clean"] is None
    assert metadata["assertions"][0]["line"] == 1
    assert json.loads(output.with_suffix(".json").read_text())["subject"] == "Human"
    root = Path(__file__).resolve().parents[1]
    assert prove(output, root)["status"] == "Theorem"
    taxonomy_problem(index, "Human", "Rock", output)
    assert prove(output, root)["status"] == "CounterSatisfiable"
    with pytest.raises(ValueError):
        taxonomy_problem(index, "Human", "Rock", output, source="absent.kif")
    with pytest.raises(KeyError):
        taxonomy_problem(index, "MissingTerm", "Rock", output)


def test_research_extension_is_structurally_valid():
    root = Path(__file__).resolve().parents[1]
    formulas = list(parse((root / "examples/fep-ontology.kif").read_text()))
    expressions = [formula.expression for formula in formulas]
    assert ("subclass", "RikishiVariationalInference", "Reasoning") in expressions
    assert (
        "instance",
        "RikishiBinaryInferenceExample",
        "RikishiVariationalInference",
    ) in expressions

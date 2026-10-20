import hashlib
import json

import pytest

from rikishi.projection import taxonomy_problem


def test_projection_keeps_selected_source_and_exact_problem_hash(tmp_path, corpus_factory):
    index = corpus_factory(tmp_path, {
        "Merge.kif": "(subclass Human Animal)\n(subclass Animal Entity)",
        "other.kif": "(subclass Human Rock)",
    })
    output = tmp_path / "experiment/taxonomy.p"
    manifest = taxonomy_problem(index, "Human", "Entity", output)
    assert len(manifest["assertions"]) == 2
    assert {row["path"] for row in manifest["assertions"]} == {"Merge.kif"}
    assert manifest["problem_sha256"] == hashlib.sha256(output.read_bytes()).hexdigest()
    assert manifest["source_file_sha256"] == hashlib.sha256(
        (tmp_path / "source/Merge.kif").read_bytes()).hexdigest()
    assert "subclass(s_48756d616e,s_416e696d616c)" in output.read_text()
    assert json.loads(output.with_suffix(".json").read_text()) == manifest


def test_invalid_projection_inputs_preserve_existing_problem(tmp_path, corpus_factory):
    index = corpus_factory(tmp_path, {"Merge.kif": "(instance Ada Human)"})
    output = tmp_path / "experiment.p"
    output.write_text("Prior experiment retained")
    with pytest.raises(ValueError, match="No asserted subclass"):
        taxonomy_problem(index, "Ada", "Human", output)
    with pytest.raises(KeyError):
        taxonomy_problem(index, "Missing", "Human", output)
    assert output.read_text() == "Prior experiment retained"

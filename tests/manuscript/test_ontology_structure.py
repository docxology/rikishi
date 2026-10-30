import json
from hashlib import sha256

import pytest
from defusedxml import ElementTree
from PIL import Image

from rikishi.ontology_figures import render_ontology_structure
from rikishi.ontology_observations import (
    StructureReport,
    measure_source_structure,
    structure_substitutions,
)
from rikishi.sumo_demonstrations import FrozenSource

SOURCE = """(subclass A B)
(subclass B C)
(subclass A B)
(subclass A C)
(subclass X Y)
(subclass Y X)
(subrelation p q)
(subrelation q q)
(=> (instance ?X A) (subclass Nested Hidden))
"""


def frozen(text=SOURCE):
    return FrozenSource(path="retained/Merge.kif", ontology_path="Merge.kif",
                        text=text, sha256=sha256(text.encode()).hexdigest(),
                        commit="unversioned", clean=None)


def test_source_taxonomies_retain_distinct_populations_and_replay():
    source = frozen()
    report = measure_source_structure(source)
    subclass, subrelation = report.graphs
    assert subclass.model_dump() == {
        "relation": "subclass", "assertion_count": 6, "unique_edges": 5, "node_count": 5,
        "root_count": 1, "multiple_parent_count": 1, "weak_component_count": 2,
        "cyclic_component_count": 1, "cyclic_node_count": 2, "self_loop_count": 0,
    }
    assert subrelation.node_count == 2
    assert subrelation.cyclic_component_count == subrelation.cyclic_node_count == 1
    assert subrelation.self_loop_count == 1
    assert report.source_sha256 == source.sha256
    assert StructureReport.model_validate_json(report.model_dump_json()) == report
    assert "| `subclass` | 6 | 5 | 5 | 1 | 1 |" in structure_substitutions(report)[
        "ONTOLOGY_STRUCTURE_TABLE"]
    changed = measure_source_structure(frozen(SOURCE + "(subclass C A)\n"))
    assert changed.graphs[0].root_count == 0
    assert changed.graphs[0].cyclic_node_count == 5


@pytest.mark.parametrize("text,corrupt_hash,message", [
    (SOURCE, True, "SHA-256 differs"),
    ("(unclosed", False, "parse errors"),
])
def test_invalid_retained_source_is_rejected(text, corrupt_hash, message):
    source = frozen(text)
    if corrupt_hash:
        source = source.model_copy(update={"sha256": "0" * 64})
    with pytest.raises(ValueError, match=message):
        measure_source_structure(source)


@pytest.mark.parametrize("text", [SOURCE, "; valid empty source\n"])
@pytest.mark.parametrize("dpi", [100, 150, 300])
def test_real_figures_preserve_checked_values_and_source_metadata(tmp_path, text, dpi):
    source = frozen(text)
    report = measure_source_structure(source)
    paths = render_ontology_structure(tmp_path / "figures", source, report, dpi=dpi)
    assert [p.name for p in paths] == [
        "ontology-structure.png", "ontology-structure.svg", "ontology-structure.json",
    ]
    data = json.loads(paths[2].read_text())
    assert data["report"] == report.model_dump(mode="json")
    with Image.open(paths[0]) as image:
        assert image.size == (int(174 / 25.4 * dpi), int(148 / 25.4 * dpi))
        assert json.loads(image.info["Description"]) == report.model_dump(mode="json")
    root = ElementTree.parse(paths[1]).getroot()
    assert root is not None
    labels = " ".join(root.itertext())
    assert source.sha256 in labels
    assert "Cycles do not certify inconsistency" in labels
    assert "subclass" in labels and "subrelation" in labels
    assert not any(e.tag.endswith("}image") for e in root.iter())


@pytest.mark.parametrize("dpi", [True, 0, 71, 1201])
def test_invalid_resolution_rejects_before_output_creation(tmp_path, dpi):
    source = frozen()
    with pytest.raises(ValueError, match="dpi"):
        render_ontology_structure(tmp_path / "absent", source, measure_source_structure(source), dpi=dpi)
    assert not (tmp_path / "absent").exists()


def test_false_counts_reject_before_output_creation(tmp_path):
    source = frozen()
    report = measure_source_structure(source)
    changed = report.model_copy(update={"graphs": [
        report.graphs[0].model_copy(update={"unique_edges": 999}), report.graphs[1],
    ]})
    with pytest.raises(ValueError, match="differs from retained source"):
        render_ontology_structure(tmp_path / "absent", source, changed, dpi=100)
    assert not (tmp_path / "absent").exists()

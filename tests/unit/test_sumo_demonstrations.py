import json
import sqlite3
import subprocess
import sys
import uuid
from hashlib import sha256

import pytest

from rikishi.kif import KifError, parse
from rikishi.ontology import OntologyIndex
from rikishi.runtime_artifacts import ArtifactError
from rikishi.sumo_demonstrations import (
    demonstrate_sumo,
    prove_sumo_taxonomy,
    report_to_substitutions,
    validate_sumo_report,
)

SOURCE = """; deliberately relocated line positions
(partition Entity Physical Abstract)
(subclass Physical Entity)
(subclass Abstract Entity)
(subclass Process Physical)
(subclass Proposition Abstract)
(instance agent CaseRole)
(instance ProbabilityFn UnaryFunction)
(domain agent 1 Process)
(domain agent 2 AutonomousAgent)
(domain ProbabilityFn 1 Formula)
(range ProbabilityFn RealNumber)
(=>
  (instance ?AGENT AutonomousAgent)
  (modalAttribute
    (exists (?PROC)
      (and
        (instance ?PROC Process)
        (agent ?PROC ?AGENT)))
    Possibility))
"""


@pytest.fixture
def indexed(tmp_path, corpus_factory):
    return corpus_factory(tmp_path, {"Merge.kif": SOURCE})


def test_live_report_preserves_real_parser_context_and_projection(indexed, tmp_path):
    report = demonstrate_sumo(indexed, tmp_path)
    formulas = list(parse(SOURCE))
    assert report.observations.source_formulas == len(formulas)
    assert report.observations.cited_formulas == len(formulas)
    assert report.observations.projected_binary_edges == 7
    assert report.source.path == "source/Merge.kif"
    assert report.source.sha256 == sha256(SOURCE.encode()).hexdigest()
    nested = report.cases["nested_formula"][0]
    assert nested.raw_kif == formulas[-1].text
    assert nested.line == formulas[-1].line
    assert nested.end_line == len(SOURCE.splitlines())
    assert nested.indexed_binary_edge is False
    assert all(not c.indexed_binary_edge for c in report.cases["agent_signature"])
    assert report.cases["probability_signature"][-1].indexed_binary_edge is True
    assert {c.predicate for c in report.cases["typing"]} == {"instance", "subclass"}
    assert indexed.neighborhood("Process", relation="agent")["total_edges"] == 0
    assert "(agent ?PROC ?AGENT)" in nested.raw_kif


def test_portable_replay_works_after_original_files_move(indexed, tmp_path):
    report = demonstrate_sumo(indexed, tmp_path)
    frozen = json.loads(report.model_dump_json())
    (tmp_path / "source").rename(tmp_path / "relocated-source")
    indexed.path.rename(tmp_path / "relocated.sqlite")
    assert validate_sumo_report(frozen) == report
    values = report_to_substitutions(frozen)
    assert "(subclass Process Physical)" in values["SUMO_HIERARCHY_KIF"]
    assert values["SUMO_NESTED_FORMULA_KIF"] == report.cases["nested_formula"][0].raw_kif
    assert values["SUMO_SOURCE_FORMULAS"] == str(len(list(parse(SOURCE))))
    assert "ATP proof" in report.scope
    assert "proof" not in frozen


@pytest.mark.parametrize("field,value", [
    ("line", 99), ("end_line", 99), ("raw_kif", "(subclass Process Abstract)"),
    ("sha256", "0" * 64), ("indexed_binary_edge", True), ("selected_terms", ["Abstract"]),
    ("predicate", "subclass"),
])
def test_portable_replay_rejects_tampered_citation(indexed, tmp_path, field, value):
    frozen = demonstrate_sumo(indexed, tmp_path).model_dump()
    frozen["cases"]["nested_formula"][0][field] = value
    with pytest.raises(ValueError, match="rederived"):
        report_to_substitutions(frozen)


@pytest.mark.parametrize("section,field,value", [
    ("source", "text", SOURCE + "\n"), ("source", "sha256", "0" * 64),
    ("source", "path", "/absolute/Merge.kif"), ("source", "path", "../Merge.kif"),
    ("source", "path", "source//Merge.kif"), ("source", "path", "other.kif"),
    ("source", "commit", "stale-revision"),
    ("observations", "source_formulas", 999), ("observations", "cited_formulas", 999),
    ("observations", "projected_binary_edges", 999),
])
def test_portable_replay_rejects_false_receipt(indexed, tmp_path, section, field, value):
    frozen = demonstrate_sumo(indexed, tmp_path).model_dump()
    frozen[section][field] = value
    with pytest.raises(ValueError):
        validate_sumo_report(frozen)


def test_portable_replay_rejects_rehashed_malformed_source(indexed, tmp_path):
    frozen = demonstrate_sumo(indexed, tmp_path).model_dump()
    text = SOURCE + "(unclosed"
    frozen["source"].update(text=text, sha256=sha256(text.encode()).hexdigest())
    with pytest.raises(KifError, match="unclosed"):
        validate_sumo_report(frozen)


@pytest.mark.parametrize("mutation", ["scope", "terms", "case", "extra", "missing", "schema"])
def test_portable_replay_rejects_changed_report_shape(indexed, tmp_path, mutation):
    frozen = demonstrate_sumo(indexed, tmp_path).model_dump()
    match mutation:
        case "scope":
            frozen["scope"] = "Full SUMO proof"
        case "terms":
            frozen["selected_terms"] = ["Human"]
        case "case":
            frozen["cases"].pop("hierarchy")
        case "extra":
            frozen["proof"] = "Theorem"
        case "missing":
            frozen.pop("source")
        case "schema":
            frozen["schema_version"] = 2
    with pytest.raises(ValueError):
        validate_sumo_report(frozen)


@pytest.mark.parametrize("change", ["modified", "missing", "parse-error", "missing-selection", "duplicate"])
def test_live_acquisition_rejects_invalid_sources(indexed, tmp_path, change):
    source = tmp_path / "source/Merge.kif"
    match change:
        case "modified":
            source.write_text(SOURCE + "\n")
        case "missing":
            source.rename(source.with_suffix(".saved"))
        case "parse-error":
            (source.parent / "broken.kif").write_text("(unclosed")
            indexed.build(source.parent)
        case "missing-selection":
            source.write_text(SOURCE.replace("(range ProbabilityFn RealNumber)\n", ""))
            indexed.build(source.parent)
        case "duplicate":
            source.write_text(SOURCE + "(subclass Physical Entity)\n")
            indexed.build(source.parent)
    with pytest.raises((ValueError, ArtifactError)):
        demonstrate_sumo(indexed, tmp_path)


def test_live_acquisition_rejects_missing_index_projection(indexed, tmp_path):
    with sqlite3.connect(indexed.path) as connection:
        connection.execute("DELETE FROM edges WHERE subject='ProbabilityFn' AND predicate='range'")
    with pytest.raises(ValueError, match="missing from the indexed projection"):
        demonstrate_sumo(indexed, tmp_path)


def test_live_acquisition_rejects_missing_index(tmp_path):
    with pytest.raises(ArtifactError, match="cannot inspect"):
        demonstrate_sumo(OntologyIndex(tmp_path / "absent.sqlite"), tmp_path)


def test_script_writes_portable_report_and_refuses_overwrite(indexed, tmp_path, project_root):
    command = [sys.executable, str(project_root / "scripts/demonstrate_sumo.py"),
               "--root", str(tmp_path), "--index", "index.sqlite", "--output", "staged/report.json"]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    assert result.stdout == ""
    report = json.loads((tmp_path / "staged/report.json").read_text())
    assert validate_sumo_report(report).source.path == "source/Merge.kif"
    refused = subprocess.run(command, capture_output=True, text=True, check=False)
    assert refused.returncode != 0
    assert "FileExistsError" in refused.stderr


def test_script_rejects_output_outside_root(indexed, tmp_path, project_root):
    command = [sys.executable, str(project_root / "scripts/demonstrate_sumo.py"),
               "--root", str(tmp_path), "--index", "index.sqlite", "--output", "../escape.json"]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    assert result.returncode != 0
    assert not (tmp_path.parent / "escape.json").exists()


@pytest.mark.integration
def test_native_taxonomy_has_positive_proof_and_countermodel(project_root):
    output = project_root / ".rikishi/results" / ("sumo-demonstration-test-" + uuid.uuid4().hex)
    proof = prove_sumo_taxonomy(OntologyIndex(project_root / ".rikishi/ontology.sqlite"),
                                project_root, output)
    assert proof["positive"]["status"] == "Theorem"
    assert proof["positive"]["proved"] is True
    assert proof["negative"]["status"] == "CounterSatisfiable"
    assert proof["negative"]["proved"] is False
    for run in (proof["positive"], proof["negative"]):
        assert sha256((project_root / run["problem"]).read_bytes()).hexdigest() == run["problem_sha256"]
        assert (project_root / run["capture"]).is_file()

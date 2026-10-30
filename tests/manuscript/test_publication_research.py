import json
import shutil
from hashlib import sha256
from uuid import uuid4

import pytest

from rikishi.alignment import run_alignment
from rikishi.publication_research import load_research_context


@pytest.fixture(scope="module")
def paired_research(project_root, tmp_path_factory, native_workspace, portable_inputs):
    directory = tmp_path_factory.mktemp("research-publication")
    for family in ("e", "v"):
        fresh = native_workspace / ("research-publication-" + uuid4().hex)
        run_alignment(project_root, fresh, prover=family,
                      workbook_path=portable_inputs.workbook_path)
        shutil.copytree(fresh, directory / family)
    return directory


@pytest.mark.integration
def test_research_context_derives_tables_from_replayed_pair(paired_research):
    context = load_research_context(paired_research, decimal_places=4)
    assert context.values["ALIGNMENT_NATIVE_INVOCATIONS"] == str(
        len(context.primary.logical) + len(context.comparison.logical))
    for first, second in zip(context.primary.logical, context.comparison.logical, strict=True):
        assert f"`{first.id}` | {first.expected} | {first.observed} | {second.observed}" in (
            context.values["ALIGNMENT_LOGICAL_TABLE"])
    assert context.input_sha256 == {
        f"{family}/alignment-report.json": sha256(
            (paired_research / family / "alignment-report.json").read_bytes()).hexdigest()
        for family in ("e", "v")}
    assert "e-" in context.values["ALIGNMENT_NUMERICAL_TABLE"]


@pytest.mark.parametrize("precision", [-1, True, 1.5])
def test_research_context_rejects_invalid_precision(tmp_path, precision):
    with pytest.raises(ValueError, match="nonnegative integer"):
        load_research_context(tmp_path, decimal_places=precision)


@pytest.mark.integration
@pytest.mark.parametrize("mutation", ["family", "summary", "numerical"])
def test_research_context_rejects_changed_actual_campaign(paired_research, tmp_path, mutation):
    directory = tmp_path / "research"
    shutil.copytree(paired_research, directory)
    if mutation == "family":
        shutil.rmtree(directory / "e")
        shutil.copytree(directory / "v", directory / "e")
    else:
        path = directory / "e/alignment-report.json"
        payload = json.loads(path.read_bytes())
        if mutation == "summary":
            payload["summary"]["campaign_complete"] = False
        else:
            payload["numerical"]["rows"][0]["result"]["free_energy"] += 1
        path.write_text(json.dumps(payload))
    with pytest.raises((ValueError, RuntimeError)):
        load_research_context(directory, decimal_places=4)

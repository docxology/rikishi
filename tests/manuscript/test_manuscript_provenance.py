import hashlib
import subprocess
from pathlib import Path

import pytest
from pydantic import ValidationError

from rikishi.manuscript_provenance import (
    ArtifactRecord,
    CorpusMeasurement,
    ProvenanceError,
    contained_path,
    hydrate_manuscript,
    prepare_renderer,
    renderer_corruption_control,
    require_evidence,
    verify_artifacts,
    verify_sources,
)


@pytest.fixture
def renderer_repository(tmp_path: Path) -> tuple[Path, str]:
    checkout = tmp_path / "template"
    checkout.mkdir()
    (checkout / "infrastructure").mkdir()
    (checkout / "infrastructure" / "__init__.py").write_text("VERSION = 1\n")
    (checkout / "pyproject.toml").write_text('[project]\nname = "fixture"\n')
    for command in (
        ["init"],
        ["add", "."],
        [
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-m",
            "fixture",
        ],
    ):
        subprocess.run(["git", "-C", str(checkout), *command], check=True, capture_output=True)
    revision = subprocess.check_output(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True
    ).strip()
    return checkout, revision


def test_snapshot_uses_committed_bytes_when_checkout_dirty(tmp_path, renderer_repository):
    checkout, revision = renderer_repository
    (checkout / "pyproject.toml").write_text("dirty source must never execute")
    snapshot, sources, archive_hash = prepare_renderer(tmp_path / "project", checkout, revision)
    assert (snapshot / "infrastructure" / "__init__.py").read_text() == "VERSION = 1\n"
    assert (snapshot / "pyproject.toml").read_text() == '[project]\nname = "fixture"\n'
    assert len(sources) == 2 and len(archive_hash) == 64


def test_snapshot_rejects_corruption_without_overwrite(tmp_path, renderer_repository):
    checkout, revision = renderer_repository
    snapshot, _, _ = prepare_renderer(tmp_path / "project", checkout, revision)
    target = snapshot / "pyproject.toml"
    target.write_text("altered")
    with pytest.raises(ProvenanceError, match="differs"):
        prepare_renderer(tmp_path / "project", checkout, revision)
    assert target.read_text() == "altered"


def test_snapshot_rejects_symlink_archive(tmp_path, renderer_repository):
    checkout, _ = renderer_repository
    (checkout / "infrastructure" / "link.py").symlink_to("__init__.py")
    subprocess.run(["git", "-C", str(checkout), "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(checkout),
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-m",
            "link",
        ],
        check=True,
        capture_output=True,
    )
    revision = subprocess.check_output(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True
    ).strip()
    with pytest.raises(ProvenanceError, match="Unsupported archive"):
        prepare_renderer(tmp_path / "project", checkout, revision)


def test_snapshot_rejects_mutable_revision(tmp_path):
    with pytest.raises(ProvenanceError, match="full Git"):
        prepare_renderer(tmp_path, tmp_path, "HEAD")


def test_corruption_control_checks_real_snapshot(tmp_path, renderer_repository):
    checkout, revision = renderer_repository
    positive, negative = renderer_corruption_control(tmp_path, checkout, revision)
    assert "2 archived files" in positive
    assert "differs from pinned archive" in negative


@pytest.mark.parametrize("relative", ["../outside", "/absolute"])
def test_receipt_paths_cannot_escape(tmp_path, relative):
    with pytest.raises(ProvenanceError, match="Nonrelative"):
        contained_path(tmp_path, relative)


def test_receipt_paths_reject_external_symlink(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "escape").symlink_to(tmp_path)
    with pytest.raises(ProvenanceError, match="escapes"):
        contained_path(root, "escape/file")


def test_sources_reject_empty_manifest(tmp_path):
    with pytest.raises(ProvenanceError, match="empty"):
        verify_sources(tmp_path, {})


@pytest.fixture
def measurement():
    return CorpusMeasurement(
        source_commit="a" * 40,
        source_clean=True,
        files=2,
        formulas=5,
        terms=3,
        edges=1,
        parse_errors=[],
    )


def test_hydration_measures_exact_input(measurement):
    result = hydrate_manuscript("{{CORPUS_FILES}}/{{CORPUS_FORMULAS}} {{SUMO_COMMIT}}", measurement)
    assert result.text == "2/5 " + "a" * 40
    assert result.substitutions["CORPUS_EDGES"] == "1"


@pytest.mark.parametrize(
    "field,value", [("source_clean", False), ("parse_errors", [{"path": "broken.kif"}])]
)
def test_hydration_rejects_untrustworthy_corpus(measurement, field, value):
    corpus = CorpusMeasurement.model_validate(measurement.model_dump() | {field: value})
    with pytest.raises(ProvenanceError, match="clean corpus"):
        hydrate_manuscript("{{CORPUS_FILES}}", corpus)


@pytest.mark.parametrize("text", ["{{UNKNOWN}}", "{{lowercase}}", "{{two\nlines}}"])
def test_hydration_rejects_unresolved_tokens(measurement, text):
    with pytest.raises(ProvenanceError, match="Unresolved"):
        hydrate_manuscript(text, measurement)


@pytest.mark.parametrize(
    "field,value", [("formulas", -1), ("files", True), ("source_commit", "HEAD")]
)
def test_corpus_schema_rejects_invalid_measurements(measurement, field, value):
    with pytest.raises(ValidationError):
        CorpusMeasurement.model_validate(measurement.model_dump() | {field: value})


def test_artifact_hash_verifies_real_bytes(tmp_path):
    (tmp_path / "artifact").write_bytes(b"data")
    record = ArtifactRecord(path="artifact", bytes=4, sha256=hashlib.sha256(b"data").hexdigest())
    verify_artifacts(tmp_path, [record])


@pytest.mark.parametrize("payload,error", [(b"longer", "size"), (b"fake", "hash")])
def test_artifact_verification_rejects_corruption(tmp_path, payload, error):
    record = ArtifactRecord(path="artifact", bytes=4, sha256=hashlib.sha256(b"data").hexdigest())
    (tmp_path / "artifact").write_bytes(payload)
    with pytest.raises(ProvenanceError, match=error):
        verify_artifacts(tmp_path, [record])


@pytest.mark.parametrize("duplicate", [False, True])
def test_artifact_manifest_requires_unique_records(tmp_path, duplicate):
    record = ArtifactRecord(path="artifact", bytes=4, sha256="a" * 64)
    with pytest.raises(ProvenanceError, match="unique nonempty"):
        verify_artifacts(tmp_path, [record, record] if duplicate else [])


@pytest.mark.parametrize("condition", [True, False])
def test_checks_remain_explicit_when_assertions_disabled(condition):
    if condition:
        require_evidence(condition, "check")
    else:
        with pytest.raises(ProvenanceError, match="check"):
            require_evidence(condition, "check")

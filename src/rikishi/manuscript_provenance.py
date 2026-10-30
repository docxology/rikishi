from __future__ import annotations

import hashlib
import io
import json
import re
import subprocess
import tarfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final

from pydantic import BaseModel, ConfigDict, Field

RENDERER_REVISION: Final = "efce6d6f5b3c4e8e2bbf92d8250855a0a9389ae8"


class ProvenanceError(ValueError):
    reason: str

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


class CorpusMeasurement(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)
    source_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    source_clean: bool
    files: int = Field(gt=0)
    formulas: int = Field(ge=0)
    terms: int = Field(ge=0)
    edges: int = Field(ge=0)
    parse_errors: list[dict[str, str]]


@dataclass(frozen=True, slots=True)
class HydratedManuscript:
    text: str
    substitutions: dict[str, str]


def hydrate_manuscript(
    source: str, corpus: CorpusMeasurement, *, values: Mapping[str, str] | None = None
) -> HydratedManuscript:
    if corpus.parse_errors or not corpus.source_clean:
        raise ProvenanceError("Manuscript requires a clean corpus export with no parse errors")
    substitutions = {
        "SUMO_COMMIT": corpus.source_commit,
        "CORPUS_FILES": str(corpus.files),
        "CORPUS_FORMULAS": str(corpus.formulas),
        "CORPUS_TERMS": str(corpus.terms),
        "CORPUS_EDGES": str(corpus.edges),
        "CORPUS_PARSE_ERRORS": str(len(corpus.parse_errors)),
    }
    if values is not None:
        if substitutions.keys() & values.keys():
            raise ProvenanceError("Publication values cannot override corpus measurements")
        if any(not re.fullmatch(r"[A-Z][A-Z0-9_]*", key) for key in values):
            raise ProvenanceError("Invalid publication substitution name")
        if any("{{" in value or "}}" in value for value in values.values()):
            raise ProvenanceError("Recursive publication substitutions are not allowed")
        substitutions.update(values)
    token = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")
    unknown = set(token.findall(source)) - substitutions.keys()
    if unknown:
        raise ProvenanceError(f"Unresolved manuscript substitutions: {sorted(unknown)}")
    hydrated = token.sub(lambda match: substitutions[match[1]], source)
    if re.search(r"\{\{.*?\}\}", hydrated, re.DOTALL):
        raise ProvenanceError("Unresolved manuscript substitution")
    return HydratedManuscript(hydrated, substitutions)


def contained_path(root: Path, relative: str) -> Path:
    target = root / relative
    if Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ProvenanceError(f"Nonrelative provenance path: {relative}")
    if not target.resolve().is_relative_to(root.resolve()):
        raise ProvenanceError(f"Provenance path escapes root: {relative}")
    return target


def prepare_renderer(
    root: Path, checkout: Path, revision: str = RENDERER_REVISION
) -> tuple[Path, dict[str, str], str]:
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ProvenanceError("Renderer revision must be a full Git object identifier")
    archive_bytes = subprocess.run(
        ["git", "-C", str(checkout), "archive", revision, "infrastructure", "pyproject.toml"],
        check=True,
        capture_output=True,
    ).stdout
    archive_hash = hashlib.sha256(archive_bytes).hexdigest()
    snapshot = root / ".rikishi" / "template-renderer" / revision
    with tarfile.open(fileobj=io.BytesIO(archive_bytes)) as archive:
        sources = {}
        for member in archive.getmembers():
            contained_path(snapshot, member.name)
            if member.isfile():
                stream = archive.extractfile(member)
                if stream is None:
                    raise ProvenanceError(f"Cannot read renderer archive file: {member.name}")
                with stream:
                    sources[member.name] = hashlib.sha256(stream.read()).hexdigest()
            elif not member.isdir():
                raise ProvenanceError(f"Unsupported archive entry {member.name}")
        if not snapshot.exists():
            snapshot.mkdir(parents=True)
            archive.extractall(snapshot, filter="data")
    verify_sources(snapshot, sources)
    origin = {"revision": revision, "archive_sha256": archive_hash, "sources": sources}
    (snapshot.parent / "renderer-origin.json").write_text(json.dumps(origin, indent=2) + "\n")
    return snapshot, sources, archive_hash


def verify_sources(snapshot: Path, sources: dict[str, str]) -> None:
    if not sources:
        raise ProvenanceError("Renderer source manifest is empty")
    for relative, digest in sources.items():
        target = contained_path(snapshot, relative)
        if target.is_symlink() or hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            raise ProvenanceError(f"Renderer snapshot differs from pinned archive: {relative}")


class ArtifactRecord(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)
    path: str
    bytes: int = Field(ge=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


def verify_artifacts(root: Path, records: list[ArtifactRecord]) -> None:
    if not records or len({item.path for item in records}) != len(records):
        raise ProvenanceError("Artifact manifest must contain unique nonempty records")
    for item in records:
        artifact = contained_path(root, item.path)
        if artifact.stat().st_size != item.bytes:
            raise ProvenanceError(f"Artifact size differs: {item.path}")
        if hashlib.sha256(artifact.read_bytes()).hexdigest() != item.sha256:
            raise ProvenanceError(f"Artifact hash differs: {item.path}")


def require_evidence(condition: bool, description: str) -> None:
    if not condition:
        raise ProvenanceError(description)


def renderer_corruption_control(
    root: Path, checkout: Path, revision: str = RENDERER_REVISION
) -> tuple[str, str]:
    (root / ".rikishi").mkdir(exist_ok=True)
    with TemporaryDirectory(prefix="renderer-control-", dir=root / ".rikishi") as directory:
        temporary_root = Path(directory)
        snapshot, sources, archive_hash = prepare_renderer(temporary_root, checkout, revision)
        positive = f"Positive control: {len(sources)} archived files verified; archive {archive_hash}"
        metadata = snapshot / "pyproject.toml"
        metadata.write_bytes(metadata.read_bytes() + b"\ncorruption-control\n")
        try:
            prepare_renderer(temporary_root, checkout, revision)
        except ProvenanceError as error:
            return positive, f"Negative control rejected altered snapshot: {error}"
        raise ProvenanceError("Modified renderer snapshot was accepted")

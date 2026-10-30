"""Freeze a complete Sigma profile before any native initialization or output."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from dataclasses import asdict, dataclass
from pathlib import Path

from defusedxml import ElementTree

from rikishi.runtime_artifacts import ArtifactError, checked_source_path, read_regular


@dataclass(frozen=True, slots=True)
class ProfileFile:
    path: str
    sha256: str
    size: int
    mtime_ns: int


@dataclass(frozen=True, slots=True)
class ProfileSnapshot:
    source: Path
    directories: tuple[str, ...]
    files: tuple[ProfileFile, ...]

    def manifest(self) -> bytes:
        """Bind all initial cache, constituent, lexicon and configuration bytes."""
        return (json.dumps({
            "policy": "complete-sigma-profile-v1", "source": str(self.source),
            "directories": self.directories, "files": [asdict(item) for item in self.files],
        }, sort_keys=True, indent=2) + "\n").encode()


def _configuration(source: Path) -> None:
    """Refuse profiles whose constituents or mutable paths escape the copy."""
    config = ElementTree.fromstring(read_regular(source / "KBs/config.xml"))
    preferences = {item.attrib["name"]: item.attrib["value"]
                   for item in config.findall("preference")}
    if len(preferences) != len(config.findall("preference")):
        raise ArtifactError("duplicate Sigma profile preferences are unsupported")
    if (Path(preferences.get("baseDir", str(source))) != source
            or Path(preferences.get("kbDir", str(source / "KBs"))) != source / "KBs"):
        raise ArtifactError("Sigma profile baseDir/kbDir must identify the copied profile")
    for name in ("graphDir", "inferenceTestDir"):
        value = preferences.get(name)
        if value and not checked_source_path(Path(value)).is_relative_to(source):
            raise ArtifactError(f"Sigma profile {name} escapes the copied profile")
    if preferences.get("verbnetDir"):
        raise ArtifactError("external VerbNet profiles are unsupported for isolated queries")
    sumo = Path(preferences.get("sumoDir", str(source / "KBs")))
    for item in config.findall("kb/constituent"):
        relative = Path(item.attrib["filename"])
        if relative.is_absolute() or ".." in relative.parts or str(relative) in {".", ""}:
            raise ArtifactError("isolated Sigma constituents must use safe relative paths")
        copied = read_regular(checked_source_path(source / "KBs" / relative))
        original = read_regular(checked_source_path(sumo / relative))
        if copied != original:
            raise ArtifactError("Sigma profile constituent differs from its configured source")


def snapshot_profile(source: Path) -> ProfileSnapshot:
    """Inspect lexical entries before reading; links and special files are errors."""
    source = checked_source_path(source)
    directories: list[str] = []
    files: list[ProfileFile] = []

    def visit(directory: Path) -> None:
        for entry in sorted(directory.iterdir()):
            metadata = entry.lstat()
            relative = str(entry.relative_to(source))
            if stat.S_ISDIR(metadata.st_mode):
                directories.append(relative)
                visit(entry)
            elif stat.S_ISREG(metadata.st_mode):
                data = read_regular(checked_source_path(entry))
                files.append(ProfileFile(relative, hashlib.sha256(data).hexdigest(),
                                         len(data), metadata.st_mtime_ns))
            else:
                raise ArtifactError(f"unsupported Sigma profile entry: {entry}")

    visit(source)
    _configuration(source)
    return ProfileSnapshot(source, tuple(directories), tuple(files))


def verify_profile(snapshot: ProfileSnapshot) -> None:
    """Require the source snapshot to survive copying and the native query."""
    if snapshot_profile(snapshot.source) != snapshot:
        raise ArtifactError("Sigma source profile changed during the isolated query")


def verify_copied_inputs(
    snapshot: ProfileSnapshot, destination: Path, *, after_execution: bool = False,
) -> None:
    """Keep consumed cache/source bytes stable; regenerated ATP files have captures."""
    generated: set[str] = set()
    if after_execution:
        config = ElementTree.fromstring(read_regular(snapshot.source / "KBs/config.xml"))
        generated = {f"KBs/{item.attrib['name']}.tptp" for item in config.findall("kb")}
        generated.update({"KBs/temp-comb.tptp", "KBs/temp-stmt.tptp"})
    for item in snapshot.files:
        if item.path in generated:
            continue
        target = checked_source_path(destination / item.path)
        data = read_regular(target)
        if (len(data) != item.size or hashlib.sha256(data).hexdigest() != item.sha256
                or target.stat().st_mtime_ns != item.mtime_ns):
            raise ArtifactError(f"isolated Sigma input changed: {item.path}")


def prepare_profile(source: Path, destination: Path) -> ProfileSnapshot:
    """Copy every regular file with exact bytes and freshness timestamps."""
    snapshot = snapshot_profile(source)
    source = snapshot.source
    destination = checked_source_path(destination.parent) / destination.name
    if destination.is_relative_to(source):
        raise ArtifactError("isolated Sigma output cannot be inside its source profile")
    destination.mkdir()
    for relative in snapshot.directories:
        (destination / relative).mkdir()
    for item in snapshot.files:
        data = read_regular(checked_source_path(source / item.path))
        if len(data) != item.size or hashlib.sha256(data).hexdigest() != item.sha256:
            raise ArtifactError("Sigma source profile changed while copying")
        target = destination / item.path
        with target.open("xb") as stream:
            stream.write(data)
        os.utime(target, ns=(item.mtime_ns, item.mtime_ns))
    verify_profile(snapshot)
    verify_copied_inputs(snapshot, destination)
    return snapshot

from __future__ import annotations

import hashlib
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

from rikishi.ontology import OntologyIndex, _read_kif_file


@dataclass(frozen=True, slots=True)
class SourceAudit:
    indexed_commit: str
    current_commit: str
    indexed_clean: bool | None
    current_clean: bool | None
    unchanged_files: int
    added: tuple[str, ...]
    missing: tuple[str, ...]
    modified: tuple[str, ...]
    escaped_paths: tuple[str, ...]
    parse_failures_at_index: int
    unavailable_paths: tuple[str, ...] = ()

    @property
    def matches_index(self) -> bool:
        return not (
            self.added or self.missing or self.modified or self.escaped_paths
            or self.unavailable_paths or self.parse_failures_at_index
        )

    @property
    def revision_matches(self) -> bool | None:
        if "unversioned" in (self.indexed_commit, self.current_commit):
            return None
        return self.indexed_commit == self.current_commit

    @property
    def passed(self) -> bool:
        return self.matches_index and self.revision_matches is not False

    def to_dict(self) -> dict[str, str | bool | int | None | tuple[str, ...]]:
        return {**asdict(self), "matches_index": self.matches_index,
                "revision_matches": self.revision_matches, "passed": self.passed}


def audit_sources(index: OntologyIndex) -> SourceAudit:
    """Compare current KIF bytes and Git revision to the indexed snapshot, without rebuilding.

    File agreement and revision agreement are separate observations. Paths
    rejected by the indexer's input boundary cannot supply hash observations.
    """
    stats = index.stats()
    root = Path(stats["source_root"])
    if root.resolve(strict=True) != root:
        raise ValueError("Recorded ontology source root is no longer its original resolved path")
    manifest = {str(row["path"]): row for row in index.source_manifest()}
    discovered = {path.relative_to(root).as_posix(): path for path in root.rglob("*.kif")
                  if ".git" not in path.parts}
    escaped = []
    for relative, path in sorted(discovered.items()):
        try:
            if not path.resolve().is_relative_to(root):
                escaped.append(relative)
        except (OSError, RuntimeError):
            # Resolution is a diagnostic only. The bounded reader decides whether
            # an indexed path can provide an actual hash observation.
            continue
    unavailable = []
    modified = []
    unchanged = 0
    for relative in sorted((manifest.keys() & discovered.keys()) - set(escaped)):
        try:
            raw = _read_kif_file(root, Path(relative))
        except (OSError, ValueError):
            unavailable.append(relative)
            continue
        digest = hashlib.sha256(raw).hexdigest()
        if digest == manifest[relative]["sha256"]:
            unchanged += 1
        else:
            modified.append(relative)
    commit, clean = "unversioned", None
    if (root / ".git").exists():
        command = ["git", "-C", str(root)]
        commit = subprocess.run([*command, "rev-parse", "HEAD"], stdin=subprocess.DEVNULL, check=True, timeout=10,
                                capture_output=True, text=True).stdout.strip()
        clean = not bool(subprocess.run([*command, "status", "--porcelain"], stdin=subprocess.DEVNULL, check=True,
                                       timeout=10, capture_output=True, text=True).stdout)
    return SourceAudit(stats["source_commit"], commit, stats["source_clean"], clean, unchanged,
                       tuple(sorted(discovered.keys() - manifest.keys())),
                       tuple(sorted(manifest.keys() - discovered.keys())), tuple(modified),
                       tuple(escaped), len(stats["parse_errors"]), tuple(unavailable))

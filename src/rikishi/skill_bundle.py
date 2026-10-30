"""Check or explicitly export .agents/skills into the packaged skills projection."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory


class SkillBundleError(ValueError):
    """A skill tree is unsafe or its distribution differs from the authority."""

    def __init__(self, issues: tuple[str, ...]) -> None:
        self.issues = issues
        super().__init__("; ".join(issues))


@dataclass(frozen=True, slots=True)
class _SkillTree:
    files: dict[Path, bytes]
    directories: frozenset[Path]


def _read_tree(directory: Path, *, required: bool) -> _SkillTree:
    files: dict[Path, bytes] = {}
    directories: set[Path] = set()

    def visit(path: Path) -> None:
        if path.is_symlink():
            raise SkillBundleError((f"symlink is not allowed: {path}",))
        if path.is_dir():
            if path != directory:
                directories.add(path.relative_to(directory))
            for child in sorted(path.iterdir()):
                visit(child)
        elif path.is_file():
            files[path.relative_to(directory)] = path.read_bytes()
        else:
            raise SkillBundleError((f"not a regular file or directory: {path}",))

    if directory.is_symlink():
        raise SkillBundleError((f"symlink is not allowed: {directory}",))
    if not directory.exists() and not required:
        return _SkillTree(files, frozenset())
    if not directory.is_dir():
        raise SkillBundleError((f"missing or invalid skill directory: {directory}",))
    visit(directory)
    return _SkillTree(files, frozenset(directories))


def sync_skill_bundle(root: Path, *, write: bool = False) -> tuple[str, ...]:
    """Return sorted skill-relative paths, raising SkillBundleError on drift.

    Read-only by default. Explicit writes repair missing/changed copies using
    independent atomic file replacements. Unexpected entries, symlinks and special
    files are rejected before writes. This local projection requires exclusive
    ownership of both trees during the call; it is not a concurrent-writer service.
    """
    if root.is_symlink() or not root.is_dir():
        raise SkillBundleError((f"missing, invalid or symlink repository root: {root}",))
    root = root.resolve()
    agents = root / ".agents"
    if agents.is_symlink() or not agents.is_dir():
        raise SkillBundleError((f"missing, invalid or symlink authority directory: {agents}",))
    source = _read_tree(agents / "skills", required=True)
    if not source.files:
        raise SkillBundleError(("authored skill tree has no files",))
    destination = root / "skills"
    copies = _read_tree(destination, required=False)
    unexpected = (copies.files.keys() - source.files.keys()) | (
        copies.directories - source.directories
    )
    if unexpected:
        raise SkillBundleError(tuple(f"unexpected copy: {path.as_posix()}"
                                     for path in sorted(unexpected)))
    missing = (source.files.keys() - copies.files.keys()) | (
        source.directories - copies.directories
    )
    changed = {path for path in source.files.keys() & copies.files.keys()
               if source.files[path] != copies.files[path]}
    issues = tuple(f"missing copy: {path.as_posix()}" for path in sorted(missing)) + tuple(
        f"changed copy: {path.as_posix()}" for path in sorted(changed)
    )
    if issues and not write:
        raise SkillBundleError(issues)
    if issues:
        destination.mkdir(exist_ok=True)
        for relative in sorted(source.directories):
            (destination / relative).mkdir(exist_ok=True)
        with TemporaryDirectory(prefix=".rikishi-skill-export-", dir=root) as temporary:
            staging = Path(temporary)
            for relative in sorted((source.files.keys() - copies.files.keys()) | changed):
                staged = staging / relative
                staged.parent.mkdir(parents=True, exist_ok=True)
                staged.write_bytes(source.files[relative])
                staged.replace(destination / relative)
    return tuple(path.as_posix() for path in sorted(source.files))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="repository root")
    parser.add_argument("--write", action="store_true", help="export authored bytes explicitly")
    args = parser.parse_args(argv)
    try:
        files = sync_skill_bundle(args.root, write=args.write)
    except (SkillBundleError, OSError) as error:
        parser.exit(1, f"skill bundle: {error}\n")
    print(json.dumps({"mode": "write" if args.write else "check", "files": files}, indent=2))
    return 0

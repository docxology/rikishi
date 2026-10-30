"""Strict, bounded file receipts for query-specific ATP inputs and outputs."""

from __future__ import annotations

import hashlib
import os
import re
import stat
import zipfile
from collections.abc import Sequence
from pathlib import Path
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, Field

from rikishi.runtime_tptp import TPTPError, parse_tptp

MAX_ARTIFACT_BYTES = 512 * 1024 * 1024
PATH_POLICY: Final = "lexical-absolute-no-symlinks-v1"
COMMAND_POLICY: Final = "single-problem-allowlist-v1"
ProverKind = Literal["e", "v"]
SZS_STATUS = re.compile(
    r"(?m)^[ \t]*(?:%%|[%#])[ \t]*SZS status ([A-Za-z]+)"
    r"(?:[ \t]+for[ \t]+\S[^\r\n]*)?[ \t]*\r?$"
)


class ArtifactError(ValueError):
    """Saved evidence is missing, unsafe, oversized, or no longer matches its receipt."""


class Artifact(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")
    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size: int = Field(ge=0, le=MAX_ARTIFACT_BYTES)


class IncludedArtifact(Artifact):
    source: str


class Capture(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")
    path_policy: Literal["lexical-absolute-no-symlinks-v1"]
    command_policy: Literal["single-problem-allowlist-v1"]
    prover: ProverKind
    invocation_id: str = Field(min_length=1)
    command: list[str] = Field(min_length=2)
    source_problem: str
    problem: Artifact
    includes: list[IncludedArtifact]
    stdout: Artifact
    stderr: Artifact
    returncode: int
    timed_out: bool
    provenance: dict[str, str] = Field(min_length=1)


def validate_prover_command(command: Sequence[str], prover: ProverKind) -> None:
    """Accept only known native options and one final absolute problem filename."""
    if (len(command) < 3 or not Path(command[0]).is_absolute()
            or not Path(command[-1]).is_absolute() or any("\0" in item for item in command)):
        raise ArtifactError("prover command requires one final absolute problem and absolute executable")
    options = command[1:-1]
    if prover == "e":
        for option in options:
            if not re.fullmatch(
                r"--(?:auto|tstp-format|proof-object|conjectures-are-questions|"
                r"cpu-limit=[1-9][0-9]*|answers=[1-9][0-9]*)", option,
            ):
                raise ArtifactError(f"unsupported E prover argument: {option}")
        if sum(option.startswith("--cpu-limit=") for option in options) != 1:
            raise ArtifactError("E prover command requires exactly one inline CPU limit")
    else:
        supported = {"--proof": {"tptp"}, "--mode": {"casc"}, "-qa": {"plain"}}
        seen: set[str] = set()
        if len(options) % 2:
            raise ArtifactError("Vampire arguments require explicit supported option/value pairs")
        for index in range(0, len(options), 2):
            option, value = options[index:index + 2]
            if (option in seen or (option == "-t" and not re.fullmatch(r"[1-9][0-9]*", value))
                    or (option != "-t" and value not in supported.get(option, set()))):
                raise ArtifactError(f"unsupported Vampire prover argument: {option} {value}")
            seen.add(option)
        if not {"--proof", "--mode", "-t"} <= seen:
            raise ArtifactError("Vampire command must use the complete supported native CASC options")


def normalized_source_identity(source: str) -> str:
    if not source.startswith("/") or source.startswith("//") or os.path.normpath(source) != source:
        raise ArtifactError("source identity must be a normalized absolute lexical path")
    return source


def checked_source_path(path: Path) -> Path:
    """Reject every symlink component before parent traversal can erase its identity."""
    absolute = path if path.is_absolute() else Path.cwd() / path
    if absolute.anchor != "/":
        raise ArtifactError("source path must use an ordinary absolute filesystem root")
    current = Path(absolute.anchor)
    for index, component in enumerate(absolute.parts[1:], start=1):
        if component == "..":
            current = current.parent
            continue
        current = current / component
        try:
            metadata = current.lstat()
        except OSError as error:
            raise ArtifactError(f"cannot inspect source path component: {current}") from error
        if stat.S_ISLNK(metadata.st_mode):
            raise ArtifactError(f"symlink source path component is unsupported: {current}")
        if index < len(absolute.parts) - 1 and not stat.S_ISDIR(metadata.st_mode):
            raise ArtifactError(f"source path ancestor is not a directory: {current}")
    normalized_source_identity(str(current))
    return current


def jar_classes_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with zipfile.ZipFile(path) as archive:
        for name in sorted(item for item in archive.namelist() if item.endswith(".class")):
            digest.update(name.encode("utf-8") + b"\0" + archive.read(name))
    return digest.hexdigest()


def read_regular(path: Path, *, limit: int = MAX_ARTIFACT_BYTES) -> bytes:
    """Reject links and special files before opening; bound reads even after growth."""
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
        with os.fdopen(descriptor, "rb") as stream:
            metadata = os.fstat(stream.fileno())
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > limit:
                raise ArtifactError(f"not a bounded regular file: {path}")
            data = stream.read(limit + 1)
    except OSError as error:
        raise ArtifactError(f"cannot read evidence: {path}") from error
    if len(data) > limit:
        raise ArtifactError(f"evidence exceeds size limit: {path}")
    return data


def receipt(path: Path, directory: Path) -> Artifact:
    data = read_regular(path)
    return Artifact(path=str(path.relative_to(directory)), size=len(data),
                    sha256=hashlib.sha256(data).hexdigest())


def verified_bytes(artifact: Artifact, directory: Path) -> bytes:
    path = directory / artifact.path
    if Path(artifact.path).is_absolute() or ".." in Path(artifact.path).parts:
        raise ArtifactError("artifact path must stay inside its evidence directory")
    if path.resolve().parent != directory.resolve():
        raise ArtifactError("artifact must be a direct file in its evidence directory")
    data = read_regular(path)
    if len(data) != artifact.size or hashlib.sha256(data).hexdigest() != artifact.sha256:
        raise ArtifactError(f"artifact checksum mismatch: {path}")
    return data


def load_capture(path: Path, invocation_id: str | None = None) -> Capture:
    capture = Capture.model_validate_json(read_regular(path, limit=64 * 1024))
    if invocation_id is not None and capture.invocation_id != invocation_id:
        raise ArtifactError("capture belongs to another invocation")
    validate_prover_command(capture.command, capture.prover)
    normalized_source_identity(capture.source_problem)
    for included in capture.includes:
        normalized_source_identity(included.source)
    for artifact in [capture.problem, *capture.includes, capture.stdout, capture.stderr]:
        verified_bytes(artifact, path.parent)
    return capture


def expanded_problem(capture: Capture, directory: Path) -> str:
    """Replay saved include bytes without consulting mutable Sigma caches."""
    validate_prover_command(capture.command, capture.prover)
    source_problem = normalized_source_identity(capture.source_problem)
    includes = {normalized_source_identity(item.source): item for item in capture.includes}
    if len(includes) != len(capture.includes):
        raise ArtifactError("duplicate included source in capture")

    def expand(data: bytes, source: str, seen: frozenset[str]) -> str:
        result: list[str] = []
        try:
            statements = parse_tptp(data.decode("utf-8"))
        except TPTPError as error:
            raise ArtifactError(f"unsupported TPTP input: {error}") from error
        for statement in statements:
            if statement.kind == "include":
                if statement.include_path is None:
                    raise ArtifactError("include directive has no recorded path")
                target = normalized_source_identity(os.path.normpath(
                    os.path.join(os.path.dirname(source), statement.include_path)))
                if target in seen or target not in includes:
                    raise ArtifactError(f"unrecorded or recursive TPTP include: {target}")
                result.append(expand(verified_bytes(includes[target], directory), target, seen | {target}))
            else:
                result.append(statement.text)
        return "\n".join(result) + "\n"

    return expand(verified_bytes(capture.problem, directory), source_problem, frozenset())

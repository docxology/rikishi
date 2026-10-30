"""Complete executable JAR identity, independent of Ant's packaging timestamp."""

from __future__ import annotations

import hashlib
import io
import re
import stat
import zipfile
import zlib
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Annotated, Final, Literal

from pydantic import BaseModel, ConfigDict, Field

from rikishi.runtime_artifacts import ArtifactError, checked_source_path, read_regular

JAR_CONTENT_POLICY: Final = "complete-jar-content-v1"
SHA256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Revision = Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]
MAX_ARCHIVE_BYTES: Final = 256 << 20
MAX_CONTENT_BYTES: Final = 512 << 20


class JarIdentityError(ArtifactError):
    """An archive cannot establish the declared complete executable identity."""


class JarContentBinding(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)
    policy: Literal["complete-jar-content-v1"]
    content_sha256: SHA256
    source_revision: Revision | None


class JarContentIdentity(JarContentBinding):
    archive_sha256: SHA256
    entry_count: int = Field(gt=0)


def _version(data: bytes, revision: str) -> str:
    """Validate Ant's source stamp without discarding any of its resource bytes."""
    fields: dict[str, str] = {}
    for line in data.decode("ascii").splitlines():
        if not line.strip():
            continue
        key, separator, value = line.partition("=")
        if not separator or key in fields:
            raise JarIdentityError("invalid or duplicate Sigma version property")
        fields[key] = value
    commit = fields.get("build.commit", "")
    if (set(fields) != {"build.version", "build.commit", "build.date"}
            or re.fullmatch(r"[0-9a-f]{7,40}", commit) is None
            or not revision.startswith(commit)):
        raise JarIdentityError("Sigma version.properties source revision differs")
    version, separator, stamped_commit = fields["build.version"].rpartition("-")
    if not separator or not version or stamped_commit != commit:
        raise JarIdentityError("Sigma build.version and build.commit disagree")
    try:
        datetime.strptime(fields["build.date"], "%Y-%m-%d")
    except ValueError as error:
        raise JarIdentityError("invalid Sigma source commit date") from error
    return version


def _manifest(data: bytes, version: str) -> bytes:
    """Keep every manifest value except Ant's validated build-clock suffix."""
    logical: list[bytes] = []
    for line in data.splitlines():
        if line.startswith(b" "):
            if not logical or not logical[-1]:
                raise JarIdentityError("invalid manifest continuation")
            logical[-1] += line[1:]
        else:
            logical.append(line)
    matches = 0
    for index, line in enumerate(logical):
        key, separator, value = line.partition(b": ")
        if key.lower() != b"implementation-version":
            continue
        matches += 1
        prefix = version.encode("ascii") + b" built on "
        if not separator or not value.startswith(prefix):
            raise JarIdentityError("Sigma manifest implementation version differs")
        timestamp = value[len(prefix):].decode("ascii")
        match = re.fullmatch(r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun), ([1-9][0-9]?) "
                             r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) "
                             r"([0-9]{4}) ([0-9]{2})([0-9]{2}) [+-]([0-9]{2})([0-9]{2})",
                             timestamp)
        if match is None:
            raise JarIdentityError("unsupported Sigma manifest build timestamp")
        try:
            weekday, day, month, year, hour, minute, zone_hour, zone_minute = match.groups()
            months = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
                      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
            instant = datetime(int(year), months.index(month) + 1, int(day), int(hour), int(minute))
            if (weekday != ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")[instant.weekday()]
                    or int(zone_hour) > 23 or int(zone_minute) > 59):
                raise JarIdentityError("invalid Sigma manifest build timestamp")
        except ValueError as error:
            raise JarIdentityError("invalid Sigma manifest build timestamp") from error
        logical[index] = key + b": " + version.encode("ascii") + b" built on <ANT-BUILD-TIME>"
    if matches != 1:
        raise JarIdentityError("Sigma manifest requires one Implementation-Version")
    return b"\n".join(logical) + b"\n"


def jar_content_identity(path: Path, *, source_revision: str | None = None) -> JarContentIdentity:
    """Hash every file resource and class; retain the exact archive SHA separately.

    Only Sigma (identified by its pinned full source revision) permits the Ant
    manifest clock normalization. Its version.properties bytes remain exact.
    Directory records, ordering, compression and ZIP metadata are packaging only.
    """
    if source_revision is not None and re.fullmatch(r"[0-9a-f]{40}", source_revision) is None:
        raise JarIdentityError("source revision must be a full lowercase Git object ID")
    data = read_regular(checked_source_path(path), limit=MAX_ARCHIVE_BYTES)
    digest = hashlib.sha256(JAR_CONTENT_POLICY.encode("ascii") + b"\0"
                            + (source_revision or "").encode("ascii") + b"\0")
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entries = archive.infolist()
            names: set[str] = set()
            files: list[zipfile.ZipInfo] = []
            total = 0
            for entry in entries:
                name = entry.filename
                components = name.rstrip("/").split("/")
                if (name in names or entry.orig_filename != name or not name
                        or "\\" in name or PurePosixPath(name).is_absolute()
                        or any(p in {"", ".", ".."} for p in components)):
                    raise JarIdentityError("duplicate or unsafe archive entry")
                names.add(name)
                if (entry.flag_bits & 1
                        or entry.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}):
                    raise JarIdentityError("unsupported archive entry encoding or file type")
                if entry.is_dir():
                    if entry.file_size:
                        raise JarIdentityError("archive directory contains data")
                    continue
                if stat.S_IFMT(entry.external_attr >> 16) not in {0, stat.S_IFREG}:
                    raise JarIdentityError("unsupported archive entry file type")
                total += entry.file_size
                files.append(entry)
            if not files or len(entries) > 100_000 or total > MAX_CONTENT_BYTES:
                raise JarIdentityError("empty or oversized executable archive")
            version = None
            if source_revision is not None:
                required = {"version.properties", "META-INF/MANIFEST.MF"}
                if not required <= {entry.filename for entry in files}:
                    raise JarIdentityError("Sigma archive lacks source stamp or manifest")
                version = _version(archive.read("version.properties"), source_revision)
            for entry in sorted(files, key=lambda item: item.filename):
                content = archive.read(entry)
                if version is not None and entry.filename == "META-INF/MANIFEST.MF":
                    content = _manifest(content, version)
                name = entry.filename.encode("utf-8")
                digest.update(len(name).to_bytes(8, "big") + name
                              + len(content).to_bytes(8, "big") + content)
    except (zipfile.BadZipFile, UnicodeError, EOFError, zlib.error) as error:
        raise JarIdentityError(f"unreadable executable archive: {error}") from error
    return JarContentIdentity(policy=JAR_CONTENT_POLICY, content_sha256=digest.hexdigest(),
                              source_revision=source_revision,
                              archive_sha256=hashlib.sha256(data).hexdigest(), entry_count=len(files))

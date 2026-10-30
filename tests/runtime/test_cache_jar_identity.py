import struct
import zipfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from rikishi.cache_jar_identity import (
    JarContentBinding,
    JarIdentityError,
    jar_content_identity,
)
from rikishi.runtime_artifacts import ArtifactError

REVISION = "d3cc7b43b38b0b45692291a1b33fe2b1a3de0095"
VERSION = (b"build.version=3.0.0-d3cc7b4\nbuild.commit=d3cc7b4\n"
           b"build.date=2026-09-24\n        \n")
MANIFEST = (b"Manifest-Version: 1.0\r\nMain-Class: example.Main\r\n"
            b"Implementation-Version: 3.0.0 built on Wed, 21 Oct 2026 1348 -0700\r\n\r\n")


def _jar(tmp_path: Path, entries: dict[str, bytes] | None = None) -> Path:
    path = tmp_path / "archive.jar"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, data in (entries if entries is not None else {
            "version.properties": VERSION, "META-INF/MANIFEST.MF": MANIFEST,
            "example/Main.class": b"real archive class bytes", "data/config.txt": b"resource=bound\n",
        }).items():
            archive.writestr(name, data)
    return path


def test_every_resource_and_source_revision_affects_identity(tmp_path: Path):
    path = _jar(tmp_path)
    sigma = jar_content_identity(path, source_revision=REVISION)
    generic = jar_content_identity(path)
    assert sigma.content_sha256 != generic.content_sha256
    assert sigma.archive_sha256 == generic.archive_sha256
    assert sigma.entry_count == 4
    assert sigma.source_revision == REVISION


def test_packaging_and_folded_manifest_timestamp_are_equivalent(tmp_path: Path):
    original = _jar(tmp_path)
    before = jar_content_identity(original, source_revision=REVISION)
    repacked = tmp_path / "repacked.jar"
    with zipfile.ZipFile(original) as source, zipfile.ZipFile(
        repacked, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=1,
    ) as target:
        target.comment = b"different archive-level metadata"
        target.writestr("extra-directory/", b"")
        for entry in reversed(source.infolist()):
            data = source.read(entry)
            if entry.filename == "META-INF/MANIFEST.MF":
                data = data.replace(b"Wed, 21 Oct 2026 1348 -0700",
                                    b"Thu, 22 Oct 2026\r\n  0102 +0000")
            target.writestr(entry.filename, data)
    after = jar_content_identity(repacked, source_revision=REVISION)
    assert before.content_sha256 == after.content_sha256
    assert before.archive_sha256 != after.archive_sha256
    assert before.entry_count == after.entry_count
    assert jar_content_identity(original).content_sha256 != jar_content_identity(repacked).content_sha256


@pytest.mark.parametrize("revision", ["", "d3cc7b4", "X" * 40, "0" * 40])
def test_revision_errors(tmp_path: Path, revision: str):
    with pytest.raises(JarIdentityError, match="revision"):
        jar_content_identity(_jar(tmp_path), source_revision=revision)


@pytest.mark.parametrize("stamp", [b"build.commit=d3cc7b4\nbuild.commit=d3cc7b4\n", b"invalid",
                                    VERSION.replace(b"build.version=3.0.0-d3cc7b4", b"build.version=bad"),
                                    VERSION.replace(b"2026-09-24", b"2026-99-99"),
                                    VERSION + b"extra=value\n", VERSION + b"\xff"])
def test_source_stamp_errors(tmp_path: Path, stamp: bytes):
    path = _jar(tmp_path, {"version.properties": stamp, "META-INF/MANIFEST.MF": MANIFEST})
    with pytest.raises(JarIdentityError):
        jar_content_identity(path, source_revision=REVISION)


@pytest.mark.parametrize("manifest", [
    b" bad continuation\n", b"\n bad continuation\n", b"Manifest-Version: 1.0\n",
    MANIFEST + b"Implementation-Version: 3.0.0 built on Wed, 21 Oct 2026 1348 -0700\n",
    MANIFEST.replace(b"3.0.0 built on", b"3.1.0 built on"),
    MANIFEST.replace(b"Wed, 21 Oct 2026 1348 -0700", b"unrecognized timestamp"),
    MANIFEST.replace(b"Wed, 21 Oct", b"Wed, 99 Oct"),
    MANIFEST.replace(b"Wed, 21 Oct", b"Thu, 21 Oct"),
    MANIFEST.replace(b"1348 -0700", b"1348 -9999"),
    MANIFEST.replace(b"Wed, 21 Oct", b"\xff, 21 Oct"),
])
def test_manifest_errors(tmp_path: Path, manifest: bytes):
    path = _jar(tmp_path, {"version.properties": VERSION, "META-INF/MANIFEST.MF": manifest})
    with pytest.raises(JarIdentityError):
        jar_content_identity(path, source_revision=REVISION)


@pytest.mark.parametrize("missing", ["version.properties", "META-INF/MANIFEST.MF"])
def test_missing_source_metadata(tmp_path: Path, missing: str):
    entries = {"version.properties": VERSION, "META-INF/MANIFEST.MF": MANIFEST}
    entries.pop(missing)
    with pytest.raises(JarIdentityError, match="lacks"):
        jar_content_identity(_jar(tmp_path, entries), source_revision=REVISION)


@pytest.mark.parametrize("name", ["../escape", "/absolute", "a/../b", "a//b", "./bad", "bad\\name"])
def test_unsafe_entry_names(tmp_path: Path, name: str):
    with pytest.raises(JarIdentityError, match="unsafe"):
        jar_content_identity(_jar(tmp_path, {name: b"data"}))


@pytest.mark.parametrize("kind", ["duplicate", "symlink", "compression", "directory-data",
                                 "empty", "directories", "null-name", "encrypted", "oversized",
                                 "crc", "not-zip", "entry-count"])
def test_archive_errors(tmp_path: Path, kind: str):
    path = tmp_path / "archive.jar"
    if kind == "not-zip":
        path.write_bytes(b"invalid archive")
    else:
        with zipfile.ZipFile(path, "w") as archive:
            if kind == "duplicate":
                archive.writestr("duplicate", b"one")
                with pytest.warns(UserWarning, match="Duplicate name"):
                    archive.writestr("duplicate", b"two")
            elif kind == "symlink":
                entry = zipfile.ZipInfo("link")
                entry.create_system = 3
                entry.external_attr = 0o120777 << 16
                archive.writestr(entry, b"target")
            elif kind == "compression":
                archive.writestr("compressed", b"data", compress_type=zipfile.ZIP_BZIP2)
            elif kind == "directory-data":
                archive.writestr("directory/", b"hidden content")
            elif kind == "directories":
                archive.writestr("directory/", b"")
            elif kind == "entry-count":
                for index in range(100_001):
                    archive.writestr(f"file-{index}", b"")
            elif kind != "empty":
                archive.writestr("resource", b"data")
        if kind in {"null-name", "encrypted", "oversized", "crc"}:
            data = bytearray(path.read_bytes())
            central = data.index(b"PK\x01\x02")
            if kind == "null-name":
                data[30] = 0
                data[central + 46] = 0
            elif kind == "encrypted":
                struct.pack_into("<H", data, central + 8, 1)
            elif kind == "oversized":
                struct.pack_into("<I", data, central + 24, 513 << 20)
            elif kind == "crc":
                data[30 + len("resource")] ^= 1
            path.write_bytes(data)
    with pytest.raises(JarIdentityError):
        jar_content_identity(path)


@pytest.mark.parametrize("kind", ["missing", "symlink", "oversized"])
def test_unreadable_source_archive(tmp_path: Path, kind: str):
    path = tmp_path / "unreadable.jar"
    if kind == "symlink":
        path.symlink_to(_jar(tmp_path))
    elif kind == "oversized":
        with path.open("xb") as stream:
            stream.truncate((256 << 20) + 1)
    with pytest.raises(ArtifactError):
        jar_content_identity(path)


def test_binding_schema_is_strict():
    with pytest.raises(ValidationError):
        JarContentBinding(policy="complete-jar-content-v1", content_sha256="0" * 63,
                          source_revision=REVISION)

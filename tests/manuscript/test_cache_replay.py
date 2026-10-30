import hashlib
import json
import os
import shutil
from pathlib import Path

import pytest

from rikishi.cache_inheritance import AUTHORITY
from rikishi.cache_replay import replay_cache
from rikishi.manuscript_provenance import ProvenanceError
from rikishi.runtime_artifacts import ArtifactError


@pytest.fixture
def packet(project_root, tmp_path):
    source = Path(os.environ.get("RIKISHI_CACHE_REPLAY_PACKET", project_root / "output/research/fresh-cache"))
    return Path(shutil.copytree(source, tmp_path / "packet"))


def read(path):
    return json.loads(path.read_bytes())


def save(path, value):
    path.write_text(json.dumps(value))


def rebound(packet, relative, content):
    path = packet / relative
    path.write_bytes(content)
    digest = hashlib.sha256(content).hexdigest()
    for filename in ("bindings-before.json", "bindings-after.json", "adapter-class.json",
                     *(f"{case['name']}/input-bindings.json" for case in read(packet / "result.json")["cases"])):
        manifest = packet / filename
        data = read(manifest)
        for key in data:
            suffix = relative.removeprefix("sources/")
            if key.endswith("/" + suffix):
                data[key] = digest
        save(manifest, data)


def test_saved_packet_verifies_with_zero_byte_process_logs(packet):
    assert (packet / "java-version-stdout.txt").read_bytes() == b""

    replay_cache(packet)


@pytest.mark.parametrize("manifest, mutation, message", [
    ("bindings-after.json", "change", "initial bindings differ from after"),
    ("bindings-after.json", "drop", "initial bindings differ from after"),
    ("bindings-after.json", "extra", "merged before/adapter/input bindings differ"),
    ("bindings-before.json", "drop", "initial binding inventory differs"),
    ("adapter-class.json", "extra", "adapter binding inventory differs"),
    ("fragment-original/input-bindings.json", "drop", "case binding inventory differs"),
    ("fragment-original/input-bindings.json", "extra", "case binding inventory differs"),
])
def test_saved_packet_rejects_incomplete_or_contradictory_manifests(packet, manifest, mutation, message):
    path = packet / manifest
    data = read(path)
    key = next(iter(read(packet / "bindings-before.json"))) if manifest == "bindings-after.json" else next(iter(data))
    if mutation == "change":
        data[key] = "0" * 64
    elif mutation == "drop":
        data.pop(key)
    else:
        data["/unrecorded/extra"] = "0" * 64
    save(path, data)

    with pytest.raises(ProvenanceError, match=message):
        replay_cache(packet)


@pytest.mark.parametrize("relative", [
    "sources/" + AUTHORITY,
    "sources/.rikishi/upstream/sumo/Merge.kif",
    "sources/scripts/runtime/FreshCacheDiagnostic.java",
    "fragment-original/input.kif",
    "fragment-original/sigma/KBs/config.xml",
    "classes/FreshCacheDiagnostic.class",
])
def test_saved_packet_rejects_changed_retained_bytes(packet, relative):
    path = packet / relative
    path.write_bytes(path.read_bytes() + b"\nchanged\n")

    with pytest.raises(ProvenanceError, match="retained authority|retained binding"):
        replay_cache(packet)


def test_saved_packet_rejects_authority_rebound_in_all_manifests(packet):
    relative = "sources/" + AUTHORITY
    data = read(packet / relative)
    data["bindings"][".rikishi/upstream/sumo/Merge.kif"] = "0" * 64
    rebound(packet, relative, json.dumps(data).encode())

    with pytest.raises(ProvenanceError, match="retained authority differs from package"):
        replay_cache(packet)


@pytest.mark.parametrize("relative", [
    "sources/.rikishi/upstream/sumo/Merge.kif",
    "fragment-original/input.kif",
    "fragment-original/sigma/KBs/config.xml",
])
def test_saved_packet_rejects_changed_inputs_even_with_rebound_manifests(packet, relative):
    content = (packet / relative).read_bytes() + b"\n(subclass Changed Entity)\n"
    rebound(packet, relative, content)

    with pytest.raises(ProvenanceError, match="authority binding differs|controlled input differs"):
        replay_cache(packet)


@pytest.mark.parametrize("relative, field, value, message", [
    ("compile-process.json", "returncode", 1, "unsuccessful saved process"),
    ("java-version-process.json", "timed_out", True, "unsuccessful saved process"),
    ("fragment-original/java-process.json", "returncode", 2, "unsuccessful saved process"),
    ("fragment-original/environment.json", "HOME", "/wrong/home", "case environment differs"),
])
def test_saved_packet_rejects_contradictory_process_records(packet, relative, field, value, message):
    path = packet / relative
    data = read(path)
    data[field] = value
    save(path, data)

    with pytest.raises(ProvenanceError, match=message):
        replay_cache(packet)


def test_saved_packet_requires_process_to_use_bound_input(packet):
    path = packet / "fragment-original/java-command.json"
    command = read(path)
    command[-2] = "/different/input.kif"
    save(path, command)

    with pytest.raises(ProvenanceError, match="saved command differs"):
        replay_cache(packet)


@pytest.mark.parametrize("relative", [
    "sources/.rikishi/upstream/sumo/Merge.kif", "compile-process.json",
    "fragment-original/java-stdout.txt", "fragment-original/java-stderr.txt",
])
def test_saved_packet_rejects_missing_custody_files(packet, relative):
    path = packet / relative
    path.rename(path.with_name(path.name + ".removed"))

    with pytest.raises((ProvenanceError, ArtifactError), match="sources missing|cannot inspect|cannot read"):
        replay_cache(packet)


@pytest.mark.parametrize("field", ["content_sha256", "archive_sha256"])
def test_saved_packet_rejects_dependency_content_receipt_contradiction(packet, field):
    path = packet / "jar-content.json"
    data = read(path)
    dependency = next(key for key in data if "/lib/" in key)
    data[dependency][field] = "0" * 64
    save(path, data)

    with pytest.raises(ProvenanceError, match="JAR authority or archive binding differs"):
        replay_cache(packet)


def test_saved_packet_rejects_changed_sigma_archive(packet):
    path = packet / "sources/.rikishi/upstream/sigmakee/build/sigmakee.jar"
    path.write_bytes(path.read_bytes() + b"changed archive custody")

    with pytest.raises(ProvenanceError, match="retained binding differs"):
        replay_cache(packet)


def test_saved_packet_rejects_contradictory_sigma_version_copy(packet):
    path = packet / "sources/sigma-version.properties"
    path.write_bytes(path.read_bytes() + b"changed=true\n")

    with pytest.raises(ProvenanceError, match="retained Sigma version stamp differs"):
        replay_cache(packet)


def test_saved_packet_rejects_contradictory_sigma_class_digest(packet):
    path = packet / "jar-classes.json"
    data = read(path)
    key = next(key for key in data if key.endswith("/build/sigmakee.jar"))
    data[key] = "0" * 64
    save(path, data)

    with pytest.raises(ProvenanceError, match="supplementary Sigma classes differ"):
        replay_cache(packet)


def test_saved_packet_does_not_consult_original_absolute_paths(packet):
    before = read(packet / "bindings-before.json")
    authority_key = next(key for key in before if key.endswith("/" + AUTHORITY))
    origin = authority_key.removesuffix("/" + AUTHORITY)
    inaccessible = "/recorded-on-another-machine/rikishi"
    assert not Path(inaccessible).exists()
    json_files = [path for path in packet.rglob("*.json") if "sources" not in path.relative_to(packet).parts]
    for path in json_files:
        path.write_text(json.dumps(read(path)).replace(origin, inaccessible))
    environment = "sources/.rikishi/runtime/environment.json"
    rebound(packet, environment, (packet / environment).read_bytes().replace(origin.encode(), inaccessible.encode()))

    replay_cache(packet)

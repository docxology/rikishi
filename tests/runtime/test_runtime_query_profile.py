import hashlib
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from rikishi.runtime_artifacts import ArtifactError
from rikishi.runtime_query_profile import (
    prepare_profile,
    snapshot_profile,
    verify_copied_inputs,
    verify_profile,
)


@pytest.fixture
def profile(tmp_path: Path) -> Path:
    source = tmp_path / "source"
    kb = source / "KBs"
    kb.mkdir(parents=True)
    (source / "graph").mkdir()
    (kb / "tests").mkdir()
    (kb / "Merge.kif").write_bytes(b"(subclass Human Animal)\n")
    (kb / "kbmanager.ser").write_bytes(bytes(range(256)) * 16)
    (kb / "config.xml").write_text(
        f'<configuration><preference name="baseDir" value="{source}"/>'
        f'<preference name="kbDir" value="{kb}"/>'
        f'<preference name="graphDir" value="{source / "graph"}"/>'
        '<kb name="SUMO"><constituent filename="Merge.kif"/></kb></configuration>'
    )
    return source


def test_two_profile_preparations_freeze_identical_bytes_and_independent_outputs(
    profile: Path, tmp_path: Path,
) -> None:
    original = snapshot_profile(profile)
    outputs = [tmp_path / "first", tmp_path / "second"]
    with ThreadPoolExecutor(max_workers=2) as pool:
        snapshots = list(pool.map(lambda target: prepare_profile(profile, target), outputs))
    assert snapshots == [original, original]
    manifest = json.loads(original.manifest())
    assert len(manifest["files"]) == 3
    for target in outputs:
        for item in original.files:
            copied = target / item.path
            assert hashlib.sha256(copied.read_bytes()).hexdigest() == item.sha256
            assert copied.stat().st_mtime_ns == item.mtime_ns
    (outputs[0] / "KBs/kbmanager.ser").write_bytes(b"isolated replacement")
    assert (outputs[1] / "KBs/kbmanager.ser").read_bytes() == (profile / "KBs/kbmanager.ser").read_bytes()
    verify_profile(original)


@pytest.mark.parametrize("entry", ["link-file", "link-directory", "fifo"])
def test_profile_rejects_unsafe_entries_before_creating_copy(
    profile: Path, tmp_path: Path, entry: str,
) -> None:
    unsafe = profile / "unsafe"
    if entry == "fifo":
        os.mkfifo(unsafe)
    else:
        unsafe.symlink_to(profile / ("KBs" if entry == "link-directory" else "KBs/Merge.kif"))
    with pytest.raises(ArtifactError, match="unsupported Sigma profile entry"):
        prepare_profile(profile, tmp_path / "copy")
    assert not (tmp_path / "copy").exists()


@pytest.mark.parametrize("change", ["cache", "constituent", "mtime", "new-file"])
def test_profile_binding_rejects_changed_input_after_preparation(
    profile: Path, tmp_path: Path, change: str,
) -> None:
    snapshot = prepare_profile(profile, tmp_path / "copy")
    target = profile / "KBs/kbmanager.ser"
    if change == "mtime":
        current = target.stat().st_mtime_ns
        os.utime(target, ns=(current + 1_000_000, current + 1_000_000))
    elif change == "constituent":
        (profile / "KBs/Merge.kif").write_text("(subclass Human Artifact)\n")
    elif change == "new-file":
        (profile / "added").write_text("new input")
    else:
        target.write_bytes(b"modified serialized cache")
    with pytest.raises(ArtifactError, match="source profile changed"):
        verify_profile(snapshot)


@pytest.mark.parametrize("name,value", [
    ("baseDir", "/unrelated"), ("kbDir", "/unrelated"),
    ("graphDir", "/"), ("inferenceTestDir", "/"), ("verbnetDir", "/"),
])
def test_profile_rejects_unisolated_directories(
    profile: Path, tmp_path: Path, name: str, value: str,
) -> None:
    config = profile / "KBs/config.xml"
    from xml.etree import ElementTree

    tree = ElementTree.parse(config)
    root = tree.getroot()
    for preference in list(root.findall("preference")):
        if preference.attrib["name"] == name:
            root.remove(preference)
    ElementTree.SubElement(root, "preference", {"name": name, "value": value})
    tree.write(config)
    with pytest.raises(ArtifactError):
        prepare_profile(profile, tmp_path / "copy")
    assert not (tmp_path / "copy").exists()


@pytest.mark.parametrize("filename", ["../Merge.kif", "/elsewhere/Merge.kif", "."])
def test_profile_rejects_escaping_constituents(
    profile: Path, tmp_path: Path, filename: str,
) -> None:
    config = profile / "KBs/config.xml"
    config.write_text(config.read_text().replace('filename="Merge.kif"', f'filename="{filename}"'))
    with pytest.raises(ArtifactError, match="safe relative paths"):
        prepare_profile(profile, tmp_path / "copy")


def test_profile_rejects_constituent_that_differs_from_configured_source(
    profile: Path, tmp_path: Path,
) -> None:
    upstream = tmp_path / "upstream"
    upstream.mkdir()
    (upstream / "Merge.kif").write_text("(subclass Human Artifact)\n")
    config = profile / "KBs/config.xml"
    config.write_text(config.read_text().replace(
        "<configuration>", f'<configuration><preference name="sumoDir" value="{upstream}"/>'
    ))
    with pytest.raises(ArtifactError, match="differs from its configured source"):
        prepare_profile(profile, tmp_path / "copy")


def test_profile_rejects_destination_inside_original(profile: Path) -> None:
    with pytest.raises(ArtifactError, match="inside its source profile"):
        prepare_profile(profile, profile / "copy")
    assert not (profile / "copy").exists()


@pytest.mark.parametrize("change", ["cache", "constituent", "mtime", "link"])
def test_copied_inputs_remain_bound_after_native_output(
    profile: Path, tmp_path: Path, change: str,
) -> None:
    destination = tmp_path / "copy"
    snapshot = prepare_profile(profile, destination)
    (destination / "KBs/temp-comb.tptp").write_text("new generated problem")
    verify_copied_inputs(snapshot, destination, after_execution=True)
    target = destination / "KBs/kbmanager.ser"
    if change == "mtime":
        current = target.stat().st_mtime_ns
        os.utime(target, ns=(current + 1_000_000, current + 1_000_000))
    elif change == "constituent":
        (destination / "KBs/Merge.kif").write_text("(subclass Human Artifact)\n")
    elif change == "link":
        target.rename(destination / "preserved-cache")
        target.symlink_to(destination / "preserved-cache")
    else:
        target.write_bytes(b"modified cache")
    with pytest.raises(ArtifactError):
        verify_copied_inputs(snapshot, destination, after_execution=True)


def test_duplicate_preferences_cannot_select_an_unbound_profile(profile: Path, tmp_path: Path) -> None:
    config = profile / "KBs/config.xml"
    config.write_text(config.read_text().replace(
        "<configuration>", f'<configuration><preference name="baseDir" value="{profile}"/>'
    ))
    with pytest.raises(ArtifactError, match="duplicate Sigma profile preferences"):
        prepare_profile(profile, tmp_path / "copy")


def test_real_partial_copy_failure_cannot_produce_a_query_result(
    profile: Path, tmp_path: Path,
) -> None:
    runtime = tmp_path / ".rikishi/runtime"
    runtime.mkdir(parents=True)
    (runtime / "environment.json").write_text(json.dumps({"SIGMA_HOME": str(profile), "SIGMA_SRC": "unused"}))
    output = tmp_path / "query.log"
    # Keep the real copy fault, then restore the limit before subprocess coverage saves.
    script = (
        "import resource, sys\nfrom pathlib import Path\n"
        "from rikishi.runtime_query import run_query\n"
        "original = resource.getrlimit(resource.RLIMIT_FSIZE)\n"
        "resource.setrlimit(resource.RLIMIT_FSIZE, (1024, original[1]))\n"
        "try:\n"
        " assert resource.getrlimit(resource.RLIMIT_FSIZE)[0] == 1024\n"
        " run_query(Path(sys.argv[1]), '(subclass Human Animal)', output=Path(sys.argv[2]))\n"
        "finally:\n"
        " resource.setrlimit(resource.RLIMIT_FSIZE, original)\n"
    )
    result = subprocess.run([sys.executable, "-c", script, str(tmp_path), str(output)],
                            capture_output=True, text=True, timeout=10, check=False)
    assert result.returncode != 0
    assert "File too large" in result.stderr
    artifacts = output.with_suffix(".log.artifacts")
    assert (artifacts / "sigma-profile/KBs/Merge.kif").is_file()
    assert not output.exists()
    assert not output.with_suffix(".log.result.json").exists()
    assert not (artifacts / "capture.json").exists()

import hashlib
import subprocess

import pytest

from rikishi.runtime_setup import apply_compatibility_patch, copy_corpus, ensure_repository


def test_interrupted_git_checkout_resumes_and_preserves_wrong_pin(tmp_path):
    ensure = ensure_repository
    source = tmp_path / "origin"
    subprocess.run(["git", "init", str(source)], check=True, capture_output=True)
    (source / "Merge.kif").write_text("(subclass Human Animal)")
    subprocess.run(["git", "add", "."], cwd=source, check=True, capture_output=True)
    subprocess.run(["git", "-c", "user.name=Runtime Test", "-c", "user.email=test@example.invalid",
                    "-c", "commit.gpgsign=false", "commit", "-m", "fixture"], cwd=source,
                   check=True, capture_output=True)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
    pin = {"url": str(source), "commit": commit}
    destination = tmp_path / "interrupted"
    subprocess.run(["git", "init", str(destination)], check=True, capture_output=True)
    with pytest.raises(subprocess.CalledProcessError):
        ensure(destination, {"url": str(tmp_path / "absent"), "commit": commit})
    ensure(destination, pin)
    assert (destination / "Merge.kif").read_text() == "(subclass Human Animal)"
    ensure(destination, pin)
    with pytest.raises(RuntimeError, match="refusing reset"):
        ensure(destination, dict(pin, commit="0" * 40))
    ensure(tmp_path / "fresh", pin)
    interrupted_dirty = tmp_path / "dirty"
    subprocess.run(["git", "init", str(interrupted_dirty)], check=True, capture_output=True)
    (interrupted_dirty / "owned.txt").write_text("preserve")
    with pytest.raises(RuntimeError, match="local files"):
        ensure(interrupted_dirty, pin)
    assert (interrupted_dirty / "owned.txt").read_text() == "preserve"


def test_sigma_copy_pin_guard_and_partial_resume(tmp_path):
    copy = copy_corpus
    source = tmp_path / "source"
    source.mkdir()
    (source / ".git").mkdir()
    (source / "Merge.kif").write_text("complete")
    (source / "nested").mkdir()
    (source / "nested/data.kif").write_text("nested")
    kb = tmp_path / "sigma/KBs"
    kb.mkdir(parents=True)
    (kb / "Merge.kif").write_text("legacy data")
    with pytest.raises(RuntimeError, match="unmarked Sigma file differs"):
        copy(source, kb, "pin-one")
    assert (kb / "Merge.kif").read_text() == "legacy data"
    (kb / "Merge.kif").write_text("complete")
    copy(source, kb, "pin-one")
    assert (kb / "Merge.kif").read_text() == "complete"
    assert (kb / "nested/data.kif").read_text() == "nested"
    assert not (kb / ".git").exists()
    (kb / "Merge.kif").write_text("local editing preserved")
    copy(source, kb, "pin-one")
    assert (kb / "Merge.kif").read_text() == "local editing preserved"
    with pytest.raises(RuntimeError, match="different SUMO pin"):
        copy(source, kb, "pin-two")


def test_compatibility_patch_integrity_and_idempotence(tmp_path):
    apply = apply_compatibility_patch
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    target = tmp_path / "fixture.txt"
    target.write_text("original\n")
    patch = tmp_path / "fix.patch"
    patch.write_text("diff --git a/fixture.txt b/fixture.txt\n--- a/fixture.txt\n+++ b/fixture.txt\n"
                     "@@ -1 +1 @@\n-original\n+corrected\n")
    specification = {"path": str(patch), "source": "fixture.txt",
                     "sha256": hashlib.sha256(patch.read_bytes()).hexdigest(),
                     "before_sha256": hashlib.sha256(b"original\n").hexdigest(),
                     "after_sha256": hashlib.sha256(b"corrected\n").hexdigest()}
    apply(tmp_path, specification)
    assert target.read_text() == "corrected\n"
    apply(tmp_path, specification)
    with pytest.raises(RuntimeError, match="patch checksum mismatch"):
        apply(tmp_path, dict(specification, sha256="incorrect"))
    target.write_text("user edits\n")
    with pytest.raises(RuntimeError, match="unexpected edits"):
        apply(tmp_path, specification)
    assert target.read_text() == "user edits\n"

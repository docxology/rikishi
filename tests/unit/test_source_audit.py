import subprocess

from rikishi.source_audit import audit_sources


def test_current_source_is_verified_without_mutating_index(tmp_path, corpus_factory):
    index = corpus_factory(tmp_path, {"Merge.kif": "(subclass Human Animal)"})
    before = index.path.read_bytes()
    audit = audit_sources(index)
    assert audit.passed is True
    assert audit.unchanged_files == 1
    assert audit.revision_matches is None
    assert audit.current_clean is None
    assert audit.to_dict()["matches_index"] is True
    assert index.path.read_bytes() == before


def test_changed_missing_added_and_escaping_sources_fail(tmp_path, corpus_factory):
    index = corpus_factory(tmp_path, {"Merge.kif": "(subclass Human Animal)",
                                      "removed.kif": "(instance Ada Human)"})
    (tmp_path / "source/Merge.kif").write_text("(subclass Human Entity)")
    (tmp_path / "source/removed.kif").unlink()
    (tmp_path / "source/new.kif").write_text("(instance Grace Human)")
    outside = tmp_path / "outside.kif"
    outside.write_bytes(b"\xff")
    (tmp_path / "source/escape.kif").symlink_to(outside)
    audit = audit_sources(index)
    assert audit.passed is False
    assert audit.modified == ("Merge.kif",)
    assert audit.missing == ("removed.kif",)
    assert audit.added == ("escape.kif", "new.kif")
    assert audit.escaped_paths == ("escape.kif",)
    assert audit.unchanged_files == 0


def test_committed_revision_and_worktree_observations_are_separate(
    tmp_path, corpus_factory, git_commit
):
    index = corpus_factory(tmp_path, {"Merge.kif": "(subclass Human Animal)"})
    source = tmp_path / "source"
    revision = git_commit(source)
    index.build(source)
    audit = audit_sources(index)
    assert audit.revision_matches is True
    assert audit.indexed_commit == revision
    assert audit.current_clean is True
    (source / "notes.md").write_text("An unrelated working note")
    dirty = audit_sources(index)
    assert dirty.matches_index is True
    assert dirty.current_clean is False
    subprocess.run(["git", "-C", str(source), "add", "."], check=True)
    subprocess.run(["git", "-C", str(source), "-c", "user.name=Fixture", "-c",
                    "user.email=fixture@example.invalid", "commit", "-m", "Notes"],
                   check=True, capture_output=True)
    changed_revision = audit_sources(index)
    assert changed_revision.matches_index is True
    assert changed_revision.revision_matches is False
    assert changed_revision.passed is False


def test_rejected_file_never_becomes_complete_source_agreement(tmp_path, corpus_factory):
    index = corpus_factory(tmp_path, {"Merge.kif": "(subclass Human Animal)",
                                      "bad.kif": "("})
    audit = audit_sources(index)
    assert audit.parse_failures_at_index == 1
    assert audit.passed is False

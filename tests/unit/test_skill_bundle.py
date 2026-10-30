import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Literal, assert_never

import pytest

from rikishi.skill_bundle import SkillBundleError, main, sync_skill_bundle


def _snapshot(directory: Path) -> tuple[tuple[str, bytes | None], ...]:
    return tuple((path.relative_to(directory).as_posix(),
                  path.read_bytes() if path.is_file() else None)
                 for path in sorted(directory.rglob("*")))


@pytest.fixture
def bundle(project_root: Path, tmp_path: Path) -> Path:
    root = tmp_path / "repository"
    source = root / ".agents/skills"
    shutil.copytree(project_root / ".agents/skills", source)
    (source / "rikishi-fep/assets").mkdir()
    (source / "rikishi-fep/assets/example.bin").write_bytes(b"\x00\xff\r\n")
    shutil.copytree(source, root / "skills")
    return root


def test_check_is_exact_and_read_only(bundle: Path) -> None:
    before = _snapshot(bundle)

    files = sync_skill_bundle(bundle)

    assert files == (
        "rikishi-fep/SKILL.md", "rikishi-fep/assets/example.bin",
        "rikishi-operator/SKILL.md",
    )
    assert _snapshot(bundle) == before


def test_export_projects_actual_authored_skills(project_root: Path, tmp_path: Path) -> None:
    source = tmp_path / ".agents/skills"
    shutil.copytree(project_root / ".agents/skills", source)
    before = _snapshot(source)

    files = sync_skill_bundle(tmp_path, write=True)

    assert files == tuple(path for path, content in before if content is not None)
    assert _snapshot(tmp_path / "skills") == before
    assert _snapshot(source) == before
    assert sync_skill_bundle(tmp_path) == files


@pytest.mark.parametrize("remove", [False, True])
def test_check_rejects_changed_or_missing_bytes_without_writes(bundle: Path, remove: bool) -> None:
    copy = bundle / "skills/rikishi-fep/SKILL.md"
    if remove:
        copy.unlink()
    else:
        copy.write_bytes(copy.read_bytes() + b"\r\nchanged\x00")
    before = _snapshot(bundle)

    with pytest.raises(SkillBundleError, match="missing copy" if remove else "changed copy"):
        sync_skill_bundle(bundle)

    assert _snapshot(bundle) == before


def test_export_repairs_changed_missing_and_empty_directory_copies(bundle: Path) -> None:
    source = bundle / ".agents/skills"
    (source / "rikishi-operator/empty").mkdir()
    (bundle / "skills/rikishi-fep/SKILL.md").write_bytes(b"changed")
    (bundle / "skills/rikishi-operator/SKILL.md").unlink()
    before = _snapshot(source)

    sync_skill_bundle(bundle, write=True)

    assert _snapshot(bundle / "skills") == before
    assert _snapshot(source) == before


@pytest.mark.parametrize("write", [False, True])
@pytest.mark.parametrize("relative,content", [
    ("stray.md", b"preserve me"), ("rogue/SKILL.md", b"preserve me"), ("empty", None),
])
def test_unexpected_copies_are_rejected_before_any_repairs(
    bundle: Path, write: bool, relative: str, content: bytes | None,
) -> None:
    unexpected = bundle / "skills" / relative
    unexpected.parent.mkdir(parents=True, exist_ok=True)
    if content is None:
        unexpected.mkdir()
    else:
        unexpected.write_bytes(content)
    (bundle / "skills/rikishi-fep/SKILL.md").write_bytes(b"also changed")
    before = _snapshot(bundle)

    with pytest.raises(SkillBundleError, match="unexpected copy"):
        sync_skill_bundle(bundle, write=write)

    assert _snapshot(bundle) == before


@pytest.mark.parametrize("relative", [
    ".agents", ".agents/skills", ".agents/skills/rikishi-fep",
    ".agents/skills/rikishi-fep/SKILL.md", "skills", "skills/rikishi-fep",
    "skills/rikishi-fep/SKILL.md",
])
@pytest.mark.parametrize("write", [False, True])
def test_symlinked_tree_paths_are_rejected_and_targets_preserved(
    bundle: Path, tmp_path: Path, relative: str, write: bool,
) -> None:
    path = bundle / relative
    outside = tmp_path / "outside"
    path.rename(outside)
    path.symlink_to(outside, target_is_directory=outside.is_dir())
    before = outside.read_bytes() if outside.is_file() else _snapshot(outside)

    with pytest.raises(SkillBundleError, match="symlink"):
        sync_skill_bundle(bundle, write=write)

    assert path.is_symlink()
    assert (outside.read_bytes() if outside.is_file() else _snapshot(outside)) == before


@pytest.mark.parametrize("relative", [".agents/skills/broken", "skills/broken"])
def test_broken_symlinks_are_rejected(bundle: Path, relative: str) -> None:
    path = bundle / relative
    path.symlink_to("absent")

    with pytest.raises(SkillBundleError, match="symlink"):
        sync_skill_bundle(bundle, write=True)

    assert path.is_symlink()
    assert not path.exists()


@pytest.mark.parametrize("relative", [".agents/skills/pipe", "skills/pipe"])
def test_special_files_are_rejected_without_opening_them(bundle: Path, relative: str) -> None:
    path = bundle / relative
    os.mkfifo(path)

    with pytest.raises(SkillBundleError, match="not a regular file or directory"):
        sync_skill_bundle(bundle, write=True)

    assert path.exists()


@pytest.mark.parametrize("relative", [".", ".agents", ".agents/skills", "skills"])
@pytest.mark.parametrize("create_file", [False, True])
def test_missing_or_file_directories_fail_safely(
    tmp_path: Path, relative: str, create_file: bool,
) -> None:
    root = tmp_path / "repository"
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if relative == "skills":
        authority = root / ".agents/skills/rikishi-fep"
        authority.mkdir(parents=True)
        (authority / "SKILL.md").write_bytes(b"authored")
    if create_file:
        path.write_bytes(b"preserve me")

    if relative == "skills" and not create_file:
        assert sync_skill_bundle(root, write=True) == ("rikishi-fep/SKILL.md",)
    else:
        with pytest.raises(SkillBundleError, match="directory|root"):
            sync_skill_bundle(root, write=True)
    if create_file:
        assert path.read_bytes() == b"preserve me"


def test_symlink_repository_root_is_rejected(bundle: Path, tmp_path: Path) -> None:
    alias = tmp_path / "alias"
    alias.symlink_to(bundle, target_is_directory=True)
    before = _snapshot(bundle)

    with pytest.raises(SkillBundleError, match="symlink repository root"):
        sync_skill_bundle(alias, write=True)

    assert _snapshot(bundle) == before


def test_empty_authority_does_not_replace_distribution(tmp_path: Path) -> None:
    (tmp_path / ".agents/skills").mkdir(parents=True)
    copies = tmp_path / "skills"
    copies.mkdir()
    (copies / "retained.md").write_bytes(b"preserve me")
    before = _snapshot(tmp_path)

    with pytest.raises(SkillBundleError, match="authored skill tree has no files"):
        sync_skill_bundle(tmp_path, write=True)

    assert _snapshot(tmp_path) == before


def test_export_replaces_hardlink_without_mutating_other_owner(bundle: Path, tmp_path: Path) -> None:
    outside = tmp_path / "outside.md"
    outside.write_bytes(b"independent owner")
    copy = bundle / "skills/rikishi-fep/SKILL.md"
    copy.unlink()
    copy.hardlink_to(outside)

    sync_skill_bundle(bundle, write=True)

    assert copy.read_bytes() == (bundle / ".agents/skills/rikishi-fep/SKILL.md").read_bytes()
    assert outside.read_bytes() == b"independent owner"
    assert not copy.samefile(outside)


def test_cli_main_returns_machine_readable_checked_paths(bundle: Path, capsys: pytest.CaptureFixture[str]) -> None:
    result = main(["--root", str(bundle)])

    captured = capsys.readouterr()
    assert result == 0
    assert json.loads(captured.out) == {"mode": "check", "files": list(sync_skill_bundle(bundle))}
    assert captured.err == ""


def test_cli_main_reports_errors_without_success_output(bundle: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (bundle / "skills/rikishi-fep/SKILL.md").write_bytes(b"changed")

    with pytest.raises(SystemExit) as error:
        main(["--root", str(bundle)])

    captured = capsys.readouterr()
    assert error.value.code == 1
    assert captured.out == ""
    assert "changed copy: rikishi-fep/SKILL.md" in captured.err


@pytest.mark.parametrize("write", [False, True])
def test_real_cli_checks_or_exports_authored_bytes(bundle: Path, project_root: Path, write: bool) -> None:
    command = [sys.executable, str(project_root / "scripts/sync_skills.py")]
    if write:
        (bundle / "skills/rikishi-fep/SKILL.md").write_bytes(b"changed")
        command += ["--root", str(bundle), "--write"]

    result = subprocess.run(
        command, cwd=bundle, capture_output=True, text=True, timeout=30, check=False,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "mode": "write" if write else "check", "files": list(sync_skill_bundle(bundle)),
    }


@pytest.mark.parametrize("mutation", ["altered", "missing", "unexpected"])
def test_real_cli_rejects_drift_without_writes(
    bundle: Path, project_root: Path, mutation: Literal["altered", "missing", "unexpected"],
) -> None:
    copy = bundle / "skills/rikishi-fep/SKILL.md"
    match mutation:
        case "altered":
            copy.write_bytes(b"changed")
        case "missing":
            copy.unlink()
        case "unexpected":
            (bundle / "skills/unexpected.md").write_bytes(b"preserve me")
        case unreachable:
            assert_never(unreachable)
    before = _snapshot(bundle)

    result = subprocess.run(
        [sys.executable, str(project_root / "scripts/sync_skills.py"), "--root", str(bundle)],
        capture_output=True, text=True, timeout=30, check=False,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert "copy:" in result.stderr
    assert _snapshot(bundle) == before

"""Reject unsafe or invalid requests before any native process can start."""

from pathlib import Path

import pytest

from rikishi.bridge_models import BridgeError
from rikishi.bridge_runner import run_bridge
from rikishi.runtime_artifacts import ArtifactError


@pytest.mark.parametrize("timeout", [0, 301, True, 1.5])
def test_invalid_timeout_rejected_without_creating_output(tmp_path: Path, timeout: int) -> None:
    output = tmp_path / "uncreated"
    with pytest.raises(BridgeError, match="integer timeout"):
        run_bridge(tmp_path, output, timeout=timeout)
    assert not output.exists()


def test_occupied_directory_is_preserved_before_canonical_or_native_access(tmp_path: Path) -> None:
    output = tmp_path / "occupied"
    output.mkdir()
    marker = output / "owner.txt"
    marker.write_text("preserve owner")
    with pytest.raises(FileExistsError):
        run_bridge(tmp_path, output)
    assert marker.read_text() == "preserve owner"


def test_escaping_output_rejected_before_source_or_tool_access(tmp_path: Path) -> None:
    with pytest.raises(BridgeError, match="inside the repository"):
        run_bridge(tmp_path, tmp_path.parent / "outside")


def test_symlinked_output_ancestor_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(target, target_is_directory=True)
    with pytest.raises(ArtifactError, match="symlink"):
        run_bridge(tmp_path, alias / "new-output")
    assert list(target.iterdir()) == []

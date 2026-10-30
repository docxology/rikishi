"""Exercise real fixture Git operations under a controlled ambient monitor."""

import os
import subprocess
import sys
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest


@dataclass(frozen=True, slots=True)
class MonitorInputs:
    config: Path
    config_bytes: bytes
    marker: Path


@pytest.fixture
def monitor_global(tmp_path: Path) -> Iterator[MonitorInputs]:
    """Select an actual temporary Git global config and restore the environment."""
    marker = tmp_path / "monitor-invocations"
    hook = tmp_path / "monitor.py"
    hook.write_text(
        f"#!{sys.executable}\n"
        "from pathlib import Path\nimport sys\n"
        f"with Path({str(marker)!r}).open('ab') as stream:\n"
        "    stream.write(b'invoked\\n')\n"
        "sys.stdout.buffer.write(b'fixture-token\\0/\\0')\n",
        encoding="utf-8",
    )
    hook.chmod(0o700)
    config = tmp_path / "isolated.gitconfig"
    subprocess.run(["git", "config", "--file", str(config), "core.fsmonitor", str(hook)],
                   check=True, capture_output=True)
    original = {key: os.environ.get(key) for key in ("GIT_CONFIG_GLOBAL", "GIT_CONFIG_NOSYSTEM")}
    os.environ.update(GIT_CONFIG_GLOBAL=str(config), GIT_CONFIG_NOSYSTEM="1")
    try:
        yield MonitorInputs(config, config.read_bytes(), marker)
    finally:
        for key, value in original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def test_real_monitor_observes_unisolated_git(tmp_path: Path, monitor_global: MonitorInputs) -> None:
    """Calibrate the real hook before relying on its absence as an oracle."""
    source = tmp_path / "unisolated"
    source.mkdir()
    (source / "Merge.kif").write_text("(subclass Human Animal)\n", encoding="utf-8")
    subprocess.run(["git", "init", "-b", "main", str(source)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(source), "add", "."], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(source), "-c", "user.name=Fixture", "-c",
                    "user.email=fixture@example.invalid", "commit", "-m", "Fixture"],
                   check=True, capture_output=True)
    assert monitor_global.marker.read_bytes().splitlines()
    assert monitor_global.config.read_bytes() == monitor_global.config_bytes


def test_shared_git_fixture_isolates_ambient_monitor(
    tmp_path: Path, monitor_global: MonitorInputs, git_commit: Callable[[Path], str],
) -> None:
    """Real commits and dirty-file detection must not call an ambient monitor."""
    source = tmp_path / "isolated"
    source.mkdir()
    formula = b"(subclass Human Animal)\n"
    (source / "Merge.kif").write_bytes(formula)
    revision = git_commit(source)
    committed = subprocess.run(["git", "-C", str(source), "show", "HEAD:Merge.kif"],
                               check=True, capture_output=True)
    head = subprocess.run(["git", "-C", str(source), "rev-parse", "HEAD"],
                          check=True, capture_output=True, text=True)
    (source / "Merge.kif").write_text("(subclass Human Entity)\n", encoding="utf-8")
    dirty = subprocess.run(["git", "-C", str(source), "status", "--porcelain"],
                           check=True, capture_output=True, text=True)
    assert committed.stdout == formula
    assert head.stdout.strip() == revision
    assert dirty.stdout.strip() == "M Merge.kif"
    assert not monitor_global.marker.exists()
    assert monitor_global.config.read_bytes() == monitor_global.config_bytes

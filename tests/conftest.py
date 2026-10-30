import os
import subprocess
from collections.abc import Callable, Mapping
from contextlib import redirect_stdout
from dataclasses import dataclass
from hashlib import sha256
from io import StringIO
from pathlib import Path
from uuid import uuid4

import pytest

from rikishi.bridge_models import BridgeReport
from rikishi.ontology import OntologyIndex
from rikishi.portable_inputs import PortableInputs, load_portable_inputs

pytest_plugins = ("fixtures.receipt_schema", "fixtures.prerequisites")


@dataclass(frozen=True, slots=True)
class BridgePacket:
    root: Path
    path: Path
    sha256: str
    report: BridgeReport


@pytest.fixture(scope="session")
def bridge_packet(project_root: Path, native_workspace: Path) -> BridgePacket:
    """Share one real campaign; explicit digest-bound reuse serves replay-only checks."""
    from rikishi.bridge_replay import validate_bridge_report
    from rikishi.cli import main

    selected = os.environ.get("RIKISHI_BRIDGE_TEST_PACKET")
    digest = os.environ.get("RIKISHI_BRIDGE_TEST_SHA256")
    if bool(selected) != bool(digest):
        raise pytest.UsageError("Bridge packet reuse requires both packet path and trusted SHA-256")
    if selected is not None and digest is not None:
        path = Path(selected)
        if not path.is_absolute():
            path = project_root / path
        if path.is_dir():
            path = path / "bridge-report.json"
        report = validate_bridge_report(path, trusted_report_sha256=digest)
        return BridgePacket(project_root, path, digest, report)
    output = native_workspace / f"bridge-tests-{uuid4().hex}"
    with redirect_stdout(StringIO()) as captured:
        status = main(["--root", str(project_root), "bridge-run", str(output),
                       "--prover", "both", "--timeout", "10"])
    transcript = output.parent / f"{output.name}-cli.json"
    transcript.write_text(captured.getvalue())
    if status != 0:
        pytest.fail(f"Fresh bridge CLI campaign failed; retained output: {transcript}")
    path = output / "bridge-report.json"
    digest = sha256(path.read_bytes()).hexdigest()
    report = validate_bridge_report(path, trusted_report_sha256=digest)
    return BridgePacket(project_root, path, digest, report)


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Locate the checkout independently of each test module's nesting depth."""
    return Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def native_workspace(project_root: Path) -> Path:
    """Retain fresh native outputs without depending on a historical campaign."""
    from rikishi.runtime_artifacts import checked_source_path

    parent = checked_source_path(project_root / ".rikishi")
    directory = parent / f"native-tests-{uuid4().hex}"
    directory.mkdir()
    return directory


@pytest.fixture(scope="session")
def portable_inputs(project_root: Path) -> PortableInputs:
    selected = os.environ.get("RIKISHI_PORTABLE_INPUTS")
    if not selected:
        raise pytest.UsageError(
            "RIKISHI_PORTABLE_INPUTS is required. Run python scripts/prepare_portable_inputs.py "
            "--output .rikishi/portable-inputs/default, then set RIKISHI_PORTABLE_INPUTS "
            "to that directory. No historical research-output fallback is used."
        )
    directory = Path(selected)
    if not directory.is_absolute():
        directory = project_root / directory
    return load_portable_inputs(directory)


@pytest.fixture
def git_commit() -> Callable[[Path], str]:
    """Commit real fixture files without an inherited filesystem monitor."""
    def commit(directory: Path) -> str:
        subprocess.run(["git", "-c", "core.fsmonitor=false", "init", "-b", "main", str(directory)],
                       check=True, capture_output=True)
        command = ["git", "-c", "core.fsmonitor=false", "-C", str(directory)]
        subprocess.run([*command, "config", "--local", "core.fsmonitor", "false"],
                       check=True, capture_output=True)
        subprocess.run([*command, "add", "."], check=True, capture_output=True)
        subprocess.run([*command, "-c", "user.name=Fixture", "-c",
                        "user.email=fixture@example.invalid", "commit", "-m", "Fixture"],
                       check=True, capture_output=True)
        return subprocess.run([*command, "rev-parse", "HEAD"], check=True,
                              capture_output=True, text=True).stdout.strip()
    return commit


@pytest.fixture
def corpus_factory() -> Callable[[Path, Mapping[str, str]], OntologyIndex]:
    """Build an actual index from explicitly supplied source files."""
    def build(directory: Path, files: Mapping[str, str]) -> OntologyIndex:
        source = directory / "source"
        for relative, text in files.items():
            path = source / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        index = OntologyIndex(directory / "index.sqlite")
        index.build(source)
        return index
    return build

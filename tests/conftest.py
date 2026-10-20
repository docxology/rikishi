import subprocess
from collections.abc import Callable, Mapping
from pathlib import Path

import pytest

from rikishi.ontology import OntologyIndex


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Locate the checkout independently of each test module's nesting depth."""
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def git_commit() -> Callable[[Path], str]:
    """Commit real fixture files using repository-local identity only."""
    def commit(directory: Path) -> str:
        subprocess.run(["git", "init", "-b", "main", str(directory)],
                       check=True, capture_output=True)
        command = ["git", "-C", str(directory)]
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

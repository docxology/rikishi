import json
import re
import shutil
import tomllib
from collections.abc import Callable, Mapping
from hashlib import sha256
from pathlib import Path
from typing import Literal, assert_never

import pytest
import yaml

from rikishi import __version__
from rikishi.alignment import run_alignment
from rikishi.bridge_study import catalog
from rikishi.competency import AlignmentError, load_study
from rikishi.dashboard import create_app
from rikishi.ontology import OntologyIndex


def test_release_metadata_agrees_with_runtime_version(project_root: Path) -> None:
    # Given the actual package, lockfile, citation and archive metadata.
    project = tomllib.loads((project_root / "pyproject.toml").read_text())["project"]
    locked = tomllib.loads((project_root / "uv.lock").read_text())
    locked_project = next(package for package in locked["package"] if package["name"] == "rikishi")
    citation = yaml.safe_load((project_root / "CITATION.cff").read_text())
    archive = json.loads((project_root / ".zenodo.json").read_text())

    # When their machine-consumed release identities are compared.
    versions = {project["version"], locked_project["version"], citation["version"], archive["version"]}

    # Then every release surface identifies the same runtime.
    assert versions == {__version__}
    assert re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", __version__)
    assert citation["repository-code"] == "https://github.com/docxology/rikishi"
    assert citation["license"].lower() == archive["license"].lower() == project["license"].lower()
    assert citation["title"] == archive["title"]


def test_dashboard_openapi_reports_runtime_version(
    tmp_path: Path,
    corpus_factory: Callable[[Path, Mapping[str, str]], OntologyIndex],
) -> None:
    # Given a real source-backed index and the actual read-only application.
    index = corpus_factory(tmp_path, {"source.kif": "(instance Example Entity)"})
    app = create_app(index.path)

    # When a client reads the application's OpenAPI metadata.
    metadata = app.openapi()

    # Then the public API identifies the same runtime as the package.
    assert metadata["info"]["version"] == __version__


@pytest.mark.parametrize("authority", ("alignment", "bridge"))
def test_packaged_studies_bind_release_inputs(
    project_root: Path, authority: Literal["alignment", "bridge"],
) -> None:
    # Given the packaged study authority consumed by a real campaign.
    bindings: dict[str, str]
    match authority:
        case "alignment":
            bindings = load_study().bindings
        case "bridge":
            study = catalog()
            bindings = {"uv.lock": study.dependency_lock_sha256,
                        "config/sumo.lock.json": study.lock_sha256}
        case unreachable:
            assert_never(unreachable)

    # When its declared inputs are read from the actual release checkout.
    actual = {name: sha256((project_root / name).read_bytes()).hexdigest() for name in bindings}

    # Then both study families bind the exact files this release will execute.
    assert actual == bindings


def test_changed_dependency_lock_rejected_before_campaign_output(
    project_root: Path, tmp_path: Path,
) -> None:
    # Given real release bindings with a changed lock in an isolated temporary root.
    for name in load_study().bindings:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(project_root / name, target)
    lock = tmp_path / "uv.lock"
    lock.write_bytes(lock.read_bytes() + b"\n")
    output = tmp_path / "uncreated"

    # When the actual runner admits the changed dependency input.
    with pytest.raises(AlignmentError, match="^Lock/dependency inputs differ from the study authority$"):
        run_alignment(tmp_path, output)

    # Then it rejects before source/index/native access or campaign output creation.
    assert not output.exists()

import json
import shutil

import pytest

from rikishi.manuscript import render_manuscript
from rikishi.manuscript_provenance import ProvenanceError
from rikishi.manuscript_verification import verify_manuscript


@pytest.mark.integration
def test_native_template_render_and_verify(project_root):
    render_manuscript(project_root)
    verify_manuscript(project_root)


@pytest.mark.integration
@pytest.mark.parametrize(
    "relative", ["manuscript/references.bib", "output/analytics.json", "manuscript/rikishi.md"]
)
def test_verifier_rejects_stale_authored_inputs(project_root, tmp_path, relative):
    receipt = json.loads((project_root / "output/manuscript/render-receipt.json").read_text())
    snapshot = receipt["renderer_snapshot"]
    shutil.copytree(project_root / "output/manuscript", tmp_path / "output/manuscript")
    shutil.copytree(project_root / "manuscript", tmp_path / "manuscript")
    shutil.copytree(project_root / snapshot, tmp_path / snapshot)
    origin = "renderer-origin.json"
    shutil.copy2((project_root / snapshot).parent / origin, (tmp_path / snapshot).parent / origin)
    shutil.copy2(project_root / "output/analytics.json", tmp_path / "output/analytics.json")
    target = tmp_path / relative
    target.write_bytes(target.read_bytes() + b"\nchanged-input\n")
    with pytest.raises(
        ProvenanceError, match="Changed manuscript input|Authored manuscript changed"
    ):
        verify_manuscript(tmp_path)

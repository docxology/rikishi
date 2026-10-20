from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from zipfile import ZipFile

from rikishi.fep import ProbabilityError, free_energy, inspect_formalization


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    evidence = root / ".omo" / "evidence" / "fep-manuscript"
    evidence.mkdir(parents=True, exist_ok=True)
    output = root / "output" / "manuscript"
    receipt = json.loads((output / "render-receipt.json").read_text())
    assert receipt["template_worktree_used"] is False
    snapshot = root / receipt["renderer_snapshot"]
    origin = json.loads((snapshot.parent / "renderer-origin.json").read_text())
    assert origin["revision"] == receipt["template_revision"]
    assert origin["archive_sha256"] == receipt["renderer_archive_sha256"]
    assert receipt["renderer_imported_sources"]
    for relative, digest in receipt["renderer_imported_sources"].items():
        assert origin["sources"][relative] == digest
        assert hashlib.sha256((snapshot / relative).read_bytes()).hexdigest() == digest
    for item in receipt["artifacts"]:
        artifact = root / item["path"]
        assert artifact.stat().st_size == item["bytes"] > 0
        assert hashlib.sha256(artifact.read_bytes()).hexdigest() == item["sha256"]
    with ZipFile(output / "docx" / "rikishi.docx") as archive:
        assert archive.testzip() is None
        document = archive.read("word/document.xml").decode()
        assert "Rikishi" in document and "Connections to formalization" in document
        figure_bytes = (output / "figures" / "fep-free-energy.png").read_bytes()
        media = [name for name in archive.namelist() if name.startswith("word/media/")]
        assert any(archive.read(name) == figure_bytes for name in media)
        corpus_figure = (output / "figures" / "corpus-files.png").read_bytes()
        assert any(archive.read(name) == corpus_figure for name in media)
    html = (output / "web" / "manuscript__rikishi.html").read_text()
    assert "Rikishi" in html and "figures/fep-free-energy.png" in html
    assert (output / "web" / "figures" / "fep-free-energy.png").is_file()
    assert (output / "web" / "figures" / "corpus-files.png").is_file()
    corpus_source = root / "output" / "data" / "corpus.json"
    assert hashlib.sha256(corpus_source.read_bytes()).hexdigest() == receipt["corpus_export_sha256"]
    corpus = json.loads(corpus_source.read_text())
    hydrated = (output / "rikishi.md").read_text()
    assert "{{" not in hydrated
    assert str(corpus["formulas"]) in hydrated
    assert corpus["source_commit"] in hydrated
    info = subprocess.run(
        ["pdfinfo", str(output / "pdf" / "rikishi.pdf")], capture_output=True, text=True, check=True
    ).stdout
    text = subprocess.run(
        ["pdftotext", str(output / "pdf" / "rikishi.pdf"), "-"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert "Rikishi" in text and "Connections to formalization" in text
    try:
        free_energy([0.4, 0.4], [0.8, 0.2], [0.5, 0.5])
    except ProbabilityError as error:
        negative_control = str(error)
    else:
        raise AssertionError("unnormalized prior was accepted")
    formal = root.parents[2] / "ActiveInferenceInstitute" / "Public" / "fep_formal"
    inspection = inspect_formalization(formal)
    (evidence / "formalization-inspection.json").write_text(json.dumps(inspection, indent=2) + "\n")
    (evidence / "pdfinfo.txt").write_text(info)
    (evidence / "pdf-text.txt").write_text(text)
    result = {
        "renderer_imported_modules_verified": len(receipt["renderer_imported_sources"]),
        "active_template_worktree_used": receipt["template_worktree_used"],
        "artifact_hashes_verified": len(receipt["artifacts"]),
        "docx_archive_and_image": "pass",
        "html_local_figure": "pass",
        "pdf_text": "pass",
        "negative_control": negative_control,
        "source_inspection_commit": inspection["commit"],
        "lean_compiled": False,
    }
    (evidence / "verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

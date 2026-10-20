from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from zipfile import ZipFile

from rikishi.fep import ProbabilityError, free_energy, inspect_formalization
from rikishi.manuscript_provenance import (
    ArtifactRecord,
    contained_path,
    require_evidence,
    verify_artifacts,
    verify_sources,
)


def verify_manuscript(root: Path) -> None:
    evidence = root / ".omo" / "evidence" / "fep-manuscript"
    evidence.mkdir(parents=True, exist_ok=True)
    output = root / "output" / "manuscript"
    receipt = json.loads((output / "render-receipt.json").read_text())
    require_evidence(
        bool(receipt["template_worktree_used"] is False),
        'Failed manuscript check: receipt["template_worktree_used"] is False',
    )
    snapshot = contained_path(root, receipt["renderer_snapshot"])
    origin = json.loads((snapshot.parent / "renderer-origin.json").read_text())
    require_evidence(
        bool(origin["revision"] == receipt["template_revision"]),
        'Failed manuscript check: origin["revision"] == receipt["template_revision"]',
    )
    require_evidence(
        bool(origin["archive_sha256"] == receipt["renderer_archive_sha256"]),
        'Failed manuscript check: origin["archive_sha256"] == receipt["renderer_archive_sha256"]',
    )
    require_evidence(
        bool(receipt["renderer_imported_sources"]),
        'Failed manuscript check: receipt["renderer_imported_sources"]',
    )
    for relative, digest in receipt["renderer_imported_sources"].items():
        require_evidence(
            bool(origin["sources"][relative] == digest),
            'Failed manuscript check: origin["sources"][relative] == digest',
        )
        require_evidence(
            bool(hashlib.sha256((snapshot / relative).read_bytes()).hexdigest() == digest),
            "Failed manuscript check: hashlib.sha256((snapshot / relative).read_bytes()).hexdigest() == digest",
        )
    verify_sources(snapshot, receipt["renderer_imported_sources"])
    verify_artifacts(root, [ArtifactRecord.model_validate(item) for item in receipt["artifacts"]])
    for filename, key in (
        (root / "manuscript" / "references.bib", "bibliography_sha256"),
        (root / "output" / "analytics.json", "analytics_sha256"),
    ):
        require_evidence(
            hashlib.sha256(filename.read_bytes()).hexdigest() == receipt[key],
            f"Changed manuscript input: {filename.name}",
        )
    require_evidence(
        hashlib.sha256((root / "manuscript" / "rikishi.md").read_bytes()).hexdigest()
        == receipt["source_sha256"],
        "Authored manuscript changed since rendering",
    )
    with ZipFile(output / "docx" / "rikishi.docx") as archive:
        require_evidence(
            bool(archive.testzip() is None), "Failed manuscript check: archive.testzip() is None"
        )
        document = archive.read("word/document.xml").decode()
        require_evidence(
            bool("Rikishi" in document and "Connections to formalization" in document),
            'Failed manuscript check: "Rikishi" in document and "Connections to formalization" in document',
        )
        figure_bytes = (output / "figures" / "fep-free-energy.png").read_bytes()
        media = [name for name in archive.namelist() if name.startswith("word/media/")]
        require_evidence(
            bool(any(archive.read(name) == figure_bytes for name in media)),
            "Failed manuscript check: any(archive.read(name) == figure_bytes for name in media)",
        )
        corpus_figure = (output / "figures" / "corpus-files.png").read_bytes()
        composition = (output / "figures" / "corpus-composition.png").read_bytes()
        require_evidence(
            any(archive.read(name) == composition for name in media),
            "DOCX composition figure missing",
        )
        require_evidence(
            bool(any(archive.read(name) == corpus_figure for name in media)),
            "Failed manuscript check: any(archive.read(name) == corpus_figure for name in media)",
        )
    html = (output / "web" / "manuscript__rikishi.html").read_text()
    require_evidence(
        bool("Rikishi" in html and "figures/fep-free-energy.png" in html),
        'Failed manuscript check: "Rikishi" in html and "figures/fep-free-energy.png" in html',
    )
    require_evidence(
        bool((output / "web" / "figures" / "fep-free-energy.png").is_file()),
        'Failed manuscript check: (output / "web" / "figures" / "fep-free-energy.png").is_file()',
    )
    require_evidence(
        bool((output / "web" / "figures" / "corpus-files.png").is_file()),
        'Failed manuscript check: (output / "web" / "figures" / "corpus-files.png").is_file()',
    )
    corpus_source = root / "output" / "data" / "corpus.json"
    require_evidence(
        (output / "web" / "figures" / "corpus-composition.png").read_bytes()
        == (output / "figures" / "corpus-composition.png").read_bytes(),
        "HTML composition figure differs",
    )
    require_evidence(
        bool(
            hashlib.sha256(corpus_source.read_bytes()).hexdigest()
            == receipt["corpus_export_sha256"]
        ),
        'Failed manuscript check: hashlib.sha256(corpus_source.read_bytes()).hexdigest() == receipt["corpus_export_sha256"]',
    )
    corpus = json.loads(corpus_source.read_text())
    hydrated = (output / "rikishi.md").read_text()
    require_evidence(bool("{{" not in hydrated), 'Failed manuscript check: "{{" not in hydrated')
    require_evidence(
        bool(str(corpus["formulas"]) in hydrated),
        'Failed manuscript check: str(corpus["formulas"]) in hydrated',
    )
    require_evidence(
        bool(corpus["source_commit"] in hydrated),
        'Failed manuscript check: corpus["source_commit"] in hydrated',
    )
    info = subprocess.run(
        ["pdfinfo", str(output / "pdf" / "rikishi.pdf")], capture_output=True, text=True, check=True
    ).stdout
    text = subprocess.run(
        ["pdftotext", str(output / "pdf" / "rikishi.pdf"), "-"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    require_evidence(
        bool("Rikishi" in text and "Connections to formalization" in text),
        'Failed manuscript check: "Rikishi" in text and "Connections to formalization" in text',
    )
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

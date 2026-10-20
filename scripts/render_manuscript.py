from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

import matplotlib

from rikishi.fep import demo

RENDERER_REVISION = "efce6d6f5b3c4e8e2bbf92d8250855a0a9389ae8"


def prepare_renderer(root: Path, checkout: Path) -> tuple[Path, dict[str, str], str]:
    archive_bytes = subprocess.run(
        [
            "git",
            "-C",
            str(checkout),
            "archive",
            RENDERER_REVISION,
            "infrastructure",
            "pyproject.toml",
        ],
        check=True,
        capture_output=True,
    ).stdout
    archive_hash = hashlib.sha256(archive_bytes).hexdigest()
    snapshot = root / ".rikishi" / "template-renderer" / RENDERER_REVISION
    with tarfile.open(fileobj=io.BytesIO(archive_bytes)) as archive:
        sources = {}
        for member in archive.getmembers():
            if member.isfile():
                stream = archive.extractfile(member)
                if stream is None:
                    raise ValueError(f"Cannot read archived source {member.name}")
                with stream:
                    sources[member.name] = hashlib.sha256(stream.read()).hexdigest()
            elif not member.isdir():
                raise ValueError(f"Unsupported archive entry {member.name}")
        if not snapshot.exists():
            snapshot.mkdir(parents=True)
            archive.extractall(snapshot, filter="data")
    for relative, digest in sources.items():
        if hashlib.sha256((snapshot / relative).read_bytes()).hexdigest() != digest:
            raise ValueError(f"Renderer snapshot differs from pinned archive: {relative}")
    origin = {"revision": RENDERER_REVISION, "archive_sha256": archive_hash, "sources": sources}
    (snapshot.parent / "renderer-origin.json").write_text(json.dumps(origin, indent=2) + "\n")
    return snapshot, sources, archive_hash


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    checkout = Path(
        os.environ.get("RIKISHI_TEMPLATE_ROOT", root.parent.parent / "Public" / "template")
    ).resolve(strict=True)
    checkout_status = subprocess.run(
        ["git", "-C", str(checkout), "status", "--porcelain"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    template, renderer_sources, archive_hash = prepare_renderer(root, checkout)
    sys.path.insert(0, str(template))
    from infrastructure.rendering.config import RenderingConfig
    from infrastructure.rendering.docx_renderer import render_docx
    from infrastructure.rendering.pdf_renderer import PDFRenderer
    from infrastructure.rendering.web_renderer import WebRenderer

    output = root / "output" / "manuscript"
    figures = output / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    example = demo()
    (output / "fep-example.json").write_text(json.dumps(example, indent=2, allow_nan=False) + "\n")
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7.2, 4.2), layout="constrained")
    ax.plot(
        [p["q_state_zero"] for p in example["scan"]],
        [p["free_energy"] for p in example["scan"]],
        color="#255b89",
        linewidth=2.4,
        label="Free energy F(q)",
    )
    ax.axhline(
        example["result"]["surprise"], color="#8c4b21", linestyle="--", label="Surprise: -log p(o)"
    )
    ax.scatter([0.8], [example["optimum"]["free_energy"]], color="#255b89", zorder=3)
    ax.set(
        xlabel="Candidate probability q(state = 0)",
        ylabel="Natural-log units (nats)",
        title="Finite variational inference: exact posterior at 0.8",
    )
    ax.legend(frameon=False)
    ax.grid(alpha=0.2)
    figure = figures / "fep-free-energy.png"
    fig.savefig(figure, dpi=180)
    plt.close(fig)
    source = root / "manuscript" / "rikishi.md"
    staged = output / source.name
    corpus_source = root / "output" / "data" / "corpus.json"
    corpus = json.loads(corpus_source.read_text())
    if corpus["parse_errors"] or not corpus["source_clean"]:
        raise ValueError("Manuscript requires a clean corpus export with no parse errors")
    substitutions = {
        "SUMO_COMMIT": corpus["source_commit"],
        "CORPUS_FILES": str(corpus["files"]),
        "CORPUS_FORMULAS": str(corpus["formulas"]),
        "CORPUS_TERMS": str(corpus["terms"]),
        "CORPUS_EDGES": str(corpus["edges"]),
        "CORPUS_PARSE_ERRORS": str(len(corpus["parse_errors"])),
    }
    hydrated = source.read_text()
    for key, value in substitutions.items():
        hydrated = hydrated.replace("{{" + key + "}}", value)
    if re.search(r"\{\{[A-Z_]+\}\}", hydrated):
        raise ValueError("Unresolved manuscript substitution")
    staged.write_text(hydrated)
    corpus_figure = figures / "corpus-files.png"
    shutil.copy2(root / "output" / "corpus-files.png", corpus_figure)
    configuration = RenderingConfig(
        manuscript_dir=str(output),
        output_dir=str(output),
        pdf_dir=str(output / "pdf"),
        web_dir=str(output / "web"),
        docx_dir=str(output / "docx"),
        figures_dir=str(figures),
        latex_compiler="xelatex",
    )
    previous = Path.cwd()
    os.chdir(output)
    try:
        pdf = PDFRenderer(configuration).render_markdown(staged)
        html = WebRenderer(configuration).render(staged)
        docx = render_docx(
            staged,
            output / "docx" / "rikishi.docx",
            title="Rikishi: a reproducible SUMO ontology operator",
            author="Daniel Ari Friedman",
            extra_args=[f"--resource-path={output}"],
        ).output_path
    finally:
        os.chdir(previous)
    shutil.copytree(figures, html.parent / "figures", dirs_exist_ok=True)
    imported_sources = {}
    for name, module in tuple(sys.modules.items()):
        if name == "infrastructure" or name.startswith("infrastructure."):
            filename = getattr(module, "__file__", None)
            if filename is None:
                continue
            relative = Path(filename).resolve().relative_to(template).as_posix()
            digest = hashlib.sha256(Path(filename).read_bytes()).hexdigest()
            if renderer_sources.get(relative) != digest:
                raise ValueError(
                    f"Imported renderer source does not match pinned archive: {relative}"
                )
            imported_sources[relative] = digest
    artifacts = [pdf, html, docx, figure, corpus_figure, staged, output / "fep-example.json"]
    receipt = {
        "renderer": "docxology/template native PDFRenderer, WebRenderer, render_docx",
        "template_revision": RENDERER_REVISION,
        "template_worktree_clean": not bool(checkout_status),
        "template_worktree_used": False,
        "renderer_snapshot": str(template.relative_to(root)),
        "renderer_archive_sha256": archive_hash,
        "renderer_imported_sources": dict(sorted(imported_sources.items())),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "corpus_export_sha256": hashlib.sha256(corpus_source.read_bytes()).hexdigest(),
        "substitutions": substitutions,
        "numerical_result": example["result"],
        "artifacts": [
            {
                "path": str(p.relative_to(root)),
                "bytes": p.stat().st_size,
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            }
            for p in artifacts
        ],
    }
    (output / "render-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()

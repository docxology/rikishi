from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml
from pydantic import TypeAdapter

from rikishi.manuscript_figures import render_manuscript_figures
from rikishi.manuscript_provenance import (
    RENDERER_REVISION,
    CorpusMeasurement,
    hydrate_manuscript,
    prepare_renderer,
    require_evidence,
)
from rikishi.ontology import OntologyIndex
from rikishi.ontology_figures import render_ontology_structure
from rikishi.ontology_observations import measure_source_structure, structure_substitutions
from rikishi.publication import load_publication_context, publication_headers
from rikishi.publication_bridge import load_bridge_context
from rikishi.publication_checks import validate_publication_source
from rikishi.publication_inference import load_inference_context
from rikishi.publication_office import verify_office_page_policy, write_office_reference
from rikishi.publication_office_content import project_office_content, verify_office_content_math
from rikishi.publication_research import load_research_context
from rikishi.research_figures import render_research_figures
from rikishi.sumo_demonstrations import demonstrate_sumo, report_to_substitutions
from rikishi.sumo_figures import render_sumo_system


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def _require_clean_tex_log(path: Path) -> None:
    require_evidence(path.is_file(), f"Native PDF compilation log missing: {path}")
    errors = [line.decode("utf-8", errors="backslashreplace")
              for line in path.read_bytes().splitlines() if line.startswith(b"!")]
    require_evidence(not errors, "Native PDF compilation contains TeX errors: " + "; ".join(errors))


def _imported_sources(template: Path, sources: dict[str, str]) -> dict[str, str]:
    imported = {}
    for name, module in tuple(sys.modules.items()):
        if name == "infrastructure" or name.startswith("infrastructure."):
            filename = getattr(module, "__file__", None)
            if filename is None:
                continue
            path = Path(filename).resolve()
            relative = path.relative_to(template).as_posix()
            digest = _sha(path)
            require_evidence(sources.get(relative) == digest,
                             f"Imported renderer differs from pinned archive: {relative}")
            imported[relative] = digest
    return dict(sorted(imported.items()))


def render_manuscript(root: Path) -> None:
    root = root.resolve(strict=True)
    moment = datetime.now(UTC)
    checkout = Path(os.environ.get(
        "RIKISHI_TEMPLATE_ROOT", root.parent.parent / "Public" / "template"
    )).resolve(strict=True)
    checkout_status = subprocess.run(
        ["git", "-C", str(checkout), "status", "--porcelain"],
        check=True, capture_output=True, text=True,
    ).stdout
    template, renderer_sources, archive_hash = prepare_renderer(root, checkout)
    sys.path.insert(0, str(template))
    from infrastructure.rendering._pandoc_args import combined_pandoc_args
    from infrastructure.rendering.config import RenderingConfig
    from infrastructure.rendering.docx_renderer import render_docx
    from infrastructure.rendering.pdf_renderer import PDFRenderer
    from infrastructure.rendering.web_renderer import WebRenderer

    output = root / "output" / "manuscript"
    figures = output / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    corpus_path = root / "output" / "data" / "corpus.json"
    corpus = CorpusMeasurement.model_validate_json(corpus_path.read_bytes())
    context = load_publication_context(root, corpus, rendered_at=moment)
    policy = context.settings.publication
    research_output = output / "research"
    for family in ("e", "v", "fresh-cache"):
        shutil.copytree(root / "output/research" / family, research_output / family,
                        dirs_exist_ok=True)
    research = load_research_context(research_output, decimal_places=policy.decimal_places)
    inference_output = output / "inference"
    shutil.copytree(root / "output/inference", inference_output, dirs_exist_ok=True)
    inference = load_inference_context(inference_output)
    bridge_output = output / "bridge"
    shutil.copytree(root / "output/bridge", bridge_output, dirs_exist_ok=True)
    bridge = load_bridge_context(bridge_output, decimal_places=policy.decimal_places)
    example = context.example
    _json(output / "fep-example.json", example)
    index = OntologyIndex(root / ".rikishi" / "ontology.sqlite")
    require_evidence(CorpusMeasurement.model_validate(index.stats()) == corpus,
                     "Corpus export differs from the graphical abstract's index")
    sumo_report = demonstrate_sumo(index, root)
    require_evidence(sumo_report.source.commit == corpus.source_commit
                     and sumo_report.source.clean is corpus.source_clean,
                     "SUMO demonstration revision differs from corpus")
    sumo_path = output / "sumo-demonstrations.json"
    _json(sumo_path, sumo_report.model_dump(mode="json"))
    sumo_values = TypeAdapter(dict[str, str]).validate_python(
        report_to_substitutions(sumo_report), strict=True
    )
    structure = measure_source_structure(sumo_report.source)
    structure_path = output / "ontology-structure.json"
    _json(structure_path, structure.model_dump(mode="json"))
    values = {**context.values, **sumo_values, **research.values, **inference.values, **bridge.values,
              **structure_substitutions(structure)}
    taxonomy = index.neighborhood(
        "Entity", limit=min(max(corpus.edges, 1), 500), relation="subclass"
    )
    generated = render_manuscript_figures(
        figures, example, corpus, taxonomy,
        dpi=policy.figure_dpi, decimal_places=policy.decimal_places,
    )
    generated.extend(render_sumo_system(figures, sumo_report, dpi=policy.figure_dpi))
    generated.extend(render_ontology_structure(
        figures, sumo_report.source, structure, dpi=policy.figure_dpi,
    ))
    with TemporaryDirectory(prefix="research-figures-", dir=root / ".rikishi/results") as temporary:
        research_figures = render_research_figures(
            Path(temporary), research_output / "e/alignment-report.json",
            comparison_path=research_output / "v/alignment-report.json",
            dpi=policy.figure_dpi, decimal_places=policy.decimal_places,
        )
        for path in research_figures:
            target = figures / path.name
            shutil.copy2(path, target)
            generated.append(target)
    for name in ("corpus-files.png", "corpus-composition.png"):
        shutil.copy2(root / "output" / name, figures / name)
    from rikishi.bridge_figures import BridgeFigureInputs, render_bridge_figures
    from rikishi.witness_abstracts import render_witness_abstracts

    with TemporaryDirectory(prefix="bridge-figures-", dir=root / ".rikishi/results") as temporary:
        bridge_figures = render_bridge_figures(
            bridge_output / "bridge-report.json", Path(temporary) / "figures",
            trusted_report_sha256=bridge.input_sha256["bridge-report.json"],
            dpi=policy.figure_dpi, decimal_places=policy.decimal_places,
        )
        for path in bridge_figures:
            target = figures / path.name
            shutil.copy2(path, target)
            generated.append(target)
    abstract_inputs = BridgeFigureInputs.model_validate_json(
        (figures / "bridge-figure-inputs.json").read_bytes())
    with TemporaryDirectory(prefix="witness-abstracts-", dir=root / ".rikishi/results") as temporary:
        for path in render_witness_abstracts(abstract_inputs, Path(temporary)):
            target = figures / path.name
            shutil.copy2(path, target)
            generated.append(target)
    from rikishi.witness_research import build_witness_research
    from rikishi.witness_research_figures import render_witness_research

    derived = build_witness_research(bridge.report, bridge.input_sha256["bridge-report.json"])
    with TemporaryDirectory(prefix="witness-research-", dir=root / ".rikishi/results") as temporary:
        for path in render_witness_research(derived, Path(temporary)):
            target = figures / path.name
            shutil.copy2(path, target)
            generated.append(target)
    from rikishi.witness_dynamics import build_witness_dynamics
    from rikishi.witness_dynamics_figures import render_witness_dynamics

    dynamics = build_witness_dynamics(bridge.report, bridge.input_sha256["bridge-report.json"])
    with TemporaryDirectory(prefix="witness-dynamics-", dir=root / ".rikishi/results") as temporary:
        for path in render_witness_dynamics(dynamics, Path(temporary)):
            target = figures / path.name
            shutil.copy2(path, target)
            generated.append(target)
    from rikishi.witness_sequence_atlas import build_sequence_atlas, render_sequence_atlas

    atlas = build_sequence_atlas(bridge.report.witnesses, bridge.input_sha256["bridge-report.json"])
    with TemporaryDirectory(prefix="witness-sequences-", dir=root / ".rikishi/results") as temporary:
        for path in render_sequence_atlas(atlas, Path(temporary)):
            target = figures / path.name
            shutil.copy2(path, target)
            generated.append(target)
    event_source = figures / "EventTransport.lean"
    shutil.copy2(root / "examples/EventTransport.lean", event_source)
    generated.append(event_source)
    pdf_figures = root / "output" / "figures"
    shutil.copytree(figures, pdf_figures, dirs_exist_ok=True)
    cover = output / context.settings.paper.cover.image
    require_evidence(cover.is_file() and cover in generated,
                     "Configured cover must be a generated manuscript figure")

    source = root / "manuscript" / "rikishi.md"
    source_bib = root / "manuscript" / "references.bib"
    hydrated = hydrate_manuscript(source.read_text(), corpus, values=values)
    bibliography = output / "references.bib"
    bibliography.write_text(source_bib.read_text().replace(
        "{{FORMAL_COMMIT}}", context.values["FORMAL_COMMIT"]
    ))
    style = output / "references.csl"
    shutil.copy2(root / policy.citation_style, style)
    checks = validate_publication_source(source, bibliography)
    tool_versions = {
        command: subprocess.run([command, "--version"], check=True, capture_output=True,
                                text=True, timeout=30).stdout.splitlines()[0]
        for command in ("pandoc", "pandoc-crossref")
    }
    metadata = {**context.metadata, "csl": str(style)}
    def header_for(edition: str) -> str:
        styled = {**metadata, "header-includes": publication_headers(
            policy, edition=edition, graphical_abstracts=context.settings.paper.graphical_abstracts)}
        return "---\n" + yaml.safe_dump(styled, sort_keys=False, allow_unicode=True) + "---\n\n"
    body = output / "rikishi-body.md"
    staged = output / "rikishi.md"
    office = output / "rikishi-office-web.md"
    body.write_text(hydrated.text)
    staged.write_text(header_for("pdf") + hydrated.text)
    office.write_text(header_for("html") + context.frontmatter + hydrated.text)
    staged_config = output / "config.yaml"
    staged_config.write_text(yaml.safe_dump(context.template_config, sort_keys=False))
    with TemporaryDirectory(prefix="office-reference-", dir=root / ".rikishi/results") as temporary:
        native_reference = write_office_reference(
            Path(temporary) / "office-reference.docx", margin_mm=policy.margin_mm,
        )
        office_reference = output / native_reference.reference_doc.name
        office_default = output / native_reference.default_reference_doc.name
        shutil.copy2(native_reference.reference_doc, office_reference)
        shutil.copy2(native_reference.default_reference_doc, office_default)
        office_receipt = {
            **asdict(native_reference),
            "reference_doc": office_reference.relative_to(root).as_posix(),
            "default_reference_doc": office_default.relative_to(root).as_posix(),
            "pandoc_executable": str(native_reference.pandoc_executable),
        }
    configuration = RenderingConfig(
        manuscript_dir=str(output), output_dir=str(root / "output"),
        pdf_dir=str(root / "output" / "pdf"), web_dir=str(root / "output" / "web"),
        docx_dir=str(root / "output" / "docx"), figures_dir=str(pdf_figures),
        latex_compiler="xelatex",
    )
    previous = Path.cwd()
    os.chdir(output)
    try:
        pdf = PDFRenderer(configuration).render_combined([staged], output, project_name="rikishi")
        _require_clean_tex_log(pdf.parent / "_combined_manuscript.log")
        html = WebRenderer(configuration).render_combined([office], output, project_name="rikishi")
        native_docx = render_docx(
            office, output / "rikishi-native.docx",
            title=context.settings.paper.title, author=context.values["AUTHOR_NAMES"],
            reference_doc=office_reference,
            extra_args=["--number-sections", "--highlight-style=monochrome", *combined_pandoc_args(
                [output, figures, figures.parent], [bibliography], edition="DOCX"
            )],
        ).output_path
    finally:
        os.chdir(previous)
    content = project_office_content(native_docx.read_bytes())
    office_math = verify_office_content_math(content.docx)
    require_evidence(len(office_math.gathered_sha256) == hydrated.text.count(r"\begin{gathered}"),
                     "Word gathered display inventory differs from the canonical body")
    docx = root / "output/docx/rikishi.docx"
    docx.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="office-final-", dir=docx.parent) as temporary:
        projected = Path(temporary) / "rikishi.docx"
        projected.write_bytes(content.docx)
        projected.replace(docx)
    office_receipt["actual"] = asdict(verify_office_page_policy(docx, margin_mm=policy.margin_mm))
    shutil.copytree(figures, html.parent / "figures", dirs_exist_ok=True)
    figure_paths = [*generated, figures / "corpus-files.png", figures / "corpus-composition.png"]
    intermediates = [
        *pdf.parent.glob("*.tex"), *pdf.parent.glob("*.aux"), *pdf.parent.glob("*.bbl"),
        pdf.parent / "_combined_manuscript.log", pdf.parent / "_latex_stdout.log",
        html.parent / "_combined_manuscript.md",
        root / "output" / "reports" / "manuscript_composition.json",
    ]
    artifacts = list(dict.fromkeys([
        pdf, html, docx, native_docx, root / "examples/EventTransport.lean", *figure_paths,
        *(pdf_figures / p.name for p in figure_paths),
        *(html.parent / "figures" / p.name for p in figure_paths),
        body, staged, office, output / "fep-example.json", sumo_path, structure_path,
        bibliography, style, staged_config, office_reference, office_default,
        *(path for path in research_output.rglob("*") if path.is_file()),
        *(path for path in inference_output.rglob("*") if path.is_file()),
        *(path for path in bridge_output.rglob("*") if path.is_file()),
        *(path for path in intermediates if path.is_file()),
    ]))
    receipt = {
        "renderer": "docxology/template native combined PDFRenderer, WebRenderer, render_docx",
        "template_revision": RENDERER_REVISION,
        "template_worktree_clean": not bool(checkout_status), "template_worktree_used": False,
        "renderer_snapshot": str(template.relative_to(root)),
        "renderer_archive_sha256": archive_hash,
        "renderer_imported_sources": _imported_sources(template, renderer_sources),
        "rendered_at": moment.isoformat(), "tool_versions": tool_versions,
        "publication_inputs": context.input_sha256,
        "research_inputs": research.input_sha256,
        "inference_inputs": inference.input_sha256,
        "bridge_inputs": bridge.input_sha256,
        "office_reference": office_receipt,
        "office_content": asdict(content.receipt), "office_math": asdict(office_math),
        "report_inputs": {f"output/{name}": _sha(root / "output" / name)
                          for name in ("corpus-files.png", "corpus-composition.png")},
        "source_sha256": _sha(source), "bibliography_sha256": _sha(source_bib),
        "corpus_export_sha256": _sha(corpus_path),
        "analytics_sha256": _sha(root / "output" / "analytics.json"),
        "sumo_demonstrations_sha256": _sha(sumo_path),
        "ontology_structure_sha256": _sha(structure_path),
        "substitutions": hydrated.substitutions, "source_checks": checks,
        "numerical_result": example["result"],
        "editions": {key: path.relative_to(root).as_posix()
                     for key, path in (("pdf", pdf), ("html", html), ("docx", docx))},
        "artifacts": [{"path": p.relative_to(root).as_posix(), "bytes": p.stat().st_size,
                       "sha256": _sha(p)} for p in artifacts],
    }
    _json(output / "render-receipt.json", receipt)
    print(json.dumps(receipt, indent=2))

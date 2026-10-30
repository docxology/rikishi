from __future__ import annotations

import hashlib
import json
import re
import subprocess
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal, localcontext
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from typing import Final
from urllib.parse import unquote, urlsplit
from xml.etree.ElementTree import Element
from zipfile import ZipFile

import yaml
from defusedxml import ElementTree
from PIL import Image
from pydantic import BaseModel, ConfigDict, JsonValue, TypeAdapter

from rikishi.cache_replay import replay_cache
from rikishi.fep import ProbabilityError, free_energy, inspect_formalization
from rikishi.manuscript_provenance import (
    RENDERER_REVISION,
    ArtifactRecord,
    CorpusMeasurement,
    contained_path,
    hydrate_manuscript,
    require_evidence,
    verify_artifacts,
    verify_sources,
)
from rikishi.ontology_figures import HEIGHT_MM, WIDTH_MM
from rikishi.ontology_observations import (
    StructureReport,
    measure_source_structure,
    structure_substitutions,
)
from rikishi.publication import (
    PublicationContext,
    load_publication_context,
    publication_headers,
    verify_publication_inputs,
)
from rikishi.publication_abstracts import ABSTRACT_NAMES
from rikishi.publication_bridge import (
    BridgeContext,
    load_bridge_context,
    verify_bridge_content,
    verify_bridge_figures,
)
from rikishi.publication_checks import validate_publication_source
from rikishi.publication_inference import (
    InferenceContext,
    load_inference_context,
    verify_inference_content,
)
from rikishi.publication_office import (
    OfficePagePolicyReport,
    verify_office_page_policy,
    verify_office_reference_policy,
)
from rikishi.publication_office_content import (
    OfficeContentReceipt,
    OfficeMathReport,
    verify_office_content_math,
    verify_office_content_projection,
)
from rikishi.publication_research import ResearchContext, load_research_context
from rikishi.research_figures import FigureInputs
from rikishi.sumo_demonstrations import (
    FrozenSource,
    SumoReport,
    report_to_substitutions,
    validate_sumo_report,
)

_EDITIONS: Final = {
    "pdf": "output/pdf/rikishi_combined.pdf", "html": "output/web/index.html",
    "docx": "output/docx/rikishi.docx",
}
_FIGURES: Final = (
    "graphical-abstract.png", "corpus-files.png", "corpus-composition.png", "fep-free-energy.png",
    "sumo-system.png", "research-controls.png", "ontology-structure.png",
    "bridge-evidence.png", "bridge-free-energy.png", "bridge-native-controls.png",
    "witness-channels.png", "witness-evidence-scaling.png", "witness-sequential.png",
    "witness-sequences.png",
    *(f"{name}.png" for name in ABSTRACT_NAMES),
)
_NS: Final = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


class _SourceChecks(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")
    citation_ids: list[str]
    citation_count: int
    citation_occurrences: int
    bibliography_count: int
    equation_labels: list[str]
    equation_count: int
    figure_labels: list[str]
    figure_count: int
    section_labels: list[str]
    section_count: int
    formalism_labels: list[str]
    formalism_count: int


class _OfficeReference(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")
    reference_doc: str
    default_reference_doc: str
    reference_sha256: str
    default_reference_sha256: str
    pandoc_executable: str
    pandoc_sha256: str
    pandoc_version: str
    geometry: OfficePagePolicyReport
    actual: OfficePagePolicyReport


class _Receipt(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)
    template_revision: str
    template_worktree_used: bool
    renderer_snapshot: str
    renderer_archive_sha256: str
    renderer_imported_sources: dict[str, str]
    rendered_at: datetime
    publication_inputs: dict[str, str]
    research_inputs: dict[str, str]
    inference_inputs: dict[str, str]
    bridge_inputs: dict[str, str]
    office_reference: _OfficeReference
    office_content: OfficeContentReceipt
    office_math: OfficeMathReport
    report_inputs: dict[str, str]
    source_sha256: str
    bibliography_sha256: str
    corpus_export_sha256: str
    analytics_sha256: str
    sumo_demonstrations_sha256: str
    ontology_structure_sha256: str
    substitutions: dict[str, str]
    source_checks: _SourceChecks
    numerical_result: dict[str, JsonValue]
    editions: dict[str, str]
    artifacts: list[ArtifactRecord]


class _BibliographyEntry(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)
    id: str
    title: str


class _OntologyRendering(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")
    dpi: int
    width_mm: int
    height_mm: int


class _OntologyFigureData(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")
    report: StructureReport
    rendering: _OntologyRendering


@dataclass(slots=True)
class _Element:
    tag: str
    attrs: dict[str, str]
    chunks: list[str] = field(default_factory=list)
    children: list[_Element] = field(default_factory=list)

    @property
    def text(self) -> str:
        return " ".join("".join(self.chunks).split())


class _HTML(HTMLParser):
    def __init__(self, source: str) -> None:
        super().__init__()
        self.elements: list[_Element] = []
        self.stack: list[_Element] = []
        self.feed(source)
        self.close()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        element = _Element(tag, {k: v for k, v in attrs if v is not None})
        self.elements.append(element)
        if self.stack:
            self.stack[-1].children.append(element)
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
                       "meta", "param", "source", "track", "wbr"}:
            self.stack.append(element)

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data: str) -> None:
        for element in self.stack:
            element.chunks.append(data)


def _read(path: Path) -> bytes:
    require_evidence(path.is_file() and not path.is_symlink(), f"Missing regular artifact: {path}")
    return path.read_bytes()


def _key(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKC", text).casefold() if c.isalnum())


def _clean(text: str, edition: str) -> None:
    require_evidence(not re.search(r"\{\{[A-Z][A-Z0-9_]*\}\}|\[\s*\?\s*\]|\?\?|@[\w:.-]+", text),
                     f"Unresolved citation or placeholder in {edition}")


def _command(arguments: list[str]) -> str:
    return subprocess.run(arguments, check=True, capture_output=True, text=True, timeout=60).stdout


def _ontology_report(path: Path, source: FrozenSource, digest: str) -> StructureReport:
    raw = _read(path)
    require_evidence(hashlib.sha256(raw).hexdigest() == digest, "Ontology structure report changed")
    report = StructureReport.model_validate_json(raw)
    require_evidence(report == measure_source_structure(source),
                     "Ontology structure report differs from retained source")
    return report


def _ontology_figures(root: Path, context: PublicationContext, report: StructureReport) -> None:
    figures = root / "output/manuscript/figures"
    for name in ("ontology-structure.svg", "ontology-structure.json"):
        for directory in ("output/figures", "output/web/figures"):
            require_evidence(_read(root / directory / name) == _read(figures / name),
                             f"Ontology asset copy differs: {directory}/{name}")
    data = _OntologyFigureData.model_validate_json(_read(figures / "ontology-structure.json"))
    require_evidence(data.report == report, "Ontology figure report differs from retained source")
    dpi = context.settings.publication.figure_dpi
    require_evidence(data.rendering == _OntologyRendering(
        dpi=dpi, width_mm=WIDTH_MM, height_mm=HEIGHT_MM,
    ), "Ontology figure presentation differs from publication policy")
    description = report.model_dump_json()
    with Image.open(figures / "ontology-structure.png") as image:
        require_evidence(image.info.get("Description") == description,
                         "Ontology PNG report provenance differs")
        require_evidence(image.size == (int(WIDTH_MM / 25.4 * dpi), int(HEIGHT_MM / 25.4 * dpi)),
                         "Ontology PNG dimensions differ from publication policy")
    tree = ElementTree.fromstring(_read(figures / "ontology-structure.svg"))
    require_evidence(tree.findtext(".//{http://purl.org/dc/elements/1.1/}description") == description,
                     "Ontology SVG report provenance differs")
    namespace = "{http://www.w3.org/2000/svg}"
    visible = " ".join("".join(node.itertext()) for node in tree.iter(f"{namespace}text"))
    expected = [report.source_sha256, report.source_commit, report.ontology_path]
    for graph in report.graphs:
        expected.extend([graph.relation, *(f"{getattr(graph, key):,}" for key in (
            "unique_edges", "node_count", "root_count", "multiple_parent_count",
            "weak_component_count", "cyclic_component_count", "cyclic_node_count", "self_loop_count",
        ))])
    require_evidence(tree.tag == f"{namespace}svg" and tree.find(f".//{namespace}image") is None
                     and all(value in visible for value in expected),
                     "Ontology SVG vector source content differs")


def _ontology_table(rows: list[list[str]], table: str, edition: str) -> None:
    expected = [[cell.strip().replace("`", "") for cell in row.strip("|").split("|")]
                for row in table.splitlines()[2:]]
    require_evidence(bool(expected) and any(rows[i:i + len(expected)] == expected
                                          for i in range(len(rows))),
                     f"Ontology structure row missing: {edition}")


def _ontology_pdf_table(layout: str, table: str) -> None:
    rows = [[cell.group() for cell in re.finditer(r"\S+(?:[ \t]\S+)*", line)]
            for line in layout.splitlines() if line.strip()]
    _ontology_table(rows, table, "PDF")


def _projections(
    root: Path, receipt: _Receipt,
) -> tuple[PublicationContext, SumoReport, ResearchContext, BridgeContext]:
    output = root / "output/manuscript"
    for relative, digest in (
        ("manuscript/rikishi.md", receipt.source_sha256),
        ("manuscript/references.bib", receipt.bibliography_sha256),
        ("output/analytics.json", receipt.analytics_sha256),
        ("output/data/corpus.json", receipt.corpus_export_sha256),
    ):
        require_evidence(hashlib.sha256(_read(root / relative)).hexdigest() == digest,
                         f"Changed manuscript input: {relative}")
    verify_publication_inputs(root, receipt.publication_inputs)
    require_evidence(receipt.rendered_at.utcoffset() == timedelta(0), "Receipt moment must be UTC")
    corpus = CorpusMeasurement.model_validate_json(_read(root / "output/data/corpus.json"))
    context = load_publication_context(root, corpus, rendered_at=receipt.rendered_at)
    require_evidence(context.input_sha256 == receipt.publication_inputs,
                     "Publication authorities differ from regenerated context")
    research = load_research_context(
        output / "research", decimal_places=context.settings.publication.decimal_places,
    )
    require_evidence(research.input_sha256 == receipt.research_inputs,
                     "Research inputs differ from regenerated context")
    inference = load_inference_context(output / "inference")
    require_evidence(inference.input_sha256 == receipt.inference_inputs,
                     "Inference inputs differ from regenerated context")
    bridge = load_bridge_context(output / "bridge", decimal_places=context.settings.publication.decimal_places)
    require_evidence(bridge.input_sha256 == receipt.bridge_inputs,
                     "Bridge inputs differ from regenerated context")
    sumo_bytes = _read(output / "sumo-demonstrations.json")
    require_evidence(hashlib.sha256(sumo_bytes).hexdigest() == receipt.sumo_demonstrations_sha256,
                     "SUMO demonstration report changed")
    sumo = validate_sumo_report(json.loads(sumo_bytes))
    require_evidence(sumo.source.commit == corpus.source_commit
                     and sumo.source.clean is corpus.source_clean,
                     "SUMO demonstration revision differs from corpus")
    sumo_values = TypeAdapter(dict[str, str]).validate_python(
        report_to_substitutions(sumo), strict=True
    )
    structure = _ontology_report(output / "ontology-structure.json", sumo.source,
                                 receipt.ontology_structure_sha256)
    _ontology_figures(root, context, structure)
    hydrated = hydrate_manuscript((root / "manuscript/rikishi.md").read_text(), corpus,
                                  values={**context.values, **sumo_values, **research.values,
                                          **inference.values, **bridge.values,
                                          **structure_substitutions(structure)})
    require_evidence(hydrated.substitutions == receipt.substitutions, "Substitutions differ")
    bibliography = (root / "manuscript/references.bib").read_text().replace(
        "{{FORMAL_COMMIT}}", context.values["FORMAL_COMMIT"]
    )
    require_evidence((output / "references.bib").read_text() == bibliography,
                     "Staged bibliography differs from authored projection")
    require_evidence(validate_publication_source(root / "manuscript/rikishi.md",
                                                output / "references.bib") == receipt.source_checks.model_dump(),
                     "Source checks differ from actual Pandoc AST")
    metadata = {**context.metadata, "csl": str(output / "references.csl")}
    for name, body, edition in (("rikishi.md", hydrated.text, "pdf"),
                                ("rikishi-office-web.md", context.frontmatter + hydrated.text, "html")):
        expected_metadata = {**metadata, "header-includes": publication_headers(
            context.settings.publication, edition=edition,
            graphical_abstracts=context.settings.paper.graphical_abstracts,
        )}
        staged = (output / name).read_text()
        require_evidence(staged.startswith("---\n"), f"Projection metadata missing: {name}")
        _, header, actual = staged.split("---\n", 2)
        observed = yaml.safe_load(header)
        # Retained absolute CSL paths may point to the original complete fixture.
        old_style = Path(observed["csl"])
        require_evidence(old_style.is_absolute() and old_style.parts[-3:] == (
            "output", "manuscript", "references.csl"), "Invalid staged citation style path")
        observed["csl"] = metadata["csl"]
        require_evidence(observed == expected_metadata and actual == "\n" + body,
                         f"Projection differs from regenerated publication: {name}")
    require_evidence((output / "rikishi-body.md").read_text() == hydrated.text,
                     "Hydrated body differs from regenerated publication")
    require_evidence(yaml.safe_load((output / "config.yaml").read_text()) == context.template_config,
                     "Staged configuration differs from regenerated publication")
    require_evidence(_read(output / "references.csl") == _read(root / context.settings.publication.citation_style),
                     "Staged citation style differs")
    require_evidence(json.loads((output / "fep-example.json").read_text()) == context.example
                     and receipt.numerical_result == context.example["result"], "Numerical example differs")
    return context, sumo, research, bridge


def _html(root: Path, receipt: _Receipt) -> _HTML:
    document = _HTML((root / receipt.editions["html"]).read_text())
    recorded = {record.path for record in receipt.artifacts}
    images = [e for e in document.elements if e.tag == "img"]
    require_evidence(len(images) == len(_FIGURES), "HTML requires all canonical image references")
    names: list[str] = []
    for image in images:
        reference = image.attrs.get("src", "")
        parsed = urlsplit(reference)
        require_evidence(not parsed.scheme and not parsed.netloc and not parsed.query
                         and not parsed.fragment, f"Nonlocal HTML image: {reference}")
        relative = unquote(parsed.path)
        require_evidence(relative.startswith("figures/") and Path(relative).name in _FIGURES,
                         f"Unexpected HTML image reference: {reference}")
        target = contained_path(root, "output/web/" + relative)
        names.append(target.name)
        require_evidence(target.relative_to(root).as_posix() in recorded,
                         f"Unrecorded HTML figure: {target.name}")
        require_evidence(_read(target) == _read(root / "output/manuscript/figures" / target.name),
                         f"HTML figure differs: {target.name}")
    require_evidence(set(names) == set(_FIGURES), "HTML figure reference missing")
    identifiers = {e.attrs["id"]: e for e in document.elements if "id" in e.attrs}
    for element in document.elements:
        target = element.attrs.get("href", "")
        if target.startswith("#"):
            require_evidence(unquote(target[1:]) in identifiers, f"Unresolved HTML link: {target}")
    for name in ("research-dashboard.html", "bridge-explorer.html"):
        require_evidence(any(e.tag == "a" and e.attrs.get("href") == "../figures/" + name
                             for e in document.elements), f"Offline explorer link missing: {name}")
        relative = "output/figures/" + name
        require_evidence(relative in recorded and _read(root / relative)
                         == _read(root / "output/manuscript/figures" / name),
                         f"Offline explorer link target differs: {name}")
    for key in receipt.source_checks.citation_ids:
        require_evidence(f"ref-{key}" in identifiers, f"HTML bibliography entry missing: {key}")
        require_evidence(any(e.attrs.get("href") == f"#ref-{key}" for e in document.elements),
                         f"HTML citation link missing: {key}")
    for label in (receipt.source_checks.equation_labels + receipt.source_checks.figure_labels
                  + receipt.source_checks.formalism_labels + receipt.source_checks.section_labels):
        require_evidence(label in identifiers, f"HTML labeled target missing: {label}")
    _ontology_table([[cell.text for cell in row.children if cell.tag in {"td", "th"}]
                     for row in document.elements if row.tag == "tr"],
                    receipt.substitutions["ONTOLOGY_STRUCTURE_TABLE"], "HTML")
    _clean(" ".join(e.text for e in document.elements if e.tag == "body"), "HTML")
    return document


def _bound_office_styles(archive: ZipFile) -> Element:
    """Bind the actual styles part before comparing its approved policy atoms."""
    relationships = ElementTree.fromstring(archive.read("word/_rels/document.xml.rels"))
    namespace = "{http://schemas.openxmlformats.org/package/2006/relationships}"
    styles = [node for node in relationships if node.get("Type", "").endswith("/styles")]
    require_evidence(relationships.tag == namespace + "Relationships" and len(styles) == 1
                     and styles[0].tag == namespace + "Relationship"
                     and styles[0].get("Type") ==
                     "http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles"
                     and styles[0].get("Target") == "styles.xml"
                     and styles[0].get("TargetMode", "Internal") == "Internal",
                     "Actual Word styles relationship must target styles.xml internally")
    types = ElementTree.fromstring(archive.read("[Content_Types].xml"))
    ct = "{http://schemas.openxmlformats.org/package/2006/content-types}"
    overrides = [node for node in types if node.get("PartName") == "/word/styles.xml"]
    require_evidence(types.tag == ct + "Types" and len(overrides) == 1
                     and overrides[0].tag == ct + "Override"
                     and overrides[0].get("ContentType") ==
                     "application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml",
                     "Actual Word styles content type is missing or ambiguous")
    document = ElementTree.fromstring(archive.read("word/styles.xml"))
    require_evidence(document.tag == f"{{{_NS['w']}}}styles", "Actual Word styles document root differs")
    return document


def _office_policy(root: Path, receipt: _Receipt, *, margin_mm: float) -> OfficePagePolicyReport:
    """Check final geometry and the retained, minimally modified native reference."""
    office = receipt.office_reference
    require_evidence(office.reference_doc == "output/manuscript/office-reference.docx"
                     and office.default_reference_doc == "output/manuscript/office-reference.native-default.docx",
                     "Office reference paths differ from the publication contract")
    reference = contained_path(root, office.reference_doc)
    native = contained_path(root, office.default_reference_doc)
    require_evidence(hashlib.sha256(_read(reference)).hexdigest() == office.reference_sha256
                     and hashlib.sha256(_read(native)).hexdigest() == office.default_reference_sha256,
                     "Office reference or native default digest differs")
    geometry = verify_office_reference_policy(_read(native), _read(reference), margin_mm=margin_mm)
    actual = verify_office_page_policy(root / receipt.editions["docx"], margin_mm=margin_mm)
    require_evidence(geometry == office.geometry and actual == office.actual,
                     "Office geometry receipt differs from actual packages")
    with ZipFile(reference) as expected, ZipFile(root / receipt.editions["docx"]) as rendered:
        expected_styles = ElementTree.fromstring(expected.read("word/styles.xml"))
        rendered_styles = _bound_office_styles(rendered)
        for identifier in ("Hyperlink", "ImageCaption", "CaptionedFigure"):
            selector = f"w:style[@w:styleId='{identifier}']"
            before = expected_styles.findall(selector, _NS)
            after = rendered_styles.findall(selector, _NS)
            require_evidence(len(before) == len(after) == 1
                             and ElementTree.tostring(before[0]) == ElementTree.tostring(after[0]),
                             f"Actual Word reference style differs: {identifier}")
    return actual


def _docx(root: Path, receipt: _Receipt) -> str:
    with ZipFile(root / receipt.editions["docx"]) as archive:
        require_evidence(archive.testzip() is None, "DOCX archive CRC failed")
        document = ElementTree.fromstring(archive.read("word/document.xml"))
        _ontology_table([["".join(node.text or "" for node in cell.findall(".//w:t", _NS))
                          for cell in row.findall("w:tc", _NS)]
                         for row in document.findall(".//w:tr", _NS)],
                        receipt.substitutions["ONTOLOGY_STRUCTURE_TABLE"], "DOCX")
        relationships = ElementTree.fromstring(archive.read("word/_rels/document.xml.rels"))
        targets = {item.attrib["Id"]: item.attrib["Target"] for item in relationships
                   if item.attrib["Type"].endswith("/image")}
        used = [node.attrib[f"{{{_NS['r']}}}embed"] for node in document.findall(".//a:blip", _NS)]
        require_evidence(len(used) == len(_FIGURES), "DOCX requires all canonical image drawings")
        embedded: list[bytes] = []
        for identifier in used:
            require_evidence(identifier in targets, "DOCX image relationship missing")
            target = PurePosixPath("word") / targets[identifier]
            require_evidence(".." not in target.parts and not target.is_absolute(), "Unsafe DOCX image target")
            embedded.append(archive.read(str(target)))
        for name in _FIGURES:
            require_evidence(_read(root / "output/manuscript/figures" / name) in embedded,
                             f"DOCX canonical image missing: {name}")
        require_evidence(embedded[0] == _read(root / "output/manuscript/figures/graphical-abstract.png"),
                         "DOCX first drawing is not the canonical cover")
        require_evidence(embedded[1:4] == [
            _read(root / "output/manuscript/figures" / f"{name}.png") for name in ABSTRACT_NAMES
        ], "DOCX graphical abstract order differs from the canonical introduction")
        paragraphs = document.findall(".//w:p", _NS)
        words = ["".join(node.text or "" for node in paragraph.iter()
                         if node.tag in {f"{{{_NS['w']}}}t", f"{{{_NS['m']}}}t"})
                 for paragraph in paragraphs]
        abstract = next((i for i, word in enumerate(words) if word == "Abstract"), -1)
        cover = next((i for i, p in enumerate(paragraphs) if p.find(".//a:blip", _NS) is not None), -1)
        breaks = [i for i, p in enumerate(paragraphs) for node in p.findall(".//w:br", _NS)
                  if node.attrib.get(f"{{{_NS['w']}}}type") == "page"]
        require_evidence(0 <= cover < abstract and any(cover < i < abstract for i in breaks),
                         "DOCX cover page break missing")
        require_evidence(sum(cover < i < abstract for i in breaks) == 4,
                         "DOCX graphical introduction requires four explicit page breaks")
        math = document.findall(".//m:oMath", _NS)
        require_evidence(len(math) >= receipt.source_checks.equation_count, "DOCX math missing")
        math_text = " ".join("".join(n.text or "" for n in node.findall(".//m:t", _NS)) for node in math)
        require_evidence(all(token in math_text for token in ("F", "q", "p", "log", "Z")),
                         "DOCX equation content missing")
        text = "\n".join(words)
        _clean(text, "DOCX")
        return text


def _references(document: _HTML, label: str, marker: str) -> None:
    for element in document.elements:
        if element.attrs.get("href") == f"#{label}" and not element.attrs.get("id", "").startswith("toc-"):
            require_evidence(element.text == marker, f"HTML reference numbering differs: {label}")


def _pdf_margin(pdf: Path, margin_mm: float) -> None:
    bounds = ElementTree.fromstring(_command(["pdftotext", "-bbox", str(pdf), "-"]))
    expected = margin_mm * 72 / 25.4
    positions = [float(node.attrib["xMin"]) for node in bounds.iter()
                 if node.tag.endswith("}word") and node.text == "Abstract"]
    require_evidence(any(abs(position - expected) < 0.75 for position in positions),
                     "PDF abstract margin differs from publication policy")


def _pdf_images(pdf: Path, expected: dict[str, Path]) -> None:
    def pixels(path: Path) -> tuple[tuple[int, int], str]:
        with Image.open(path) as image:
            return image.size, hashlib.sha256(image.convert("RGB").tobytes()).hexdigest()

    with TemporaryDirectory(prefix="rikishi-pdf-images-") as temporary:
        # Lossless portable pixmap/bitmap intermediates avoid re-encoding every
        # high-resolution figure before comparing the same decoded RGB bytes.
        _command(["pdfimages", str(pdf), str(Path(temporary) / "image")])
        embedded = {pixels(path) for path in Path(temporary).glob("image-*")}
        for name, path in expected.items():
            require_evidence(pixels(path) in embedded, f"PDF canonical figure missing: {name}")


def _pdf_body_text(pdf: Path, margin_mm: float) -> str:
    bounds = ElementTree.fromstring(_command(["pdftotext", "-bbox", str(pdf), "-"]))
    margin = margin_mm * 72 / 25.4
    return " ".join(word.text or "" for page in bounds.iter() if page.tag.endswith("}page")
                    for word in page.iter() if word.tag.endswith("}word")
                    and float(word.attrib["yMax"]) <= float(page.attrib["height"]) - margin)


def _research_figures(root: Path, context: PublicationContext, research: ResearchContext) -> None:
    figures = root / "output/manuscript/figures"
    for name in ("research-controls.svg", "research-controls.json",
                 "research-dashboard.html"):
        for directory in ("output/figures", "output/web/figures"):
            require_evidence(_read(root / directory / name) == _read(figures / name),
                             f"Research asset copy differs: {directory}/{name}")
    data = FigureInputs.model_validate_json(_read(figures / "research-controls.json"))
    require_evidence([item.report for item in data.reports]
                     == [research.primary, research.comparison], "Research figure reports differ")
    for item in data.reports:
        relative = f"{item.report.prover}/alignment-report.json"
        require_evidence(item.sha256 == research.input_sha256[relative]
                         and Path(item.path).is_absolute()
                         and Path(item.path).parts[-5:] == (
                             "output", "manuscript", "research", item.report.prover,
                             "alignment-report.json"), "Research figure report binding differs")
    policy = context.settings.publication
    require_evidence(data.dpi == policy.figure_dpi and data.decimal_places == policy.decimal_places,
                     "Research figure presentation differs from publication policy")
    require_evidence(all(getattr(data, name) == FigureInputs.model_fields[name].default for name in (
        "schema_version", "width_mm", "ratio_threshold", "symlog_linear_threshold", "boundary",
    )), "Research figure scale or scope differs from canonical contract")
    study = research.primary.study
    provenance = [f"{item.report.prover.upper()} report: {item.path}\nSHA-256: {item.sha256}"
                  for item in data.reports]
    provenance.extend([
        f"Study: {study.study_id}; authority SHA-256: {research.primary.authority_sha256}",
        f"SUMO: {study.sumo_path}; lines: " + ", ".join(
            f"{citation.line}-{citation.end_line}" for citation in research.primary.source_claims.citations),
        f"SUMO revision: {study.sumo_commit}; SHA-256: {study.sumo_sha256}",
        f"SUMO URL: {study.sumo_url}",
        (f"Workbook: {study.workbook_path}; sheet: {study.workbook_sheet!r}; "
         f"rows: {study.workbook_rows}; columns: {study.workbook_columns}"),
        f"Workbook SHA-256: {study.workbook_sha256}",
        f"Workbook URL: {study.workbook_url}; accessed: {study.access_date}",
        f"Scope: {study.scope}",
        f"Replay boundary: {research.primary.replay_boundary}",
        "Complete inputs/captures bindings: research-controls.json; explorer: research-dashboard.html",
    ])
    require_evidence(data.provenance == provenance, "Research figure complete provenance differs")
    expected = [("ordinary", row) for row in research.primary.numerical.rows]
    expected.extend(("boundary", row) for row in research.primary.numerical.extremes)
    require_evidence(len(data.numerical_rows) == len(expected), "Research figure row inventory differs")
    for actual, (population, row) in zip(data.numerical_rows, expected, strict=True):
        with localcontext() as decimal_context:
            decimal_context.prec = research.primary.study.numerical.decimal_precision
            ratios = [float(Decimal.from_float(error) / Decimal(row.tolerance)) for error in (
                row.max_reference_error, row.permutation_max_error, row.rescaling_max_error,
            )]
        require_evidence((actual.id, actual.dimension, actual.candidate, actual.population,
                          actual.tolerance, actual.passed) == (
                              row.input.id, row.dimension, row.candidate, population,
                              row.tolerance, row.passed)
                         and list(actual.ratios.model_dump().values()) == ratios,
                         f"Research figure numerical row differs: {row.input.id}")
    ordinary = [row for row in data.numerical_rows if row.population == "ordinary"]
    groups = sorted({(row.dimension, row.candidate) for row in ordinary})
    require_evidence([(group.dimension, group.candidate) for group in data.aggregates] == groups,
                     "Research figure aggregate inventory differs")
    for aggregate in data.aggregates:
        selected = [row for row in ordinary
                    if (row.dimension, row.candidate) == (aggregate.dimension, aggregate.candidate)]
        metrics = ("reference", "permutation", "rescaling")
        require_evidence(aggregate.rows == len(selected)
                         and aggregate.maxima.model_dump() == {
                             metric: max(getattr(row.ratios, metric) for row in selected)
                             for metric in metrics}
                         and aggregate.zeros == {
                             metric: sum(getattr(row.ratios, metric) == 0 for row in selected)
                             for metric in metrics}, "Research figure aggregate differs")
    description = "\n".join(f"{item.report.prover}: {item.sha256}" for item in data.reports)
    with Image.open(figures / "research-controls.png") as image:
        require_evidence(image.info.get("Description") == description,
                         "Research PNG report provenance differs")
    svg = (figures / "research-controls.svg").read_text()
    tree = ElementTree.fromstring(svg)
    require_evidence(tree.findtext(".//{http://purl.org/dc/elements/1.1/}description") == description,
                     "Research SVG report provenance differs")
    dashboard_text = (figures / "research-dashboard.html").read_text()
    require_evidence(svg[svg.index("<svg "):] in dashboard_text,
                     "Research dashboard SVG differs from canonical figure")
    dashboard = _HTML(dashboard_text)
    embedded = [element for element in dashboard.elements
                if element.tag == "script" and element.attrs.get("id") == "research-data"]
    require_evidence(len(embedded) == 1
                     and embedded[0].attrs.get("type") == "application/json"
                     and json.loads("".join(embedded[0].chunks)) == data.model_dump(mode="json"),
                     "Research dashboard data differs from canonical figure data")


def _fresh_cache(directory: Path) -> None:
    replay_cache(directory)


def _research_content(text: str, edition: str, research: ResearchContext) -> None:
    compact = "".join(unicodedata.normalize("NFKC", text).split()).replace("−", "-")
    for token in ("ALIGNMENT_LOGICAL_TABLE", "ALIGNMENT_NUMERICAL_TABLE"):
        for row in research.values[token].splitlines()[2:]:
            expected = "".join(row.replace("|", "").replace("`", "").split())
            require_evidence(expected in compact, f"Research result row missing: {edition}, {row}")


def _research_pdf_tables(layout: str, research: ResearchContext) -> None:
    lines = layout.splitlines()
    for token in ("ALIGNMENT_LOGICAL_TABLE", "ALIGNMENT_NUMERICAL_TABLE"):
        source = research.values[token].splitlines()
        expected = [[cell.strip().replace("`", "") for cell in row.strip("|").split("|")]
                    for row in (source[:1] + source[2:])]
        headers = [index for index, line in enumerate(lines)
                   if "".join(line.split()) == "".join(expected[0])]
        observed_tables: list[list[list[str]]] = []
        for index in headers:
            rows: list[list[str]] = []
            starts: list[int] = []
            for line in lines[index + 1:]:
                if not line.strip():
                    if rows:
                        break
                    continue
                cells = list(re.finditer(r"\S+(?:[ \t]\S+)*", line))
                if len(cells) == len(expected[0]):
                    rows.append([cell.group() for cell in cells])
                    starts = [cell.start() for cell in cells]
                elif rows and len(cells) < len(expected[0]):
                    for cell in cells:
                        column = min(range(len(starts)), key=lambda i: abs(starts[i] - cell.start()))
                        rows[-1][column] += cell.group()
                else:
                    break
            observed_tables.append(rows)
        matched = False
        for start in range(len(observed_tables)):
            joined: list[list[str]] = []
            for fragment in observed_tables[start:]:
                joined.extend(fragment)
                if joined == expected[1:]:
                    matched = True
                    break
                if joined != expected[1:len(joined) + 1]:
                    break
        require_evidence(matched,
                         f"Research result row missing: PDF, {token}")


def _content(
    root: Path, receipt: _Receipt, context: PublicationContext, sumo: SumoReport,
    research: ResearchContext, inference: InferenceContext, bridge: BridgeContext,
) -> tuple[str, str]:
    html = _html(root, receipt)
    docx = _docx(root, receipt)
    pdf = root / receipt.editions["pdf"]
    info = _command(["pdfinfo", str(pdf)])
    pdf_text = _command(["pdftotext", str(pdf), "-"])
    _pdf_margin(pdf, context.settings.publication.margin_mm)
    _pdf_images(pdf, {name: root / "output/manuscript/figures" / name for name in _FIGURES})
    for page, abstract in enumerate(context.settings.paper.graphical_abstracts, 2):
        with TemporaryDirectory(prefix="rikishi-graphical-abstract-") as temporary:
            _command(["pdfimages", "-f", str(page), "-l", str(page), "-png",
                      str(pdf), str(Path(temporary) / "abstract")])
            with Image.open(root / "output/manuscript" / abstract.image) as image:
                expected_size, expected_rgb = image.size, image.convert("RGB").tobytes()
            matches = []
            for candidate in Path(temporary).glob("*.png"):
                with Image.open(candidate) as image:
                    matches.append(image.size == expected_size
                                   and image.convert("RGB").tobytes() == expected_rgb)
            require_evidence(any(matches), f"Graphical abstract missing from actual PDF page {page}")
    _clean(pdf_text, "PDF")
    texts = {
        "HTML": " ".join(e.text for e in html.elements if e.tag == "body"),
        "DOCX": docx, "PDF": pdf_text,
    }
    for edition in ("HTML", "DOCX"):
        _research_content(texts[edition], edition, research)
    layout = _command(["pdftotext", "-layout", str(pdf), "-"])
    _research_pdf_tables(layout, research)
    _ontology_pdf_table(layout, receipt.substitutions["ONTOLOGY_STRUCTURE_TABLE"])
    for edition, text in texts.items():
        verify_inference_content(layout if edition == "PDF" else text, inference, edition)
        verify_bridge_content(layout if edition == "PDF" else text, bridge, edition)
        compact = re.sub(r"\s+", "", text)
        for citations in sumo.cases.values():
            for citation in citations:
                require_evidence(re.sub(r"\s+", "", citation.raw_kif) in compact,
                                 f"SUMO source formula missing: {edition}, line {citation.line}")
    abstract_index = next(i for i, e in enumerate(html.elements) if e.attrs.get("id") == "abstract")
    html_front = " ".join(e.text for e in html.elements[:abstract_index] if e.tag == "p" or e.tag == "h1")
    pdf_body = pdf_text[pdf_text.find("\f", pdf_text.find("Contents")) + 1:]
    authors = [author.name for author in context.settings.authors]
    affiliations = list(dict.fromkeys(a for author in context.settings.authors for a in author.affiliations))
    orcids = [author.orcid for author in context.settings.authors if author.orcid is not None]
    for edition, text in (("HTML", html_front), ("DOCX", docx.split("\nAbstract\n")[0]),
                          ("PDF cover", pdf_text.split("\f")[0])):
        for expected in (context.settings.paper.title, context.settings.paper.subtitle,
                         context.settings.paper.date, *authors, *affiliations, *orcids):
            require_evidence(_key(expected) in _key(text), f"{edition} publication text missing: {expected}")
    require_evidence(_key(context.settings.paper.title) in _key(info), "PDF title metadata missing")
    with TemporaryDirectory(prefix="rikishi-pdf-cover-") as temporary:
        _command(["pdfimages", "-f", "1", "-l", "1", "-png", str(pdf), str(Path(temporary) / "cover")])
        with Image.open(root / "output/manuscript/figures/graphical-abstract.png") as image:
            canonical, size = image.convert("RGB").tobytes(), image.size
        matches: list[bool] = []
        for path in Path(temporary).glob("*.png"):
            with Image.open(path) as image:
                matches.append(image.size == size and image.convert("RGB").tobytes() == canonical)
        require_evidence(any(matches), "PDF first-page canonical cover image missing")
    body = (root / "output/manuscript/rikishi-body.md").read_text()
    identifiers = {e.attrs["id"]: e for e in html.elements if "id" in e.attrs}
    counters = [0] * 6
    for level, title, label in re.findall(r"^(#{1,6}) (.*?) \{#(sec:[^}]+)\}$", body, re.MULTILINE):
        depth = len(level)
        counters[depth - 1] += 1
        counters[depth:] = [0] * (6 - depth)
        number = ".".join(str(n) for n in counters[:depth])
        node = identifiers[label]
        require_evidence(node.tag == f"h{depth}" and node.attrs.get("data-number") == number
                         and _key(title) in _key(node.text), f"HTML section numbering differs: {label}")
        _references(html, label, number)
        for edition, text in (("PDF", pdf_body), ("DOCX", docx)):
            require_evidence(_key(number + title) in _key(text), f"{edition} numbered heading missing: {label}")
    for number, label in enumerate(re.findall(r"\{#(eq:[^}]+)\}", body), 1):
        require_evidence(re.search(rf"\(\s*{number}\s*\)", identifiers[label].text) is not None,
                         f"HTML equation number missing: {label}")
        _references(html, label, str(number))
        for edition, text in (("PDF", pdf_body), ("DOCX", docx)):
            require_evidence(re.search(rf"\(\s*{number}\s*\)", text) is not None,
                             f"{edition} equation number missing: {label}")
    for formula, label in re.findall(r"\$\$(.*?)\$\$\s*\{#(eq:[^}]+)\}", body, re.DOTALL):
        require_evidence(re.sub(r"\s+", "", formula) in re.sub(r"\s+", "", identifiers[label].text),
                         f"HTML equation content differs: {label}")
    kinds: dict[str, int] = {}
    for kind, label in re.findall(r"^::: \{\.(\w+) #([^ }]+)", body, re.MULTILINE):
        kinds[kind] = kinds.get(kind, 0) + 1
        marker = f"{kind.title()} {kinds[kind]}"
        _references(html, label, marker)
        for edition, text in (("HTML", identifiers[label].text), ("PDF", pdf_body), ("DOCX", docx)):
            require_evidence(marker in " ".join(text.split()), f"{edition} formalism number missing: {label}")
    for number, label in enumerate(re.findall(r"\{#(fig:[^}]+)\}", body), 1):
        require_evidence(re.search(rf"Figure\s+{number}\s*:", identifiers[label].text) is not None,
                         f"HTML body figure numbering differs: {label}")
        _references(html, label, str(number))
        for edition, text in (("PDF", pdf_body), ("DOCX", docx)):
            require_evidence(re.search(rf"Figure\s+{number}\s*:", text) is not None,
                             f"{edition} body figure number missing: {label}")
    entries = TypeAdapter(list[_BibliographyEntry]).validate_json(_command([
        "pandoc", str(root / "output/manuscript/references.bib"), "-f", "bibtex", "-t", "csljson",
        "--fail-if-warnings",
    ]))
    pdf_bibliography = _pdf_body_text(pdf, context.settings.publication.margin_mm)
    for entry in entries:
        for edition, text in (("HTML", identifiers[f"ref-{entry.id}"].text),
                              ("PDF", pdf_bibliography), ("DOCX", docx)):
            require_evidence(_key(entry.title) in _key(text),
                             f"{edition} bibliography title missing: {entry.id}")
    return info, pdf_text


def verify_manuscript(root: Path) -> None:
    """Replay publication authorities and inspect the three actual receipted editions."""
    root = root.resolve(strict=True)
    output = root / "output/manuscript"
    receipt = _Receipt.model_validate_json(_read(output / "render-receipt.json"))
    require_evidence(not receipt.template_worktree_used, "Active template worktree was used")
    require_evidence(receipt.template_revision == RENDERER_REVISION, "Renderer revision differs from pin")
    snapshot = contained_path(root, receipt.renderer_snapshot)
    origin = json.loads(_read(snapshot.parent / "renderer-origin.json"))
    require_evidence(origin["revision"] == receipt.template_revision
                     and origin["archive_sha256"] == receipt.renderer_archive_sha256,
                     "Renderer origin differs from receipt")
    require_evidence(bool(receipt.renderer_imported_sources), "Imported renderer manifest is empty")
    require_evidence(all(origin["sources"].get(p) == digest
                         for p, digest in receipt.renderer_imported_sources.items()),
                     "Imported renderer source differs from origin")
    verify_sources(snapshot, receipt.renderer_imported_sources)
    require_evidence(receipt.editions == _EDITIONS, "Edition paths differ from native combined contract")
    for record in receipt.artifacts:
        _read(contained_path(root, record.path))
    verify_artifacts(root, receipt.artifacts)
    recorded = {record.path for record in receipt.artifacts}
    required = {*_EDITIONS.values(), "output/pdf/_combined_manuscript.log",
                "output/pdf/_latex_stdout.log", *(f"output/manuscript/{name}" for name in (
        "rikishi-body.md", "rikishi.md", "rikishi-office-web.md", "references.bib", "references.csl",
        "config.yaml", "fep-example.json", "sumo-demonstrations.json", "ontology-structure.json",
        "research/fresh-cache/result.json", "office-reference.docx", "office-reference.native-default.docx",
        "rikishi-native.docx",
    ))}
    tex_errors = [line for line in _read(root / "output/pdf/_combined_manuscript.log").splitlines()
                  if line.startswith(b"!")]
    require_evidence(not tex_errors, "Native PDF compilation contains TeX errors")
    for directory in ("output/manuscript/figures", "output/figures"):
        required.update(f"{directory}/{name}" for name in _FIGURES)
    required.add("examples/EventTransport.lean")
    for directory in ("output/manuscript/figures", "output/figures", "output/web/figures"):
        required.update(f"{directory}/{name}" for name in (
            "research-controls.png", "research-controls.svg", "research-controls.json",
            "research-dashboard.html",
            "ontology-structure.png", "ontology-structure.svg", "ontology-structure.json",
            "bridge-evidence.png", "bridge-evidence.svg", "bridge-free-energy.png", "bridge-free-energy.svg",
            "bridge-native-controls.png", "bridge-native-controls.svg", "bridge-figure-inputs.json", "bridge-explorer.html",
            "witness-channels.png", "witness-channels.svg", "witness-evidence-scaling.png",
            "witness-evidence-scaling.svg", "witness-research.json",
            "witness-sequential.png", "witness-sequential.svg", "witness-dynamics.json",
            "witness-sequences.png", "witness-sequences.svg", "witness-sequences.json",
            "EventTransport.lean",
        ))
    required.update(path.relative_to(root).as_posix()
                    for path in (output / "research").rglob("*") if path.is_file())
    required.update(path.relative_to(root).as_posix()
                    for path in (output / "inference").rglob("*") if path.is_file())
    required.update(path.relative_to(root).as_posix()
                    for path in (output / "bridge").rglob("*") if path.is_file())
    require_evidence(required <= recorded, f"Required artifact records missing: {sorted(required - recorded)}")
    context, sumo, research, bridge = _projections(root, receipt)
    office_policy = _office_policy(root, receipt, margin_mm=context.settings.publication.margin_mm)
    office_bytes = _read(root / receipt.editions["docx"])
    office_content = verify_office_content_projection(_read(output / "rikishi-native.docx"), office_bytes)
    office_math = verify_office_content_math(office_bytes)
    require_evidence(len(office_math.gathered_sha256)
                     == (output / "rikishi-body.md").read_text().count(r"\begin{gathered}"),
                     "Word gathered display inventory differs from the canonical body")
    require_evidence(office_content == receipt.office_content and office_math == receipt.office_math,
                     "Office content or math receipt differs from actual packages")
    inference = load_inference_context(output / "inference")
    require_evidence(receipt.inference_inputs == inference.input_sha256,
                     "Inference publication input digest differs from the receipt")
    _fresh_cache(output / "research/fresh-cache")
    require_evidence(set(receipt.report_inputs) == {
        "output/corpus-files.png", "output/corpus-composition.png"}, "Report input manifest differs")
    for relative, digest in receipt.report_inputs.items():
        source = _read(root / relative)
        require_evidence(hashlib.sha256(source).hexdigest() == digest, f"Report input changed: {relative}")
        require_evidence(source == _read(output / "figures" / Path(relative).name),
                         f"Report figure differs from canonical image: {relative}")
    for name in _FIGURES:
        require_evidence(_read(root / "output/figures" / name) == _read(output / "figures" / name),
                         f"PDF figure copy differs: {name}")
    _research_figures(root, context, research)
    verify_bridge_figures(root, bridge, dpi=context.settings.publication.figure_dpi,
                          decimal_places=context.settings.publication.decimal_places)
    info, text = _content(root, receipt, context, sumo, research, inference, bridge)
    try:
        free_energy([0.4, 0.4], [0.8, 0.2], [0.5, 0.5])
    except ProbabilityError as error:
        negative_control = str(error)
    else:
        raise AssertionError("unnormalized prior was accepted")
    inspection = inspect_formalization(root.parents[2] / "ActiveInferenceInstitute/Public/fep_formal")
    result = {
        "renderer_imported_modules_verified": len(receipt.renderer_imported_sources),
        "active_template_worktree_used": receipt.template_worktree_used,
        "artifact_hashes_verified": len(receipt.artifacts), "editions": receipt.editions,
        "publication_authorities_verified": len(receipt.publication_inputs),
        "research_inputs_verified": research.input_sha256,
        "inference_inputs_verified": inference.input_sha256,
        "bridge_inputs_verified": bridge.input_sha256,
        "bridge_source_tables_in_all_editions": "pass",
        "bridge_figure_inputs_copies_and_finite_curves": "pass",
        "office_page_policy": asdict(office_policy),
        "office_content_projection": asdict(office_content), "office_math": asdict(office_math),
        "inference_source_tables_in_all_editions": "pass",
        "research_source_tables_in_all_editions": "pass",
        "research_figure_data_and_copies": "pass",
        "ontology_structure_source_tables_in_all_editions": "pass",
        "ontology_structure_report_and_figure_copies": "pass",
        "fresh_cache_saved_observations": "pass",
        "source_checks": receipt.source_checks.model_dump(), "publication_projections": "pass",
        "docx_archive_and_canonical_images": "pass", "html_canonical_local_figures": "pass",
        "pdf_cover_and_text": "pass", "negative_control": negative_control,
        "sumo_source_examples_in_all_editions": "pass",
        "sumo_source_observations": sumo.observations.model_dump(),
        "source_inspection_commit": inspection["commit"], "lean_compiled": False,
    }
    evidence = root / ".omo/evidence/fep-manuscript"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "formalization-inspection.json").write_text(json.dumps(inspection, indent=2) + "\n")
    (evidence / "pdfinfo.txt").write_text(info)
    (evidence / "pdf-text.txt").write_text(text)
    (evidence / "verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))

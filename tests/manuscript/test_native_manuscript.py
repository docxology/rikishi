import ctypes
import errno
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from collections.abc import Callable
from dataclasses import asdict
from fractions import Fraction
from functools import partial
from pathlib import Path
from time import monotonic
from typing import Final, Literal, assert_never
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile

import pytest
import yaml
from defusedxml import ElementTree
from PIL import Image, PngImagePlugin
from pydantic import ValidationError

from rikishi.cache_inheritance import CacheDiagnosticError
from rikishi.manuscript_provenance import ProvenanceError
from rikishi.manuscript_verification import (
    _HTML,
    _fresh_cache,
    _office_policy,
    _ontology_pdf_table,
    _ontology_report,
    _ontology_table,
    _pdf_images,
    _Receipt,
    _research_pdf_tables,
    verify_manuscript,
)
from rikishi.ontology_observations import measure_source_structure, structure_substitutions
from rikishi.publication_office import OfficePagePolicyError
from rikishi.publication_office_content import OfficeContentError, project_office_content
from rikishi.publication_research import load_research_context
from rikishi.runtime_process import run_bounded
from rikishi.sumo_demonstrations import FrozenSource

FIGURES = (
    "graphical-abstract.png", "fep-free-energy.png", "corpus-files.png", "corpus-composition.png",
    "sumo-system.png", "research-controls.png", "ontology-structure.png",
    "bridge-evidence.png", "bridge-free-energy.png", "bridge-native-controls.png",
    "witness-channels.png", "witness-evidence-scaling.png", "witness-sequential.png",
    "witness-sequences.png",
    "abstract-source.png", "abstract-witness.png", "abstract-evidence.png",
)


def test_native_receipt_requires_research_inputs(receipt_schema):
    receipt = receipt_schema.model_dump(mode="json")
    receipt.pop("research_inputs", None)
    with pytest.raises(ValidationError, match="research_inputs"):
        _Receipt.model_validate_json(json.dumps(receipt))


def test_native_receipt_requires_inference_inputs(receipt_schema):
    receipt = receipt_schema.model_dump(mode="json")
    receipt.pop("inference_inputs")
    with pytest.raises(ValidationError, match="inference_inputs"):
        _Receipt.model_validate_json(json.dumps(receipt))


@pytest.mark.parametrize("field", ["bridge_inputs", "office_reference", "office_content", "office_math"])
def test_native_receipt_requires_bridge_and_office_authorities(receipt_schema, field):
    receipt = receipt_schema.model_dump(mode="json")
    receipt.pop(field)
    with pytest.raises(ValidationError, match=field):
        _Receipt.model_validate_json(json.dumps(receipt))


@pytest.mark.integration
def test_pdf_research_table_requires_complete_order_across_repeated_page_headers(project_root):
    research = load_research_context(project_root / "output/research", decimal_places=6)
    tables = []
    for token in ("ALIGNMENT_LOGICAL_TABLE", "ALIGNMENT_NUMERICAL_TABLE"):
        lines = research.values[token].splitlines()
        rows = ["    ".join(cell.strip().replace("`", "") for cell in line.strip("|").split("|"))
                for line in [lines[0], *lines[2:]]]
        tables.append(rows)
    logical, numerical = tables
    first = "\n".join(logical[:7])
    continued = "\n".join([logical[0], *logical[7:]])
    layout = first + "\n\n21\f" + continued + "\n\n" + "\n".join(numerical)
    _research_pdf_tables(layout, research)
    with pytest.raises(ProvenanceError, match="Research result row missing"):
        _research_pdf_tables(layout.replace(logical[-1], ""), research)
    with pytest.raises(ProvenanceError, match="Research result row missing"):
        _research_pdf_tables(layout.replace(logical[-1], logical[-2]), research)


def test_native_receipt_requires_ontology_structure(receipt_schema):
    receipt = receipt_schema.model_dump(mode="json")
    receipt.pop("ontology_structure_sha256", None)
    with pytest.raises(ValidationError, match="ontology_structure_sha256"):
        _Receipt.model_validate_json(json.dumps(receipt))


@pytest.fixture
def portable_structure(tmp_path):
    text = ("(subclass Leaf Root)\n(subclass Leaf Root)\n(subclass Leaf Parent)\n"
            "(subclass Parent Root)\n(subrelation narrower broader)\n")
    source = FrozenSource(path="retained/Merge.kif", ontology_path="Merge.kif", commit="1" * 40,
                          clean=True, text=text, sha256=hashlib.sha256(text.encode()).hexdigest())
    path = tmp_path / "ontology-structure.json"
    path.write_text(measure_source_structure(source).model_dump_json())
    return source, path


def test_portable_ontology_structure_recomputes_real_source(portable_structure):
    source, path = portable_structure
    report = _ontology_report(path, source, hashlib.sha256(path.read_bytes()).hexdigest())
    assert report.graphs[0].assertion_count == 4
    assert report.graphs[0].unique_edges == 3
    assert report.graphs[0].multiple_parent_count == 1
    assert report.graphs[1].unique_edges == 1


@pytest.mark.parametrize("graph", [0, 1])
@pytest.mark.parametrize("field", [
    "assertion_count", "unique_edges", "node_count", "root_count", "multiple_parent_count",
    "weak_component_count", "cyclic_component_count", "cyclic_node_count", "self_loop_count",
])
def test_portable_rebound_ontology_counts_must_recompute(portable_structure, graph, field):
    source, path = portable_structure
    data = json.loads(path.read_text())
    data["graphs"][graph][field] += 1
    path.write_text(json.dumps(data))
    with pytest.raises(ProvenanceError, match="Ontology structure report differs from retained source"):
        _ontology_report(path, source, hashlib.sha256(path.read_bytes()).hexdigest())


@pytest.mark.parametrize("field, value", [
    ("source_sha256", "0" * 64), ("source_commit", "0" * 40), ("ontology_path", "Other.kif"),
    ("graphs", []),
])
def test_portable_rebound_ontology_identity_must_recompute(portable_structure, field, value):
    source, path = portable_structure
    data = json.loads(path.read_text())
    data[field] = value
    path.write_text(json.dumps(data))
    with pytest.raises(ProvenanceError, match="Ontology structure report differs from retained source"):
        _ontology_report(path, source, hashlib.sha256(path.read_bytes()).hexdigest())


def test_portable_ontology_report_requires_receipt_digest(portable_structure):
    source, path = portable_structure
    with pytest.raises(ProvenanceError, match="Ontology structure report changed"):
        _ontology_report(path, source, "0" * 64)


def test_portable_ontology_table_requires_actual_cells(portable_structure):
    source, _ = portable_structure
    table = structure_substitutions(measure_source_structure(source))["ONTOLOGY_STRUCTURE_TABLE"]
    rows = [[cell.strip().replace("`", "") for cell in row.strip("|").split("|")]
            for row in table.splitlines()[2:]]
    html = "<table>" + "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row)
                                  + "</tr>" for row in rows) + "</table>"
    document = _HTML(html)
    observed = [[cell.text for cell in row.children if cell.tag == "td"]
                for row in document.elements if row.tag == "tr"]
    _ontology_table(observed, table, "HTML")
    layout = "\n".join("    ".join(row) for row in rows)
    _ontology_pdf_table(layout, table)
    observed[0][1] = "999999"
    with pytest.raises(ProvenanceError, match="Ontology structure row missing: HTML"):
        _ontology_table(observed, table, "HTML")
    with pytest.raises(ProvenanceError, match="Ontology structure row missing: PDF"):
        _ontology_pdf_table(layout.replace("subclass", "altered-subclass"), table)


@pytest.fixture
def saved_fresh_cache(project_root, tmp_path):
    source = project_root / "output/research/fresh-cache"
    return Path(shutil.copytree(source, tmp_path / "saved-cache"))


def test_relocated_fresh_cache_saved_observations_verify(saved_fresh_cache):
    _fresh_cache(saved_fresh_cache)


@pytest.mark.parametrize("field, value", [
    ("status", "failed"), ("freshcache_scope", "none"),
    ("semantic_validation", True), ("bindings_stable", False),
])
def test_saved_fresh_cache_rejects_overstated_receipt(saved_fresh_cache, field, value):
    path = saved_fresh_cache / "result.json"
    data = json.loads(path.read_text())
    data[field] = value
    path.write_text(json.dumps(data))
    with pytest.raises(ProvenanceError, match="Fresh-cache experiment"):
        _fresh_cache(saved_fresh_cache)


def test_saved_fresh_cache_requires_actual_observation(saved_fresh_cache):
    path = saved_fresh_cache / "result.json"
    data = json.loads(path.read_text())
    data["cases"][0]["observation"]["cached_path"] = []
    path.write_text(json.dumps(data))
    with pytest.raises(ProvenanceError, match="Fresh-cache observation differs from raw report"):
        _fresh_cache(saved_fresh_cache)


def test_saved_fresh_cache_rechecks_controlled_observations(saved_fresh_cache):
    path = saved_fresh_cache / "result.json"
    data = json.loads(path.read_text())
    authority = json.loads((saved_fresh_cache / "sources/src/rikishi/data/fresh-cache-v1.json").read_text())
    case = next(case for case in authority["cases"] if case["expect_partial"])
    recorded = next(recorded for recorded in data["cases"] if recorded["name"] == case["name"])
    observation = recorded["observation"]
    for field in ("cached_path", "generated_path"):
        observation[field].remove("PartialValuedRelation")
    observation["generated_sources"].pop("PartialValuedRelation")
    path.write_text(json.dumps(data))
    (saved_fresh_cache / case["name"] / "observation.json").write_text(json.dumps(observation))
    with pytest.raises(CacheDiagnosticError, match="generated partial classification differs from control"):
        _fresh_cache(saved_fresh_cache)


@pytest.fixture(scope="module")
def rendered_native_outputs(project_root, tmp_path_factory):
    """Exercise the deployed entrypoint with production budgets and traced children."""
    retained = tmp_path_factory.mktemp("native-manuscript-production")
    environment = dict(os.environ)
    parent_marker = os.environ.get("PYTEST_CURRENT_TEST")
    # The pinned dependency uses this pytest metadata for eight-second smoke-test
    # limits. This integration child runs the deployed entrypoint with its normal
    # production limits; parent metadata and coverage tracing remain intact.
    environment.pop("PYTEST_CURRENT_TEST", None)
    command = [sys.executable, str(project_root / "scripts/render_manuscript.py")]
    stdout, stderr = retained / "stdout.log", retained / "stderr.log"
    started = monotonic()
    result = run_bounded(command, cwd=project_root, stdout=stdout, stderr=stderr,
                         timeout=1800, environment=environment)
    receipt = {"command": command, "cwd": str(project_root),
        "outer_wall_timeout_seconds": 1800, "elapsed_seconds": monotonic() - started,
        "returncode": result.returncode, "timed_out": result.timed_out,
        "child_environment_excludes": ["PYTEST_CURRENT_TEST"],
        "parent_marker_unchanged": os.environ.get("PYTEST_CURRENT_TEST") == parent_marker,
        "coverage_configuration_preserved": environment.get("COVERAGE_PROCESS_CONFIG")
            == os.environ.get("COVERAGE_PROCESS_CONFIG"),
        "stdout_sha256": hashlib.sha256(stdout.read_bytes()).hexdigest(),
        "stderr_sha256": hashlib.sha256(stderr.read_bytes()).hexdigest()}
    (retained / "launch.json").write_text(json.dumps(receipt, indent=2) + "\n")
    assert receipt["parent_marker_unchanged"] and receipt["coverage_configuration_preserved"]
    assert not result.timed_out and result.returncode == 0, (
        f"Actual production renderer failed; retained invocation and output: {retained}\n"
        + stderr.read_text(errors="backslashreplace")
    )
    return project_root


@pytest.mark.integration
def test_native_template_render_and_verify(rendered_native_outputs):
    verify_manuscript(rendered_native_outputs)


@pytest.mark.integration
def test_native_conditioning_cell_has_separate_state_products(rendered_native_outputs: Path) -> None:
    # Given the actual public producer's DOCX, locate the theorem's atlas row.
    namespaces = {
        "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
        "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    }
    with ZipFile(rendered_native_outputs / "output/docx/rikishi.docx") as archive:
        document = ElementTree.fromstring(archive.read("word/document.xml"))
    rows = [row for row in document.findall(".//w:tr", namespaces)
            if "UniformPrior.posterior_reconstruction" in
            [text.text for text in row.findall(".//w:t", namespaces)]]
    assert len(rows) == 1
    cells = rows[0].findall("w:tc", namespaces)
    assert len(cells) == 4

    # When reading the native math objects in the calculation cell.
    equations = cells[2].findall(".//m:oMath", namespaces)

    # Then each state has a short, separately laid-out product with exact values.
    assert len(equations) == 2, "State products must not share one unbreakable math object"
    for equation, numerator in zip(equations, (1, 3), strict=True):
        fractions = equation.findall("m:f", namespaces)
        values = [Fraction(
            int("".join(part.itertext())), int("".join(denominator.itertext())))
            for fraction in fractions
            for part in fraction.findall("m:num", namespaces)
            for denominator in fraction.findall("m:den", namespaces)]
        operators = [text.text for text in equation.findall("m:r/m:t", namespaces)]
        assert values == [Fraction(numerator, 4), Fraction(1, 2), Fraction(numerator, 8)]
        assert operators == ["×", "="]
        assert values[0] * values[1] == values[2]


@pytest.mark.integration
def test_pdf_pixel_validation_rejects_a_real_one_pixel_change(rendered_native_outputs, tmp_path):
    pdf = rendered_native_outputs / "output/pdf/rikishi_combined.pdf"
    expected = {name: rendered_native_outputs / "output/manuscript/figures" / name for name in FIGURES}
    _pdf_images(pdf, expected)
    with Image.open(expected["graphical-abstract.png"]) as original:
        changed = original.convert("RGB")
    pixel = changed.getpixel((0, 0))
    assert isinstance(pixel, tuple) and len(pixel) == 3
    red, green, blue = pixel
    changed.putpixel((0, 0), ((red + 1) % 256, green, blue))
    target = tmp_path / "altered-cover.png"
    changed.save(target)
    with pytest.raises(ProvenanceError, match="PDF canonical figure missing: graphical-abstract.png"):
        _pdf_images(pdf, {**expected, "graphical-abstract.png": target})


@pytest.fixture(scope="module")
def verified_native_outputs(rendered_native_outputs, tmp_path_factory):
    root = _copy_native_outputs(rendered_native_outputs, tmp_path_factory.mktemp("verified-native"))
    verify_manuscript(root)
    return root


@pytest.fixture
def manuscript_copy(verified_native_outputs, tmp_path):
    return _copy_native_outputs(verified_native_outputs, tmp_path)


_COPY_NATIVE_APFS: Final = sys.platform == "darwin"
_CLONE_LIBRARY: Final = ctypes.CDLL(None, use_errno=True) if _COPY_NATIVE_APFS else None
if _CLONE_LIBRARY is not None:
    _CLONE_LIBRARY.clonefile.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint32]
    _CLONE_LIBRARY.clonefile.restype = ctypes.c_int


def _reject_native_links(directory: str, names: list[str]) -> set[str]:
    """Reject symbolic fixture inputs; never exclude a name from a tree copy."""
    path = Path(directory).absolute()
    for candidate in (path, *path.parents, *(path / name for name in names)):
        if candidate.is_symlink():
            raise OSError(errno.ELOOP, os.strerror(errno.ELOOP), str(candidate))
    return set()


def _copy_native_file(source: str | Path, destination: str | Path, *, use_clone: bool) -> str:
    """Copy one owned regular file, create-only; a requested clone never falls back."""
    original, target = Path(source).absolute(), Path(destination).absolute()
    for path in (original, target):
        if "\0" in str(path) or ".." in path.parts:
            raise OSError(errno.EINVAL, os.strerror(errno.EINVAL), str(path))
        _reject_native_links(str(path.parent), [path.name])
    before = original.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise OSError(errno.EINVAL, os.strerror(errno.EINVAL), str(original))
    if target.exists() or target.is_symlink():
        raise FileExistsError(errno.EEXIST, os.strerror(errno.EEXIST), str(target))
    if use_clone:
        if _CLONE_LIBRARY is None:
            raise OSError(errno.ENOTSUP, os.strerror(errno.ENOTSUP), str(target))
        # Installed sys/clonefile.h: NOFOLLOW(0x1) | NOFOLLOW_ANY(0x8).
        if _CLONE_LIBRARY.clonefile(os.fsencode(original), os.fsencode(target), 0x0009) != 0:
            error = ctypes.get_errno()
            raise OSError(error, os.strerror(error), str(target))
    else:
        with original.open("rb") as incoming, target.open("xb") as outgoing:
            shutil.copyfileobj(incoming, outgoing)
    copied = target.lstat()
    if (not stat.S_ISREG(copied.st_mode) or copied.st_nlink != 1
            or (copied.st_dev, copied.st_ino) == (before.st_dev, before.st_ino)):
        raise OSError(errno.EIO, os.strerror(errno.EIO), str(target))
    shutil.copystat(original, target, follow_symlinks=False)
    return str(target)


def _copy_native_outputs(project_root: Path, tmp_path: Path, *,
                         use_clone: bool = _COPY_NATIVE_APFS) -> Path:
    _reject_native_links(str(project_root), [])
    _reject_native_links(str(tmp_path), [])
    copy_file = partial(_copy_native_file, use_clone=use_clone)
    root = tmp_path / "docxology/Private/rikishi"
    receipt = json.loads((project_root / "output/manuscript/render-receipt.json").read_text())
    snapshot = receipt["renderer_snapshot"]
    for relative in (
        "output/manuscript", "output/pdf", "output/web", "output/docx", "output/figures",
        "manuscript", "config", snapshot,
    ):
        shutil.copytree(project_root / relative, root / relative,
                        copy_function=copy_file, ignore=_reject_native_links)
    origin = "renderer-origin.json"
    copy_file((project_root / snapshot).parent / origin, (root / snapshot).parent / origin)
    for relative in (
        "pyproject.toml", "output/analytics.json", "output/data/corpus.json",
        "output/formalization/verification.json", "output/corpus-files.png",
        "output/corpus-composition.png",
    ):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        copy_file(project_root / relative, target)
    for record in receipt["artifacts"]:
        target = root / record["path"]
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            copy_file(project_root / record["path"], target)
    formal = tmp_path / "ActiveInferenceInstitute/Public/fep_formal"
    formal.parent.mkdir(parents=True)
    formal.symlink_to(project_root.parents[2] / "ActiveInferenceInstitute/Public/fep_formal")
    return root


def rebind(root: Path, relative: str) -> None:
    path = root / "output/manuscript/render-receipt.json"
    receipt = json.loads(path.read_text())
    target = root / relative
    for record in receipt["artifacts"]:
        if record["path"] == relative:
            record["bytes"] = target.stat().st_size
            record["sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
    if relative == receipt["editions"]["docx"]:
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        receipt["office_reference"]["actual"]["docx_sha256"] = digest
        receipt["office_content"]["projected_sha256"] = digest
    path.write_text(json.dumps(receipt))


def rewrite_docx(root: Path, part: str, transform) -> None:
    path = root / "output/docx/rikishi.docx"
    with ZipFile(path) as archive:
        parts = {name: archive.read(name) for name in archive.namelist()}
    parts[part] = transform(parts[part])
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        for name, content in parts.items():
            archive.writestr(name, content)
    rebind(root, "output/docx/rikishi.docx")


def rewrite_native_docx(root: Path, part: str, transform: Callable[[bytes], bytes]) -> None:
    """Rebind permitted row projection so a later semantic validator is exercised."""
    relative = "output/manuscript/rikishi-native.docx"
    native = root / relative
    with ZipFile(native) as archive:
        parts = [(item, archive.read(item)) for item in archive.infolist()]
        comment = archive.comment
    with ZipFile(native, "w") as archive:
        archive.comment = comment
        for item, payload in parts:
            archive.writestr(item, transform(payload) if item.filename == part else payload)
    projection = project_office_content(native.read_bytes())
    (root / "output/docx/rikishi.docx").write_bytes(projection.docx)
    rebind(root, relative)
    rebind(root, "output/docx/rikishi.docx")
    receipt_path = root / "output/manuscript/render-receipt.json"
    receipt = json.loads(receipt_path.read_text())
    receipt["office_content"] = asdict(projection.receipt)
    receipt_path.write_text(json.dumps(receipt))


@pytest.mark.integration
def test_complete_relocated_editions_verify(manuscript_copy):
    verify_manuscript(manuscript_copy)


@pytest.mark.integration
@pytest.mark.parametrize("mutation", ["missing", "wide", "size"])
def test_rebound_actual_word_geometry_must_match_policy(manuscript_copy, mutation):
    def transform(data):
        if mutation == "missing":
            changed = re.sub(rb"<w:pgMar\b[^>]*/>", b"", data)
        elif mutation == "wide":
            changed = data.replace(b'w:left="680"', b'w:left="1440"')
        else:
            changed = data.replace(b'w:w="12240"', b'w:w="12000"')
        assert changed != data
        return changed

    rewrite_docx(manuscript_copy, "word/document.xml", transform)
    receipt_path = manuscript_copy / "output/manuscript/render-receipt.json"
    data = json.loads(receipt_path.read_text())
    # Rebind the digest so actual geometry, rather than a stale hash, rejects it.
    data["office_reference"]["actual"]["docx_sha256"] = hashlib.sha256(
        (manuscript_copy / "output/docx/rikishi.docx").read_bytes()).hexdigest()
    receipt = _Receipt.model_validate_json(json.dumps(data))
    with pytest.raises(OfficePagePolicyError, match="explicit pgSz|geometry differs"):
        _office_policy(manuscript_copy, receipt, margin_mm=12)


@pytest.mark.integration
def test_rebound_word_reference_must_preserve_native_style_payload(manuscript_copy):
    relative = "output/manuscript/office-reference.docx"
    target = manuscript_copy / relative
    with ZipFile(target) as archive:
        parts = [(item, archive.read(item)) for item in archive.infolist()]
    assert any(item.filename == "word/styles.xml" for item, _ in parts)
    with ZipFile(target, "w") as archive:
        for item, raw in parts:
            archive.writestr(item, raw + b"\n" if item.filename == "word/styles.xml" else raw)
    rebind(manuscript_copy, relative)
    data = json.loads((manuscript_copy / "output/manuscript/render-receipt.json").read_text())
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    data["office_reference"]["reference_sha256"] = digest
    data["office_reference"]["geometry"]["docx_sha256"] = digest
    receipt = _Receipt.model_validate_json(json.dumps(data))
    with pytest.raises(OfficePagePolicyError, match="reference differs from the exact approved"):
        _office_policy(manuscript_copy, receipt, margin_mm=12)


@pytest.mark.integration
@pytest.mark.parametrize("old,new,style", [
    (b'w:val="005EA8"', b'w:val="4F81BD"', "Hyperlink"),
    (b'w:val="005EA8"', b'w:val="005EA8" w:themeColor="accent1"', "Hyperlink"),
    (b"<w:keepLines />", b'<w:keepLines w:val="0" />', "ImageCaption"),
    (b"<w:keepNext />", b'<w:keepNext w:val="0" />', "CaptionedFigure"),
])
def test_rebound_word_must_propagate_approved_reference_styles(manuscript_copy, old, new, style):
    def transform(raw):
        pattern = rb'<w:style\b[^>]*w:styleId="' + style.encode() + rb'"[^>]*>.*?</w:style>'
        match = re.search(pattern, raw, re.DOTALL)
        assert match is not None and old in match[0]
        changed = match[0].replace(old, new, 1)
        return raw[:match.start()] + changed + raw[match.end():]

    # Both native and final hashes/row-custody receipts are coherently rebound.
    rewrite_native_docx(manuscript_copy, "word/styles.xml", transform)
    receipt = _Receipt.model_validate_json(
        (manuscript_copy / "output/manuscript/render-receipt.json").read_text())
    with pytest.raises(ProvenanceError, match=f"Actual Word reference style differs: {style}"):
        _office_policy(manuscript_copy, receipt, margin_mm=12)


@pytest.mark.integration
@pytest.mark.parametrize("mutation", ["decoy", "duplicate", "external", "type", "root", "namespace"])
def test_rebound_word_must_bind_the_actual_styles_part(manuscript_copy, mutation):
    native = manuscript_copy / "output/manuscript/rikishi-native.docx"
    with ZipFile(native) as archive:
        parts = {item.filename: (item, archive.read(item)) for item in archive.infolist()}
        comment = archive.comment
    item, raw = parts["word/_rels/document.xml.rels"]
    relation = re.search(rb'<Relationship\b[^>]*Type="http://schemas.openxmlformats.org/'
                         rb'officeDocument/2006/relationships/styles"[^>]*/>', raw)
    assert relation is not None
    extra = ()
    if mutation in {"root", "namespace"}:
        style, payload = parts["word/styles.xml"]
        if mutation == "root":
            payload = payload.replace(b"<w:styles ", b"<w:notStyles ", 1).replace(
                b"</w:styles>", b"</w:notStyles>")
        else:
            payload = payload.replace(b"<w:styles ", b'<x:styles xmlns:x="urn:unsupported-styles" ', 1).replace(
                b"</w:styles>", b"</x:styles>")
        parts["word/styles.xml"] = style, payload
    elif mutation == "decoy":
        raw = raw.replace(relation[0], relation[0].replace(
            b'Target="styles.xml"', b'Target="actual-styles.xml"'))
        extra = (("word/actual-styles.xml", parts["word/styles.xml"][1].replace(b"005EA8", b"4F81BD")),)
        ct, payload = parts["[Content_Types].xml"]
        parts["[Content_Types].xml"] = ct, payload.replace(b"</Types>",
            b'<Override PartName="/word/actual-styles.xml" ContentType="application/vnd.openxmlformats-'
            b'officedocument.wordprocessingml.styles+xml"/></Types>')
    elif mutation == "duplicate":
        raw = raw.replace(b"</Relationships>", relation[0].replace(b'Id="', b'Id="duplicate-')
                          + b"</Relationships>")
    elif mutation == "external":
        raw = raw.replace(relation[0], relation[0].replace(b'Target="styles.xml"',
            b'Target="https://example.invalid/styles.xml" TargetMode="External"'))
    else:
        ct, payload = parts["[Content_Types].xml"]
        parts["[Content_Types].xml"] = ct, payload.replace(
            b"application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml", b"text/plain", 1)
    parts["word/_rels/document.xml.rels"] = item, raw
    with ZipFile(native, "w") as archive:
        archive.comment = comment
        for item, payload in parts.values():
            archive.writestr(item, payload)
        for name, payload in extra:
            archive.writestr(name, payload)
    projection = project_office_content(native.read_bytes())
    (manuscript_copy / "output/docx/rikishi.docx").write_bytes(projection.docx)
    rebind(manuscript_copy, "output/manuscript/rikishi-native.docx")
    rebind(manuscript_copy, "output/docx/rikishi.docx")
    path = manuscript_copy / "output/manuscript/render-receipt.json"
    data = json.loads(path.read_text())
    data["office_content"] = asdict(projection.receipt)
    receipt = _Receipt.model_validate_json(json.dumps(data))
    with pytest.raises(ProvenanceError, match="Actual Word styles relationship|Actual Word styles content type"
                       "|Actual Word styles document root"):
        _office_policy(manuscript_copy, receipt, margin_mm=12)


@pytest.mark.integration
def test_rebound_word_must_retain_the_actual_row_projection(manuscript_copy):
    def transform(raw):
        changed = raw.replace(b"<w:cantSplit/>", b"", 1)
        assert changed != raw
        return changed

    rewrite_docx(manuscript_copy, "word/document.xml", transform)
    with pytest.raises(OfficeContentError, match="permitted row projection"):
        verify_manuscript(manuscript_copy)


@pytest.mark.integration
@pytest.mark.parametrize("edition", ["html", "docx"])
def test_rebound_editions_reject_altered_inference_table(manuscript_copy, edition):
    root = manuscript_copy
    expected = b"source individual inheritance"
    if edition == "html":
        relative = "output/web/index.html"
        path = root / relative
        raw = path.read_bytes()
        assert expected in raw
        path.write_bytes(raw.replace(expected, b"altered inference category"))
        rebind(root, relative)
    else:
        def transform(raw):
            assert expected in raw
            return raw.replace(expected, b"altered inference category")

        rewrite_native_docx(root, "word/document.xml", transform)
    with pytest.raises(ProvenanceError, match="Inference result row missing"):
        verify_manuscript(root)


@pytest.mark.integration
@pytest.mark.parametrize("name", ["research-dashboard.html", "bridge-explorer.html"])
def test_rebound_html_requires_working_offline_explorer_links(manuscript_copy, name):
    relative = "output/web/index.html"
    target = manuscript_copy / relative
    original = target.read_text()
    changed = original.replace("../figures/" + name, "../figures/missing-explorer.html")
    assert changed != original
    target.write_text(changed)
    rebind(manuscript_copy, relative)
    with pytest.raises(ProvenanceError, match="Offline explorer link missing"):
        verify_manuscript(manuscript_copy)


@pytest.mark.integration
@pytest.mark.parametrize("mutation, message", [
    ("bindings", "Fresh-cache initial bindings differ from after"),
    ("authority", "Fresh-cache retained authority differs from package"),
])
def test_complete_relocated_editions_reject_original_cache_mutants(manuscript_copy, mutation, message):
    root = manuscript_copy
    relative = "output/manuscript/research/fresh-cache/"
    if mutation == "bindings":
        relative += "bindings-after.json"
        data = json.loads((root / relative).read_bytes())
        before = json.loads((root / relative).with_name("bindings-before.json").read_bytes())
        key = next(iter(before))
        assert data[key] == before[key]
        data[key] = "0" * 64
    else:
        relative += "sources/src/rikishi/data/fresh-cache-v1.json"
        data = json.loads((root / relative).read_bytes())
        data["bindings"][".rikishi/upstream/sumo/Merge.kif"] = "0" * 64
    (root / relative).write_text(json.dumps(data))
    rebind(root, relative)

    with pytest.raises(ProvenanceError, match=message):
        verify_manuscript(root)


@pytest.mark.integration
@pytest.mark.parametrize("edition, error, message", [
    ("html", ProvenanceError, "HTML requires all canonical image references"),
    ("docx", OfficePagePolicyError, "File is not a zip file"),
    ("pdf", subprocess.CalledProcessError, "pdfinfo"),
])
def test_rebound_empty_editions_are_rejected_by_actual_parsers(
    manuscript_copy, edition, error, message,
):
    root = manuscript_copy
    receipt = json.loads((root / "output/manuscript/render-receipt.json").read_text())
    relative = receipt["editions"][edition]
    (root / relative).write_bytes(b"")
    rebind(root, relative)
    with pytest.raises(error, match=message) as caught:
        verify_manuscript(root)
    if edition == "docx":
        assert isinstance(caught.value.__cause__, BadZipFile)


@pytest.mark.integration
@pytest.mark.parametrize("relative", [
    "manuscript/references.bib", "output/analytics.json", "manuscript/rikishi.md",
    "output/data/corpus.json",
])
def test_verifier_rejects_stale_authored_inputs(manuscript_copy, relative):
    target = manuscript_copy / relative
    target.write_bytes(target.read_bytes() + b"\nchanged-input\n")
    with pytest.raises(ProvenanceError, match="Changed manuscript input"):
        verify_manuscript(manuscript_copy)


@pytest.mark.integration
@pytest.mark.parametrize("relative", [
    "config/manuscript.yaml", "config/references.csl", "pyproject.toml",
    "output/formalization/verification.json",
])
def test_verifier_rejects_stale_publication_inputs(manuscript_copy, relative):
    target = manuscript_copy / relative
    target.write_bytes(target.read_bytes() + b"\nchanged-input\n")
    with pytest.raises(ProvenanceError, match="Publication input changed"):
        verify_manuscript(manuscript_copy)


@pytest.mark.integration
@pytest.mark.parametrize("name", FIGURES)
@pytest.mark.parametrize("mutation", ["replace", "replace-rebound", "drop-record", "reference-rebound"])
def test_verifier_rejects_wrong_web_figures(manuscript_copy, name, mutation):
    root = manuscript_copy
    receipt_path = root / "output/manuscript/render-receipt.json"
    receipt = json.loads(receipt_path.read_text())
    relative = f"output/web/figures/{name}"
    target = root / relative
    match mutation:
        case "replace" | "replace-rebound":
            wrong = "corpus-files.png" if name != "corpus-files.png" else "fep-free-energy.png"
            target.write_bytes((root / "output/manuscript/figures" / wrong).read_bytes())
            message = "Artifact size differs|Artifact hash differs"
            if mutation == "replace-rebound":
                message = ("Mixed-sequence atlas evidence copy differs" if name == "witness-sequences.png"
                           else "Bridge figure evidence copy differs" if name.startswith("bridge-")
                           else "Witness research evidence copy differs" if name.startswith("witness-")
                           else "HTML figure differs")
        case "drop-record":
            receipt["artifacts"] = [r for r in receipt["artifacts"] if r["path"] != relative]
            message = ("Required artifact records missing" if name in {
                "research-controls.png", "ontology-structure.png",
                "bridge-evidence.png", "bridge-free-energy.png", "bridge-native-controls.png",
                "witness-channels.png", "witness-evidence-scaling.png", "witness-sequential.png",
                "witness-sequences.png"}
                       else "Unrecorded HTML figure")
        case "reference-rebound":
            relative = "output/web/index.html"
            target = root / relative
            target.write_text(target.read_text().replace(f"figures/{name}", "figures/missing.png"))
            message = "Unexpected HTML image reference"
        case _:
            pytest.fail(f"Unknown mutation: {mutation}")
    receipt_path.write_text(json.dumps(receipt))
    if mutation.endswith("rebound"):
        rebind(root, relative)
    with pytest.raises(ProvenanceError, match=message):
        verify_manuscript(root)


@pytest.mark.integration
@pytest.mark.parametrize("name", FIGURES)
def test_verifier_rejects_rebound_pdf_figure_copies(manuscript_copy, name):
    relative = f"output/figures/{name}"
    (manuscript_copy / relative).write_bytes(
        (manuscript_copy / "output/manuscript/figures" / (
            "corpus-files.png" if name != "corpus-files.png" else "fep-free-energy.png"
        )).read_bytes()
    )
    rebind(manuscript_copy, relative)
    with pytest.raises(ProvenanceError, match="PDF figure copy differs"):
        verify_manuscript(manuscript_copy)


@pytest.mark.integration
@pytest.mark.parametrize("name", ["corpus-files.png", "corpus-composition.png"])
def test_verifier_rejects_changed_report_image_source(manuscript_copy, name):
    target = manuscript_copy / "output" / name
    target.write_bytes(target.read_bytes() + b"changed")
    with pytest.raises(ProvenanceError, match="Report input changed"):
        verify_manuscript(manuscript_copy)


@pytest.mark.integration
@pytest.mark.parametrize("name, message", [
    ("rikishi-body.md", "Hydrated body differs"),
    ("rikishi.md", "Projection differs"),
    ("rikishi-office-web.md", "Projection differs"),
    ("references.bib", "Staged bibliography differs"),
    ("config.yaml", "Staged configuration differs"),
    ("fep-example.json", "Numerical example differs"),
])
def test_rebound_staged_publication_is_recomputed(manuscript_copy, name, message):
    relative = f"output/manuscript/{name}"
    target = manuscript_copy / relative
    match name:
        case "config.yaml":
            target.write_text(target.read_text().replace("Rikishi", "Altered title"))
        case "fep-example.json":
            data = json.loads(target.read_text())
            data["result"]["free_energy"] += 1
            target.write_text(json.dumps(data))
        case _:
            target.write_text(target.read_text() + "\nAltered projection.\n")
    rebind(manuscript_copy, relative)
    with pytest.raises(ProvenanceError, match=message):
        verify_manuscript(manuscript_copy)


@pytest.mark.integration
@pytest.mark.parametrize("name", ["rikishi.md", "rikishi-office-web.md"])
def test_rebound_staged_publication_rejects_removed_reading_policy(manuscript_copy, name):
    relative = f"output/manuscript/{name}"
    target = manuscript_copy / relative
    _, header, body = target.read_text().split("---\n", 2)
    metadata = yaml.safe_load(header)
    assert metadata.pop("header-includes")
    target.write_text("---\n" + yaml.safe_dump(metadata, sort_keys=False) + "---\n" + body)
    rebind(manuscript_copy, relative)
    with pytest.raises(ProvenanceError, match="Projection differs"):
        verify_manuscript(manuscript_copy)


@pytest.mark.integration
def test_rebound_native_log_rejects_tex_errors(manuscript_copy):
    relative = "output/pdf/_combined_manuscript.log"
    path = manuscript_copy / relative
    path.write_bytes(path.read_bytes() + b"\n! LaTeX Error: There's no line here to end.\n")
    rebind(manuscript_copy, relative)
    with pytest.raises(ProvenanceError, match="compilation contains TeX errors"):
        verify_manuscript(manuscript_copy)


@pytest.mark.integration
@pytest.mark.parametrize("key, value, message", [
    ("substitutions", {}, "Substitutions differ"),
    ("numerical_result", {}, "Numerical example differs"),
    ("editions", {}, "Edition paths differ"),
    ("report_inputs", {}, "Report input manifest differs"),
    ("publication_inputs", {}, "Publication input manifest"),
    ("research_inputs", {}, "Research inputs differ"),
    ("ontology_structure_sha256", "0" * 64, "Ontology structure report changed"),
    ("template_revision", "0" * 40, "Renderer revision differs"),
])
def test_verifier_recomputes_receipt_claims(manuscript_copy, key, value, message):
    path = manuscript_copy / "output/manuscript/render-receipt.json"
    receipt = json.loads(path.read_text())
    receipt[key] = value
    path.write_text(json.dumps(receipt))
    with pytest.raises(ProvenanceError, match=message):
        verify_manuscript(manuscript_copy)


@pytest.mark.integration
def test_source_inventory_recomputed_from_actual_pandoc_ast(manuscript_copy):
    path = manuscript_copy / "output/manuscript/render-receipt.json"
    receipt = json.loads(path.read_text())
    receipt["source_checks"]["citation_occurrences"] += 1
    path.write_text(json.dumps(receipt))
    with pytest.raises(ProvenanceError, match="Source checks differ from actual Pandoc AST"):
        verify_manuscript(manuscript_copy)


@pytest.mark.integration
@pytest.mark.parametrize("old, new, message", [
    ("Daniel Ari Friedman", "An altered author", "HTML publication text missing"),
    ("Active Inference Institute", "An altered affiliation", "HTML publication text missing"),
    ("0000-0001-6232-9096", "0000-0001-0000-0000", "HTML publication text missing"),
    ('data-number="1" id="sec:sumo"', 'data-number="8" id="sec:sumo"', "HTML section numbering"),
    ('id="ref-niles2001sumo"', 'id="missing-reference"', "Unresolved HTML link"),
    ("Definition 1 (", "Definition 8 (", "HTML formalism number"),
    ('href="#eq:finite-model">', 'href="#eq:finite-model">999', "HTML reference numbering"),
    (r"Z=p(o)=", r"Z=0=", "HTML equation content differs"),
    (r"\qquad", r"\qquad {{UNRESOLVED}}", "Unresolved citation or placeholder"),
])
def test_rebound_html_semantics_reject(manuscript_copy, old, new, message):
    relative = "output/web/index.html"
    target = manuscript_copy / relative
    source = target.read_text()
    assert old in source
    target.write_text(source.replace(old, new))
    rebind(manuscript_copy, relative)
    with pytest.raises(ProvenanceError, match=message):
        verify_manuscript(manuscript_copy)


@pytest.mark.integration
@pytest.mark.parametrize("name", FIGURES)
def test_docx_uses_all_canonical_media(manuscript_copy, name):
    canonical = (manuscript_copy / "output/manuscript/figures" / name).read_bytes()
    path = manuscript_copy / "output/docx/rikishi.docx"
    with ZipFile(path) as archive:
        target = next(n for n in archive.namelist() if n.startswith("word/media/")
                      and archive.read(n) == canonical)
    rewrite_native_docx(manuscript_copy, target, lambda data: data + b"altered")
    with pytest.raises(ProvenanceError, match="DOCX canonical image missing"):
        verify_manuscript(manuscript_copy)


@pytest.mark.integration
@pytest.mark.parametrize("mutation, error, message", [
    ("break", ProvenanceError, "DOCX cover page break"),
    ("author", ProvenanceError, "DOCX publication text missing"),
    ("math", OfficeContentError, "Repaired math structures changed"),
    ("drawing", ProvenanceError, "DOCX requires all canonical image drawings"),
])
def test_rebound_docx_structure_rejects(manuscript_copy, mutation, error, message):
    def alter(data):
        match mutation:
            case "break":
                changed = re.sub(rb'<w:br w:type="page"\s*/>', b"", data)
            case "author":
                changed = data.replace(b"Daniel Ari Friedman", b"Altered author")
            case "math":
                changed = re.sub(rb"<m:t(?:\s[^>]*)?>[A-Za-z]+</m:t>", b"<m:t>0</m:t>", data)
            case "drawing":
                changed = re.sub(rb"<a:blip\b[^>]*/>", b"", data, count=1)
            case _:
                pytest.fail(f"Unknown DOCX mutation: {mutation}")
        assert changed != data
        return changed
    rewrite_native_docx(manuscript_copy, "word/document.xml", alter)
    with pytest.raises(error, match=message):
        verify_manuscript(manuscript_copy)


@pytest.mark.integration
def test_missing_edition_fails_even_with_python_assertions_disabled(manuscript_copy):
    (manuscript_copy / "output/pdf/rikishi_combined.pdf").unlink()
    command = (
        "from pathlib import Path; from rikishi.manuscript_verification import verify_manuscript; "
        f"verify_manuscript(Path({str(manuscript_copy)!r}))"
    )
    result = subprocess.run([sys.executable, "-O", "-c", command], check=False,
                            capture_output=True, text=True, env=os.environ.copy(), timeout=30)
    assert result.returncode != 0
    assert "Missing regular artifact" in result.stderr


@pytest.mark.integration
def test_changed_sumo_demonstration_receipt_is_rejected(manuscript_copy):
    path = manuscript_copy / "output/manuscript/sumo-demonstrations.json"
    path.write_bytes(path.read_bytes() + b"\n")
    rebind(manuscript_copy, "output/manuscript/sumo-demonstrations.json")
    with pytest.raises(ProvenanceError, match="SUMO demonstration report changed"):
        verify_manuscript(manuscript_copy)


@pytest.mark.integration
@pytest.mark.parametrize("mutation", ["source_bytes", "revision", "observations"])
def test_rebound_sumo_demonstration_must_replay(manuscript_copy, mutation):
    relative = "output/manuscript/sumo-demonstrations.json"
    path = manuscript_copy / relative
    data = json.loads(path.read_text())
    match mutation:
        case "source_bytes":
            data["source"]["text"] += "\n(instance TamperedExample Entity)\n"
        case "revision":
            data["source"]["commit"] = "0" * 40
        case "observations":
            data["observations"] = {}
    path.write_text(json.dumps(data))
    rebind(manuscript_copy, relative)
    receipt_path = manuscript_copy / "output/manuscript/render-receipt.json"
    receipt = json.loads(receipt_path.read_text())
    receipt["sumo_demonstrations_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    receipt_path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError):
        verify_manuscript(manuscript_copy)


@pytest.mark.integration
def test_rebound_html_must_contain_injected_sumo_formula(manuscript_copy):
    relative = "output/web/index.html"
    path = manuscript_copy / relative
    original = path.read_text()
    changed = re.sub(
        r"(<pre\b[^>]*>)(.*?)(</pre>)",
        lambda match: match[1] + match[2].replace("Process", "WrongProcess") + match[3],
        original, flags=re.DOTALL,
    )
    assert changed != original
    path.write_text(changed)
    rebind(manuscript_copy, relative)
    with pytest.raises(ProvenanceError, match="SUMO source formula missing: HTML"):
        verify_manuscript(manuscript_copy)


@pytest.mark.integration
@pytest.mark.parametrize("family", ["e", "v"])
def test_rebound_research_report_requires_original_input_hash(manuscript_copy, family):
    relative = f"output/manuscript/research/{family}/alignment-report.json"
    path = manuscript_copy / relative
    path.write_bytes(path.read_bytes() + b"\n")
    rebind(manuscript_copy, relative)
    with pytest.raises(ProvenanceError, match="Research inputs differ"):
        verify_manuscript(manuscript_copy)


@pytest.mark.integration
def test_rebound_research_pair_requires_distinct_families(manuscript_copy):
    root = manuscript_copy
    shutil.copytree(root / "output/manuscript/research/e",
                    root / "output/manuscript/research/v", dirs_exist_ok=True)
    receipt_path = root / "output/manuscript/render-receipt.json"
    receipt = json.loads(receipt_path.read_text())
    for record in receipt["artifacts"]:
        if record["path"].startswith("output/manuscript/research/v/"):
            target = root / record["path"]
            record.update(bytes=target.stat().st_size,
                          sha256=hashlib.sha256(target.read_bytes()).hexdigest())
    receipt["research_inputs"]["v/alignment-report.json"] = hashlib.sha256(
        (root / "output/manuscript/research/v/alignment-report.json").read_bytes()).hexdigest()
    receipt_path.write_text(json.dumps(receipt))
    with pytest.raises(ProvenanceError, match="Research prover families differ"):
        verify_manuscript(root)


@pytest.mark.integration
def test_research_substitutions_are_recomputed(manuscript_copy):
    path = manuscript_copy / "output/manuscript/render-receipt.json"
    receipt = json.loads(path.read_text())
    keys = [key for key in receipt["substitutions"] if key.startswith("ALIGNMENT_")]
    assert keys
    for key in keys:
        receipt["substitutions"][key] = "altered research value"
    path.write_text(json.dumps(receipt))
    with pytest.raises(ProvenanceError, match="Substitutions differ"):
        verify_manuscript(manuscript_copy)


@pytest.mark.integration
@pytest.mark.parametrize("edition", ["html", "docx"])
def test_rebound_editions_require_actual_research_results(manuscript_copy, edition):
    root = manuscript_copy
    data = json.loads((root / "output/manuscript/research/e/alignment-report.json").read_text())
    identifier = data["logical"][0]["id"]
    match edition:
        case "html":
            relative = "output/web/index.html"
            path = root / relative
            original = path.read_text()
            assert identifier in original
            path.write_text(original.replace(identifier, "altered-research-result"))
            rebind(root, relative)
        case "docx":
            def alter(content):
                assert identifier.encode() in content
                return content.replace(identifier.encode(), b"altered-research-result")
            rewrite_native_docx(root, "word/document.xml", alter)
    with pytest.raises(ProvenanceError, match=f"Research result row missing: {edition.upper()}"):
        verify_manuscript(root)


@pytest.mark.integration
@pytest.mark.parametrize("token", ["ALIGNMENT_LOGICAL_TABLE", "ALIGNMENT_NUMERICAL_TABLE"])
def test_actual_pdf_research_table_cells_are_checked(manuscript_copy, token):
    root = manuscript_copy
    figure = json.loads((root / "output/manuscript/figures/research-controls.json").read_text())
    research = load_research_context(root / "output/manuscript/research",
                                     decimal_places=figure["decimal_places"])
    result = subprocess.run(["pdftotext", "-layout", str(root / "output/pdf/rikishi_combined.pdf"), "-"],
                            check=True, capture_output=True, text=True)
    lines = result.stdout.splitlines()
    header = "".join(research.values[token].splitlines()[0].replace("|", "").split())
    index = next(i for i, line in enumerate(lines) if "".join(line.split()) == header)
    row = next(i for i in range(index + 1, len(lines)) if lines[i].strip())
    original = lines[row]
    lines[row] = re.sub(r"\S+", "altered-research-cell", original, count=1)
    assert lines[row] != original
    with pytest.raises(ProvenanceError, match="Research result row missing: PDF"):
        _research_pdf_tables("\n".join(lines), research)


@pytest.mark.integration
@pytest.mark.parametrize("family", ["e", "v", "fresh-cache"])
def test_complete_research_tree_must_be_recorded(manuscript_copy, family):
    path = manuscript_copy / "output/manuscript/render-receipt.json"
    receipt = json.loads(path.read_text())
    selected = next(record for record in receipt["artifacts"]
                    if record["path"].startswith(f"output/manuscript/research/{family}/")
                    and not record["path"].endswith("alignment-report.json"))
    receipt["artifacts"].remove(selected)
    path.write_text(json.dumps(receipt))
    with pytest.raises(ProvenanceError, match="Required artifact records missing"):
        verify_manuscript(manuscript_copy)


@pytest.mark.integration
@pytest.mark.parametrize("mutation, message", [
    ("report", "Research figure reports differ"),
    ("ratio", "Research figure numerical row differs"),
    ("aggregate", "Research figure aggregate differs"),
    ("policy", "Research figure presentation differs"),
    ("scale", "Research figure scale or scope differs"),
    ("provenance", "Research figure complete provenance differs"),
])
def test_rebound_research_figure_data_is_recomputed(manuscript_copy, mutation, message):
    root = manuscript_copy
    name = "research-controls.json"
    data = json.loads((root / "output/manuscript/figures" / name).read_text())
    match mutation:
        case "report":
            data["reports"][0]["report"]["summary"]["logical_matched"] += 1
        case "ratio":
            data["numerical_rows"][0]["ratios"]["reference"] += 1
        case "aggregate":
            data["aggregates"][0]["rows"] += 1
        case "policy":
            data["decimal_places"] += 1
        case "scale":
            data["ratio_threshold"] += 1
        case "provenance":
            data["provenance"] = []
    for directory in ("output/manuscript/figures", "output/figures", "output/web/figures"):
        relative = f"{directory}/{name}"
        (root / relative).write_text(json.dumps(data))
        rebind(root, relative)
    with pytest.raises(ProvenanceError, match=message):
        verify_manuscript(root)


@pytest.mark.integration
@pytest.mark.parametrize("field, value", [
    ("status", "failed"), ("freshcache_scope", "none"),
    ("semantic_validation", True), ("bindings_stable", False),
])
def test_rebound_fresh_cache_claims_are_checked(manuscript_copy, field, value):
    relative = "output/manuscript/research/fresh-cache/result.json"
    path = manuscript_copy / relative
    data = json.loads(path.read_text())
    data[field] = value
    path.write_text(json.dumps(data))
    rebind(manuscript_copy, relative)
    with pytest.raises(ProvenanceError, match="Fresh-cache experiment"):
        verify_manuscript(manuscript_copy)


@pytest.mark.integration
@pytest.mark.parametrize("mutation", ["count", "source", "revision", "path", "inventory"])
def test_rebound_ontology_report_is_recomputed(manuscript_copy, mutation):
    root = manuscript_copy
    relative = "output/manuscript/ontology-structure.json"
    path = root / relative
    data = json.loads(path.read_text())
    match mutation:
        case "count":
            data["graphs"][0]["unique_edges"] += 1
        case "source":
            data["source_sha256"] = "0" * 64
        case "revision":
            data["source_commit"] = "0" * 40
        case "path":
            data["ontology_path"] = "Other.kif"
        case "inventory":
            data["graphs"].reverse()
    path.write_text(json.dumps(data))
    rebind(root, relative)
    receipt_path = root / "output/manuscript/render-receipt.json"
    receipt = json.loads(receipt_path.read_text())
    receipt["ontology_structure_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    receipt_path.write_text(json.dumps(receipt))
    with pytest.raises(ProvenanceError, match="Ontology structure report differs from retained source"):
        verify_manuscript(root)


@pytest.mark.integration
@pytest.mark.parametrize("mutation, message", [
    ("count", "Ontology figure report differs from retained source"),
    ("source", "Ontology figure report differs from retained source"),
    ("dpi", "Ontology figure presentation differs from publication policy"),
    ("width_mm", "Ontology figure presentation differs from publication policy"),
    ("height_mm", "Ontology figure presentation differs from publication policy"),
])
def test_rebound_ontology_figure_json_is_recomputed(manuscript_copy, mutation, message):
    root = manuscript_copy
    data = json.loads((root / "output/manuscript/figures/ontology-structure.json").read_text())
    match mutation:
        case "count":
            data["report"]["graphs"][1]["root_count"] += 1
        case "source":
            data["report"]["source_sha256"] = "0" * 64
        case _:
            data["rendering"][mutation] += 1
    for directory in ("output/manuscript/figures", "output/figures", "output/web/figures"):
        relative = f"{directory}/ontology-structure.json"
        (root / relative).write_text(json.dumps(data))
        rebind(root, relative)
    with pytest.raises(ProvenanceError, match=message):
        verify_manuscript(root)


@pytest.mark.integration
@pytest.mark.parametrize("directory", ["output/figures", "output/web/figures"])
@pytest.mark.parametrize("suffix", ["svg", "json"])
def test_rebound_ontology_asset_copies_must_match(manuscript_copy, directory, suffix):
    relative = f"{directory}/ontology-structure.{suffix}"
    path = manuscript_copy / relative
    path.write_bytes(path.read_bytes() + b"\n")
    rebind(manuscript_copy, relative)
    with pytest.raises(ProvenanceError, match="Ontology asset copy differs"):
        verify_manuscript(manuscript_copy)


@pytest.mark.integration
@pytest.mark.parametrize("relative", [
    "output/manuscript/ontology-structure.json",
    *(f"{directory}/ontology-structure.{suffix}"
      for directory in ("output/manuscript/figures", "output/figures", "output/web/figures")
      for suffix in ("png", "svg", "json")),
])
def test_all_ontology_assets_require_artifact_records(manuscript_copy, relative):
    path = manuscript_copy / "output/manuscript/render-receipt.json"
    receipt = json.loads(path.read_text())
    receipt["artifacts"] = [record for record in receipt["artifacts"] if record["path"] != relative]
    path.write_text(json.dumps(receipt))
    with pytest.raises(ProvenanceError, match="Required artifact records missing"):
        verify_manuscript(manuscript_copy)


@pytest.mark.integration
@pytest.mark.parametrize("mutation, message", [
    ("description", "Ontology PNG report provenance differs"),
    ("dimensions", "Ontology PNG dimensions differ from publication policy"),
])
def test_rebound_ontology_png_metadata_is_checked(manuscript_copy, mutation, message):
    path = manuscript_copy / "output/manuscript/figures/ontology-structure.png"
    with Image.open(path) as original:
        image = original.copy()
        description = original.info["Description"]
    if mutation == "description":
        description = "{}"
    else:
        image = image.crop((0, 0, image.width - 1, image.height))
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("Description", description)
    image.save(path, pnginfo=metadata)
    rebind(manuscript_copy, "output/manuscript/figures/ontology-structure.png")
    with pytest.raises(ProvenanceError, match=message):
        verify_manuscript(manuscript_copy)


@pytest.mark.integration
@pytest.mark.parametrize("mutation, message", [
    ("metadata", "Ontology SVG report provenance differs"),
    ("visible", "Ontology SVG vector source content differs"),
])
def test_rebound_ontology_svg_source_is_checked(manuscript_copy, mutation, message):
    root = manuscript_copy
    original = (root / "output/manuscript/figures/ontology-structure.svg").read_text()
    if mutation == "metadata":
        changed = re.sub(r"(<dc:description>).*?(</dc:description>)", r"\g<1>{}\2",
                         original, flags=re.DOTALL)
    else:
        digest = json.loads((root / "output/manuscript/ontology-structure.json").read_text())[
            "source_sha256"]
        changed = original.replace("Source SHA-256: " + digest, "Source SHA-256: " + "0" * 64)
    assert changed != original
    for directory in ("output/manuscript/figures", "output/figures", "output/web/figures"):
        relative = f"{directory}/ontology-structure.svg"
        (root / relative).write_text(changed)
        rebind(root, relative)
    with pytest.raises(ProvenanceError, match=message):
        verify_manuscript(root)


@pytest.mark.integration
def test_rebound_pdf_requires_actual_ontology_image_pixels(manuscript_copy):
    root = manuscript_copy
    path = root / "output/manuscript/figures/ontology-structure.png"
    canonical = path.read_bytes()
    with Image.open(path) as original:
        image = original.convert("RGB")
        description = original.info["Description"]
    image.putpixel((0, 0), (0, 0, 0))
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("Description", description)
    image.save(path, pnginfo=metadata)
    changed = path.read_bytes()
    assert changed != canonical
    for directory in ("output/manuscript/figures", "output/figures", "output/web/figures"):
        relative = f"{directory}/ontology-structure.png"
        (root / relative).write_bytes(changed)
        rebind(root, relative)
    with ZipFile(root / "output/docx/rikishi.docx") as archive:
        part = next(name for name in archive.namelist() if name.startswith("word/media/")
                    and archive.read(name) == canonical)
    rewrite_native_docx(root, part, lambda content: changed)
    with pytest.raises(ProvenanceError, match="PDF canonical figure missing: ontology-structure.png"):
        verify_manuscript(root)


@pytest.mark.integration
@pytest.mark.parametrize("edition", ["html", "docx"])
def test_rebound_native_editions_require_actual_ontology_table_cells(manuscript_copy, edition):
    root = manuscript_copy
    match edition:
        case "html":
            relative = "output/web/index.html"
            path = root / relative
            original = path.read_text()
            changed = re.sub(r"<tr\b[^>]*>.*?</tr>",
                             lambda row: re.sub(r">\d+<", ">999999<", row[0], count=1)
                             if ">subclass<" in row[0] else row[0], original, flags=re.DOTALL)
            assert changed != original
            path.write_text(changed)
            rebind(root, relative)
        case "docx":
            def alter(content):
                changed = re.sub(rb"<w:tr\b[^>]*>.*?</w:tr>",
                                 lambda row: re.sub(rb">\d+<", b">999999<", row[0], count=1)
                                 if b">subclass<" in row[0] else row[0], content, flags=re.DOTALL)
                assert changed != content
                return changed
            rewrite_native_docx(root, "word/document.xml", alter)
    with pytest.raises(ProvenanceError, match=f"Ontology structure row missing: {edition.upper()}"):
        verify_manuscript(root)


@pytest.mark.integration
def test_actual_pdf_ontology_table_cells_are_checked(manuscript_copy):
    root = manuscript_copy
    receipt = json.loads((root / "output/manuscript/render-receipt.json").read_text())
    result = subprocess.run(["pdftotext", "-layout", str(root / "output/pdf/rikishi_combined.pdf"), "-"],
                            check=True, capture_output=True, text=True)
    layout = result.stdout
    _ontology_pdf_table(layout, receipt["substitutions"]["ONTOLOGY_STRUCTURE_TABLE"])
    lines = layout.splitlines()
    index = next(i for i, line in enumerate(lines)
                 if len(re.split(r"\s{2,}", line.strip())) == 6 and line.strip().startswith("subclass"))
    lines[index] = re.sub(r"\b\d+\b", "999999", lines[index], count=1)
    with pytest.raises(ProvenanceError, match="Ontology structure row missing: PDF"):
        _ontology_pdf_table("\n".join(lines), receipt["substitutions"]["ONTOLOGY_STRUCTURE_TABLE"])


@pytest.mark.integration
def test_rebound_event_proof_copies_must_equal_actual_source(manuscript_copy):
    # Given actual rendered copies whose artifact digests are coherently rebound.
    root = manuscript_copy
    original = (root / "examples/EventTransport.lean").read_bytes()
    changed = original.replace(b"collapse_intersection_failure", b"changed_event_claim")
    assert changed != original
    for directory in ("output/manuscript/figures", "output/figures", "output/web/figures"):
        relative = directory + "/EventTransport.lean"
        (root / relative).write_bytes(changed)
        rebind(root, relative)
    # When the real verifier compares the actual source, then a new checksum cannot waive it.
    with pytest.raises(ProvenanceError, match="Event-transport proof source copy differs"):
        verify_manuscript(root)


_NATIVE_COPY_METHODS: Final[tuple[bool, ...]] = (False, True) if _COPY_NATIVE_APFS else (False,)


@pytest.mark.integration
@pytest.mark.parametrize("use_clone", _NATIVE_COPY_METHODS)
def test_native_fixture_copy_preserves_bytes_and_metadata(tmp_path: Path, use_clone: bool) -> None:
    # Given a real owned file with deliberately selected content and metadata.
    source, target = tmp_path / "source", tmp_path / "target"
    payload = b"fixture-content\x00\xff"
    source.write_bytes(payload)
    source.chmod(0o640)
    os.utime(source, ns=(1700000000123456789, 1700000000987654321))
    before = source.stat()

    # When the selected supported copy method creates a destination.
    _copy_native_file(source, target, use_clone=use_clone)

    # Then the copied bytes/metadata agree and the file is a separate inode.
    actual = target.stat()
    assert target.read_bytes() == payload
    assert (stat.S_IMODE(actual.st_mode), actual.st_mtime_ns) == (
        stat.S_IMODE(before.st_mode), before.st_mtime_ns)
    assert (actual.st_dev, actual.st_ino) != (before.st_dev, before.st_ino)
    assert actual.st_nlink == 1


@pytest.mark.integration
@pytest.mark.parametrize("use_clone", _NATIVE_COPY_METHODS)
@pytest.mark.parametrize("changed_side", ("source", "destination"))
def test_native_fixture_copy_writes_are_isolated(
    tmp_path: Path, use_clone: bool, changed_side: Literal["source", "destination"],
) -> None:
    # Given independently copied files and the side selected for mutation.
    source, target = tmp_path / "source", tmp_path / "target"
    payload = b"unchanged"
    source.write_bytes(payload)
    _copy_native_file(source, target, use_clone=use_clone)
    match changed_side:
        case "source":
            changed, untouched = source, target
        case "destination":
            changed, untouched = target, source
        case unreachable:
            assert_never(unreachable)

    # When one side is modified.
    changed.write_bytes(b"modified!")

    # Then the other file retains its original contents.
    assert untouched.read_bytes() == payload


@pytest.mark.integration
@pytest.mark.parametrize("use_clone", _NATIVE_COPY_METHODS)
def test_native_fixture_copy_is_create_only(tmp_path: Path, use_clone: bool) -> None:
    # Given an existing destination whose data must survive the refusal.
    source, target = tmp_path / "source", tmp_path / "target"
    source.write_bytes(b"source")
    target.write_bytes(b"protected")

    # When a copy attempts to replace that destination.
    with pytest.raises(FileExistsError) as error:
        _copy_native_file(source, target, use_clone=use_clone)

    # Then it refuses for the intended cause without changing the destination.
    assert error.value.errno == errno.EEXIST
    assert target.read_bytes() == b"protected"


@pytest.mark.integration
@pytest.mark.parametrize("use_clone", _NATIVE_COPY_METHODS)
@pytest.mark.parametrize("symbolic_input", ("source-leaf", "source-parent", "destination-parent"))
def test_native_fixture_copy_rejects_symbolic_inputs(
    tmp_path: Path, use_clone: bool,
    symbolic_input: Literal["source-leaf", "source-parent", "destination-parent"],
) -> None:
    # Given a real file and an unexpected symbolic path component.
    source, target = tmp_path / "source", tmp_path / "target"
    source.write_bytes(b"source")
    match symbolic_input:
        case "source-leaf":
            link = tmp_path / "source-link"
            link.symlink_to(source)
            source = link
        case "source-parent":
            parent = tmp_path / "source-real"
            parent.mkdir()
            source.rename(parent / "source")
            link = tmp_path / "source-parent"
            link.symlink_to(parent, target_is_directory=True)
            source = link / "source"
        case "destination-parent":
            parent = tmp_path / "target-real"
            parent.mkdir()
            link = tmp_path / "target-parent"
            link.symlink_to(parent, target_is_directory=True)
            target = link / "target"
        case unreachable:
            assert_never(unreachable)

    # When copying would traverse that symbolic input.
    with pytest.raises(OSError) as error:
        _copy_native_file(source, target, use_clone=use_clone)

    # Then the intended symbolic-path refusal occurs before a destination exists.
    assert error.value.errno == errno.ELOOP
    assert not target.exists()

"""Real package and native controls for the bounded Office geometry helper.

Programming size exception (# noqa: SIZE_OK): ownership permits one test module.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import struct
import sys
from dataclasses import asdict
from io import BytesIO
from pathlib import Path
from types import FrameType
from typing import Literal, Protocol, assert_never
from xml.etree import ElementTree
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

import pytest
from PIL import Image

from rikishi.publication_office import (
    OfficePagePolicyError,
    _ensure_new,
    _package,
    _parent_directory,
    _read_regular,
    _reference,
    _write_new,
    _written_reference,
    verify_office_page_policy,
    verify_office_reference_policy,
    write_office_reference,
)

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
GEOMETRY = ('<w:pgSz w:w="12240" w:h="15840"/>'
            '<w:pgMar w:top="680" w:right="680" w:bottom="680" w:left="680" '
            'w:header="680" w:footer="680" w:gutter="0"/>')
XML_PREFIX = ('<?xml version="1.0" encoding="utf-8"?>'
              '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
              'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" '
              'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
              '<w:body>')
CONTENT = ('<w:p><w:r><w:t>Native scientific text α</w:t></w:r>'
           '<m:oMath><m:r><m:t>x²</m:t></m:r></m:oMath>'
           '<w:hyperlink r:id="rId1"><w:r><w:t>source</w:t></w:r></w:hyperlink></w:p>')
RELATIONSHIPS = ('<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                 '<Relationship Id="rId1" '
                 'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
                 'Target="word/document.xml"/></Relationships>')
CONTENT_TYPES = ('<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                 '<Override PartName="/word/document.xml" '
                 'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                 '<Override PartName="/word/styles.xml" '
                 'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
                 '</Types>')
STYLES = (b'<?xml version="1.0" encoding="UTF-8"?>'
          b'<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
          b'<w:style w:type="paragraph" w:styleId="Normal"><w:rPr>'
          b'<w:rFonts w:ascii="Cambria"/></w:rPr></w:style>'
          b'<w:style w:type="paragraph" w:styleId="Caption"><w:basedOn w:val="Normal"/></w:style>'
          b'<w:style w:type="character" w:styleId="Hyperlink"><w:rPr>'
          b'<w:color w:val="4F81BD" w:themeColor="accent1" w:themeTint="00" w:themeShade="FF"/>'
          b'</w:rPr></w:style>'
          b'<w:style w:type="paragraph" w:styleId="ImageCaption">'
          b'<w:basedOn w:val="Caption"/></w:style>'
          b'<w:style w:type="paragraph" w:styleId="CaptionedFigure"><w:pPr>'
          b'<w:keepNext/></w:pPr></w:style></w:styles>')
STYLES_RELS = (b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
               b'<Relationship Id="rId2" Target="styles.xml" '
               b'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles"/>'
               b'</Relationships>')


def package(tmp_path: Path, section: str = GEOMETRY, *, prefix: str = XML_PREFIX) -> Path:
    output = tmp_path / "fixture.docx"
    xml = (prefix + CONTENT + "<w:sectPr>" + section + "</w:sectPr></w:body></w:document>")
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("_rels/.rels", RELATIONSHIPS)
        archive.writestr("[Content_Types].xml", CONTENT_TYPES)
        archive.writestr("word/document.xml", xml.encode())
        archive.writestr("word/styles.xml", STYLES)
        archive.writestr("word/_rels/document.xml.rels", STYLES_RELS)
        archive.writestr("word/header1.xml", b'<header>retained opaque header</header>')
        archive.writestr("word/fontTable.xml", b'<fonts>retained opaque fonts</fonts>')
        archive.writestr("word/media/image.png", b"retained-image-payload")
    return output


def replace_part(output: Path, name: str, replacement: bytes) -> None:
    with ZipFile(output) as archive:
        parts = [(row, archive.read(row)) for row in archive.infolist()]
    with ZipFile(output, "w") as archive:
        for row, payload in parts:
            archive.writestr(row, replacement if row.filename == name else payload)


def test_root_relationship_cannot_redirect_to_wrong_geometry_while_decoy_is_correct(tmp_path: Path) -> None:
    output = package(tmp_path)
    replace_part(output, "_rels/.rels", RELATIONSHIPS.replace("word/document.xml", "word/actual.xml").encode())
    replace_part(output, "[Content_Types].xml", CONTENT_TYPES.replace("</Types>",
                 CONTENT_TYPES[CONTENT_TYPES.index("<Override"):CONTENT_TYPES.index("</Types>")]
                 .replace("/word/document.xml", "/word/actual.xml") + "</Types>").encode())
    with ZipFile(output, "a") as archive:
        archive.writestr("word/actual.xml", (XML_PREFIX + CONTENT + "<w:sectPr>" +
                         GEOMETRY.replace('w:left="680"', 'w:left="1440"') +
                         "</w:sectPr></w:body></w:document>"))
    rebound_hash = hashlib.sha256(output.read_bytes()).hexdigest()
    assert len(rebound_hash) == 64
    with pytest.raises(OfficePagePolicyError, match="main-document relationship"):
        verify_office_page_policy(output, margin_mm=12)


@pytest.mark.parametrize("relationships", [
    RELATIONSHIPS.replace('Target="word/document.xml"', 'Target="word/document.xml" TargetMode="External"'),
    RELATIONSHIPS.replace("word/document.xml", "word/%64ocument.xml"),
    RELATIONSHIPS.replace("word/document.xml", "/word/document.xml"),
    RELATIONSHIPS.replace("officeDocument\"", "somethingElse\""),
    RELATIONSHIPS.replace("</Relationships>", RELATIONSHIPS[RELATIONSHIPS.index("<Relationship Id="):]),
    "<Relationships/>",
])
def test_root_main_part_must_be_unique_internal_and_unambiguous(tmp_path: Path, relationships: str) -> None:
    output = package(tmp_path)
    replace_part(output, "_rels/.rels", relationships.encode())
    with pytest.raises(OfficePagePolicyError):
        verify_office_page_policy(output, margin_mm=12)


@pytest.mark.parametrize("types", ["<Types/>", CONTENT_TYPES.replace(".document.main+xml", ".template.main+xml"),
                                   CONTENT_TYPES.replace("/word/document.xml", "/word/other.xml")])
def test_root_document_content_type_is_required(tmp_path: Path, types: str) -> None:
    output = package(tmp_path)
    replace_part(output, "[Content_Types].xml", types.encode())
    with pytest.raises(OfficePagePolicyError, match="content type"):
        verify_office_page_policy(output, margin_mm=12)


def test_directory_swap_keeps_creations_in_the_pinned_parent(tmp_path: Path) -> None:
    selected, retained, other = tmp_path / "selected", tmp_path / "retained", tmp_path / "other"
    selected.mkdir()
    other.mkdir()
    (selected / "input").write_bytes(b"selected")
    (other / "input").write_bytes(b"redirected")
    with _parent_directory(selected / "output") as directory:
        selected.rename(retained)
        selected.symlink_to(other, target_is_directory=True)
        _ensure_new(directory, ("output", "native-default"))
        _write_new(directory, "output", b"actual output")
        _write_new(directory, "native-default", b"actual default")
        descriptor = os.open("input", os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory)
        with os.fdopen(descriptor, "rb") as handle:
            assert handle.read() == b"selected"
    assert (retained / "output").read_bytes() == b"actual output"
    assert (retained / "native-default").read_bytes() == b"actual default"
    assert sorted(path.name for path in other.iterdir()) == ["input"]
    with pytest.raises(OfficePagePolicyError, match="Symlink"):
        _read_regular(selected / "input", 100)


def test_descriptor_creation_never_follows_an_occupied_leaf(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.write_bytes(b"retained")
    (tmp_path / "symlink").symlink_to(target)
    with _parent_directory(tmp_path / "new") as directory:
        with pytest.raises(FileExistsError):
            _ensure_new(directory, ("new", "symlink"))
        with pytest.raises(FileExistsError):
            _write_new(directory, "symlink", b"overwritten")
    assert target.read_bytes() == b"retained"
    assert not (tmp_path / "new").exists()


def test_regular_file_admission_rejects_fifo_without_blocking_and_sparse_oversize(tmp_path: Path) -> None:
    fifo = tmp_path / "fifo"
    os.mkfifo(fifo)
    with pytest.raises(OfficePagePolicyError, match="nonregular"):
        _read_regular(fifo, 100)
    sparse = tmp_path / "sparse"
    with sparse.open("xb") as handle:
        handle.truncate(64 * 1024 * 1024 + 1)
    with pytest.raises(OfficePagePolicyError, match="Oversized"):
        verify_office_page_policy(sparse, margin_mm=12)


def test_actual_geometry_has_letter_size_nearest_twip_margins_and_digest(tmp_path: Path) -> None:
    output = package(tmp_path)
    report = verify_office_page_policy(output, margin_mm=12)
    assert report.margin_twips == 680
    assert abs(report.margin_twips * 25.4 / 1440 - 12) < 0.01
    assert report.page_width_twips == 12240
    assert report.page_height_twips == 15840
    assert report.section_count == 1
    assert report.docx_sha256 == hashlib.sha256(output.read_bytes()).hexdigest()


@pytest.mark.parametrize("section", [
    "", '<w:pgSz w:w="12240" w:h="15840"/>',
    GEOMETRY.replace('w:left="680"', 'w:left="1440"'),
    GEOMETRY.replace('w:right="680"', 'w:right="679"'),
    GEOMETRY.replace('w:top="680"', 'w:top="681"'),
    GEOMETRY.replace('w:bottom="680"', 'w:bottom="-680"'),
    GEOMETRY.replace('w:w="12240"', 'w:w="11906"'),
    GEOMETRY.replace('w:h="15840"', 'w:h="16838"'),
    GEOMETRY.replace('w:h="15840"', 'w:h="15840" w:orient="landscape"'),
    GEOMETRY.replace('w:gutter="0"', 'w:gutter="20"'),
    GEOMETRY.replace('w:header="680"', 'w:header="681"'),
    GEOMETRY.replace('w:footer="680"', ''),
    GEOMETRY + '<w:pgMar w:top="680"/>',
    GEOMETRY + '<w:cols w:num="2"/>',
    GEOMETRY + '<w:cols><w:col w:w="3000"/></w:cols>',
    GEOMETRY + '<w:cols/><w:cols/>',
    GEOMETRY + '<w:sectPrChange/>',
    GEOMETRY + '<w:unknown/>',
])
def test_rebound_hash_cannot_authorize_wrong_or_implicit_geometry(tmp_path: Path, section: str) -> None:
    output = package(tmp_path, section)
    rebound_receipt = json.loads(json.dumps({"docx_sha256": hashlib.sha256(output.read_bytes()).hexdigest()}))
    assert rebound_receipt["docx_sha256"] == hashlib.sha256(output.read_bytes()).hexdigest()
    with pytest.raises(OfficePagePolicyError):
        verify_office_page_policy(output, margin_mm=12)


def test_every_real_section_is_checked_and_section_count_is_retained(tmp_path: Path) -> None:
    prefix = XML_PREFIX + '<w:p><w:pPr><w:sectPr>' + GEOMETRY + '</w:sectPr></w:pPr></w:p>'
    output = package(tmp_path, prefix=prefix)
    assert verify_office_page_policy(output, margin_mm=12).section_count == 2
    output = package(tmp_path, prefix=prefix.replace('w:left="680"', 'w:left="1440"'))
    with pytest.raises(OfficePagePolicyError):
        verify_office_page_policy(output, margin_mm=12)


@pytest.mark.parametrize("section", [
    GEOMETRY[GEOMETRY.index("<w:pgMar"):] + GEOMETRY[:GEOMETRY.index("<w:pgMar")],
    '<w:docGrid/>' + GEOMETRY,
])
def test_schema_order_is_required(tmp_path: Path, section: str) -> None:
    with pytest.raises(OfficePagePolicyError, match="schema order"):
        verify_office_page_policy(package(tmp_path, section), margin_mm=12)


@pytest.mark.parametrize("prefix", [
    XML_PREFIX.replace("<w:body>", ""),
    XML_PREFIX + "<w:sectPr/>",
    XML_PREFIX + "<w:p><w:sectPr/></w:p>",
    XML_PREFIX + '<w:p><w:pPr><w:sectPr><w:sectPrChange><w:sectPr/></w:sectPrChange></w:sectPr></w:pPr></w:p>',
])
def test_noncurrent_or_malformed_sections_are_rejected(tmp_path: Path, prefix: str) -> None:
    with pytest.raises(OfficePagePolicyError):
        verify_office_page_policy(package(tmp_path, prefix=prefix), margin_mm=12)


@pytest.mark.parametrize("name", [
    "word/document.xml", "WORD/document.xml", "../outside", "/outside", "word/../outside",
    "word/./other", "word//other", "word\\other", "C:other", "word/document.xml/",
])
def test_ambiguous_or_unsafe_zip_members_are_rejected(tmp_path: Path, name: str) -> None:
    output = package(tmp_path)
    with ZipFile(output, "a") as archive:
        if name == "word/document.xml":
            with pytest.warns(UserWarning):
                archive.writestr(name, b"other")
        else:
            archive.writestr(name, b"other")
    with pytest.raises(OfficePagePolicyError, match="Unsafe or duplicate"):
        verify_office_page_policy(output, margin_mm=12)


@pytest.mark.parametrize("mode", [stat.S_IFLNK, stat.S_IFIFO, stat.S_IFSOCK, stat.S_IFDIR])
def test_zip_nonregular_members_are_rejected(tmp_path: Path, mode: int) -> None:
    output = package(tmp_path)
    row = ZipInfo("word/unsafe")
    row.create_system = 3
    row.external_attr = (mode | 0o600) << 16
    with ZipFile(output, "a") as archive:
        archive.writestr(row, b"external-target")
    with pytest.raises(OfficePagePolicyError, match="Unsafe or duplicate"):
        verify_office_page_policy(output, margin_mm=12)


def test_archive_budget_and_dtds_are_rejected(tmp_path: Path) -> None:
    output = tmp_path / "budget.docx"
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        for number in range(4097):
            archive.writestr(f"entry-{number}", b"")
    with pytest.raises(OfficePagePolicyError, match="archive budget"):
        verify_office_page_policy(output, margin_mm=12)
    prefix = XML_PREFIX.replace('<?xml version="1.0" encoding="utf-8"?>',
                                '<!DOCTYPE document [<!ENTITY bad "unsafe">]>')
    with pytest.raises(OfficePagePolicyError, match="Unsafe or malformed"):
        verify_office_page_policy(package(tmp_path, prefix=prefix), margin_mm=12)


def test_corrupt_missing_xml_and_symlink_paths_are_rejected(tmp_path: Path) -> None:
    output = tmp_path / "bad.docx"
    output.write_bytes(b"not a ZIP")
    with pytest.raises(OfficePagePolicyError, match="Unreadable DOCX"):
        verify_office_page_policy(output, margin_mm=12)
    with ZipFile(output, "w") as archive:
        archive.writestr("other.xml", b"<other/>")
    with pytest.raises(OfficePagePolicyError, match="word/document.xml"):
        verify_office_page_policy(output, margin_mm=12)
    regular = package(tmp_path)
    link = tmp_path / "linked.docx"
    link.symlink_to(regular)
    with pytest.raises(OfficePagePolicyError, match="Symlink"):
        verify_office_page_policy(link, margin_mm=12)
    directory_link = tmp_path / "linked-directory"
    directory_link.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(OfficePagePolicyError, match="Symlink"):
        verify_office_page_policy(directory_link / regular.name, margin_mm=12)


@pytest.mark.parametrize("margin,width,height", [
    (0, 215.9, 279.4), (-12, 215.9, 279.4), (float("nan"), 215.9, 279.4),
    (float("inf"), 215.9, 279.4), (12, 0, 279.4), (12, 215.9, 0),
    (120, 215.9, 279.4), (12, 279.4, 215.9), (12, 600, 700), (0.001, 215.9, 279.4),
])
def test_impossible_policy_does_not_create_reference(
    tmp_path: Path, margin: float, width: float, height: float,
) -> None:
    output = tmp_path / "reference.docx"
    with pytest.raises(OfficePagePolicyError):
        write_office_reference(output, margin_mm=margin, page_width_mm=width, page_height_mm=height)
    assert not output.exists()


def test_reference_refuses_occupied_output_missing_parent_and_missing_tool(tmp_path: Path) -> None:
    output = tmp_path / "reference.docx"
    output.write_bytes(b"owned existing data")
    with pytest.raises(FileExistsError):
        write_office_reference(output, margin_mm=12)
    assert output.read_bytes() == b"owned existing data"
    with pytest.raises(OfficePagePolicyError, match="existing regular parent"):
        write_office_reference(tmp_path / "absent" / "new.docx", margin_mm=12)
    with pytest.raises(OfficePagePolicyError, match="unavailable"):
        write_office_reference(tmp_path / "new.docx", margin_mm=12,
                               pandoc_path=str(tmp_path / "no-such-pandoc"))


def test_occupied_native_sidecar_is_preserved_before_either_write(tmp_path: Path) -> None:
    output = tmp_path / "reference.docx"
    sidecar = tmp_path / "reference.native-default.docx"
    sidecar.write_bytes(b"another owner's retained native bytes")
    with pytest.raises(FileExistsError):
        write_office_reference(output, margin_mm=12)
    assert not output.exists()
    assert sidecar.read_bytes() == b"another owner's retained native bytes"


def test_reference_refuses_symlink_output_and_parent(tmp_path: Path) -> None:
    occupied = tmp_path / "occupied"
    occupied.write_bytes(b"retained")
    link = tmp_path / "reference.docx"
    link.symlink_to(occupied)
    with pytest.raises(OfficePagePolicyError, match="Symlink"):
        write_office_reference(link, margin_mm=12)
    directory = tmp_path / "directory-link"
    directory.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(OfficePagePolicyError, match="Symlink"):
        write_office_reference(directory / "new.docx", margin_mm=12)
    assert occupied.read_bytes() == b"retained"


def test_real_subprocess_failure_keeps_output_absent(tmp_path: Path) -> None:
    with pytest.raises(OfficePagePolicyError, match="command failed"):
        write_office_reference(tmp_path / "reference.docx", margin_mm=12, pandoc_path="false")
    assert not list(tmp_path.iterdir())


class _TraceArgument(Protocol):
    def __repr__(self) -> str: ...


@pytest.mark.integration
@pytest.mark.parametrize("changed_artifact", ["reference", "default"])
def test_public_write_refuses_regular_directory_replacement_before_receipt(
    tmp_path: Path, changed_artifact: str,
) -> None:
    selected, retained, replacement = tmp_path / "selected", tmp_path / "retained", tmp_path / "replacement"
    selected.mkdir()
    replacement.mkdir()
    swapped = False

    def swap_at_receipt(frame: FrameType, event: str, _arg: _TraceArgument | None) -> None:
        nonlocal swapped
        # Control scheduling at the actual public writer's receipt boundary.
        # Both calls and filesystem operations remain real; no API is replaced.
        if not swapped and event == "call" and frame.f_code is _written_reference.__code__:
            swapped = True
            for name in ("reference.docx", "reference.native-default.docx"):
                (replacement / name).write_bytes((selected / name).read_bytes())
            if changed_artifact == "reference":
                with ZipFile(replacement / "reference.docx") as archive:
                    styles = archive.read("word/styles.xml")
                replace_part(replacement / "reference.docx", "word/styles.xml",
                             styles + b"<!-- unrelated package -->")
            else:
                with ZipFile(replacement / "reference.native-default.docx", "a") as archive:
                    archive.comment = b"unrelated native export"
            selected.rename(retained)
            replacement.rename(selected)

    previous_trace = sys.gettrace()
    sys.settrace(swap_at_receipt)
    try:
        with pytest.raises(OfficePagePolicyError, match="differ from intended native bytes"):
            write_office_reference(selected / "reference.docx", margin_mm=12)
    finally:
        sys.settrace(previous_trace)
    assert swapped
    assert (retained / "reference.docx").is_file()
    assert (retained / "reference.native-default.docx").is_file()
    # Substituted reference still meets page policy; custody must reject it.
    assert verify_office_page_policy(selected / "reference.docx", margin_mm=12).margin_twips == 680
    assert (retained / "reference.docx").read_bytes() != (selected / "reference.docx").read_bytes() or (
        retained / "reference.native-default.docx").read_bytes() != (
        selected / "reference.native-default.docx").read_bytes()


@pytest.mark.integration
def test_native_reference_preserves_payloads_and_propagates_geometry(tmp_path: Path, project_root: Path) -> None:
    native = project_root / ".rikishi/template-renderer/efce6d6f5b3c4e8e2bbf92d8250855a0a9389ae8"
    assert native.is_dir(), "Pinned native renderer must exist for this bounded integration test"
    sys.path.insert(0, str(native))
    try:
        from infrastructure.rendering.docx_renderer import render_docx
    finally:
        sys.path.remove(str(native))
    receipt = write_office_reference(tmp_path / "reference.docx", margin_mm=12)
    assert Path(render_docx.__code__.co_filename).resolve().is_relative_to(native)
    default = receipt.default_reference_doc.read_bytes()
    assert receipt.default_reference_sha256 == hashlib.sha256(default).hexdigest()
    assert receipt.pandoc_sha256 == hashlib.sha256(receipt.pandoc_executable.read_bytes()).hexdigest()
    assert receipt.pandoc_version.startswith("pandoc ")
    with ZipFile(BytesIO(default)) as original, ZipFile(receipt.reference_doc) as reference:
        assert original.namelist() == reference.namelist()
        assert original.comment == reference.comment
        for name in original.namelist():
            before, after = original.read(name), reference.read(name)
            if name == "word/styles.xml":
                assert after.replace(b'<w:color w:val="005EA8"/>',
                                     b'<w:color w:val="4F81BD" w:themeColor="accent1" />')\
                    .replace(b'<w:pPr><w:keepLines/></w:pPr>', b'') == before
            elif name != "word/document.xml":
                assert before == after, name
            else:
                assert after.replace(GEOMETRY.encode(), b"") == before
                assert len(ElementTree.fromstring(after).findall(".//" + W + "sectPr")) == 1
    assert verify_office_reference_policy(default, receipt.reference_doc.read_bytes(),
                                          margin_mm=12) == receipt.geometry
    assert json.loads(json.dumps(asdict(receipt.geometry)))["margin_twips"] == 680
    markdown = tmp_path / "fixture.md"
    Image.new("RGB", (16, 16), color=(180, 50, 10)).save(tmp_path / "image.png")
    markdown.write_text("# Bounded fixture\n\nNative paragraph α $x^2$ [source](https://example.org).\n\n"
                        "$$F(q)=1.$$\n\n![Real image](image.png){width=16px}\n")
    baseline = render_docx(markdown, tmp_path / "baseline.docx",
                           extra_args=[f"--resource-path={tmp_path}"]).output_path
    with pytest.raises(OfficePagePolicyError, match="explicit pgSz and pgMar"):
        verify_office_page_policy(baseline, margin_mm=12)
    output = render_docx(markdown, tmp_path / "native.docx", reference_doc=receipt.reference_doc,
                         extra_args=[f"--resource-path={tmp_path}"]).output_path
    actual = verify_office_page_policy(output, margin_mm=12)
    assert actual.section_count == 1
    with ZipFile(output) as archive, ZipFile(baseline) as original:
        document = ElementTree.fromstring(archive.read("word/document.xml"))
        assert document.findall(".//{http://schemas.openxmlformats.org/officeDocument/2006/math}oMath")
        before = ElementTree.fromstring(original.read("word/document.xml"))
        assert [node.text for node in before.iter(W + "t")] == [
            node.text for node in document.iter(W + "t")]
        math_namespace = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"
        assert [ElementTree.tostring(node) for node in before.iter(math_namespace + "oMath")] == [
            ElementTree.tostring(node) for node in document.iter(math_namespace + "oMath")]
        for name in archive.namelist():
            if name.startswith("word/media/") or name == "word/_rels/document.xml.rels":
                assert archive.read(name) == original.read(name), name
        # Pandoc serializes styles into the manuscript. Invert only the two
        # approved atoms and require all remaining final styles bytes unchanged.
        assert archive.read("word/styles.xml").replace(
            b'<w:color w:val="005EA8" />',
            b'<w:color w:val="4F81BD" w:themeColor="accent1" />').replace(
            b'<w:pPr><w:keepLines /></w:pPr>', b'') == original.read("word/styles.xml")
    wrong = write_office_reference(tmp_path / "wrong-reference.docx", margin_mm=25)
    wrong_docx = render_docx(markdown, tmp_path / "wrong.docx", reference_doc=wrong.reference_doc,
                             extra_args=[f"--resource-path={tmp_path}"]).output_path
    with pytest.raises(OfficePagePolicyError, match="differs from publication policy"):
        verify_office_page_policy(wrong_docx, margin_mm=12)


@pytest.mark.parametrize("policy", ["effective-link-contrast", "explicit-link-color", "caption-keep"])
def test_native_reference_repairs_effective_link_and_caption_policy(
    tmp_path: Path, policy: Literal["effective-link-contrast", "explicit-link-color", "caption-keep"],
) -> None:
    # Given: the real native Pandoc default, including its overriding theme colour.
    receipt = write_office_reference(tmp_path / "reference.docx", margin_mm=12)
    with ZipFile(receipt.reference_doc) as archive:
        styles = ElementTree.fromstring(archive.read("word/styles.xml"))
        by_id = {node.get(W + "styleId"): node for node in styles.findall(W + "style")}
        color = by_id["Hyperlink"].find(W + "rPr/" + W + "color")
        assert color is not None
        drawing = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
        accent = ElementTree.fromstring(archive.read("word/theme/theme1.xml")).find(
            ".//" + drawing + "clrScheme/" + drawing + "accent1/" + drawing + "srgbClr")
        assert accent is not None
    # When: resolve theme precedence, as the native renderer does.
    effective = accent.get("val") if color.get(W + "themeColor") == "accent1" else color.get(W + "val")
    assert effective is not None
    channels = [int(effective[index:index + 2], 16) / 255 for index in (0, 2, 4)]
    luminance = sum(weight * (c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
                    for weight, c in zip((0.2126, 0.7152, 0.0722), channels))
    # Then: both visible link contrast and native caption grouping are required.
    match policy:
        case "effective-link-contrast":
            assert 1.05 / (luminance + 0.05) >= 4.5
            fallback = color.get(W + "val", "")
            fallback_channels = [int(fallback[index:index + 2], 16) / 255 for index in (0, 2, 4)]
            fallback_luminance = sum(
                weight * (c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
                for weight, c in zip((0.2126, 0.7152, 0.0722), fallback_channels))
            assert 1.05 / (fallback_luminance + 0.05) >= 4.5
        case "explicit-link-color":
            assert color.attrib == {W + "val": "005EA8"}
        case "caption-keep":
            assert by_id["ImageCaption"].find(W + "pPr/" + W + "keepLines") is not None
            assert by_id["CaptionedFigure"].find(W + "pPr/" + W + "keepNext") is not None
        case unreachable:
            assert_never(unreachable)


def test_reference_projection_preserves_every_non_target_byte_and_zip_metadata(tmp_path: Path) -> None:
    # Given: a real OPC fixture with unrelated fonts, header and image bytes.
    default = package(tmp_path, section="").read_bytes()
    # When: generate and independently verify the exact approved projection.
    projected = _reference(_package(default), 680, 12240, 15840)
    report = verify_office_reference_policy(default, projected, margin_mm=12)
    # Then: inverse projection recovers every XML byte, and all other parts are exact.
    assert report.docx_sha256 == hashlib.sha256(projected).hexdigest()
    with ZipFile(BytesIO(default)) as before, ZipFile(BytesIO(projected)) as after:
        assert before.namelist() == after.namelist()
        assert before.comment == after.comment
        for row, changed in zip(before.infolist(), after.infolist(), strict=True):
            for field in ("filename", "date_time", "compress_type", "comment", "extra", "create_system",
                          "create_version", "extract_version", "reserved", "flag_bits", "volume",
                          "internal_attr", "external_attr"):
                assert getattr(row, field) == getattr(changed, field), (row.filename, field)
            original, actual = before.read(row), after.read(changed)
            inverse = {
                "word/document.xml": actual.replace(GEOMETRY.encode(), b""),
                "word/styles.xml": actual.replace(b'<w:color w:val="005EA8"/>',
                    b'<w:color w:val="4F81BD" w:themeColor="accent1" w:themeTint="00" w:themeShade="FF"/>')
                    .replace(b'<w:pPr><w:keepLines/></w:pPr>', b''),
            }.get(row.filename, actual)
            assert inverse == original



@pytest.mark.parametrize("part,old,new", [
    ("word/styles.xml", b'005EA8', b'0000FF'),
    ("word/styles.xml", b'w:val="005EA8"', b'w:val="005EA8" w:themeColor="accent1"'),
    ("word/styles.xml", b'<w:keepLines/>', b'<w:keepLines w:val="false"/>'),
    ("word/styles.xml", b'<w:keepNext/>', b'<w:keepNext w:val="false"/>'),
    ("word/styles.xml", b'Cambria', b'Arial'),
    ("word/styles.xml", b'</w:styles>', b'<w:style w:styleId="Extra"/></w:styles>'),
    ("word/header1.xml", b'retained', b'unapproved'),
    ("word/fontTable.xml", b'retained', b'unapproved'),
    ("word/media/image.png", b'retained', b'unapproved'),
    ("word/document.xml", b'w:top="680"', b'w:top="681"'),
    ("word/document.xml", b'w:w="12240"', b'w:w="11906"'),
    ("word/document.xml", b'Native scientific text', b'Unapproved scientific text'),
])
def test_reference_verifier_rejects_rehashed_unapproved_payload_edits(
    tmp_path: Path, part: str, old: bytes, new: bytes,
) -> None:
    # Given: an approved reference, then an independently rehashed unauthorized edit.
    default = package(tmp_path, section="").read_bytes()
    output = tmp_path / "reference.docx"
    output.write_bytes(_reference(_package(default), 680, 12240, 15840))
    with ZipFile(output) as archive:
        original = archive.read(part)
    assert old in original
    replace_part(output, part, original.replace(old, new, 1))
    rebound = hashlib.sha256(output.read_bytes()).hexdigest()
    assert rebound != hashlib.sha256(default).hexdigest()
    # When / Then: whole-reference policy refuses the mutation despite its fresh hash.
    with pytest.raises(OfficePagePolicyError, match="exact approved native projection"):
        verify_office_reference_policy(default, output.read_bytes(), margin_mm=12)


@pytest.mark.parametrize("field", ["date_time", "external_attr", "comment", "extra", "flag-bits", "archive-comment",
                                   "order", "new-member", "trailing"])
def test_reference_verifier_rejects_rehashed_zip_custody_changes(tmp_path: Path, field: str) -> None:
    # Given: a valid projected archive whose payloads will be retained.
    default = package(tmp_path, section="").read_bytes()
    projected = _reference(_package(default), 680, 12240, 15840)
    with ZipFile(BytesIO(projected)) as archive:
        rows = [(row, archive.read(row)) for row in archive.infolist()]
    mutated = BytesIO()
    with ZipFile(mutated, "w") as archive:
        if field == "archive-comment":
            archive.comment = b"unapproved comment"
        if field == "order":
            rows.reverse()
        row = rows[0][0]
        if field == "date_time":
            row.date_time = (2020, 1, 1, 0, 0, 0)
        if field == "external_attr":
            row.external_attr = (stat.S_IFREG | 0o644) << 16
        if field == "comment":
            row.comment = b"unapproved member comment"
        if field == "extra":
            row.extra = b"\xfe\xca\x00\x00"
        for row, payload in rows:
            archive.writestr(row, payload)
        if field == "new-member":
            archive.writestr("word/unapproved.xml", b"<unapproved/>")
    actual = mutated.getvalue() + (b"trailing" if field == "trailing" else b"")
    if field == "flag-bits":
        data = bytearray(actual)
        struct.pack_into("<H", data, 6, 0x800)
        struct.pack_into("<H", data, data.index(b"PK\x01\x02") + 8, 0x800)
        actual = bytes(data)
    assert hashlib.sha256(actual).hexdigest() != hashlib.sha256(projected).hexdigest()
    # When / Then: identical part payloads cannot authorize different archive custody.
    with pytest.raises(OfficePagePolicyError, match="exact approved native projection"):
        verify_office_reference_policy(default, actual, margin_mm=12)


@pytest.mark.parametrize("styles", [
    b"<broken>",
    STYLES.replace(b'UTF-8', b'unknown-codec'),
    STYLES.replace(b'UTF-8', b'UTF-16'),
    STYLES.replace(b'</w:styles>', b'\xff</w:styles>'),
    STYLES.replace(b'wordprocessingml/2006/main', b'unsupported/main'),
    STYLES.replace(b'</w:styles>', b'<!-- comment --></w:styles>'),
    STYLES.replace(b'</w:styles>', b'<?processing instruction?></w:styles>'),
    STYLES.replace(b'</w:styles>', b'<w:style w:type="character" w:styleId="Hyperlink"/></w:styles>'),
    STYLES.replace(b'<w:color ', b'<w:color w:val="000000"/><w:color '),
    STYLES.replace(b'w:themeColor="accent1"', b'w:unknown="accent1"'),
    STYLES.replace(b'<w:keepNext/>', b'<w:keepNext w:val="false"/>'),
    STYLES.replace(b'<w:keepNext/>', b'<w:keepNext/><w:keepNext/>'),
    STYLES.replace(b'w:val="Caption"', b'w:val="Other"'),
    STYLES.replace(b'<w:basedOn w:val="Caption"/>', b'<w:pPr><w:keepLines/></w:pPr>'),
    STYLES.replace(b'<w:basedOn w:val="Caption"/>', b'<w:basedOn w:val="Caption"/><w:pPr/>'),
    STYLES.replace(b'w:styleId="ImageCaption"', b'w:styleId="OtherCaption"'),
    STYLES.replace(b'<w:basedOn w:val="Caption"/>', b'<w:basedOn w:val="Caption"/><w:rPr/><w:rPr/>'),
    STYLES.replace(b'<w:basedOn w:val="Caption"/>', b'<w:rPr/><w:basedOn w:val="Caption"/>'),
    STYLES.replace(b'<w:color ', b'<w:color xmlns:w="urn:unsupported" '),
])
def test_unsupported_style_xml_is_a_typed_policy_failure(tmp_path: Path, styles: bytes) -> None:
    # Given: real malformed/unsupported style XML in an otherwise valid OPC package.
    output = package(tmp_path, section="")
    replace_part(output, "word/styles.xml", styles)
    # When / Then: no native default fallback or raw parser/codec exception escapes.
    with pytest.raises(OfficePagePolicyError):
        _reference(_package(output.read_bytes()), 680, 12240, 15840)


@pytest.mark.parametrize("part,payload", [
    ("word/_rels/document.xml.rels", STYLES_RELS.replace(b'styles.xml', b'other.xml')),
    ("word/_rels/document.xml.rels", STYLES_RELS.replace(b'Target="styles.xml"', b'Target="styles.xml" TargetMode="External"')),
    ("word/_rels/document.xml.rels", b'<Relationships/>'),
    ("[Content_Types].xml", CONTENT_TYPES.replace('word/styles.xml', 'word/other.xml').encode()),
])
def test_reference_rejects_decoy_or_unbound_styles(tmp_path: Path, part: str, payload: bytes) -> None:
    # Given: a decoy styles part with an incorrect native relationship/type.
    output = package(tmp_path, section="")
    replace_part(output, part, payload)
    # When / Then: byte patching must bind the document's actual styles.
    with pytest.raises(OfficePagePolicyError, match="styles"):
        _reference(_package(output.read_bytes()), 680, 12240, 15840)

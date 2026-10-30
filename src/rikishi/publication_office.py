"""Bounded Word geometry, hyperlink colour and figure-caption reference policy.

Only two geometry elements, the Hyperlink colour atom and ImageCaption keepLines
are changed. All other member payloads and XML bytes remain exact.
Verification reads the actual package; these checks do not establish pagination.
Programming size exception (# noqa: SIZE_OK): ownership permits one source module.
"""

from __future__ import annotations

import errno
import hashlib
import math
import os
import re
import shutil
import stat
import struct
import subprocess
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from copy import copy
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from io import BytesIO
from pathlib import Path, PurePosixPath
from typing import Final
from xml.etree.ElementTree import Element, ParseError
from zipfile import ZIP_DEFLATED, ZIP_STORED, BadZipFile, ZipFile, ZipInfo

from defusedxml.common import DefusedXmlException
from defusedxml.ElementTree import fromstring

W: Final = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_MAX_BYTES: Final = 64 * 1024 * 1024
_MAX_EXPANDED: Final = 128 * 1024 * 1024
_MAX_XML: Final = 16 * 1024 * 1024
_TOLERANCE_MM: Final = 0.01
_SECTION_ORDER: Final = (
    "headerReference", "footerReference", "footnotePr", "endnotePr", "type",
    "pgSz", "pgMar", "paperSrc", "pgBorders", "lnNumType", "pgNumType", "cols",
    "formProt", "vAlign", "noEndnote", "titlePg", "textDirection", "bidi",
    "rtlGutter", "docGrid", "printerSettings", "sectPrChange",
)


class OfficePagePolicyError(ValueError):
    """A package, tool, or geometry failed the bounded Office contract."""

    __slots__ = ("detail",)
    detail: str

    def __init__(self, detail: str) -> None:
        # Exceptions must permit the runtime to attach traceback/context fields.
        self.detail = detail
        super().__init__(detail)


@dataclass(frozen=True, slots=True)
class OfficePagePolicyReport:
    """Uniform geometry independently observed in every actual section."""

    docx_sha256: str
    margin_mm: float
    page_width_mm: float
    page_height_mm: float
    margin_twips: int
    page_width_twips: int
    page_height_twips: int
    section_count: int


@dataclass(frozen=True, slots=True)
class OfficeReferenceReceipt:
    """Bind the actual reference to its native default and Pandoc executable."""

    reference_doc: Path
    default_reference_doc: Path
    reference_sha256: str
    default_reference_sha256: str
    pandoc_executable: Path
    pandoc_sha256: str
    pandoc_version: str
    geometry: OfficePagePolicyReport


@dataclass(frozen=True, slots=True)
class _Package:
    original: bytes
    parts: tuple[tuple[ZipInfo, bytes], ...]
    comment: bytes
    document: bytes


def _no_symlinks(path: Path) -> Path:
    """Refuse symlink leaves and ancestors before any filesystem access."""
    absolute = path.absolute()
    if any(part.is_symlink() for part in (absolute, *absolute.parents)):
        raise OfficePagePolicyError(f"Symlink path refused: {path}")
    return absolute


def _read_regular(path: Path, limit: int) -> bytes:
    """Bound both the initial stat and the actual read, without following links."""
    path = _no_symlinks(path)
    with _parent_directory(path) as directory:
        descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        with os.fdopen(descriptor, "rb") as handle:
            info = os.fstat(handle.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
                raise OfficePagePolicyError(f"Oversized or nonregular file: {path}")
            data = handle.read(limit + 1)
    if len(data) > limit:
        raise OfficePagePolicyError(f"File exceeds byte budget: {path}")
    return data


@contextmanager
def _parent_directory(path: Path) -> Iterator[int]:
    """Pin every ancestor through no-follow directory descriptors, including races."""
    absolute = path.absolute()
    if ".." in absolute.parts:
        raise OfficePagePolicyError("Parent traversal refused in Office artifact path")
    try:
        with ExitStack() as stack:
            flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
            descriptor = os.open(absolute.anchor, flags)
            stack.callback(os.close, descriptor)
            for component in absolute.parent.parts[1:]:
                descriptor = os.open(component, flags, dir_fd=descriptor)
                stack.callback(os.close, descriptor)
            yield descriptor
    except OSError as exc:
        if exc.errno in (errno.ELOOP, errno.ENOTDIR):
            raise OfficePagePolicyError(f"Symlink or non-directory path refused: {path}") from exc
        raise


def _ensure_new(directory: int, names: tuple[str, ...]) -> None:
    """Check every destination before either creation; exclusive opens arbitrate races."""
    for name in names:
        try:
            os.stat(name, dir_fd=directory, follow_symlinks=False)
        except FileNotFoundError:
            # Absence is the required state; every other stat error propagates.
            continue
        raise FileExistsError(name)


def _write_new(directory: int, name: str, data: bytes) -> None:
    """Create only through the pinned directory; never replace an occupied leaf."""
    descriptor = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=directory)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(data)


def _xml(payload: bytes, part: str) -> Element:
    """Reject entities, malformed XML and unbounded package control parts."""
    if len(payload) > _MAX_XML:
        raise OfficePagePolicyError(f"Office XML exceeds byte budget: {part}")
    try:
        return fromstring(payload, forbid_dtd=True)
    except (ParseError, DefusedXmlException) as exc:
        raise OfficePagePolicyError(f"Unsafe or malformed Office XML {part}: {exc}") from exc


def _main_document(parts: tuple[tuple[ZipInfo, bytes], ...]) -> None:
    """Bind geometry to the Office root relationship rather than a decoy ZIP path."""
    payloads = {row.filename: payload for row, payload in parts}
    if "_rels/.rels" not in payloads or "[Content_Types].xml" not in payloads:
        raise OfficePagePolicyError("Office package requires root relationships and content types")
    relationships = _xml(payloads["_rels/.rels"], "_rels/.rels")
    namespace = "{http://schemas.openxmlformats.org/package/2006/relationships}"
    candidates = [node for node in relationships if node.get("Type", "").endswith("/officeDocument")]
    relationship_type = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
    if (relationships.tag != namespace + "Relationships" or len(candidates) != 1
            or candidates[0].tag != namespace + "Relationship"
            or candidates[0].get("Type") != relationship_type
            or candidates[0].get("Target") != "word/document.xml"
            or candidates[0].get("TargetMode", "Internal") != "Internal"):
        raise OfficePagePolicyError("Office main-document relationship must target word/document.xml internally")
    types = _xml(payloads["[Content_Types].xml"], "[Content_Types].xml")
    ct = "{http://schemas.openxmlformats.org/package/2006/content-types}"
    overrides = [node for node in types if node.get("PartName") == "/word/document.xml"]
    if (types.tag != ct + "Types" or len(overrides) != 1 or overrides[0].tag != ct + "Override"
            or overrides[0].get("ContentType") !=
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"):
        raise OfficePagePolicyError("Office main-document content type is missing or ambiguous")


def _package(data: bytes) -> _Package:
    """Admit only finite, unambiguous, regular Office ZIP members; never extract."""
    if len(data) > _MAX_BYTES:
        raise OfficePagePolicyError("DOCX exceeds archive byte budget")
    try:
        with ZipFile(BytesIO(data)) as archive:
            rows = archive.infolist()
            if len(rows) > 4096 or sum(row.file_size for row in rows) > _MAX_EXPANDED:
                raise OfficePagePolicyError("DOCX exceeds expanded archive budget")
            seen: set[str] = set()
            for row in rows:
                name = row.filename
                pieces = name.rstrip("/").split("/")
                mode = stat.S_IFMT(row.external_attr >> 16)
                if (name != row.orig_filename or not name or "\\" in name or ":" in name
                        or PurePosixPath(name).is_absolute()
                        or any(piece in ("", ".", "..") for piece in pieces)
                        or name.rstrip("/").casefold() in seen
                        or mode not in (0, stat.S_IFREG, stat.S_IFDIR)
                        or (mode == stat.S_IFDIR and not row.is_dir())
                        or row.flag_bits & 1 or row.compress_type not in (ZIP_STORED, ZIP_DEFLATED)):
                    raise OfficePagePolicyError(f"Unsafe or duplicate ZIP member: {name!r}")
                seen.add(name.rstrip("/").casefold())
            parts = tuple((row, archive.read(row)) for row in rows)
            documents = [payload for row, payload in parts if row.filename == "word/document.xml"]
            if len(documents) != 1 or len(documents[0]) > _MAX_XML:
                raise OfficePagePolicyError("DOCX requires one bounded word/document.xml")
            _main_document(parts)
            return _Package(data, parts, archive.comment, documents[0])
    except (BadZipFile, RuntimeError, NotImplementedError) as exc:
        raise OfficePagePolicyError(f"Unreadable DOCX ZIP: {exc}") from exc


def _sections(xml: bytes) -> tuple[Element, ...]:
    """Require real current sections in schema order, including a final body section."""
    document = _xml(xml, "word/document.xml")
    body = document.find(W + "body")
    sections = tuple(document.iter(W + "sectPr"))
    if (document.tag != W + "document" or body is None or len(body) == 0
            or body[-1].tag != W + "sectPr" or not 1 <= len(sections) <= 256
            or len(body.findall(W + "sectPr")) != 1):
        raise OfficePagePolicyError("DOCX requires bounded current sections and one final body section")
    parents = {child: parent for parent in document.iter() for child in parent}
    for section in sections:
        parent = parents[section]
        if parent is not body and (parent.tag != W + "pPr"
                                  or parents[parent].tag != W + "p"):
            raise OfficePagePolicyError("Unsupported nested or historical section properties")
        tags = [child.tag.removeprefix(W) for child in section]
        if any(tag not in _SECTION_ORDER for tag in tags) or "sectPrChange" in tags:
            raise OfficePagePolicyError("Unsupported section child or tracked section change")
        ranks = [_SECTION_ORDER.index(tag) for tag in tags]
        if ranks != sorted(ranks):
            raise OfficePagePolicyError("Section children violate OOXML schema order")
    return sections


def _twips(value: float) -> int:
    """Use decimal half-up rounding; the nearest twip is within 0.01 mm."""
    if not math.isfinite(value) or value <= 0 or value > 558.8:
        raise OfficePagePolicyError("Page dimensions and margin must be finite, positive, <=558.8 mm")
    result = int((Decimal(str(value)) * 1440 / Decimal("25.4")).to_integral_value(
        rounding=ROUND_HALF_UP))
    if result == 0 or abs(result * 25.4 / 1440 - value) > _TOLERANCE_MM:
        raise OfficePagePolicyError("Policy cannot be represented within 0.01 mm in twips")
    return result


def _geometry(margin_mm: float, width_mm: float, height_mm: float) -> tuple[int, int, int]:
    margin, width, height = (_twips(value) for value in (margin_mm, width_mm, height_mm))
    if 2 * margin >= min(width, height) or width > height:
        raise OfficePagePolicyError("Policy requires positive usable area and portrait paper")
    return margin, width, height


def _integer(node: Element, name: str) -> int:
    value = node.get(W + name, "")
    if re.fullmatch(r"[0-9]{1,8}", value) is None:
        raise OfficePagePolicyError(f"Missing or invalid Word geometry attribute: {name}")
    return int(value)


def _report(
    package: _Package, margin_mm: float, page_width_mm: float, page_height_mm: float,
) -> OfficePagePolicyReport:
    """Check actual geometry before publishing a reference or accepting an artifact."""
    margin, width, height = _geometry(margin_mm, page_width_mm, page_height_mm)
    sections = _sections(package.document)
    for section in sections:
        sizes, margins = section.findall(W + "pgSz"), section.findall(W + "pgMar")
        if len(sizes) != 1 or len(margins) != 1:
            raise OfficePagePolicyError("Every section needs one explicit pgSz and pgMar")
        size, edges = sizes[0], margins[0]
        if (len(size) or len(edges) or _integer(size, "w") != width or _integer(size, "h") != height
                or size.get(W + "orient", "portrait") != "portrait"
                or any(_integer(edges, edge) != margin for edge in ("top", "right", "bottom", "left"))
                or _integer(edges, "gutter") != 0
                or any(_integer(edges, edge) > margin for edge in ("header", "footer"))):
            raise OfficePagePolicyError("Actual Word page geometry differs from publication policy")
        columns = section.findall(W + "cols")
        if len(columns) > 1 or any(col.get(W + "num", "1") != "1" or len(col) for col in columns):
            raise OfficePagePolicyError("Office policy requires a single full-width text column")
    return OfficePagePolicyReport(hashlib.sha256(package.original).hexdigest(), margin_mm,
                                  page_width_mm, page_height_mm, margin, width, height, len(sections))


def verify_office_page_policy(
    docx: Path, *, margin_mm: float, page_width_mm: float = 215.9,
    page_height_mm: float = 279.4,
) -> OfficePagePolicyReport:
    """Check actual XML against policy, independently of receipt hashes.

    Every section must specify the nearest twip for page size and all four body
    margins, with zero gutter and one text column. Header/footer distances must
    be explicit and within the body margin. No pagination or visual claim follows.
    """
    return _report(_package(_read_regular(docx, _MAX_BYTES)), margin_mm,
                   page_width_mm, page_height_mm)


def _reference_styles(payload: bytes) -> bytes:
    """Patch two exact native style atoms; refuse ambiguous or unsupported defaults.

    LibreOffice uses the fallback colour; theme-aware consumers may use accent1.
    Remove theme selectors only from Hyperlink's colour so both get explicit blue.
    Native CaptionedFigure already keeps with the following ImageCaption. Add
    keepLines only to ImageCaption, leaving table and other captions untouched.
    """
    try:
        payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise OfficePagePolicyError("Native styles require UTF-8 XML") from exc
    declaration = re.match(br'<\?xml version="1\.0" encoding="(?:UTF-8|utf-8)"\?>', payload)
    remainder = payload[declaration.end():] if declaration else payload
    if (b"<?" in remainder or b"<!--" in payload or b"<!" in payload
            or re.search(br'encoding\s*=', remainder)
            or len(re.findall(br'xmlns:w\s*=', payload)) != 1):
        raise OfficePagePolicyError("Native styles are outside the byte-preserving XML grammar")
    root = _xml(payload, "word/styles.xml")
    if root.tag != W + "styles" or not re.match(
            br'\s*<w:styles\s[^<>]*xmlns:w="http://schemas.openxmlformats.org/'
            br'wordprocessingml/2006/main"[^<>]*>', remainder):
        raise OfficePagePolicyError("Native styles require the supported Word namespace and prefix")
    styles = root.findall(W + "style")
    identifiers = [node.get(W + "styleId") for node in styles]
    if (None in identifiers or len(set(identifiers)) != len(identifiers)
            or len(tuple(root.iter(W + "style"))) != len(styles)):
        raise OfficePagePolicyError("Native styles have missing, nested or duplicate style targets")
    selected: dict[str, tuple[Element, bytes]] = {}
    for identifier, kind in (("Hyperlink", "character"), ("ImageCaption", "paragraph"),
                             ("CaptionedFigure", "paragraph")):
        nodes = [node for node in styles if node.get(W + "styleId") == identifier]
        blocks = re.findall(br'<w:style\b[^<>]*\bw:styleId="' + identifier.encode()
                            + br'"[^<>]*>.*?</w:style>', payload, re.DOTALL)
        if len(nodes) != 1 or len(blocks) != 1 or nodes[0].get(W + "type") != kind:
            raise OfficePagePolicyError(f"Native styles require one supported {identifier} target")
        order = (W + "name", W + "basedOn", W + "pPr", W + "rPr")
        children = [child.tag for child in nodes[0]]
        if (any(tag not in order for tag in children) or len(set(children)) != len(children)
                or children != sorted(children, key=order.index)):
            raise OfficePagePolicyError(f"Native {identifier} has unsupported style properties")
        selected[identifier] = nodes[0], blocks[0]
    link, link_bytes = selected["Hyperlink"]
    properties = link.findall(W + "rPr")
    colors = link.findall(".//" + W + "color")
    color_bytes = re.findall(br'<w:color\b[^<>]*/>', link_bytes)
    if (len(properties) != 1 or len(colors) != 1 or colors[0] not in properties[0]
            or len(color_bytes) != 1 or len(colors[0])
            or not {W + "val"} <= colors[0].attrib.keys()
            or not colors[0].attrib.keys() <= {W + name for name in (
                "val", "themeColor", "themeTint", "themeShade")}
            or re.fullmatch(r"[0-9a-fA-F]{6}", colors[0].get(W + "val", "")) is None):
        raise OfficePagePolicyError("Native Hyperlink requires one supported colour atom")
    caption, caption_bytes = selected["ImageCaption"]
    bases = caption.findall(W + "basedOn")
    figure = selected["CaptionedFigure"][0]
    keeps = figure.findall(W + "pPr/" + W + "keepNext")
    if (len(bases) != 1 or bases[0].get(W + "val") != "Caption"
            or caption.findall(W + "pPr") or len(keeps) != 1 or len(keeps[0])
            or keeps[0].get(W + "val", "true") not in ("true", "1", "on")
            or len(figure.findall(W + "pPr")) != 1
            or len(figure.findall(".//" + W + "keepNext")) != 1):
        raise OfficePagePolicyError("Native caption/figure keep linkage is unsupported")
    patched_link = link_bytes.replace(color_bytes[0], b'<w:color w:val="005EA8"/>', 1)
    # pPr belongs before rPr in CT_Style; preserve all existing bytes and spacing.
    position = caption_bytes.find(b"<w:rPr")
    if position == -1:
        position = caption_bytes.index(b"</w:style>")
    patched_caption = (caption_bytes[:position] + b"<w:pPr><w:keepLines/></w:pPr>"
                       + caption_bytes[position:])
    result = payload.replace(link_bytes, patched_link, 1).replace(caption_bytes, patched_caption, 1)
    _xml(result, "word/styles.xml")
    return result


def _styles_binding(package: _Package) -> bytes:
    """Refuse a styles.xml decoy that is not the main document's actual styles part."""
    payloads = {row.filename: payload for row, payload in package.parts}
    if not {"word/styles.xml", "word/_rels/document.xml.rels"} <= payloads.keys():
        raise OfficePagePolicyError("Native reference requires a bound word/styles.xml")
    rels = _xml(payloads["word/_rels/document.xml.rels"], "word/_rels/document.xml.rels")
    namespace = "{http://schemas.openxmlformats.org/package/2006/relationships}"
    candidates = [node for node in rels if node.get("Type", "").endswith("/styles")]
    if (rels.tag != namespace + "Relationships" or len(candidates) != 1
            or candidates[0].tag != namespace + "Relationship"
            or candidates[0].get("Type") !=
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles"
            or candidates[0].get("Target") != "styles.xml"
            or candidates[0].get("TargetMode", "Internal") != "Internal"):
        raise OfficePagePolicyError("Native styles relationship must target styles.xml internally")
    types = _xml(payloads["[Content_Types].xml"], "[Content_Types].xml")
    overrides = [node for node in types if node.get("PartName") == "/word/styles.xml"]
    if (len(overrides) != 1 or overrides[0].tag !=
            "{http://schemas.openxmlformats.org/package/2006/content-types}Override"
            or overrides[0].get("ContentType") !=
            "application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"):
        raise OfficePagePolicyError("Native styles content type is missing or ambiguous")
    return payloads["word/styles.xml"]


def _reference(package: _Package, margin: int, width: int, height: int) -> bytes:
    """Apply the approved geometry/style projection without serializing XML."""
    sections = _sections(package.document)
    # This bounded generator accepts only a single default section whose existing
    # properties precede page geometry. A changed native template fails explicitly.
    if len(sections) != 1 or any(child.tag not in {W + tag for tag in _SECTION_ORDER[:5]}
                                 for child in sections[0]):
        raise OfficePagePolicyError("Native default reference has unsupported existing section geometry")
    xml = package.document
    opening = b'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    if (opening not in xml or xml.count(b"<w:sectPr>") != 1
            or xml.count(b"</w:sectPr>") != 1):
        raise OfficePagePolicyError("Native default reference is outside byte-preserving XML grammar")
    geometry = (f'<w:pgSz w:w="{width}" w:h="{height}"/>'
                f'<w:pgMar w:top="{margin}" w:right="{margin}" w:bottom="{margin}" '
                f'w:left="{margin}" w:header="{margin}" w:footer="{margin}" w:gutter="0"/>').encode()
    patched = xml.replace(b"</w:sectPr>", geometry + b"</w:sectPr>", 1)
    _sections(patched)
    patched_styles = _reference_styles(_styles_binding(package))
    destination = BytesIO()
    with ZipFile(destination, "w") as archive:
        archive.comment = package.comment
        for row, payload in package.parts:
            if row.flag_bits not in (0, 0x800) or not row.filename.isascii():
                raise OfficePagePolicyError("Native ZIP filename flags are unsupported")
            replacement = {"word/document.xml": patched, "word/styles.xml": patched_styles}.get(
                row.filename, payload)
            archive.writestr(copy(row), replacement)
        central_start = destination.tell()
    # zipfile resets flags and supplies nonzero external attributes for zero.
    # Restore these native fields in its own newly generated bounded ZIP records;
    # names are ASCII, so either admitted UTF-8 flag state uses identical bytes.
    data = bytearray(destination.getvalue())
    with ZipFile(BytesIO(data)) as archive:
        cursor = central_start
        for (native, _), generated in zip(package.parts, archive.infolist(), strict=True):
            struct.pack_into("<H", data, generated.header_offset + 6, native.flag_bits)
            struct.pack_into("<H", data, cursor + 8, native.flag_bits)
            struct.pack_into("<I", data, cursor + 38, native.external_attr)
            lengths = struct.unpack_from("<HHH", data, cursor + 28)
            cursor += 46 + sum(lengths)
    rendered = bytes(data)
    # ZIP writing may normalize unsupported flags/metadata. Refuse that default
    # rather than silently discard its custody data. CRC, sizes and offsets must
    # change with the approved payloads and are bound by whole-archive equality.
    metadata = ("filename", "date_time", "compress_type", "comment", "extra", "create_system",
                "create_version", "extract_version", "reserved", "flag_bits", "volume",
                "internal_attr", "external_attr")
    projected = _package(rendered)
    for (before, _), (after, _) in zip(package.parts, projected.parts, strict=True):
        if any(getattr(before, field) != getattr(after, field) for field in metadata):
            raise OfficePagePolicyError("Native reference ZIP metadata cannot be preserved")
    return rendered


def verify_office_reference_policy(
    default_docx: bytes, reference_docx: bytes, *, margin_mm: float,
    page_width_mm: float = 215.9, page_height_mm: float = 279.4,
) -> OfficePagePolicyReport:
    """Require the exact approved projection of the retained native default.

    Pure: no filesystem or native-tool access. Reconstruct using the writer's
    generator, then compare every archive byte, including ZIP metadata. Arbitrary
    style, header, font, member or geometry changes fail even after receipt rehash.
    The returned report has the existing frozen geometry fields; no visual or
    Microsoft Word pagination verdict follows from reference-policy verification.
    """
    geometry = _geometry(margin_mm, page_width_mm, page_height_mm)
    expected = _reference(_package(default_docx), *geometry)
    actual = _package(reference_docx)
    if reference_docx != expected:
        raise OfficePagePolicyError("Office reference differs from the exact approved native projection")
    return _report(actual, margin_mm, page_width_mm, page_height_mm)


def _pandoc(executable: Path, arguments: list[str]) -> bytes:
    """Preserve native command failures and their diagnostics without a fallback."""
    try:
        result = subprocess.run([str(executable), *arguments], capture_output=True,
                                check=False, timeout=20)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise OfficePagePolicyError(f"Pandoc native reference command failed: {exc}") from exc
    if result.returncode != 0:
        raise OfficePagePolicyError(
            f"Pandoc native reference command failed (exit {result.returncode}): "
            + result.stderr.decode("utf-8", errors="replace"))
    return result.stdout


def _written_reference(
    output: Path, original_output: Path, *, default: bytes, rendered: bytes,
    margin_mm: float, page_width_mm: float, page_height_mm: float,
) -> OfficePagePolicyReport:
    """Receipt only the exact intended artifacts, including after directory replacement."""
    actual_reference = _read_regular(output, _MAX_BYTES)
    actual_default = _read_regular(original_output, _MAX_BYTES)
    if actual_reference != rendered or actual_default != default:
        raise OfficePagePolicyError("Written Office reference artifacts differ from intended native bytes")
    return _report(_package(actual_reference), margin_mm, page_width_mm, page_height_mm)


def write_office_reference(
    output: Path, *, margin_mm: float, page_width_mm: float = 215.9,
    page_height_mm: float = 279.4, pandoc_path: str = "pandoc",
) -> OfficeReferenceReceipt:
    """Create a new reference from the invoked Pandoc's unmodified native default.

    Refuse occupied outputs and unsafe ZIPs. Retain the exact native archive in
    ``<output.stem>.native-default.docx`` beside the generated reference, because
    Pandoc's default-export ZIP timestamps vary between invocations.
    Apply only the approved Hyperlink colour and ImageCaption keepLines atoms.
    Preserve every other member payload and ZIP metadata,
    plus the section's footnote/header/footer settings. Header/footer distances
    equal the body margin; gutter is zero. No renderer or manuscript is edited.
    """
    margin, width, height = _geometry(margin_mm, page_width_mm, page_height_mm)
    output = _no_symlinks(output)
    original_output = _no_symlinks(output.with_name(output.stem + ".native-default.docx"))
    if output.exists():
        raise FileExistsError(output)
    if original_output.exists():
        raise FileExistsError(original_output)
    if not output.parent.is_dir():
        raise OfficePagePolicyError("Reference output requires an existing regular parent directory")
    found = shutil.which(pandoc_path)
    if found is None:
        raise OfficePagePolicyError(f"Pandoc executable unavailable: {pandoc_path}")
    executable = Path(found).resolve(strict=True)
    digest = hashlib.sha256(_read_regular(executable, 512 * 1024 * 1024)).hexdigest()
    try:
        version = _pandoc(executable, ["--version"]).decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise OfficePagePolicyError(f"Pandoc version is not UTF-8: {exc}") from exc
    if not version.startswith("pandoc "):
        raise OfficePagePolicyError("Native reference tool did not identify itself as Pandoc")
    default = _pandoc(executable, ["--print-default-data-file", "reference.docx"])
    package = _package(default)
    rendered = _reference(package, margin, width, height)
    _report(_package(rendered), margin_mm, page_width_mm, page_height_mm)
    _no_symlinks(output)
    _no_symlinks(original_output)
    if hashlib.sha256(_read_regular(executable, 512 * 1024 * 1024)).hexdigest() != digest:
        raise OfficePagePolicyError("Pandoc executable changed while generating reference")
    with _parent_directory(output) as directory:
        _ensure_new(directory, (output.name, original_output.name))
        _write_new(directory, original_output.name, default)
        _write_new(directory, output.name, rendered)
    report = _written_reference(output, original_output, default=default, rendered=rendered,
                                margin_mm=margin_mm, page_width_mm=page_width_mm,
                                page_height_mm=page_height_mm)
    return OfficeReferenceReceipt(output, original_output, report.docx_sha256,
                                  hashlib.sha256(default).hexdigest(), executable, digest, version, report)

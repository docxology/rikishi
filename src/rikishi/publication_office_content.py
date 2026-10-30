"""Bounded final-Word row projection and the three repaired math serializations.

The byte-only projection inserts cantSplit in ordinary native Pandoc table rows.
It never rewrites text, math, geometry, styles or another ZIP member payload.
The frozen geometry helper supplies its existing safe package parser read-only.
Programming size exception (# noqa: SIZE_OK): assigned ownership permits one
module for this bounded projection, complete custody and math checks.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from enum import IntEnum, StrEnum
from io import BytesIO
from struct import unpack_from
from typing import Final, assert_never
from xml.etree.ElementTree import Element
from zipfile import ZipFile, ZipInfo
from zlib import crc32, decompressobj
from zlib import error as ZlibError

from rikishi.publication_office import OfficePagePolicyError, _Package, _package, _xml

W: Final = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
M: Final = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"
_ROWS: Final = re.compile(rb"<w:tr>.*?</w:tr>", re.DOTALL)
_PROPERTY_ORDER: Final = (
    "cnfStyle", "divId", "gridBefore", "gridAfter", "wBefore", "wAfter", "cantSplit",
    "trHeight", "tblHeader", "tblCellSpacing", "jc", "hidden", "ins", "del", "trPrChange",
)
# Structural digests of the native positive fixture, bound to the canonical patch
# in office-content/canonical-math.patch. Expanded names, attributes, text and
# child order include operators, scripts and bounds, independently of XML prefixes.
_GATHERED: Final = (
    "8494bc72ad1a8e05a7c9f714fc7f3e1c8365822d2380fbf1cc698c58befe257b",
    "538314dcbed1271846520cc1158a7e6d2cce222290d99ea214952ffbe5345939",
    "db3f3769b5617c08e217563a0f8aea739f7b64ac3836ee0ff8d2315fd9766265",
)
_RELATIONS: Final = (
    "f20c4284d107a9651e2d64b2d1b61a8a8476acc45252c3f16ee8f39aab97949d",
    "a0b1016a0fc9c5b209fd7e834989d83030403839305f05bdf10e76e9fabbaa18",
)
# The two existing gathered displays in the complete shared body, independently
# rendered from eq:sumo-translated-core and eq:logarithmic-normalization.
_FULL_GATHERED: Final = (
    _GATHERED[0], "94ad79e149bc0fed070c1c28499528ec490ea717aab9f0a929f7a6acbdb3bbc2",
    _GATHERED[1], "975a2931177a78f6ac3114682a17ce1b30b4c0fa66c1bb03a2b44aa0213cb3e4",
    _GATHERED[2],
)
type _Shape = tuple[str, tuple[tuple[str, str], ...], str, tuple[_Shape, ...]]


class _Compression(IntEnum):
    STORED = 0
    DEFLATE = 8


class _RowProperty(StrEnum):
    CONDITIONAL_STYLE = "cnfStyle"
    KEEP_ROW = "cantSplit"
    HEADER = "tblHeader"


class OfficeContentError(ValueError):
    """An unsupported native package or changed projection, with typed detail."""

    detail: str

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


@dataclass(frozen=True, slots=True)
class OfficeRowChange:
    """Zero-based document row ordinal and its exact byte custody."""

    row_index: int
    before_sha256: str
    after_sha256: str


@dataclass(frozen=True, slots=True)
class OfficeContentReceipt:
    """Actual package bindings; counts are derived, never manuscript constants."""

    schema_version: int
    native_sha256: str
    projected_sha256: str
    native_document_sha256: str
    projected_document_sha256: str
    table_count: int
    row_count: int
    repeated_header_count: int
    changes: tuple[OfficeRowChange, ...]


@dataclass(frozen=True, slots=True)
class OfficeContentProjection:
    """New final-document bytes and the exact bounded transformation receipt."""

    docx: bytes
    receipt: OfficeContentReceipt


@dataclass(frozen=True, slots=True)
class OfficeMathReport:
    """Checks only the three declared displays and the contrasting logic pair."""

    gathered_sha256: tuple[str, ...]
    atomic_non_entailments: int
    entailments_of_negation: int


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _document_xml(payload: bytes) -> Element:
    """Keep the frozen main-XML parser's codec failures typed and cause-specific."""
    try:
        return _xml(payload, "word/document.xml")
    except (ValueError, LookupError) as exc:
        raise OfficeContentError(str(exc)) from exc


def _shape(node: Element) -> _Shape:
    return (node.tag, tuple(sorted(node.attrib.items())), node.text or "",
            tuple(_shape(child) for child in node))


def _on_off(node: Element) -> bool:
    """Parse the supported empty OOXML on/off property, including disabled headers."""
    value = node.get(W + "val", "true")
    if (node.text or len(node) or set(node.attrib) - {W + "val"}
            or value not in ("true", "1", "on", "false", "0", "off")):
        raise OfficeContentError("Malformed row on/off property")
    return value in ("true", "1", "on")


def _position(raw: bytes, marker: bytes) -> int:
    """Refuse namespace-aliased lexical forms instead of leaking bytes.index errors."""
    position = raw.find(marker)
    if position < 0:
        raise OfficeContentError("Unsupported native row property namespace/serialization")
    return position


def _metadata(row: ZipInfo) -> tuple[str | bytes | int | tuple[int, ...], ...]:
    """Preserve all public ZIP metadata except derived sizes/CRC and offsets.

    Recompression may change compressed size; payload comparison binds size/CRC.
    Header offsets and raw DOS time are derived, not independent metadata.
    """
    return (row.filename, row.orig_filename, row.date_time, row.compress_type,
            row.comment, row.extra, row.create_system, row.create_version,
            row.extract_version, row.reserved, row.flag_bits, row.volume,
            row.internal_attr, row.external_attr)


def _wire(data: bytes, parts: tuple[tuple[ZipInfo, bytes], ...]) -> None:
    """Admit complete single-disk native ZIP streams with reconciled headers."""
    end = data.rfind(b"PK\x05\x06")
    if end < 0 or end + 22 > len(data):
        raise OfficeContentError("Unsupported native ZIP end record")
    disk, directory_disk, disk_entries, entries, size, start, comment = unpack_from(
        "<4H2LH", data, end + 4)
    if disk or directory_disk or disk_entries != entries:
        raise OfficeContentError("Unsupported multi-disk ZIP archive metadata")
    if (entries != len(parts) or start + size != end or end + 22 + comment != len(data)):
        raise OfficeContentError("Unsupported native ZIP directory/end-record layout")
    with ZipFile(BytesIO(data)) as archive:
        offset = archive.start_dir
        if offset != start:
            raise OfficeContentError("Unsupported native ZIP prefix")
        ranges = []
        for row, payload in parts:
            if offset + 46 > len(data) or data[offset:offset + 4] != b"PK\x01\x02":
                raise OfficeContentError("Unsupported native central directory")
            name, extra, comment, disk = unpack_from("<HHHH", data, offset + 28)
            if disk:
                raise OfficeContentError("Unsupported multi-disk ZIP member metadata")
            local = row.header_offset
            if local < 0 or local + 30 > start or data[local:local + 4] != b"PK\x03\x04":
                raise OfficeContentError("Unsupported native local ZIP header")
            version, flags, method, time, date, crc, compressed_size, file_size, ln, le = unpack_from(
                "<5H3L2H", data, local + 4)
            central_time, central_date = unpack_from("<HH", data, offset + 12)
            if (flags & ~0x800 or (version, flags, method, time, date, crc, compressed_size, file_size)
                    != (row.extract_version | row.reserved << 8, row.flag_bits, row.compress_type,
                        central_time, central_date, row.CRC, row.compress_size, row.file_size)
                    or data[local + 30:local + 30 + ln] != data[offset + 46:offset + 46 + name]
                    or data[local + 30 + ln:local + 30 + ln + le] != row.extra):
                raise OfficeContentError(f"ZIP member metadata changed: {row.filename} (local header)")
            payload_start = local + 30 + ln + le
            payload_end = payload_start + compressed_size
            if payload_end > start:
                raise OfficeContentError("ZIP member overlaps the central directory")
            compressed = data[payload_start:payload_end]
            match _Compression(method):
                case _Compression.STORED:
                    decoded = compressed
                case _Compression.DEFLATE:
                    decoder = decompressobj(-15)
                    decoded = decoder.decompress(compressed, file_size + 1)
                    if not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
                        raise OfficeContentError(f"Incomplete or overlong DEFLATE stream: {row.filename}")
                case unreachable:
                    assert_never(unreachable)
            if len(decoded) != file_size or decoded != payload or crc32(decoded) != crc:
                raise OfficeContentError(f"ZIP actual/declared size or payload mismatch: {row.filename}")
            ranges.append((local, payload_end))
            offset += 46 + name + extra + comment
        previous = 0
        for first, last in sorted(ranges):
            if first != previous:
                raise OfficeContentError("Unsupported native ZIP gap/overlap")
            previous = last
        if previous != start or offset != end:
            raise OfficeContentError("Unsupported native ZIP directory boundary")


def _admit(data: bytes) -> _Package:
    """Combine the frozen budgeted parser with complete native wire validation."""
    try:
        package = _package(data)
    except (ValueError, OverflowError, LookupError, ZlibError, EOFError) as exc:
        # The frozen stdlib-backed parser can report malformed offsets as a
        # ValueError (negative seek) or OverflowError (unsupported ZIP64 seek).
        # Unsupported XML codec declarations can instead report LookupError.
        # Keep those input failures typed here without changing the parser.
        raise OfficeContentError(str(exc)) from exc
    try:
        _wire(data, package.parts)
    except ZlibError as exc:
        raise OfficeContentError(str(exc)) from exc
    return package


def _row_properties(props: Element) -> None:
    """Parse only on/off headers/keep-row and empty conditional style properties."""
    if props.attrib or (props.text or "").strip() or any((node.tail or "").strip() for node in props):
        raise OfficeContentError("Malformed row property character content")
    for node in props:
        try:
            kind = _RowProperty(node.tag.removeprefix(W))
        except ValueError as exc:
            raise OfficeContentError(f"Unsupported native row property: {node.tag}") from exc
        match kind:
            case _RowProperty.KEEP_ROW | _RowProperty.HEADER:
                _on_off(node)
            case _RowProperty.CONDITIONAL_STYLE:
                if node.attrib or len(node) or (node.text or "").strip():
                    raise OfficeContentError("Only empty native cnfStyle row property is supported")
            case unreachable:
                assert_never(unreachable)


def _row_insert(row: Element, raw: bytes) -> bytes:
    """Insert one on/off property in schema order; refuse deliberate split policy."""
    if any(node.tag not in (W + "trPr", W + "tc") for node in row):
        raise OfficeContentError("Unsupported native row child namespace/serialization")
    properties = row.findall(W + "trPr")
    if len(properties) > 1:
        raise OfficeContentError("Duplicate row property container")
    if not properties:
        return raw.replace(b"<w:tr>", b"<w:tr><w:trPr><w:cantSplit/></w:trPr>", 1)
    props = properties[0]
    if any(not node.tag.startswith(W) for node in props):
        raise OfficeContentError("Unsupported row property namespace/serialization")
    names = [node.tag.removeprefix(W) for node in props]
    if (any(name not in _PROPERTY_ORDER for name in names) or len(set(names)) != len(names)
            or names != sorted(names, key=_PROPERTY_ORDER.index)):
        raise OfficeContentError("Unsupported row property ordering")
    _row_properties(props)
    if any(re.search(rb"<w:" + name.encode() + rb"(?=[\s/>])", raw) is None for name in names):
        raise OfficeContentError("Unsupported native row property namespace/serialization")
    current = props.find(W + "cantSplit")
    if current is not None:
        if not _on_off(current):
            raise OfficeContentError("Explicit split policy")
        return raw
    marker = b"<w:trPr>"
    if marker not in raw:
        raise OfficeContentError("Unsupported native row property syntax")
    preceding = [name for name in names if _PROPERTY_ORDER.index(name) < 6]
    offset = _position(raw, marker) + len(marker)
    if preceding:
        following = [name for name in names if _PROPERTY_ORDER.index(name) > 6]
        marker = (b"<w:" + following[0].encode()) if following else b"</w:trPr>"
        offset = _position(raw, marker)
    return raw[:offset] + b"<w:cantSplit/>" + raw[offset:]


def _document_projection(document: bytes) -> tuple[bytes, tuple[OfficeRowChange, ...]]:
    """Splice exact native row spans after matching them to the parsed document."""
    root = _document_xml(document)
    if b"<!--" in document or b"<![CDATA[" in document:
        raise OfficeContentError("Comments/CDATA are outside the supported native serialization")
    if root.tag != W + "document":
        raise OfficeContentError("Unsupported main-document namespace")
    rows = tuple(root.iter(W + "tr"))
    tables = tuple(root.iter(W + "tbl"))
    if (rows != tuple(row for table in tables for row in table.findall(W + "tr"))
            or any(table.findall(".//" + W + "tbl") for table in tables)
            or any(row.findall(".//" + W + tag)
                   for row in rows for tag in ("vMerge", "hMerge", "gridSpan", "drawing", "pict", "object"))):
        raise OfficeContentError("Only ordinary unmerged text table rows are supported")
    matches = tuple(_ROWS.finditer(document))
    opening = re.search(rb"<w:document\b[^>]*>", document)
    if opening is None or len(rows) != len(matches):
        raise OfficeContentError("Unsupported native row serialization")
    chunks: list[bytes] = []
    changes: list[OfficeRowChange] = []
    end = 0
    for index, (row, match) in enumerate(zip(rows, matches, strict=True)):
        raw = match.group()
        fragment = _xml(opening.group() + raw + b"</w:document>", "row span")
        if len(fragment) != 1 or _shape(fragment[0]) != _shape(row):
            raise OfficeContentError("Native row span does not match the parsed document")
        result = _row_insert(row, raw)
        chunks.extend((document[end:match.start()], result))
        if result != raw:
            changes.append(OfficeRowChange(index, _digest(raw), _digest(result)))
        end = match.end()
    return b"".join((*chunks, document[end:])), tuple(changes)


def project_office_content(native_docx: bytes) -> OfficeContentProjection:
    """Return final bytes with every ordinary row kept intact; perform no I/O."""
    try:
        package = _admit(native_docx)
        document, _ = _document_projection(package.document)
        target = BytesIO()
        with ZipFile(target, "w") as archive:
            archive.comment = package.comment
            for row, payload in package.parts:
                flags = row.flag_bits
                if flags & ~0x800:
                    raise OfficeContentError("Unsupported native ZIP flags")
                attributes = row.external_attr
                archive.writestr(row, document if row.filename == "word/document.xml" else payload)
                # ZipFile substitutes permissions for zero; restore the actual
                # native central-directory attributes before writing that directory.
                row.external_attr = attributes
                row.flag_bits = flags
                # ZipFile clears the UTF-8 flag for ASCII filenames. Keep the
                # local header and central directory faithful to native metadata.
                position = target.tell()
                target.seek(row.header_offset + 6)
                target.write(flags.to_bytes(2, "little"))
                target.seek(position)
        projected = target.getvalue() if document != package.document else native_docx
        receipt = verify_office_content_projection(native_docx, projected)
        return OfficeContentProjection(projected, receipt)
    except (OfficePagePolicyError, LookupError, ZlibError, UnicodeDecodeError, EOFError) as exc:
        raise OfficeContentError(str(exc)) from exc


def verify_office_content_projection(native_docx: bytes, projected_docx: bytes) -> OfficeContentReceipt:
    """Reconstruct permitted inserts and reject every other XML/member mutation."""
    try:
        native, projected = _admit(native_docx), _admit(projected_docx)
        expected, changes = _document_projection(native.document)
        if projected.document != expected:
            raise OfficeContentError("Final document differs from the permitted row projection")
        if (native.comment != projected.comment
                or [r.filename for r, _ in native.parts] != [r.filename for r, _ in projected.parts]):
            raise OfficeContentError("ZIP member inventory/order or archive comment changed")
        for (before, data), (after, payload) in zip(native.parts, projected.parts, strict=True):
            if before.filename != "word/document.xml" and data != payload:
                raise OfficeContentError(f"Non-target ZIP payload changed: {before.filename}")
            if _metadata(before) != _metadata(after):
                raise OfficeContentError(f"ZIP member metadata changed: {before.filename}")
        root = _document_xml(projected.document)
        for row in root.iter(W + "tr"):
            policy = row.findall(W + "trPr/" + W + "cantSplit")
            if len(policy) != 1 or not _on_off(policy[0]):
                raise OfficeContentError("Actual final row lacks enabled cantSplit")
        return OfficeContentReceipt(1, _digest(native_docx), _digest(projected_docx),
                                    _digest(native.document), _digest(projected.document),
                                    len(tuple(root.iter(W + "tbl"))),
                                    len(tuple(root.iter(W + "tr"))),
                                    sum(_on_off(node) for row in root.iter(W + "tr")
                                        for node in row.findall(W + "trPr/" + W + "tblHeader")), changes)
    except (OfficePagePolicyError, LookupError, ZlibError, UnicodeDecodeError, EOFError) as exc:
        raise OfficeContentError(str(exc)) from exc


def _display_matrix(math: Element) -> str:
    """Bind the entire display, allowing only the exact native number suffix."""
    children = tuple(math)
    if math.attrib or math.text or len(children) not in (1, 5) or children[0].tag != M + "m":
        raise OfficeContentError("Unexpected content surrounding a gathered display")
    if len(children) == 5:
        number = children[3].find(M + "t")
        number_text = "" if number is None else number.text or ""
        if re.fullmatch(r"[1-9][0-9]*", number_text) is None:
            raise OfficeContentError("Unsupported native equation number")
        suffix = ('<m:oMath xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">'
                  '<m:r><m:t>\u2001\u2001</m:t></m:r><m:r><m:rPr><m:sty m:val="p"/></m:rPr>'
                  '<m:t>(</m:t></m:r><m:r><m:t>' + number_text + '</m:t></m:r>'
                  '<m:r><m:rPr><m:sty m:val="p"/></m:rPr><m:t>)</m:t></m:r></m:oMath>')
        expected = _xml(suffix.encode(), "native number suffix")
        if tuple(_shape(node) for node in children[1:]) != tuple(_shape(node) for node in expected):
            raise OfficeContentError("Unexpected content in native number suffix")
    return _digest(repr(_shape(children[0])).encode())


def _display_envelopes(root: Element) -> tuple[Element, ...]:
    """Admit only the pinned writer's single-expression centered display hosts."""
    parents = {child: parent for parent in root.iter() for child in parent}
    properties: _Shape = (M + "oMathParaPr", (), "", (
        (M + "jc", ((M + "val", "center"),), "", ()),))
    displays: list[Element] = []
    for paragraph in root.iter(M + "oMathPara"):
        nodes = tuple(paragraph)
        host = parents.get(paragraph)
        if (paragraph.attrib or len(nodes) != 2 or _shape(nodes[0]) != properties
                or nodes[1].tag != M + "oMath" or host is None or host.tag != W + "p"
                or len(host.findall(M + "oMathPara")) != 1
                or len(tuple(host.iter(M + "oMath"))) != 1
                or any(node.tag not in (W + "pPr", W + "bookmarkStart", W + "bookmarkEnd",
                                        M + "oMathPara") for node in host)
                or (host.text or "").strip() or any((node.tail or "").strip() for node in host)):
            raise OfficeContentError("Unsupported native display envelope")
        if any((node.tail or "").strip() or
               (node.tag != M + "t" and (node.text or "").strip()) for node in paragraph.iter()):
            raise OfficeContentError("Unsupported math character content outside m:t")
        displays.append(nodes[1])
    return tuple(displays)


def verify_office_content_math(docx: bytes) -> OfficeMathReport:
    """Require the exact supported gathered structures and atomic relation pair.

    This rejects changed operators/bounds/scripts, literal alignment glyphs and
    combining negation. It is intentionally specific to this manuscript's three
    equations, not a general LaTeX or scientific-validity verifier.
    """
    try:
        root = _document_xml(_admit(docx).document)
    except (OfficePagePolicyError, LookupError, ZlibError, UnicodeDecodeError, EOFError) as exc:
        raise OfficeContentError(str(exc)) from exc
    text = "".join(node.text or "" for node in root.iter(M + "t"))
    maths = tuple(root.iter(M + "oMath"))
    displays = _display_envelopes(root)
    for math in maths:
        if any((node.tail or "").strip() or
               (node.tag != M + "t" and (node.text or "").strip()) for node in math.iter()):
            raise OfficeContentError("Unsupported math character content outside m:t")
    gathered = tuple(math for math in maths if math.find(".//" + M + "m") is not None)
    if any(math not in displays for math in gathered):
        raise OfficeContentError("Gathered math requires a native display envelope")
    matrices = tuple(_display_matrix(math) for math in gathered)
    if len(tuple(root.iter(M + "m"))) != len(matrices):
        raise OfficeContentError("Gathered matrices must belong to complete display expressions")
    if "&" in text or "\u0338" in text or matrices not in (_GATHERED, _FULL_GATHERED):
        raise OfficeContentError("Repaired math structures changed or contain alignment/negation glyphs")
    relations = tuple(_digest(repr(_shape(math)).encode()) for math in maths
                      if "".join(n.text or "" for n in math.iter(M + "t")) in ("T⊭q", "T⊨¬q"))
    if relations != _RELATIONS or text.count("⊭") != 1:
        raise OfficeContentError("Atomic non-entailment and entailment-of-negation pair must be distinct")
    return OfficeMathReport(matrices, 1, 1)

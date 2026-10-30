"""Real Pandoc/package controls for the bounded final-Word projection.

SIZE_OK: the assigned ownership permits one test module only.
"""

from __future__ import annotations

import re
import subprocess
from collections.abc import Callable
from io import BytesIO
from pathlib import Path
from struct import pack, pack_into, unpack_from
from xml.etree.ElementTree import Element, SubElement, fromstring, tostring
from zipfile import ZipFile, ZipInfo
from zlib import decompressobj

import pytest

from rikishi.publication_office_content import (
    OfficeContentError,
    OfficeContentProjection,
    OfficeMathReport,
    project_office_content,
    verify_office_content_math,
    verify_office_content_projection,
)

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
MATH = r"""$$
\begin{gathered}
\mathcal{R}_r = \{v\in V_r:\deg_r^{+}(v)=0\},\\
\mathcal{M}_r = \{v\in V_r:\deg_r^{+}(v)>1\},\\
\mathcal{C}_r = \{S\in\operatorname{SCC}(V_r,E_r):
 \lvert S\rvert>1\;\lor\;\exists v\in S\;(v,v)\in E_r\}.
\end{gathered}
$$

$$
\begin{gathered}
F(q)=-H(q)-\mathbb E_q[\log p(s,o)]\\
F(q)=D_{\mathrm{KL}}(q\Vert p)-\mathbb E_q[\log\ell(s)]\\
F(q)=D_{\mathrm{KL}}(q\Vert p(\cdot\mid o))-\log Z.
\end{gathered}
$$

$$
\begin{gathered}
H_L(a)=\sum_s\operatorname{negMulLog}(a_s),\\
C_L(a,b)=-\sum_s a_s\log b_s,\\
D_L(a,b)=\sum_s b_s\operatorname{klFun}(a_s/b_s).
\end{gathered}
$$

Non-entailment $T\nvDash q$. Distinct $T\models\neg q$.
"""
TABLES = """
| Class | Meaning |
| --- | --- |
| α | finite state |
| β | conditional likelihood |

| Role | Scope |
| --- | --- |
| γ | source identity |
"""
CONTEXT_CORE = r"""$$
\begin{gathered}
\operatorname{disjoint}(T,U),\quad I(t,T),\quad I(t,U),\\
\forall C,D\;\left(\operatorname{disjoint}(C,D)\Rightarrow
\neg\exists x\,[I(x,C)\land I(x,D)]\right).
\end{gathered}
$$"""
CONTEXT_LOG = r"""$$
\begin{gathered}
b_*=\max_{s\in T} b_s,\qquad r_s=a_s+(b_s-b_*),\qquad
r_*=\max_{s\in T}r_s,\\
L=\log\sum_{s\in T}\exp(r_s-r_*),\\
\log Z=b_*+r_*+L,\qquad
\log p(s\mid o)=r_s-r_*-L.
\end{gathered}
$$"""


def payload(data: bytes, name: str = "word/document.xml") -> bytes:
    with ZipFile(BytesIO(data)) as archive:
        return archive.read(name)


def replace(data: bytes, name: str, replacement: bytes) -> bytes:
    target = BytesIO()
    with ZipFile(BytesIO(data)) as original, ZipFile(target, "w") as changed:
        changed.comment = original.comment
        for row in original.infolist():
            write_member(target, changed, (row, replacement if row.filename == name else original.read(row)))
    return target.getvalue()


def write_member(target: BytesIO, archive: ZipFile, member: tuple[ZipInfo, bytes]) -> None:
    """Keep independent ZIP metadata exact when constructing a single-mutation control."""
    row, data = member
    flags, attributes = row.flag_bits, row.external_attr
    archive.writestr(row, data)
    row.flag_bits, row.external_attr = flags, attributes
    position = target.tell()
    target.seek(row.header_offset + 6)
    target.write(flags.to_bytes(2, "little"))
    target.seek(position)


def native(tmp_path: Path, markdown: str) -> bytes:
    path = tmp_path / "fixture.md"
    path.write_text(markdown)
    output = tmp_path / "fixture.docx"
    subprocess.run(["pandoc", "-f", "markdown", "-t", "docx", str(path), "-o", str(output)],
                   check=True, capture_output=True, text=True, timeout=20)
    return output.read_bytes()


@pytest.fixture
def package(tmp_path: Path) -> bytes:
    return native(tmp_path, TABLES + "\n" + MATH)


def test_projection_keeps_every_native_row_and_preserves_other_bytes(package: bytes) -> None:
    # Given a real package with two ordinary tables and the repaired math.
    original_xml = payload(package)
    original_root = fromstring(original_xml)
    # When projecting final-document row policy.
    result = project_office_content(package)
    # Then every row is intact, repeated headers survive, and all other bytes survive.
    xml = payload(result.docx)
    root = fromstring(xml)
    assert result.receipt.row_count == 5
    assert result.receipt.table_count == 2
    assert result.receipt.repeated_header_count == 2
    assert len(result.receipt.changes) == 5
    assert len(root.findall(".//" + W + "cantSplit")) == 5
    assert xml.replace(b"<w:cantSplit/>", b"").replace(b"<w:trPr></w:trPr>", b"") == original_xml
    assert list(original_root.itertext()) == list(root.itertext())
    assert verify_office_content_math(result.docx).atomic_non_entailments == 1


def test_verifier_reconstructs_exact_projection(package: bytes) -> None:
    # Given independently retained native/final bytes.
    result = project_office_content(package)
    # When independently verifying their allowed difference.
    receipt = verify_office_content_projection(package, result.docx)
    # Then the complete receipt is reproducible.
    assert receipt == result.receipt


@pytest.mark.parametrize("before,after", [
    (b"<m:t>=</m:t>", b"<m:t>\xe2\x89\xa0</m:t>"),
    (b'm:val="\xe2\x88\x91"', b'm:val="\xe2\x88\x8f"'),
    (b'm:val="script"', b'm:val="double-struck"'),
    ("⊭".encode(), "⊨".encode()),
    (b"<m:t>=</m:t>", b"<m:t>&amp;=</m:t>"),
])
def test_math_checker_rejects_real_semantic_or_alignment_mutation(
    package: bytes, before: bytes, after: bytes,
) -> None:
    # Given an actual native OMML mutation, including operator attributes.
    xml = payload(package)
    assert before in xml
    changed = replace(package, "word/document.xml", xml.replace(before, after, 1))
    # When checking actual mathematical serialization.
    with pytest.raises(OfficeContentError):
        verify_office_content_math(changed)
    # Then the malformed/changed relation or display cannot pass.


def test_original_aligned_and_combining_negation_fail(tmp_path: Path) -> None:
    # Given the original source forms rendered by real Pandoc.
    source = MATH.replace("{gathered}", "{aligned}").replace("=", "&=")
    source = source.replace(r"\nvDash", r"\not\models")
    docx = native(tmp_path, source)
    # When checking the bad native representation.
    with pytest.raises(OfficeContentError, match="math structures"):
        verify_office_content_math(docx)
    # Then the originally observed class of failure is rejected.


@pytest.mark.parametrize("name,before,after", [
    ("word/document.xml", b"finite state", b"infinite state"),
    ("word/document.xml", b"<w:cantSplit/>", b"<w:cantSplit w:val=\"false\"/>"),
    ("word/document.xml", b"<w:tblHeader", b"<w:otherHeader"),
    ("word/styles.xml", b"Normal", b"Changed"),
])
def test_custody_verifier_rejects_unapproved_changes(
    package: bytes, name: str, before: bytes, after: bytes,
) -> None:
    # Given final bytes whose row/text/style payload was subsequently changed.
    projected = project_office_content(package).docx
    data = payload(projected, name)
    assert before in data
    changed = replace(projected, name, data.replace(before, after, 1))
    # When comparing to the actual native input.
    with pytest.raises(OfficeContentError):
        verify_office_content_projection(package, changed)
    # Then a changed scientific or non-target payload cannot pass custody.


@pytest.mark.parametrize("fragment,error", [
    (b'<w:trPr><w:cantSplit w:val="false"/></w:trPr>', "Explicit split"),
    (b'<w:trPr><w:tblHeader/><w:cnfStyle/></w:trPr>', "ordering"),
    (b'<w:trPr><w:unknown/></w:trPr>', "ordering"),
    (b'<w:trPr/><w:trPr/>', "Duplicate row"),
    (b'<w:trPr/>', "property syntax"),
    (b'<w:tc><w:tcPr><w:vMerge/></w:tcPr></w:tc>', "ordinary"),
    ((b'<w:tc><w:tcPr><w:hMerge w:val="restart"/></w:tcPr></w:tc>'
      b'<w:tc><w:tcPr><w:hMerge/></w:tcPr></w:tc>'), "ordinary"),
    (b'<w:tc><w:tcPr><w:gridSpan w:val="2"/></w:tcPr></w:tc>', "ordinary"),
    (b'<w:tc><w:p><w:r><w:drawing/></w:r></w:p></w:tc>', "ordinary"),
    (b'<w:tc><w:tbl/></w:tc>', "ordinary"),
])
def test_unsupported_row_contract_fails_explicitly(
    package: bytes, fragment: bytes, error: str,
) -> None:
    # Given an actual package with a nonordinary row or explicit split policy.
    assert b"<w:tr><w:tc>" in payload(package)
    xml = payload(package).replace(b"<w:tr><w:tc>", b"<w:tr>" + fragment + b"<w:tc>", 1)
    changed = replace(package, "word/document.xml", xml)
    # When requesting the bounded projection.
    with pytest.raises(OfficeContentError, match=error):
        project_office_content(changed)
    # Then unsupported input never silently falls back.


def test_projection_is_idempotent(package: bytes) -> None:
    # Given a package already carrying the required policy.
    first = project_office_content(package)
    # When projecting it again.
    second = project_office_content(first.docx)
    # Then every byte stays exact and the change inventory is empty.
    assert second.docx == first.docx
    assert second.receipt.changes == ()


def test_no_tables_is_exact_identity(tmp_path: Path) -> None:
    # Given ordinary native prose without any table.
    docx = native(tmp_path, "Text with $x^2$ and α.\n")
    # When projecting rows.
    result = project_office_content(docx)
    # Then no archive bytes are gratuitously rewritten.
    assert result.docx == docx
    assert result.receipt.row_count == 0


@pytest.mark.parametrize("data", [b"not a ZIP", b"PK\x03\x04"])
def test_malformed_package_has_typed_error(data: bytes) -> None:
    # Given an unreadable actual package.
    # When entering the byte boundary.
    with pytest.raises(OfficeContentError, match="ZIP"):
        project_office_content(data)
    # Then the caller receives the declared typed failure.


@pytest.mark.parametrize("properties", [b'<w:cnfStyle/>', b'<w:cnfStyle/><w:tblHeader/>'])
def test_existing_properties_keep_their_order(package: bytes, properties: bytes) -> None:
    # Given a native row carrying properties before and optionally after cantSplit.
    xml = payload(package).replace(b"<w:tr><w:tc>", b"<w:tr><w:trPr>" + properties +
                                   b"</w:trPr><w:tc>", 1)
    docx = replace(package, "word/document.xml", xml)
    # When projecting the keep-row policy.
    result = project_office_content(docx)
    # Then cantSplit is inserted after cnfStyle in schema order.
    assert b"<w:cnfStyle/><w:cantSplit/>" in payload(result.docx)


@pytest.mark.parametrize("before,after,error", [
    (b"<w:tr>", b'<w:tr w:rsidR="1">', "serialization"),
    (b"<w:tr>", b"<w:tr", "malformed"),
    (b"wordprocessingml/2006/main", b"wordprocessingml/2006/other", "namespace"),
])
def test_unsupported_document_serialization_fails(
    package: bytes, before: bytes, after: bytes, error: str,
) -> None:
    # Given a malformed or unsupported real native XML serialization.
    xml = payload(package).replace(before, after, 1)
    docx = replace(package, "word/document.xml", xml)
    # When requesting the bounded projection.
    with pytest.raises(OfficeContentError, match=error):
        project_office_content(docx)
    # Then the boundary reports the specific unsupported form.


def test_zip_inventory_mutation_is_rejected(package: bytes) -> None:
    # Given final bytes with an added non-target member.
    data = BytesIO(project_office_content(package).docx)
    with ZipFile(data, "a") as archive:
        archive.writestr("unexpected.bin", b"extra")
    # When independently verifying custody.
    with pytest.raises(OfficeContentError, match="inventory/order"):
        verify_office_content_projection(package, data.getvalue())
    # Then the member cannot hide behind unchanged document XML.


def test_atomic_relation_with_combining_slash_is_rejected(package: bytes) -> None:
    # Given actual OMML with a detached combining-negation representation.
    xml = payload(package).replace("⊭".encode(), "⊨\u0338".encode())
    docx = replace(package, "word/document.xml", xml)
    # When checking the repaired mathematical representation.
    with pytest.raises(OfficeContentError, match="negation glyphs"):
        verify_office_content_math(docx)
    # Then combining negation is rejected independently of alignment syntax.


def test_complete_display_rejects_appended_mathematical_content(package: bytes) -> None:
    # Given a changed expression outside an otherwise correct matrix fingerprint.
    xml = payload(package).replace(b"</m:m>", b"</m:m><m:r><m:t>+1</m:t></m:r>", 1)
    changed = replace(package, "word/document.xml", xml)
    # When checking the complete repaired displays.
    with pytest.raises(OfficeContentError, match="surrounding"):
        verify_office_content_math(changed)
    # Then content surrounding a correct matrix cannot change the expression.


def test_relation_moved_into_superscript_is_rejected(package: bytes) -> None:
    # Given the reviewer's changed structure with identical flattened math text.
    m = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"
    root = fromstring(payload(package))
    relation = next(node for node in root.iter(m + "oMath")
                    if "".join(node.itertext()) == "T⊭q")
    base, operator, query = tuple(relation)
    relation.clear()
    superscript = Element(m + "sSup")
    SubElement(superscript, m + "e").append(base)
    SubElement(superscript, m + "sup").append(operator)
    relation.extend((superscript, query))
    changed = replace(package, "word/document.xml", tostring(root))
    # When checking the actual relation structure.
    with pytest.raises(OfficeContentError, match="pair"):
        verify_office_content_math(changed)
    # Then flattened text alone cannot authenticate the relation.


def test_native_multidigit_number_suffix_is_supported(package: bytes) -> None:
    # Given the exact native suffix around an unchanged display, with two digits.
    suffix = ('<m:r><m:t>\u2001\u2001</m:t></m:r><m:r><m:rPr><m:sty m:val="p"/>'
              '</m:rPr><m:t>(</m:t></m:r><m:r><m:t>12</m:t></m:r>'
              '<m:r><m:rPr><m:sty m:val="p"/></m:rPr><m:t>)</m:t></m:r>').encode()
    xml = payload(package).replace(b"</m:m>", b"</m:m>" + suffix)
    changed = replace(package, "word/document.xml", xml)
    # When checking complete display structures.
    report = verify_office_content_math(changed)
    # Then numbering is allowed without permitting arbitrary appended math.
    assert len(report.gathered_sha256) == 3


def test_comment_property_decoy_is_rejected(package: bytes) -> None:
    # Given the exact review counterexample that formerly hid cantSplit in a comment.
    xml = payload(package).replace(b"<w:trPr>",
              b"<w:trPr><w:cnfStyle/><!-- <w:tblHeader /> -->", 1)
    changed = replace(package, "word/document.xml", xml)
    # When requesting a bounded native projection.
    with pytest.raises(OfficeContentError, match="Comments/CDATA"):
        project_office_content(changed)
    # Then comment markers cannot be mistaken for actual property offsets.


def test_namespace_aliased_property_has_typed_failure(package: bytes) -> None:
    # Given a valid namespace alias in an unsupported native lexical form.
    xml = payload(package).replace(b"<w:document ", b'<w:document xmlns:x="' +
              W[1:-1].encode() + b'" ', 1)
    xml = xml.replace(b"<w:tblHeader", b"<w:cnfStyle/><x:tblHeader", 1)
    changed = replace(package, "word/document.xml", xml)
    # When finding the insertion offset after cnfStyle.
    with pytest.raises(OfficeContentError, match="namespace/serialization"):
        project_office_content(changed)
    # Then bytes.index never leaks a plain ValueError.


@pytest.mark.parametrize("attribute,value", [
    ("internal_attr", 1), ("create_system", 3), ("create_version", 63),
    ("extract_version", 63), ("reserved", 1),
])
def test_all_independent_zip_metadata_is_bound(
    package: bytes, attribute: str, value: int,
) -> None:
    # Given a final archive with payloads unchanged but a preserved metadata field changed.
    final = project_office_content(package).docx
    target = BytesIO()
    with ZipFile(BytesIO(final)) as source, ZipFile(target, "w") as changed:
        for row in source.infolist():
            data = source.read(row)
            if row.filename == "word/styles.xml":
                assert getattr(row, attribute) != value
                setattr(row, attribute, value)
            write_member(target, changed, (row, data))
    # When verifying native/final custody.
    with pytest.raises(OfficeContentError, match="metadata changed: word/styles.xml"):
        verify_office_content_projection(package, target.getvalue())
    # Then unchanged payloads cannot hide independent metadata changes.


def test_corrupted_deflate_has_typed_failure(package: bytes) -> None:
    # Given a real ZIP local payload with an invalid reserved deflate block type.
    with ZipFile(BytesIO(package)) as archive:
        row = archive.getinfo("word/document.xml")
        offset = row.header_offset + 30 + len(row.filename.encode()) + len(row.extra)
    changed = bytearray(package)
    changed[offset] = (changed[offset] & 0xF8) | 0x07
    # When the actual decompressor crosses the byte boundary.
    with pytest.raises(OfficeContentError, match="invalid block type"):
        project_office_content(bytes(changed))
    # Then zlib.error is normalized without changing the frozen package parser.


def test_character_content_in_cant_split_is_rejected(package: bytes) -> None:
    # Given malformed property character content rather than an empty on/off element.
    final = project_office_content(package).docx
    xml = payload(final).replace(b"<w:cantSplit/>", b"<w:cantSplit>false</w:cantSplit>", 1)
    changed = replace(final, "word/document.xml", xml)
    # When checking whether the existing policy can be retained.
    with pytest.raises(OfficeContentError, match="Malformed row"):
        project_office_content(changed)
    # Then text content is never interpreted as an enabled policy.


def test_header_count_includes_only_enabled_properties(package: bytes) -> None:
    # Given two native header properties, one explicitly disabled.
    xml = payload(package).replace(b'<w:tblHeader w:val="on" />',
                                   b'<w:tblHeader w:val="false"/>', 1)
    assert xml != payload(package)
    changed = replace(package, "word/document.xml", xml)
    # When projecting and deriving the actual repeated-header count.
    result = project_office_content(changed)
    # Then the disabled property is preserved but not reported as active.
    assert result.receipt.repeated_header_count == 1


def test_complete_shared_body_gathered_context_is_source_derived(tmp_path: Path) -> None:
    # Given all five literal source displays, including both unchanged context displays.
    taxonomy, objective, information, relations = MATH.strip().split("\n\n")
    source = (f"{taxonomy}\n\n{CONTEXT_CORE}\n\n{objective}\n\n{CONTEXT_LOG}"
              f"\n\n{information}\n\n{relations}")
    docx = native(tmp_path, source)
    # When checking the real complete-context native mathematical serialization.
    report = verify_office_content_math(docx)
    # Then the repaired displays retain the same identities within the larger body.
    assert len(report.gathered_sha256) == 5


def test_context_display_operator_mutation_is_rejected(tmp_path: Path) -> None:
    # Given the complete supported context with one altered quantifier.
    taxonomy, objective, information, relations = MATH.strip().split("\n\n")
    source = "\n\n".join((taxonomy, CONTEXT_CORE.replace(r"\forall", r"\exists"),
                           objective, CONTEXT_LOG, information, relations))
    docx = native(tmp_path, source)
    # When checking mathematical structure.
    with pytest.raises(OfficeContentError, match="math structures"):
        verify_office_content_math(docx)
    # Then unknown context hashes are never silently admitted.


def test_nonzero_disk_metadata_is_rejected_on_the_wire(package: bytes) -> None:
    # Given a genuine central-directory mutation ignored by ZipInfo.volume.
    final = project_office_content(package).docx
    with ZipFile(BytesIO(final)) as archive:
        offset = archive.start_dir
        for row in archive.infolist():
            if row.filename == "word/styles.xml":
                break
            name, extra, comment = unpack_from("<HHH", final, offset + 28)
            offset += 46 + name + extra + comment
    changed = bytearray(final)
    changed[offset + 34:offset + 36] = b"\x01\x00"
    # When verifying metadata custody against the original native package.
    with pytest.raises(OfficeContentError, match="multi-disk ZIP member metadata"):
        verify_office_content_projection(package, bytes(changed))
    # Then an unsupported nonzero disk field cannot disappear during parsing.


def central_members(data: bytes) -> tuple[tuple[ZipInfo, int], ...]:
    """Locate actual central headers for wire-level mutation controls."""
    result = []
    with ZipFile(BytesIO(data)) as archive:
        offset = archive.start_dir
        for row in archive.infolist():
            result.append((row, offset))
            name, extra, comment = unpack_from("<HHH", data, offset + 28)
            offset += 46 + name + extra + comment
    return tuple(result)


def incomplete_deflate(data: bytes) -> bytes:
    """Replace a real member by a payload-identical nonfinal DEFLATE stored block."""
    row, _central = next(item for item in central_members(data)
                        if item[0].filename == "word/styles.xml")
    decoded = payload(data, row.filename)
    assert len(decoded) < 65536
    name, extra = unpack_from("<HH", data, row.header_offset + 26)
    start = row.header_offset + 30 + name + extra
    stream = b"\x00" + pack("<HH", len(decoded), 65535 - len(decoded)) + decoded
    decoder = decompressobj(-15)
    assert decoder.decompress(stream) == decoded and not decoder.eof
    delta = len(stream) - row.compress_size
    changed = bytearray(data[:start] + stream + data[start + row.compress_size:])
    pack_into("<L", changed, row.header_offset + 18, len(stream))
    for member, offset in central_members(data):
        offset += delta
        if member.filename == row.filename:
            pack_into("<L", changed, offset + 20, len(stream))
        if member.header_offset > row.header_offset:
            pack_into("<L", changed, offset + 42, member.header_offset + delta)
    end = data.rfind(b"PK\x05\x06")
    directory = unpack_from("<L", data, end + 16)[0]
    pack_into("<L", changed, end + delta + 16, directory + delta)
    assert payload(bytes(changed), row.filename) == decoded
    return bytes(changed)


@pytest.mark.parametrize("entrypoint", [project_office_content, verify_office_content_math])
def test_incomplete_deflate_is_rejected_at_each_boundary(
    package: bytes, entrypoint: Callable[[bytes], OfficeContentProjection | OfficeMathReport],
) -> None:
    # Given the exact review control with unchanged decoded payload but no end marker.
    changed = incomplete_deflate(package)
    # When entering either producer or math admission.
    with pytest.raises(OfficeContentError, match="DEFLATE"):
        entrypoint(changed)
    # Then successful ZipFile.read alone cannot admit an unfinished stream.


def test_incomplete_deflate_final_is_rejected(package: bytes) -> None:
    # Given a final package with a payload-identical unfinished compressed member.
    changed = incomplete_deflate(project_office_content(package).docx)
    # When verifying it against the native input.
    with pytest.raises(OfficeContentError, match="DEFLATE"):
        verify_office_content_projection(package, changed)
    # Then the custody gate checks real stream completion too.


def test_incorrect_declared_uncompressed_size_is_rejected(package: bytes) -> None:
    # Given matching local/central declarations one byte larger than the real payload.
    row, offset = next(item for item in central_members(package)
                       if item[0].filename == "word/styles.xml")
    changed = bytearray(package)
    pack_into("<L", changed, row.header_offset + 22, row.file_size + 1)
    pack_into("<L", changed, offset + 24, row.file_size + 1)
    assert payload(bytes(changed), row.filename) == payload(package, row.filename)
    # When admitting the package.
    with pytest.raises(OfficeContentError, match="size"):
        project_office_content(bytes(changed))
    # Then successful extraction does not authenticate declared sizes.


@pytest.mark.parametrize("offset,value", [(6, 0), (6, 2049), (8, 0)])
def test_contradictory_local_header_is_rejected(package: bytes, offset: int, value: int) -> None:
    # Given unchanged central metadata/payload and a contradictory local field.
    final = project_office_content(package).docx
    row = next(item[0] for item in central_members(final) if item[0].filename == "word/styles.xml")
    changed = bytearray(final)
    pack_into("<H", changed, row.header_offset + offset, value)
    assert payload(bytes(changed), row.filename) == payload(final, row.filename)
    # When verifying actual archive custody.
    with pytest.raises(OfficeContentError, match="metadata"):
        verify_office_content_projection(package, bytes(changed))
    # Then local flags/encryption/method cannot contradict the central directory.


@pytest.mark.parametrize("offset", [4, 6])
def test_archive_disk_fields_are_rejected(package: bytes, offset: int) -> None:
    # Given a nonzero end-record disk field ignored by ordinary extraction.
    changed = bytearray(package)
    pack_into("<H", changed, package.rfind(b"PK\x05\x06") + offset, 1)
    # When admitting the archive.
    with pytest.raises(OfficeContentError, match="disk"):
        project_office_content(bytes(changed))
    # Then unsupported multi-disk archive metadata cannot pass.


@pytest.mark.parametrize("fragment", [
    b'<w:pict><v:rect xmlns:v="urn:schemas-microsoft-com:vml"/></w:pict>',
    b'<w:object/>',
])
def test_legacy_graphics_rows_are_rejected(package: bytes, fragment: bytes) -> None:
    # Given a legacy graphical object in an otherwise ordinary row paragraph.
    xml = payload(package).replace(b"<w:tr><w:tc>", b"<w:tr><w:tc><w:p><w:r>" +
                                   fragment + b"</w:r></w:p>", 1)
    changed = replace(package, "word/document.xml", xml)
    # When selecting the ordinary-text-row policy.
    with pytest.raises(OfficeContentError, match="ordinary"):
        project_office_content(changed)
    # Then VML/OLE objects cannot bypass the modern-drawing restriction.


@pytest.mark.parametrize("fragment", [
    b'<w:cnfStyle><w:unknown/></w:cnfStyle>',
    b'<w:trHeight w:val="not-an-integer"/>',
    b'<w:cantSplit/>false',
    b'false<w:cantSplit/>',
])
def test_malformed_row_property_contents_are_rejected(package: bytes, fragment: bytes) -> None:
    # Given the review's malformed recognized properties or stray character content.
    xml = payload(package).replace(b"<w:tr><w:tc>", b"<w:tr><w:trPr>" +
                                   fragment + b"</w:trPr><w:tc>", 1)
    changed = replace(package, "word/document.xml", xml)
    # When parsing supported row properties.
    with pytest.raises(OfficeContentError, match="row property"):
        project_office_content(changed)
    # Then a recognized element name does not establish supported content.


def test_historical_row_properties_are_explicitly_unsupported(package: bytes) -> None:
    # Given a revision history containing a header on a current ordinary body row.
    fragment = b'<w:trPr><w:trPrChange><w:trPr><w:tblHeader/></w:trPr></w:trPrChange></w:trPr>'
    xml = payload(package).replace(b"<w:tr><w:tc>", b"<w:tr>" + fragment + b"<w:tc>", 1)
    changed = replace(package, "word/document.xml", xml)
    # When admitting the bounded native row contract.
    with pytest.raises(OfficeContentError, match="row property"):
        project_office_content(changed)
    # Then unsupported revisions cannot inflate the current-header receipt.


@pytest.mark.parametrize("marker", [b"</m:m>", b"</m:t>"])
def test_math_character_tails_are_rejected(package: bytes, marker: bytes) -> None:
    # Given unsupported character content omitted by the old structural shape.
    xml = payload(package).replace(marker, marker + b"+1", 1)
    changed = replace(package, "word/document.xml", xml)
    # When checking actual math syntax.
    with pytest.raises(OfficeContentError, match="character content"):
        verify_office_content_math(changed)
    # Then unchanged protected hashes cannot hide nonwhitespace XML tails.


def test_stored_native_package_is_a_real_positive_control(package: bytes) -> None:
    # Given the same real native payloads serialized with the other admitted ZIP method.
    target = BytesIO()
    with ZipFile(BytesIO(package)) as original, ZipFile(target, "w") as stored:
        for row in original.infolist():
            data = original.read(row)
            row.compress_type = 0
            write_member(target, stored, (row, data))
    # When projecting an actual stored-member package.
    result = project_office_content(target.getvalue())
    # Then both supported methods preserve the same ordinary rows and math.
    assert result.receipt.row_count == 5
    assert verify_office_content_math(result.docx).atomic_non_entailments == 1


def test_native_number_suffix_character_tail_is_rejected(package: bytes) -> None:
    # Given the actual native suffix grammar with unsupported character content between runs.
    suffix = ('<m:r><m:t>\u2001\u2001</m:t></m:r><m:r><m:rPr><m:sty m:val="p"/>'
              '</m:rPr><m:t>(</m:t></m:r><m:r><m:t>12</m:t>+1</m:r>'
              '<m:r><m:rPr><m:sty m:val="p"/></m:rPr><m:t>)</m:t></m:r>').encode()
    xml = payload(package).replace(b"</m:m>", b"</m:m>" + suffix)
    changed = replace(package, "word/document.xml", xml)
    # When validating the complete numbered expression.
    with pytest.raises(OfficeContentError, match="character content"):
        verify_office_content_math(changed)
    # Then unsupported suffix tails cannot hide behind normalization.


def test_actual_row_policy_check_rejects_processing_instruction_decoy(package: bytes) -> None:
    # Given a valid XML instruction whose lexical marker is not a real property.
    xml = payload(package).replace(b"<w:trPr>",
              b"<w:trPr><w:cnfStyle/><?office <w:tblHeader /> ?>", 1)
    changed = replace(package, "word/document.xml", xml)
    # When reconstruction alone would splice into the ignored instruction.
    with pytest.raises(OfficeContentError, match="Actual final row lacks enabled cantSplit"):
        project_office_content(changed)
    # Then the independent parsed-policy check is a real gate that can fail.


def test_same_display_sibling_math_is_rejected(package: bytes) -> None:
    # Given a second expression appended inside the protected native display paragraph.
    sibling = b'<m:oMath><m:r><m:t>+1</m:t></m:r></m:oMath>'
    xml = payload(package).replace(b"</m:oMathPara>", sibling + b"</m:oMathPara>", 1)
    changed = replace(package, "word/document.xml", xml)
    # When checking the complete display envelope.
    with pytest.raises(OfficeContentError, match="display envelope"):
        verify_office_content_math(changed)
    # Then an unchanged matrix cannot authorize additional math in the same display.


def test_display_host_extra_run_is_rejected(package: bytes) -> None:
    # Given extra text in the Word paragraph hosting a protected display.
    xml = payload(package).replace(b"</m:oMathPara>",
              b'</m:oMathPara><w:r><w:t>+1</w:t></w:r>', 1)
    changed = replace(package, "word/document.xml", xml)
    # When admitting the native display envelope.
    with pytest.raises(OfficeContentError, match="display envelope"):
        verify_office_content_math(changed)
    # Then nonnative host content is rejected rather than interpreted as harmless metadata.


def bad_directory_offset(data: bytes) -> bytes:
    """Reproduce the frozen parser's malformed EOCD-offset failure."""
    result = bytearray(data)
    end = data.rfind(b"PK\x05\x06")
    offset = unpack_from("<L", data, end + 16)[0]
    pack_into("<L", result, end + 16, offset + 1)
    return bytes(result)


@pytest.mark.parametrize("entrypoint", [project_office_content, verify_office_content_math])
def test_bad_directory_offset_has_typed_failure(
    package: bytes, entrypoint: Callable[[bytes], OfficeContentProjection | OfficeMathReport],
) -> None:
    # Given the review's EOCD-offset mutation causing a negative seek in ZipFile.
    changed = bad_directory_offset(package)
    # When either producer/math boundary invokes the frozen parser.
    with pytest.raises(OfficeContentError):
        entrypoint(changed)
    # Then no plain ValueError escapes this byte boundary.


@pytest.mark.parametrize("mutate_native", [True, False])
def test_bad_directory_offset_is_typed_in_either_custody_input(
    package: bytes, mutate_native: bool,
) -> None:
    # Given one corrupted input to the two-input verifier.
    final = project_office_content(package).docx
    before = bad_directory_offset(package) if mutate_native else package
    after = final if mutate_native else bad_directory_offset(final)
    # When verifying native/final custody.
    with pytest.raises(OfficeContentError):
        verify_office_content_projection(before, after)
    # Then both untrusted input slots have the same typed failure contract.


def test_unnamespaced_property_with_instruction_decoy_is_rejected(package: bytes) -> None:
    # Given the exact review control whose lexical marker disguises an unqualified property.
    marker = (b'<w:trPr><?independent <w:cantSplit/> ?><cantSplit/></w:trPr>')
    xml = re.sub(rb"<w:trPr>.*?</w:trPr>", marker, payload(package), count=1, flags=re.DOTALL)
    changed = replace(package, "word/document.xml", xml)
    # When parsing expanded row-property names.
    with pytest.raises(OfficeContentError, match="namespace"):
        project_office_content(changed)
    # Then namespace markers inside instructions cannot grant a property its namespace.


def oversized_zip64_offset(data: bytes) -> bytes:
    """Reproduce an unsupported ZIP64 offset overflowing the frozen parser's seek."""
    _, offset = central_members(data)[0]
    name, extra = unpack_from("<HH", data, offset + 28)
    insertion = offset + 46 + name + extra
    field = pack("<HHQ", 1, 8, 0xFFFFFFFFFFFFFFFF)
    changed = bytearray(data[:insertion] + field + data[insertion:])
    pack_into("<H", changed, offset + 30, extra + len(field))
    pack_into("<L", changed, offset + 42, 0xFFFFFFFF)
    end = data.rfind(b"PK\x05\x06")
    size = unpack_from("<L", data, end + 12)[0]
    pack_into("<L", changed, end + len(field) + 12, size + len(field))
    return bytes(changed)


@pytest.mark.parametrize("entrypoint", [project_office_content, verify_office_content_math])
def test_oversized_zip64_offset_has_typed_failure(
    package: bytes, entrypoint: Callable[[bytes], OfficeContentProjection | OfficeMathReport],
) -> None:
    # Given the exact ZIP64-offset shape producing a real OverflowError in ZipFile.
    changed = oversized_zip64_offset(package)
    # When either producer/math boundary invokes the frozen parser.
    with pytest.raises(OfficeContentError):
        entrypoint(changed)
    # Then unsupported ZIP64 remains a typed rejection, with no new ZIP64 support.


@pytest.mark.parametrize("mutate_native", [True, False])
def test_oversized_zip64_offset_is_typed_in_either_custody_input(
    package: bytes, mutate_native: bool,
) -> None:
    # Given one custody input with the oversized ZIP64 member offset.
    final = project_office_content(package).docx
    before = oversized_zip64_offset(package) if mutate_native else package
    after = final if mutate_native else oversized_zip64_offset(final)
    # When verifying native/final custody.
    with pytest.raises(OfficeContentError):
        verify_office_content_projection(before, after)
    # Then both input slots normalize the same underlying parser overflow.


def unknown_xml_encoding(data: bytes, part: str) -> bytes:
    """Change a real XML declaration to an unsupported codec without changing its text."""
    xml = payload(data, part)
    changed = re.sub(rb'encoding="[^"]+"', b'encoding="x-rikishi-unknown"', xml, count=1)
    assert changed != xml
    return replace(data, part, changed)


@pytest.mark.parametrize("part", ["_rels/.rels", "[Content_Types].xml", "word/document.xml"])
@pytest.mark.parametrize("entrypoint", [project_office_content, verify_office_content_math])
def test_unknown_xml_encoding_has_typed_diagnostic(
    package: bytes, part: str,
    entrypoint: Callable[[bytes], OfficeContentProjection | OfficeMathReport],
) -> None:
    # Given an actual package with a single unsupported XML encoding declaration.
    changed = unknown_xml_encoding(package, part)
    # When producer/math admission parses the control part or main document.
    with pytest.raises(OfficeContentError, match="unknown encoding: x-rikishi-unknown") as raised:
        entrypoint(changed)
    # Then the original codec failure remains visible as the typed diagnostic's cause.
    assert type(raised.value.__cause__) is LookupError
    assert raised.value.detail == str(raised.value.__cause__)


@pytest.mark.parametrize("scenario", [
    ("_rels/.rels", True, True), ("_rels/.rels", False, True),
    ("[Content_Types].xml", True, True), ("[Content_Types].xml", False, True),
    ("word/document.xml", True, True), ("word/document.xml", False, False),
])
def test_unknown_xml_encoding_is_typed_in_either_custody_input(
    package: bytes, scenario: tuple[str, bool, bool],
) -> None:
    # Given a codec mutation in one actual custody input.
    part, mutate_native, reaches_xml_parser = scenario
    final = project_office_content(package).docx
    before = unknown_xml_encoding(package, part) if mutate_native else package
    after = final if mutate_native else unknown_xml_encoding(final, part)
    # When verifying native/final custody.
    with pytest.raises(OfficeContentError) as raised:
        verify_office_content_projection(before, after)
    # Then parsed declarations retain their cause; changed final XML rejects even earlier.
    if reaches_xml_parser:
        assert type(raised.value.__cause__) is LookupError
        assert raised.value.detail == "unknown encoding: x-rikishi-unknown"
    else:
        assert raised.value.__cause__ is None
        assert raised.value.detail == "Final document differs from the permitted row projection"


def unsupported_multibyte_encoding(data: bytes) -> bytes:
    """Use a recognized codec unsupported by the actual native XML parser."""
    xml = payload(data)
    changed = xml.replace(b'encoding="UTF-8"', b'encoding="utf-7"', 1)
    assert changed != xml
    return replace(data, "word/document.xml", changed)


@pytest.mark.parametrize("entrypoint", [project_office_content, verify_office_content_math])
def test_unsupported_multibyte_xml_has_typed_diagnostic(
    package: bytes, entrypoint: Callable[[bytes], OfficeContentProjection | OfficeMathReport],
) -> None:
    # Given a real main-document declaration that causes the parser's plain ValueError.
    changed = unsupported_multibyte_encoding(package)
    # When parsing main-document XML at producer/math admission.
    with pytest.raises(OfficeContentError, match="multi-byte encodings are not supported") as raised:
        entrypoint(changed)
    # Then the specific native parser cause survives the owned XML boundary.
    assert type(raised.value.__cause__) is ValueError
    assert raised.value.detail == str(raised.value.__cause__)


@pytest.mark.parametrize("mutate_native", [True, False])
def test_unsupported_multibyte_xml_is_typed_in_either_custody_input(
    package: bytes, mutate_native: bool,
) -> None:
    # Given an unsupported multibyte declaration in either custody input.
    final = project_office_content(package).docx
    before = unsupported_multibyte_encoding(package) if mutate_native else package
    after = final if mutate_native else unsupported_multibyte_encoding(final)
    # When verifying the actual native/final difference.
    with pytest.raises(OfficeContentError) as raised:
        verify_office_content_projection(before, after)
    # Then the native parser failure is typed and the existing earlier final rejection survives.
    if mutate_native:
        assert type(raised.value.__cause__) is ValueError
        assert raised.value.detail == "multi-byte encodings are not supported"
    else:
        assert raised.value.__cause__ is None
        assert raised.value.detail == "Final document differs from the permitted row projection"

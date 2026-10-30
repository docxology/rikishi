from __future__ import annotations

import re
import shlex
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from rikishi.manuscript import _require_clean_tex_log
from rikishi.manuscript_provenance import ProvenanceError, prepare_renderer
from rikishi.publication import PublicationSettings, publication_headers

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def settings() -> PublicationSettings:
    return PublicationSettings.model_validate(yaml.safe_load((ROOT / "config/manuscript.yaml").read_text()))


def test_configured_link_contrast_exceeds_normal_text_threshold(settings: PublicationSettings) -> None:
    color = settings.publication.link_color_hex
    channels = [int(color[index:index + 2], 16) / 255 for index in (0, 2, 4)]
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
              for value in channels]
    luminance = sum(value * weight for value, weight in zip(linear, (0.2126, 0.7152, 0.0722), strict=True))
    assert 1.05 / (luminance + 0.05) >= 4.5
    assert 1.05 / (0.2126 + 0.05) < 4.5


@pytest.mark.parametrize(("key", "value"), [
    ("web_body_font_px", 16), ("margin_mm", 0), ("margin_mm", -1),
    ("margin_mm", float("inf")), ("link_color_hex", "red"),
])
def test_invalid_reading_policy_is_rejected(settings: PublicationSettings, key: str, value: object) -> None:
    configuration = settings.model_dump()
    configuration["publication"][key] = value
    with pytest.raises(ValidationError):
        PublicationSettings.model_validate(configuration)


@pytest.mark.parametrize(("edition", "writer", "expected"), [
    ("pdf", "latex", r"\definecolor{red}{HTML}{A00000}"),
    ("html", "html5", '<style id="rikishi-publication-policy">'),
])
def test_pandoc_preserves_native_header_policy(
    tmp_path: Path, settings: PublicationSettings, edition: str, writer: str, expected: str,
) -> None:
    source = tmp_path / "paper.md"
    source.write_text("---\n" + yaml.safe_dump({
        "header-includes": publication_headers(settings.publication, edition=edition),
    }) + "---\n\nA paragraph.\n\n```bash\nprintf '%s' example\n```\n")
    result = subprocess.run(
        ["pandoc", "--standalone", "--to", writer, str(source)],
        check=True, capture_output=True, text=True, timeout=30,
    )
    assert expected in result.stdout
    if edition == "pdf":
        assert r"\leftskip" not in result.stdout
        assert r"\rightskip" not in result.stdout
        assert r"\setlist" not in result.stdout
        assert r"\widowpenalty=10000" in result.stdout
        assert r"\AtBeginEnvironment{thebibliography}{\interlinepenalty=10000}" in result.stdout
    else:
        assert "html body { font-size: 17px;" in result.stdout
        assert "width: 100%; max-width: none; margin: 0; padding: 12mm;" in result.stdout
        assert "@media (max-width: 600px)" in result.stdout
        assert "padding: min(12mm, 4vw);" in result.stdout
        assert "body code { font-size: max(15px, 0.85em); }" in result.stdout
        assert "body p, body li { max-width: none; }" in result.stdout
        assert "body .table-scroll { max-width: 100%; overflow-x: auto; }" in result.stdout
        assert "white-space: pre-wrap; overflow-wrap: anywhere" in result.stdout


@pytest.mark.parametrize("key", ["pdf_prose_width_mm", "web_prose_width_ch"])
def test_removed_prose_caps_require_explicit_configuration_migration(
    settings: PublicationSettings, key: str,
) -> None:
    configuration = settings.model_dump()
    configuration["publication"][key] = 110
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        PublicationSettings.model_validate(configuration)


def test_html_preserves_configured_desktop_margin_and_reduces_phone_gutters(settings: PublicationSettings) -> None:
    configuration = settings.model_dump()
    configuration["publication"].update(margin_mm=24.5, web_body_font_px=20)
    policy = PublicationSettings.model_validate(configuration).publication
    headers = "\n".join(publication_headers(policy, edition="html"))
    assert "font-size: 20px;" in headers
    assert "padding: 24.5mm;" in headers
    assert "padding: min(24.5mm, 4vw);" in headers


def test_html_code_floor_applies_before_viewport_specific_rules(settings: PublicationSettings) -> None:
    headers = "\n".join(publication_headers(settings.publication, edition="html"))
    global_policy = headers.split("@media", 1)[0]
    assert "body code { font-size: max(15px, 0.85em); }" in global_policy


def _assert_toc_target_policy(headers: str) -> None:
    """Require both native TOC selectors to receive the global navigation target floor."""
    targets = {"body .toc a", "body #TOC a"}
    heights: dict[str, str] = {}
    for selectors, block in re.findall(r"([^{}]+)\{([^{}]*)\}", headers.split("@media", 1)[0]):
        declarations = dict(re.findall(r"([\w-]+)\s*:\s*([^;]+);", block))
        if "min-height" in declarations:
            for selector in selectors.split(","):
                if selector.strip() in targets:
                    heights[selector.strip()] = declarations["min-height"].strip()
    assert heights == dict.fromkeys(targets, "44px")


def test_html_toc_navigation_targets_have_global_floor(settings: PublicationSettings) -> None:
    headers = "\n".join(publication_headers(settings.publication, edition="html"))
    _assert_toc_target_policy(headers)


@pytest.mark.parametrize("rule", [
    "",
    "body .toc a { min-height: 44px; }",
    "body #TOC a { min-height: 44px; }",
    "body .toc, body #TOC { min-height: 44px; }",
    "body .toc a, body #toc a { min-height: 44px; }",
    "body a { min-height: 44px; }",
    "body .toc a, body #TOC a { min-height: 28px; }",
    "body .toc a, body #TOC a { min-height: 43.99px; }",
    "body .toc a, body #TOC a { min-height: 44px; min-height: 28px; }",
    "body .toc a, body #TOC a { min-height: 44px; } body #TOC a { min-height: 28px; }",
    "@media (max-width: 600px) { body .toc a, body #TOC a { min-height: 44px; } }",
])
def test_toc_target_guard_rejects_missing_or_wrong_navigation_policy(rule: str) -> None:
    with pytest.raises(AssertionError):
        _assert_toc_target_policy(rule)


def test_publication_syntax_palette_contrasts_with_native_dark_code_blocks(settings: PublicationSettings) -> None:
    headers = "\n".join(publication_headers(settings.publication, edition="html"))
    colors = []
    for line in headers.splitlines():
        if "body pre" not in line:
            continue
        match = re.search(r"(?:\{|;)\s*color:\s*rgb\((\d+),\s*(\d+),\s*(\d+)\)", line)
        if match:
            colors.append(tuple(int(value) for value in match.groups()))
    assert colors

    def luminance(color: tuple[int, ...]) -> float:
        normalized = [channel / 255 for channel in color]
        linear = [value / 12.92 if value <= 0.04045 else ((value + .055) / 1.055) ** 2.4
                  for value in normalized]
        return sum(value * weight for value, weight in zip(linear, (.2126, .7152, .0722), strict=True))

    background = luminance((44, 62, 80))
    for color in colors:
        foreground = luminance(color)
        assert (max(foreground, background) + .05) / (min(foreground, background) + .05) >= 4.5


def test_unknown_edition_is_rejected(settings: PublicationSettings) -> None:
    with pytest.raises(ValueError, match="Unsupported publication style edition"):
        publication_headers(settings.publication, edition="unknown")


def _toc_pages(directory: Path, headers: list[str]) -> tuple[int, tuple[str, ...], list[float]]:
    """Render a real 48-entry TOC and read its pages and nominal fonts at unit zoom."""
    directory.mkdir()
    source = directory / "toc.md"
    source.write_text("---\n" + yaml.safe_dump({
        "documentclass": "article", "fontsize": "12pt", "geometry": "margin=12mm",
        "header-includes": headers,
    }) + "---\n\n\\clearpage\n\nBodyStart\n\n" + "\n\n".join(
        f"{'#' if index % 8 == 1 else '##'} TOCENTRY{index:03d} Source evidence and mathematical obligations\n\nBodyEnd{index:03d}."
        for index in range(1, 49)))
    tex = directory / "toc.tex"
    result = subprocess.run(["pandoc", "--standalone", "--toc", "--to", "latex",
                             "--output", str(tex), str(source)],
                            check=True, capture_output=True, timeout=30)
    (directory / "pandoc.stderr").write_bytes(result.stderr)
    for iteration in range(2):
        rendered = subprocess.run([
            "xelatex", "-interaction=nonstopmode", "-halt-on-error", "toc.tex",
        ], cwd=directory, check=False, capture_output=True, timeout=90)
        (directory / f"xelatex-{iteration}.stdout").write_bytes(rendered.stdout)
        (directory / f"xelatex-{iteration}.stderr").write_bytes(rendered.stderr)
        rendered.check_returncode()
    text = subprocess.run(["pdftotext", str(directory / "toc.pdf"), "-"],
                          check=True, capture_output=True, text=True, timeout=30).stdout
    (directory / "extracted.txt").write_text(text)
    pages = text.split("\f")
    body_page = next(index for index, page in enumerate(pages) if "BodyStart" in page)
    entries = tuple(re.findall(r"TOCENTRY\d+", "\n".join(pages[:body_page])))
    xml = subprocess.run(["pdftohtml", "-xml", "-zoom", "1", "-stdout",
                          str(directory / "toc.pdf")],
                         check=True, capture_output=True, text=True, timeout=30)
    (directory / "text-geometry.xml").write_text(xml.stdout)
    geometry = ET.fromstring(xml.stdout)
    fonts = {row.attrib["id"]: float(row.attrib["size"])
             for row in geometry.findall(".//fontspec")}
    body_sizes = [fonts[row.attrib["font"]] for page in geometry.findall("page")[body_page:]
                  for row in page.findall("text") if "BodyStart" in "".join(row.itertext())]
    assert body_sizes == [12.0]
    sizes = [fonts[row.attrib["font"]] for page in geometry.findall("page")[:body_page]
             for row in page.findall("text") if "TOCENTRY" in "".join(row.itertext())]
    return body_page, entries, sizes


@pytest.mark.integration
def test_compact_toc_keeps_all_entries_on_one_page(
    tmp_path: Path, settings: PublicationSettings,
) -> None:
    # Given the actual publication TOC policy and 48 distinct retained entries.
    # When real Pandoc/XeLaTeX pagination is inspected with Poppler.
    pages, entries, sizes = _toc_pages(tmp_path / "compact", publication_headers(
        settings.publication, edition="pdf"))
    # Then every entry fits one page at readable nominal font sizes.
    assert pages == 1
    assert entries == tuple(f"TOCENTRY{index:03d}" for index in range(1, 49))
    assert len(sizes) == 48 and min(sizes) >= 7.5


@pytest.mark.integration
def test_native_toc_control_exposes_extra_page_without_compaction(
    tmp_path: Path, settings: PublicationSettings,
) -> None:
    # Given the same actual renderer with only TOC compaction removed.
    headers = [part for part in publication_headers(settings.publication, edition="pdf")
               if not part.startswith(r"\csletcs{rikishiOriginalTableOfContents}")]
    # When the same 48 entries are typeset.
    pages, entries, _ = _toc_pages(tmp_path / "uncompacted", headers)
    # Then the original spill is reproduced without losing or inventing entries.
    assert pages > 1
    assert entries == tuple(f"TOCENTRY{index:03d}" for index in range(1, 49))


@pytest.fixture(scope="module")
def layout_renderer(tmp_path_factory: pytest.TempPathFactory) -> Path:
    snapshot, _, _ = prepare_renderer(
        tmp_path_factory.mktemp("layout-renderer"), ROOT.parent.parent / "Public/template",
    )
    return snapshot


def _render_layout(
    directory: Path, settings: PublicationSettings, renderer: Path, *, narrow: bool = False,
    graphical: bool = False,
) -> ET.Element:
    """Exercise the pinned combined renderer and retain its real TeX and Poppler coordinates."""
    directory.mkdir()
    manuscript_dir = directory / "manuscript"
    manuscript_dir.mkdir()
    policy = settings.publication
    headers = publication_headers(policy, edition="pdf", graphical_abstracts=(
        settings.paper.graphical_abstracts if graphical else None))
    paper: dict[str, object] = {"title": "Layout fixture"}
    if graphical:
        from PIL import Image

        (directory / "output/figures").mkdir(parents=True)
        for index, name in enumerate([settings.paper.cover.image,
                                      *(p.image for p in settings.paper.graphical_abstracts)]):
            Image.new("RGB", (120, 140), (index * 50, 70, 120)).save(directory / "output" / name)
        paper["cover"] = settings.paper.cover.model_dump()
    if narrow:
        headers.append(r"\AtBeginDocument{\leftskip=\dimexpr(\textwidth-110mm)/2\relax"
                       r"\rightskip=\leftskip}")
    paragraph = "ordinary reproducible software methods retain measured evidence for independent inspection. " * 12
    manuscript = manuscript_dir / "reading.md"
    manuscript.write_text("---\n" + yaml.safe_dump({
        "geometry": f"margin={policy.margin_mm:g}mm", "fontsize": f"{policy.font_size_pt}pt",
        "header-includes": headers,
    }) + "---\n\n# Abstract {.unnumbered}\n\nProseStart " + paragraph
        + "\n\n| Tableleft | Tableright |\n|:---|:---|\n| " + paragraph[:160]
        + " | " + paragraph[:160] + " |\n\nAfterStart " + paragraph
        + "\n\n1. OrderedStart " + paragraph
        + "\n\n   - NestedStart " + paragraph
        + "\n\n- BulletStart " + paragraph
        + "\n\n```python\nnumber = 123\n```\n")
    (manuscript_dir / "config.yaml").write_text(yaml.safe_dump({
        "metadata": {"geometry": f"margin={policy.margin_mm:g}mm",
                     "fontsize": f"{policy.font_size_pt}pt", "documentclass": "article"},
        "rendering": settings.rendering.model_dump(),
        "paper": paper,
    }))
    command = """import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.pdf_renderer import PDFRenderer
root = Path(sys.argv[2])
manuscript = root / 'manuscript'
config = RenderingConfig(manuscript_dir=str(manuscript), output_dir=str(root / 'output'),
    pdf_dir=str(root / 'output/pdf'), figures_dir=str(root / 'output/figures'), latex_compiler='xelatex')
PDFRenderer(config).render_combined([manuscript / 'reading.md'], manuscript, project_name='layout')
"""
    result = subprocess.run([sys.executable, "-c", command, str(renderer), str(directory)],
                            check=False, capture_output=True, text=True, timeout=120)
    (directory / "renderer-stdout.txt").write_text(result.stdout)
    (directory / "renderer-stderr.txt").write_text(result.stderr)
    result.check_returncode()
    output = directory / "output/pdf"
    _require_clean_tex_log(output / "_combined_manuscript.log")
    extracted = subprocess.run(["pdftotext", "-bbox-layout", str(output / "layout_combined.pdf"), "-"],
                               check=True, capture_output=True, text=True, timeout=30)
    (directory / "coordinates.xhtml").write_text(extracted.stdout)
    return ET.fromstring(extracted.stdout)


@pytest.mark.integration
def test_three_actual_graphical_abstracts_occupy_physical_pages_two_to_four(
    tmp_path: Path, settings: PublicationSettings, layout_renderer: Path,
) -> None:
    from PIL import Image

    directory = tmp_path / "abstract-layout"
    _render_layout(directory, settings, layout_renderer, graphical=True)
    pdf = directory / "output/pdf/layout_combined.pdf"
    for number, page in enumerate(settings.paper.graphical_abstracts, 2):
        prefix = directory / f"page-{number}"
        subprocess.run(["pdfimages", "-f", str(number), "-l", str(number), "-png",
                        str(pdf), str(prefix)], check=True, capture_output=True, timeout=30)
        with Image.open(directory / "output" / page.image) as canonical:
            expected = canonical.convert("RGB").tobytes()
        images = list(directory.glob(f"page-{number}-*.png"))
        assert len(images) == 1
        with Image.open(images[0]) as actual:
            assert actual.size == (120, 140) and actual.convert("RGB").tobytes() == expected


def _assert_full_width(document: ET.Element, margin_mm: float) -> None:
    """Require page-edge prose, normal list indentation, and a shared table/heading edge."""
    namespace = {"x": "http://www.w3.org/1999/xhtml"}
    words = document.findall(".//x:word", namespace)
    positions = {word.text: float(word.attrib["xMin"]) for word in words}
    margin = margin_mm * 72 / 25.4
    assert positions["Abstract"] == pytest.approx(margin, abs=1)
    assert positions["Tableleft"] == pytest.approx(positions["Abstract"], abs=1)
    assert positions["ProseStart"] == pytest.approx(margin, abs=1)
    assert positions["AfterStart"] == pytest.approx(margin, abs=1)
    assert margin + 10 < positions["OrderedStart"] < margin + 40
    assert positions["BulletStart"] == pytest.approx(positions["OrderedStart"], abs=1)
    assert positions["OrderedStart"] + 10 < positions["NestedStart"] < margin + 80
    page = document.find(".//x:page", namespace)
    assert page is not None
    usable = float(page.attrib["width"]) - 2 * margin
    prose = [line for line in document.findall(".//x:line", namespace)
             if any(word.text == "ordinary" for word in line.findall("x:word", namespace))]
    full_lines = [line for line in prose
                  if float(line.attrib["xMax"]) - float(line.attrib["xMin"]) > .9 * usable]
    assert len(full_lines) >= 4
    # Native microtype protrudes a terminal period by 2.12 pt at this 11 pt font.
    optical_protrusion_pt = 3
    assert all(float(line.attrib["xMin"]) >= margin - optical_protrusion_pt
               and float(line.attrib["xMax"]) <= margin + usable + optical_protrusion_pt
               for line in prose)


@pytest.mark.integration
@pytest.mark.parametrize("margin_mm", [12.0, 24.5])
def test_pdf_uses_full_width_at_configured_margins(
    tmp_path: Path, settings: PublicationSettings, layout_renderer: Path, margin_mm: float,
) -> None:
    configuration = settings.model_dump()
    configuration["publication"]["margin_mm"] = margin_mm
    configured = PublicationSettings.model_validate(configuration)
    document = _render_layout(tmp_path / "full-width", configured, layout_renderer)
    _assert_full_width(document, margin_mm)


@pytest.mark.integration
def test_actual_narrow_pdf_is_rejected(
    tmp_path: Path, settings: PublicationSettings, layout_renderer: Path,
) -> None:
    document = _render_layout(tmp_path / "narrow-control", settings, layout_renderer, narrow=True)
    with pytest.raises(AssertionError):
        _assert_full_width(document, settings.publication.margin_mm)


def test_verification_shell_continuations_preserve_digest_argument() -> None:
    source = (ROOT / "manuscript/rikishi.md").read_text()
    command = source.split("```bash\n")[-2].split("```", 1)[0]
    arguments = shlex.split(command.replace("\\\n", " "))
    assert arguments == ["uv", "run", "--locked", "--no-sync", "rikishi", "inference-verify",
                         "output/inference/inference-report.json", "--sha256", "$REPORT_SHA256"]
    assert max(map(len, command.splitlines())) <= 75


def test_native_tex_log_guard_rejects_partial_success_and_missing_log(tmp_path: Path) -> None:
    log = tmp_path / "native.log"
    with pytest.raises(ProvenanceError, match="compilation log missing"):
        _require_clean_tex_log(log)
    log.write_text("Package caption Warning: Unused setup.\nAn inline ! is ordinary text.\n")
    _require_clean_tex_log(log)
    log.write_bytes(log.read_bytes() + b"! LaTeX Error: There's no line here to end.\nOutput written on paper.pdf\n")
    with pytest.raises(ProvenanceError, match="compilation contains TeX errors: ! LaTeX Error"):
        _require_clean_tex_log(log)


@pytest.mark.integration
def test_native_code_contrast_accepts_policy_and_rejects_default_palette(
    tmp_path: Path, settings: PublicationSettings,
) -> None:
    def contrast(color: str) -> float:
        channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
                  for value in channels]
        luminance = sum(value * weight for value, weight in zip(linear, (.2126, .7152, .0722), strict=True))
        return 1.05 / (luminance + .05)

    observed = {}
    for label, headers in (("default", []), ("policy", publication_headers(settings.publication, edition="pdf"))):
        folder = tmp_path / label
        folder.mkdir()
        source = folder / "contrast.md"
        source.write_text("---\n" + yaml.safe_dump({"header-includes": headers}) + "---\n\n"
                          "```python\nnumber = 123\nvalue = 1.25\n```\n\n"
                          "```bash\nprintf --help\n```\n")
        subprocess.run(["pandoc", "--standalone", "--pdf-engine=xelatex", str(source),
                        "-o", str(folder / "contrast.pdf")], check=True, capture_output=True, timeout=60)
        result = subprocess.run(["pdftohtml", "-xml", "-hidden", "-i", "-stdout", str(folder / "contrast.pdf")],
                                check=True, capture_output=True, text=True, timeout=30)
        document = ET.fromstring(result.stdout)
        fonts = {node.attrib["id"]: node.attrib["color"] for node in document.findall(".//fontspec")}
        ratios = [contrast(fonts[node.attrib["font"]]) for node in document.findall(".//text")
                  if "".join(node.itertext()).strip()]
        assert ratios
        observed[label] = min(ratios)
    assert observed["default"] < 4.5
    assert observed["policy"] >= 4.5

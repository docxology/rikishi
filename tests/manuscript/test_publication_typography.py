from __future__ import annotations

import html
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Final, Literal, assert_never

import pytest
import yaml
from pydantic import BaseModel, ConfigDict

from rikishi.publication import PublicationSettings, publication_headers
from rikishi.runtime_process import run_bounded

ROOT: Final = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.integration


class TypographyObservation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    targets: int
    minimum_target_height: float
    minimum_target_width: float
    minimum_gap: float
    numeric_lines: int
    number: str
    hash_lines: int
    hash_text: str
    table_width: float
    region_width: float
    body_scroll_width: float
    viewport_width: float
    table_text: str
    excluded_code: str
    atomic_tokens: tuple[str, ...]
    nested_atoms: int
    edge_text: str
    excluded_link: str
    excluded_math: str
    excluded_editable: str
    atoms_before: int
    body_text_preserved: bool


PROBE: Final = r"""<script>
let beforeTypography;
let atomsBefore;
document.addEventListener('DOMContentLoaded', () => {
  beforeTypography = document.body.textContent;
  atomsBefore = document.querySelectorAll('.rikishi-scientific-number').length;
}, {once:true});
addEventListener('load', () => {
  const source = document.querySelector('#rikishi-scientific-numbers');
  if (source) {
    const again = document.createElement('script'); again.textContent = source.textContent;
    document.head.append(again);
  }
  const targets = [...document.querySelectorAll('#TOC a')];
  const boxes = targets.map(e => e.getBoundingClientRect());
  const lines = e => {
    const r = document.createRange(); r.selectNodeContents(e);
    return new Set([...r.getClientRects()].filter(b => b.width && b.height).map(b => b.top)).size;
  };
  const number = document.querySelector('#number strong');
  const hash = document.querySelector('#hash code');
  const region = document.querySelector('.table-scroll');
  const data = {
    targets: targets.length,
    minimum_target_height: Math.min(...boxes.map(b => b.height)),
    minimum_target_width: Math.min(...boxes.map(b => b.width)),
    minimum_gap: Math.min(...boxes.slice(1).map((b, i) => b.top - boxes[i].bottom)),
    numeric_lines: lines(number), number: number.textContent,
    hash_lines: lines(hash), hash_text: hash.textContent,
    table_width: region.querySelector('table').getBoundingClientRect().width,
    region_width: region.clientWidth,
    body_scroll_width: document.documentElement.scrollWidth,
    viewport_width: document.documentElement.clientWidth,
    table_text: region.textContent.replace(/\s+/g, ' ').trim(),
    excluded_code: document.querySelector('#excluded').innerHTML,
    atomic_tokens: [...document.querySelectorAll('.rikishi-scientific-number')].map(e => e.textContent),
    nested_atoms: document.querySelectorAll('.rikishi-scientific-number .rikishi-scientific-number').length,
    edge_text: document.querySelector('#edge').textContent,
    excluded_link: document.querySelector('#edge a').innerHTML,
    excluded_math: document.querySelector('#edge .math').innerHTML,
    excluded_editable: document.querySelector('#edge [contenteditable]').innerHTML,
    atoms_before: atomsBefore,
    body_text_preserved: beforeTypography === document.body.textContent,
  };
  const out = document.createElement('pre'); out.id = 'typography-observation';
  out.textContent = JSON.stringify(data); document.body.append(out);
});
</script>"""

BASE_STYLE: Final = """<style>
body { font-family: serif; overflow-wrap: anywhere; }
#TOC a { display: inline-block; line-height: 1.5; padding-block: 2px; }
#TOC li { margin-block: 1px; }
#number { width: 125px; font-family: serif; }
#hash { width: 180px; }
code { overflow-wrap: anywhere; word-break: break-word; }
.table-scroll { overflow-x: auto; max-width: 100%; }
.table-scroll > table { display: block; width: max-content; min-width: 100%; }
th, td { border: 1px solid; padding: 8px; }
</style>"""

HASH: Final = "0123456789abcdef" * 4
CELL: Final = "Complete mathematical and source evidence stays readable in every table column. " * 4
EDGE: Final = "Signed +2.4E+5; Unicode −3.2e−4; fraction .5e2; identifier a1e3; long 1e+" + "3" * 30


def _observe(directory: Path, mutation: Literal["none", "gap", "numbers", "tables"] = "none") -> TypographyObservation:
    """Run real Pandoc and an explicitly selected private Chromium process."""
    executable = os.environ.get("RIKISHI_CHROMIUM")
    if not executable or not Path(executable).is_file():
        raise pytest.UsageError("Native typography tests require RIKISHI_CHROMIUM")
    directory.mkdir()
    settings = PublicationSettings.model_validate(yaml.safe_load(
        (ROOT / "config/manuscript.yaml").read_text()))
    headers = publication_headers(settings.publication, edition="html")
    match mutation:
        case "numbers":
            headers = [part for part in headers if 'id="rikishi-scientific-numbers"' not in part]
        case "none" | "gap" | "tables":
            pass
        case unreachable:
            assert_never(unreachable)
    overrides = {
        "none": "", "numbers": "",
        "gap": "body #TOC li { margin-block: 0 !important; }",
        "tables": "body .table-scroll > table { display: block !important; width: max-content !important; }",
    }
    source = directory / "fixture.md"
    source.write_text("---\n" + yaml.safe_dump({
        "header-includes": [BASE_STYLE, PROBE, *headers, "<style>" + overrides[mutation] + "</style>"],
    }) + "---\n\n"
        + "<p id=\"number\">The <strong>8.326673e-17</strong>.</p>\n\n"
        + f'<p id="hash"><code>{HASH}</code></p>\n\n'
        + '<pre id="excluded"><code>value = 8.326673e-17</code></pre>\n\n'
        + f'<p id="edge">{EDGE} <a href="#literal">1e3</a> '
        + '<span class="math">2e3</span> <span contenteditable="true">3e3</span></p>\n\n'
        + '<div class="table-scroll">\n\n| Role | Model | Result |\n| --- | --- | --- |\n'
        + f'| {CELL} | {CELL} | {CELL} |\n\n</div>\n\n'
        + "\n\n".join(f"# Navigation target {i}\n\nComplete source paragraph." for i in range(6)))
    rendered = subprocess.run([
        "pandoc", "--standalone", "--toc", "--to", "html5", str(source),
    ], capture_output=True, check=True, timeout=30)
    paper = directory / "fixture.html"
    paper.write_bytes(rendered.stdout)
    (directory / "pandoc.stderr").write_bytes(rendered.stderr)
    result = run_bounded([
        executable, "--headless=new", "--no-first-run", "--disable-background-networking",
        "--disable-component-update", "--disable-extensions", "--disable-sync", "--disable-gpu",
        f"--user-data-dir={directory / 'profile'}", "--window-size=800,900",
        "--dump-dom", "--virtual-time-budget=2000", paper.as_uri(),
    ], cwd=directory, stdout=directory / "browser.stdout", stderr=directory / "browser.stderr",
        timeout=40)
    (directory / "process.json").write_text(json.dumps({
        "returncode": result.returncode, "timed_out": result.timed_out,
    }))
    assert result.returncode == 0 and not result.timed_out
    dom = (directory / "browser.stdout").read_text()
    match = re.search(r'<pre id="typography-observation">(.*?)</pre>', dom, re.DOTALL)
    assert match is not None, "Real browser observation missing"
    payload = html.unescape(match.group(1))
    (directory / "observation.json").write_text(payload)
    return TypographyObservation.model_validate_json(payload)


@pytest.fixture(scope="module")
def observation(tmp_path_factory: pytest.TempPathFactory) -> TypographyObservation:
    return _observe(tmp_path_factory.mktemp("typography") / "positive")


def test_navigation_reserves_target_and_inter_target_space(observation: TypographyObservation) -> None:
    # Given the actual Pandoc navigation and installed production headers.
    # When Chromium lays out every fixture target.
    # Then hit regions and separation both satisfy the publication contract.
    assert observation.targets == 6
    assert observation.minimum_target_height >= 44
    assert observation.minimum_target_width >= 44
    assert observation.minimum_gap >= 8


def test_short_scientific_notation_is_atomic_while_hashes_wrap(observation: TypographyObservation) -> None:
    # Given a narrow paragraph, a complete hash and literal code.
    # When the production typography pass runs in the real DOM.
    # Then a numerical exponent stays with its mantissa without changing content.
    assert observation.numeric_lines == 1
    assert observation.number == "8.326673e-17"
    assert observation.hash_lines > 1
    assert observation.hash_text == HASH
    assert observation.excluded_code == "<code>value = 8.326673e-17</code>"


def test_table_reflows_complete_text_within_reading_region(observation: TypographyObservation) -> None:
    # Given three prose-heavy columns rather than a single unbreakable formula.
    # When automatic table layout resolves the available reading width.
    # Then text is preserved without max-content blank travel or page overflow.
    assert observation.table_width <= observation.region_width + 1
    assert observation.body_scroll_width == observation.viewport_width
    assert observation.table_text == "Role Model Result " + " ".join([CELL.strip()] * 3)


def test_numeric_projection_is_idempotent_and_preserves_literal_contexts(
    observation: TypographyObservation,
) -> None:
    # Given scientific notation, identifiers, a very long exponent and literal contexts.
    # When the actual production script executes before and after document load.
    # Then only bounded numerical tokens are wrapped, with exact text and no nesting.
    assert observation.atomic_tokens == ("8.326673e-17", "+2.4E+5", "−3.2e−4", ".5e2")
    assert observation.nested_atoms == 0
    assert " ".join(observation.edge_text.split()) == EDGE + " 1e3 2e3 3e3"
    assert observation.atoms_before == 0
    assert observation.body_text_preserved
    assert observation.excluded_link == "1e3"
    assert observation.excluded_math == "2e3"
    assert observation.excluded_editable == "3e3"


@pytest.mark.parametrize("mutation", ["gap", "numbers", "tables"])
def test_rendered_controls_expose_missing_typography_behavior(
    tmp_path: Path, mutation: Literal["gap", "numbers", "tables"],
) -> None:
    # Given a rendered control with exactly one behavior removed.
    # When the same real-browser observation runs.
    # Then the corresponding geometry oracle must fail while content remains present.
    control = _observe(tmp_path / mutation, mutation)
    match mutation:
        case "gap":
            assert control.minimum_gap < 8
        case "numbers":
            assert control.numeric_lines > 1
        case "tables":
            assert control.table_width > control.region_width + 1
        case unreachable:
            assert_never(unreachable)
    assert control.number == "8.326673e-17" and control.hash_text == HASH

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from defusedxml import ElementTree
from PIL import Image
from pydantic import ValidationError

from rikishi.bridge_figures import build_bridge_figure_inputs
from rikishi.publication_abstracts import (
    ABSTRACT_NAMES,
    GraphicalAbstract,
    abstract_pages_latex,
    abstract_pages_markdown,
)
from rikishi.witness_abstracts import _source, render_witness_abstracts

if TYPE_CHECKING:
    from conftest import BridgePacket


def abstracts() -> list[GraphicalAbstract]:
    return [GraphicalAbstract(image=f"figures/{name}.png", title=f"Visual guide {index}",
                             alt=f"Source-bound diagram {index}", summary=f"Explanation {index}.")
            for index, name in enumerate(ABSTRACT_NAMES, 1)]


def test_front_pages_preserve_three_distinct_images_and_hard_page_boundaries() -> None:
    pages = abstracts()
    latex = abstract_pages_latex(pages)
    markdown = abstract_pages_markdown(pages)
    assert latex.count(r"\includegraphics") == 3
    assert latex.count(r"\clearpage") == 4
    assert markdown.count(r"\newpage") == 3
    assert [latex.index(page.image) for page in pages] == sorted(latex.index(p.image) for p in pages)
    assert all(markdown.count(page.image) == 1 for page in pages)


@pytest.mark.parametrize("images", [[], [0, 1], [0, 1, 1], [2, 1, 0]])
def test_front_pages_reject_missing_duplicate_or_reordered_abstracts(images: list[int]) -> None:
    pages = abstracts()
    with pytest.raises(ValueError, match="three graphical abstracts"):
        abstract_pages_latex([pages[index] for index in images])


@pytest.mark.parametrize("path", ["../x.png", "figures/x.png", "https://example.com/x.png",
                                   "figures/abstract-source.png}\\input{secret}"])
def test_abstract_image_boundary_rejects_unknown_or_injected_paths(path: str) -> None:
    with pytest.raises(ValidationError):
        GraphicalAbstract(image=path, title="Source", alt="Source", summary="Source.")


def test_latex_frontmatter_escapes_plain_text() -> None:
    pages = abstracts()
    pages[0] = pages[0].model_copy(update={"title": r"A & B_1 {bound} 10%"})
    assert r"A \& B\_1 \{bound\} 10\%" in abstract_pages_latex(pages)


def test_percentage_width_does_not_force_a_distorting_html_height() -> None:
    result = subprocess.run(["pandoc", "-f", "markdown", "-t", "json"],
                            input=abstract_pages_markdown(abstracts()), text=True,
                            capture_output=True, check=True, timeout=30)
    document = json.loads(result.stdout)
    images = [block["c"][2][0]["c"][0]["c"] for block in document["blocks"]
              if block["t"] == "Figure"]
    assert len(images) == 3
    assert all("height" not in dict(image[0][2]) for image in images)


def test_actual_abstract_exports_bind_the_report_and_preserve_legible_svg_text(
    bridge_packet: BridgePacket, tmp_path: Path,
) -> None:
    inputs = build_bridge_figure_inputs(bridge_packet.path,
                                       trusted_report_sha256=bridge_packet.sha256)
    outputs = render_witness_abstracts(inputs, tmp_path)
    assert {p.name for p in outputs} == {
        *(f"{name}.{suffix}" for name in ABSTRACT_NAMES for suffix in ("png", "svg")),
        "witness-abstracts.json",
    }
    manifest = json.loads((tmp_path / "witness-abstracts.json").read_text())
    assert manifest["report_sha256"] == bridge_packet.sha256
    assert manifest["witnesses"] == [w.model_dump(mode="json") for w in inputs.report.witnesses]
    for name in ABSTRACT_NAMES:
        tree = ElementTree.fromstring((tmp_path / f"{name}.svg").read_bytes())
        texts = tree.findall(".//{http://www.w3.org/2000/svg}text")
        assert len(texts) >= 15
        sizes = [float(size) for node in texts for size in re.findall(
            r"(?:font-size:\s*|font:\s*)([\d.]+)px", node.get("style", ""))]
        assert sizes and min(sizes) >= 9
        with Image.open(tmp_path / f"{name}.png") as image:
            image.load()
            assert image.size == (2266, 2421)
            assert bridge_packet.sha256 in image.info["Description"]


def test_source_abstract_formats_actual_witness_values(bridge_packet: BridgePacket) -> None:
    # The low-level formatter is exercised with a mathematical mutation only;
    # no authentication or native result is claimed for this changed object.
    inputs = build_bridge_figure_inputs(bridge_packet.path,
                                       trusted_report_sha256=bridge_packet.sha256)
    first = inputs.report.witnesses[0].model_copy(update={"likelihood": ("1/8", "7/8")})
    report = inputs.report.model_copy(update={"witnesses": (first, *inputs.report.witnesses[1:])})
    figure = _source(inputs.model_copy(update={"report": report}))
    try:
        text = "\n".join(artist.get_text() for artist in figure.texts)
        assert "L=(1/8,7/8)" in text
        assert "Joint pL=(1/16,7/16); evidence Z=1/2; posterior r=(1/8,7/8)." in text
        assert "Here: (1/8)(1/2)=1/16 and (7/8)(1/2)=7/16" in text
    finally:
        figure.clear()


@pytest.mark.parametrize("mutation", ["posterior", "candidate", "order"])
def test_abstracts_reject_false_qualitative_contrasts_before_writing(
    bridge_packet: BridgePacket, tmp_path: Path, mutation: str,
) -> None:
    inputs = build_bridge_figure_inputs(bridge_packet.path,
                                       trusted_report_sha256=bridge_packet.sha256)
    witnesses = list(inputs.report.witnesses)
    match mutation:
        case "posterior":
            witnesses[0] = witnesses[0].model_copy(update={"likelihood": ("1/8", "7/8")})
        case "candidate":
            witnesses[2] = witnesses[2].model_copy(update={"candidate": ("1/2", "1/2")})
        case "order":
            witnesses.reverse()
    report = inputs.report.model_copy(update={"witnesses": tuple(witnesses)})
    output = tmp_path / "uncreated"
    with pytest.raises(ValueError, match="Graphical abstracts require"):
        render_witness_abstracts(inputs.model_copy(update={"report": report}), output)
    assert not output.exists()


def test_export_rejects_existing_output_without_overwriting(
    bridge_packet: BridgePacket, tmp_path: Path,
) -> None:
    inputs = build_bridge_figure_inputs(bridge_packet.path,
                                       trusted_report_sha256=bridge_packet.sha256)
    target = tmp_path / f"{ABSTRACT_NAMES[0]}.png"
    target.write_bytes(b"existing owner")
    with pytest.raises(FileExistsError):
        render_witness_abstracts(inputs, tmp_path)
    assert target.read_bytes() == b"existing owner"


def test_dense_exports_expose_exact_inputs_controls_and_derived_examples(
    bridge_packet: BridgePacket, tmp_path: Path,
) -> None:
    inputs = build_bridge_figure_inputs(bridge_packet.path,
                                       trusted_report_sha256=bridge_packet.sha256)
    render_witness_abstracts(inputs, tmp_path)
    texts = []
    for name, minimum in zip(ABSTRACT_NAMES, (40, 55, 55), strict=True):
        tree = ElementTree.fromstring((tmp_path / f"{name}.svg").read_bytes())
        lines = ["".join(node.itertext()) for node in
                 tree.findall(".//{http://www.w3.org/2000/svg}text")]
        assert len(lines) >= minimum
        texts.append("\n".join(lines))
    assert "(exists (?AGENT)" in texts[0]
    assert "posterior_mul_predictive" in texts[0]
    assert "CounterSatisfiable" in texts[0]
    for value in ("1/10", "2/11", "12/13", "5/16", "11/24", "13/36"):
        assert value in texts[1]
    assert "DERIVED" in texts[1]
    assert "Candidate q" in texts[1]
    for value in ("0.836988", "0.143841", "0.693147"):
        assert value in texts[1]
    assert "16326" in texts[2]
    assert str(len(inputs.report.lean.declarations)) in texts[2]
    assert "CounterSatisfiable" in texts[2]


def test_dense_panel_geometry_and_numeric_table_cells(
    bridge_packet: BridgePacket, tmp_path: Path,
) -> None:
    import numpy as np
    from matplotlib.backends.backend_agg import FigureCanvasAgg

    from rikishi.witness_abstracts import _evidence, _source, _witness

    inputs = build_bridge_figure_inputs(bridge_packet.path,
                                       trusted_report_sha256=bridge_packet.sha256)
    measurements = []
    for build in (_source, _witness, _evidence):
        fig = build(inputs)
        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        renderer = canvas.get_renderer()
        for ax in fig.axes:
            for table in ax.tables:
                for cell in table.get_celld().values():
                    text = cell.get_text().get_window_extent(renderer)
                    box = cell.get_window_extent(renderer)
                    assert box.x0 <= text.x0 <= text.x1 <= box.x1
                    assert box.y0 <= text.y0 <= text.y1 <= box.y1
        gaps = []
        for index, left in enumerate(fig.texts):
            a = left.get_window_extent(renderer)
            for right in fig.texts[index + 1:]:
                b = right.get_window_extent(renderer)
                if min(a.x1, b.x1) > max(a.x0, b.x0):
                    gap = max(a.y0 - b.y1, b.y0 - a.y1)
                    assert gap >= 2
                    gaps.append(gap)
        if build is _witness:
            table = fig.axes[0].tables[0]
            for index, witness in enumerate(inputs.report.witnesses, 1):
                assert table[index, 3].get_text().get_text() == ", ".join(witness.candidate)
            for line, curve in zip(fig.axes[1].lines, inputs.curves, strict=True):
                assert np.array_equal(line.get_ydata(), curve.free_energy)
        measurements.append({"panel": build.__name__, "minimum_text_gap_px": min(gaps)})
        fig.clear()
    (tmp_path / "geometry.json").write_text(json.dumps(measurements, indent=2))

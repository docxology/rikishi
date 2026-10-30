import subprocess
from pathlib import Path

import pytest
from PIL import Image

from rikishi.manuscript_provenance import ProvenanceError
from rikishi.manuscript_verification import _pdf_images, _pdf_margin


@pytest.mark.integration
@pytest.mark.parametrize("heading", ["Abstract", "Another heading"])
def test_pdf_margin_uses_actual_page_coordinates(tmp_path: Path, heading: str) -> None:
    source = tmp_path / "margin.tex"
    source.write_text(
        "\\documentclass{article}\n\\usepackage[margin=25mm]{geometry}\n"
        f"\\begin{{document}}\\section*{{{heading}}}Actual page content.\\end{{document}}\n"
    )
    subprocess.run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", source.name],
                   cwd=tmp_path, check=True, capture_output=True, timeout=60)
    pdf = source.with_suffix(".pdf")
    if heading == "Abstract":
        _pdf_margin(pdf, 25)
    with pytest.raises(ProvenanceError, match="PDF abstract margin differs"):
        _pdf_margin(pdf, 12)


@pytest.mark.integration
def test_pdf_figure_check_reads_embedded_pixels(tmp_path: Path) -> None:
    expected = {name: tmp_path / name for name in ("cover.png", "body.png")}
    for color, path in zip(("navy", "teal"), expected.values(), strict=True):
        Image.new("RGB", (32, 24), color).save(path)
    source = tmp_path / "images.tex"
    source.write_text(
        "\\documentclass{article}\\usepackage{graphicx}\\begin{document}"
        "\\includegraphics{cover.png}\\includegraphics{body.png}\\end{document}"
    )
    subprocess.run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", source.name],
                   cwd=tmp_path, check=True, capture_output=True, timeout=60)
    pdf = source.with_suffix(".pdf")
    _pdf_images(pdf, expected)
    Image.new("RGB", (32, 24), "red").save(expected["body.png"])
    with pytest.raises(ProvenanceError, match="PDF canonical figure missing: body.png"):
        _pdf_images(pdf, expected)

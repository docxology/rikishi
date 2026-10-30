from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile

import pytest
from PIL import Image

from rikishi.publication_checks import PublicationSourceError, validate_publication_source

pytestmark = pytest.mark.integration

BIBLIOGRAPHY = """@article{scholar2020,
  author = {Researcher, Ada}, title = {Finite inference},
  journal = {Methods}, year = {2020}
}
"""
SOURCE = r"""# Abstract {.unnumbered}
An authored {{TITLE}} with {{OBSERVATIONS}} observations.

# Methods {#sec:methods}
## Model {#sec:model}

::: {.definition #def:energy title="Objective"}
A finite objective.
:::

$$F(q)={{VALUE}}.$$ {#eq:energy}

![Measured illustration](figure.png){#fig:measurement}

See [@sec:methods], [@eq:energy], [@fig:measurement], [@def:energy],
and [@scholar2020]. Repeated citation [@scholar2020].

```markdown
# 1. This is quoted source, not a manuscript heading.
$$unlabeled = 1$$
[@missing_in_code]
```
"""


def write_inputs(tmp_path: Path, source: str = SOURCE, bib: str = BIBLIOGRAPHY) -> tuple[Path, Path]:
    manuscript, bibliography = tmp_path / "main.md", tmp_path / "references.bib"
    manuscript.write_text(source, encoding="utf-8")
    bibliography.write_text(bib, encoding="utf-8")
    return manuscript, bibliography


def test_counts_come_from_real_pandoc_nodes_with_repeated_citations(tmp_path: Path) -> None:
    source, bib = write_inputs(tmp_path)
    result = validate_publication_source(source, bib)
    assert result["citation_ids"] == ["scholar2020"]
    assert result["citation_count"] == 1 and result["citation_occurrences"] == 2
    assert result["bibliography_count"] == 1
    assert result["equation_labels"] == ["eq:energy"] and result["equation_count"] == 1
    assert result["figure_labels"] == ["fig:measurement"] and result["figure_count"] == 1
    assert result["section_labels"] == ["sec:methods", "sec:model"]
    assert result["section_count"] == 2
    assert result["formalism_labels"] == ["def:energy"] and result["formalism_count"] == 1


@pytest.mark.parametrize(
    "text, message",
    [
        (SOURCE.replace("scholar2020", "unknown2020"), "Unknown literature"),
        (SOURCE.replace("[@eq:energy]", "[@eq:missing]"), "Unresolved cross-reference"),
        (SOURCE.replace("[@fig:measurement]", "[@fig:missing]"), "Unresolved cross-reference"),
        (SOURCE.replace("[@sec:methods]", "[@sec:missing]"), "Unresolved cross-reference"),
        (SOURCE.replace("[@def:energy]", "[@def:missing]"), "Unresolved cross-reference"),
        (SOURCE.replace("{#eq:energy}", ""), "Unlabeled display equation"),
        (SOURCE.replace("$$F(q)={{VALUE}}.$$ {#eq:energy}", "[$$F(q)=1.$$]{.boxed}")
         .replace("[@eq:energy]", "the objective"),
         "Unlabeled display equation"),
        (SOURCE + r"\begin{equation}F(q)=1.\end{equation}" + "\n", "labeled Pandoc math"),
        (SOURCE + "\n$$G(q)=0.$$\n", "Unlabeled display equation"),
        (SOURCE.replace("{#eq:energy}", "{#eq missing}"), "Unlabeled display equation"),
        (SOURCE.replace("#def:energy", ""), "Unlabeled formalism"),
        (SOURCE.replace("# Methods", "# 1. Methods"), "Manual section number"),
        (SOURCE.replace("# Methods", "# `1.` Methods"), "Manual section number"),
        (SOURCE + "\n\\begin{eqnarray}x &=& 1\\end{eqnarray}\n", "labeled Pandoc math"),
        (SOURCE + "\n```{=latex}\n\\begin {eqnarray}x &=& 1\\end {eqnarray}\n```\n",
         "labeled Pandoc math"),
        (SOURCE + "\n\\begin{multline}x=1\\end{multline}\n", "labeled Pandoc math"),
        (SOURCE + "\n```{=latex}\n$$x=1$$\n```\n", "labeled Pandoc math"),
        ('---\nabstract: "Missing [@unknown2020]."\n---\n' + SOURCE, "Unknown literature"),
        (SOURCE.replace("## Model", "## 1.2 Model"), "Manual section number"),
        (SOURCE.replace("F(q)=", r"F(q)=\tag{7}"), "Manual equation tag"),
        (SOURCE.replace("sec:model", "sec:methods"), "[Dd]uplicate"),
        (SOURCE + "\n[Repeated]{#sec:methods}\n", "[Dd]uplicate"),
        (SOURCE + "\n$$G(q)=0.$$ {#eq:energy}\n", "[Dd]uplicate"),
        (SOURCE.replace("::: {.definition #def:energy title=\"Objective\"}",
                        "::: {.ordinary #def:energy}"), "Unresolved cross-reference"),
        (SOURCE + "\n[Missing](#fig:missing)\n", "Unresolved cross-reference"),
        (SOURCE.replace("# Methods {#sec:methods}", "# Methods {#eq:fake}")
         .replace("[@sec:methods]", "[@eq:fake]"), "Unresolved cross-reference"),
    ],
)
def test_rejects_invalid_authored_contract(tmp_path: Path, text: str, message: str) -> None:
    source, bib = write_inputs(tmp_path, text)
    with pytest.raises(PublicationSourceError, match=message):
        validate_publication_source(source, bib)


@pytest.mark.parametrize(
    "bib, message",
    [
        (BIBLIOGRAPHY + BIBLIOGRAPHY, "Duplicate bibliography"),
        (BIBLIOGRAPHY + BIBLIOGRAPHY.replace("scholar2020", "Scholar2020"), "Duplicate bibliography"),
        ("@article{broken, title={Unclosed}", "Pandoc rejected"),
        (BIBLIOGRAPHY + "\n@article{broken, title={Unclosed}", "Pandoc rejected"),
        ("not a bibliography", "Empty bibliography"),
        ("@article{scholar2020,title=,year={2020}}", "BibTeX rejected"),
        ("@article{scholar2020,title=UNDEFINED,year={2020}}", "BibTeX diagnostics"),
        ("@article{scholar2020,title={Valid},author=UNDEFINED,year={2020}}", "BibTeX diagnostics"),
        ("@article{scholar2020,title={Valid},month=UNKNOWNMONTH,year={2020}}", "BibTeX diagnostics"),
    ],
)
def test_rejects_invalid_bibliographies(tmp_path: Path, bib: str, message: str) -> None:
    source, bibliography = write_inputs(tmp_path, bib=bib)
    with pytest.raises(PublicationSourceError, match=message):
        validate_publication_source(source, bibliography)


def test_missing_input_and_missing_installed_tool_fail_closed(tmp_path: Path) -> None:
    source, bib = write_inputs(tmp_path)
    with pytest.raises(PublicationSourceError, match="Pandoc rejected"):
        validate_publication_source(tmp_path / "absent.md", bib)
    script = (
        "from pathlib import Path; "
        "from rikishi.publication_checks import validate_publication_source; "
        f"validate_publication_source(Path({str(source)!r}), Path({str(bib)!r}))"
    )
    failed = subprocess.run(
        [sys.executable, "-c", script], check=False, env=os.environ | {"PATH": str(tmp_path)},
        capture_output=True, text=True, timeout=10,
    )
    assert failed.returncode != 0
    assert "PublicationSourceError" in failed.stderr and "Pandoc unavailable" in failed.stderr


def test_source_error_survives_generator_context_unwinding(tmp_path: Path) -> None:
    """A real missing-tool error must retain its type through fixture cleanup."""
    source, bib = write_inputs(tmp_path)
    script = tmp_path / "source_error_context.py"
    script.write_text(
        "from contextlib import contextmanager\n"
        "from pathlib import Path\n"
        "from rikishi.publication_checks import validate_publication_source\n"
        "@contextmanager\n"
        "def cleanup():\n"
        "    yield\n"
        "with cleanup():\n"
        f"    validate_publication_source(Path({str(source)!r}), Path({str(bib)!r}))\n"
    )
    failed = subprocess.run(
        [sys.executable, str(script)], check=False, env=os.environ | {"PATH": str(tmp_path)},
        capture_output=True, text=True, timeout=10,
    )
    assert failed.returncode != 0
    assert "Pandoc unavailable" in failed.stderr
    assert "PublicationSourceError" in failed.stderr
    assert "TypeError" not in failed.stderr


@pytest.mark.parametrize("kind", [
    "definition", "proposition", "theorem", "lemma", "corollary", "remark", "axiom",
    "claim", "example",
])
def test_native_formalism_kinds_and_declared_prefixes(tmp_path: Path, kind: str) -> None:
    text = f"::: {{.{kind} #custom:one}}\nA formalism.\n:::\n\nBy [@custom:one].\n"
    source, bib = write_inputs(tmp_path, text)
    result = validate_publication_source(source, bib)
    assert result["formalism_labels"] == ["custom:one"] and result["citation_ids"] == []
    source.write_text(text.replace("[@custom:one]", "[@custom:missing]"))
    with pytest.raises(PublicationSourceError, match="Unresolved cross-reference"):
        validate_publication_source(source, bib)


def test_metadata_citations_are_counted_with_body_citations(tmp_path: Path) -> None:
    source, bib = write_inputs(tmp_path, '---\nabstract: "Source [@scholar2020]."\n---\n' + SOURCE)
    result = validate_publication_source(source, bib)
    assert result["citation_occurrences"] == 3 and result["citation_count"] == 1


@pytest.mark.parametrize("month", ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug",
                                  "sep", "oct", "nov", "dec"])
def test_standard_bibtex_month_macros_are_valid(tmp_path: Path, month: str) -> None:
    source, bib = write_inputs(tmp_path, "Cited [@scholar2020].\n",
                               BIBLIOGRAPHY.replace("year = {2020}", f"month={month}, year={{2020}}"))
    result = validate_publication_source(source, bib)
    assert result["citation_ids"] == ["scholar2020"] and result["bibliography_count"] == 1


@pytest.mark.parametrize("writer", ["html5", "docx", "latex"])
def test_real_filters_renumber_inserted_objects_and_references(
    tmp_path: Path, project_root: Path, writer: str,
) -> None:
    snapshot = project_root / ".rikishi/template-renderer/efce6d6f5b3c4e8e2bbf92d8250855a0a9389ae8"
    formalism = snapshot / "infrastructure/rendering/formalism.lua"
    source, bib = write_inputs(tmp_path, SOURCE.replace("{{VALUE}}", "1"))
    Image.new("RGB", (16, 16), "navy").save(tmp_path / "figure.png")
    inserted = (
        "# Preliminary model {#sec:preliminary}\n\n"
        "$$G(q)=0.$$ {#eq:preliminary}\n\n"
        "![Preliminary illustration](figure.png){#fig:preliminary}\n\n"
        "::: {.definition #def:preliminary}\nA preliminary objective.\n:::\n\n"
    )
    versions = [source.read_text(), source.read_text().replace("# Methods", inserted + "# Methods")]
    outputs: list[str] = []
    hyperlink_values: list[list[str]] = []
    for index, text in enumerate(versions):
        source.write_text(text, encoding="utf-8")
        inventory = validate_publication_source(source, bib)
        assert inventory["equation_count"] == inventory["figure_count"] == index + 1
        assert inventory["section_count"] == index + 2
        product = tmp_path / f"edition-{index}.{writer}"
        subprocess.run(
            ["pandoc", str(source), "-t", writer, "-o", str(product),
             "--number-sections", "--lua-filter", str(formalism),
             "--filter", "pandoc-crossref", "--citeproc", f"--bibliography={bib}",
             f"--resource-path={tmp_path}", "--metadata=linkReferences:true",
             "--fail-if-warnings"], check=True, capture_output=True, text=True, timeout=30,
        )
        if writer == "docx":
            with ZipFile(product) as archive:
                document = ElementTree.fromstring(archive.read("word/document.xml"))
                outputs.append(" ".join(document.itertext()))
                hyperlink_values.append([
                    " ".join(link.itertext()) for link in document.findall(
                        ".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}hyperlink"
                    )
                ])
        else:
            outputs.append(product.read_text())
    before, after = outputs
    assert "scholar2020]" not in before and "scholar2020]" not in after
    assert "Researcher" in before and "Researcher" in after
    if writer == "html5":
        assert re.search(r'id="sec:methods">.*?number">1<', before, re.DOTALL)
        assert re.search(r'id="sec:methods">.*?number">2<', after, re.DOTALL)
        assert re.search(r'href="#eq:energy">\s*1\s*</a>', before)
        assert re.search(r'href="#eq:energy">\s*2\s*</a>', after)
        assert re.search(r'href="#fig:measurement">\s*1\s*</a>', before)
        assert re.search(r'href="#fig:measurement">\s*2\s*</a>', after)
        assert re.search(r'href="#sec:methods">\s*1\s*</a>', before)
        assert re.search(r'href="#sec:methods">\s*2\s*</a>', after)
        assert re.search(r'href="#def:energy">Definition 1</a>', before)
        assert re.search(r'href="#def:energy">Definition 2</a>', after)
    elif writer == "docx":
        assert "1 Methods" in before and "2 Methods" in after
        assert "Definition 1" in before and "Definition 2" in after
        assert "Figure 1:" in before and "Figure 2:" in after
        assert "( 1 )" in before and "( 2 )" in after
        assert re.search(r"eq\.\s+1", before) and re.search(r"eq\.\s+2", after)
        assert hyperlink_values == [["1", "1", "1", "Definition 1"],
                                    ["2", "2", "2", "Definition 2"]]
    else:
        assert r"\label{eq:energy}" in before and r"\label{eq:energy}" in after
        assert before.count(r"\begin{equation}") == 1
        assert after.count(r"\begin{equation}") == 2
        assert before.count(r"\section{") == 1 and after.count(r"\section{") == 2
        assert after.index(r"\label{sec:preliminary}") < after.index(r"\label{sec:methods}")
        assert r"eq.~\ref{eq:energy}" in before and r"eq.~\ref{eq:energy}" in after
        assert "Definition 1" in before and "Definition 2" in after
        assert r"sec.~\ref{sec:methods}" in before and r"sec.~\ref{sec:methods}" in after
        assert r"\hyperref[def:energy]{Definition 1}" in before
        assert r"\hyperref[def:energy]{Definition 2}" in after


def test_real_citeproc_unknown_key_is_a_failing_control(tmp_path: Path) -> None:
    source, bib = write_inputs(tmp_path, "Missing [@unknown2020].\n")
    failed = subprocess.run(
        ["pandoc", str(source), "-t", "html5", "--citeproc", f"--bibliography={bib}",
         "--fail-if-warnings"], check=False, capture_output=True, text=True, timeout=30,
    )
    assert failed.returncode != 0 and "unknown2020 not found" in failed.stderr

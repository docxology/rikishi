"""One ordered three-page visual introduction shared by all native editions."""

from __future__ import annotations

from typing import Annotated, Final

from pydantic import BaseModel, ConfigDict, StringConstraints

from rikishi.manuscript_provenance import ProvenanceError

ABSTRACT_NAMES: Final = ("abstract-source", "abstract-witness", "abstract-evidence")
type AbstractImage = Annotated[str, StringConstraints(
    pattern=r"^figures/abstract-(source|witness|evidence)\.png$")]
type PlainText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class GraphicalAbstract(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")
    image: AbstractImage
    title: PlainText
    alt: PlainText
    summary: PlainText


def _ordered(pages: list[GraphicalAbstract]) -> None:
    if [page.image for page in pages] != [f"figures/{name}.png" for name in ABSTRACT_NAMES]:
        raise ProvenanceError("Require the three graphical abstracts in source, witness, evidence order")


def _latex(text: str) -> str:
    replacements = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
                    "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
                    "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    return "".join(replacements.get(character, character) for character in text)


def abstract_pages_latex(pages: list[GraphicalAbstract]) -> str:
    """Insert physical pages 2–4 immediately before the native table of contents."""
    _ordered(pages)
    blocks = [r"\clearpage"]
    for index, page in enumerate(pages, 1):
        blocks.extend([
            r"\thispagestyle{empty}",
            r"\noindent{\Large\sffamily\bfseries " + _latex(page.title) + r"\par}",
            r"\medskip\noindent " + _latex(page.summary) + r"\par\medskip",
            r"\noindent\includegraphics[width=\textwidth,height=0.80\textheight,keepaspectratio,alt={"
            + _latex(page.alt) + r"}]{../manuscript/" + page.image + "}",
            r"\par\vfill\noindent{\small Graphical abstract " + str(index) + r" of 3}\clearpage",
        ])
    return "\n".join(blocks)


def abstract_pages_markdown(pages: list[GraphicalAbstract]) -> str:
    """Project the same ordered graphics with explicit Word page breaks and HTML headings."""
    _ordered(pages)
    return "\n\n".join(
        f"# {page.title} {{.unnumbered .unlisted}}\n\n{page.summary}\n\n"
        f"![{page.alt}]({page.image}){{width=100%}}\n\n\\newpage"
        for page in pages
    ) + "\n\n"

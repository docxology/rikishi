from __future__ import annotations

import re
import subprocess
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final, assert_never

from pydantic import BaseModel, ConfigDict, Field, JsonValue, TypeAdapter

_JSON: Final = TypeAdapter(JsonValue)
_EQUATION_LABEL: Final = re.compile(r"\{#(eq:[\w:.-]+)\}")
_MANUAL_SECTION: Final = re.compile(r"^(?:\d+(?:\.\d+)*[.)]?|Section\s+\d+)\s")
_MANUAL_TAG: Final = re.compile(r"\\(?:tag|eqno|leqno)\b")
_KINDS: Final = (
    "definition", "proposition", "theorem", "lemma", "corollary", "remark", "axiom",
    "claim", "example",
)
_RAW_DISPLAY: Final = re.compile(
    r"\\begin\s*\{(?:equation|eqnarray|align|alignat|flalign|gather|multline|displaymath|"
    + "|".join(_KINDS) + r")\*?\}|\\\[|\$\$"
)
_PREFIXES: Final = (
    "eq:", "fig:", "sec:", "tbl:", "lst:", "def:", "prop:", "thm:", "lem:",
    "cor:", "rem:", "axiom:", "claim:", "ex:", "inv:", "conj:", "alg:",
)
_ATTR_NODES: Final = {"Figure", "Image", "Div", "Span", "Table", "CodeBlock", "Code", "Link"}


@dataclass(slots=True)
class PublicationSourceError(ValueError):
    """Preserve diagnostic data while allowing Python to update exception metadata."""

    reason: str

    def __str__(self) -> str:
        return self.reason


class _BibliographyEntry(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)
    id: str = Field(min_length=1)


def _pandoc(source: Path, reader: str, writer: str) -> str:
    try:
        result = subprocess.run(
            ["pandoc", "--from", reader, "--to", writer, "--fail-if-warnings", str(source)],
            check=True, capture_output=True, text=True, timeout=30,
        )
    except subprocess.CalledProcessError as error:
        raise PublicationSourceError(
            f"Pandoc rejected {source}: {error.stderr.strip() or error.stdout.strip()}"
        ) from error
    except (OSError, subprocess.TimeoutExpired) as error:
        raise PublicationSourceError(f"Pandoc unavailable for {source}: {error}") from error
    if result.stderr.strip():
        raise PublicationSourceError(f"Pandoc diagnostics for {source}: {result.stderr.strip()}")
    return result.stdout


def _nodes(value: JsonValue) -> Iterator[dict[str, JsonValue]]:
    match value:
        case dict() as mapping:
            yield mapping
            for child in mapping.values():
                yield from _nodes(child)
        case list() as values:
            for child in values:
                yield from _nodes(child)
        case str() | int() | float() | bool() | None:
            return
        case unreachable:
            assert_never(unreachable)


def _check_bibtex(bibliography: Path) -> None:
    with TemporaryDirectory(prefix="publication-bibtex-") as temporary:
        directory = Path(temporary)
        raw = bibliography.read_bytes()
        (directory / "references.bib").write_bytes(raw)
        kinds = {kind.lower() for kind in re.findall(rb"@([A-Za-z]+)\s*[{(]", raw)}
        functions = "\n".join(f"FUNCTION {{{kind.decode()}}} {{ skip$ }}" for kind in sorted(
            kinds - {b"comment", b"string", b"preamble"}
        ))
        fields = {field.lower() for field in re.findall(rb"\b([A-Za-z][A-Za-z0-9_-]*)\s*=", raw)}
        declarations = " ".join(field.decode() for field in sorted(fields - {b"crossref"}))
        months = ("January", "February", "March", "April", "May", "June", "July", "August",
                  "September", "October", "November", "December")
        macros = "\n".join(f'MACRO {{{name[:3].lower()}}} {{"{name}"}}' for name in months)
        (directory / "syntax.bst").write_text(
            f"ENTRY {{ {declarations} }} {{}} {{}}\n{functions}\n{macros}\nREAD\n"
        )
        (directory / "syntax.aux").write_text("\\citation{*}\n\\bibstyle{syntax}\n\\bibdata{references}\n")
        try:
            result = subprocess.run(["bibtex", "syntax"], cwd=directory, check=True,
                                    capture_output=True, text=True, timeout=30)
        except subprocess.CalledProcessError as error:
            raise PublicationSourceError(
                f"BibTeX rejected {bibliography}: {error.stdout}{error.stderr}"
            ) from error
        except (OSError, subprocess.TimeoutExpired) as error:
            raise PublicationSourceError(f"BibTeX unavailable for {bibliography}: {error}") from error
        if "Warning--" in result.stdout or result.stderr.strip():
            raise PublicationSourceError(f"BibTeX diagnostics for {bibliography}: {result.stdout}{result.stderr}")


def _header_text(value: JsonValue) -> str:
    words: list[str] = []
    for node in _nodes(value):
        match node:
            case {"t": "Str", "c": str() as word} | {"t": "Code", "c": [_, str() as word]}:
                words.append(word)
    return " ".join(words)


def _equation_labels(inlines: list[JsonValue]) -> Iterator[str]:
    for index, inline in enumerate(inlines):
        match inline:
            case {"t": "Math", "c": [{"t": "DisplayMath"}, _]}:
                following = [item for item in inlines[index + 1:]
                             if item not in ({"t": "Space"}, {"t": "SoftBreak"})]
                label = ""
                if following:
                    match following[0]:
                        case {"t": "Str", "c": str() as token}:
                            found = _EQUATION_LABEL.fullmatch(token)
                            if found:
                                label = found.group(1)
                if not label:
                    raise PublicationSourceError("Unlabeled display equation; use $$...$$ {#eq:label}")
                yield label


def validate_publication_source(source: Path, bibliography: Path) -> dict[str, object]:
    """Check authored Pandoc labels/citations before hydration; return receipt inventories."""
    entries = TypeAdapter(list[_BibliographyEntry]).validate_json(
        _pandoc(bibliography, "bibtex", "csljson")
    )
    bib_ids = [entry.id for entry in entries]
    if not bib_ids:
        raise PublicationSourceError("Empty bibliography after Pandoc BibTeX parsing")
    if len({key.casefold() for key in bib_ids}) != len(bib_ids):
        raise PublicationSourceError("Duplicate bibliography IDs")
    _check_bibtex(bibliography)
    document = _JSON.validate_json(_pandoc(source, "markdown+yaml_metadata_block", "json"))
    match document:
        case {"blocks": list(), "meta": dict()}:
            pass
        case _:
            raise PublicationSourceError("Pandoc did not return a document AST")
    labels: list[str] = []
    groups: dict[str, set[str]] = {key: set() for key in ("equation", "figure", "section", "formalism")}
    citations: list[str] = []
    links: list[str] = []
    display_count = 0
    for node in _nodes(document):
        match node:
            case {"citationId": str() as key}:
                citations.append(key)
            case {"t": "Header", "c": [_, [str() as label, _, _], inlines]}:
                words = _header_text(inlines)
                if _MANUAL_SECTION.match(words):
                    raise PublicationSourceError(f"Manual section number: {words}")
                labels.append(label)
                if label.startswith("sec:"):
                    groups["section"].add(label)
            case {"t": str() as tag, "c": [[str() as label, classes, _], *_]} if tag in _ATTR_NODES:
                if label:
                    labels.append(label)
                if tag in {"Figure", "Image"} and label.startswith("fig:"):
                    groups["figure"].add(label)
                if tag == "Div" and isinstance(classes, list) and any(k in classes for k in _KINDS):
                    if not label:
                        raise PublicationSourceError("Unlabeled formalism block")
                    groups["formalism"].add(label)
                if tag == "Link":
                    match node:
                        case {"c": [_, _, [str() as target, _]]} if target.startswith("#"):
                            links.append(target[1:])
            case {"t": "Para" | "Plain", "c": list() as inlines}:
                equations = list(_equation_labels(inlines))
                labels.extend(equations)
                groups["equation"].update(equations)
            case {"t": ("Math" | "RawInline" | "RawBlock") as kind, "c": [mode, str() as formula]}:
                if kind == "Math" and mode == {"t": "DisplayMath"}:
                    display_count += 1
                if _MANUAL_TAG.search(formula):
                    raise PublicationSourceError("Manual equation tag")
                if kind != "Math" and _RAW_DISPLAY.search(formula):
                    raise PublicationSourceError("Use labeled Pandoc math or fenced formalism blocks")
            case dict():
                continue
            case unreachable:
                assert_never(unreachable)
    if len(set(labels)) != len(labels):
        raise PublicationSourceError("Duplicate manuscript IDs")
    if display_count != len(groups["equation"]):
        raise PublicationSourceError("Unlabeled display equation outside a labeled paragraph")
    literature: list[str] = []
    prefixes = (*_PREFIXES, *(kind + ":" for kind in _KINDS), *(
        label.partition(":")[0] + ":" for label in groups["formalism"] if ":" in label
    ))
    for key in citations:
        if key.startswith(prefixes) or key in groups["formalism"]:
            expected = {"eq:": "equation", "fig:": "figure", "sec:": "section"}
            targets = groups[expected[key[:key.index(":") + 1]]] if key.startswith(
                ("eq:", "fig:", "sec:")
            ) else set(labels) if key.startswith(("tbl:", "lst:")) else groups["formalism"]
            if key not in targets:
                raise PublicationSourceError(f"Unresolved cross-reference: {key}")
        else:
            literature.append(key)
    if missing := set(literature) - set(bib_ids):
        raise PublicationSourceError(f"Unknown literature citation IDs: {sorted(missing)}")
    if unresolved := set(links) - set(labels):
        raise PublicationSourceError(f"Unresolved cross-reference links: {sorted(unresolved)}")
    result: dict[str, object] = {
        "citation_ids": sorted(set(literature)), "citation_count": len(set(literature)),
        "citation_occurrences": len(literature), "bibliography_count": len(bib_ids),
    }
    for kind, values in groups.items():
        result[f"{kind}_labels"] = sorted(values)
        result[f"{kind}_count"] = len(values)
    return result

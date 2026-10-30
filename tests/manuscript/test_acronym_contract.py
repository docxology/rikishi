from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
EXPANSIONS = {
    "API": "application programming interface",
    "AST": "abstract syntax tree",
    "CNF": "conjunctive normal form",
    "CPU": "central processing unit",
    "CSL": "Citation Style Language",
    "DOI": "digital object identifier",
    "IR": "intermediate representation",
    "I/O": "input/output",
    "JVM": "Java virtual machine",
    "KIF": "Knowledge Interchange Format",
    "PR": "pull request",
    "URL": "Uniform Resource Locator",
    "UTC": "Coordinated Universal Time",
    "XML": "Extensible Markup Language",
    "SUMO": "Suggested Upper Merged Ontology",
    "SUO-KIF": "Standard Upper Ontology Knowledge Interchange Format",
    "ATP": "automated theorem proving",
    "FEP": "Free Energy Principle",
    "FOL": "first-order logic",
    "MCP": "Model Context Protocol",
    "TPTP": "Thousands of Problems for Theorem Provers",
    "KL": "Kullback-Leibler",
    "JDK": "Java Development Kit",
    "JSON": "JavaScript Object Notation",
    "PDF": "Portable Document Format",
    "CLI": "command-line interface",
    "HTTP": "Hypertext Transfer Protocol",
    "HTML": "Hypertext Markup Language",
    "SVG": "Scalable Vector Graphics",
    "PNG": "Portable Network Graphics",
    "JAR": "Java archive",
    "KB": "knowledge base",
    "CSS": "Cascading Style Sheets",
    "SQL": "Structured Query Language",
    "DOM": "Document Object Model",
    "IEEE": "Institute of Electrical and Electronics Engineers",
    "KEE": "Knowledge Engineering Environment",
    "SHA-256": "Secure Hash Algorithm 256-bit",
}
SPELLINGS = {name: (name, "SHA256") if name == "SHA-256" else (name,) for name in EXPANSIONS}
ARTIFACTS = (
    "manuscript/rikishi.md",
    "README.md",
    *(path.relative_to(ROOT).as_posix() for path in sorted((ROOT / "docs").rglob("*.md"))),
)


def _prose(markdown: str) -> str:
    def inline(match: re.Match[str]) -> str:
        value = match.group(1)
        acronyms = {
            spelling + plural
            for names in SPELLINGS.values()
            for spelling in names
            for plural in ("", "s")
        }
        return value if value in acronyms | {"E/V"} else ""

    prose = re.sub(r"```.*?```", "", markdown, flags=re.DOTALL)
    prose = re.sub(r"`([^`]*)`", inline, prose)
    prose = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", prose)
    prose = re.sub(r"https?://\S+", "", prose)
    prose = re.sub(r"\b[\w.-]+\.(?:md|py|json|yaml|yml|kif|png|svg|pdf|html|docx)\b", "", prose)
    return re.sub(r"\s+", " ", prose)


def _undefined_first_uses(markdown: str) -> list[str]:
    prose = _prose(markdown)
    failures: list[str] = []
    for acronym, expansion in EXPANSIONS.items():
        names = "|".join(re.escape(name) for name in SPELLINGS[acronym])
        first = re.search(rf"(?<![\w-])(?P<name>{names})(?P<plural>s)?(?![\w-])", prose)
        if first is not None:
            plural = "s" if first.group("plural") else ""
            name = first.group("name")
            prefix = prose[: first.end() + 1]
            if not prefix.casefold().endswith(f"{expansion}{plural} ({name}{plural})".casefold()):
                failures.append(name + plural)
    return failures


def _unintroduced_provers(markdown: str) -> list[str]:
    prose = _prose(markdown)
    shorthand = re.search(r"(?<![\w-])E/V(?![\w-])", prose)
    if shorthand is None:
        return []
    prefix = prose[: shorthand.start()]
    return [name for name in ("E", "Vampire") if re.search(rf"\b{name}\b", prefix) is None]


@pytest.mark.parametrize("relative", ARTIFACTS)
def test_standalone_artifact_defines_first_use(relative: str) -> None:
    assert _undefined_first_uses((ROOT / relative).read_text(encoding="utf-8")) == []


@pytest.mark.parametrize("relative", ARTIFACTS)
def test_standalone_artifact_introduces_provers_before_shorthand(relative: str) -> None:
    assert _unintroduced_provers((ROOT / relative).read_text(encoding="utf-8")) == []


def _figure_captions(markdown: str) -> dict[str, str]:
    return {
        identifier: caption
        for caption, identifier in re.findall(
            r"!\[([^\]]+)\]\(figures/[^)]+\)\{#fig:([^}]+)\}", markdown
        )
    }


@pytest.mark.parametrize("identifier, required", [
    ("corpus-files", ("SUMO",)),
    ("corpus-composition", ("SUMO",)),
    ("ontology-structure", ("SUMO", "SHA-256")),
    ("sumo-system", ("SUMO", "SHA-256")),
    ("research-controls", ("FOL", "SUMO")),
    ("bridge-evidence", ()),
    ("witness-channels", ("KL",)),
    ("witness-evidence-scaling", ()),
])
def test_detached_figure_caption_defines_its_local_keys(identifier, required) -> None:
    caption = _figure_captions((ROOT / "manuscript/rikishi.md").read_text())[identifier]
    for acronym in required:
        assert f"{EXPANSIONS[acronym]} ({acronym})" in caption
    assert _undefined_first_uses(caption) == []
    assert _unintroduced_provers(caption) == []
    if identifier in {"research-controls", "bridge-evidence"}:
        assert "E = E theorem prover" in caption
        assert "V = Vampire" in caption


def test_detached_figure_caption_missing_definition_is_detected() -> None:
    caption = "Suggested Upper Merged Ontology (SUMO) source graph."
    markdown = f"![{caption}](figures/graph.png){{#fig:graph}}"
    assert _undefined_first_uses(_figure_captions(markdown)["graph"]) == []
    broken = markdown.replace("Suggested Upper Merged Ontology (SUMO)", "SUMO")
    assert _undefined_first_uses(_figure_captions(broken)["graph"]) == ["SUMO"]


@pytest.mark.parametrize(
    "text, expected",
    [
        ("The capture APIs return data.", ["APIs"]),
        ("The API returns data.", ["API"]),
        ("The capture APIs. Later: application programming interfaces (APIs).", ["APIs"]),
        ("Application programming interfaces (APIs) return data.", []),
        ("Application programming interface (API) supplies APIs.", []),
        ("Read [API.md](docs/API.md) and `response.json` examples.", []),
        ("A JSON response follows [API.md](docs/API.md).", ["JSON"]),
        ("An `API` returns structured responses.", ["API"]),
        ("Application programming interface (`API`) returns data.", []),
        ("A `JSON` example.", ["JSON"]),
        ("Use `--output JSON` and `get_JSON()`.", []),
        ("UTC and DOI are identifiers.", ["DOI", "UTC"]),
        ("The SHA256 fingerprint.", ["SHA256"]),
        ("Secure Hash Algorithm 256-bit (SHA-256) then SHA256.", []),
    ],
)
def test_first_use_handles_plural_acronyms_and_literal_file_names(
    text: str, expected: list[str]
) -> None:
    assert _undefined_first_uses(text) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("E/V campaigns run.", ["E", "Vampire"]),
        ("E campaigns run. E/V agrees.", ["Vampire"]),
        ("E/V agrees. E and Vampire run.", ["E", "Vampire"]),
        ("E and Vampire (E/V) run.", []),
        ("```bash\nE/V --help\n```", []),
    ],
)
def test_prover_shorthand_requires_prior_names(text: str, expected: list[str]) -> None:
    assert _unintroduced_provers(text) == expected


def test_first_use_check_rejects_a_late_definition() -> None:
    assert _undefined_first_uses("An ATP query. Later: automated theorem proving (ATP).") == ["ATP"]
    assert _undefined_first_uses("automated theorem proving (ATP) executes a query.") == []


def test_sha256_first_use_rejects_missing_and_late_expansions() -> None:
    assert _undefined_first_uses("The source SHA-256 binds the bytes.") == ["SHA-256"]
    assert _undefined_first_uses(
        "The source SHA-256 binds bytes. Secure Hash Algorithm 256-bit (SHA-256)."
    ) == ["SHA-256"]
    assert _undefined_first_uses("Secure Hash Algorithm 256-bit (SHA-256) binds the bytes.") == []


def test_cover_has_no_unexplained_prover_or_source_abbreviations(
    tmp_path: Path, git_commit: Callable[[Path], str]
) -> None:
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure
    from matplotlib.text import Text

    from rikishi.fep import demo
    from rikishi.manuscript_figures import _cover, _validate_example
    from rikishi.manuscript_provenance import CorpusMeasurement
    from rikishi.ontology import OntologyIndex

    source = tmp_path / "source"
    source.mkdir()
    (source / "Merge.kif").write_text("(subclass Physical Entity)\n", encoding="utf-8")
    git_commit(source)
    index = OntologyIndex(tmp_path / "index.sqlite")
    index.build(source)
    figure = Figure(figsize=(7.2, 6.4), dpi=100)
    canvas = FigureCanvasAgg(figure)
    _cover(
        figure,
        _validate_example(demo()),
        CorpusMeasurement.model_validate(index.stats()),
        index.neighborhood("Entity", relation="subclass"),
        4,
    )
    canvas.draw()
    copy = " ".join(text.get_text() for text in figure.findobj(Text))
    assert "ATP query" not in copy
    assert "SUO-KIF" not in copy
    assert "FINITE FEP ILLUSTRATION" not in copy
    assert "Automated theorem" in copy
    assert "Kullback-Leibler" in copy
    renderer = canvas.get_renderer()
    visible = [text for text in figure.findobj(Text) if text.get_text().strip()]
    for text in visible:
        assert figure.bbox.contains(*text.get_window_extent(renderer).get_points()[0])
        assert figure.bbox.contains(*text.get_window_extent(renderer).get_points()[1])

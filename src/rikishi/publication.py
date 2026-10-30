from __future__ import annotations

import hashlib
import json
import re
import tomllib
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib.resources import files
from pathlib import Path
from typing import Annotated, Final

import yaml
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, TypeAdapter

from rikishi import fep
from rikishi.manuscript_provenance import (
    CorpusMeasurement,
    ProvenanceError,
    contained_path,
    hydrate_manuscript,
    require_evidence,
)
from rikishi.publication_abstracts import (
    GraphicalAbstract,
    abstract_pages_latex,
    abstract_pages_markdown,
)
from rikishi.publication_typography import SCIENTIFIC_NOTATION_SCRIPT

type Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
type Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
PACKAGE_MODEL: Final = "package:rikishi/data/fep-example.json"


class _Checked(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid", allow_inf_nan=False)


class Cover(_Checked):
    image: Text
    alt: Text


class Paper(_Checked):
    title: Text
    subtitle: Text
    date: Text
    year: Text
    cover: Cover
    graphical_abstracts: list[GraphicalAbstract] = Field(min_length=3, max_length=3)


class Author(_Checked):
    name: Text
    affiliations: list[Text] = Field(min_length=1)
    orcid: Annotated[str, Field(pattern=r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")] | None = None


class RenderingPolicy(_Checked):
    section_breaks: bool
    include_date: bool
    figure_height_fraction: float = Field(gt=0, le=1)
    cover_height_fraction: float = Field(gt=0, le=1)
    front_matter_figure_height_fraction: float = Field(gt=0, le=1)


class PublicationPolicy(_Checked):
    """Share one page-margin authority across the full-width PDF and HTML editions."""

    document_kind: Text
    decimal_places: int = Field(ge=0)
    font_size_pt: int = Field(gt=0)
    margin_mm: float = Field(gt=0)
    web_body_font_px: int = Field(ge=17)
    link_color_hex: Annotated[str, Field(pattern=r"^[0-9A-Fa-f]{6}$")]
    figure_dpi: int = Field(gt=0)
    citation_style: Text
    citation_style_sha256: Digest
    citation_style_repository: Text
    citation_style_revision: Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]


class PublicationSettings(_Checked):
    paper: Paper
    authors: list[Author] = Field(min_length=1)
    language: Text
    rendering: RenderingPolicy
    publication: PublicationPolicy


class _FormalReceipt(_Checked):
    model_config = ConfigDict(extra="ignore")
    commit: Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]
    compiler_version: Text
    source_sha256: dict[str, Digest] = Field(min_length=1)
    declaration_axioms: Text
    dependency_cache_files: int = Field(ge=0)
    scope: Text


@dataclass(frozen=True, slots=True)
class PublicationContext:
    settings: PublicationSettings
    example: fep.DemoResult
    values: dict[str, str]
    input_sha256: dict[str, str]
    metadata: dict[str, object]
    template_config: dict[str, object]
    frontmatter: str


def publication_headers(policy: PublicationPolicy, *, edition: str,
                        graphical_abstracts: list[GraphicalAbstract] | None = None) -> list[str]:
    """Supply edition styles through Pandoc metadata, leaving the native snapshot intact."""
    if edition == "pdf":
        headers = [
            r"\usepackage{etoolbox}",
            r"\AtBeginDocument{\definecolor{red}{HTML}{" + policy.link_color_hex + "}}",
            (r"\AtBeginDocument{\let\AttributeTok\KeywordTok\let\BaseNTok\KeywordTok"
             r"\let\DecValTok\KeywordTok\let\FloatTok\KeywordTok}"),
            r"\AtBeginDocument{\clubpenalty=10000\widowpenalty=10000\displaywidowpenalty=10000}",
            r"\AtBeginEnvironment{thebibliography}{\interlinepenalty=10000}",
            # Indirect naming prevents Pandoc expanding the later abstract patch target.
            (r"\csletcs{rikishiOriginalTableOfContents}{tableofcontents}"
             r"\csdef{tableofcontents}{\begingroup\fontsize{10pt}{12pt}\selectfont"
             r"\setlength{\parskip}{0pt}\csuse{rikishiOriginalTableOfContents}\endgroup}"),
        ]
        if graphical_abstracts is not None:
            headers.append(r"\pretocmd{\tableofcontents}{" + abstract_pages_latex(graphical_abstracts)
                           + r"}{}{\PackageError{rikishi}{Cannot insert graphical abstracts}{}}")
        return headers
    if edition == "html":
        return [f"""<style id="rikishi-publication-policy">
body {{ --rikishi-space-1: 4px; --rikishi-space-2: 8px; --rikishi-space-3: 12px; --rikishi-space-4: 16px; --rikishi-space-6: 24px; --rikishi-radius: 4px; }}
html body {{ font-size: {policy.web_body_font_px}px; box-sizing: border-box; width: 100%; max-width: none; margin: 0; padding: {policy.margin_mm:g}mm; }}
body code {{ font-size: max(15px, 0.85em); }}
html .figure-full-size-label {{ font-size: max(15px, 0.875rem); }}
body .toc a, body #TOC a {{ min-height: 44px; }}
body .toc li, body #TOC li {{ margin-block: var(--rikishi-space-2); }}
body .toc {{ padding: var(--rikishi-space-4); margin-bottom: var(--rikishi-space-6); border-radius: var(--rikishi-radius); }}
@media (max-width: 600px) {{ html body {{ padding: min({policy.margin_mm:g}mm, 4vw); }} }}
body p, body li {{ max-width: none; }}
body .figure-long-description > p, body .figure-exact-values {{ max-width: none; }}
body .table-scroll {{ max-width: 100%; overflow-x: auto; }}
body .table-scroll > table {{ display: table; width: 100%; min-width: 100%; table-layout: auto; }}
body .table-scroll th, body .table-scroll td {{ min-width: 8rem; max-width: 32rem; padding: var(--rikishi-space-2); vertical-align: top; overflow-wrap: anywhere; word-break: normal; }}
body .rikishi-scientific-number {{ white-space: nowrap; overflow-wrap: normal; word-break: normal; }}
body pre, body pre code {{ white-space: pre-wrap; overflow-wrap: anywhere; word-break: normal; }}
body pre {{ background-color: rgb(44, 62, 80); color: rgb(248, 250, 252); padding: var(--rikishi-space-3); border-radius: var(--rikishi-radius); }}
body pre code {{ background: transparent; color: inherit; }}
body pre code span[class] {{ background: transparent; color: inherit; }}
body pre code span.at, body pre code span.bn, body pre code span.dv, body pre code span.fl {{ color: rgb(183, 228, 199); font-weight: bold; }}
body pre code span.kw, body pre code span.cf, body pre code span.dt {{ color: rgb(201, 228, 255); }}
body pre code span.st, body pre code span.ch, body pre code span.ss {{ color: rgb(255, 229, 180); }}
body pre code span.co, body pre code span.cv, body pre code span.ca {{ color: rgb(213, 220, 227); }}
body div.sourceCode {{ overflow: visible; }}
body a {{ color: #{policy.link_color_hex}; }}
</style>""", SCIENTIFIC_NOTATION_SCRIPT]
    raise ValueError(f"Unsupported publication style edition: {edition}")


def _input_bytes(root: Path, identifier: str) -> bytes:
    if identifier == PACKAGE_MODEL:
        return files("rikishi").joinpath("data", "fep-example.json").read_bytes()
    require_evidence(":" not in identifier and "\\" not in identifier, "Invalid publication input path")
    path = contained_path(root, identifier)
    require_evidence(path.is_file() and not path.is_symlink(), f"Missing regular input: {identifier}")
    return path.read_bytes()


def verify_publication_inputs(root: Path, input_sha256: dict[str, str]) -> None:
    """Reject changed publication inputs, resolving only contained files or the exact package ID."""
    fixed = {"config/manuscript.yaml", "pyproject.toml", "output/formalization/verification.json"}
    require_evidence(fixed <= input_sha256.keys() and len(input_sha256) == len(fixed) + 2,
                     "Publication input manifest requires all authorities and one model")
    observed: dict[str, bytes] = {}
    for identifier, digest in input_sha256.items():
        require_evidence(bool(re.fullmatch(r"[0-9a-f]{64}", digest)), "Invalid input SHA-256")
        observed[identifier] = _input_bytes(root, identifier)
        actual = hashlib.sha256(observed[identifier]).hexdigest()
        require_evidence(actual == digest, f"Publication input changed: {identifier}")
    policy = PublicationSettings.model_validate(yaml.safe_load(observed["config/manuscript.yaml"])).publication
    parts = re.split(r"(\{\{[A-Z][A-Z0-9_]*\}\})", policy.citation_style)
    pattern = "".join(".*" if part.startswith("{{") else re.escape(part) for part in parts)
    styles = [key for key in input_sha256.keys() - fixed if key != PACKAGE_MODEL
              and input_sha256[key] == policy.citation_style_sha256 and re.fullmatch(pattern, key)]
    require_evidence(len(styles) == 1,
                     "Publication manifest is missing its configured citation style")
    model_id, = input_sha256.keys() - fixed - {styles[0]}
    fep.DemoParameters.model_validate_json(observed[model_id])


def _formal_values(root: Path, receipt: bytes) -> dict[str, str]:
    formal = _FormalReceipt.model_validate_json(receipt)
    require_evidence(formal.commit == fep.PIN, "Formal receipt commit differs from FEP pin")
    for source in formal.source_sha256:
        contained_path(root, source)
    modules = [s for s in formal.source_sha256 if s.startswith("lean/") and s.endswith(".lean")]
    require_evidence(fep.SOURCE in modules, "Formal receipt is missing the finite source module")
    declarations = re.findall(
        r"^'FEP\.FiniteInformation\.([^']+)' depends on axioms: \[[^\]\n]*\]$",
        formal.declaration_axioms, re.MULTILINE,
    )
    require_evidence(
        sorted(declarations) == sorted(fep.DECLARATIONS)
        and len(formal.declaration_axioms.splitlines()) == len(declarations),
        "Formal receipt declaration counts differ from the pinned inspection",
    )
    compiler = re.match(r"Lean \(version ([^,\s]+),", formal.compiler_version)
    if compiler is None:
        raise ProvenanceError("Unrecognized formal compiler version")
    return {
        "FORMAL_COMMIT": formal.commit, "LEAN_VERSION": compiler[1],
        "FORMAL_MODULE_COUNT": str(len(modules)),
        "FORMAL_DECLARATION_COUNT": str(len(declarations)),
        "FORMAL_CACHE_FILES": str(formal.dependency_cache_files), "FORMAL_SCOPE": formal.scope,
    }


def load_publication_context(
    root: Path, corpus: CorpusMeasurement, *, parameters_path: Path | None = None,
    rendered_at: datetime | None = None,
) -> PublicationContext:
    """Derive publication substitutions and native metadata from checked, hashed authorities."""
    project = root.resolve(strict=True)
    measurement = CorpusMeasurement.model_validate(corpus.model_dump())
    inputs = {name: _input_bytes(project, name) for name in (
        "config/manuscript.yaml", "pyproject.toml", "output/formalization/verification.json"
    )}
    settings = PublicationSettings.model_validate(yaml.safe_load(inputs["config/manuscript.yaml"]))
    model_id, parameter_file = PACKAGE_MODEL, None
    if parameters_path is not None:
        parameter_file = (project / parameters_path).resolve()
        require_evidence(parameter_file.is_relative_to(project), "Model parameters escape root")
        model_id = parameter_file.relative_to(project).as_posix()
        require_evidence(":" not in model_id and "\\" not in model_id,
                         "Model parameters require a contained relative file")
    inputs[model_id] = _input_bytes(project, model_id)
    parameters = fep.DemoParameters.model_validate_json(inputs[model_id])
    example = fep.demo(parameters)
    example["state_labels"] = list(parameters.state_labels)
    example["scan_points"] = parameters.scan_points
    version = TypeAdapter(Text).validate_python(
        tomllib.loads(inputs["pyproject.toml"].decode())["project"]["version"], strict=True
    )
    moment = rendered_at if rendered_at is not None else datetime.now(UTC)
    require_evidence(moment.utcoffset() is not None, "rendered_at must be timezone-aware")
    date = moment.astimezone(UTC).date()
    precision = settings.publication.decimal_places
    affiliations = list(dict.fromkeys(a for author in settings.authors for a in author.affiliations))
    values = {
        "PAPER_TITLE": settings.paper.title, "PAPER_SUBTITLE": settings.paper.subtitle,
        "AUTHOR_NAMES": ", ".join(author.name for author in settings.authors),
        "AUTHOR_AFFILIATIONS": "; ".join(affiliations), "DOCUMENT_DATE": date.isoformat(),
        "DOCUMENT_YEAR": str(date.year), "SOFTWARE_VERSION": version,
        "DOCUMENT_LABEL": f"{settings.publication.document_kind} v{version} ({date.isoformat()})",
        "DECIMAL_PLACES": str(precision), "MODEL_STATE_COUNT": str(len(parameters.prior)),
        "MODEL_SCAN_POINTS": str(parameters.scan_points),
        "MODEL_STATE_LABELS": "(" + ", ".join(parameters.state_labels) + ")",
        "MODEL_FIRST_STATE": parameters.state_labels[0], "MODEL_SECOND_STATE": parameters.state_labels[1],
        **_formal_values(project, inputs["output/formalization/verification.json"]),
    }
    for name, vector in {
        "PRIOR": example["prior"], "LIKELIHOOD": example["likelihood"],
        "CANDIDATE": example["candidate"], "POSTERIOR": example["result"]["exact_posterior"],
        "JOINT": [p * likelihood for p, likelihood in zip(parameters.prior, parameters.likelihood, strict=True)],
    }.items():
        values[f"MODEL_{name}"] = "(" + ", ".join(format(v, f"z.{precision}f") for v in vector) + ")"
    for name, value in {
        "EVIDENCE": example["result"]["evidence"], "FREE_ENERGY": example["result"]["free_energy"],
        "SURPRISE": example["result"]["surprise"], "KL": example["result"]["kl_to_posterior"],
        "OPTIMUM_F": example["optimum"]["free_energy"], "OPTIMUM_KL": example["optimum"]["kl_to_posterior"],
        "POSTERIOR_FIRST": example["result"]["exact_posterior"][0],
    }.items():
        values[f"FEP_{name}"] = format(value, f"z.{precision}f")
    values["FEP_RESIDUAL"] = format(example["result"]["identity_residual"], f".{precision}e")
    escaped = {key: json.dumps(value, ensure_ascii=False)[1:-1] for key, value in values.items()}
    settings = PublicationSettings.model_validate_json(
        hydrate_manuscript(settings.model_dump_json(), measurement, values=escaped).text
    )
    style = settings.publication.citation_style
    require_evidence(":" not in style, "Citation style must be a contained relative path")
    inputs[style] = _input_bytes(project, style)
    require_evidence(hashlib.sha256(inputs[style]).hexdigest() == settings.publication.citation_style_sha256,
                     "Citation style hash differs from publication policy")
    contained_path(project, settings.paper.cover.image)
    require_evidence(":" not in settings.paper.cover.image and "\\" not in settings.paper.cover.image,
                     "Cover image must be a contained relative path")
    metadata: dict[str, object] = {
        "title": settings.paper.title, "subtitle": settings.paper.subtitle,
        "author": [author.name for author in settings.authors], "date": settings.paper.date,
        "lang": settings.language, "geometry": f"margin={settings.publication.margin_mm:g}mm",
        "fontsize": f"{settings.publication.font_size_pt}pt", "bibliography": "references.bib",
        "csl": str(contained_path(project, style).resolve()), "biblio-style": "plainnat",
        "natbiboptions": "authoryear,round", "link-citations": True,
        "reference-section-title": "References", "crossref": {
            "eqnPrefix": "Equation", "figPrefix": "Figure", "secPrefix": "Section", "linkReferences": True,
        },
    }
    cover = settings.paper.cover
    identifiers = [f"{author.name}: [ORCID {author.orcid}](https://orcid.org/{author.orcid})"
                   for author in settings.authors if author.orcid is not None]
    frontmatter = "\n\n".join([
        *affiliations, *identifiers, f"![{cover.alt}]({cover.image}){{width=100%}}", r"\newpage"
    ]) + "\n\n" + abstract_pages_markdown(settings.paper.graphical_abstracts)
    template_config = settings.model_dump(mode="json")
    template_config["metadata"] = {
        "language": metadata["lang"], "geometry": metadata["geometry"],
        "fontsize": metadata["fontsize"], "documentclass": "article",
    }
    return PublicationContext(settings, example, values,
        {name: hashlib.sha256(content).hexdigest() for name, content in inputs.items()},
        metadata, template_config, frontmatter)

import hashlib
import json
import math
from datetime import UTC, date, datetime, timedelta, timezone
from importlib.resources import files
from pathlib import Path
from typing import Final

import pytest
import yaml
from pydantic import JsonValue

from rikishi import fep
from rikishi.manuscript_provenance import CorpusMeasurement
from rikishi.publication import (
    PublicationContext,
    load_publication_context,
    verify_publication_inputs,
)

NOW: Final = datetime(2031, 1, 1, 1, tzinfo=timezone(timedelta(hours=3)))
PACKAGED: Final = "package:rikishi/data/fep-example.json"
CONFIG: Final = "config/manuscript.yaml"
FORMAL: Final = "output/formalization/verification.json"
AUTHORITIES: Final = (CONFIG, "pyproject.toml", FORMAL, "config/references.csl", PACKAGED)
REQUIRED: Final = {
    "PAPER_TITLE", "PAPER_SUBTITLE", "AUTHOR_NAMES", "AUTHOR_AFFILIATIONS", "DOCUMENT_DATE",
    "DOCUMENT_YEAR", "DOCUMENT_LABEL", "SOFTWARE_VERSION", "MODEL_PRIOR", "MODEL_LIKELIHOOD",
    "MODEL_CANDIDATE", "MODEL_JOINT", "MODEL_POSTERIOR", "MODEL_STATE_COUNT", "FEP_EVIDENCE",
    "FEP_FREE_ENERGY", "FEP_SURPRISE", "FEP_KL", "FEP_RESIDUAL", "FEP_OPTIMUM_F", "FEP_OPTIMUM_KL",
    "FEP_POSTERIOR_FIRST", "FORMAL_COMMIT", "LEAN_VERSION", "FORMAL_MODULE_COUNT",
    "FORMAL_DECLARATION_COUNT", "FORMAL_CACHE_FILES", "MODEL_STATE_LABELS", "MODEL_FIRST_STATE",
    "MODEL_SECOND_STATE", "MODEL_SCAN_POINTS", "FORMAL_SCOPE", "DECIMAL_PLACES",
}


def set_setting(path: Path, dotted: str, value: JsonValue = None, *, remove: bool = False) -> None:
    data = yaml.safe_load(path.read_text())
    node = data
    parts = dotted.split(".")
    for key in parts[:-1]:
        node = node[int(key)] if key.isdigit() else node[key]
    if remove:
        del node[parts[-1]]
    else:
        node[parts[-1]] = value
    path.write_text(json.dumps(data) if path.suffix == ".json" else yaml.safe_dump(data))


def test_optional_author_orcid_is_projected_from_configuration(publication_root, corpus):
    identifier = "0000-0001-6232-9096"
    set_setting(publication_root / CONFIG, "authors.0.orcid", identifier)
    context = load_publication_context(publication_root, corpus, rendered_at=NOW)
    assert context.settings.authors[0].orcid == identifier
    assert context.template_config["authors"][0]["orcid"] == identifier
    assert f"[ORCID {identifier}](https://orcid.org/{identifier})" in context.frontmatter
    assert "Ada" in context.frontmatter


@pytest.mark.parametrize("identifier", ["missing", "https://orcid.org/0000-0001-6232-9096",
                                       "0000-0001-6232-909!"])
def test_invalid_author_orcid_is_rejected(publication_root, corpus, identifier):
    set_setting(publication_root / CONFIG, "authors.0.orcid", identifier)
    with pytest.raises(ValueError):
        load_publication_context(publication_root, corpus, rendered_at=NOW)


@pytest.fixture
def corpus() -> CorpusMeasurement:
    return CorpusMeasurement(source_commit="b" * 40, source_clean=True, files=2,
                             formulas=5, terms=3, edges=1, parse_errors=[])


@pytest.fixture
def publication_root(tmp_path: Path, project_root: Path) -> Path:
    root = tmp_path / "project"
    (root / "config").mkdir(parents=True)
    data = yaml.safe_load((project_root / CONFIG).read_text())
    style = data["publication"]["citation_style"]
    (root / style).parent.mkdir(parents=True, exist_ok=True)
    (root / style).write_bytes((project_root / style).read_bytes())
    data["paper"].update(title='A "quoted": title', subtitle="Measured: fixture")
    data["authors"] = [{"name": 'Ada "Quill"', "affiliations": ["Shared", "Lab A"]},
                       {"name": "Bo: Reader", "affiliations": ["Shared", "Lab B"]}]
    data["language"] = "fr"
    data["publication"].update(decimal_places=3, document_kind="Review draft", font_size_pt=12,
                               margin_mm=18, figure_dpi=144,
                               citation_style_sha256=hashlib.sha256((root / style).read_bytes()).hexdigest())
    (root / CONFIG).write_text(yaml.safe_dump(data))
    (root / "pyproject.toml").write_text('[project]\nname = "fixture"\nversion = "2.7.4"\n')
    (root / FORMAL).parent.mkdir(parents=True)
    receipt = {
        "commit": fep.PIN,
        "compiler_version": "Lean (version 4.35.0, fixture-platform, commit abc, Release)",
        "source_sha256": {fep.SOURCE: "a" * 64, "lean/FepSketches/other.lean": "b" * 64,
                          "generated/DeclarationAudit.lean": "c" * 64},
        "dependency_cache_files": 7,
        "declaration_axioms": "\n".join(
            f"'FEP.FiniteInformation.{name}' depends on axioms: [propext, Classical.choice]"
            for name in fep.DECLARATIONS),
        "scope": "Fixture receipt scope; preserve this string verbatim.",
        "unused_extra_field": {"ignored": True},
    }
    (root / FORMAL).write_text(json.dumps(receipt))
    return root


@pytest.mark.parametrize("style", [
    "config/references.csl", "config/{{SOFTWARE_VERSION}}.csl", "{{DOCUMENT_YEAR}}"])
def test_context_hydrates_coherent_native_metadata(publication_root, corpus, style):
    resolved = style.replace("{{SOFTWARE_VERSION}}", "2.7.4").replace("{{DOCUMENT_YEAR}}", "2030")
    (publication_root / resolved).write_bytes((publication_root / "config/references.csl").read_bytes())
    set_setting(publication_root / CONFIG, "publication.citation_style", style)
    context: PublicationContext = load_publication_context(publication_root, corpus, rendered_at=NOW)
    assert context.settings.publication.citation_style == resolved
    values = context.values
    assert set(values) == REQUIRED and all(isinstance(value, str) for value in values.values())
    assert values["DOCUMENT_DATE"] == "2030-12-31" and values["DOCUMENT_YEAR"] == "2030"
    assert values["DOCUMENT_LABEL"] == "Review draft v2.7.4 (2030-12-31)"
    assert values["SOFTWARE_VERSION"] == "2.7.4" and values["DECIMAL_PLACES"] == "3"
    assert values["PAPER_TITLE"] == 'A "quoted": title'
    assert all(name in values["AUTHOR_NAMES"] for name in ('Ada "Quill"', "Bo: Reader"))
    assert all(values["AUTHOR_AFFILIATIONS"].count(lab) == 1 for lab in ("Shared", "Lab A", "Lab B"))
    assert values["FORMAL_COMMIT"] == fep.PIN and values["LEAN_VERSION"] == "4.35.0"
    assert [values[key] for key in ("FORMAL_MODULE_COUNT", "FORMAL_DECLARATION_COUNT",
                                   "FORMAL_CACHE_FILES")] == ["2", "3", "7"]
    assert values["FORMAL_SCOPE"] == json.loads((publication_root / FORMAL).read_text())["scope"]
    assert context.metadata == {
        "title": values["PAPER_TITLE"], "subtitle": "Measured: fixture",
        "author": ['Ada "Quill"', "Bo: Reader"], "date": values["DOCUMENT_LABEL"], "lang": "fr",
        "geometry": "margin=18mm", "fontsize": "12pt", "bibliography": "references.bib",
        "csl": str((publication_root / resolved).resolve()),
        "biblio-style": "plainnat", "natbiboptions": "authoryear,round", "link-citations": True,
        "reference-section-title": "References", "crossref": {
            "eqnPrefix": "Equation", "figPrefix": "Figure", "secPrefix": "Section",
            "linkReferences": True},
    }
    native = context.settings.model_dump()
    for key in ("paper", "authors", "language", "rendering"):
        assert context.template_config[key] == native[key]
    assert context.template_config["metadata"] == {
        "language": context.metadata["lang"], "geometry": context.metadata["geometry"],
        "fontsize": context.metadata["fontsize"], "documentclass": "article"}
    assert native["paper"]["date"] == values["DOCUMENT_LABEL"]
    assert str(native["paper"]["year"]) == "2030"
    cover = native["paper"]["cover"]
    assert not (publication_root / cover["image"]).exists()
    assert f'![{cover["alt"]}]({cover["image"]}){{width=100%}}' in context.frontmatter
    assert "#fig" not in context.frontmatter
    assert context.frontmatter.rstrip().endswith(r"\newpage")
    affiliations = context.frontmatter.split("![", 1)[0]
    assert all(affiliations.count(lab) == 1 for lab in ("Shared", "Lab A", "Lab B"))
    assert [line for line in context.frontmatter.splitlines() if line][:3] == ["Shared", "Lab A", "Lab B"]
    assert all(text not in context.frontmatter for text in
               (values["PAPER_TITLE"], values["PAPER_SUBTITLE"], 'Ada "Quill"', "Bo: Reader"))
    assert set(context.input_sha256) == {CONFIG, resolved, "pyproject.toml", FORMAL, PACKAGED}
    assert verify_publication_inputs(publication_root, context.input_sha256) is None


def test_changed_model_controls_values_and_preserves_tiny_residual(publication_root, corpus):
    path = publication_root / "model.json"
    path.write_text(json.dumps({"prior": [0.25, 0.75], "likelihood": [0.9, 0.2],
                               "candidate": [0.6, 0.4], "scan_points": 9,
                               "state_labels": ["left", "right"]}))
    context = load_publication_context(publication_root, corpus, parameters_path=path, rendered_at=NOW)
    values, result = context.values, context.example["result"]
    energy = 0.6 * math.log(0.6 / 0.225) + 0.4 * math.log(0.4 / 0.15)
    assert result["evidence"] == pytest.approx(0.375)
    assert result["free_energy"] == pytest.approx(energy)
    assert context.example["state_labels"] == ["left", "right"]
    assert context.example["scan_points"] == 9
    assert len(context.example["scan"]) == 9
    assert {key: values[key] for key in ("MODEL_PRIOR", "MODEL_LIKELIHOOD", "MODEL_CANDIDATE",
                                       "MODEL_JOINT", "MODEL_POSTERIOR")} == {
        "MODEL_PRIOR": "(0.250, 0.750)", "MODEL_LIKELIHOOD": "(0.900, 0.200)",
        "MODEL_CANDIDATE": "(0.600, 0.400)", "MODEL_JOINT": "(0.225, 0.150)",
        "MODEL_POSTERIOR": "(0.600, 0.400)"}
    assert values["FEP_EVIDENCE"] == "0.375"
    assert values["FEP_FREE_ENERGY"] == values["FEP_SURPRISE"] == values["FEP_OPTIMUM_F"] == "0.981"
    assert values["FEP_KL"] == values["FEP_OPTIMUM_KL"] == "0.000"
    assert values["FEP_POSTERIOR_FIRST"] == "0.600"
    assert values["MODEL_STATE_COUNT"] == "2" and values["MODEL_SCAN_POINTS"] == "9"
    residual = result["identity_residual"]
    assert 0 < abs(residual) < 1e-12
    assert values["FEP_RESIDUAL"] == f"{residual:.3e}"
    assert float(values["FEP_RESIDUAL"]) != 0
    assert float(values["FEP_RESIDUAL"]) == pytest.approx(residual, rel=5e-4, abs=0)
    assert "model.json" in context.input_sha256 and PACKAGED not in context.input_sha256
    assert verify_publication_inputs(publication_root, context.input_sha256) is None


def test_default_timestamp_is_current_utc_date(publication_root, corpus):
    before = datetime.now(UTC).date()
    context = load_publication_context(publication_root, corpus)
    assert before <= date.fromisoformat(context.values["DOCUMENT_DATE"]) <= datetime.now(UTC).date()


@pytest.mark.parametrize("field,value", [
    ("publication.decimal_places", True), ("publication.decimal_places", -1),
    ("publication.citation_style_sha256", "z" * 64), ("unexpected", True),
    ("publication.citation_style", "config/missing.csl"), ("paper.title", "{{UNKNOWN}}"),
    ("publication.citation_style_sha256", "0" * 64), ("paper.title", "{{PAPER_TITLE}}"),
])
def test_invalid_settings_are_rejected(publication_root, corpus, field, value):
    set_setting(publication_root / CONFIG, field, value)
    with pytest.raises(ValueError):
        load_publication_context(publication_root, corpus, rendered_at=NOW)


@pytest.mark.parametrize("section", ["paper", "authors", "language", "rendering", "publication"])
def test_every_configuration_field_is_required(publication_root, corpus, section):
    original = (publication_root / CONFIG).read_bytes()
    settings = yaml.safe_load(original)
    paths = [section]
    if isinstance(settings[section], dict):
        paths += [f"{section}.{key}" for key in settings[section]]
    paths += {"paper": ["paper.cover.image", "paper.cover.alt"],
              "authors": ["authors.0.name", "authors.0.affiliations"]}.get(section, [])
    for dotted in paths:
        (publication_root / CONFIG).write_bytes(original)
        set_setting(publication_root / CONFIG, dotted, remove=True)
        with pytest.raises(ValueError):
            load_publication_context(publication_root, corpus, rendered_at=NOW)


@pytest.mark.parametrize("field,value", [
    ("commit", "0" * 40), ("compiler_version", "4.35.0"),
    ("source_sha256", {}), ("source_sha256", {fep.SOURCE: "bad"}),
    ("dependency_cache_files", -1), ("dependency_cache_files", True),
    *(("declaration_axioms", "\n".join(
        f"'FEP.FiniteInformation.{name}' depends on axioms: []" for name in names))
      for names in (fep.DECLARATIONS[1:], (*fep.DECLARATIONS, fep.DECLARATIONS[0]))),
])
def test_malformed_formal_receipt_is_rejected(publication_root, corpus, field, value):
    set_setting(publication_root / FORMAL, field, value)
    with pytest.raises(ValueError):
        load_publication_context(publication_root, corpus, rendered_at=NOW)


@pytest.mark.parametrize("field", ["publication.citation_style", "paper.cover.image", "model"])
@pytest.mark.parametrize("escape", ["traversal", "absolute", "symlink", "packaged-id"])
def test_publication_paths_cannot_escape(publication_root, corpus, field, escape):
    outside = publication_root.parent / "outside"
    outside.write_text("outside bytes")
    (publication_root / "escape").symlink_to(outside)
    collision = publication_root / PACKAGED
    collision.parent.mkdir(parents=True)
    collision.write_bytes(files("rikishi").joinpath("data/fep-example.json").read_bytes())
    paths = {"traversal": "../outside", "absolute": str(outside), "symlink": "escape",
             "packaged-id": PACKAGED}
    kwargs = {"parameters_path": Path(paths[escape])} if field == "model" else {}
    if field != "model":
        set_setting(publication_root / CONFIG, field, paths[escape])
    with pytest.raises(ValueError):
        load_publication_context(publication_root, corpus, rendered_at=NOW, **kwargs)


@pytest.mark.parametrize("field,value", [("source_clean", False), ("files", 0),
                                       ("parse_errors", [{"path": "broken.kif"}])])
def test_invalid_corpus_is_rejected(publication_root, corpus, field, value):
    invalid = corpus.model_copy(update={field: value})
    with pytest.raises(ValueError):
        load_publication_context(publication_root, invalid, rendered_at=NOW)


def test_naive_datetime_is_rejected(publication_root, corpus):
    with pytest.raises(ValueError):
        load_publication_context(publication_root, corpus, rendered_at=NOW.replace(tzinfo=None))


@pytest.mark.parametrize("removed,replacement,override", [
    *((key, None, None) for key in AUTHORITIES),
    *((key, key, "0" * 64) for key in AUTHORITIES),
    (CONFIG, CONFIG, "malformed"), (CONFIG, CONFIG, "policy"),
    (PACKAGED, "package:rikishi/data/other.json", None),
    (PACKAGED, "https://example.invalid/input", None), (PACKAGED, "../outside", None),
    (PACKAGED, "absolute", None), (PACKAGED, "escape", None),
    ("config/references.csl", "config/unrecognized.csl", None),
    (PACKAGED, "nonmodel.json", hashlib.sha256(b"{}").hexdigest()),
])
def test_verifier_rejects_invalid_manifest(publication_root, corpus, removed, replacement, override):
    manifest = load_publication_context(publication_root, corpus, rendered_at=NOW).input_sha256
    outside = publication_root.parent / "outside"
    outside.write_bytes(files("rikishi").joinpath("data/fep-example.json").read_bytes())
    (publication_root / "escape").symlink_to(outside)
    (publication_root / "config/unrecognized.csl").write_bytes(
        (publication_root / "config/references.csl").read_bytes())
    (publication_root / "nonmodel.json").write_bytes(b"{}")
    if override == "policy":
        set_setting(publication_root / CONFIG, "publication.citation_style_sha256", "0" * 64)
        override = hashlib.sha256((publication_root / CONFIG).read_bytes()).hexdigest()
    digest = manifest.pop(removed)
    if replacement is not None:
        key = str(outside) if replacement == "absolute" else replacement
        manifest[key] = digest if override is None else override
    with pytest.raises(ValueError):
        verify_publication_inputs(publication_root, manifest)

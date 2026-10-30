from datetime import UTC, datetime

import pytest

from rikishi.manuscript_verification import _Receipt
from rikishi.publication_office import OfficePagePolicyReport
from rikishi.publication_office_content import OfficeContentReceipt, OfficeMathReport


@pytest.fixture
def receipt_schema() -> _Receipt:
    return _Receipt.model_validate({
        "template_revision": "0" * 40,
        "template_worktree_used": False,
        "renderer_snapshot": "synthetic-schema-only-no-rendered-edition",
        "renderer_archive_sha256": "0" * 64,
        "renderer_imported_sources": {},
        "rendered_at": datetime(2000, 1, 1, tzinfo=UTC),
        "publication_inputs": {},
        "research_inputs": {},
        "inference_inputs": {},
        "bridge_inputs": {},
        "office_reference": {
            "reference_doc": "synthetic-schema-only",
            "default_reference_doc": "synthetic-schema-only-default",
            "reference_sha256": "0" * 64, "default_reference_sha256": "0" * 64,
            "pandoc_executable": "synthetic-schema-only-tool", "pandoc_sha256": "0" * 64,
            "pandoc_version": "synthetic-schema-only-version",
            "geometry": OfficePagePolicyReport("0" * 64, 12, 215.9, 279.4, 680, 12240, 15840, 1),
            "actual": OfficePagePolicyReport("0" * 64, 12, 215.9, 279.4, 680, 12240, 15840, 1),
        },
        "office_content": OfficeContentReceipt(1, "0" * 64, "0" * 64, "0" * 64, "0" * 64, 0, 0, 0, ()),
        "office_math": OfficeMathReport((), 0, 0),
        "report_inputs": {},
        "source_sha256": "0" * 64,
        "bibliography_sha256": "0" * 64,
        "corpus_export_sha256": "0" * 64,
        "analytics_sha256": "0" * 64,
        "sumo_demonstrations_sha256": "0" * 64,
        "ontology_structure_sha256": "0" * 64,
        "substitutions": {},
        "source_checks": {
            "citation_ids": [], "citation_count": 0, "citation_occurrences": 0,
            "bibliography_count": 0, "equation_labels": [], "equation_count": 0,
            "figure_labels": [], "figure_count": 0, "section_labels": [],
            "section_count": 0, "formalism_labels": [], "formalism_count": 0,
        },
        "numerical_result": {},
        "editions": {},
        "artifacts": [],
    })

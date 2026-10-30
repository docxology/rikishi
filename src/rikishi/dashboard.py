"""Read-only ontology dashboard and portable measured reports."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from rikishi import __version__
from rikishi.analytics import CorpusAnalytics, measure_corpus
from rikishi.bridge_models import BridgeReport, BridgeStudy
from rikishi.bridge_views import BridgeCaseView
from rikishi.corpus_query import FileQuery, FormulaQuery, QueryError
from rikishi.fep import DemoResult, demo, free_energy
from rikishi.graph_types import (
    FilePage,
    FormulaPage,
    Neighborhood,
    RelationSummaryResult,
    TaxonomyPath,
    TaxonomyResult,
)
from rikishi.ontology import OntologyIndex
from rikishi.ontology_analysis import TaxonomyQuery
from rikishi.taxonomy_paths import TaxonomyPathQuery

STATIC = Path(__file__).with_name("static")


def create_app(index_path: Path) -> FastAPI:
    """Serve an existing index; no HTTP endpoint mutates the corpus."""
    if not Path(index_path).is_file():
        raise FileNotFoundError(f"Build the ontology index first: {index_path}")
    index = OntologyIndex(index_path)
    app = FastAPI(title="Rikishi ontology workbench", version=__version__)

    @app.get("/api/bridge/catalog")
    def bridge_catalog() -> BridgeStudy:
        from rikishi.bridge_study import catalog

        return catalog()

    @app.get("/api/bridge/report")
    def bridge_report(
        report: str = Query(min_length=1, max_length=2048),
        sha256: str = Query(pattern=r"^[0-9a-f]{64}$"),
    ) -> BridgeReport:
        from rikishi.bridge_views import inspect_report

        try:
            return inspect_report(index.path.parent.parent, report, sha256)
        except FileNotFoundError as error:
            raise HTTPException(404, "Bridge report not found") from error
        except (ValueError, OSError) as error:
            raise HTTPException(422, str(error)) from error

    @app.get("/api/bridge/case")
    def bridge_case(
        report: str = Query(min_length=1, max_length=2048),
        sha256: str = Query(pattern=r"^[0-9a-f]{64}$"),
        case_id: str = Query(min_length=1, max_length=200),
        prover: Literal["e", "v"] = "e",
    ) -> BridgeCaseView:
        from rikishi.bridge_views import inspect_case
        from rikishi.inference_views import CaseSelection

        try:
            return inspect_case(index.path.parent.parent, CaseSelection(report, sha256, case_id, prover))
        except (FileNotFoundError, KeyError) as error:
            raise HTTPException(404, "Bridge case not found") from error
        except (ValueError, OSError) as error:
            raise HTTPException(422, str(error)) from error

    @app.get("/api/bridge/explorer", response_class=HTMLResponse)
    def bridge_explorer(
        report: str = Query(min_length=1, max_length=2048),
        sha256: str = Query(pattern=r"^[0-9a-f]{64}$"),
    ) -> HTMLResponse:
        from rikishi.bridge_figures import bridge_explorer_html, build_bridge_figure_inputs
        from rikishi.inference_views import report_path

        try:
            path = report_path(index.path.parent.parent, report)
            inputs = build_bridge_figure_inputs(path, trusted_report_sha256=sha256)
            return HTMLResponse(bridge_explorer_html(inputs), headers={"X-Content-Type-Options": "nosniff"})
        except FileNotFoundError as error:
            raise HTTPException(404, "Bridge evidence not found") from error
        except (ValueError, OSError) as error:
            raise HTTPException(422, str(error)) from error

    @app.get("/api/inference/catalog")
    def inference_catalog() -> dict[str, object]:
        from rikishi.inference_study import catalog

        return catalog().model_dump(mode="json")

    @app.get("/api/inference/report")
    def inference_report(
        report: str = Query(min_length=1, max_length=2048),
        sha256: str = Query(pattern=r"^[0-9a-f]{64}$"),
    ) -> dict[str, object]:
        from rikishi.inference_views import inspect_report

        try:
            return inspect_report(index.path.parent.parent, report, sha256)
        except FileNotFoundError as error:
            raise HTTPException(404, "Inference report not found") from error
        except (ValueError, OSError) as error:
            raise HTTPException(422, str(error)) from error

    @app.get("/api/inference/published")
    def inference_published() -> dict[str, object]:
        from rikishi.inference_views import published_report

        try:
            return published_report(index.path.parent.parent)
        except FileNotFoundError as error:
            raise HTTPException(404, "No published inference campaign; run inference-run then inference-publish") from error
        except (ValueError, OSError) as error:
            raise HTTPException(422, str(error)) from error

    @app.get("/api/inference/case")
    def inference_case(
        report: str = Query(min_length=1, max_length=2048),
        sha256: str = Query(pattern=r"^[0-9a-f]{64}$"),
        case_id: str = Query(min_length=1, max_length=200),
        prover: Literal["e", "v"] = "e",
    ) -> dict[str, object]:
        from rikishi.inference_views import CaseSelection, inspect_case

        try:
            return inspect_case(index.path.parent.parent, CaseSelection(report, sha256, case_id, prover))
        except (FileNotFoundError, KeyError) as error:
            raise HTTPException(404, "Inference case not found") from error
        except (ValueError, OSError) as error:
            raise HTTPException(422, str(error)) from error

    @app.exception_handler(QueryError)
    async def invalid_query(_request: Request, exc: QueryError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.get("/", include_in_schema=False)
    def home() -> FileResponse:
        return FileResponse(STATIC / "index.html")

    @app.get("/api/stats")
    def stats() -> dict:
        return index.stats()

    @app.get("/api/analytics", response_model=None)
    def analytics() -> CorpusAnalytics:
        return measure_corpus(index)

    @app.get("/api/corpus/files", response_model=None)
    def corpus_files(
        path: str = Query("", max_length=2048),
        sort: Literal["path", "formulas"] = "path",
        descending: bool = False,
        limit: int = Query(50, ge=1, le=500),
        offset: int = Query(0, ge=0, le=1_000_000),
    ) -> FilePage:
        return index.corpus_files(FileQuery(path, sort, descending, limit, offset))

    @app.get("/api/corpus/formulas", response_model=None)
    def corpus_formulas(
        text: str = Query("", max_length=2048),
        head: str = Query("", max_length=2048),
        path: str = Query("", max_length=2048),
        term: str = Query("", max_length=2048),
        limit: int = Query(50, ge=1, le=500),
        offset: int = Query(0, ge=0, le=1_000_000),
    ) -> FormulaPage:
        return index.formula_search(FormulaQuery(text, head, path, term, limit, offset))

    @app.get("/api/corpus/relations", response_model=None)
    def corpus_relations() -> RelationSummaryResult:
        return index.relation_inventory()

    @app.get("/api/taxonomy", response_model=None)
    def taxonomy(
        relation: Literal["subclass", "subrelation"] = "subclass",
        path: str = Query("", max_length=2048),
        limit: int = Query(50, ge=1, le=500),
        offset: int = Query(0, ge=0, le=1_000_000),
    ) -> TaxonomyResult:
        return index.taxonomy_analysis(TaxonomyQuery(relation, path, limit, offset))

    @app.get("/api/taxonomy/path", response_model=None)
    def taxonomy_path(
        source: str = Query(min_length=1, max_length=2048),
        target: str = Query(min_length=1, max_length=2048),
        relation: Literal["subclass", "subrelation"] = "subclass",
        path: str = Query("", max_length=2048),
        max_depth: int = Query(20, ge=0, le=100),
        max_visited: int = Query(10_000, ge=1, le=100_000),
    ) -> TaxonomyPath:
        try:
            return index.taxonomy_path(
                TaxonomyPathQuery(source, target, relation, path, max_depth, max_visited)
            )
        except KeyError as exc:
            raise HTTPException(404, "Path endpoint not found in this index") from exc

    @app.get("/api/fep")
    def fep(q: float = Query(0.5, ge=0, le=1)) -> DemoResult:
        example = demo()
        example["candidate"] = [q, 1 - q]
        example["result"] = free_energy(
            example["prior"], example["likelihood"], example["candidate"]
        )
        return example

    @app.get("/api/search")
    def search(
        q: str = Query(min_length=1, max_length=200), limit: int = Query(30, ge=1, le=100)
    ) -> list:
        return index.search(q, limit=limit)

    @app.get("/api/terms/{name}")
    def term(name: str) -> dict:
        try:
            return index.term(name)
        except KeyError as exc:
            raise HTTPException(404, "Term not found in this index") from exc

    @app.get("/api/graph")
    def graph(
        term: str = Query(min_length=1, max_length=200),
        limit: int = Query(40, ge=1, le=100),
        relation: str | None = Query(None, min_length=1, max_length=200),
    ) -> Neighborhood:
        if relation is not None and not relation.strip():
            raise HTTPException(422, "relation must be nonempty when supplied")
        try:
            return index.neighborhood(term, limit=limit, relation=relation)
        except KeyError as exc:
            raise HTTPException(404, "Term not found in this index") from exc

    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    return app

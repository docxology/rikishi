"""Read-only ontology dashboard and portable measured reports."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from rikishi.analytics import CorpusAnalytics, measure_corpus
from rikishi.fep import demo, free_energy
from rikishi.ontology import OntologyIndex
from rikishi.reports import build_report

__all__ = ["build_report", "create_app"]

STATIC = Path(__file__).with_name("static")


def create_app(index_path: Path) -> FastAPI:
    """Serve an existing index; no HTTP endpoint mutates the corpus."""
    if not Path(index_path).is_file():
        raise FileNotFoundError(f"Build the ontology index first: {index_path}")
    index = OntologyIndex(index_path)
    app = FastAPI(title="Rikishi ontology workbench", version="0.1.0")

    @app.get("/", include_in_schema=False)
    def home() -> FileResponse:
        return FileResponse(STATIC / "index.html")

    @app.get("/api/stats")
    def stats() -> dict:
        return index.stats()

    @app.get("/api/analytics", response_model=None)
    def analytics() -> CorpusAnalytics:
        return measure_corpus(index)

    @app.get("/api/fep")
    def fep(q: float = Query(0.5, ge=0, le=1)) -> dict:
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
        term: str = Query(min_length=1, max_length=200), limit: int = Query(40, ge=1, le=100)
    ) -> dict:
        try:
            index.term(term)
            return index.neighborhood(term, limit=limit)
        except KeyError as exc:
            raise HTTPException(404, "Term not found in this index") from exc

    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    return app

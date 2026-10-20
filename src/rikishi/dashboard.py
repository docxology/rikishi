"""Read-only ontology dashboard and portable measured reports."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from rikishi.fep import demo, free_energy
from rikishi.ontology import OntologyIndex

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

    @app.get("/api/fep")
    def fep(q: float = Query(0.5, ge=0, le=1)) -> dict:
        example = demo()
        example["candidate"] = [q, 1 - q]
        example["result"] = free_energy(example["prior"], example["likelihood"], example["candidate"])
        return example

    @app.get("/api/search")
    def search(q: str = Query(min_length=1, max_length=200), limit: int = Query(30, ge=1, le=100)) -> list:
        return index.search(q, limit=limit)

    @app.get("/api/terms/{name}")
    def term(name: str) -> dict:
        try:
            return index.term(name)
        except KeyError as exc:
            raise HTTPException(404, "Term not found in this index") from exc

    @app.get("/api/graph")
    def graph(term: str = Query(min_length=1, max_length=200), limit: int = Query(40, ge=1, le=100)) -> dict:
        try:
            index.term(term)
            return index.neighborhood(term, limit=limit)
        except KeyError as exc:
            raise HTTPException(404, "Term not found in this index") from exc

    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    return app


def build_report(index_path: Path, output_dir: Path) -> dict:
    """Export measured corpus data, SVG/PNG chart, and a standalone HTML report."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    index = OntologyIndex(index_path)
    stats = index.stats()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(stats, indent=2, ensure_ascii=True)
    (output_dir / "corpus.json").write_text(payload + "\n", encoding="utf-8")
    rows = stats["top_files"][:12]
    fig, ax = plt.subplots(figsize=(10, 6), layout="constrained")
    ax.barh([row["path"] for row in rows][::-1], [row["formulas"] for row in rows][::-1], color="#176b62")
    ax.set(xlabel="Top-level KIF formulas", title="SUMO corpus: largest indexed source files")
    ax.spines[["top", "right"]].set_visible(False)
    for suffix in ("svg", "png"):
        fig.savefig(output_dir / f"corpus-files.{suffix}", dpi=180)
    plt.close(fig)
    html = (STATIC / "report.html").read_text(encoding="utf-8")
    html = html.replace("__STYLE__", (STATIC / "style.css").read_text(encoding="utf-8"))
    html = html.replace("__DATA__", payload.replace("<", "\\u003c"))
    (output_dir / "dashboard.html").write_text(html, encoding="utf-8")
    return {"html": str(output_dir / "dashboard.html"), "data": str(output_dir / "corpus.json"), "svg": str(output_dir / "corpus-files.svg"), "png": str(output_dir / "corpus-files.png")}

import json
from pathlib import Path
from typing import TypedDict

from rikishi.analytics import measure_corpus
from rikishi.ontology import OntologyIndex

STATIC = Path(__file__).with_name("static")


class ReportArtifacts(TypedDict):
    html: str
    data: str
    svg: str
    png: str
    analytics: str
    summary: str
    composition_svg: str
    composition_png: str


def build_report(index_path: Path, output_dir: Path) -> ReportArtifacts:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    index = OntologyIndex(index_path)
    stats = index.stats()
    measurements = measure_corpus(index)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(stats, indent=2, ensure_ascii=True)
    analytical_payload = json.dumps(measurements, indent=2, ensure_ascii=True)
    (output_dir / "corpus.json").write_text(payload + "\n", encoding="utf-8")
    (output_dir / "analytics.json").write_text(analytical_payload + "\n", encoding="utf-8")
    rows = stats["top_files"][:12]
    fig, ax = plt.subplots(figsize=(10, 6), layout="constrained")
    ax.barh(
        [row["path"] for row in rows][::-1],
        [row["formulas"] for row in rows][::-1],
        color="#176b62",
    )
    ax.set(xlabel="Top-level KIF formulas", title="SUMO corpus: largest indexed source files")
    ax.spines[["top", "right"]].set_visible(False)
    for suffix in ("svg", "png"):
        fig.savefig(output_dir / f"corpus-files.{suffix}", dpi=180)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), layout="constrained")
    predicates = measurements["predicates"][:10]
    remainder = measurements["formula_denominator"] - sum(r["count"] for r in predicates)
    labels = [r["label"] for r in predicates] + ["All remaining heads"]
    counts = [r["count"] for r in predicates] + [remainder]
    axes[0].barh(labels[::-1], counts[::-1], color="#176b62")
    axes[0].set(title="Formula head composition", xlabel="Top-level formulas (all heads included)")
    degrees = measurements["degree_distribution"]
    axes[1].scatter(
        [r["degree"] for r in degrees], [r["terms"] for r in degrees], color="#176b62", s=18
    )
    axes[1].set(
        xscale="symlog",
        yscale="symlog",
        title="Direct-edge degree distribution",
        xlabel="In + out degree (symlog; zero retained)",
        ylabel="Indexed symbols (symlog)",
    )
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
    for suffix in ("svg", "png"):
        fig.savefig(output_dir / f"corpus-composition.{suffix}", dpi=180)
    plt.close(fig)
    summary = (
        "# Indexed corpus measurements\n\n"
        f"Source revision: `{measurements['source_commit']}`. Clean source: `{measurements['source_clean']}`.\n\n"
        f"{measurements['formula_denominator']:,} top-level formulas in {measurements['indexed_files']:,} parsed files; "
        f"{measurements['rejected_files']:,} rejected files. Formula counts measure syntax.\n\n"
        f"{measurements['edge_assertions']:,} binary edge assertions reduce to {measurements['unique_edges']:,} distinct labeled directed triples. "
        f"{measurements['zero_degree_terms']:,} of {measurements['term_denominator']:,} indexed symbols have zero degree in this restricted graph.\n\n"
        "Degree includes both endpoints (self-loops count twice). The graph excludes nested assertions and inferred closure. "
        "No metric establishes ontology consistency, semantic completeness, or independent factual content. "
        "See docs/metrics.md for denominators and analytics.json for complete distributions.\n"
    )
    (output_dir / "measurements.md").write_text(summary, encoding="utf-8")
    html = (STATIC / "report.html").read_text(encoding="utf-8")
    html = html.replace("__STYLE__", (STATIC / "style.css").read_text(encoding="utf-8"))
    html = html.replace("__DATA__", payload.replace("<", "\\u003c"))
    html = html.replace("__ANALYTICS__", analytical_payload.replace("<", "\\u003c"))
    html = html.replace("__ANALYTICS_JS__", (STATIC / "analytics.js").read_text(encoding="utf-8"))
    (output_dir / "dashboard.html").write_text(html, encoding="utf-8")
    return ReportArtifacts(
        html=str(output_dir / "dashboard.html"),
        data=str(output_dir / "corpus.json"),
        svg=str(output_dir / "corpus-files.svg"),
        png=str(output_dir / "corpus-files.png"),
        analytics=str(output_dir / "analytics.json"),
        summary=str(output_dir / "measurements.md"),
        composition_svg=str(output_dir / "corpus-composition.svg"),
        composition_png=str(output_dir / "corpus-composition.png"),
    )

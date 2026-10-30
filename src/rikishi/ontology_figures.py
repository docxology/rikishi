import json
from pathlib import Path

from rikishi.ontology_observations import StructureReport, measure_source_structure
from rikishi.sumo_demonstrations import FrozenSource

WIDTH_MM = 174
HEIGHT_MM = 148


def render_ontology_structure(
    output: Path, source: FrozenSource, report: StructureReport, *, dpi: int,
) -> list[Path]:
    if type(dpi) is not int or not 72 <= dpi <= 1200:
        raise ValueError("Ontology figure dpi must be an integer between 72 and 1200")
    if report != measure_source_structure(source):
        raise ValueError("Ontology structure report differs from retained source")
    import matplotlib
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure
    from matplotlib.ticker import MaxNLocator, StrMethodFormatter
    from matplotlib.transforms import Bbox

    output.mkdir(parents=True, exist_ok=True)
    paths = [output / f"ontology-structure.{suffix}" for suffix in ("png", "svg", "json")]
    colors = ("#193449", "#176b62")
    with matplotlib.rc_context({"font.family": "DejaVu Sans", "svg.fonttype": "none",
                                "font.size": 8, "savefig.bbox": None}):
        figure = Figure(figsize=(WIDTH_MM / 25.4, HEIGHT_MM / 25.4), facecolor="white")
        FigureCanvasAgg(figure)
        try:
            figure.text(0.07, 0.95, f"SUMO | Direct taxonomy structure in {report.ontology_path}",
                        fontsize=12, weight="bold", color=colors[0])
            figure.text(0.07, 0.90, "A  Counts in each selected relation; duplicates removed for edges",
                        fontsize=8.5, color=colors[0])
            axes = figure.add_axes((0.22, 0.57, 0.65, 0.27))
            for position, graph in enumerate(report.graphs):
                for offset, count, label in (
                    (-0.17, graph.unique_edges, "distinct edges"),
                    (0.17, graph.node_count, "endpoint nodes"),
                ):
                    axes.barh(position + offset, count, height=0.26,
                              color=colors[position], alpha=1 if offset < 0 else 0.45,
                              hatch=None if offset < 0 else "///", label=label if position == 0 else None)
                    axes.annotate(f"{count:,}", (count, position + offset), xytext=(4, 0),
                                  textcoords="offset points", va="center", fontsize=8)
            largest = max((max(g.unique_edges, g.node_count) for g in report.graphs), default=0)
            axes.set(yticks=range(len(report.graphs)),
                     yticklabels=[g.relation for g in report.graphs], xlim=(0, max(1, largest * 1.2)))
            axes.invert_yaxis()
            axes.xaxis.set_major_locator(MaxNLocator(nbins=4, integer=True))
            axes.xaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
            axes.spines[["top", "right", "left"]].set_visible(False)
            axes.tick_params(axis="y", length=0)
            axes.legend(loc="lower left", bbox_to_anchor=(-0.04, 1.00), ncol=2,
                        frameon=False, fontsize=7.5)
            figure.text(0.07, 0.49, "B  Diagnostic counts use only endpoints of the selected relation",
                        fontsize=8.5, color=colors[0])
            table_axes = figure.add_axes((0.07, 0.18, 0.86, 0.27))
            table_axes.set_axis_off()
            metrics = [("Roots (zero direct parents)", "root_count"),
                       ("Nodes with multiple direct parents", "multiple_parent_count"),
                       ("Weakly connected components", "weak_component_count"),
                       ("Cyclic strongly connected components", "cyclic_component_count"),
                       ("Nodes in directed cycles", "cyclic_node_count"),
                       ("Self-loops", "self_loop_count")]
            table = table_axes.table(
                cellText=[[label, *(f"{getattr(g, key):,}" for g in report.graphs)]
                          for label, key in metrics],
                colLabels=["Source graph diagnostic", *(g.relation for g in report.graphs)],
                colWidths=[0.62, 0.19, 0.19], cellLoc="left", bbox=Bbox.from_bounds(0, 0, 1, 1),
            )
            table.auto_set_font_size(False)
            table.set_fontsize(7.8)
            for (row, _), cell in table.get_celld().items():
                cell.set_edgecolor("#dce4e5")
                cell.set_linewidth(0.5)
                if row == 0:
                    cell.set_facecolor("#f2f5f5")
                    cell.set_text_props(weight="bold")
            figure.text(0.07, 0.125, "Graph paths describe source syntax. Cycles do not certify inconsistency.",
                        fontsize=7.5, color=colors[0])
            figure.text(0.07, 0.085, f"Revision: {report.source_commit}", fontsize=7.5)
            figure.text(0.07, 0.05, f"Source SHA-256: {report.source_sha256}", fontsize=7.5)
            metadata = {"Description": report.model_dump_json()}
            figure.savefig(paths[0], dpi=dpi, metadata=metadata)
            figure.savefig(paths[1], metadata=metadata)
        finally:
            figure.clear()
    paths[2].write_text(json.dumps({"report": report.model_dump(mode="json"), "rendering": {
        "dpi": dpi, "width_mm": WIDTH_MM, "height_mm": HEIGHT_MM,
    }}, indent=2) + "\n")
    return paths

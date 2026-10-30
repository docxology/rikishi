from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from rikishi.ontology import OntologyIndex
from rikishi.ontology_analysis import TaxonomyQuery
from rikishi.sumo_demonstrations import FrozenSource


class TaxonomyCounts(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")
    relation: Literal["subclass", "subrelation"]
    assertion_count: int = Field(ge=0)
    unique_edges: int = Field(ge=0)
    node_count: int = Field(ge=0)
    root_count: int = Field(ge=0)
    multiple_parent_count: int = Field(ge=0)
    weak_component_count: int = Field(ge=0)
    cyclic_component_count: int = Field(ge=0)
    cyclic_node_count: int = Field(ge=0)
    self_loop_count: int = Field(ge=0)


class StructureReport(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")
    schema_version: Literal[1] = 1
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_commit: str
    ontology_path: str
    scope: Literal["complete retained source file; distinct direct taxonomy edges; no inference"]
    graphs: list[TaxonomyCounts]


def measure_source_structure(source: FrozenSource) -> StructureReport:
    raw = source.text.encode("utf-8")
    if sha256(raw).hexdigest() != source.sha256:
        raise ValueError("Ontology structure source SHA-256 differs")
    with TemporaryDirectory(prefix="rikishi-source-structure-") as temporary:
        root = Path(temporary)
        source_dir = root / "source"
        source_dir.mkdir()
        (source_dir / source.ontology_path).write_bytes(raw)
        index = OntologyIndex(root / "index.sqlite")
        stats = index.build(source_dir)
        if stats["parse_errors"]:
            raise ValueError("Ontology structure source has parse errors")
        graphs = []
        for relation in ("subclass", "subrelation"):
            measured = index.taxonomy_analysis(TaxonomyQuery(relation=relation, limit=1))
            graphs.append(TaxonomyCounts.model_validate({
                name: dict(measured)[name] for name in TaxonomyCounts.model_fields
            }))
    return StructureReport(
        source_sha256=source.sha256, source_commit=source.commit,
        ontology_path=source.ontology_path,
        scope="complete retained source file; distinct direct taxonomy edges; no inference",
        graphs=graphs,
    )


def structure_substitutions(report: StructureReport) -> dict[str, str]:
    rows = ["| Relation | Assertions | Distinct edges | Endpoint nodes | Roots | Multiple parents |",
            "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for graph in report.graphs:
        rows.append(f"| `{graph.relation}` | {graph.assertion_count} | {graph.unique_edges} | "
                    f"{graph.node_count} | {graph.root_count} | {graph.multiple_parent_count} |")
    return {"ONTOLOGY_STRUCTURE_TABLE": "\n".join(rows)}

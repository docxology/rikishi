import hashlib
import json
from pathlib import Path

from rikishi.ontology import OntologyIndex


def _constant(name: str) -> str:
    return "s_" + name.encode("utf-8").hex()


def taxonomy_problem(
    index: OntologyIndex, subject: str, target: str, output: Path, source: str = "Merge.kif"
) -> dict:
    index.term(subject)
    index.term(target)
    assertions = index.assertions("subclass", source)
    if not assertions:
        raise ValueError(f"No asserted subclass facts in {source}")
    lines = ["fof(transitivity,axiom,(![X,Y,Z]:((subclass(X,Y)&subclass(Y,Z))=>subclass(X,Z))))."]
    for number, assertion in enumerate(assertions):
        lines.append(
            f"fof(a{number},axiom,subclass({_constant(assertion['subject'])},{_constant(assertion['object'])}))."
        )
    lines.append(f"fof(goal,conjecture,subclass({_constant(subject)},{_constant(target)})).")
    problem = "\n".join(lines) + "\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(problem, encoding="utf-8")
    stats = index.stats()
    metadata = {
        "scope": "First-order taxonomic projection: direct subclass facts from one source file plus subclass transitivity. Not full SUMO inference.",
        "source_commit": stats["source_commit"],
        "source_clean": stats["source_clean"],
        "source_file_sha256": assertions[0]["source_sha256"],
        "source_file": source,
        "subject": subject,
        "target": target,
        "assertions": assertions,
        "problem_sha256": hashlib.sha256(problem.encode()).hexdigest(),
    }
    output.with_suffix(".json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata

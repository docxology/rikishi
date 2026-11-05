# Source-bound ontology demonstrations

These demonstrations inspect the Suggested Upper Merged Ontology (SUMO), whose
source uses the Standard Upper Ontology Knowledge Interchange Format (SUO-KIF).

`rikishi.sumo_demonstrations` delegates to the existing `OntologyIndex`, source
parser, source audit, taxonomy projection, and native E runtime. It selects
assertions by parsed expression, never by a fixed line number. It does not add
an ontology engine or change runtime semantics.

From the mounted checkout:

```bash
source scripts/env.sh
uv run python -c 'import sys; print(sys.prefix); print(sys.base_prefix)'
uv run python scripts/demonstrate_sumo.py \
  --output output/sumo-demonstrations.json
```

The output path must be inside the selected root and must be fresh. Source,
index, parse, hash and selection failures propagate; there is no automatic
reindexing or substitution of remembered examples. The default report performs
no automated theorem proving (ATP) invocation.

## Selected cases and their acceptance scope

| Case | Observation from the selected SUMO assertions | Projection limit |
| --- | --- | --- |
| `hierarchy` | Entity's Physical/Abstract partition, both direct subclass assertions, Process under Physical and Proposition under Abstract | The partition is not a binary edge; superclass assertions alone do not establish disjointness or exhaustiveness |
| `typing` | Process has a superclass; agent is an instance of CaseRole; ProbabilityFn is an instance of UnaryFunction | `subclass` and `instance` remain separate predicate labels; membership does not become subclasshood |
| `agent_signature` | Position 1 has domain Process; position 2 has domain AutonomousAgent | These ternary relation signatures are formulas, not indexed binary edges or demonstrated type-checking rules |
| `probability_signature` | ProbabilityFn is a UnaryFunction with domain Formula and range RealNumber | The binary range assertion is indexed; the argument-position domain assertion is not. This does not identify the function with a finite numerical distribution or equate Formula with Proposition |
| `nested_formula` | An implication contains an existential Process witness and an agent relation inside a modal possibility formula | Its nested agent expression is not a standalone asserted graph edge; no particular process or agent is inferred |

The exact source excerpts come from the report's `cases`, including the original
whitespace. Each citation records selected terms, predicate, start `line`,
`end_line`, `raw_kif`, excerpt `sha256`, and `indexed_binary_edge`. Source identity
is shared through `source.path`, `source.ontology_path`, `source.commit`,
`source.clean`, and the complete frozen `source.text` with its byte digest.

For a parsed source population \(S\), the restricted binary projection retains
only complete top-level expressions with a predicate and two atomic arguments,
both recognized as symbols by the existing parser. It excludes variables,
numeric positions, quoted strings and nested formulas. Counts describe assertion
occurrences, not deduplicated triples or inferred truths. `cited_formulas` counts
distinct source line/text pairs across cases, so a reused citation is counted
once. All observations are computed from the frozen source.

## Importable application programming interface (API) and portable replay

```python
import json
from pathlib import Path

from rikishi.ontology import OntologyIndex
from rikishi.sumo_demonstrations import (
    demonstrate_sumo,
    report_to_substitutions,
    validate_sumo_report,
)

root = Path.cwd()
report = demonstrate_sumo(OntologyIndex(root / ".rikishi/ontology.sqlite"), root)
payload = json.loads(report.model_dump_json())
validated = validate_sumo_report(payload)
substitutions = report_to_substitutions(validated)
```

`SumoReport` is a frozen Pydantic model with forbidden extra fields. The public
report has `schema_version`, `scope`, `source`, `selected_terms`, `cases` and
`observations`. Save `report.model_dump_json(indent=2)` as the pipeline artifact.

Both portable methods operate entirely on the report, with no filesystem or
index access. They check the retained source Secure Hash Algorithm 256-bit
(SHA-256) fingerprint, parse the complete frozen
text, repeat expression selection, regenerate exact citations and observations,
and require exact agreement. They reject changed excerpts, line ranges, excerpt
digests, selection identities, scope, counts, missing fields and malformed Knowledge Interchange Format (KIF) input.
They work after the original source and index have moved or disappeared.

Portable replay establishes internal agreement of retained bytes and derived
observations. It cannot independently authenticate the claimed Git commit or
protect against an adversary replacing a whole internally consistent report.
The live source audit and the pipeline's separate artifact binding supply that
provenance boundary.

`report_to_substitutions` returns these string-valued keys:

- `SUMO_SOURCE_PATH`, `SUMO_SOURCE_COMMIT`, `SUMO_SOURCE_SHA256`.
- `SUMO_SOURCE_FORMULAS`, `SUMO_PROJECTED_BINARY_EDGES`, `SUMO_CITED_FORMULAS`.
- `SUMO_HIERARCHY_KIF`, `SUMO_TYPING_KIF`, `SUMO_AGENT_SIGNATURE_KIF`,
  `SUMO_PROBABILITY_SIGNATURE_KIF`, `SUMO_NESTED_FORMULA_KIF`.

The KIF values are actual source excerpts joined with newlines. A manuscript
places its placeholders inside Markdown code fences and supplies captions and
interpretation separately; it need not transcribe the ontology. Counts arrive as
derived strings suitable for the same placeholder mechanism. A renderer can run
the live method once and stage the report; a relocated verifier then calls the
portable validator and substitutions method against that retained JavaScript Object Notation (JSON).

## Separate native taxonomy demonstration

```bash
source scripts/env.sh
uv run python scripts/demonstrate_sumo.py \
  --output output/sumo-native-source-report.json \
  --proof-directory output/sumo-native-taxonomy
```

The optional `prove_sumo_taxonomy(index, root, output)` freezes the source report
and stages the selected hierarchy's exact subclass excerpts. It builds a real
small index with `OntologyIndex.build`, then calls the existing
`taxonomy_problem` and `runtime.prove` interfaces. This source subset has its own
digest and an explicitly unversioned index; it does not masquerade as the
complete upstream revision.

Both native runs use the same selected subclass facts plus the existing
transitivity axiom. The positive query asks whether Process is a subclass of
Entity; E must report `Theorem`. The negative control asks about Process and
Abstract; E must report `CounterSatisfiable`. Unexpected status, timeout or
missing runtime fails the invocation. These outcomes concern only that selected
first-order taxonomy theory. In particular, the countermodel is not a
countermodel of full SUMO, and graph absence is never used to establish falsity.

The optional directory retains the original frozen source report, selected KIF,
its actual SQLite index, each exact Thousands of Problems for Theorem Provers
(TPTP) problem and projection metadata, and a
compact `demonstration.json`. Its paths are root-relative, including references
to native capture receipts. Existing runtime capture files retain the prover's
stdout, stderr, executable binding and submitted bytes under `.rikishi/results`.
No ATP result is embedded in the default portable publication report.

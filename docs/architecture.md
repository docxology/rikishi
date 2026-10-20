# Architecture and method contracts

Rikishi is an operator package around upstream SUMO, with independently reusable
source indexing, numerical examples, service interfaces, and manuscript rendering.

| Layer | Input | Observable result | What it establishes |
| --- | --- | --- | --- |
| Upstream acquisition | pinned Git revision | local ontology files and revision receipt | source identity |
| SUO-KIF parsing/indexing | ontology files | expressions, terms, relationships, diagnostics | lexical and structural inventory |
| Reasoning runtime | explicit axioms and conjecture | prover status and retained stdout | the stated query under that runtime |
| Dashboard and MCP | index and operator functions | HTTP or MCP responses | interface behavior |
| FEP example | finite prior, likelihood, candidate | evidence, KL, objective, residual | finite numerical calculation |
| Formal source inspection | committed Lean objects | declaration locations | source provenance only |
| Manuscript renderer | Markdown and generated figure | PDF, DOCX, HTML, receipt | artifact production |

Indexing does not prove consistency. Term counts do not quantify truth. A graph
edge extracted from a sentence does not necessarily represent an unconditional
logical assertion: quantifiers, implications, negation, and higher-order context
matter. Preserve formula context when interpreting relationships.

The service should run on loopback for local research. MCP clients can invoke the
tools registered by the server; examine tool schemas before connecting an agent.
Treat ontology documentation and retrieved text as data, never as instructions.
Do not expose a local operator service to a public network without a separate
authentication, request-limiting, and threat-model review.

Keep upstream code, downloaded executables, generated indexes, reports, and build
outputs distinct. The ontology corpus retains its upstream license and provenance;
the operator's license does not replace upstream terms. Query results should identify
which installed revision supplied their source. A changed ontology revision requires
rebuilding the index and repeating reasoning checks.

## Importable methods and thin entrypoints

| Module | Interface and failure contract |
| --- | --- |
| `kif` | Parse complete source expressions with file/line attribution; reject malformed syntax |
| `ontology` | Atomically replace a complete SQLite index; never publish partially parsed bad files |
| `source_audit` | Compare recorded source hashes and revision with disk without changing the index |
| `analytics` | Read-only exact aggregation over the indexed population; undefined ratios are null |
| `reports` | Export numerical measurements, plots, and self-contained HTML using shared analytics |
| `projection` | Emit explicit subclass facts plus transitivity with exact problem/source hashes |
| `runtime` / `runtime_results` | Bound real prover execution; decode actual structured ATP results and reject stale invocations |
| `runtime_setup` | Preserve existing source/runtime files, verify pins and patch hashes, install native environment |
| `runtime_query` / `runtime_server` | Orchestrate native processes explicitly, without process work on import |
| `fep` | Validate finite distributions and compute the objective, decomposition, and residual |
| `manuscript_provenance` | Validate inputs, hydrate explicit tokens, freeze and verify renderer sources/artifacts |
| `manuscript` / `manuscript_verification` | Invoke canonical renderers and inspect actual PDF/DOCX/HTML output |
| `quality` | Reject incomplete coverage observations; enforce core and infrastructure floors separately |

`cli`, `dashboard`, and `mcp_server` adapt these methods to their transports.
The runtime and manuscript scripts select the checkout root and call importable
entrypoints. They contain no installation, numerical, hashing, rendering, or
result-classification implementation. No runtime script starts processes merely
because it is imported; isolated subprocess tests check this with invalid argv.

The index's SQLite schema and read-only connection are package-internal seams
shared by indexing and analytics. Public consumers use method results rather than
depending on tables. Test fixtures cross the same methods with actual files and
repositories; they do not replace methods with mocked return values.

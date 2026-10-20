# Architecture and trust boundaries

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

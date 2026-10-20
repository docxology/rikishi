# Observed verification

Rikishi is a working ontology environment with explicit evidence boundaries.
The records below distinguish structural reading, local theorem-prover execution,
Sigma translation, numerical calculation, and formalization source inspection.
Live test counts and coverage are in `output/tests.xml` and `output/coverage.json`.

## Source corpus

The pinned SUMO tree is `efcd059f8feebfe3488a09f575f88d4d009b1e5c`.
`output/data/corpus.json` records 144 discovered and indexed KIF files,
212845 top-level formulas, 34885 symbols, 71701 asserted binary edges, and no
structural parse errors. `output/data/source-manifest.json` contains per-file
SHA256 hashes. The source checkout was clean when indexed. These counts describe
syntax and extraction policy, not independently proven facts or semantic validity.

The index rejects malformed KIF and invalid UTF-8, exposes complete diagnostics,
and does not retain a partially parsed bad file. Real temporary Git repositories
test clean/dirty attribution and atomic preservation after corrupt Git metadata.
Proof manifests carry source cleanliness, file hashes, and problem hashes.

## Runtime and inference

Java 21, Ant, Tomcat, WordNet 3.0, SigmaKEE, its Java dependencies, E, and the
Apple Silicon Vampire executable were installed or built on GitVault. Revisions
and the local Sigma patch are recorded in `config/sumo.lock.json`.
`.omo/evidence/runtime/doctor.json` reports actual artifacts and checkout changes.

The real Sigma application at <http://127.0.0.1:8085/sigma/KBs.jsp> was exercised
through the browser. The knowledge-base page displayed SUMO with four selected
constituents. The Manifest showed `Merge.kif`, `Mid-level-ontology.kif`,
`domainEnglishFormat.kif`, and `english_format.kif` selected, with 74 top-level
files available. Browsing `Human` displayed source assertions at Merge lines
18961 and 18962 and loaded WordNet lexical entries. This goes beyond testing a
login page or an HTTP status code.

Actual Sigma translation and E execution returned `Theorem` for
`(subclass Human Animal)`. The negative query `(subclass Human Artifact)` returned
`ContradictoryAxioms`. This is an **unresolved translated-core consistency issue**.
Its origin has not been established; it may involve the ontology, translation,
or their interaction. A positive result from this profile is not sufficient for
scientific or semantic validation. The operator must retain this limitation.
Raw and structured results are under `.omo/evidence/runtime/sigma-core-*`.

The separate taxonomic example derives a first-order problem from direct
`Merge.kif` subclass assertions plus explicit transitivity. `Human` to
`AutonomousAgent` produces an E theorem. Its controlled test also requires a
countermodel for a nonentailed target. This restricted projection has a narrower
semantics than the full Sigma-translated knowledge base.

The E tests run real theorem and countermodel problems, malformed TPTP, missing
tools, invalid time limits, and a FIFO that blocks reads. The FIFO test requires
wall-clock termination. Bootstrap tests use real local Git repositories to
exercise failed-fetch recovery, wrong-revision refusal, and preservation of
unmatched existing knowledge-base files.

## Reproduced failures and corrections

- Native query execution first failed with `Cannot run program "/usr/bin/dot"`.
  The installed `dot` executable was invoked successfully and its actual path
  configured. The original failure remains in `sigma-query.log`.
- E rejected the upstream translation with `Closing bracket ')' expected` at
  a raw compound symbol `s__(ExtensionFn Oval)`. The versioned patch parses
  compound class terms as expressions in both type-guard branches. It preserves
  the term structure and axioms. Before/after regression and source hashes are
  retained; no change is made to the upstream SUMO checkout.
- The first web request returned `JSP file [/KBs.jsp] not found` because proof
  rendering had created a partial exploded WAR directory. Deployment now merges
  the complete WAR assets while preserving generated graphs. The real KB and
  term pages were subsequently verified.
- An independent reviewer demonstrated that an echoed query containing
  `SZS status Theorem` could fool mixed-log status extraction. Native status must
  come from the actual ATP result, with query text treated as data. The runtime
  review and result-parser negative controls record the correction.
- Initial wheel construction failed with `A second file is being added to the
  wheel archive at the same path: rikishi/static/app.js`. The redundant forced
  inclusion was removed. Source distribution, wheel, and an independent wheel
  installation were then exercised with actual assets and numerical results.

## Dashboard, MCP, and FEP

The local dashboard at <http://127.0.0.1:8765> was exercised on desktop and a
390-pixel mobile viewport. Checks covered term search, empty results, graph-node
navigation, bounded scrolling, theme switching, source links pinned to the clean
SUMO revision, corpus charts, and the live finite free-energy slider. The mobile
layout had no horizontal overflow. At candidate probability 0.8, free energy
equalled surprise to numerical precision and KL was zero to rounding tolerance.

The real MCP stdio test launches a subprocess, initializes a client session,
discovers tools and resources, inspects terms, checks corpus and graph values,
and verifies protocol errors for missing terms and invalid probability vectors.
Direct tool/resource tests check semantic payloads rather than truthiness.

FEP tests compare against independent logarithmic values and reject invalid
normalization, lengths, nonfinite inputs, zero evidence, and unsupported mass.
The proposed vocabulary candidates were checked against the actual SUMO index.
`fep_formal` was inspected at commit
`9a0694f16b8e89b66b2f7f8cc7426c650dd2c4de`; its source checkout was clean. Lean
was not compiled and no proof transport or SUMO/Lean equivalence is claimed.

## Manuscript and review

PDF, DOCX, and HTML are generated using the actual docxology/template adapters.
The renderer extracts a pristine archive at
`efce6d6f5b3c4e8e2bbf92d8250855a0a9389ae8`, verifies its files before import,
and records imported module hashes. Unrelated dirty work in the shared template
checkout is preserved and is not used to render the manuscript. A negative
control modifies a temporary snapshot file and requires verification to reject it.

`output/manuscript/render-receipt.json` records source, data, renderer, and output
hashes. All rendered PDF pages were visually inspected, and both figures were
verified in the DOCX and local HTML output. The manuscript distinguishes
proposed connections from proved results and records the runtime limitation.

The independent review is `.omo/evidence/rikishi-code-review.md`. Final test,
lint, packaging, and publication observations accompany this repository. The
GitHub workflow runs portable tests with integration tests explicitly excluded;
the full branch-aware 90% gate requires the installed local tools and runs on
the GitVault workstation.

An initial whole-tree Git whitespace scan reported spaces emitted inside
Matplotlib SVG paths and blank EOF lines in preserved/generated documents. Those
generated and template bytes are retained. Authored source is checked separately;
the manuscript source EOF was normalized and its outputs regenerated. This is
separate from the passing test, coverage, lint, and artifact-verification gates.

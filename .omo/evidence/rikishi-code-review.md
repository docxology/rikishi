# Independent Rikishi code review

codeQualityStatus: CLEAR
recommendation: APPROVE

This is a bounded, independent review of the new uncommitted package. The reviewer did not implement it. The repository had an unborn main branch, so reviewed files constitute the proposed addition rather than a commit diff. Implementation continued concurrently; findings below describe the inspected snapshot and must not be presented as final runtime acceptance.

## Findings

### CRITICAL

None identified.

### HIGH

None remaining. The mixed-log false-theorem issue introduced in the runtime delta was reproduced with a bounded parser control, then resolved and independently rechecked as documented below.

### MEDIUM

None remaining after the bounded delta review. Direct MCP tests now compare actual search, term, graph, corpus, free-energy, and resource payload values.

### LOW

Public return shapes frequently remain untyped dictionaries (`ontology.py`, `mcp_server.py`, `projection.py`), and no type-check gate is declared in `pyproject.toml`. This departs from the programming skill's typed-boundary perspective. The code is small enough to inspect, but consumers currently rely on string-key conventions. No correctness failure attributable to this was observed.

## Resolved during review

- Runtime tests initially required installed tools even under `-m 'not integration'`. Runtime tests and the projection proof test subsequently received integration markers.
- Bootstrap initially skipped fetch/checkout after an interrupted initial fetch because the destination existed. The new `ensure_repository` retries an unborn clean checkout and refuses locally populated incomplete checkouts.
- Bootstrap now rejects dirty SUMO source before copying, and records the Sigma working-copy source pin.
- The FEP extension test originally pinned an arbitrary formula count. It now checks actual subclass and instance relationships.
- A new MCP transport test initially assumed `structuredContent` was populated. The corrected test reads the SDK's JSON text content and passes real success and failure scenarios.
- Index metadata now records `source_clean`; projection manifests include that state and the indexed source file SHA256. Inspected these changes directly. Corrupt Git metadata raises before replacing the existing index.
- Legacy Sigma adoption now compares existing source files before copying anything, rejects differences, and only copies missing files. This resolves the overwrite finding from the initial bootstrap revision.
- The MCP context-manager lint failure was fixed; an independent final `uv run ruff check src tests scripts` returned **All checks passed!**
- The weak direct MCP truthiness assertions were replaced by semantic payload checks. A bounded independent rerun of both MCP test modules returned **2 passed in 0.65 s**; lint again returned **All checks passed!**
- Inspected packaging delta: the duplicate wheel force-include is removed and sdist inclusion is explicit. Wheel and sdist artifacts exist in `dist/`. The executor owns the clean-wheel-install verification; it was not repeated by this reviewer.
- Confirmed `.github/workflows/check.yml:18` explicitly runs `pytest -m 'not integration'`. Rechecked repository recovery, legacy KB preservation, source cleanliness metadata, and projection source hashes against current source.

## Verification performed

- Confirmed `.venv` and Python base prefix both resolve on GitVault.
- Independently ran the full suite while edits were underway: **68 passed, 1 failed**. The sole failure was `tests/test_mcp_transport.py:32`, `TypeError: 'NoneType' object is not subscriptable`, from the obsolete `structuredContent` assumption. The chained lint invocation therefore did not run on that attempt.
- After correction, independently ran `uv run pytest tests/test_mcp.py tests/test_mcp_transport.py -q`: **2 passed in 0.46 s**. The transport test verifies initialize, tool discovery, source term, corpus count, graph edges, missing-term errors, invalid probability errors, and resource discovery through the actual subprocess protocol.
- After provenance and projection changes, independently ran `uv run pytest tests/test_ontology.py tests/test_projection.py tests/test_mcp.py tests/test_mcp_transport.py -q`: **16 passed in 0.88 s**.
- Then ran `uv run ruff check src tests scripts`: **failed** with `SIM117` at `tests/test_mcp_transport.py:25`, asking to combine nested async context managers. Reported to executor; not edited by reviewer.
- Checked manuscript PDF, DOCX and HTML exist on disk and inspected their verification receipt. Did not independently render or visually inspect those outputs; runtime and visual evidence must be supplied by their owners.
- `omo-agent-toolkit ulw-loop status --json` returned `ULW_LOOP_PLAN_MISSING`, so this report uses the prescribed `.omo/evidence/` fallback.

## Skill perspective

Loaded `omo:remove-ai-slops`, `omo:programming`, and the Python reference. Applied their review criteria only; no cleanup workflow or code edits were performed. No deletion-only tests or prompt-prose tests were found. Most tests exercise real SQLite files, HTTP, subprocesses, numerical examples, or failure paths. Raw public dictionary types remain a low-priority departure from the programming perspective; the weak MCP assertions were resolved. No unnecessary production parsing or broad speculative abstraction was identified: the KIF reader and index directly support the requested ontology workbench.

## Blockers and limits

No code blockers remain in the reviewed delta. The executor owns final whole-project verification and browser acceptance. This report does not certify private GitHub publication, final manuscript visuals, or upstream issue/PR submission. The observed translated-core contradiction must remain explicit; the positive theorem alone is not evidence of consistent axioms.

## Final runtime and renderer delta inspection

- Verified patch SHA256 and patched FormulaPreprocessor source SHA256 against `config/sumo.lock.json`; both match. Bootstrap verifies patch bytes and before/after target hashes, checks applicability, and rejects unexpected edits.
- The two-line semantic change preserves atomic class names and parses compound instance/subclass type arguments as expression trees. Inspected the failing pre-rebuild regression artifact and passing `type-guard-after-build.log`, which covers both compound cases and an atomic control.
- Inspected `sigma-core-patched-query.json` and its raw log: actual E output reports `SZS status Theorem` for `(subclass Human Animal)`. The negative query receipt reports `ContradictoryAxioms`, `proved=false`, and `inconclusive`; this is not a successful countermodel or a corpus consistency guarantee.
- Verified `template_worktree_used=false` and all **256** imported renderer module hashes against files in the pinned archive snapshot. The renderer uses committed archive bytes and rejects mismatched cached snapshot files; it does not import the shared dirty worktree.
- Did not rerun Java compilation, full inference, or browser deployment. Full Tomcat/Sigma browser acceptance remains executor-owned.

## Runtime blocker resolution

Inspected the final `RikishiQuery.java`, `runtime-query.py`, and `interpret_sigma_result` implementation. The Java adapter now writes a dedicated JSON sidecar directly from `ATPResult`, including SZS status, actual ATP exit code, and stdout count. `CREATE_NEW` plus wrapper existence checks prevent reuse of an old result path. The Python wrapper no longer scans mixed logs. Missing sidecars, unsuccessful Java runs, empty theorem output, unsuccessful theorem ATP exit, and timeout cannot yield `proved=true`.

Independently ran `uv run pytest tests/test_runtime.py -q`: **20 passed in 7.42 s**, including the query-echo spoof control, structured outcome controls, real E success/failure checks, and bootstrap helper tests. Targeted `ruff check` returned **All checks passed!** No heavyweight Java process was started by the reviewer.

Inspected both actual structured sidecars and their summary receipts: the positive run records `Theorem`, ATP exit 0, and 21226 stdout lines; the negative run records `ContradictoryAxioms`, ATP exit 0, and 64788 stdout lines. The wrapper classifies the latter as `inconsistent_translated_axioms`, `proved=false`, with a non-success wrapper exit policy. This identifies contradictory translated axioms without claiming the original ontology itself has been proved inconsistent. The earlier HIGH finding is closed.

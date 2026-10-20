# Independent improvement-pass code review

- Base: `0a67379aa214641d0084940894c8b58f82feb826`.
- Scope: the final working-tree improvement diff, including new untracked active source, factored tests, scripts, documentation, scholarship, and regenerated artifacts.
- Role: independent read-only auditor; no implementation edits performed.
- `codeQualityStatus`: CLEAR
- `recommendation`: APPROVE
- `blockers`: []

## Findings by severity

### CRITICAL

None.

### HIGH

None.

### MEDIUM

None remaining. Two findings were communicated during review and fixed by the implementers:

1. Manuscript verification originally recorded bibliography and analytics digests without checking the current authored input files. `src/rikishi/manuscript_verification.py` now compares both, and checks the composition figure in DOCX and HTML. Three stale-input negative controls independently passed.
2. The import-safety test originally imported already-cached modules and could not observe import-time side effects. `tests/runtime/test_runtime_entrypoints.py` now uses a fresh subprocess with invalid argv and an empty root, plus a real unsafe-import negative control. The corrected test independently passed.

### LOW

None remaining. Reinspection confirmed `src/rikishi/source_audit.py:39` has the explicit return annotation `dict[str, str | bool | int | None | tuple[str, ...]]`; the earlier bare-dict observation was stale and is withdrawn. The project has no configured static type-checker gate, so static type correctness is not certified by this review.

## Evidence independently inspected or executed

- Loaded `programming/SKILL.md`, its Python reference, and `remove-ai-slops/SKILL.md`. The test relevance and unnecessary-complexity review ran over production and test changes. No remaining deletion-only, requested-removal, tautological, or constant-mirroring test was identified. The two corrected findings above came from these perspectives. Necessary boundary parsing of ATP sidecars, corpus inputs, manifests, and coverage observations is justified by their actual trust boundaries.
- Both interpreter prefixes were observed on mounted GitVault: the project `.venv` and external CPython 3.12 runtime. Tests ran under the repository operation lease with external temporary/cache bindings.
- Independently ran the portable suite: **149 passed, 9 deselected**, before the final added provenance cases. Artifact: `.omo/evidence/improvements/review-portable-tests.xml`.
- Independently ran the three stale-input negative controls and corrected import-safety scenario: **4 passed**. Artifact: `.omo/evidence/improvements/review-regressions.xml`.
- Compared original and factored test function inventories: all **43 original test function names** remained represented; no baseline behavior test disappeared in factoring.
- Inspected the final full-run log and XML: **163 passed**, with the known Starlette/httpx deprecation warning. Evidence: `output/tests.xml` and `.omo/evidence/improvements/final-full-tests.txt`. The native run includes real bootstrap, Sigma query, and manuscript rendering; this full run was executed by the parent, not repeated by the auditor.
- Independently reevaluated `output/coverage.json` against `config/coverage.toml`: all **21 package Python files** present; core **96.346644%**, infrastructure **82.484725%** combined line/branch coverage. Five exact infrastructure paths are explicit; all other paths default to core. Inspected negative controls for missing files, excluded lines, malformed counts, invalid policy paths, and each failing scope.
- Inspected final Ruff and build logs: clean lint and successful source distribution/wheel. Authored `git diff --check -- src scripts tests docs manuscript/rikishi.md` independently exited zero.
- Independently hashed and size-checked all **nine** final manuscript receipt artifacts, including PDF, HTML, DOCX, three figures, hydrated manuscript, numerical output, and bibliography. All matched the current receipt.
- Inspected the manuscript page-5 image: the finite objective plot, formula interpretation, and long Lean declaration list were readable without clipping. Complete final PDF page review remains the parent's recorded visual QA responsibility.
- Checked nonce propagation through Python launch, Java exclusive sidecar creation, and strict result parsing. A successful theorem retains `consistency: not_established`; contradictory axioms do not produce `proved: true`.
- Checked source audit semantics: current byte agreement, revision agreement, dirty-worktree observations, escaped paths, and parse failures remain distinct. The CLI converts operational failures into nonzero structured errors.
- Checked analytics SQL, fixtures, metric definitions, and rendering: duplicate assertion counts are separate from distinct triples; self-loops contribute twice; every indexed symbol participates in the degree denominator; the composition remainder retains all formula heads; empty ratios are null. Browser code uses textContent for data labels and embedded JSON escapes less-than signs.
- Directly consulted the primary Pease 2023 arXiv abstract, TPTP SZS documentation, and author-hosted Blei et al. 2017 paper. Their bounded translation/status/variational-identity claims agree with the manuscript. Source-inspected Lean declarations remain explicitly distinguished from compiled Lean verification.

## Residual limits

- The native core negative control still reports contradictory translated axioms. The separate no-conjecture E run reports ResourceOut, not a consistency result or minimized contradiction. Neither result establishes where the source/translation defect lies. Documentation preserves this limitation.
- Native setup coverage is not exhaustive: fresh network downloads, alternate platform paths, and some server lifecycle failures remain unexercised. The infrastructure denominator exposes these gaps; it is not omitted from measurement.
- GitHub hosted Actions remain externally budget-blocked according to the existing recorded annotation. Local gates do not establish Linux hosted execution.
- The renderer snapshot and artifact hashes establish provenance under the documented local execution model, not semantic correctness, a Lean proof, or an adversarial sandbox guarantee.
- No static security scanner or static type-checker is configured; those gates are N/A, not implicitly passed.

The toolkit returned `ULW_LOOP_PLAN_MISSING`; this report uses the required non-loop fallback path. No source, upstream checkout, Git history, remote state, or implementation file was modified by the reviewer.

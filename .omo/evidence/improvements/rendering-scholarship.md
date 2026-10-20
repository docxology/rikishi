# Rendering and scholarship improvement evidence

## Changes observed on disk

- `src/rikishi/manuscript.py` contains native template adapter orchestration;
  `manuscript_provenance.py` contains typed corpus parsing, hydration, safe paths,
  Git snapshot verification, artifact checks, and a real corruption control;
  `manuscript_verification.py` checks generated document contents and source hashes.
- Rendering and verification command scripts are thin entrypoints without
  import-time execution. Verification uses explicit exceptions, not assertions
  that disappear with `python -O`.
- `manuscript/references.bib` contains six primary-source/software references.
  `docs/scholarship.md` maps claims to sources and records fetched-source limits.
  The manuscript explicitly separates variational inference, the wider FEP account,
  source-only Lean inspection, and the unproved interpretation between languages.
- Nine receipt artifacts include three scientific figures and the bibliography.
  Current authored Markdown, bibliography, analytics and corpus hashes are checked.

## Scenarios and binary observables

1. `source scripts/env.sh; uv run pytest tests/manuscript --cov=rikishi.manuscript
   --cov=rikishi.manuscript_provenance --cov=rikishi.manuscript_verification
   --cov-report=term-missing --cov-fail-under=90
   --junitxml=.omo/evidence/improvements/manuscript-tests.xml`
   ran under `repository_operation` and passed 28 tests with 98.22% combined
   line/branch coverage. Captured stdout/stderr: `manuscript-tests.txt` in this
   directory. This run includes real native PDF/DOCX/HTML generation and three
   deliberately stale authored-input controls. A subsequent extracted corruption
   helper adds one portable test, bringing the current manuscript suite to 29.
2. Portable provenance controls use real temporary Git repositories, archive
   extraction, dirty checkout bytes, corruption, symlinks, invalid measurements,
   and mismatched artifact hashes. The final targeted 25-test invocation passes;
   the only unreachable line is the guard for a corruption control unexpectedly
   accepting modified renderer bytes. No mocks or interpreter-internal patches.
3. `uv run python -O scripts/verification-manuscript.py` exited zero and reported
   nine verified artifact hashes, 256 verified imported renderer modules, valid
   DOCX media, local HTML figures, PDF text, and rejected unnormalized prior.
4. `uv run python scripts/verification-renderer-provenance.py` exercises the actual
   pinned template archive and rejects a deliberately modified snapshot.
5. `pdftoppm -scale-to 1200 -png output/manuscript/pdf/rikishi.pdf
   .omo/evidence/improvements/manuscript-pages/page` produced seven page images.
   All seven were inspected. A clipped long Lean declaration on page 5 was fixed
   by a list layout, the document was regenerated, and pages 5-7 were inspected
   again. Figures, equations, captions, links and bibliography fit the page area.
   Page images are in `manuscript-pages/`; `pdfinfo` reports seven letter-size pages.
6. Scoped Ruff checks pass for all three modules, manuscript tests, and wrappers.

## Interpretation limits

Native core contradiction remains explicitly unresolved. Bibliographic context is
not a proof of the proposed bridge. Lean declarations were read at the pinned
Git object, not compiled. The FOIS abstract/metadata was retrievable, but its full
PDF fetch failed through the research browser; no detailed argument from that
paper is relied on. Blei Section 2.2, Friston Box 1, TPTP SZS documentation, Pease's
arXiv abstract and the pinned Lean definitions were inspected directly.

The parent final gate will rerender and independently review the integrated tree;
this file records the worker's observed scenarios, not that future gate's result.

## Fresh receipt verification output

Command: `source scripts/env.sh && uv run pytest tests/manuscript/test_manuscript_provenance.py --cov=rikishi.manuscript_provenance --cov-report=term-missing --cov-fail-under=90 && uv run python -O scripts/verification-manuscript.py`

Exit status: 0

```text
============================= test session starts ==============================
platform darwin -- Python 3.12.13, pytest-9.1.1, pluggy-1.6.0
rootdir: /Volumes/GitVault/Username/docxology/Private/rikishi
configfile: pyproject.toml
plugins: anyio-4.15.1, cov-7.0.0
collected 25 items

tests/manuscript/test_manuscript_provenance.py ......................... [100%]

================================ tests coverage ================================
______________ coverage: platform darwin, python 3.12.13-final-0 _______________

Name                                   Stmts   Miss Branch BrPart  Cover   Missing
----------------------------------------------------------------------------------
src/rikishi/manuscript_provenance.py     108      1     36      0    99%   149
----------------------------------------------------------------------------------
TOTAL                                    108      1     36      0    99%
Required test coverage of 90% reached. Total coverage: 99.31%
============================== 25 passed in 0.80s ==============================
{
  "renderer_imported_modules_verified": 256,
  "active_template_worktree_used": false,
  "artifact_hashes_verified": 9,
  "docx_archive_and_image": "pass",
  "html_local_figure": "pass",
  "pdf_text": "pass",
  "negative_control": "prior must sum to one",
  "source_inspection_commit": "9a0694f16b8e89b66b2f7f8cc7426c650dd2c4de",
  "lean_compiled": false
}
```

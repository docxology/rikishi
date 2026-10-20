# Dashboard and analytical reporting improvement evidence

## Scope and implementation

- `src/rikishi/reports.py` owns plotting and portable report generation.
  `dashboard.py` retains the previous `build_report` import as a compatibility
  export; HTTP handlers adapt the index, FEP, and analytics APIs.
- `src/rikishi/analytics.py` returns typed records from read-only SQLite queries.
  Full formula-head counts, file concentration, distinct directed labeled
  triples, repeated assertions and all-symbol degree distributions have explicit
  denominators and empty-population handling in `docs/metrics.md`.
- Live and offline reports share `static/analytics.js`; composition uses a
  table with an explicit remainder and degree uses bars with exact text counts.
  Responsive columns collapse to one on narrow screens. No external asset or
  visualization dependency was added.
- Dashboard tests now live under `tests/dashboard/`, with measurement-method
  cases separated from HTTP and artifact surface tests.

## Observed checks

| Scenario | Invocation | Binary observable | Evidence |
| --- | --- | --- | --- |
| Scoped real-file HTTP, analytics and export regression gate | `uv run pytest tests/dashboard --cov=rikishi.analytics --cov=rikishi.reports --cov=rikishi.dashboard --cov-report=term-missing --cov-report=json:.omo/evidence/improvements/dashboard-coverage.json --junitxml=.omo/evidence/improvements/dashboard-tests.xml`, inside GitVault repository operation lease | 18 passed, exit 0; 100% of 150 statements and 8 measured branches | `dashboard-tests.txt`, `dashboard-tests.xml`, `dashboard-coverage.json` |
| Adversarial fixtures | Same gate; duplicate triples, self-loop, 35 formula heads, malformed KIF, empty file, missing database, invalid HTTP queries, embedded markup | Counts retain repeats separately, degree weighted sum = twice unique edges, all heads accounted for; invalid inputs explicitly rejected | Test XML and `tests/dashboard/test_analytics.py` |
| Real SUMO report | `uv run python scripts/build_dashboard.py --index .rikishi/ontology.sqlite --output output` | Exit 0; eight nonempty report artifacts | `output/analytics.json`, `output/measurements.md`, `output/dashboard.html`, `output/corpus-composition.png`, `.svg`, existing `corpus-files` figures and `corpus.json` |
| Lint and JS parse | Scoped `uv run ruff check`; `node --check src/rikishi/static/analytics.js` and `app.js` | Exit 0 | Parent full gate repeats lint; this scoped observation recorded here |
| Figure visual inspection | `view_image(output/corpus-composition.png)` | Both panels readable, axes and zero-degree point visible; no clipped labels | `output/corpus-composition.png` |

Observed real corpus: source revision
`efcd059f8feebfe3488a09f575f88d4d009b1e5c`, clean source, 212845 formulas,
144 files, zero rejected files; 71701 edge assertions, 70843 unique triples,
858 repeated assertions; 34885 symbols and 256 with zero restricted-graph degree.
Largest file share 0.1901477601071202, top-ten share 0.7206464798327421,
file HHI 0.10081185672804989. Direct checks sum all predicate counts to 212845
and degree-weighted counts to 141686 = 2 × 70843.

Python prefix and base prefix both resolved on mounted GitVault. A known
Starlette/httpx deprecation warning appears in the scoped tests. No browser
execution is claimed by this worker; root owns live/offline browser QA and the
final combined gate. No commits or remote writes made by this worker.

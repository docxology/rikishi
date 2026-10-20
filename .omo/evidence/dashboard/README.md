# Dashboard execution evidence

- `uv run pytest tests/test_dashboard.py --cov=rikishi.dashboard --cov-report=term-missing --cov-report=json:.omo/evidence/dashboard/coverage.json --cov-fail-under=90 --junitxml=.omo/evidence/dashboard/tests.xml -q`: 12 passed; 100% statements and branches. Captured in `tests.log`, `tests.xml`, `coverage.json`.
- Real KIF fixtures are indexed to SQLite and queried through the FastAPI HTTP
  client. Assertions cover source filenames/lines, relationship content, real
  counts, missing-term 404, invalid-query 422, nonexistent database refusal,
  positive-support free energy, and its optimum.
- Export scenario: `uv run python scripts/build_dashboard.py --index .rikishi/ontology.sqlite --output .omo/evidence/dashboard/full-corpus`. Exit 0. `export.json` lists the actual portable HTML, measured JSON, SVG, and PNG artifacts under `full-corpus/`.
- Negative controls: q=1.1 and q=nan reject with 422; absent terms reject with
  404; invalid limits reject with 422; missing database startup raises without
  creating a file. Embedded markup is escaped and still round-trips as JSON.
- `uv run ruff check src/rikishi/dashboard.py tests/test_dashboard.py scripts/build_dashboard.py`: all checks passed (`ruff.log`).
- Accent-stripe checker: four static files checked, no findings (`style-check.log`).
- `bun build src/rikishi/static/app.js --target browser --outdir .omo/evidence/dashboard/js-check`: exit 0, executable browser JavaScript bundle emitted at `js-check/app.js`.
- Root browser review identified result-grid shrinking and overly tall source
  lists. CSS now uses natural-height block results within 420px overflow,
  source disclosures within 480px overflow, and relation list within 320px.
  Root owns the final browser verification; this report does not claim visual
  QA or Lighthouse scores.
- Environment verified: both Python prefix and base prefix are on GitVault.
  One upstream Starlette TestClient deprecation warning remains visible in logs.

# Runtime methods improvement evidence

## Scope and observed behavior

The bootstrap, query, and Tomcat scripts now delegate to importable runtime
modules. The ATP result parser is separately typed and rejects malformed values,
unknown fields, stale invocation identifiers, unsuccessful process completion,
empty output, and incompatible proof/countermodel exit codes. Each live Java
adapter invocation echoes its fresh identifier in an exclusively created sidecar.
Positive theorem results still explicitly leave premise consistency unestablished.

## Verification

- `source scripts/env.sh` then `uv run ruff check src/rikishi/runtime*.py scripts/runtime*.py tests/runtime`: exit 0, all checks passed.
- `uv run pytest tests/runtime --cov=rikishi.runtime --cov=rikishi.runtime_results --cov=rikishi.runtime_setup --cov=rikishi.runtime_query --cov=rikishi.runtime_server --cov-report=json:.omo/evidence/improvements/runtime-coverage.json --cov-fail-under=0 --junitxml=.omo/evidence/improvements/runtime-tests.xml`: 42 passed in 38.77 seconds under the repository lease. Artifacts: `runtime-tests.xml`, `runtime-coverage.json`. This run preceded the additional explicit NoSZSStatus negative control.
- `uv run pytest tests/runtime -m 'not integration' --no-cov --junitxml=.omo/evidence/improvements/runtime-portable-tests.xml`: final portable source, 36 passed and 7 native tests deselected. Artifact: `runtime-portable-tests.xml`; includes the added NoSZSStatus control. Root's final whole-project gate covers the combined final tree.
- Measured module coverage including branches: runtime 98%, runtime_results 100%, runtime_setup 74%, runtime_query 92%, runtime_server 72%. Setup/query/server are explicitly classified infrastructure; proof and result interpretation stay in the core scope.
- Actual native bootstrap completed and rebuilt the pinned installation. Actual native Human/Animal query returned Theorem, ATP exit 0, and 21226 stdout lines. Its sidecar `.rikishi/results/fa80a5fb31074054898e067d45c34ab0.log.result.json` contains invocation `583ecf9b7fd94327b60cab21133bfcff`; the test asserts identity equality and rejects reuse of that output path.
- `uv run python scripts/runtime-sigma.py status`: HTTP 200, 3543 body bytes after starting the real foreground server. Session 99967 owns that foreground process. The first status-dependent test failed with ConnectionRefusedError because the prior session had ended; tests now own a real local HTTP fixture and no longer assume a persistent service.
- Both Python prefixes resolved to GitVault: repository `.venv` and `Local/runtimes/uv-python/cpython-3.12-macos-aarch64-none`.

## Bounded consistency experiment

Copied the generated core to `.omo/evidence/runtime/improvement-core-snapshot.tptp`
(9536183 bytes, SHA256 `3af8bbb0023ce53c65b6504a025cc0f30ff2132667bbd1f8cd249e2e1967e3ed`).
Invoked the installed E binary with `--auto --tstp-format --proof-object
--cpu-limit=15` on that snapshot, with no conjecture added. Exit 8 and SZS
ResourceOut; stdout is `translated-core-consistency.log`. The preserved snapshot
is ignored as a large generated runtime artifact. No source-ontology consistency
or inconsistency conclusion follows, and no proof core was available to minimize.

## Module review

The independent reviewer identified that the first import-safety test reused
already imported modules. It now launches a fresh Python subprocess with malformed
argv and an empty root, requires the import-success marker, and checks no runtime
directory was created. A real fixture module that parses argv during import is
the negative control: it exits 2 and cannot emit the success marker. Invocation:
`uv run pytest tests/runtime/test_runtime_entrypoints.py -m 'not integration'
--no-cov --junitxml=.omo/evidence/improvements/runtime-import-tests.xml`;
4 passed, 2 native scenarios deselected. Evidence: `runtime-import-tests.xml`.
Runtime tests are factored into ATP contract, E prover, source provisioning,
Sigma outcome, and entry-point suites.

Each extracted module owns one runtime boundary. Core ATP input is parsed into a
strict frozen Pydantic contract before classification. No mocking framework was
introduced. Runtime source pure-line counts: setup 196, query 50, server 26,
results 42, runtime 61. No module exceeds 200 pure lines. Existing installer
network/download branches remain outside the exercised native installed-path
scenario; the explicit infrastructure coverage report exposes those gaps.

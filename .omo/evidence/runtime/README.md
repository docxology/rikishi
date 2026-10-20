# SUMO runtime verification receipt

Observed on 2026-10-19 on Apple Silicon. All downloads, sources, build products,
Python prefixes, Java user/temp directories, and evidence reside on GitVault.

| Scenario | Invocation | Binary observable | Artifact |
| --- | --- | --- | --- |
| Full pinned sources and real binaries | `rikishi.runtime.status(Path.cwd())` | All six source HEADs match lock; SUMO clean; actual E and Sigma JAR exist | `status.json` |
| Official Java application build and complete deployment | `bash scripts/bootstrap-sumo.sh --core-only` | Ant `BUILD SUCCESSFUL`; WAR expanded preserving graph files | `bootstrap-deploy.log` |
| Real E positive proof | `eprover --auto --tstp-format --proof-object --cpu-limit=10 entails.p` | `SZS status Theorem` | `entails.p`, `entails.out` |
| Real E negative control | Same command with `nonentails.p` | `SZS status CounterSatisfiable` | `nonentails.p`, `nonentails.out` |
| Upstream malformed translation reproduced | E invoked against generated `SUMO.tptp` | Parse error at compound-class symbol `s__(ExtensionFn Oval)` | `e-sigma-native.err`, `SUMO-unpatched.tptp` |
| Java regression before compatibility patch | Java source launcher on `RuntimeTypeGuardRegression.java` with original JAR | Assertion failure: compound class flattened into Atom | `type-guard-before.log` |
| Java regression after rebuilt compatibility patch | Same Java regression with rebuilt JAR | Compound instance and subclass guards plus atomic control pass | `type-guard-after-build.log` |
| Actual Sigma core translation and E query | `uv run python scripts/runtime-query.py '(subclass Human Animal)' --prover e --timeout 10 --output .omo/evidence/runtime/sigma-structured-positive.log` | Java and ATP exit 0; structured ATP status Theorem | `sigma-structured-positive.json`, `.log`, `.log.result.json` |
| Full-core negative control | Same wrapper with `(subclass Human Artifact)`, timeout 5 | Wrapper exit 2; ATP reports ContradictoryAxioms; proved false | `sigma-structured-negative.json`, `.log`, `.log.result.json` |
| Real browser deployment | `uv run python scripts/runtime-sigma.py run` then GET `/sigma/KBs.jsp` | HTTP 200; actual Sigma page contains SUMO | `sigma-server-deployed.log`, `sigma-kbs-deployed.html`, `sigma-http-status.json` |
| Runtime tests and negative controls | `uv run pytest tests/test_runtime.py --cov=rikishi.runtime --cov-branch --cov-report=term-missing --cov-report=json:.omo/evidence/runtime/coverage.json --cov-fail-under=90` | 20 passed; 98.39% branch-aware coverage | `coverage-final.log`, `coverage.json` |
| Owned Python lint | `uv run ruff check src/rikishi/runtime.py scripts/runtime-bootstrap.py scripts/runtime-sigma.py scripts/runtime-query.py tests/test_runtime.py` | All checks passed | `lint.log` |

The core browser profile contains exactly the four upstream configured
constituents. The parent separately verified the visible manifest and Human's
source axioms. The foreground Tomcat process is intentionally left running at
127.0.0.1:8085; the final native exec session is 2635.

The broad 74-file attempt is retained in `sigma-query.log` and
`sigma-all-domains.xml`: it loaded 522,593 cached formulas, then exposed an
upstream startup race and malformed TPTP. It is not the active profile. Its old
working data remains at `.rikishi/sigma/KBs`; newly selected profiles use
separate `.rikishi/sigma/core` and `.rikishi/sigma/all-domains` directories.

The final compatibility patch is explicitly versioned and checksum-guarded in
`config/sumo.lock.json`. Sigma's working tree therefore intentionally differs
from its pinned commit in `FormulaPreprocessor.java`. SUMO source data is
unchanged. E's build changes its generated tracked `Makefile.vars`.

The observed `ContradictoryAxioms` result is a limitation of the current
translated core theory. Its origin has not been isolated to original ontology,
cached axioms, or other translation behavior. No semantic-consistency or FEP
validation claim follows from the positive theorem. No axioms were dropped to
make the check pass.

Intermediate failed attempts remain visible: `coverage.log` includes the test
fixture missing its own Git initialization; `coverage-final.log` records the
corrected passing run. `type-guard-after.log` ran before the rebuilt JAR finished
and still failed; `type-guard-after-build.log` is the successful post-build
regression. The native unpatched query logs explicitly retain their failures.

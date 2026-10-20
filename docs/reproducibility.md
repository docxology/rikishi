# Reproduce observations, not just installation

A reproducible run identifies source bytes, environment, commands, and outputs.
Rikishi separates the pinned ontology checkout, generated index, Sigma's writable
KB, bounded proof problems, numerical examples, and publication artifacts.

## What to retain

| Evidence | Why it matters |
| --- | --- |
| `config/sumo.lock.json` | Upstream revisions and acquisition identities |
| `uv.lock` and Python prefix information | Python package resolution and interpreter location |
| `output/data/source-manifest.json` | Source-file inventory and integrity metadata |
| `output/data/corpus.json` | Measured counts, source revision, and parser diagnostics |
| `output/reasoning/taxonomy.p` | Exact restricted first-order problem |
| `output/reasoning/taxonomy.json` | Mapping from projected facts to original source |
| `output/reasoning/taxonomy.result.json` | Actual prover command, status, and output |
| `output/manuscript/render-receipt.json` | Template revision, substitutions, source/output hashes |
| `.omo/evidence/` | Test output, visual inspection, and negative controls |

Preserve these together before changing source revision, query, configuration, or
dependencies. Do not assume a report generated earlier describes the current index.
Run `rikishi stats` and regenerate `rikishi report` when inputs change.

## Deterministic manuscript hydration

The manuscript source contains explicit count placeholders. The rendering script
reads `output/data/corpus.json`, requires a clean source export without parse errors,
and replaces the declared placeholders deterministically. It refuses unresolved
uppercase placeholders. The hydrated source is retained as
`output/manuscript/rikishi.md`, and the receipt records both source hash and corpus
export hash plus every substitution.

The corpus chart is copied from the report output into the manuscript figure set.
Regenerate the report before rendering so chart and counts describe the same run.
The finite-example JSON and plot are recomputed by the numerical implementation.
The canonical docxology/template adapters then generate PDF, DOCX, and HTML.
They are imported from a verified Git-archive snapshot of the pinned template
commit, not the active checkout's working files. The receipt identifies the archive
and every imported infrastructure module by SHA-256; the outside origin manifest
records all archived source hashes. The active checkout may be dirty, and its
cleanliness is recorded explicitly without treating unrelated edits as renderer input.

Byte-identical PDFs and DOCX files are not promised across tool versions or runs:
archive timestamps, font libraries, and PDF metadata can differ. The receipt
identifies actual output bytes. Numerical and semantic agreement should be checked
separately from byte equality.

## Negative controls and failure interpretation

Tests reject an unnormalized prior, impossible observation, mismatched vectors,
nonfinite values, and positive candidate mass outside joint support. The source
inspection tests use real temporary Git repositories, including missing declarations
and dirty working trees. Prover tests require both a theorem and a nonentailed query
to have distinguishable outcomes. Missing tools and malformed inputs remain errors.

Run the complete project gate described in [verification.md](verification.md).
Capture command exit statuses directly; piping output through a logger without
checking the command's status can turn a failure into apparent success. The
manuscript verifier checks nonempty artifacts, hashes, embedded image bytes,
extracted PDF content, and local HTML figures. Visual inspection remains a separate
step and should record which artifact hash was actually viewed.

## Limits of a receipt

A receipt establishes an observed execution and its inputs. It does not establish
ontology consistency, prove arbitrary SUMO entailments, validate an empirical FEP
claim, or certify an ontology-to-Lean translation. State those acceptance scopes
separately, and retain inconclusive results as inconclusive.

The observed native Sigma core run illustrates this distinction. With four core
constituents and the versioned compound-type guard patch, `(subclass Human Animal)`
returned `SZSTheorem`, while the negative control `(subclass Human Artifact)`
returned `SZSContradictoryAxioms`. The translated-core inconsistency is unresolved;
its origin has not been assigned to the ontology or the translator. Preserve both
query logs and do not treat the positive result as meaningful semantic validation.
The separate restricted taxonomy proof retains its own axiom set and acceptance
scope. See the current runtime and verification guides for the retained evidence.

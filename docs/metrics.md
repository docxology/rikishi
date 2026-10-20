# Corpus measurement methods

`rikishi.analytics.measure_corpus` reads one existing SQLite index in read-only
mode. `/api/analytics` exposes the same record used by `rikishi report`.
The population is successfully parsed files, not all discoverable files: rejected
files are reported separately. No statistical sampling or confidence interval is
involved. Revision and source cleanliness describe the index's build provenance.

| Field | Definition and denominator |
| --- | --- |
| `formula_denominator` | Sum of top-level parsed expressions over successfully indexed files |
| `predicates` | Every outermost formula head, including logical operators; counts sum to all formulas, shares divide by `formula_denominator` |
| `file_hhi` | Sum of squared file formula shares; 1 for a corpus concentrated in one file, 1/N for equal formula counts across N nonempty files |
| `largest_file_share` | Largest file's formula count divided by all indexed formulas |
| `top_ten_file_share` | Sum of the ten largest file counts (or all files if fewer) divided by all indexed formulas |
| `edge_assertions` | Indexed top-level binary assertions with atomic, non-variable endpoints; repetitions remain |
| `unique_edges` | Number of distinct `(subject, predicate, object)` triples |
| `duplicate_edge_assertions` | Edge assertion count minus distinct triple count; repetition does not imply a semantic defect |
| `term_denominator` | All indexed symbols, including relation names and symbols occurring only inside nested expressions |
| `degree_distribution` | Number of indexed symbols with each in-degree plus out-degree in the distinct triple graph; self-loops contribute two |
| `zero_degree_terms` | Symbols that never occur as an endpoint of these triples; not a count of disconnected ontology concepts |
| `mean_total_degree` | Twice the distinct triple count divided by all indexed symbols |

Ratios with an empty denominator are JSON `null`. Empty distributions are `[]`.
The degree histogram must sum to the term denominator. Its degree-weighted sum
must equal twice the distinct edge count. These identities are tested with real
KIF fixtures containing duplicate assertions and a self-loop. A 35-head fixture
ensures the existing 30-row display summary cannot truncate analytics.

## Visual encodings

Live and offline surfaces share `static/analytics.js`. The composition table
shows eight heads plus an explicitly measured remainder; every formula remains
accounted for. Degree bars group symbols into 0, 1, 2–4, 5–16, 17–64 and 65+
degrees. Width represents a fraction of **all indexed symbols**, with exact counts
shown in text. Both views remain readable without color interpretation.

`corpus-composition.svg` and `.png` provide publication figures: ten formula heads
plus the remainder, and the complete exact degree distribution. Degree axes use
Matplotlib symmetric-log scaling, retaining zero; the axes disclose this choice.
These are descriptive charts, not evidence for a power-law fit. Original
`corpus-files` figures and `corpus.json` remain available unchanged in meaning.

Syntax counts cannot establish independent facts, ontology consistency, logical
completeness, or inferred connectivity. Runtime Sigma caches may add or transform
formulas and are a different population. The source graph excludes nested
assertions and inferred closure; its degrees must not be interpreted as semantic
importance. See [runtime limitations](runtime.md) and [FEP boundaries](fep.md).

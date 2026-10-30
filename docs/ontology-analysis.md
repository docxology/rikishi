# Read-only ontology queries

`OntologyIndex` delegates corpus queries to `corpus_query`, structural diagnostics
to `ontology_analysis`, and bounded paths to `taxonomy_paths`. These methods read
the existing index without rebuilding it, migrating its schema, reading source
paths from disk, or invoking a reasoner. `graph_types` defines their JavaScript
Object Notation (JSON)-compatible
response records. Callers should retain `provenance` and `scope` with exported data.

```python
from rikishi.ontology import OntologyIndex
from rikishi.corpus_query import FileQuery, FormulaQuery
from rikishi.ontology_analysis import TaxonomyQuery
from rikishi.taxonomy_paths import TaxonomyPathQuery

index = OntologyIndex(".rikishi/ontology.sqlite")
files = index.corpus_files(FileQuery(sort="formulas", descending=True, limit=25))
formulas = index.formula_search(FormulaQuery(term="Human", head="subclass"))
relations = index.relation_inventory()
taxonomy = index.taxonomy_analysis(TaxonomyQuery(relation="subclass"))
path = index.taxonomy_path(TaxonomyPathQuery("Human", "Entity", path="Merge.kif"))
```

## Corpus pages

`FileQuery.path` matches a literal, case-sensitive substring. `sort` is `path` or
`formulas`; `descending` reverses the primary sort. Equal formula counts always
break ties by ascending path. File rows contain `path`, `sha256`, and `formulas`.
`total_formulas` covers every successfully indexed file; `filtered_formulas` covers
the entire matching file set, including rows outside the returned page.

`FormulaQuery.text` matches a literal, case-sensitive substring of retained formula
text. `head`, `path`, and `term` require exact matches. Term matching includes
symbols inside nested expressions, but the returned row is always the complete
top-level source formula. Filters combine with AND. Percent signs, underscores,
backslashes, quotes and Structured Query Language (SQL)-looking strings remain data. Formula rows retain
`id`, `path`, `line`, `text`, `predicate`, and `source_sha256`; repeated source
formulas remain separate rows. Order is ascending path, line, then formula ID.

Pages expose `items`, `total`, `filtered_total`, `returned`, `limit`, `offset`,
`truncated`, and `has_more`. `total` precedes filtering; `filtered_total` includes
all matches. `truncated` means some matches are omitted before or after the page;
`has_more` means matches remain after it. An offset beyond the population returns
an empty page and complete totals. Empty filter strings select the full population.
Nonempty whitespace-only filters and NUL are rejected. Strings are limited to
2048 characters; limits are integers from 1 to 500, offsets from 0 to 1,000,000.
Invalid parameters raise `QueryError`, a `ValueError` subclass.

Existing `term()` rows retain their fields and fixed display caps. They additionally
expose `formulas_total`, `formulas_truncated`, `children_total`, and
`children_truncated`. `formula_search(FormulaQuery(term=...))` pages all formulas.
The neighborhood relation inventory and deterministic unique-triple contract are
unchanged.

## Relations and taxonomy

`relation_inventory()` lists every indexed binary relation in name order. Each row
has `relation`, `assertion_count`, `unique_edges`, `duplicate_assertions`, and
`node_count`. Assertion counts retain repetition; distinct triples eliminate it.
Endpoint counts are distinct within each relation and cannot be summed across
relations to obtain a corpus term count. Relation names and terms occurring only
inside nested expressions are excluded unless they also occur as endpoints.

`TaxonomyQuery.relation` accepts exactly `subclass` and `subrelation`. The selected
graph uses distinct direct child-to-parent edges. Its optional `path` is an exact
indexed source path. `total` counts that relation's endpoints across the corpus;
`filtered_total` and `node_count` count endpoints after selecting a source path.
This is an endpoint-only population, distinct from all indexed symbols. An
isolated symbol that never participates in the selected edges is absent.

Node diagnostics page by name and expose `parent_count`, `child_count`, weak
`component`, and nullable `cycle_component`. A repeated assertion contributes one
edge, a self-loop contributes one parent and one child. Roots have zero outgoing
parent edges. Multiple-parent nodes have at least two distinct parents. Weak
components ignore edge direction; their stable identifier is their smallest name.

Cycles use directed strongly connected components (SCCs): components of more than
one node, or singleton components with a self-loop. `cyclic_component_count`,
`cyclic_node_count`, and `self_loop_count` describe the complete selected graph.
`cycle_components` provides at most `limit` SCC summaries, each with representative,
full node count and up to ten sorted members. Both summary and member truncation
are explicit. Node pages identify membership even when the SCC sample omits it.
These are graph cycle diagnostics, not contradiction evidence. Analysis rejects
graphs with more than 1,000,000 distinct selected edges rather than returning
partial counts. Iterative traversals avoid Python recursion limits.

## Source-backed paths

`TaxonomyPathQuery` requires indexed `source` and `target` symbols; unknown symbols
raise `KeyError`. Relations and source-path filtering have the same meaning as
taxonomy analysis. Breadth-first traversal returns one shortest child-to-parent
path, with lexically ordered neighbors resolving ties. Every edge includes an
original formula's line, exact text and recorded file hash. Duplicate assertions
select the earliest indexed formula ID. A known symbol reaches itself with a
zero-edge path, including when it has no selected graph edges.

`status` is `found`, `not_found`, `max_depth`, or `max_visited`. Only `not_found`
exhausts the selected reachable graph. A depth-limited or visit-limited search
makes no absence claim. Depth is bounded from 0 to 100; discovered nodes are
bounded from 1 to 100,000, including the source. `visited` counts discovered nodes.
A discovered target has a shortest path even if another neighbor reaches the
visit cap. The response retains the bounds, filter, provenance and scope.

These paths summarize retained syntax. They do not introduce inferred assertions,
prove logical transitivity under arbitrary source-language context, establish consistency,
or certify semantic completeness. See [method contracts](architecture.md).

async () => {
  const checks = [];
  const assert = (condition, message) => {
    if (!condition) throw new Error(message);
    checks.push(message);
  };
  const waitFor = async (predicate, message) => {
    const deadline = Date.now() + 10000;
    while (!predicate()) {
      if (Date.now() > deadline) throw new Error(message);
      await new Promise(resolve => setTimeout(resolve, 30));
    }
  };
  const byId = id => document.getElementById(id);
  const change = (id, value, event = "change") => {
    byId(id).value = value;
    byId(id).dispatchEvent(new Event(event, { bubbles: true }));
  };
  const count = node => Number(node.textContent.split(" (")[0].replaceAll(",", ""));
  await waitFor(() => byId("file-filter") && byId("head-filter"), "Measured controls did not load");
  const offline = !!byId("data");
  const stats = offline ? JSON.parse(byId("data").textContent) : await (await fetch("/api/stats")).json();
  const metrics = offline ? JSON.parse(byId("analytics-data").textContent) : await (await fetch("/api/analytics")).json();
  assert(document.title === (offline ? "Rikishi · Corpus report" : "Rikishi · Ontology workbench"), "Correct page identity");
  assert(document.querySelectorAll("#metrics dd").length === 4, "Four measured overview counts render");
  const sumFormulaRows = () => [...document.querySelectorAll("#analytics tbody tr")]
    .reduce((sum, row) => sum + count(row.querySelector("td")), 0);
  assert(sumFormulaRows() === metrics.formula_denominator, "Composition page plus remainder preserves all formulas");
  change("head-filter", "__NoSuchHead_4d_8932__", "input");
  assert(document.querySelectorAll("#analytics tbody tr").length === 1 && sumFormulaRows() === metrics.formula_denominator,
    "Empty head filter retains the complete formula remainder");
  change("head-filter", "", "input");
  change("head-sort", "name");
  const headNames = [...document.querySelectorAll("#analytics tbody th")].slice(0, -1).map(n => n.textContent);
  assert(headNames.every((name, i) => i === 0 || headNames[i - 1] <= name), "Formula head name order is deterministic");
  change("head-sort", "count");
  change("file-filter", "__NoSuchFile_4d_8932__", "input");
  assert(byId("file-bars").textContent.includes("No source files match"), "Empty file filter has a visible state");
  change("file-filter", "", "input");
  change("file-sort", "name");
  const fileLabels = [...document.querySelectorAll("#file-bars .bar-label")].map(n => n.textContent);
  const ordered = stats.top_files.map(row => row.path).sort();
  assert(JSON.stringify(fileLabels) === JSON.stringify(ordered.slice(0, 12)), "File sorting happens before pagination");
  if (ordered.length > 12) {
    document.querySelector("nav[aria-label='Source file pages'] button:last-child").click();
    assert(document.querySelector("#file-bars .bar-label").textContent === ordered[12], "File paging reaches the next population slice");
  }
  change("file-filter", "", "input");
  change("file-sort", "count");
  change("degree-mode", "bins");
  const degreeSum = () => [...document.querySelectorAll("#degree-chart .bar-count")].reduce((sum, row) => sum + count(row), 0);
  assert(degreeSum() === metrics.term_denominator, "Grouped degree bars preserve all indexed symbols");
  change("degree-mode", "exact");
  assert(degreeSum() === metrics.term_denominator, "Exact degree view preserves all indexed symbols");
  assert(document.querySelectorAll("#degree-chart .bar-row").length === metrics.degree_distribution.length,
    "Exact degree view includes every measured degree");
  change("degree-mode", "bins");
  const previousTheme = getComputedStyle(document.documentElement).colorScheme;
  byId("theme").click();
  assert(getComputedStyle(document.documentElement).colorScheme !== previousTheme, "Theme toggles from the effective system or explicit appearance");
  byId("theme").click();
  assert(document.querySelector("#file-distribution img, #analytics img, #file-distribution [onerror], #analytics [onerror]") === null,
    "Corpus labels remain inert text");
  assert(!/NaN|Infinity/.test(document.querySelector("#analytics").textContent), "Metrics render without nonfinite labels");
  if (offline) {
    assert([...document.scripts].every(script => !script.src), "Offline report embeds every executable script");
    assert(performance.getEntriesByType("resource").every(entry => !/^https?:/.test(entry.name)), "Offline report requests no network resources");
  } else {
    await waitFor(() => byId("graph").getAttribute("aria-busy") === "false", "Initial graph did not settle");
    const term = byId("term-title").textContent;
    const graph = await (await fetch(`/api/graph?term=${encodeURIComponent(term)}&limit=20`)).json();
    change("graph-limit", "20");
    await waitFor(() => byId("graph").getAttribute("aria-busy") === "false", "Budget request did not settle");
    assert(document.querySelectorAll("#relationships li").length === (graph.returned_edges || 1), "Loaded relationship list agrees with the real graph response");
    assert(byId("graph-status").textContent.includes(`${viewNumber(graph.total_edges)} matching`), "Graph reports the uncapped matching population");
    if (graph.truncated) assert(byId("graph-status").textContent.includes("omitted by the edge budget"), "Truncated graph explicitly reports omissions");
    if (graph.relations.length) {
      const relation = graph.relations[0].relation;
      change("graph-relation", relation);
      await waitFor(() => byId("graph").getAttribute("aria-busy") === "false", "Relation request did not settle");
      assert([...document.querySelectorAll(".relation-arrow")].every(node => node.textContent === `${relation} →`), "Relation selection filters the directed diagram");
      assert(document.querySelectorAll(".relation-row").length <= 8, "Diagram pages cap rows without overlapping graph labels");
      const endpoint = document.querySelector(".relation-node");
      if (endpoint) {
        assert(endpoint.tagName === "BUTTON" && endpoint.getBoundingClientRect().height >= 44, "Graph endpoints are native controls with usable target height");
        const nextTerm = endpoint.textContent;
        endpoint.click();
        await waitFor(() => byId("term-title").textContent === nextTerm && byId("graph").getAttribute("aria-busy") === "false", "Graph endpoint navigation did not settle");
        assert(document.activeElement === byId("term-title"), "Endpoint navigation transfers focus to the selected term heading");
        await selectTerm(term);
        await waitFor(() => byId("graph").getAttribute("aria-busy") === "false", "Endpoint navigation reset did not settle");
      }
    }
    change("graph-relation", ""); change("graph-limit", "40");
    await waitFor(() => byId("graph").getAttribute("aria-busy") === "false", "Graph reset did not settle");
    change("belief", "80", "input");
    await waitFor(() => byId("fep-metrics").textContent.includes("0.0000"), "FEP optimum did not render");
    assert(byId("belief-value").textContent === "0.80", "FEP control displays the posterior optimum");
    change("belief", "50", "input");
    if (byId("corpus-table")) {
      const settled = async () => waitFor(() => byId("corpus-table").getAttribute("aria-busy") === "false", "Corpus query did not settle");
      assert(document.documentElement.dataset.theme === "light" && getComputedStyle(document.documentElement).backgroundColor === "rgb(255, 255, 255)", "Fresh workspace uses white explicit light theme");
      const full = await (await fetch("/api/corpus/formulas?limit=25")).json();
      openCorpusEvidence(); await settled();
      assert(document.querySelectorAll("#corpus-table tbody tr").length === full.returned, "Formula table matches real page size");
      assert(byId("corpus-status").textContent.includes(viewNumber(full.total)), "Formula status discloses full denominator");
      const first = document.querySelector("#corpus-table tbody .table-action");
      if (first) {
        first.click();
        assert(document.activeElement === byId("inspector-title"), "Formula inspection hands focus to source heading");
        assert(byId("inspector-content").querySelector("pre").textContent === full.items[0].text, "Source inspector preserves exact indexed formula text");
        assert(byId("inspector-content").textContent.includes(full.items[0].source_sha256), "Source inspector discloses indexed file hash");
        document.querySelector("#corpus-table input[type=checkbox]").click();
        assert(!byId("corpus-export").disabled && byId("corpus-selected").textContent.startsWith("1 "), "Checked row enables explicit selected-data export");
      }
      if (full.has_more) {
        byId("corpus-next").click(); await settled();
        assert(byId("corpus-page").textContent.includes("26"), "Formula pagination reaches rows beyond the first page");
        assert(byId("corpus-export").disabled && byId("corpus-selected").textContent.startsWith("0 "), "Changing page clears stale selections");
      }
      change("corpus-text", "__NoSuchFormula_8932__", "input");
      byId("corpus-form").requestSubmit(); await settled();
      assert(byId("corpus-table").textContent.includes("No indexed rows"), "Empty formula query has visible state");
      assert(byId("corpus-next").disabled && byId("corpus-export").disabled, "Empty result disables paging and export");
      change("corpus-head", " ", "input");
      byId("corpus-form").requestSubmit(); await settled();
      assert(byId("corpus-status").textContent.includes("Query failed:"), "Real HTTP 422 renders a visible query error");
      assert(byId("corpus-table").querySelector("button").textContent === "Retry query", "Query failure exposes retry without stale rows");
      openCorpusEvidence({}, "files"); await settled();
      const files = await (await fetch("/api/corpus/files?limit=25")).json();
      assert(document.querySelectorAll("#corpus-table tbody tr").length === files.returned, "File table pages the real complete population");
      assert(byId("corpus-text").disabled && !byId("corpus-sort").disabled, "File view enables only applicable filters");
      if (files.returned) {
        document.querySelector("#corpus-table tbody .table-action").click(); await settled();
        assert(byId("corpus-path").value === files.items[0].path && byId("corpus-view").value === "formulas", "File row drills down to exact source-file formulas");
        assert(document.activeElement === byId("query-title"), "Corpus drill-down hands focus to evidence heading");
      }
      await waitFor(() => byId("relation-filter") && byId("taxonomy-status").textContent.includes("endpoint symbols"), "Relation and taxonomy controls did not load");
      change("relation-filter", "__NoSuchRelation8932__", "input");
      assert(byId("relation-inventory").textContent.includes("No relation names match"), "Relation inventory filter has visible empty state");
      change("relation-filter", "", "input");
      const taxonomy = await (await fetch("/api/taxonomy?limit=50")).json();
      const candidate = taxonomy.items.find(item => item.parent_count > 0);
      const neighborhood = await (await fetch(`/api/graph?term=${encodeURIComponent(candidate.name)}&relation=subclass&limit=100`)).json();
      const direct = neighborhood.edges.find(edge => edge.source === candidate.name);
      assert(direct, "A real direct taxonomy edge is available for path controls");
      change("path-source", direct.source, "input"); change("path-target", direct.target, "input"); change("path-depth", "0", "input");
      byId("path-source").closest("form").requestSubmit();
      await waitFor(() => byId("path-result").getAttribute("aria-busy") === "false", "Bounded path did not settle");
      const bounded = await (await fetch(`/api/taxonomy/path?source=${encodeURIComponent(direct.source)}&target=${encodeURIComponent(direct.target)}&max_depth=0`)).json();
      assert(bounded.status === "max_depth" && byId("path-status").textContent.includes("absence is not established"), "Depth exhaustion is distinct from exhaustive path absence");
      change("path-depth", "20", "input"); byId("path-source").closest("form").requestSubmit();
      await waitFor(() => byId("path-result").getAttribute("aria-busy") === "false", "Source path did not settle");
      assert(byId("path-status").textContent.includes("Shortest source path found"), "Taxonomy path renders real found state");
      assert(byId("path-result").querySelector("button"), "Found path exposes exact source evidence actions");
      openCorpusEvidence(); await settled();
    }
  }
  assert(document.documentElement.scrollWidth <= innerWidth, "Viewport has no horizontal page overflow");
  return { surface: offline ? "offline" : "live", width: innerWidth, height: innerHeight, checks };
}

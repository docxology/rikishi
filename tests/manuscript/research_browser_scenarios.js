() => {
  "use strict";
  const checks = [];
  const assert = (condition, message) => {
    if (!condition) throw new Error(message);
    checks.push(message);
  };
  const byId = id => document.getElementById(id);
  const data = JSON.parse(byId("research-data").textContent);
  const first = data.reports[0].report;
  const logical = data.reports.flatMap(binding => binding.report.logical);
  const initialTotals = byId("population").textContent;
  assert(byId("complete-provenance").textContent === data.provenance.join("\n"),
    "Complete source custody remains visible outside the compact figure");
  const change = (id, value) => {
    byId(id).value = value;
    byId(id).dispatchEvent(new Event("change", {bubbles: true}));
  };
  const rowCount = id => byId(id).querySelectorAll("tr").length;
  assert(rowCount("logical-rows") === logical.length, "All validated logical observations render");
  assert(rowCount("numerical-rows") === data.numerical_rows.length, "All numerical rows render without sampling");
  assert(rowCount("invalid-rows") === first.numerical.invalid.length, "All invalid controls render");
  for (const status of new Set(logical.map(run => run.observed))) {
    change("logical-status", status);
    assert(rowCount("logical-rows") === logical.filter(run => run.observed === status).length,
      `Status ${status} selects the measured population`);
  }
  change("logical-status", "");
  for (const disposition of ["matched", "mismatch", "unresolved"]) {
    change("logical-disposition", disposition);
    const expected = logical.filter(run => run.disposition === disposition).length;
    assert(rowCount("logical-rows") === expected && byId("logical-empty").hidden === (expected > 0),
      `Disposition ${disposition} preserves counts and the empty state`);
  }
  change("logical-disposition", "");
  for (const dimension of new Set(data.numerical_rows.map(row => row.dimension))) {
    change("numerical-dimension", String(dimension));
    for (const candidate of new Set(data.numerical_rows.map(row => row.candidate))) {
      change("numerical-candidate", candidate);
      const expected = data.numerical_rows.filter(row => row.dimension === dimension && row.candidate === candidate).length;
      assert(rowCount("numerical-rows") === expected && byId("numerical-empty").hidden === (expected > 0),
        `Dimension ${dimension} / ${candidate} filters actual rows`);
    }
  }
  change("numerical-dimension", ""); change("numerical-candidate", "");
  change("numerical-population", "boundary");
  assert(rowCount("numerical-rows") === first.numerical.extremes.length, "Boundary population stays separate");
  change("numerical-population", "ordinary");
  assert(rowCount("numerical-rows") === first.numerical.rows.length, "Ordinary population matches its denominator");
  change("numerical-population", "");
  assert(byId("population").textContent === initialTotals, "Filters preserve visible full-population totals");
  assert([...document.querySelectorAll("select")].every(select => document.querySelector(`label[for='${select.id}']`)),
    "All native filters have associated labels");
  assert(byId("logical-count").getAttribute("aria-live") === "polite" && byId("numerical-count").getAttribute("aria-live") === "polite",
    "Filtered counts announce updates");
  byId("grayscale").click();
  assert(byId("grayscale").getAttribute("aria-pressed") === "true" && document.body.classList.contains("grayscale"),
    "Grayscale changes the visible figure and pressed state");
  byId("grayscale").click();
  assert([...document.scripts].every(script => !script.src), "Executable scripts are fully embedded");
  assert(!document.querySelector("#provenance img, #source-inputs img, #logical-inputs img, [onerror], [onclick]"),
    "Source and user strings remain inert DOM text");
  assert(performance.getEntriesByType("resource").every(entry => !/^https?:/.test(entry.name)),
    "The local explorer requests no network resources");
  return {checks, viewport: {width: innerWidth, height: innerHeight},
    pageOverflow: document.documentElement.scrollWidth > innerWidth,
    logicalRows: logical.length, numericalRows: data.numerical_rows.length};
}

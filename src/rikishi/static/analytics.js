"use strict";

function viewElement(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function viewNumber(value) { return Number(value).toLocaleString("en-US"); }
function viewPercent(value) { return value === null ? "undefined (empty population)" : `${(100 * value).toFixed(2)}%`; }

function setupTheme() {
  const button = document.getElementById("theme");
  function isDark() {
    return document.documentElement.dataset.theme === "dark";
  }
  function label() { button.textContent = isDark() ? "Use light theme" : "Use dark theme"; button.setAttribute("aria-label", button.textContent); }
  button.addEventListener("click", () => {
    document.documentElement.dataset.theme = isDark() ? "light" : "dark";
    label();
  });
  document.documentElement.dataset.theme = "light";
  label();
}

function viewControl(id, title, choices) {
  const label = viewElement("label", title);
  label.htmlFor = id;
  const select = viewElement("select");
  select.id = id;
  for (const [value, text] of choices) {
    const option = viewElement("option", text);
    option.value = value;
    select.append(option);
  }
  label.append(select);
  return { label, select };
}

function viewPager(label) {
  const node = viewElement("nav", undefined, "pager");
  node.setAttribute("aria-label", label);
  const previous = viewElement("button", "Previous"), next = viewElement("button", "Next");
  previous.type = next.type = "button";
  const status = viewElement("span");
  status.setAttribute("role", "status");
  node.append(previous, status, next);
  return { node, previous, next, status };
}

function viewBar(label, count, denominator, suffix = "") {
  const row = viewElement("div", undefined, "bar-row");
  const track = viewElement("div", undefined, "bar-track");
  track.setAttribute("aria-hidden", "true");
  const fill = viewElement("div", undefined, "bar-fill");
  fill.style.width = `${denominator ? 100 * count / denominator : 0}%`;
  track.append(fill);
  row.append(viewElement("span", label, "bar-label"), track,
    viewElement("span", `${viewNumber(count)}${suffix}`, "bar-count"));
  return row;
}

function renderFileDistribution(data, target) {
  target.tabIndex = 0;
  target.setAttribute("role", "region");
  target.setAttribute("aria-label", "Source file distribution; scroll for all controls and rows");
  const controls = viewElement("div", undefined, "view-controls");
  const label = viewElement("label", "Filter source files");
  label.htmlFor = "file-filter";
  const filter = viewElement("input");
  filter.id = "file-filter";
  filter.type = "search";
  filter.placeholder = "Source filename";
  label.append(filter);
  const sort = viewControl("file-sort", "Order files", [["count", "Formula count"], ["name", "Filename"]]);
  controls.append(label, sort.label);
  const population = viewElement("p", undefined, "muted");
  const bars = viewElement("div", undefined, "bars");
  bars.id = "file-bars";
  const pager = viewPager("Source file pages");
  const pageSize = 12;
  let page = 0;
  const files = [...data.top_files];
  const maximum = Math.max(1, ...files.map(row => row.formulas));
  function render() {
    const query = filter.value.trim().toLowerCase();
    const rows = files.filter(row => row.path.toLowerCase().includes(query));
    rows.sort((a, b) => (sort.select.value === "count" ? b.formulas - a.formulas : 0) ||
      (a.path < b.path ? -1 : a.path > b.path ? 1 : 0));
    page = Math.min(page, Math.max(0, Math.ceil(rows.length / pageSize) - 1));
    const visible = rows.slice(page * pageSize, (page + 1) * pageSize);
    bars.replaceChildren(...visible.map(row => {
      const bar = viewBar(row.path, row.formulas, maximum);
      if (window.openCorpusEvidence) {
        const button = viewElement("button", row.path, "bar-label");
        button.type = "button";
        button.setAttribute("aria-label", `Inspect formulas in ${row.path}`);
        button.addEventListener("click", () => window.openCorpusEvidence({ path: row.path }));
        bar.firstChild.replaceWith(button);
      }
      return bar;
    }));
    if (!visible.length) bars.append(viewElement("p", "No source files match this filter."));
    const matchingCount = rows.reduce((sum, row) => sum + row.formulas, 0);
    population.textContent = `${viewNumber(rows.length)} of ${viewNumber(data.files)} indexed files match; ` +
      `${viewNumber(matchingCount)} of ${viewNumber(data.formulas)} formulas ` +
      `(${viewPercent(data.formulas ? matchingCount / data.formulas : null)}). Bar scale stays fixed to the largest indexed file.`;
    pager.status.textContent = rows.length ? `Files ${page * pageSize + 1}–${page * pageSize + visible.length} of ${viewNumber(rows.length)}` : "0 files";
    pager.previous.disabled = page === 0;
    pager.next.disabled = (page + 1) * pageSize >= rows.length;
  }
  filter.addEventListener("input", () => { page = 0; render(); });
  sort.select.addEventListener("change", () => { page = 0; render(); });
  pager.previous.addEventListener("click", () => { page--; render(); });
  pager.next.addEventListener("click", () => { page++; render(); });
  target.replaceChildren(controls, population, bars, pager.node);
  render();
}

function renderAnalytics(data, target) {
  target.tabIndex = 0;
  target.setAttribute("role", "region");
  target.setAttribute("aria-label", "Corpus composition and degree measurements; scroll for all content");
  target.replaceChildren(viewElement("h2", "Composition and connectivity"));
  target.append(viewElement("p", `Largest file: ${viewPercent(data.largest_file_share)} of ${viewNumber(data.formula_denominator)} formulas. ` +
    `Top ten files: ${viewPercent(data.top_ten_file_share)}. Herfindahl–Hirschman index (HHI): ${data.file_hhi === null ? "undefined" : data.file_hhi.toFixed(4)}.`, "muted"));
  target.append(viewElement("p", `${viewNumber(data.edge_assertions)} edge assertions; ${viewNumber(data.unique_edges)} distinct labeled directed triples; ` +
    `${viewNumber(data.duplicate_edge_assertions)} repeated assertions. ${viewNumber(data.zero_degree_terms)} of ${viewNumber(data.term_denominator)} indexed symbols have zero degree.`, "muted"));
  const layout = viewElement("div", undefined, "analytics-grid");
  const composition = viewElement("section");
  composition.append(viewElement("h3", "Formula head composition"));
  const controls = viewElement("div", undefined, "view-controls");
  const label = viewElement("label", "Filter formula heads");
  label.htmlFor = "head-filter";
  const filter = viewElement("input");
  filter.id = "head-filter";
  filter.type = "search";
  label.append(filter);
  const sort = viewControl("head-sort", "Order heads", [["count", "Formula count"], ["name", "Head name"]]);
  controls.append(label, sort.label);
  const table = viewElement("table"), caption = viewElement("caption", "Shares of all indexed formulas");
  const head = viewElement("thead"), heading = viewElement("tr"), body = viewElement("tbody");
  for (const text of ["Head", "Formulas", "Share"]) {
    const cell = viewElement("th", text); cell.scope = "col"; heading.append(cell);
  }
  head.append(heading); table.append(caption, head, body);
  const population = viewElement("p", undefined, "muted");
  const pager = viewPager("Formula head pages");
  let page = 0;
  function renderHeads() {
    const rows = data.predicates.filter(row => row.label.toLowerCase().includes(filter.value.trim().toLowerCase()));
    rows.sort((a, b) => (sort.select.value === "count" ? b.count - a.count : 0) ||
      (a.label < b.label ? -1 : a.label > b.label ? 1 : 0));
    const visible = rows.slice(page * 8, (page + 1) * 8);
    const shownCount = visible.reduce((sum, row) => sum + row.count, 0);
    const remainder = data.formula_denominator - shownCount;
    body.replaceChildren();
    for (const row of [...visible, { label: "All other heads (outside this page)", count: remainder,
      share: data.formula_denominator ? remainder / data.formula_denominator : null }]) {
      const tr = viewElement("tr"), name = viewElement("th", row.label);
      name.scope = "row";
      if (window.openCorpusEvidence && visible.includes(row)) {
        const button = viewElement("button", row.label, "table-action");
        button.type = "button";
        button.addEventListener("click", () => window.openCorpusEvidence({ head: row.label }));
        name.replaceChildren(button);
      }
      tr.append(name, viewElement("td", viewNumber(row.count)), viewElement("td", viewPercent(row.share)));
      body.append(tr);
    }
    population.textContent = `${viewNumber(rows.length)} of ${viewNumber(data.predicates.length)} heads match. ` +
      `Denominator stays ${viewNumber(data.formula_denominator)} formulas; the remainder includes every head outside this page and filter.`;
    pager.status.textContent = rows.length ? `Heads ${page * 8 + 1}–${page * 8 + visible.length} of ${viewNumber(rows.length)}` : "No matching heads";
    pager.previous.disabled = page === 0;
    pager.next.disabled = (page + 1) * 8 >= rows.length;
  }
  filter.addEventListener("input", () => { page = 0; renderHeads(); });
  sort.select.addEventListener("change", () => { page = 0; renderHeads(); });
  pager.previous.addEventListener("click", () => { page--; renderHeads(); });
  pager.next.addEventListener("click", () => { page++; renderHeads(); });
  composition.append(controls, population, table, pager.node);
  const degrees = viewElement("section");
  degrees.append(viewElement("h3", "Degree distribution"), viewElement("p",
    `Symbols by in + out degree of distinct labeled triples; self-loops count twice. Every bar is scaled to all ${viewNumber(data.term_denominator)} indexed symbols.`, "muted"));
  const mode = viewControl("degree-mode", "Degree detail", [["bins", "Grouped degrees"], ["exact", "Exact degrees"]]);
  const chart = viewElement("div", undefined, "degree-chart");
  chart.id = "degree-chart";
  chart.tabIndex = 0;
  chart.setAttribute("role", "region");
  chart.setAttribute("aria-label", "Degree counts and shares; scroll for exact degrees");
  function renderDegrees() {
    const bins = [{ label: "0", lo: 0, hi: 0 }, { label: "1", lo: 1, hi: 1 },
      { label: "2–4", lo: 2, hi: 4 }, { label: "5–16", lo: 5, hi: 16 },
      { label: "17–64", lo: 17, hi: 64 }, { label: "65+", lo: 65, hi: Infinity }];
    const rows = mode.select.value === "exact" ? data.degree_distribution.map(row => ({ label: String(row.degree), count: row.terms })) :
      bins.map(bin => ({ label: bin.label, count: data.degree_distribution.filter(row => row.degree >= bin.lo && row.degree <= bin.hi)
        .reduce((sum, row) => sum + row.terms, 0) }));
    chart.replaceChildren(...rows.map(row => viewBar(row.label, row.count, data.term_denominator,
      ` (${viewPercent(data.term_denominator ? row.count / data.term_denominator : null)})`)));
    if (!data.term_denominator) chart.replaceChildren(viewElement("p", "No indexed symbols; degree shares are undefined."));
  }
  mode.select.addEventListener("change", renderDegrees);
  degrees.append(mode.label, chart);
  layout.append(composition, degrees);
  target.append(layout, viewElement("p", `Source revision ${data.source_commit}; clean: ${String(data.source_clean)}. ` +
    `${data.rejected_files} rejected source files. These describe the successfully indexed syntax population. Nested assertions and inferred closure are excluded from the graph. Runtime cached formulas are a different population.`, "muted"));
  renderHeads(); renderDegrees();
}

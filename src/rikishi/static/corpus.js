"use strict";

(() => {
  const byId = id => document.getElementById(id);
  const make = viewElement;
  const selected = new Map();
  let request = 0, page = null, applied = null;
  const fields = ["text", "head", "path", "term"];

  function action(label, callback, className = "table-action") {
    const button = make("button", label, className);
    button.type = "button";
    button.addEventListener("click", callback);
    return button;
  }
  function jump(id) {
    const section = byId(id);
    const heading = section.querySelector("h2, h3");
    section.scrollIntoView({ block: "start" });
    if (heading) { heading.tabIndex = -1; heading.focus({ preventScroll: true }); }
  }
  function provenanceText(data) {
    return `Source revision ${data.source_commit || "unversioned"}; clean at index build: ${String(data.source_clean)}.`;
  }
  function download(data, name) {
    const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
    const link = make("a");
    link.href = url; link.download = name;
    document.body.append(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  async function copy(text, target) {
    target.querySelector(".copy-fallback")?.remove();
    try {
      if (!navigator.clipboard?.writeText) throw new Error("Clipboard access is unavailable");
      await navigator.clipboard.writeText(text);
      byId("corpus-status").textContent = "Copied the requested source data.";
    } catch (error) {
      const wrapper = make("div", undefined, "copy-fallback");
      const label = make("label", `${error.message}. Copy the selected text below with your keyboard.`);
      const area = make("textarea");
      area.readOnly = true; area.value = text;
      label.append(area); wrapper.append(label); target.append(wrapper);
      area.focus(); area.select();
    }
  }
  function selectionStatus() {
    byId("corpus-selected").textContent = `${viewNumber(selected.size)} rows selected on this page`;
    byId("corpus-copy").disabled = byId("corpus-export").disabled = !selected.size;
    const all = byId("corpus-select-all");
    all.disabled = !page?.returned;
    all.checked = !!page?.returned && selected.size === page.returned;
    all.indeterminate = selected.size > 0 && selected.size < page.returned;
  }
  function checkedPacket() {
    return {
      dataset: applied.view, query: applied.params, selection_scope: "checked rows on the displayed page",
      total: page.total, filtered_total: page.filtered_total, returned: page.returned,
      selected: selected.size, provenance: page.provenance, scope: page.scope,
      items: [...selected.values()]
    };
  }
  function table(headers, caption) {
    const node = make("table"), head = make("thead"), row = make("tr"), body = make("tbody");
    for (const text of headers) { const cell = make("th", text); cell.scope = "col"; row.append(cell); }
    head.append(row); node.append(make("caption", caption), head, body);
    return { node, body };
  }
  function sourceInspector(item, origin) {
    const section = byId("source-inspector"), target = byId("inspector-content");
    target.replaceChildren(
      make("p", `${item.path}:${item.line} · ${item.predicate} · indexed formula #${item.id}`),
      make("pre", item.text),
      make("p", `Source file SHA-256 at index build: ${item.source_sha256}`, "muted"),
      make("p", provenanceText(origin), "muted")
    );
    const actions = make("div", undefined, "source-actions");
    actions.append(action("Copy exact indexed formula", () => copy(item.text, target)));
    if (origin.source_clean === true && /^[a-f0-9]{40}$/i.test(origin.source_commit)) {
      const link = make("a", "Open pinned upstream source");
      link.href = `https://github.com/ontologyportal/sumo/blob/${origin.source_commit}/${item.path.split("/").map(encodeURIComponent).join("/")}#L${item.line}`;
      link.target = "_blank"; link.rel = "noopener noreferrer"; actions.append(link);
    }
    target.append(actions); section.hidden = false; jump("source-inspector");
  }
  function renderPage() {
    const files = applied.view === "files";
    const result = table(files ? ["Select", "Source file", "Formulas", "SHA-256 at index build"] :
      ["Select", "Source / starting line", "Formula head", "Exact indexed formula"],
      files ? "Complete indexed file population, paged after filtering" : "Retained top-level KIF formulas, ordered by file, line, then formula ID");
    page.items.forEach((item, index) => {
      const row = make("tr"), checkCell = make("td"), label = make("label", undefined, "checkbox-label"), check = make("input");
      check.type = "checkbox"; check.dataset.index = index;
      check.setAttribute("aria-label", `Select ${files ? item.path : item.path + ":" + item.line}`);
      check.addEventListener("change", () => {
        if (check.checked) selected.set(index, item); else selected.delete(index);
        selectionStatus();
      });
      label.append(check); checkCell.append(label); row.append(checkCell);
      const name = make("td");
      name.append(action(files ? item.path : `${item.path}:${item.line}`,
        () => files ? openEvidence({ path: item.path }) : sourceInspector(item, page.provenance)));
      row.append(name);
      if (files) row.append(make("td", viewNumber(item.formulas), "number"), make("td", item.sha256, "hash"));
      else {
        const head = make("td"); head.append(action(item.predicate, () => openEvidence({ head: item.predicate })));
        const formula = make("td"); formula.append(make("pre", item.text));
        row.append(head, formula);
      }
      result.body.append(row);
    });
    byId("corpus-table").replaceChildren(page.items.length ? result.node :
      make("p", "No indexed rows match these filters. Clear filters or broaden the query.", "muted"));
    byId("corpus-status").textContent = `${viewNumber(page.filtered_total)} of ${viewNumber(page.total)} ${files ? "files" : "formulas"} match; ${viewNumber(page.returned)} returned on this page. ` +
      (files ? `${viewNumber(page.filtered_formulas)} of ${viewNumber(page.total_formulas)} indexed formulas are in the matching files. ` : "") +
      (page.truncated ? "Other matching rows remain outside this page." : "The full matching population is on this page.");
    byId("corpus-page").textContent = page.returned ?
      `Rows ${viewNumber(page.offset + 1)}–${viewNumber(page.offset + page.returned)} of ${viewNumber(page.filtered_total)}` : "0 rows";
    byId("corpus-previous").disabled = page.offset === 0;
    byId("corpus-next").disabled = !page.has_more;
    byId("corpus-query-provenance").textContent = `${provenanceText(page.provenance)} ${page.scope}. Exports contain checked rows only.`;
    selectionStatus();
  }
  function configureView() {
    const files = byId("corpus-view").value === "files";
    for (const name of ["text", "head", "term"]) {
      byId("corpus-" + name).disabled = files;
      byId("corpus-" + name).parentElement.hidden = files;
    }
    for (const name of ["sort", "direction"]) {
      byId("corpus-" + name).disabled = !files;
      byId("corpus-" + name).parentElement.hidden = !files;
    }
    byId("path-label").textContent = files ? "Source filename contains" : "Exact source file";
    byId("query-help").textContent = files ?
      "Filename matching is a literal, case-sensitive substring. Sorting runs across all matching files before pagination." :
      "Filters run against the complete index before pagination. Formula text is literal and case-sensitive; head, file, and symbol filters are exact.";
  }
  function readQuery() {
    const view = byId("corpus-view").value;
    const params = { limit: byId("corpus-limit").value, offset: "0", path: byId("corpus-path").value };
    if (view === "files") { params.sort = byId("corpus-sort").value; params.descending = byId("corpus-direction").value; }
    else for (const field of fields) params[field] = byId("corpus-" + field).value;
    return { view, params };
  }
  async function load(query) {
    const generation = ++request;
    applied = query; page = null; selected.clear();
    byId("corpus-status").textContent = "Loading the indexed population…";
    byId("corpus-table").setAttribute("aria-busy", "true");
    byId("corpus-table").replaceChildren(make("p", "Loading rows…", "muted"));
    byId("corpus-previous").disabled = byId("corpus-next").disabled = true;
    byId("corpus-query-provenance").textContent = "";
    byId("corpus-page").textContent = "Loading…";
    byId("source-inspector").hidden = true; selectionStatus();
    try {
      const data = await api(`/api/corpus/${query.view}?${new URLSearchParams(query.params)}`);
      if (generation !== request) return;
      page = data; renderPage();
    } catch (error) {
      if (generation !== request) return;
      byId("corpus-status").textContent = `Query failed: ${error.message}`;
      byId("corpus-table").replaceChildren(make("p", "Indexed evidence is unavailable for this query.", "error"),
        action("Retry query", () => load(query)));
      byId("corpus-page").textContent = "Query unavailable";
    } finally {
      if (generation === request) byId("corpus-table").setAttribute("aria-busy", "false");
    }
  }
  function openEvidence(filters = {}, view = "formulas") {
    byId("corpus-view").value = view;
    for (const field of fields) byId("corpus-" + field).value = filters[field] || "";
    configureView(); load(readQuery()); jump("corpus-query");
  }
  window.openCorpusEvidence = openEvidence;
  window.inspectCorpusFormula = sourceInspector;
  byId("corpus-form").addEventListener("submit", event => { event.preventDefault(); load(readQuery()); });
  byId("corpus-view").addEventListener("change", () => { configureView(); load(readQuery()); });
  byId("query-reset").addEventListener("click", () => openEvidence({}, byId("corpus-view").value));
  byId("corpus-previous").addEventListener("click", () => load({ view: applied.view, params: { ...applied.params, offset: String(Math.max(0, page.offset - page.limit)) } }));
  byId("corpus-next").addEventListener("click", () => load({ view: applied.view, params: { ...applied.params, offset: String(page.offset + page.limit) } }));
  byId("corpus-select-all").addEventListener("change", event => {
    selected.clear();
    byId("corpus-table").querySelectorAll("input[type=checkbox]").forEach(check => {
      check.checked = event.target.checked;
      if (check.checked) selected.set(Number(check.dataset.index), page.items[Number(check.dataset.index)]);
    });
    selectionStatus();
  });
  byId("corpus-copy").addEventListener("click", () => copy(JSON.stringify(checkedPacket(), null, 2), byId("corpus-query")));
  byId("corpus-export").addEventListener("click", () => download(checkedPacket(), `rikishi-${applied.view}-selected.json`));
  byId("term-all-formulas").addEventListener("click", () => openEvidence({ term: selectedTerm }));
  function navigation() {
    const hash = location.hash || "#corpus";
    document.querySelectorAll("header .workspace-nav a").forEach(link => {
      if (link.hash === hash || link.hash === "#corpus" && !["#workbench", "#inference", "#proof-lab"].includes(hash))
        link.setAttribute("aria-current", "location");
      else link.removeAttribute("aria-current");
    });
  }
  document.querySelectorAll(".workspace-nav a, .skip, a.brand").forEach(link => link.addEventListener("click", event => {
    event.preventDefault();
    const target = document.querySelector(link.hash);
    const heading = target?.querySelector("h2, h1") || target;
    if (heading) {
      history.pushState(null, "", link.hash);
      target.scrollIntoView({ block: "start" });
      heading.tabIndex = -1; heading.focus({ preventScroll: true });
      navigation();
    }
  }));
  window.addEventListener("hashchange", navigation);
  configureView(); navigation(); load(readQuery());

  async function relations() {
    const target = byId("relation-inventory");
    target.setAttribute("aria-busy", "true");
    target.replaceChildren(make("p", "Loading relation inventory…", "muted"));
    try {
      const data = await api("/api/corpus/relations");
      const controls = make("div", undefined, "view-controls");
      const label = make("label", "Filter relation names"), filter = make("input");
      filter.id = "relation-filter"; filter.type = "search"; label.htmlFor = filter.id; label.append(filter);
      const order = viewControl("relation-sort", "Order relations", [["name", "Relation name"], ["count", "Distinct edges"]]);
      controls.append(label, order.label);
      const count = make("p", undefined, "muted"), wrapper = make("div", undefined, "table-scroll");
      wrapper.tabIndex = 0; wrapper.setAttribute("role", "region"); wrapper.setAttribute("aria-label", "Complete relation inventory");
      const pager = viewPager("Relation inventory pages");
      let offset = 0;
      function render() {
        const rows = data.items.filter(item => item.relation.toLowerCase().includes(filter.value.toLowerCase()));
        rows.sort((a, b) => (order.select.value === "count" ? b.unique_edges - a.unique_edges : 0) ||
          (a.relation < b.relation ? -1 : a.relation > b.relation ? 1 : 0));
        const visible = rows.slice(offset, offset + 10);
        const result = table(["Relation", "Assertions", "Distinct edges", "Repeated assertions", "Endpoint symbols"], "Complete inventory of indexed atomic binary relations");
        for (const item of visible) {
          const row = make("tr"), name = make("th"); name.scope = "row";
          name.append(action(item.relation, () => openEvidence({ head: item.relation })));
          row.append(name, ...["assertion_count", "unique_edges", "duplicate_assertions", "node_count"].map(key => make("td", viewNumber(item[key]), "number")));
          result.body.append(row);
        }
        wrapper.replaceChildren(visible.length ? result.node : make("p", "No relation names match this filter.", "muted"));
        count.textContent = `${viewNumber(rows.length)} of ${viewNumber(data.total)} relations match. Entire inventory: ${viewNumber(data.assertion_count)} assertions; ${viewNumber(data.unique_edges)} distinct labeled triples.`;
        pager.status.textContent = rows.length ? `Relations ${offset + 1}–${offset + visible.length} of ${viewNumber(rows.length)}` : "0 relations";
        pager.previous.disabled = !offset; pager.next.disabled = offset + visible.length >= rows.length;
      }
      filter.addEventListener("input", () => { offset = 0; render(); });
      order.select.addEventListener("change", () => { offset = 0; render(); });
      pager.previous.addEventListener("click", () => { offset -= 10; render(); });
      pager.next.addEventListener("click", () => { offset += 10; render(); });
      target.replaceChildren(controls, count, wrapper, pager.node, make("p", `${provenanceText(data.provenance)} ${data.scope}.`, "muted"));
      render();
    } catch (error) { target.replaceChildren(make("p", `Relation inventory failed: ${error.message}`, "error"), action("Retry relation inventory", relations)); }
    finally { target.setAttribute("aria-busy", "false"); }
  }
  relations();

  const taxonomy = byId("taxonomy-workspace");
  const taxonomyForm = make("form"), controls = make("div", undefined, "view-controls");
  const relation = viewControl("taxonomy-relation", "Taxonomy relation", [["subclass", "subclass"], ["subrelation", "subrelation"]]);
  function inputControl(id, title, value = "", type = "text") {
    const label = make("label", title), input = make("input"); input.id = id; label.htmlFor = id;
    input.type = type; input.value = value; input.maxLength = 500;
    if (type === "number") input.inputMode = "numeric";
    label.append(input);
    return { label, input };
  }
  const path = inputControl("taxonomy-file", "Exact source file (optional)");
  const submit = make("button", "Analyze direct taxonomy", "primary"); submit.type = "submit";
  controls.append(relation.label, path.label, submit); taxonomyForm.append(controls);
  const taxonomyStatus = make("p", "Loading direct taxonomy…", "muted"); taxonomyStatus.id = "taxonomy-status"; taxonomyStatus.setAttribute("role", "status");
  const taxonomyResult = make("div"), taxonomyPager = viewPager("Taxonomy node pages");
  taxonomy.append(make("h3", "Direct taxonomy diagnostics"), make("p", "Endpoint-only graph of child → parent assertions. Roots have no asserted parents. Cycles and multiple parents describe source structure, not consistency or logical validity.", "muted"), taxonomyForm, taxonomyStatus, taxonomyResult, taxonomyPager.node);
  let taxonomyRequest = 0, taxonomyPage = null, taxonomyQuery = null;
  async function loadTaxonomy(offset = 0, fresh = false) {
    const generation = ++taxonomyRequest;
    if (fresh || !taxonomyQuery) taxonomyQuery = { relation: relation.select.value, path: path.input.value };
    taxonomyStatus.textContent = "Analyzing indexed direct edges…"; taxonomyResult.setAttribute("aria-busy", "true");
    taxonomyResult.replaceChildren(); taxonomyPager.previous.disabled = taxonomyPager.next.disabled = true;
    try {
      const data = await api(`/api/taxonomy?${new URLSearchParams({ ...taxonomyQuery, limit: "10", offset: String(offset) })}`);
      if (generation !== taxonomyRequest) return;
      taxonomyPage = data;
      taxonomyStatus.textContent = `${viewNumber(data.node_count)} endpoint symbols; ${viewNumber(data.unique_edges)} distinct ${data.relation} edges; ${viewNumber(data.assertion_count)} assertions (${viewNumber(data.duplicate_assertions)} repeated).`;
      const metrics = make("dl", undefined, "compact-metrics");
      for (const [key, title] of [["root_count", "Roots"], ["multiple_parent_count", "Multiple parents"], ["weak_component_count", "Weak components"], ["cyclic_component_count", "Cyclic components"], ["cyclic_node_count", "Symbols in cycles"], ["self_loop_count", "Self-loops"]]) {
        const item = make("div"); item.append(make("dt", title), make("dd", viewNumber(data[key]))); metrics.append(item);
      }
      const wrapper = make("div", undefined, "table-scroll"); wrapper.tabIndex = 0; wrapper.setAttribute("role", "region"); wrapper.setAttribute("aria-label", "Taxonomy endpoint diagnostics");
      const result = table(["Symbol", "Parents", "Children", "Weak component", "Cycle component"], `Endpoint symbols ${data.offset + (data.returned ? 1 : 0)}–${data.offset + data.returned} of ${viewNumber(data.filtered_total)} matching (${viewNumber(data.total)} before file filter)`);
      for (const item of data.items) {
        const row = make("tr"), name = make("th"); name.scope = "row";
        name.append(action(item.name, () => { jump("workbench"); selectTerm(item.name, true); }));
        row.append(name, make("td", viewNumber(item.parent_count)), make("td", viewNumber(item.child_count)), make("td", item.component), make("td", item.cycle_component || "None"));
        result.body.append(row);
      }
      wrapper.append(data.items.length ? result.node : make("p", "No endpoint symbols in this relation/file population.", "muted"));
      taxonomyResult.replaceChildren(metrics, wrapper);
      if (data.cycle_components.length) {
        const details = make("details"); details.append(make("summary", "Cycle component evidence"));
        for (const component of data.cycle_components) details.append(make("p", `${component.representative}: ${viewNumber(component.node_count)} symbols. Listed members: ${component.members.join(", ")}${component.members_truncated ? " (member list truncated)" : ""}.`));
        details.append(make("p", data.cycle_components_truncated ? "Other cyclic components are outside the component budget." : "All cyclic components are listed.", "muted"));
        taxonomyResult.append(details);
      }
      taxonomyResult.append(make("p", `${provenanceText(data.provenance)} ${data.scope}. ${data.truncated ? "Other endpoint rows are outside this page." : "All matching endpoint rows are displayed."}`, "muted"));
      taxonomyPager.status.textContent = data.returned ? `Nodes ${data.offset + 1}–${data.offset + data.returned} of ${viewNumber(data.filtered_total)}` : "0 nodes";
      taxonomyPager.previous.disabled = !data.offset; taxonomyPager.next.disabled = !data.has_more;
    } catch (error) {
      if (generation !== taxonomyRequest) return;
      taxonomyStatus.textContent = `Taxonomy analysis failed: ${error.message}`;
      taxonomyResult.append(action("Retry taxonomy analysis", () => loadTaxonomy(offset)));
      taxonomyPager.status.textContent = "Analysis unavailable";
    } finally { if (generation === taxonomyRequest) taxonomyResult.setAttribute("aria-busy", "false"); }
  }
  taxonomyForm.addEventListener("submit", event => { event.preventDefault(); loadTaxonomy(0, true); });
  taxonomyPager.previous.addEventListener("click", () => loadTaxonomy(Math.max(0, taxonomyPage.offset - taxonomyPage.limit)));
  taxonomyPager.next.addEventListener("click", () => loadTaxonomy(taxonomyPage.offset + taxonomyPage.limit));
  loadTaxonomy();

  const pathForm = make("form"), pathControls = make("div", undefined, "view-controls");
  const from = inputControl("path-source", "Child / source symbol", "Human"), to = inputControl("path-target", "Parent / target symbol", "Entity");
  from.input.required = to.input.required = true;
  const pathRelation = viewControl("path-relation", "Path relation", [["subclass", "subclass"], ["subrelation", "subrelation"]]);
  const pathFile = inputControl("path-file", "Exact source file (optional)");
  const depth = inputControl("path-depth", "Maximum path depth", "20", "number"); depth.input.min = "0"; depth.input.max = "100"; depth.input.required = true;
  const visited = inputControl("path-visited", "Maximum visited symbols", "10000", "number"); visited.input.min = "1"; visited.input.max = "100000"; visited.input.required = true;
  const pathSubmit = make("button", "Find shortest source path", "primary"); pathSubmit.type = "submit";
  pathControls.append(from.label, to.label, pathRelation.label, pathFile.label, depth.label, visited.label, pathSubmit); pathForm.append(pathControls);
  const pathStatus = make("p", "Choose symbols to follow a shortest child-to-parent path.", "muted"); pathStatus.id = "path-status"; pathStatus.setAttribute("role", "status");
  const pathResult = make("div"); pathResult.id = "path-result";
  taxonomy.append(make("h3", "Source-backed taxonomy path"), pathForm, pathStatus, pathResult);
  let pathRequest = 0;
  pathForm.addEventListener("submit", async event => {
    event.preventDefault(); const generation = ++pathRequest;
    pathStatus.textContent = "Searching direct taxonomy paths…"; pathResult.setAttribute("aria-busy", "true"); pathResult.replaceChildren();
    const params = { source: from.input.value, target: to.input.value, relation: pathRelation.select.value, path: pathFile.input.value, max_depth: depth.input.value, max_visited: visited.input.value };
    try {
      const data = await api(`/api/taxonomy/path?${new URLSearchParams(params)}`);
      if (generation !== pathRequest) return;
      const descriptions = { found: "Shortest source path found", not_found: "No directed path exists in the selected reachable population", max_depth: "Depth budget exhausted; path absence is not established", max_visited: "Visited-symbol budget exhausted; path absence is not established" };
      pathStatus.textContent = `${descriptions[data.status]}. ${viewNumber(data.visited)} symbols visited; maximum depth ${data.max_depth}; visited-symbol budget ${viewNumber(data.max_visited)}.`;
      if (data.status === "found") {
        pathResult.append(make("p", data.nodes.join(" → ")));
        if (!data.edges.length) pathResult.append(make("p", "Source and target are identical: a zero-edge path."));
        for (const edge of data.edges) {
          const row = make("div", undefined, "path-edge");
          row.append(make("p", `${edge.source} → ${edge.relation} → ${edge.target}`), action(`Inspect ${edge.formula.path}:${edge.formula.line}`, () => sourceInspector(edge.formula, data.provenance)));
          pathResult.append(row);
        }
      }
      pathResult.append(make("p", `${provenanceText(data.provenance)} ${data.scope}.`, "muted"));
    } catch (error) { if (generation === pathRequest) pathStatus.textContent = `Path query failed: ${error.message}`; }
    finally { if (generation === pathRequest) pathResult.setAttribute("aria-busy", "false"); }
  });
})();

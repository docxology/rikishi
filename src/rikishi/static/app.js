"use strict";
const $ = (id) => document.getElementById(id);
const format = viewNumber;
for (const [id, label] of [["definition", "Selected term documentation"], ["graph", "Direct relationship diagram"], ["formulas", "Selected term source formulas"], ["taxonomy-workspace", "Taxonomy diagnostics and path controls"], ["relation-inventory", "Complete relation inventory"]]) {
  $(id).tabIndex = 0;
  if (!$(id).hasAttribute("role")) $(id).setAttribute("role", "region");
  $(id).setAttribute("aria-label", label);
}
for (const id of ["graph-status", "corpus-status", "corpus-query-provenance", "search-status", "source-summary", "fep-status"]) $(id).tabIndex = 0;
let selection = 0;
let selectedTerm = "Entity";
let graphRequest = 0;
const headerObserver = new ResizeObserver(() => {
  document.documentElement.style.setProperty("--header-height", `${document.querySelector("header").offsetHeight}px`);
});
headerObserver.observe(document.querySelector("header"));
function preserveInitialAnchor() {
  const target = document.getElementById(location.hash.slice(1));
  const state = { active: Boolean(target), reason: target ? "loading" : "no anchor" };
  const events = ["wheel", "keydown", "pointerdown", "touchstart", "click", "beforeinput"];
  const stop = reason => {
    if (!state.active) return;
    state.active = false; state.reason = reason;
    observer.disconnect();
    for (const event of events) window.removeEventListener(event, userInput, true);
  };
  const userInput = () => stop("user input");
  const observer = new ResizeObserver(() => {
    if (!state.active || !target) return;
    const requested = target.getBoundingClientRect().top + scrollY - document.querySelector("header").offsetHeight - 16;
    const position = Math.max(0, Math.min(requested, document.documentElement.scrollHeight - innerHeight));
    scrollTo(0, position);
  });
  if (target) {
    observer.observe(document.querySelector("main"));
    for (const event of events) window.addEventListener(event, userInput, { capture: true, passive: true });
  }
  return { state, stop };
}
const initialAnchor = preserveInitialAnchor();
let pendingRequests = 0, idleTimer;
function element(tag, text, className) { const node = document.createElement(tag); if(text !== undefined) node.textContent = text; if(className) node.className = className; return node; }
async function api(path) {
  pendingRequests++;
  clearTimeout(idleTimer);
  try {
    const response = await fetch(path);
    if (!response.ok) {
      let detail = `Request rejected (${response.status})`;
      if (response.headers.get("content-type")?.includes("application/json")) {
        const data = await response.json();
        if (typeof data.detail === "string") detail = data.detail;
      }
      throw new Error(detail);
    }
    return await response.json();
  } finally {
    pendingRequests--;
    if (!pendingRequests) idleTimer = setTimeout(() => initialAnchor.stop("requests settled"), 100);
  }
}
function reportError(target, error) {
  const retry = element("button", "Reload page");
  retry.type = "button";
  retry.addEventListener("click", () => window.location.reload());
  target.replaceChildren(element("p", error.message, "error"),
    element("p", "Check the local service, then reload this page to retry.", "muted"), retry);
}
function termButton(name) { const button = element("button",name); button.type="button"; button.addEventListener("click",()=>selectTerm(name, true)); return button; }
function drawGraph(data, selected) {
  const graph = $("graph"), rows = element("div", undefined, "relation-rows");
  const pager = viewPager("Relationship diagram pages");
  let page = 0;
  function render() {
    const edges = data.edges.slice(page * 8, (page + 1) * 8);
    rows.replaceChildren(...edges.map(edge => {
      const row = element("div", undefined, "relation-row");
      for (const [role, name] of [["Subject", edge.source], ["Object", edge.target]]) {
        const node = termButton(name);
        node.setAttribute("aria-label", `${role}: explore ${name}`);
        node.className = name === selected ? "relation-node central" : "relation-node";
        if (name === selected) {
          const marker = element("span", "Selected", "selection-marker");
          marker.setAttribute("aria-hidden", "true");
          node.append(" ", marker);
          node.setAttribute("aria-label", `${role}: explore ${name} Selected`);
        }
        if (role === "Object") row.append(element("span", `${edge.relation} →`, "relation-arrow"));
        row.append(node);
      }
      return row;
    }));
    if (!edges.length) rows.append(element("p", "No direct edges match this relation filter.", "muted"));
    pager.status.textContent = edges.length ? `Diagram ${page * 8 + 1}–${page * 8 + edges.length} of ${format(data.returned_edges)} loaded edges` : "0 loaded edges";
    pager.previous.disabled = page === 0;
    pager.next.disabled = (page + 1) * 8 >= data.edges.length;
  }
  pager.previous.addEventListener("click", () => { page--; render(); });
  pager.next.addEventListener("click", () => { page++; render(); });
  graph.replaceChildren(rows, pager.node);
  graph.setAttribute("aria-label", `Directed relationship diagram of ${selected}`);
  $("relationships").replaceChildren(...data.edges.map(edge => {
    const row = element("li");
    row.append(termButton(edge.source), document.createTextNode(` — ${edge.relation} → `), termButton(edge.target));
    return row;
  }));
  if (!data.edges.length) $("relationships").append(element("li", "No matching indexed direct relationships."));
  const omitted = data.total_edges - data.returned_edges;
  const all = data.relations.reduce((sum, row) => sum + row.count, 0);
  $("graph-status").textContent = `${format(data.returned_edges)} of ${format(data.total_edges)} matching distinct directed edges loaded; ` +
    `${format(all)} across all relation types. ` + (data.truncated ? `${format(omitted)} omitted by the edge budget. Increase the budget or choose a relation.` : "No edges omitted by the budget.");
  render();
}

async function updateGraph() {
  const request = ++graphRequest, name = selectedTerm;
  const relation = $("graph-relation").value;
  const params = new URLSearchParams({ term: name, limit: $("graph-limit").value });
  if (relation) params.set("relation", relation);
  $("graph-status").textContent = "Loading direct relationships…";
  $("graph").setAttribute("aria-busy", "true");
  try {
    const data = await api(`/api/graph?${params}`);
    if (request !== graphRequest) return;
    const all = data.relations.reduce((sum, row) => sum + row.count, 0);
    const option = (value, label) => { const node = element("option", label); node.value = value; return node; };
    $("graph-relation").replaceChildren(option("", `All relations (${format(all)})`),
      ...data.relations.map(row => option(row.relation, `${row.relation} (${format(row.count)})`)));
    $("graph-relation").value = relation;
    drawGraph(data, name);
  } catch (error) {
    if (request === graphRequest) {
      reportError($("graph"), error);
      $("relationships").replaceChildren();
      $("graph-status").textContent = "Direct relationships unavailable.";
    }
  } finally {
    if (request === graphRequest) $("graph").setAttribute("aria-busy", "false");
  }
}
async function selectTerm(name, moveFocus = false) {
  const request = ++selection;
  selectedTerm = name;
  $("graph-relation").disabled = $("graph-limit").disabled = false;
  if ($("term-all-formulas")) $("term-all-formulas").disabled = false;
  $("graph-relation").value = "";
  $("term-title").textContent = name;
  $("term-title").tabIndex = -1;
  if (moveFocus) $("term-title").focus({ preventScroll: true });
  $("definition").textContent = "Loading source evidence…";
  for (const id of ["graph", "formulas", "relationships"]) $(id).replaceChildren();
  $("source-summary").textContent = "";
  updateGraph();
  document.querySelectorAll(".result").forEach(button => {
    const selected = button.dataset.name === name;
    button.setAttribute("aria-pressed", String(selected));
    button.querySelector(".selection-marker").hidden = !selected;
  });
  try {
    const [term, stats] = await Promise.all([
      api(`/api/terms/${encodeURIComponent(name)}`),
      api("/api/stats")
    ]);
    if (request !== selection) return;
    const english = new Set(["EnglishWrittenLanguage", "EnglishLanguage"]);
    const documentation = [...term.documentation].sort((a, b) => Number(english.has(b.language)) - Number(english.has(a.language)));
    $("definition").replaceChildren(...documentation.map(d => element("span", `${d.language}: ${d.text} `)));
    if (!documentation.length) $("definition").textContent = "No documentation assertion is indexed for this term. Inspect the source formulas below.";
    $("source-summary").textContent = `${format(term.formula_count)} formula references; displaying ${term.formulas.length} source excerpts.`;
    const pinned = stats.source_clean === true && /^[a-f0-9]{40}$/i.test(stats.source_commit);
    term.formulas.forEach(formula => {
      const details = element("details"), summary = element("summary", `${formula.path}:${formula.line} · ${formula.predicate}`), code = element("pre", formula.text);
      details.append(summary, code);
      if (pinned) {
        const link = element("a", `View ${formula.path}:${formula.line} at pinned SUMO revision ↗`);
        link.href = `https://github.com/ontologyportal/sumo/blob/${stats.source_commit}/${formula.path.split("/").map(encodeURIComponent).join("/")}#L${formula.line}`;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        details.append(link);
      }
      $("formulas").append(details);
    });
  } catch (error) {
    if (request === selection) {
      $("definition").textContent = "Unable to load this term. Check the local service, then reload this page to retry.";
      reportError($("formulas"), error);
    }
  }
}
let searchRequest=0;
function noSelectedTerm(message) {
  $("term-title").textContent = "No term selected";
  $("definition").textContent = message;
  $("graph-status").textContent = "No relationships to display until a term is selected.";
  $("graph").replaceChildren();
  $("graph").setAttribute("aria-busy", "false");
  $("source-summary").textContent = "No source formulas selected.";
  $("formulas").replaceChildren();
  $("graph-relation").disabled = $("graph-limit").disabled = true;
  if ($("term-all-formulas")) $("term-all-formulas").disabled = true;
}
async function search(event) {
  if (event) event.preventDefault();
  const request = ++searchRequest, query = $("query").value.trim();
  if (!query) return;
  $("search-status").textContent = "Searching the local corpus…";
  try {
    const results = await api(`/api/search?q=${encodeURIComponent(query)}&limit=30`);
    if (request !== searchRequest) return;
    $("results").replaceChildren();
    $("search-status").textContent = results.length ? `${results.length} results (maximum 30)` : `No matches for “${query}”. Try a broader term.`;
    results.forEach(result => {
      const button = element("button", undefined, "result");
      button.type = "button"; button.dataset.name = result.name;
      button.setAttribute("aria-pressed", "false");
      const title = element("span", undefined, "result-label");
      const marker = element("span", "Selected", "selection-marker");
      marker.hidden = true;
      marker.setAttribute("aria-hidden", "true");
      title.append(element("span", result.name), marker);
      button.append(title, element("small", `${format(result.formula_count)} formula references`));
      button.addEventListener("click", () => selectTerm(result.name, true));
      $("results").append(button);
    });
    if (results.length) await selectTerm(results[0].name);
    else if (!selection) noSelectedTerm("No indexed symbol matches this search. Broaden the term query or inspect corpus evidence.");
  } catch (error) {
    if (request === searchRequest) {
      $("search-status").textContent = "Search failed.";
      reportError($("results"), error);
      if (!selection) noSelectedTerm("Term search is unavailable. Retry the search when the local service is available.");
    }
  }
}
async function loadStats() {
  try {
    const stats = await api("/api/stats");
    for (const [key, label] of [["files", "Source files"], ["formulas", "KIF formulas"], ["terms", "Indexed symbols"], ["edges", "Edge assertions"]]) {
      const item = element("div");
      item.append(element("dt", label), element("dd", format(stats[key])));
      $("metrics").append(item);
    }
    $("provenance").textContent = `SUMO revision ${stats.source_commit || "unversioned source"}; clean: ${String(stats.source_clean)}.`;
    renderFileDistribution(stats, $("file-distribution"));
    $("file-distribution").setAttribute("aria-busy", "false");
    $("parse-status").textContent = stats.parse_errors.length ? `${stats.parse_errors.length} source files reported parse errors; inspect raw measurements for details.` : "All indexed source files parsed without reported errors.";
  } catch (error) {
    reportError($("file-distribution"), error);
    $("file-distribution").setAttribute("aria-busy", "false");
    $("provenance").textContent = "Index measurements unavailable.";
  }
}
setupTheme();
$("graph-relation").addEventListener("change", updateGraph);
$("graph-limit").addEventListener("change", updateGraph);
$("search-form").addEventListener("submit",search);document.querySelectorAll("[data-term]").forEach(button=>button.addEventListener("click",()=>{$("query").value=button.dataset.term;search();}));loadStats();search();
let energyRequest=0,energyView=null;
function drawEnergy(example,q){
  energyView={example,q};
  const canvas=$("energy-curve"),{width,height}=canvas.getBoundingClientRect();
  if(!width||!height)return;
  const styles=getComputedStyle(canvas),space=name=>parseFloat(styles.getPropertyValue(name));
  const left=space("--s6"),right=width-space("--s3"),top=space("--s6")+space("--s3"),bottom=height-space("--s6");
  const ns="http://www.w3.org/2000/svg",svg=document.createElementNS(ns,"svg");
  const maximum=Math.max(...example.scan.map(p=>p.free_energy))*1.1,x=v=>left+(right-left)*v,y=v=>bottom-(bottom-top)*v/maximum;
  svg.setAttribute("viewBox",`0 0 ${width} ${height}`);
  svg.setAttribute("role","img");
  svg.setAttribute("aria-label",`Free energy curve over candidate probabilities. Minimum at ${example.result.exact_posterior[0]}. Selected q ${q}, free energy ${example.result.free_energy.toFixed(4)} nats.`);
  function node(tag,attrs,text){const item=document.createElementNS(ns,tag);Object.entries(attrs).forEach(([key,value])=>item.setAttribute(key,value));if(text!==undefined)item.textContent=text;svg.append(item);return item;}
  [0,0.5,1].forEach(value=>node("text",{x:x(value),y:bottom+space("--s3"),"text-anchor":"middle"},value.toFixed(1)));
  [0,1,2].forEach(value=>{
    node("line",{x1:left,x2:right,y1:y(value),y2:y(value)});
    node("text",{x:left-space("--s3"),y:y(value)+space("--s0"),"text-anchor":"end"},value.toFixed(1));
  });
  node("text",{x:space("--s3"),y:space("--s4")},"Free energy / nats");
  node("text",{x:(left+right)/2,y:height-space("--s1"),"text-anchor":"middle"},"Candidate probability q(state 0)");
  node("line",{x1:left,x2:right,y1:y(example.result.surprise),y2:y(example.result.surprise),"stroke-dasharray":"5 5",style:"stroke:var(--muted)"});
  node("text",{x:right,y:space("--s5")+space("--s2"),"text-anchor":"end"},"Surprisal lower bound");
  node("path",{d:example.scan.map((p,i)=>`${i?'L':'M'}${x(p.q_state_zero)},${y(p.free_energy)}`).join(" "),fill:"none",stroke:"var(--accent)","stroke-width":2.5});
  node("circle",{cx:x(q),cy:y(example.result.free_energy),r:6});
  canvas.replaceChildren(svg);
}
new ResizeObserver(()=>{if(energyView)drawEnergy(energyView.example,energyView.q);}).observe($("energy-curve"));
async function updateEnergy() {
  const request = ++energyRequest, q = Number($("belief").value) / 100;
  const canvas = $("energy-curve"), metrics = $("fep-metrics"), status = $("fep-status");
  $("belief-value").textContent = q.toFixed(2);
  energyView = null;
  canvas.replaceChildren();
  metrics.replaceChildren();
  canvas.setAttribute("aria-busy", "true");
  metrics.setAttribute("aria-busy", "true");
  status.textContent = `Calculating the finite model for q = ${q.toFixed(2)}…`;
  try {
    const example = await api(`/api/fep?q=${q}`);
    if (request !== energyRequest) return;
    drawEnergy(example, q);
    for (const [key, label] of [["free_energy", "Free energy / nats"], ["surprise", "Surprisal / nats"], ["kl_to_posterior", "KL divergence / nats"], ["evidence", "Observation evidence"]]) {
      const item = element("div");
      item.append(element("dt", label), element("dd", example.result[key].toFixed(4)));
      metrics.append(item);
    }
    status.textContent = `F = surprisal + KL(q ∥ posterior). Exact posterior: [${example.result.exact_posterior.map(x => x.toFixed(2)).join(", ")}]. Identity residual: ${example.result.identity_residual.toExponential(2)}.`;
  } catch (error) {
    if (request !== energyRequest) return;
    energyView = null;
    canvas.replaceChildren();
    metrics.replaceChildren();
    status.textContent = `Calculation failed: ${error.message}. Check the local service, then adjust the slider to retry.`;
  } finally {
    if (request === energyRequest) {
      canvas.setAttribute("aria-busy", "false");
      metrics.setAttribute("aria-busy", "false");
    }
  }
}
$("belief").addEventListener("input",updateEnergy);updateEnergy();
const analyticsSection = $("analytics");
api("/api/analytics").then(data => renderAnalytics(data, analyticsSection))
  .catch(error => reportError(analyticsSection, error))
  .finally(() => analyticsSection.setAttribute("aria-busy", "false"));

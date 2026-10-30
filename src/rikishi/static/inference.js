(() => {
  "use strict";
  const find = id => document.getElementById(id);
  const node = (tag, text, className) => {
    const item = document.createElement(tag);
    if (text !== undefined) item.textContent = String(text);
    if (className) item.className = className;
    return item;
  };
  const labels = {e: "E", v: "Vampire"};
  const kinds = {background: "Background", positive: "Entailment", negative: "Countermodel", "removed-premise": "Removed premise", refutation: "Refutation"};
  let study = null, report = null, descriptor = null, page = 0, controller = null, detailSequence = 0;
  const pageSize = 15;
  async function request(url, signal) {
    const response = await fetch(url, {signal});
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || `Request failed (${response.status})`);
    return data;
  }
  function metric(label, value) {
    const group = node("div");
    group.append(node("dt", label), node("dd", value));
    return group;
  }
  async function detail(scenario, run) {
    const sequence = ++detailSequence;
    const content = find("proof-detail-content");
    find("proof-detail-title").textContent = scenario.title;
    content.replaceChildren(node("p", `${scenario.category} · ${scenario.id}`, "muted"));
    for (const [heading, text] of [["Query", scenario.query], ["Countermodel query", scenario.negative_query]]) {
      content.append(node("h4", heading), node("pre", text));
    }
    content.append(node("h4", "Local assumptions"), node("pre", scenario.assumptions.join("\n") || "None"));
    content.append(node("p", "Local assumptions are authored inputs. Source selections below come from the pinned ontology.", "muted"));
    if (run) {
      const description = run.kind === "background" ? "No conjecture: checks satisfiability of the selected background." :
        run.kind === "refutation" ? `No conjecture: adds the negated positive query as an axiom: (not ${scenario.query})` :
        run.kind === "negative" ? `Submitted conjecture: ${scenario.negative_query}` : `Submitted conjecture: ${scenario.query}`;
      content.append(node("p", `${kinds[run.kind] || run.kind}. ${description}`));
      if (run.kind === "removed-premise") {
        const removed = scenario.removed_selection !== null ? `source selection ${scenario.removed_selection + 1}, starting at line ${scenario.selections[scenario.removed_selection].line}` : `local assumption ${scenario.removed_assumption + 1}: ${scenario.assumptions[scenario.removed_assumption]}`;
        content.append(node("p", `This control omits ${removed}. The source list below records the complete original scenario.`, "muted"));
      }
      content.append(node("h4", "Recorded native result"), node("pre", JSON.stringify({
        prover: labels[run.prover] || run.prover, control: run.kind,
        expected: run.expected, observed: run.observed, matched: run.matched,
        problem_sha256: run.problem_sha256, capture: run.capture,
        capture_sha256: run.capture_sha256, invocation_id: run.invocation_id
      }, null, 2)));
    }
    for (const selection of scenario.selections) {
      const source = report?.source_claims.find(item => item.line === selection.line);
      const disclosure = node("details");
      disclosure.append(node("summary", source ? `Merge.kif:${source.line}–${source.end_line}` : `Merge.kif:${selection.line} · registered selection`));
      if (source) {
        disclosure.append(node("pre", source.raw_kif), node("p", `Source formula SHA-256: ${source.sha256}`, "hash"));
        if (/^[0-9a-f]{40}$/.test(study.source_commit)) {
          const link = node("a", "Inspect pinned upstream source");
          link.href = `https://github.com/ontologyportal/sumo/blob/${study.source_commit}/Merge.kif#L${source.line}-L${source.end_line}`;
          link.target = "_blank"; link.rel = "noopener";
          disclosure.append(link);
        }
      }
      if (Object.keys(selection.predicate_bindings).length) {
        disclosure.append(node("p", "Explicit predicate substitution", "muted"), node("pre", JSON.stringify(selection.predicate_bindings, null, 2)));
      }
      content.append(disclosure);
    }
    find("proof-detail").hidden = false;
    find("proof-detail-title").focus({preventScroll: true});
    find("proof-detail").scrollIntoView({block: "start"});
    if (run && descriptor) {
      const output = node("details"), body = node("div");
      output.append(node("summary", "Submitted problem and native proof output"), body);
      body.append(node("p", "Loading captured evidence…", "muted")); content.append(output);
      const query = new URLSearchParams({...descriptor, case_id: run.id, prover: run.prover});
      try {
        const evidence = await request(`/api/inference/case?${query}`, controller.signal);
        if (sequence !== detailSequence) return;
        body.replaceChildren(node("p", evidence.scope, "muted"), node("h4", "Submitted first-order problem"), node("pre", evidence.problem),
          node("h4", "Native standard output"), node("pre", evidence.stdout));
        if (evidence.stderr) body.append(node("h4", "Native error output"), node("pre", evidence.stderr));
      } catch (error) {
        if (sequence === detailSequence) body.replaceChildren(node("p", `Captured evidence unavailable: ${error.message}. Reload evidence to retry.`, "error"));
      }
    }
  }
  function render() {
    detailSequence++;
    find("proof-detail").hidden = true;
    const category = find("proof-category").value;
    const prover = find("proof-prover").value;
    const outcome = find("proof-outcome").value;
    const scenarios = study?.scenarios || [];
    const byId = new Map(scenarios.map(item => [item.id, item]));
    const rows = (report ? report.cases : scenarios.map(item => ({id: item.id, group: item.id, kind: "Registered", expected: "Not run", observed: "Not run"})))
      .map(run => ({run, scenario: byId.get(run.group) || byId.get(run.id)}))
      .filter(({run, scenario}) => scenario && (!category || scenario.category === category) && (!prover || run.prover === prover) &&
        (!outcome || (outcome === "unmatched" ? !run.matched : run.observed === outcome)));
    const pages = Math.max(1, Math.ceil(rows.length / pageSize));
    page = Math.min(page, pages - 1);
    const table = node("table"), head = node("thead"), body = node("tbody"), headings = node("tr");
    table.append(node("caption", report ? "Retained native outcomes. Select a scenario for its source and query." : "Registered scenarios. Native evidence has not been loaded."));
    for (const text of ["Scenario", "Control", "Prover", "Expected", "Observed", "Check"]) {
      const cell = node("th", text); cell.scope = "col"; headings.append(cell);
    }
    head.append(headings); table.append(head, body);
    for (const {run, scenario} of rows.slice(page * pageSize, (page + 1) * pageSize)) {
      const row = node("tr"), title = node("td"), button = node("button", scenario.title, "table-action");
      button.type = "button";
      button.addEventListener("click", () => detail(scenario, report ? run : null));
      title.append(button, node("div", scenario.category, "muted")); row.append(title);
      for (const text of [kinds[run.kind] || run.kind, labels[run.prover] || "—", run.expected, run.observed,
        report ? (run.matched ? "Matched" : "Unmatched") : "Not run"]) row.append(node("td", text));
      body.append(row);
    }
    find("proof-table").replaceChildren(rows.length ? table : node("p", "No results match these filters. Choose another category, prover or result.", "muted"));
    find("proof-table").setAttribute("aria-busy", "false");
    find("proof-page").textContent = `${rows.length ? page * pageSize + 1 : 0}–${Math.min((page + 1) * pageSize, rows.length)} of ${rows.length} results`;
    find("proof-previous").disabled = page === 0;
    find("proof-next").disabled = page + 1 >= pages;
  }
  async function load() {
    controller?.abort();
    const active = new AbortController(); controller = active;
    study = null; report = null; descriptor = null; page = 0; detailSequence++;
    find("proof-metrics").replaceChildren();
    find("proof-scope").replaceChildren();
    find("proof-detail").hidden = true;
    find("proof-table").replaceChildren(node("p", "Reading study and replaying the published evidence…", "muted"));
    find("proof-table").setAttribute("aria-busy", "true");
    find("proof-status").textContent = "Loading the registered study and published evidence…";
    find("proof-status").className = "";
    find("proof-reload").disabled = true;
    find("proof-previous").disabled = true; find("proof-next").disabled = true;
    const results = await Promise.allSettled([
      request("/api/inference/catalog", active.signal), request("/api/inference/published", active.signal)
    ]);
    if (controller !== active) return;
    find("proof-reload").disabled = false;
    if (results[0].status === "rejected") {
      find("proof-status").textContent = `Study unavailable: ${results[0].reason.message}. Reload evidence to retry.`;
      find("proof-status").className = "error";
      find("proof-table").replaceChildren(); find("proof-table").setAttribute("aria-busy", "false");
      find("proof-page").textContent = "No evidence loaded";
      return;
    }
    study = results[0].value;
    const previousCategory = find("proof-category").value;
    find("proof-category").replaceChildren(new Option("All categories", ""), ...[...new Set(study.scenarios.map(item => item.category))].sort().map(value => new Option(value, value)));
    if ([...find("proof-category").options].some(option => option.value === previousCategory)) find("proof-category").value = previousCategory;
    find("proof-scope").append(node("p", study.semantic_scope), node("p", `Supported syntax: ${study.supported_syntax.join(", ")}`, "muted"));
    if (results[1].status === "fulfilled") {
      const published = results[1].value; report = published.report; descriptor = published.descriptor;
      find("proof-metrics").append(metric("Source scenarios", report.summary.scenarios), metric("Native runs", report.summary.total),
        metric("Matched expectations", report.summary.matched), metric("Unresolved", report.summary.unresolved));
      find("proof-status").textContent = report.summary.passed ? "Published native campaign replayed; every registered expectation matched." : "Campaign replayed with unmatched or unresolved results. Inspect each control.";
      find("proof-scope").append(node("p", published.authority, "muted"), node("p", `Report SHA-256: ${published.descriptor.sha256}`, "hash"), node("p", report.replay_boundary, "muted"));
    } else {
      find("proof-status").textContent = `Native evidence unavailable: ${results[1].reason.message}. Registered scenarios remain inspectable; reload to retry.`;
      find("proof-status").className = "error";
      find("proof-metrics").append(metric("Registered scenarios", study.scenarios.length), metric("Native evidence", "Unavailable"));
    }
    find("proof-prover").disabled = !report; find("proof-outcome").disabled = !report;
    render();
  }
  for (const id of ["proof-category", "proof-prover", "proof-outcome"]) find(id).addEventListener("change", () => {page = 0; render();});
  find("proof-previous").addEventListener("click", () => {page--; render();});
  find("proof-next").addEventListener("click", () => {page++; render();});
  find("proof-reload").addEventListener("click", load);
  load();
})();

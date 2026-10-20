"use strict";
const $ = (id) => document.getElementById(id);
const format = (n) => Number(n).toLocaleString();
let selection = 0;
function element(tag, text, className) { const node = document.createElement(tag); if(text !== undefined) node.textContent = text; if(className) node.className = className; return node; }
async function api(path) { const response = await fetch(path); if(!response.ok) { const data = await response.json(); throw new Error(typeof data.detail === "string" ? data.detail : `Request rejected (${response.status})`); } return response.json(); }
function reportError(target, error) { target.replaceChildren(element("p", error.message, "error")); }
function termButton(name) { const button = element("button",name); button.type="button"; button.addEventListener("click",()=>selectTerm(name)); return button; }
function drawGraph(data, selected) {
  const ns="http://www.w3.org/2000/svg", svg=document.createElementNS(ns,"svg");
  svg.setAttribute("viewBox","0 0 800 430");svg.setAttribute("role","img");svg.setAttribute("aria-label",`Direct relationships of ${selected}; keyboard links follow below`);
  const title=document.createElementNS(ns,"title");title.textContent=`Neighborhood of ${selected}`;svg.append(title);
  const nodes=data.nodes.filter(n=>n.id!==selected), positions=new Map([[selected,{x:400,y:210}]]);
  nodes.forEach((node,i)=>{const angle=2*Math.PI*i/Math.max(nodes.length,1)-Math.PI/2;positions.set(node.id,{x:400+295*Math.cos(angle),y:210+165*Math.sin(angle)});});
  const defs=document.createElementNS(ns,"defs"), marker=document.createElementNS(ns,"marker"), path=document.createElementNS(ns,"path");marker.setAttribute("id","arrow");marker.setAttribute("viewBox","0 0 10 10");marker.setAttribute("refX","8");marker.setAttribute("refY","5");marker.setAttribute("markerWidth","5");marker.setAttribute("markerHeight","5");marker.setAttribute("orient","auto-start-reverse");path.setAttribute("d","M 0 0 L 10 5 L 0 10 z");marker.append(path);defs.append(marker);svg.append(defs);
  data.edges.forEach(edge=>{const a=positions.get(edge.source),b=positions.get(edge.target);if(!a||!b)return;const line=document.createElementNS(ns,"line"),distance=Math.hypot(b.x-a.x,b.y-a.y)||1;line.setAttribute("x1",a.x);line.setAttribute("y1",a.y);line.setAttribute("x2",b.x-(b.x-a.x)*12/distance);line.setAttribute("y2",b.y-(b.y-a.y)*12/distance);line.setAttribute("marker-end","url(#arrow)");svg.append(line);});
  for(const [name,pos] of positions){const group=document.createElementNS(ns,"g"),circle=document.createElementNS(ns,"circle"),label=document.createElementNS(ns,"text");group.setAttribute("role","button");group.setAttribute("tabindex","0");group.setAttribute("aria-label",`Explore ${name}`);if(name===selected)group.setAttribute("class","central");circle.setAttribute("cx",pos.x);circle.setAttribute("cy",pos.y);circle.setAttribute("r",name===selected?13:7);label.setAttribute("x",pos.x);label.setAttribute("y",pos.y+26);label.setAttribute("text-anchor","middle");label.textContent=name.length>26?name.slice(0,24)+"…":name;group.append(circle,label);group.addEventListener("click",()=>selectTerm(name));group.addEventListener("keydown",event=>{if(event.key==="Enter"||event.key===" "){event.preventDefault();selectTerm(name);}});svg.append(group);}
  $("graph").replaceChildren(svg);$("relationships").replaceChildren();data.edges.forEach(edge=>{const row=element("li");row.append(termButton(edge.source),document.createTextNode(` — ${edge.relation} → `),termButton(edge.target));$("relationships").append(row);});
  if(!data.edges.length)$("relationships").append(element("li","No indexed direct relationships for this term."));
}
async function selectTerm(name) {
  const request = ++selection;
  $("term-title").textContent = name;
  $("definition").textContent = "Loading source evidence…";
  for (const id of ["graph", "formulas", "relationships"]) $(id).replaceChildren();
  $("source-summary").textContent = "";
  document.querySelectorAll(".result").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.name === name)));
  try {
    const [term, graph, stats] = await Promise.all([
      api(`/api/terms/${encodeURIComponent(name)}`),
      api(`/api/graph?term=${encodeURIComponent(name)}&limit=40`),
      api("/api/stats")
    ]);
    if (request !== selection) return;
    const english = new Set(["EnglishWrittenLanguage", "EnglishLanguage"]);
    const documentation = [...term.documentation].sort((a, b) => Number(english.has(b.language)) - Number(english.has(a.language)));
    $("definition").replaceChildren(...documentation.map(d => element("span", `${d.language}: ${d.text} `)));
    if (!documentation.length) $("definition").textContent = "No documentation assertion is indexed for this term. Inspect the source formulas below.";
    drawGraph(graph, name);
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
      $("definition").textContent = "Unable to load this term.";
      reportError($("graph"), error);
    }
  }
}
let searchRequest=0;
async function search(event){if(event)event.preventDefault();const request=++searchRequest,query=$("query").value.trim();if(!query)return;$("search-status").textContent="Searching the local corpus…";try{const results=await api(`/api/search?q=${encodeURIComponent(query)}&limit=30`);if(request!==searchRequest)return;$("results").replaceChildren();$("search-status").textContent=results.length?`${results.length} results (maximum 30)`:`No matches for “${query}”. Try a broader term.`;results.forEach(result=>{const button=element("button",undefined,"result");button.type="button";button.dataset.name=result.name;button.setAttribute("aria-pressed","false");button.append(element("span",result.name),element("small",`${format(result.formula_count)} formula references`));button.addEventListener("click",()=>selectTerm(result.name));$("results").append(button);});if(results.length)await selectTerm(results[0].name);}catch(error){if(request===searchRequest){$("search-status").textContent="Search failed.";reportError($("results"),error);}}}
async function loadStats(){try{const stats=await api("/api/stats");for(const [key,label] of [["files","Source files"],["formulas","KIF formulas"],["terms","Indexed terms"],["edges","Direct relations"]]){const item=element("div");item.append(element("dt",label),element("dd",format(stats[key])));$("metrics").append(item);}$("provenance").textContent=`SUMO revision ${stats.source_commit || "unversioned source"}`;const rows=stats.top_files.slice(0,12),max=Math.max(1,...rows.map(r=>r.formulas));rows.forEach(row=>{const item=element("div",undefined,"bar-row"),track=element("div",undefined,"bar-track"),fill=element("div",undefined,"bar-fill");fill.style.width=`${row.formulas/max*100}%`;track.append(fill);item.append(element("span",row.path,"bar-label"),track,element("span",format(row.formulas),"bar-count"));$("bars").append(item);});$("parse-status").textContent=stats.parse_errors.length?`${stats.parse_errors.length} source files reported parse errors; inspect raw measurements for details.`:"All indexed source files parsed without reported errors.";}catch(error){reportError($("bars"),error);$("provenance").textContent="Index measurements unavailable.";}}
$("theme").addEventListener("click",()=>{document.documentElement.dataset.theme=document.documentElement.dataset.theme==="dark"?"light":"dark";});
$("search-form").addEventListener("submit",search);document.querySelectorAll("[data-term]").forEach(button=>button.addEventListener("click",()=>{$("query").value=button.dataset.term;search();}));loadStats();search();
let energyRequest=0;
function drawEnergy(example,q){const ns="http://www.w3.org/2000/svg",svg=document.createElementNS(ns,"svg"),maximum=Math.max(...example.scan.map(p=>p.free_energy))*1.1,x=v=>70+650*v,y=v=>260-210*v/maximum;svg.setAttribute("viewBox","0 0 800 320");svg.setAttribute("role","img");svg.setAttribute("aria-label",`Free energy curve over candidate probabilities. Minimum at 0.8. Selected q ${q}, free energy ${example.result.free_energy.toFixed(4)} nats.`);function node(tag,attrs,text){const item=document.createElementNS(ns,tag);Object.entries(attrs).forEach(([key,value])=>item.setAttribute(key,value));if(text!==undefined)item.textContent=text;svg.append(item);return item;}[0,0.5,1].forEach(value=>{node("text",{x:x(value),y:284,"text-anchor":"middle"},value.toFixed(1));});[0,1,2].forEach(value=>{node("line",{x1:70,x2:720,y1:y(value),y2:y(value)});node("text",{x:55,y:y(value)+4,"text-anchor":"end"},value.toFixed(1));});node("text",{x:70,y:24},"Free energy / nats");node("text",{x:400,y:310,"text-anchor":"middle"},"Candidate probability q(state 0)");node("line",{x1:70,x2:720,y1:y(example.result.surprise),y2:y(example.result.surprise),"stroke-dasharray":"5 5"});node("text",{x:720,y:y(example.result.surprise)-10,"text-anchor":"end"},"Surprisal lower bound");node("path",{d:example.scan.map((p,i)=>`${i?'L':'M'}${x(p.q_state_zero)},${y(p.free_energy)}`).join(" "),fill:"none",stroke:"var(--accent)","stroke-width":2.5});node("circle",{cx:x(q),cy:y(example.result.free_energy),r:6});$("energy-curve").replaceChildren(svg);}
async function updateEnergy(){const request=++energyRequest,q=Number($("belief").value)/100;$("belief-value").textContent=q.toFixed(2);try{const example=await api(`/api/fep?q=${q}`);if(request!==energyRequest)return;drawEnergy(example,q);$("fep-metrics").replaceChildren();for(const [key,label] of [["free_energy","Free energy / nats"],["surprise","Surprisal / nats"],["kl_to_posterior","KL divergence / nats"],["evidence","Observation evidence"]]){const item=element("div");item.append(element("dt",label),element("dd",example.result[key].toFixed(4)));$("fep-metrics").append(item);}$("fep-status").textContent=`F = surprisal + KL(q ∥ posterior). Exact posterior: [${example.result.exact_posterior.map(x=>x.toFixed(2)).join(", ")}]. Identity residual: ${example.result.identity_residual.toExponential(2)}.`;}catch(error){if(request===energyRequest)$("fep-status").textContent=`Calculation failed: ${error.message}`;}}
$("belief").addEventListener("input",updateEnergy);updateEnergy();

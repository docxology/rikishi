"use strict";
function renderAnalytics(data, target) {
  const make = (tag, text, cls) => { const node = document.createElement(tag); if(text !== undefined) node.textContent = text; if(cls) node.className = cls; return node; };
  const number = n => Number(n).toLocaleString();
  const percent = n => n === null ? "undefined (no formulas)" : (100*n).toFixed(2)+"%";
  target.replaceChildren(make("h2", "Composition and connectivity"));
  target.append(make("p", `Largest file: ${percent(data.largest_file_share)} of ${number(data.formula_denominator)} formulas. Top ten files: ${percent(data.top_ten_file_share)}. File concentration HHI: ${data.file_hhi === null ? "undefined" : data.file_hhi.toFixed(4)}.`, "muted"));
  target.append(make("p", `${number(data.edge_assertions)} edge assertions; ${number(data.unique_edges)} unique labeled directed triples; ${number(data.duplicate_edge_assertions)} repeated assertions. ${number(data.zero_degree_terms)} of ${number(data.term_denominator)} indexed symbols have zero degree.`, "muted"));
  const layout=make("div", undefined, "analytics-grid");
  function table(title, headings, rows) {
    const section=make("section"), table=make("table"), caption=make("caption", title), head=make("thead"), hr=make("tr"), body=make("tbody");
    headings.forEach(text=>{const th=make("th",text);th.scope="col";hr.append(th);});head.append(hr);
    rows.forEach(row=>{const tr=make("tr");row.forEach(value=>tr.append(make("td",value)));body.append(tr);});
    table.append(caption,head,body);section.append(table);return section;
  }
  const top=data.predicates.slice(0,8), remainder=data.formula_denominator-top.reduce((n,r)=>n+r.count,0);
  const composition=top.map(r=>[r.label,number(r.count),percent(r.share)]);
  composition.push(["All remaining heads",number(remainder),percent(data.formula_denominator ? remainder/data.formula_denominator : null)]);
  layout.append(table("Formula heads (all formulas accounted for)",["Head","Formulas","Share"],composition));
  const bins=[{label:"0",lo:0,hi:0},{label:"1",lo:1,hi:1},{label:"2–4",lo:2,hi:4},{label:"5–16",lo:5,hi:16},{label:"17–64",lo:17,hi:64},{label:"65+",lo:65,hi:Infinity}];
  const degrees=make("section");degrees.append(make("h3","Degree distribution"),make("p","Symbols by in + out degree; unique labeled triples. Self-loops count twice. All indexed symbols included.","muted"));
  for(const bin of bins){const count=data.degree_distribution.filter(r=>r.degree>=bin.lo&&r.degree<=bin.hi).reduce((n,r)=>n+r.terms,0), row=make("div",undefined,"bar-row"), track=make("div",undefined,"bar-track"), fill=make("div",undefined,"bar-fill");fill.style.width=(data.term_denominator?100*count/data.term_denominator:0)+"%";track.setAttribute("aria-hidden","true");track.append(fill);row.append(make("span",bin.label),track,make("span",number(count),"bar-count"));degrees.append(row);}
  layout.append(degrees);target.append(layout,make("p",`Source ${data.source_commit}; clean: ${String(data.source_clean)}. ${data.rejected_files} rejected source files. These are syntax measurements of the indexed subset; nested assertions and inferred closure are excluded from the graph. Runtime cached formulas are a different population.`,"muted"));
}

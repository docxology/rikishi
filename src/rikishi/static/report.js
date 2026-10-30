"use strict";
const data = JSON.parse(document.getElementById("data").textContent);
const analytics = JSON.parse(document.getElementById("analytics-data").textContent);
for (const [key, label] of [["files", "Source files"], ["formulas", "KIF formulas"], ["terms", "Indexed symbols"], ["edges", "Edge assertions"]]) {
  const row = viewElement("div");
  row.append(viewElement("dt", label), viewElement("dd", viewNumber(data[key])));
  document.getElementById("metrics").append(row);
}
document.getElementById("revision").textContent = `Source revision: ${data.source_commit}; clean: ${String(data.source_clean)}. ` +
  `${data.parse_errors.length} rejected source files. Revision and cleanliness were recorded when this index was built.`;
document.getElementById("json").textContent = JSON.stringify({ corpus: data, analytics }, null, 2);
renderFileDistribution(data, document.getElementById("file-distribution"));
renderAnalytics(analytics, document.getElementById("analytics"));
setupTheme();

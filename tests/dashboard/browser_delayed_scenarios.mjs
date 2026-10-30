const checks = [];
const assert = (condition, message) => {
  if (!condition) throw new Error(message);
  checks.push(message);
};
const settled = () => page.eval(async () => {
  const deadline = Date.now() + 15000;
  while (pendingRequests || initialAnchor.state.active) {
    if (Date.now() > deadline) throw new Error("Delayed real API requests did not settle");
    await new Promise(resolve => setTimeout(resolve, 30));
  }
  await new Promise(requestAnimationFrame);
  return true;
});
for (const anchor of ["corpus", "inference"]) {
  await page.open(`http://127.0.0.1:8770/?delay-case=${anchor}-${Date.now()}#${anchor}`);
  const before = await page.eval(() => {
    const height = id => document.getElementById(id).getBoundingClientRect().height;
    return {
      pending: pendingRequests, active: initialAnchor.state.active,
      metrics: height("metrics"), canvas: height("energy-curve"),
      fep: height("fep-metrics"), table: height("corpus-table"),
      focus: document.activeElement.id || document.activeElement.tagName,
      theme: document.documentElement.dataset.theme,
      panes: Object.fromEntries(["file-distribution", "analytics", "relation-inventory", "taxonomy-workspace", "definition", "graph", "formulas"].map(id => [id, height(id)])),
    };
  });
  assert(before.pending > 0 && before.active, `${anchor}: fixture really delays requests while preserving initial anchor`);
  assert(before.theme === "light", `${anchor}: fresh delayed page remains white under dark OS preference`);
  assert(before.metrics >= 122 && before.canvas >= 200 && before.table === 560, `${anchor}: real loading DOM reserves metrics, FEP canvas, and table geometry`);
  await settled();
  const final = await page.eval(`() => {
    const height = id => document.getElementById(id).getBoundingClientRect().height;
    const target = document.getElementById(${JSON.stringify(anchor)}).getBoundingClientRect();
    const bottom = document.querySelector("header").getBoundingClientRect().bottom;
    return {metrics:height("metrics"),canvas:height("energy-curve"),fep:height("fep-metrics"),table:height("corpus-table"),
      visible:target.top >= bottom && target.top < innerHeight,
      focus:document.activeElement.id || document.activeElement.tagName,
      panes:Object.fromEntries(["file-distribution","analytics","relation-inventory","taxonomy-workspace","definition","graph","formulas"].map(id=>[id,height(id)])),
      delay:performance.getEntriesByType("resource").filter(row=>row.name.includes("/api/")).map(row=>row.duration)};
  }`);
  assert(["metrics", "canvas", "fep", "table"].every(key => Math.abs(before[key] - final[key]) < 1), `${anchor}: reserved data geometry stays unchanged after actual HTTP fills`);
  assert(Object.keys(before.panes).every(key => Math.abs(before.panes[key] - final.panes[key]) < 1), `${anchor}: every asynchronous ancestor pane keeps its actual geometry`);
  assert(final.visible, `${anchor}: initial hash destination stays below sticky navigation after delayed ancestor fills`);
  assert(final.focus === before.focus, `${anchor}: loading never moves keyboard focus`);
  assert(final.delay.some(value => value >= 1900), `${anchor}: browser records actual server delay`);
}
for (const gesture of ["key", "pointer", "scroll"]) {
  await page.open(`http://127.0.0.1:8770/?delay-gesture=${gesture}-${Date.now()}#inference`);
  const active = await page.eval(() => initialAnchor.state.active && pendingRequests > 0);
  assert(active, `${gesture}: preservation is active before real interaction`);
  if (gesture === "key") await page.press("Tab");
  if (gesture === "pointer") await page.click("#theme");
  if (gesture === "scroll") await page.press("PageDown");
  await page.eval(async () => { await new Promise(requestAnimationFrame); await new Promise(requestAnimationFrame); });
  const stopped = await page.eval(() => ({active:initialAnchor.state.active,reason:initialAnchor.state.reason,focus:document.activeElement.id || document.activeElement.tagName}));
  assert(!stopped.active && stopped.reason.startsWith("user"), `${gesture}: initial anchor preservation stops immediately on interaction`);
  await settled();
  const final = await page.eval(() => ({active:initialAnchor.state.active,focus:document.activeElement.id || document.activeElement.tagName}));
  assert(!final.active && final.focus === stopped.focus, `${gesture}: later HTTP fills never restart preservation or steal focus`);
}
console.log(JSON.stringify({checks}));

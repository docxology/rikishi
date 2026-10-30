const checks = [];
const assert = (condition, message) => {
  if (!condition) throw new Error(message);
  checks.push(message);
};
const url = await page.eval(() => location.href);
assert(url.startsWith("file:"), "Offline anchor regression uses a real standalone file");
await page.open(`${url.split(/[?#]/)[0]}?offline-anchor-check=${Date.now()}`);
await page.eval(() => window.scrollTo(0, 0));
await page.press("Tab");
assert(await page.eval(() => document.activeElement.matches(".skip")), "Native Tab reaches the report skip link first");
await page.press("Enter");
const geometry = await page.eval(async () => {
  await new Promise(requestAnimationFrame);
  const section = document.getElementById("corpus");
  const heading = section.querySelector("h2").getBoundingClientRect();
  return {
    width: innerWidth,
    headerBottom: document.querySelector("header").getBoundingClientRect().bottom,
    sectionTop: section.getBoundingClientRect().top,
    headingTop: heading.top,
    headingBottom: heading.bottom,
    viewportHeight: innerHeight,
    focus: document.activeElement.id,
    hash: location.hash,
  };
});
console.log(JSON.stringify({ geometry }));
assert(geometry.sectionTop >= geometry.headerBottom, "Native skip target clears the actual sticky header");
assert(geometry.headingTop >= geometry.headerBottom && geometry.headingBottom < geometry.viewportHeight, "Source heading is fully visible after native skip activation");
assert(geometry.focus === "corpus" && geometry.hash === "#corpus", "Native skip activation hands focus to its report section");
assert(await page.eval(() => performance.getEntriesByType("resource").every(row => !/^https?:/.test(row.name))), "Native offline skip requests no HTTP resources");
console.log(JSON.stringify({ checks }));

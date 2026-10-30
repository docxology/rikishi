async () => {
  const checks = [];
  const assert = (condition, message) => {
    if (!condition) throw new Error(message);
    checks.push(message);
  };
  const id = value => document.getElementById(value);
  const wait = async predicate => {
    const deadline = Date.now() + 10000;
    while (!predicate()) {
      if (Date.now() > deadline) throw new Error("Real fixture surface did not settle");
      await new Promise(resolve => setTimeout(resolve, 30));
    }
  };
  const stats = await (await fetch("/api/stats")).json();
  await wait(() => id("corpus-table").getAttribute("aria-busy") === "false" && id("relation-inventory").getAttribute("aria-busy") === "false");
  assert(document.documentElement.dataset.theme === "light", "Real fixture starts in explicit light mode");
  if (!stats.formulas) {
    await wait(() => id("search-status").textContent.includes("No matches"));
    assert(id("corpus-table").textContent.includes("No indexed rows"), "Empty corpus shows explicit evidence state");
    assert(!id("graph-status").textContent.includes("Loading"), "Empty term population never leaves graph loading indefinitely");
    assert(id("term-all-formulas").disabled && id("graph-limit").disabled, "Empty term population disables term-specific controls");
    assert(id("corpus-export").disabled && id("corpus-next").disabled, "Empty corpus disables export and pagination");
    assert(id("relation-inventory").textContent.includes("No relation names match"), "Empty atomic relation population is explicit");
    await wait(() => id("taxonomy-status").textContent.includes("endpoint symbols"));
    assert(id("taxonomy-status").textContent.startsWith("0 endpoint symbols"), "Empty taxonomy preserves a zero endpoint denominator");
  } else {
    const expected = await (await fetch("/api/corpus/formulas?head=%3Cscript%3E")).json();
    assert(expected.returned === 1, "Hostile fixture is really indexed and queryable");
    openCorpusEvidence({ head: "<script>" });
    await wait(() => id("corpus-table").getAttribute("aria-busy") === "false");
    assert(id("corpus-table").textContent.includes("<script>"), "Hostile formula head remains literal DOM text");
    document.querySelector("#corpus-table tbody .table-action").click();
    assert(id("inspector-content").querySelector("pre").textContent === expected.items[0].text, "Hostile formula inspector preserves actual source bytes as text");
    assert(!id("inspector-content").querySelector("a"), "Unversioned fixture never invents a pinned upstream source link");
    assert(!document.querySelector("#corpus-table script, #corpus-table img, #inspector-content script, #inspector-content img, #file-distribution img"), "Hostile indexed markup never becomes an executable element");
    const taxonomy = await (await fetch("/api/taxonomy")).json();
    assert(taxonomy.cyclic_component_count === 1 && taxonomy.self_loop_count === 1, "Real cyclic and self-loop fixture diagnostics remain visible");
    openCorpusEvidence({ path: "literal%_<img>.kif" });
    await wait(() => id("corpus-table").getAttribute("aria-busy") === "false");
    assert(id("corpus-status").textContent.includes("9 of 9 formulas"), "Hostile exact filename filter retains every indexed formula");
  }
  assert(!/NaN|Infinity/.test(id("analytics").textContent), "Empty and hostile measurements have no nonfinite UI labels");
  assert(document.documentElement.scrollWidth <= innerWidth, "Fixture viewport has no horizontal page overflow");
  return { fixture: stats.formulas ? "hostile" : "empty", width: innerWidth, checks };
}

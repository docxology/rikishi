async () => {
async function measureEnergyChart() {
  await document.fonts.ready;
  const canvas = document.getElementById("energy-curve");
  const svg = canvas.querySelector("svg");
  if (!svg) throw new Error("Finite-model SVG has not loaded");
  const box = item => item.getBoundingClientRect().toJSON();
  const labels = [...svg.querySelectorAll("text")].map(item => {
    const matrix = item.getScreenCTM();
    const style = getComputedStyle(item);
    return {
      text: item.textContent, box: box(item),
      font: parseFloat(style.fontSize) * Math.hypot(matrix.c, matrix.d),
      visible: style.display !== "none" && style.visibility === "visible" && Number(style.opacity) > 0,
    };
  });
  const q = Number(document.getElementById("belief").value) / 100;
  const response = await fetch(`/api/fep?q=${q}`);
  if (!response.ok) throw new Error(`Finite-model API returned ${response.status}`);
  const example = await response.json();
  const coordinate = (item, name) => Number(item.getAttribute(name));
  const luminance = color => {
    const components = color.match(/[\d.]+/g).map(Number);
    if (components.length < 3 || (components[3] ?? 1) !== 1) throw new Error(`Expected opaque computed chart color: ${color}`);
    return components.slice(0,3).map(value => value / 255).map(value => value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4)
      .reduce((sum, value, index) => sum + value * [0.2126, 0.7152, 0.0722][index], 0);
  };
  const boundStroke = getComputedStyle(svg.querySelector("line[stroke-dasharray]")).stroke;
  const background = getComputedStyle(canvas).backgroundColor;
  const strokeLuminance = luminance(boundStroke), backgroundLuminance = luminance(background);
  return {
    width: innerWidth, height: innerHeight, scale: visualViewport.scale,
    theme: document.documentElement.dataset.theme,
    pageOverflow: document.documentElement.scrollWidth > innerWidth,
    canvas: box(canvas), svg: box(svg), labels, q, example,
    matrix: [svg.getScreenCTM().a, svg.getScreenCTM().b, svg.getScreenCTM().c, svg.getScreenCTM().d, svg.getScreenCTM().e, svg.getScreenCTM().f],
    aria: svg.getAttribute("aria-label"),
    curve: svg.querySelector("path").getAttribute("d"),
    marker: Object.fromEntries(["cx", "cy", "r"].map(name => [name, coordinate(svg.querySelector("circle"), name)])),
    bound: Object.fromEntries(["x1", "x2", "y1", "y2"].map(name => [name, coordinate(svg.querySelector("line[stroke-dasharray]"), name)])),
    boundContrast: {stroke:boundStroke, background, ratio:(Math.max(strokeLuminance,backgroundLuminance)+0.05)/(Math.min(strokeLuminance,backgroundLuminance)+0.05)},
    viewBox: [svg.viewBox.baseVal.width, svg.viewBox.baseVal.height],
    yTicks: [...svg.querySelectorAll("line:not([stroke-dasharray])")].map(line => coordinate(line, "y1")),
  };
}

function assertEnergyChart(value) {
  const check = (condition, message) => { if (!condition) throw new Error(message); };
  const near = (a, b) => Math.abs(a - b) < 0.01;
  const within = (inner, outer) => inner.left >= outer.left - 0.01 && inner.right <= outer.right + 0.01
    && inner.top >= outer.top - 0.01 && inner.bottom <= outer.bottom + 0.01;
  check(value.scale === 1, "Chart must be measured at normal viewport scale");
  check(!value.pageOverflow, "Chart page must not overflow horizontally");
  check(value.labels.length === 9, "Every tick, axis and lower-bound annotation must remain visible");
  for (const label of value.labels) {
    check(label.font >= 12 - 0.000001, `Unreadable chart label: ${label.text} is ${label.font} CSS px`);
    check(label.visible && label.box.width > 0 && label.box.height > 0, `Hidden chart label: ${label.text}`);
    check(within(label.box, value.svg) && within(label.box, value.canvas), `Clipped chart label: ${label.text}`);
  }
  check(value.boundContrast.ratio >= 3, `Surprisal bound contrast is ${value.boundContrast.ratio}:1; minimum is 3:1`);
  for (let i = 0; i < value.labels.length; i++) {
    for (const other of value.labels.slice(i + 1)) {
      const first = value.labels[i];
      check(Math.min(first.box.right, other.box.right) <= Math.max(first.box.left, other.box.left)
        || Math.min(first.box.bottom, other.box.bottom) <= Math.max(first.box.top, other.box.top),
      `Overlapping chart labels: ${first.text} and ${other.text}`);
    }
  }
  const points = [...value.curve.matchAll(/[ML]([^, ]+),([^ ]+)/g)].map(match => [Number(match[1]), Number(match[2])]);
  check(points.length === value.example.scan.length, "Curve must retain every API scan point");
  const [first, last] = [points[0], points.at(-1)];
  const [a, b, c, d, e, f] = value.matrix;
  for (const [px, py] of points) {
    const screenX = a * px + c * py + e, screenY = b * px + d * py + f;
    check(value.labels.every(label => screenX < label.box.left || screenX > label.box.right
      || screenY < label.box.top || screenY > label.box.bottom), "Curve must not run through a chart label");
  }
  const y = energy => value.yTicks[0] + energy * (value.yTicks[1] - value.yTicks[0]);
  const x = q => first[0] + q * (last[0] - first[0]);
  value.example.scan.forEach((point, i) => {
    check(near(points[i][0], x(point.q_state_zero)) && near(points[i][1], y(point.free_energy)), "Curve must match numerical API data");
    check(points[i][0] >= 0 && points[i][0] <= value.viewBox[0] && points[i][1] >= 0 && points[i][1] <= value.viewBox[1], "Curve point is outside SVG");
  });
  check(near(value.marker.cx, x(value.q)) && near(value.marker.cy, y(value.example.result.free_energy)), "Selected marker must match actual q and free energy");
  check(value.marker.cx - value.marker.r >= 0 && value.marker.cx + value.marker.r <= value.viewBox[0]
    && value.marker.cy - value.marker.r >= 0 && value.marker.cy + value.marker.r <= value.viewBox[1], "Selected marker is clipped");
  check(near(value.bound.x1, first[0]) && near(value.bound.x2, last[0]) && near(value.bound.y1, y(value.example.result.surprise))
    && near(value.bound.y1, value.bound.y2), "Surprisal bound must span the full plot at the API value");
  check(value.aria.includes(`Minimum at ${value.example.result.exact_posterior[0]}.`), "Accessible minimum must use the exact posterior");
  check(value.aria.includes(`Selected q ${value.q}, free energy ${value.example.result.free_energy.toFixed(4)} nats.`), "Accessible selection must use API values");
  return {labels: value.labels.length, minimumFont: Math.min(...value.labels.map(label => label.font)), scanPoints: points.length, boundContrast:value.boundContrast.ratio, q: value.q};
}

  const wait = async expected => {
    const deadline = Date.now() + 15000;
    while (!document.querySelector("#energy-curve svg") || pendingRequests || initialAnchor.state.active
      || (expected !== null && !document.querySelector("#energy-curve svg").getAttribute("aria-label").includes(`Selected q ${expected},`))) {
      if (Date.now() > deadline) throw new Error("Real finite-model request did not settle");
      await new Promise(resolve => setTimeout(resolve, 30));
    }
    await new Promise(requestAnimationFrame);
    await new Promise(requestAnimationFrame);
  };
  globalThis.energyChartProbe = {measure: measureEnergyChart, assert: assertEnergyChart};
  await wait(null);
  const initial = await measureEnergyChart();
  const checks = [assertEnergyChart(initial)];
  const slider = document.getElementById("belief");
  slider.focus();
  for (const q of [0, 0.8, 1]) {
    slider.value = String(q * 100);
    slider.dispatchEvent(new Event("input", {bubbles: true}));
    await wait(q);
    const current = await measureEnergyChart();
    checks.push(assertEnergyChart(current));
    if (Math.abs(current.canvas.height - initial.canvas.height) > 0.01 || Math.abs(current.canvas.width - initial.canvas.width) > 0.01) {
      throw new Error("Real slider input changed reserved canvas geometry");
    }
    if (document.activeElement.id !== "belief") throw new Error("Slider input lost keyboard focus");
  }
  slider.value = String(initial.q * 100);
  slider.dispatchEvent(new Event("input", {bubbles: true}));
  await wait(initial.q);
  return {caseId: "F1-energy-chart", initial, checks};
}

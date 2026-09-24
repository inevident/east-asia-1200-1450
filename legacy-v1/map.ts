import { geoConicEqualArea, geoGraticule10, geoPath, type GeoProjection } from "d3-geo";
import { feature } from "topojson-client";
import type { Topology, GeometryCollection } from "topojson-specification";

/* ==========================================================================
   "East Asia in the Afro-Eurasian web" — routes, diffusion arcs, campaigns.
   ========================================================================== */

type LonLat = [number, number];
interface Layer {
  id: string;
  name: string;
  color: string;
  on: boolean;
  legend: string;
}

const LAYERS: Layer[] = [
  { id: "silk", name: "Silk Roads", color: "#d9b36c", on: true, legend: "<b>Silk Roads.</b> Revived under the Pax Mongolica; silk, porcelain and paper money west, silver and cloth east." },
  { id: "sea", name: "Indian Ocean", color: "#6fa4c9", on: true, legend: "<b>Monsoon sea lanes.</b> Junks, dhows and merchant diasporas linking Quanzhou to Calicut, Hormuz, Aden and the Swahili coast." },
  { id: "zheng", name: "Zheng He, 1405–33", color: "#f0d06b", on: true, legend: "<b>Zheng He.</b> Seven Ming treasure-fleet voyages carried the tributary system as far as East Africa." },
  { id: "canal", name: "Grand Canal", color: "#8fd1b8", on: true, legend: "<b>Grand Canal.</b> Southern rice to the northern capital; extended to Dadu (Beijing) under the Yuan." },
  { id: "diff", name: "Diffusion", color: "#e8836b", on: true, legend: "<b>Diffusion.</b> Crops, faiths, minerals, science, money and technology crossing the region’s borders." },
  { id: "war", name: "Mongol campaigns", color: "#c9453a", on: false, legend: "<b>Mongol campaigns.</b> Failed invasions of Japan (1274, 1281) and Đại Việt (defeated at Bạch Đằng, 1288)." },
];

const CITIES: { name: string; at: LonLat; major?: boolean; dx?: number; dy?: number; anchor?: string }[] = [
  { name: "Hangzhou", at: [120.16, 30.27], major: true, dx: 8, dy: 12 },
  { name: "Quanzhou (Zayton)", at: [118.59, 24.91], major: true, dx: 8, dy: 4 },
  { name: "Dadu (Beijing)", at: [116.4, 39.9], major: true, dx: 8, dy: -6 },
  { name: "Kaifeng", at: [114.31, 34.8], dx: -8, dy: 12, anchor: "end" },
  { name: "Jingdezhen", at: [117.2, 29.3], dx: -8, dy: 3, anchor: "end" },
  { name: "Kyoto", at: [135.77, 35.01], major: true, dx: 8, dy: 10 },
  { name: "Kamakura", at: [139.55, 35.32], dx: 6, dy: -8 },
  { name: "Kaesong", at: [126.55, 37.97], dx: 8, dy: -4 },
  { name: "Thăng Long", at: [105.85, 21.03], dx: -8, dy: -4, anchor: "end" },
  { name: "Champa", at: [109.2, 13.8], dx: 8, dy: 4 },
  { name: "Malacca", at: [102.25, 2.19], dx: -8, dy: 4, anchor: "end" },
  { name: "Calicut", at: [75.78, 11.25], major: true, dx: -8, dy: 4, anchor: "end" },
  { name: "Hormuz", at: [56.46, 27.1], dx: -8, dy: 12, anchor: "end" },
  { name: "Aden", at: [45.03, 12.78], dx: -8, dy: 4, anchor: "end" },
  { name: "Malindi", at: [40.12, -3.22], dx: -8, dy: 4, anchor: "end" },
  { name: "Tabriz", at: [46.29, 38.08], dx: -8, dy: -6, anchor: "end" },
  { name: "Maragheh", at: [46.24, 37.39], dx: 8, dy: 10 },
  { name: "Samarkand", at: [66.96, 39.65], dx: 0, dy: -10, anchor: "middle" },
  { name: "Kashgar", at: [75.99, 39.47], dx: 6, dy: 12 },
  { name: "Karakorum", at: [102.83, 47.2], dx: 0, dy: -10, anchor: "middle" },
  { name: "Baghdad", at: [44.36, 33.31], dx: -8, dy: 10, anchor: "end" },
  { name: "Cairo", at: [31.24, 30.04], dx: -8, dy: 4, anchor: "end" },
  { name: "Venice", at: [12.33, 45.44], major: true, dx: -8, dy: -4, anchor: "end" },
];

interface Route {
  layer: string;
  title: string;
  text: string;
  cats: string;
  pts: LonLat[];
  width?: number;
  dash?: string;
}

const ROUTES: Route[] = [
  {
    layer: "silk",
    title: "The overland Silk Roads",
    text: "Revived under Mongol rule. Caravans carried silk, porcelain and ideas west; Marco Polo and papal envoys came east.",
    cats: "E · I · R",
    pts: [[116.4, 39.9], [108.94, 34.34], [103.83, 36.06], [94.66, 40.14], [89.19, 42.95], [75.99, 39.47], [66.96, 39.65], [64.42, 39.77], [61.84, 37.66], [58.8, 36.2], [51.4, 35.7], [46.29, 38.08], [39.72, 41.0], [28.97, 41.01], [23.7, 37.9], [19.4, 40.1], [12.33, 45.44]],
    width: 2.4,
  },
  {
    layer: "silk",
    title: "Steppe road to Karakorum",
    text: "The Mongol heartland: envoys, merchants and captured artisans travelled to the khans’ court.",
    cats: "P · E",
    pts: [[116.4, 39.9], [111.7, 40.8], [106.9, 44.5], [102.83, 47.2], [93.0, 46.8], [84.0, 44.3], [76.0, 43.2], [66.96, 39.65]],
    width: 1.6,
    dash: "5 5",
  },
  {
    layer: "sea",
    title: "Monsoon sea lanes of the Indian Ocean",
    text: "Seasonal winds carried junks, dhows and Indian ships between Quanzhou, Malacca, Calicut, Hormuz, Aden and the Swahili coast.",
    cats: "T · E · R",
    pts: [[118.59, 24.91], [116.5, 22.3], [111.5, 18.0], [109.2, 13.0], [106.5, 8.0], [104.0, 2.5], [101.5, 2.3], [98.0, 5.2], [95.0, 6.0], [88.0, 6.0], [81.2, 5.8], [77.5, 8.0], [75.78, 11.25], [70.0, 17.0], [62.0, 23.0], [56.46, 27.1]],
    width: 2.4,
  },
  {
    layer: "sea",
    title: "To Arabia, Egypt and East Africa",
    text: "From India’s Malabar coast, ships crossed to Aden and on to the Red Sea or down to the Swahili city-states.",
    cats: "E · R",
    pts: [[75.78, 11.25], [65.0, 12.5], [52.0, 12.8], [45.03, 12.78], [42.8, 13.8], [39.0, 20.5], [35.8, 25.8], [33.9, 28.2], [32.55, 29.97], [31.24, 30.04]],
    width: 1.8,
  },
  {
    layer: "sea",
    title: "Swahili coast",
    text: "Gold and ivory from East Africa met Chinese porcelain and Indian cloth.",
    cats: "E",
    pts: [[45.03, 12.78], [51.0, 10.5], [48.0, 5.0], [45.34, 2.05], [42.5, -0.5], [40.12, -3.22]],
    width: 1.6,
  },
  {
    layer: "zheng",
    title: "Zheng He’s voyages, 1405–1433",
    text: "Seven Ming expeditions (the first with 317 ships and nearly 28,000 men) sailed as far as the east coast of Africa to enrol rulers in the tributary system.",
    cats: "P · T",
    pts: [[118.8, 32.06], [121.5, 30.0], [119.8, 25.9], [115.0, 21.0], [110.8, 15.5], [109.2, 11.5], [106.5, 5.0], [106.8, -4.0], [112.75, -6.9], [108.0, -5.8], [104.75, -2.99], [102.25, 2.19], [97.1, 5.2], [88.5, 5.5], [80.2, 6.0], [75.78, 11.25], [66.0, 18.0], [58.0, 24.5], [56.46, 27.1], [59.0, 21.0], [54.0, 13.5], [49.0, 10.0], [45.34, 2.05], [40.12, -3.22]],
    width: 2.2,
    dash: "2 7",
  },
  {
    layer: "canal",
    title: "The Grand Canal",
    text: "China’s great inland waterway carried southern rice to the political north; the Yuan extended it to their capital at Dadu (Beijing).",
    cats: "E · T",
    pts: [[120.16, 30.27], [120.6, 31.3], [119.43, 32.39], [119.0, 33.6], [117.9, 34.3], [116.6, 35.4], [115.7, 36.8], [116.3, 37.45], [117.2, 39.1], [116.4, 39.9]],
    width: 3,
  },
];

interface Arc {
  layer: string;
  from: LonLat;
  to: LonLat;
  label: string;
  title: string;
  text: string;
  cats: string;
  bend?: number;
  labelAt?: number;
}

const ARCS: Arc[] = [
  { layer: "diff", from: [109.2, 13.8], to: [119.3, 27.5], label: "Champa rice", title: "Champa rice, by 1012", text: "Fast-ripening, drought-resistant rice from Champa (Vietnam) spread across the Yangzi and Huai regions, fuelling population growth.", cats: "T · S", bend: -0.25 },
  { layer: "diff", from: [84.99, 24.69], to: [112.45, 34.62], label: "Buddhism", title: "Buddhism enters East Asia", text: "An Indian religion carried over the Silk Roads; in China it became Chan and Pure Land Buddhism.", cats: "R", bend: -0.35 },
  { layer: "diff", from: [120.3, 30.8], to: [135.4, 34.8], label: "Chan → Zen", title: "Chan becomes Zen", text: "Meditation Buddhism spread from China to Japan, where it was embraced by the samurai.", cats: "R · A", bend: -0.3 },
  { layer: "diff", from: [116.6, 40.3], to: [126.9, 37.5], label: "Neo-Confucianism", title: "Neo-Confucianism to Korea", text: "Zhu Xi’s Confucianism became the ruling ideology of Joseon Korea after 1392.", cats: "I · S", bend: -0.35, labelAt: 0.4 },
  { layer: "diff", from: [51.45, 33.98], to: [117.2, 29.3], label: "Persian cobalt", title: "Persian cobalt → Jingdezhen", text: "Cobalt from Persia gave Yuan blue-and-white porcelain its blue; the finished wares sailed back to Islamic markets.", cats: "A · E", bend: 0.18, labelAt: 0.55 },
  { layer: "diff", from: [46.24, 37.39], to: [116.4, 39.9], label: "Astronomy", title: "Maragheh → Beijing", text: "Khubilai invited the Persian astronomer Jamal al-Din; with Guo Shoujing he helped produce a more accurate calendar.", cats: "I · T", bend: -0.22, labelAt: 0.45 },
  { layer: "diff", from: [116.4, 39.9], to: [46.29, 38.08], label: "Paper money, 1294", title: "Paper money to Tabriz, 1294", text: "The Ilkhanate copied Yuan paper notes, but distrustful merchants refused them and the experiment collapsed.", cats: "E", bend: -0.12, labelAt: 0.62 },
  { layer: "diff", from: [114.3, 34.8], to: [14.0, 46.5], label: "Gunpowder · paper · compass", title: "Chinese technology travels west", text: "Gunpowder weapons, paper and the magnetic compass diffused across Eurasia to the Islamic world and Europe.", cats: "T · I", bend: -0.28, labelAt: 0.5 },
  { layer: "diff", from: [77.3, 42.4], to: [34.5, 45.0], label: "Plague, 1300s", title: "Plague along the trade routes", text: "Pathogens moved with trade; plague, war and famine helped end Yuan rule in 1368.", cats: "S · E", bend: 0.2, labelAt: 0.5 },
  { layer: "war", from: [128.9, 35.1], to: [130.4, 33.6], label: "1274 · 1281", title: "Mongol invasions of Japan", text: "Fleets sailed from Korea twice; samurai resistance (and storms) defeated both.", cats: "P", bend: -0.4 },
  { layer: "war", from: [108.3, 22.8], to: [106.7, 20.9], label: "Bạch Đằng 1288", title: "Đại Việt defeats the Mongols", text: "Iron-tipped stakes in the Bạch Đằng River wrecked a Yuan fleet at low tide.", cats: "P", bend: 0.5 },
];

export async function mountMap() {
  const svg = document.getElementById("map") as unknown as SVGSVGElement;
  const tip = document.getElementById("map-tip") as HTMLElement;
  const controls = document.getElementById("map-controls") as HTMLElement;
  const legend = document.getElementById("map-legend") as HTMLElement;
  if (!svg) return;
  const W = 1600,
    H = 940;
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);

  const topo = (await import("world-atlas/land-50m.json")).default as unknown as Topology<{ land: GeometryCollection }>;
  const land = feature(topo, topo.objects.land);

  const projection: GeoProjection = geoConicEqualArea().parallels([12, 44]).rotate([-78, 0]);
  const extent = {
    type: "Feature",
    properties: {},
    geometry: { type: "MultiPoint", coordinates: [[8, -9], [146, -9], [146, 52], [8, 52], [78, 56], [78, -12]] },
  } as GeoJSON.Feature;
  projection.fitExtent([[20, 20], [W - 20, H - 20]], extent);
  const path = geoPath(projection);
  const P = (ll: LonLat) => projection(ll) as [number, number];

  const NS = "http://www.w3.org/2000/svg";
  const el = (tag: string, attrs: Record<string, string | number>, parent: Element) => {
    const n = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, String(v));
    parent.appendChild(n);
    return n;
  };

  const defs = el("defs", {}, svg);
  for (const L of LAYERS) {
    const m = el("marker", { id: `arrow-${L.id}`, viewBox: "0 0 10 10", refX: 8, refY: 5, markerWidth: 7, markerHeight: 7, orient: "auto-start-reverse" }, defs);
    el("path", { d: "M 0 0 L 10 5 L 0 10 z", fill: L.color }, m);
  }
  el("path", { d: path(geoGraticule10()) ?? "", class: "graticule" }, svg);
  el("path", { d: path(land) ?? "", class: "land" }, svg);

  const groups: Record<string, SVGGElement> = {};
  for (const L of LAYERS) groups[L.id] = el("g", { class: "layer", "data-layer": L.id, "data-off": String(!L.on) }, svg) as SVGGElement;

  const showTip = (e: PointerEvent, title: string, text: string, cats: string) => {
    tip.innerHTML = `<b>${title}</b>${text}<span class="cats">PIRATES · ${cats}</span>`;
    tip.hidden = false;
    const r = svg.getBoundingClientRect();
    const x = e.clientX - r.left;
    const y = e.clientY - r.top;
    const tw = tip.offsetWidth;
    tip.style.left = `${Math.min(Math.max(8, x + 14), r.width - tw - 8)}px`;
    tip.style.top = `${Math.max(8, y - tip.offsetHeight - 12)}px`;
  };
  const hideTip = () => (tip.hidden = true);

  const drawn: { p: SVGPathElement; len: number }[] = [];
  for (const r of ROUTES) {
    const L = LAYERS.find((l) => l.id === r.layer)!;
    const g = groups[r.layer];
    const d = path({ type: "LineString", coordinates: r.pts } as GeoJSON.LineString) ?? "";
    const p = el("path", { d, class: "route", stroke: L.color, "stroke-width": r.width ?? 2, ...(r.dash ? { "stroke-dasharray": r.dash } : {}) }, g) as SVGPathElement;
    if (!r.dash) drawn.push({ p, len: p.getTotalLength() });
    const hit = el("path", { d, class: "route-hit" }, g);
    hit.addEventListener("pointermove", (e) => showTip(e as PointerEvent, r.title, r.text, r.cats));
    hit.addEventListener("pointerleave", hideTip);
  }
  for (const a of ARCS) {
    const L = LAYERS.find((l) => l.id === a.layer)!;
    const g = groups[a.layer];
    const [x1, y1] = P(a.from);
    const [x2, y2] = P(a.to);
    const mx = (x1 + x2) / 2,
      my = (y1 + y2) / 2;
    const dx = x2 - x1,
      dy = y2 - y1;
    const bend = a.bend ?? 0.25;
    const cx = mx - dy * bend,
      cy = my + dx * bend;
    const d = `M ${x1} ${y1} Q ${cx} ${cy} ${x2} ${y2}`;
    const p = el("path", { d, class: "route", stroke: L.color, "stroke-width": 1.8, "stroke-dasharray": "1 5", "marker-end": `url(#arrow-${L.id})` }, g) as SVGPathElement;
    p.style.strokeDasharray = "5 4";
    const t = a.labelAt ?? 0.5;
    const lx = (1 - t) * (1 - t) * x1 + 2 * (1 - t) * t * cx + t * t * x2;
    const ly = (1 - t) * (1 - t) * y1 + 2 * (1 - t) * t * cy + t * t * y2;
    const label = el("text", { x: lx, y: ly - 6, class: "arc-label", fill: L.color, "text-anchor": "middle" }, g);
    label.textContent = a.label;
    const hit = el("path", { d, class: "route-hit" }, g);
    hit.addEventListener("pointermove", (e) => showTip(e as PointerEvent, a.title, a.text, a.cats));
    hit.addEventListener("pointerleave", hideTip);
  }

  const cityG = el("g", { class: "cities" }, svg);
  for (const c of CITIES) {
    const [x, y] = P(c.at);
    const g = el("g", { class: `city${c.major ? " major" : ""}`, transform: `translate(${x},${y})` }, cityG);
    el("circle", { r: c.major ? 4 : 3 }, g);
    const t = el("text", { x: c.dx ?? 7, y: c.dy ?? 4, "text-anchor": c.anchor ?? "start" }, g);
    t.textContent = c.name;
  }

  // layer toggles + legend
  controls.innerHTML = LAYERS.map(
    (L) => `<button type="button" class="map-toggle" data-layer="${L.id}" aria-pressed="${L.on}" style="--c:${L.color}"><i></i>${L.name}</button>`,
  ).join("");
  controls.querySelectorAll<HTMLButtonElement>(".map-toggle").forEach((b) =>
    b.addEventListener("click", () => {
      const on = b.getAttribute("aria-pressed") !== "true";
      b.setAttribute("aria-pressed", String(on));
      groups[b.dataset.layer!].setAttribute("data-off", String(!on));
    }),
  );
  legend.innerHTML = LAYERS.map((L) => `<li>${L.legend}</li>`).join("");

  // draw-on animation for solid routes when the map scrolls into view
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!reduced) {
    drawn.forEach(({ p, len }) => {
      p.style.strokeDasharray = `${len}`;
      p.style.strokeDashoffset = `${len}`;
    });
    const io = new IntersectionObserver(
      (es) => {
        if (!es.some((e) => e.isIntersecting)) return;
        io.disconnect();
        drawn.forEach(({ p }, i) => {
          p.style.transition = `stroke-dashoffset 2.2s cubic-bezier(.22,1,.36,1) ${i * 0.18}s`;
          p.style.strokeDashoffset = "0";
        });
      },
      { threshold: 0.3 },
    );
    io.observe(svg);
  }
}

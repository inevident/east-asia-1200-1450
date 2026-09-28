// Scroll the whole page at a steady speed in headless Chrome and check the camera for jumps.
// usage: node tools/scroll-check.mjs [--speed=30] [--size=1440x900] [--url=http://127.0.0.1:5173/]
import { spawn } from "node:child_process";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const args = process.argv.slice(2);
const opt = (k, d) => (args.find((a) => a.startsWith(`--${k}=`)) ?? `--${k}=${d}`).split("=")[1];
const [W, H] = opt("size", "1440x900").split("x").map(Number);
const SPEED = Number(opt("speed", "30")); // px per frame (30 px at 60 fps = a brisk 1800 px/s)
const BASE = opt("url", "http://127.0.0.1:5173/");
const PORT = 9300 + Math.floor(Math.random() * 500);
const chrome = spawn(
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  ["--headless=new", `--remote-debugging-port=${PORT}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), "cdp-"))}`, `--window-size=${W},${H}`,
   "--no-first-run", "--hide-scrollbars", "--ignore-gpu-blocklist", "--use-angle=metal", "--force-device-scale-factor=1", "about:blank"],
  { stdio: "ignore" },
);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let target;
for (let i = 0; i < 50 && !target; i++) {
  await sleep(200);
  try {
    target = (await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find((t) => t.type === "page");
  } catch {}
}
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((r) => (ws.onopen = r));
let id = 0;
const pending = new Map();
ws.onmessage = (m) => {
  const msg = JSON.parse(m.data);
  if (msg.id && pending.has(msg.id)) {
    pending.get(msg.id)(msg);
    pending.delete(msg.id);
  } else if (msg.method === "Runtime.exceptionThrown") console.log("[exception]", msg.params.exceptionDetails.exception?.description?.slice(0, 300));
};
const send = (method, params = {}) =>
  new Promise((r) => {
    const i = ++id;
    pending.set(i, r);
    ws.send(JSON.stringify({ id: i, method, params }));
  });
const evaluate = async (expr) => (await send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true })).result?.result?.value;
await send("Runtime.enable");
await send("Page.enable");
await send("Emulation.setDeviceMetricsOverride", { width: W, height: H, deviceScaleFactor: 1, mobile: W < 760 });
await send("Page.navigate", { url: BASE });
for (let i = 0; i < 150; i++) {
  await sleep(200);
  if (await evaluate("!!(window.director && document.body.classList.contains('map-ready'))")) break;
}
await sleep(1500);

const data = await evaluate(`(async () => {
  const d = window.director, w = window.world, L = window.lenis;
  const raf = () => new Promise((r) => requestAnimationFrame(r));
  const maxY = document.documentElement.scrollHeight - innerHeight;
  const rows = [];
  for (let y = 0; y <= maxY; y += ${SPEED}) {
    if (L) L.scrollTo(y, { immediate: true, force: true });
    scrollTo(0, y);
    await raf();
    const t = d.want, c = w.camera.position;
    rows.push([y, d.active, d.stepProgress, t.t.x, t.t.y, t.t.z, t.logd, t.pitch, t.yaw, t.ox, c.x, c.y, c.z]);
  }
  return { maxY, rows, ids: d.steps.map((s) => s.id), pins: d.pins, H: innerHeight };
})()`);
ws.close();
chrome.kill();

const { rows, ids, pins, maxY, H: vh } = data;
console.log(`page: ${(maxY / vh + 1).toFixed(0)} screens tall; ${rows.length} frames at ${SPEED} px/frame`);
// per-frame change of the camera target, in units of the viewing distance (a jump would be a spike)
const jumps = [];
let still = 0, stillFrames = 0;
for (let i = 1; i < rows.length; i++) {
  const a = rows[i - 1], b = rows[i];
  const dist = Math.exp(b[6]);
  const dpos = Math.hypot(b[3] - a[3], b[4] - a[4], b[5] - a[5]) / dist;
  const dlog = Math.abs(b[6] - a[6]);
  const dang = Math.abs(b[7] - a[7]) + Math.abs(Math.atan2(Math.sin(b[8] - a[8]), Math.cos(b[8] - a[8])));
  const dox = Math.abs(b[9] - a[9]) / 400;
  const j = dpos + dlog + dang + dox;
  jumps.push({ i, j, y: b[0], step: ids[b[1]], p: b[2], dpos, dlog, dang, dox });
  if (b[2] >= 0.999) { stillFrames++; if (j > 0.002) still++; }
}
jumps.sort((x, y) => y.j - x.j);
console.log("largest per-frame target changes (flight speed; >0.12 would look like a cut):");
for (const q of jumps.slice(0, 8)) console.log(`  ${q.j.toFixed(3)}  y=${q.y}  ${q.step} @${q.p.toFixed(2)}  pos ${q.dpos.toFixed(3)} zoom ${q.dlog.toFixed(3)} angle ${q.dang.toFixed(3)} offset ${q.dox.toFixed(3)}`);
console.log(`frames while a card is held after its animation: ${stillFrames}; of those, frames where the target still moved: ${still}`);
// per-stop check: does every flight arrive before the card is released?
console.log("stops whose camera was still far from its target at release:");
let bad = 0;
for (let i = 0; i < ids.length; i++) {
  const [pa, pb] = pins[i];
  if (pb <= pa) continue;
  const at = rows.find((r) => r[0] >= pb);
  if (!at) continue;
  const dist = Math.exp(at[6]);
  const gap = Math.hypot(at[10] - at[3], at[11] - at[4], at[12] - at[5]) / dist;
  if (gap > 1.6) { bad++; console.log(`  ${ids[i]}: camera ${gap.toFixed(1)}x the viewing distance from its target at release`); }
}
if (!bad) console.log("  (none)");
console.log(`page height: ${(maxY / vh + 1).toFixed(0)} screens`);

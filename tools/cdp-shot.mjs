// Headless Chrome screenshots of the dev site at story steps, driven over the DevTools protocol (no dependencies).
// usage: node tools/cdp-shot.mjs [--size=1440x900] [--wait=2200] step[:key][=name] ...
import { spawn } from "node:child_process";
import { mkdtempSync, writeFileSync, mkdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const args = process.argv.slice(2);
const opt = (k, d) => {
  const a = args.find((x) => x.startsWith(`--${k}=`)) ?? `--${k}=${d}`;
  return a.slice(a.indexOf("=") + 1);
};
const [W, H] = opt("size", "1440x900").split("x").map(Number);
const WAIT = Number(opt("wait", "2200"));
const BASE = opt("url", "http://127.0.0.1:5173/");
const shots = args.filter((a) => !a.startsWith("--"));
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
  } else if (msg.method === "Runtime.consoleAPICalled" && ["error", "warning"].includes(msg.params.type)) {
    console.log(`[console.${msg.params.type}]`, msg.params.args.map((a) => a.value ?? a.description).join(" ").slice(0, 300));
  } else if (msg.method === "Runtime.exceptionThrown") {
    console.log("[exception]", msg.params.exceptionDetails.exception?.description?.slice(0, 400));
  }
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
  if (await evaluate("document.body.classList.contains('map-ready') && !!(window.__goto || !location.port)")) break;
}
await sleep(1500);
mkdirSync(".snaps", { recursive: true });
for (const s of shots) {
  const eq = s.lastIndexOf("=");
  const spec = eq >= 0 ? s.slice(0, eq) : s;
  const name = eq >= 0 ? s.slice(eq + 1) : undefined;
  const [step, key = "0"] = spec.split(/:(?=-?[\d.]+$)/);
  // "@selector" clicks an element (a rail link, say) and waits for the page's own smooth scroll to finish
  if (step.startsWith("@")) {
    await evaluate(`document.querySelector(${JSON.stringify(step.slice(1))}).click()`);
    await sleep(5500);
  }
  const ok = step.startsWith("@") ? true : step.startsWith("#")
    ? await evaluate(`(() => { const el = document.querySelector(${JSON.stringify(step)}); if (!el) return false; window.scrollTo(0, el.getBoundingClientRect().top + scrollY + ${Number(key)}); return true; })()`)
    : await evaluate(`window.__goto(${JSON.stringify(step)}, ${Number(key)})`);
  if (!ok) {
    console.log(`no such stop: ${spec}`);
    continue;
  }
  await sleep(WAIT);
  if (args.includes("--fps")) {
    // frames the map actually draws per second once the view has settled (not the browser's refresh rate)
    const fps = await evaluate(`new Promise((res) => { const w = window.world; const n0 = w.drawn; const t0 = performance.now(); setTimeout(() => res(Math.round((w.drawn - n0) / ((performance.now() - t0) / 1000))), 3000); })`);
    console.log(`${spec}: map draws ~${fps} frames/s while idle`);
  }
  if (args.includes("--probe")) {
    const info = await evaluate(`(() => { const d = window.director; return JSON.stringify({ active: d.steps[d.active].id, progress: +d.stepProgress.toFixed(2), y: scrollY, labels: [...document.querySelectorAll('.lbl.is-on:not(.is-off)')].map((e) => e.textContent.trim().slice(0, 18)) }); })()`);
    console.log(`${spec}: ${info}`);
  }
  const ev = opt("eval", "");
  if (ev) console.log(`${spec} eval:`, JSON.stringify(await evaluate(ev)));
  const shot = await send("Page.captureScreenshot", { format: "png" });
  const file = `.snaps/${name ?? `${step}-${key}`}.png`;
  writeFileSync(file, Buffer.from(shot.result.data, "base64"));
  console.log(file);
}
ws.close();
chrome.kill();

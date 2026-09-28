import "./style.css";
import Lenis from "lenis";
import { renderSite, noteHtml } from "./story/panels";
import { STEPS, type Step } from "./story/steps";
import { createWorld, startLoop } from "./world/world";
import { makeProjector } from "./world/geo";
import { Director } from "./story/director";
import { Movers } from "./world/movers";
import { loadLandmarks } from "./world/landmarks";

document.documentElement.classList.add("js");
const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;

renderSite();

/* ---------------------------------------------------------------- smooth scroll */
let lenis: Lenis | null = null;
if (!reduced) {
  lenis = new Lenis({ lerp: 0.085, smoothWheel: true, wheelMultiplier: 0.9, autoRaf: true });
}

/** Set once the map is up: where to land so a stop shows its finished animation with its card locked in view. */
let landingFor: ((id: string) => number | null) | null = null;

function scrollToHash(hash: string) {
  const target = document.querySelector(hash) as HTMLElement | null;
  if (!target) return;
  const r = target.getBoundingClientRect();
  const land = target.classList.contains("step") && landingFor ? landingFor(target.id) : null;
  const y = land ?? scrollY + r.top;
  const dist = Math.abs(y - scrollY);
  if (lenis) lenis.scrollTo(y, { duration: Math.min(1.2 + dist / 9000, 4.5) });
  else scrollTo({ top: y, behavior: reduced ? "auto" : "smooth" });
  history.replaceState(null, "", hash);
}

document.addEventListener("click", (e) => {
  const a = (e.target as Element).closest("a[href^='#']") as HTMLAnchorElement | null;
  if (!a || a.getAttribute("href") === "#") return;
  if (a.closest(".fn") && matchMedia("(hover: none)").matches) return; // touch: first tap shows the popover
  e.preventDefault();
  scrollToHash(a.getAttribute("href")!);
});

/* ---------------------------------------------------------------- progress bar + rail */
const bar = document.querySelector(".progress span") as HTMLElement;
const rail = document.querySelector(".rail") as HTMLElement;
const links = [...document.querySelectorAll<HTMLAnchorElement>(".rail-link")];
const root = document.documentElement;
let mapWorld: Awaited<ReturnType<typeof createWorld>> | null = null;
const onScroll = () => {
  const max = root.scrollHeight - innerHeight;
  bar.style.transform = `scaleX(${max > 0 ? scrollY / max : 0})`;
  rail.classList.toggle("is-visible", scrollY > innerHeight * 0.6);
  // the opening painting dissolves into the live map as the reader starts scrolling
  const t = Math.min(Math.max((scrollY - innerHeight * 0.12) / (innerHeight * 0.75), 0), 1);
  const heroO = 1 - t * t * (3 - 2 * t);
  root.style.setProperty("--hero-o", String(heroO));
  if (mapWorld) {
    mapWorld.covered = heroO > 0.985;
    mapWorld.busy = true; // wake the map at once; it idles again when the view settles
  }
};
addEventListener("scroll", onScroll, { passive: true });
onScroll();

function markStep(i: number, s: Step) {
  const letter = s.chapter !== undefined ? "PIRATES"[s.chapter] : "";
  links.forEach((l) => l.classList.toggle("is-active", l.dataset.letter === letter));
  document.querySelectorAll(".step.is-active").forEach((el) => el.classList.remove("is-active"));
  document.getElementById(s.id)?.classList.add("is-active");
  document.body.dataset.step = s.kind;
  void i;
}

/* ---------------------------------------------------------------- footnote popovers */
const pop = document.getElementById("fn-pop") as HTMLElement;
let popFor: HTMLElement | null = null;
function showNote(a: HTMLAnchorElement) {
  const n = Number(a.dataset.fn);
  pop.innerHTML = `<b>${n}</b>${noteHtml(n)}${matchMedia("(hover: none)").matches ? ` <a href="#fn-${n}" class="fn-go">Go to note ↓</a>` : ""}`;
  pop.hidden = false;
  const r = a.getBoundingClientRect();
  const pw = pop.offsetWidth;
  const ph = pop.offsetHeight;
  let x = r.left + r.width / 2 - pw / 2;
  x = Math.max(12, Math.min(x, innerWidth - pw - 12));
  let y = r.top - ph - 10;
  if (y < 12) y = r.bottom + 10;
  pop.style.left = `${x}px`;
  pop.style.top = `${y}px`;
  popFor = a;
}
function hideNote() {
  pop.hidden = true;
  popFor = null;
}
document.addEventListener("pointerover", (e) => {
  const a = (e.target as Element).closest(".fn a") as HTMLAnchorElement | null;
  if (a && (e as PointerEvent).pointerType === "mouse") showNote(a);
});
document.addEventListener("pointerout", (e) => {
  const a = (e.target as Element).closest(".fn a");
  if (a && (e as PointerEvent).pointerType === "mouse") hideNote();
});
document.addEventListener("focusin", (e) => {
  const a = (e.target as Element).closest?.(".fn a") as HTMLAnchorElement | null;
  if (a) showNote(a);
});
document.addEventListener("focusout", (e) => {
  if ((e.target as Element).closest?.(".fn a")) hideNote();
});
document.addEventListener("click", (e) => {
  const a = (e.target as Element).closest(".fn a") as HTMLAnchorElement | null;
  if (a && matchMedia("(hover: none)").matches) {
    e.preventDefault();
    if (popFor === a) hideNote();
    else showNote(a);
  } else if (!(e.target as Element).closest("#fn-pop")) hideNote();
});
addEventListener("scroll", () => popFor && hideNote(), { passive: true });

/* ---------------------------------------------------------------- artifacts (Blender models, lazy) */
{
  const els = document.querySelectorAll(".artifact");
  const io = new IntersectionObserver(
    (es) => {
      if (es.some((e) => e.isIntersecting)) {
        io.disconnect();
        import("./viewer").then((m) => m.mountArtifacts());
      }
    },
    { rootMargin: "150% 0px" },
  );
  els.forEach((el) => io.observe(el));
}

/* ---------------------------------------------------------------- the 3D map */
const loader = document.querySelector(".loader") as HTMLElement;
const loaderBar = loader.querySelector(".loader-bar i") as HTMLElement;
const canvas = document.getElementById("map") as HTMLCanvasElement;
try {
  const world = await createWorld(canvas, (f) => (loaderBar.style.transform = `scaleX(${f})`));
  mapWorld = world;
  onScroll();
  addEventListener("pointermove", () => (world.busy = true), { passive: true });
  const proj = makeProjector(world.geo, world.heightAt);
  const director = new Director(world, proj, STEPS, document.getElementById("labels")!);
  director.onStep = markStep;
  landingFor = (id) => director.landing(id);
  const movers = new Movers(world, director.routes);
  director.movers = (step, p, dt) => movers.update(step, p, dt);
  world.onFrame.push((dt) => director.update(dt));
  loadLandmarks(world, proj).then((lm) => {
    movers.useModels(lm.movers);
    world.landmarks = lm;
  });
  startLoop(world);
  loaderBar.style.transform = "scaleX(1)";
  document.body.classList.add("map-ready");
  setTimeout(() => loader.classList.add("is-done"), 250);
  // stop drawing the map while the appendix (timeline, notes, bibliography) covers the whole screen
  const after = document.getElementById("after")!;
  const checkCovered = () => {
    const r = after.getBoundingClientRect();
    world.paused = r.top <= 0 && r.bottom >= innerHeight;
  };
  addEventListener("scroll", checkCovered, { passive: true });
  checkCovered();
  Object.assign(window, { world, director });
  // dev/QA: jump straight to a camera stop (?step=<id>&k=<key>, or window.__goto(id, key) from tools/cdp-shot.mjs)
  if (import.meta.env.DEV) {
    const go = (id: string, k = 0) => {
      const i = STEPS.findIndex((s) => s.id === id);
      // the stop's own keys (not the hold that keeps the previous view until its card locks); fractional k lands
      // between two of them, and k = -1 is the moment the card locks, before the flight starts
      const own = director.keys.map((kk, idx) => ({ kk, idx })).filter(({ kk }) => kk.step === i && !kk.hold);
      if (!own.length) return false;
      const [pa] = director.pins[i];
      let y: number;
      if (k < 0) y = pa + 1;
      else {
        const lo = own[Math.min(Math.floor(k), own.length - 1)];
        const next = director.keys[Math.min(lo.idx + 1, director.keys.length - 1)];
        y = lo.kk.y + (next.y - lo.kk.y) * (k - Math.floor(k));
      }
      lenis?.scrollTo(y, { immediate: true, force: true });
      scrollTo(0, y);
      director.snap();
      return true;
    };
    Object.assign(window, { __goto: go });
    const q = new URLSearchParams(location.search);
    if (q.get("step")) go(q.get("step")!, Number(q.get("k") ?? 0));
  }
} catch (err) {
  console.error(err);
  loader.querySelector(".loader-text")!.textContent = "The 3D map could not start on this device. The full text is below.";
  loader.classList.add("is-error");
  document.body.classList.add("no-map");
}

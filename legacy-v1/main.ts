import "./style.css";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Lenis from "lenis";
import { noteHtml, renderSite } from "./render";
import { mountScenes, type SceneMeta } from "./parallax";

gsap.registerPlugin(ScrollTrigger);
document.documentElement.classList.add("js");
const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;

renderSite();

/* ---------------------------------------------------------------- smooth scroll */
let lenis: Lenis | null = null;
if (!reduced) {
  lenis = new Lenis({ lerp: 0.11, smoothWheel: true, wheelMultiplier: 0.95 });
  lenis.on("scroll", ScrollTrigger.update);
  gsap.ticker.add((t) => lenis!.raf(t * 1000));
  gsap.ticker.lagSmoothing(0);
}

function scrollToHash(hash: string) {
  const target = document.querySelector(hash) as HTMLElement | null;
  if (!target) return;
  if (lenis) lenis.scrollTo(target, { offset: hash === "#top" ? 0 : -8, duration: 1.4 });
  else target.scrollIntoView({ behavior: reduced ? "auto" : "smooth" });
  history.replaceState(null, "", hash);
}

document.addEventListener("click", (e) => {
  const a = (e.target as Element).closest("a[href^='#']") as HTMLAnchorElement | null;
  if (!a || a.getAttribute("href") === "#") return;
  if (a.closest(".fn") && matchMedia("(hover: none)").matches) return; // touch: first tap shows the popover
  e.preventDefault();
  scrollToHash(a.getAttribute("href")!);
});

/* ---------------------------------------------------------------- 3D scenes */
const manifest: Record<string, SceneMeta & { lqip?: string }> = await fetch("scenes/manifest.json").then((r) => r.json());
// blurred placeholder so a scene is never a black box while its image loads
document.querySelectorAll<HTMLElement>(".scene[data-scene]").forEach((el) => {
  const m = manifest[el.dataset.scene!];
  if (!m?.lqip) return;
  el.style.backgroundImage = `url("${m.lqip}")`;
  el.style.backgroundSize = "cover";
  el.style.backgroundPosition = `${m.focal[0] * 100}% ${m.focal[1] * 100}%`;
});
const scenes = mountScenes(manifest);
for (const s of scenes) {
  ScrollTrigger.create({
    trigger: s.el,
    start: "top bottom",
    end: "bottom top",
    onUpdate: (self) => (s.progress = self.progress),
  });
}

/* ---------------------------------------------------------------- hero entrance */
if (!reduced) {
  gsap.from(".hero .kicker, .hero-title__main, .hero-title__years, .hero-sub, .hero-byline", {
    y: 30,
    opacity: 0,
    duration: 1.4,
    ease: "power3.out",
    stagger: 0.12,
    delay: 0.2,
  });
  gsap.from(".hero-vertical", { opacity: 0, y: -20, duration: 2, delay: 0.9, ease: "power2.out" });
  gsap.to(".hero-inner", {
    yPercent: -12,
    opacity: 0.2,
    ease: "none",
    scrollTrigger: { trigger: ".hero", start: "top top", end: "bottom top", scrub: true },
  });
}

/* ---------------------------------------------------------------- reveals */
if (!reduced) {
  ScrollTrigger.batch(".reveal", {
    start: "top 88%",
    once: true,
    onEnter: (els) => gsap.to(els, { opacity: 1, y: 0, duration: 1, ease: "power3.out", stagger: 0.08, overwrite: true }),
  });
  document.querySelectorAll<HTMLElement>(".chapter").forEach((ch) => {
    const head = ch.querySelector(".chapter-head");
    const hanzi = ch.querySelector(".chapter-hanzi");
    const tl = gsap.timeline({ scrollTrigger: { trigger: ch, start: "top 70%" } });
    if (head) tl.from(head.children, { y: 40, opacity: 0, duration: 1.2, ease: "power3.out", stagger: 0.1 });
    if (hanzi) tl.from(hanzi, { opacity: 0, scale: 0.92, duration: 2, ease: "power2.out" }, 0);
  });
  gsap.from(".dyn-bar", {
    scaleX: 0,
    duration: 1.1,
    ease: "power3.out",
    stagger: 0.05,
    scrollTrigger: { trigger: "#dynasty-chart", start: "top 85%" },
  });
}

/* ---------------------------------------------------------------- progress bar + rail */
const bar = document.querySelector(".progress span") as HTMLElement;
ScrollTrigger.create({
  start: 0,
  end: "max",
  onUpdate: (self) => (bar.style.transform = `scaleX(${self.progress})`),
});
const rail = document.querySelector(".rail") as HTMLElement;
ScrollTrigger.create({
  trigger: "#prologue",
  start: "top 60%",
  onEnter: () => rail.classList.add("is-visible"),
  onLeaveBack: () => rail.classList.remove("is-visible"),
});
const links = [...document.querySelectorAll<HTMLAnchorElement>(".rail-link")];
document.querySelectorAll<HTMLElement>(".chapter").forEach((ch) => {
  ScrollTrigger.create({
    trigger: ch,
    start: "top 50%",
    end: "bottom 50%",
    onToggle: (self) => {
      if (!self.isActive) return;
      links.forEach((l) => l.classList.toggle("is-active", l.dataset.target === ch.id));
    },
  });
});
ScrollTrigger.create({
  trigger: "#connections",
  start: "top 50%",
  onEnter: () => links.forEach((l) => l.classList.remove("is-active")),
});

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
window.addEventListener("scroll", () => popFor && hideNote(), { passive: true });

/* ---------------------------------------------------------------- lazy modules: artifacts + map */
const lazy = (sel: string, load: () => Promise<unknown>) => {
  const els = document.querySelectorAll(sel);
  if (!els.length) return;
  const io = new IntersectionObserver(
    (es) => {
      if (es.some((e) => e.isIntersecting)) {
        io.disconnect();
        load();
      }
    },
    { rootMargin: "150% 0px" },
  );
  els.forEach((el) => io.observe(el));
};
lazy(".artifact", () => import("./viewer").then((m) => m.mountArtifacts()));
lazy("#connections", () => import("./map").then((m) => m.mountMap()));

// refresh trigger positions once fonts and images have settled
document.fonts?.ready.then(() => ScrollTrigger.refresh());
window.addEventListener("load", () => ScrollTrigger.refresh());

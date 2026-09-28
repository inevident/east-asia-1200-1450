import * as THREE from "three";
import type { World } from "../world/world";
import type { Projector } from "../world/geo";
import { Labels } from "../world/labels";
import { Routes, type RouteLine } from "../world/routes";
import type { Cam, Step } from "./steps";

interface CamState {
  t: THREE.Vector3;
  logd: number;
  pitch: number;
  yaw: number;
  ox: number; // horizontal view offset (px): positive moves the target to the right
  oy: number;
}

interface Key {
  step: number;
  y: number; // scroll position at which this key is exactly reached
  cam: Cam;
  pos: THREE.Vector3;
  /** a copy of the previous view that holds the camera still until this stop's animation begins */
  hold?: boolean;
}

const DEG = Math.PI / 180;
const smooth = (e0: number, e1: number, x: number) => {
  const t = Math.min(Math.max((x - e0) / (e1 - e0), 0), 1);
  return t * t * (3 - 2 * t);
};
const wrapAngle = (a: number) => Math.atan2(Math.sin(a), Math.cos(a));
/** Set a CSS custom property only when it changes (layout runs often; avoid needless style recalcs). */
const setVar = (el: HTMLElement, name: string, value: string) => {
  if (el.style.getPropertyValue(name) !== value) el.style.setProperty(name, value);
};

/**
 * Scroll-driven camera. Each stop's text card scrolls in and then locks in place (sticky) once it is fully on
 * screen, or once the reader has reached its end if it is taller than the screen. While it is locked, scrolling plays
 * that stop's animation: the camera flies there (pulling back for long hops) and its routes and arcs draw. Then the
 * card is released and scrolls away; the camera holds still while cards come and go. On phones, where the card
 * covers the map, the animation plays in the map-only gap before each card instead.
 */
export class Director {
  world: World;
  proj: Projector;
  steps: Step[];
  sections: HTMLElement[];
  keys: Key[] = [];
  /** scroll range in which each stop's animation plays */
  pins: [number, number][] = [];
  /** per stop: the reference timeline's segment boundaries and the actual (flight-length-weighted) ones */
  private tl: { ref: number[]; act: number[] }[] = [];
  labels: Labels;
  routes: Routes;
  cur!: CamState;
  want!: CamState;
  active = -1;
  stepProgress = 0;
  reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  heroSpin = 0;
  onStep?: (i: number, s: Step) => void;
  /** gentle look-around that follows the mouse, eased */
  private look = { x: 0, y: 0, tx: 0, ty: 0 };
  movers?: (step: Step, progress: number, dt: number) => void;
  private lastLayout = 0;
  private lastScrollY = -1;
  private lastMotion = 0;

  constructor(world: World, proj: Projector, steps: Step[], labelsRoot: HTMLElement) {
    this.world = world;
    this.proj = proj;
    this.steps = steps;
    this.sections = steps.map((s) => document.getElementById(s.id)!);
    this.labels = new Labels(labelsRoot, proj);
    this.routes = new Routes(world.geo.routes, proj, world.heightAt);
    world.scene.add(this.routes.group);
    this.layout();
    const first = this.stateAt(scrollY);
    this.cur = { ...first, t: first.t.clone() };
    this.want = first;
    addEventListener("resize", () => this.layout());
    if (matchMedia("(pointer: fine)").matches && !this.reduced) {
      addEventListener("pointermove", (e) => {
        this.look.tx = e.clientX / innerWidth - 0.5;
        this.look.ty = e.clientY / innerHeight - 0.5;
      });
    }
    new ResizeObserver(() => this.layout()).observe(document.body);
  }

  /** Scroll position for a link into a stop: its card at the top of the screen, its animation about to begin. */
  landing(id: string): number | null {
    const i = this.steps.findIndex((s) => s.id === id);
    if (i < 0) return null;
    this.layout();
    const el = this.sections[i];
    const stick = parseFloat(el.style.getPropertyValue("--stick"));
    const enter = parseFloat(el.style.getPropertyValue("--enter"));
    if (Number.isNaN(stick) || Number.isNaN(enter)) return this.pins[i][1];
    const top = el.getBoundingClientRect().top + scrollY;
    return top + enter - Math.max(stick, innerHeight * 0.08);
  }

  /**
   * Reference timeline of a stop's locked stretch (0..1): a flight to each place, a rest at it, and a longer dwell
   * at the last one, every flight the same length. Route, arc and mover timings in steps.ts are written against
   * this; the real stretch gives each flight scroll distance in proportion to its length, and progress is mapped back.
   */
  static timeline(n: number): { arrive: number; leave: number }[] {
    return Director.plan(new Array<number>(n).fill(1), 1, 0.4, 0.5).map(({ arrive, leave }) => ({ arrive, leave }));
  }

  /** Lay flights (in units of `px` per unit of length, clamped) and rests along a stop's stretch. */
  static plan(lens: number[], px: number, rest: number, dwell: number, min = 0, max = Infinity) {
    const n = lens.length;
    let t = 0;
    const out: { arrive: number; leave: number }[] = [];
    lens.forEach((L, j) => {
      t += Math.min(Math.max(L * px, min), max);
      const arrive = t;
      t += j < n - 1 ? rest : dwell;
      out.push({ arrive, leave: t });
    });
    return out.map(({ arrive, leave }) => ({ arrive: arrive / t, leave: leave / t, total: t }));
  }

  /** Progress through a stop's stretch (0..1), expressed on the reference timeline that steps.ts timings use. */
  toRef(i: number, p: number): number {
    const t = this.tl[i];
    if (!t) return p;
    const { ref, act } = t;
    let k = 0;
    while (k < act.length - 2 && p > act[k + 1]) k++;
    const span = act[k + 1] - act[k];
    return span > 0 ? ref[k] + ((ref[k + 1] - ref[k]) * (p - act[k])) / span : ref[k];
  }

  private camTarget(c: Cam): THREE.Vector3 {
    const pos = this.proj.place(c.at);
    if (c.off) {
      pos.x += c.off[0];
      pos.z -= c.off[1];
      pos.y = Math.max(this.world.heightAt(pos.x, pos.z), 0);
    }
    return pos;
  }

  /** Size each stop's section around its card, then place the camera keys inside each stop's locked stretch. */
  layout() {
    const H = innerHeight;
    const mobile = innerWidth <= 760;
    const cards = this.sections.map((el) => el.querySelector(".card") as HTMLElement | null);
    // 0) camera targets, how much motion each flight holds, and each stop's stretch: long flights get more scroll
    const targets = this.steps.map((s) => s.cams.map((c) => this.camTarget(c)));
    let pPos: THREE.Vector3 | null = null;
    let pD = 1;
    const plans = this.steps.map((s, i) => {
      const lens = s.cams.map((c, j) => {
        const pos = targets[i][j];
        const L = pPos ? flightLength(pD, c.d, pPos.distanceTo(pos)) : 0;
        pPos = pos;
        pD = c.d;
        return L;
      });
      const plan = Director.plan(lens, 240, 0.2 * H, 0.35 * H, 0.3 * H, 1.2 * H);
      const ref = Director.timeline(s.cams.length);
      const bounds = (t: { arrive: number; leave: number }[]) => [0, ...t.flatMap((x) => [x.arrive, x.leave])];
      this.tl[i] = { ref: bounds(ref), act: bounds(plan) };
      return plan;
    });
    // 1) sizes: [gap] [card] [locked stretch that plays the animation]
    this.steps.forEach((s, i) => {
      const el = this.sections[i];
      const card = cards[i];
      if (!card || s.kind === "hero") return;
      const anim = Math.round(plans[i][0]?.total ?? H);
      if (mobile) {
        setVar(el, "--gap", `${anim + Math.round(H * 0.5)}px`);
        for (const v of ["--stick", "--enter", "--step-h"]) el.style.removeProperty(v);
        return;
      }
      el.style.removeProperty("--gap");
      const cardH = card.offsetHeight;
      const margin = H * 0.08;
      // short cards lock a little above centre; tall ones lock once their last line is on screen
      const stick = cardH <= H - 2 * margin ? Math.max(margin, (H - cardH) * 0.42) : H - cardH - margin;
      const enter = Math.round(H * 0.3);
      setVar(el, "--stick", `${Math.round(stick)}px`);
      setVar(el, "--enter", `${enter}px`);
      setVar(el, "--step-h", `${enter + cardH + anim}px`);
    });
    // 2) where each stop's animation starts and ends, and the camera keys within it
    this.keys = [];
    this.pins = [];
    let prev: Key | null = null;
    this.steps.forEach((s, i) => {
      const el = this.sections[i];
      const card = cards[i];
      const top = el.getBoundingClientRect().top + scrollY;
      let a = top;
      let b = top;
      if (card && s.kind !== "hero") {
        if (mobile) {
          const gap = parseFloat(getComputedStyle(el).paddingTop) || H;
          a = top - H * 0.2; // the previous card has left the screen
          b = top + gap - H * 0.75; // this card is just coming up from the bottom
        } else {
          const stick = parseFloat(el.style.getPropertyValue("--stick")) || 0;
          const enter = parseFloat(el.style.getPropertyValue("--enter")) || 0;
          a = top + enter - stick; // the card locks in place here...
          b = top + el.offsetHeight - card.offsetHeight - stick; // ...and is released here
        }
      }
      this.pins[i] = [a, b];
      // the previous view holds (with its own framing) until this card locks and the flight begins
      if (prev && a > prev.y) this.keys.push({ ...prev, y: a, hold: true });
      const n = s.cams.length;
      const tl = plans[i];
      s.cams.forEach((c, j) => {
        const pos = targets[i][j];
        const k: Key = { step: i, y: b > a ? a + (b - a) * tl[j].arrive : a, cam: c, pos };
        this.keys.push(k);
        // rest at this place before flying on to the next one
        if (j < n - 1 && b > a) this.keys.push({ ...k, y: a + (b - a) * tl[j].leave, hold: true });
        prev = k;
      });
    });
    this.lastLayout = performance.now();
  }

  /** How far the panel for a step sits from the left edge, so the camera can frame the map beside it. */
  private offsetFor(step: Step): [number, number] {
    const W = innerWidth;
    if (W < 760) return [0, step.kind === "hero" ? 0 : -innerHeight * 0.12];
    if (step.kind === "hero") return [0, -innerHeight * 0.06];
    const card = this.sections[this.steps.indexOf(step)]?.querySelector(".card") as HTMLElement | null;
    const right = card ? Math.min(card.getBoundingClientRect().right, W * 0.62) : W * 0.4;
    return [right / 2, 0];
  }

  private camOf(k: Key): CamState {
    const [ox, oy] = this.offsetFor(this.steps[k.step]);
    return { t: k.pos.clone(), logd: Math.log(k.cam.d), pitch: k.cam.pitch * DEG, yaw: k.cam.yaw * DEG, ox, oy };
  }

  /** The camera the scroll position asks for. */
  stateAt(y: number): CamState {
    const K = this.keys;
    if (y <= K[0].y) return this.camOf(K[0]);
    if (y >= K[K.length - 1].y) return this.camOf(K[K.length - 1]);
    let i = 0;
    while (i < K.length - 2 && y > K[i + 1].y) i++;
    const A = this.camOf(K[i]);
    const B = this.camOf(K[i + 1]);
    const f = (y - K[i].y) / Math.max(K[i + 1].y - K[i].y, 1);
    if (this.reduced) return f < 0.5 ? A : B;
    const e = smooth(0.03, 0.97, f);
    return blend(A, B, e);
  }

  /** Jump the camera straight to where the scroll position wants it (no easing). */
  snap() {
    const w = this.stateAt(scrollY);
    this.cur = { ...w, t: w.t.clone() };
  }

  update(dt: number) {
    const W = innerWidth;
    const H = innerHeight;
    if (performance.now() - this.lastLayout > 1500) this.layout(); // fonts and images can shift the layout
    const y = scrollY;
    this.want = this.stateAt(y);

    // the current stop is the latest one whose animation has begun; progress runs 0 to 1 while its card is locked
    let act = 0;
    for (let i = 0; i < this.pins.length; i++) if (y >= this.pins[i][0] - 1) act = i;
    const [pa, pb] = this.pins[act];
    this.stepProgress = pb > pa ? Math.min(Math.max((y - pa) / (pb - pa), 0), 1) : 1;
    if (act !== this.active) {
      this.active = act;
      this.labels.set(this.steps[act].labels ?? []);
      this.onStep?.(act, this.steps[act]);
    }

    // hero: a slow drifting orbit while the title is up
    const step = this.steps[act];
    if (step.kind === "hero" && !this.reduced) this.heroSpin += dt * 0.012;
    else this.heroSpin *= Math.exp(-dt * 1.5);
    this.want.yaw += this.heroSpin;
    const lk = 1 - Math.exp(-dt * 2.5);
    this.look.x += (this.look.tx - this.look.x) * lk;
    this.look.y += (this.look.ty - this.look.y) * lk;
    this.want.yaw += this.look.x * 4 * DEG;
    this.want.pitch += this.look.y * 2 * DEG;

    // ease the real camera toward the wanted one; catch up faster when it has fallen far behind
    const c = this.cur;
    const behind = Math.min(1, c.t.distanceTo(this.want.t) / Math.exp(c.logd));
    const k = this.reduced ? 1 : 1 - Math.exp(-dt * 4.2 * (1 + 3 * behind));
    c.t.lerp(this.want.t, k);
    c.logd += (this.want.logd - c.logd) * k;
    c.pitch += (this.want.pitch - c.pitch) * k;
    c.yaw += wrapAngle(this.want.yaw - c.yaw) * k;
    c.ox += (this.want.ox - c.ox) * k;
    c.oy += (this.want.oy - c.oy) * k;
    this.apply(c, W, H);

    // routes and arcs for the active step
    const want = new Map<RouteLine, number>();
    const pRef = this.toRef(act, this.stepProgress);
    const arrive = Director.timeline(step.cams.length)[step.cams.length - 1].arrive;
    for (const r of step.routes ?? []) {
      const line = this.routes.route(r.id, r.style);
      // by default a route draws once the camera has reached the stop's last place; "full" draws during the flight
      const span = r.draw === "full" ? [0.02, 0.6] : (r.span ?? [arrive, 0.97]);
      want.set(line, smooth(span[0], Math.min(Math.max(span[1], span[0] + 0.05), 0.985), pRef));
    }
    for (const a of step.arcs ?? []) {
      const line = this.routes.arc(a);
      const d0 = a.delay ?? arrive;
      want.set(line, smooth(d0, Math.min(d0 + 0.22, 0.985), pRef));
    }
    for (const line of this.routes.lines.values()) {
      const w = want.get(line);
      line.targetOpacity = w === undefined ? 0 : 1;
      if (w !== undefined) line.targetDraw = Math.max(w, 0.0001);
      else if (line.opacity < 0.02) line.targetDraw = 0;
    }
    this.routes.update(dt, Math.exp(c.logd));
    // stay at full frame rate until the camera and the routes have settled and the reader has stopped scrolling
    const now = performance.now();
    if (y !== this.lastScrollY) {
      this.lastScrollY = y;
      this.lastMotion = now;
    }
    const w = this.want;
    const d = Math.exp(c.logd);
    const moving =
      c.t.distanceTo(w.t) > d * 0.0004 ||
      Math.abs(c.logd - w.logd) > 0.0004 ||
      Math.abs(c.pitch - w.pitch) > 0.0004 ||
      Math.abs(wrapAngle(c.yaw - w.yaw)) > (step.kind === "hero" ? 0.006 : 0.0004) || // the hero's slow orbit is ambient
      Math.abs(c.ox - w.ox) > 0.5 ||
      Math.abs(c.oy - w.oy) > 0.5 ||
      [...this.routes.lines.values()].some((r) => Math.abs(r.opacity - r.targetOpacity) > 0.01 || Math.abs(r.draw - r.targetDraw) > 0.002);
    if (moving) this.lastMotion = now;
    this.world.busy = now - this.lastMotion < 700;
    this.movers?.(step, pRef, dt);
    this.labels.update(this.world.camera, W, H);
  }

  private apply(c: CamState, W: number, H: number) {
    const cam = this.world.camera;
    const d = Math.exp(c.logd);
    const cp = Math.cos(c.pitch);
    cam.position.set(c.t.x + Math.sin(c.yaw) * cp * d, c.t.y + Math.sin(c.pitch) * d, c.t.z + Math.cos(c.yaw) * cp * d);
    // never dip below the ground on the way in
    const ground = Math.max(this.world.heightAt(cam.position.x, cam.position.z), 0);
    if (cam.position.y < ground + 1.2) cam.position.y = ground + 1.2;
    cam.up.set(0, 1, 0);
    cam.lookAt(c.t);
    this.world.focus.copy(c.t);
    this.world.focusDist = d;
    cam.near = Math.max(0.05, d * 0.02);
    cam.far = Math.max(4000, d * 8);
    if (Math.abs(c.ox) > 0.5 || Math.abs(c.oy) > 0.5) cam.setViewOffset(W, H, -c.ox, -c.oy, W, H);
    else cam.clearViewOffset();
    cam.updateProjectionMatrix();
  }
}

const RHO = 1.42;

/**
 * The smooth zoom-out, pan, zoom-in path between two views (van Wijk & Nuij, "Smooth and efficient zooming and
 * panning", 2003): w0 and w1 are the start and end viewing distances, u1 the pan distance, s the progress (0..1).
 * Returns how far along the pan to be (0..1) and the viewing distance, such that motion looks steady on screen.
 */
function flightPath(w0: number, w1: number, u1: number, s: number): { u: number; w: number } {
  if (u1 < 1e-4 * (w0 + w1)) return { u: s, w: w0 * Math.pow(w1 / w0, s) };
  const r = (i: 0 | 1) => {
    const wi = i ? w1 : w0;
    const b = (w1 * w1 - w0 * w0 + (i ? -1 : 1) * RHO ** 4 * u1 * u1) / (2 * wi * RHO * RHO * u1);
    return Math.log(-b + Math.sqrt(b * b + 1));
  };
  const r0 = r(0);
  const r1 = r(1);
  const S = (r1 - r0) / RHO;
  const x = RHO * s * S + r0;
  const u = ((w0 / (RHO * RHO)) * (Math.cosh(r0) * Math.tanh(x) - Math.sinh(r0))) / u1;
  const w = (w0 * Math.cosh(r0)) / Math.cosh(x);
  return { u: Math.min(Math.max(u, 0), 1), w };
}

/** Length of the flight path in "screens of motion": the amount of perceived movement between two views. */
function flightLength(w0: number, w1: number, u1: number): number {
  if (u1 < 1e-4 * (w0 + w1)) return Math.abs(Math.log(w1 / w0)) / RHO;
  const r = (i: 0 | 1) => {
    const wi = i ? w1 : w0;
    const b = (w1 * w1 - w0 * w0 + (i ? -1 : 1) * RHO ** 4 * u1 * u1) / (2 * wi * RHO * RHO * u1);
    return Math.log(-b + Math.sqrt(b * b + 1));
  };
  return (r(1) - r(0)) / RHO;
}

/** Blend two camera states along the flight path; big pull-backs also tilt the camera down a little at the apex. */
function blend(A: CamState, B: CamState, e: number): CamState {
  const w0 = Math.exp(A.logd);
  const w1 = Math.exp(B.logd);
  const D = A.t.distanceTo(B.t);
  const { u, w } = flightPath(w0, w1, D, e);
  const apex = Math.max(w / Math.max(w0, w1), 1);
  const bump = Math.min(14 * DEG, (80 * DEG - Math.max(A.pitch, B.pitch)) * 0.5) * Math.min(1, Math.log(apex) / 1.5) * 4 * e * (1 - e);
  return {
    t: A.t.clone().lerp(B.t, u),
    logd: Math.log(w),
    pitch: A.pitch + (B.pitch - A.pitch) * e + bump,
    yaw: A.yaw + wrapAngle(B.yaw - A.yaw) * e,
    ox: A.ox + (B.ox - A.ox) * e,
    oy: A.oy + (B.oy - A.oy) * e,
  };
}

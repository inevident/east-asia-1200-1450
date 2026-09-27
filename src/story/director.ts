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
}

const DEG = Math.PI / 180;
const smooth = (e0: number, e1: number, x: number) => {
  const t = Math.min(Math.max((x - e0) / (e1 - e0), 0), 1);
  return t * t * (3 - 2 * t);
};
const wrapAngle = (a: number) => Math.atan2(Math.sin(a), Math.cos(a));

/**
 * Scroll-driven camera: each story step's section defines one or more camera keys; scrolling between keys
 * flies the camera along an arc that pulls back for long hops (like a bird's-eye "hop" between places).
 */
export class Director {
  world: World;
  proj: Projector;
  steps: Step[];
  sections: HTMLElement[];
  keys: Key[] = [];
  tops: number[] = [];
  heights: number[] = [];
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

  /** Scroll positions for every camera key (a key is reached when its point in the section crosses mid-screen). */
  layout() {
    const H = innerHeight;
    this.keys = [];
    this.steps.forEach((s, i) => {
      const el = this.sections[i];
      const top = el.getBoundingClientRect().top + scrollY;
      const h = el.offsetHeight;
      this.tops[i] = top;
      this.heights[i] = h;
      const n = s.cams.length;
      s.cams.forEach((c, j) => {
        const frac = n === 1 ? 0.5 : 0.18 + (0.64 * j) / (n - 1);
        const pos = this.proj.place(c.at);
        if (c.off) {
          pos.x += c.off[0];
          pos.z -= c.off[1];
          pos.y = Math.max(this.world.heightAt(pos.x, pos.z), 0);
        }
        this.keys.push({ step: i, y: top + h * frac - H / 2, cam: c, pos });
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
    const e = smooth(0.2, 0.8, f);
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

    // which step is under mid-screen, and how far through it
    const mid = y + H / 2;
    let act = 0;
    for (let i = 0; i < this.tops.length; i++) if (mid >= this.tops[i]) act = i;
    this.stepProgress = Math.min(Math.max((mid - this.tops[act]) / Math.max(this.heights[act], 1), 0), 1);
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

    // ease the real camera toward the wanted one (critically damped feel)
    const k = this.reduced ? 1 : 1 - Math.exp(-dt * 4.2);
    const c = this.cur;
    c.t.lerp(this.want.t, k);
    c.logd += (this.want.logd - c.logd) * k;
    c.pitch += (this.want.pitch - c.pitch) * k;
    c.yaw += wrapAngle(this.want.yaw - c.yaw) * k;
    c.ox += (this.want.ox - c.ox) * k;
    c.oy += (this.want.oy - c.oy) * k;
    this.apply(c, W, H);

    // routes and arcs for the active step
    const want = new Map<RouteLine, number>();
    for (const r of step.routes ?? []) {
      const line = this.routes.route(r.id, r.style);
      const span = step.cams.length > 1 ? [0.45, 0.9] : [0.12, 0.72];
      want.set(line, r.draw === "full" ? 1 : smooth(span[0], span[1], this.stepProgress));
    }
    for (const a of step.arcs ?? []) {
      const line = this.routes.arc(a);
      const d0 = a.delay ?? 0.2;
      want.set(line, smooth(d0, d0 + 0.28, this.stepProgress));
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
    this.movers?.(step, this.stepProgress, dt);
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

/** Blend two camera states; long hops pull the camera back and tilt it down, then swing in to the next place. */
function blend(A: CamState, B: CamState, e: number): CamState {
  const D = Math.hypot(B.t.x - A.t.x, B.t.z - A.t.z);
  const dA = Math.exp(A.logd);
  const dB = Math.exp(B.logd);
  const dMid = Math.max(dA, dB, D * 0.8);
  const hop = dMid > Math.max(dA, dB) * 1.1;
  let logd: number;
  // pan speed follows altitude: while low, the target barely moves, so flights climb, travel, then descend
  let te = dB > dA * 2 ? e * e : dA > dB * 2 ? 1 - (1 - e) * (1 - e) : e;
  let bump = 0;
  if (hop) {
    const lm = Math.log(dMid);
    logd = (1 - e) * (1 - e) * A.logd + 2 * e * (1 - e) * lm + e * e * B.logd;
    te = smooth(0.08, 0.92, e);
    bump = Math.min(14 * DEG, (80 * DEG - Math.max(A.pitch, B.pitch)) * 0.5) * 4 * e * (1 - e);
  } else {
    logd = A.logd + (B.logd - A.logd) * e;
  }
  return {
    t: A.t.clone().lerp(B.t, te),
    logd,
    pitch: A.pitch + (B.pitch - A.pitch) * e + bump,
    yaw: A.yaw + wrapAngle(B.yaw - A.yaw) * e,
    ox: A.ox + (B.ox - A.ox) * e,
    oy: A.oy + (B.oy - A.oy) * e,
  };
}

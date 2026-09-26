import * as THREE from "three";
import { Line2 } from "three/addons/lines/Line2.js";
import { LineGeometry } from "three/addons/lines/LineGeometry.js";
import { LineMaterial } from "three/addons/lines/LineMaterial.js";
import type { Arc, RouteStyle } from "../story/steps";
import type { Projector } from "./geo";

interface StyleDef {
  color: string;
  width: number;
  dash?: [number, number];
  flow?: number;
}

export const STYLES: Record<RouteStyle, StyleDef> = {
  land: { color: "#a8321f", width: 3.2, dash: [2.6, 1.6], flow: 2.2 },
  sea: { color: "#1f4a8a", width: 2.8, dash: [3.2, 2.2], flow: 3 },
  fleet: { color: "#b07d1e", width: 4.2 },
  canal: { color: "#155f69", width: 3.6 },
  war: { color: "#2a1e18", width: 3, dash: [1.6, 1.1], flow: 1.6 },
  idea: { color: "#2d7a62", width: 3.2 },
  goods: { color: "#1c4c98", width: 3.2 },
  plague: { color: "#7b1616", width: 3.2, dash: [1.8, 1.2], flow: 2.4 },
};

const CASING = new THREE.Color("#f6efe0");

/** A drawable line (a trade route, voyage, canal, or an arc of diffusion) with a paper-coloured casing. */
export class RouteLine {
  group = new THREE.Group();
  line: Line2;
  casing: Line2;
  mat: LineMaterial;
  cmat: LineMaterial;
  points: THREE.Vector3[];
  curve: THREE.CatmullRomCurve3;
  segs: number;
  head: THREE.Mesh;
  style: StyleDef;
  opacity = 0;
  targetOpacity = 0;
  draw = 0;
  targetDraw = 0;
  isArc: boolean;

  constructor(points: THREE.Vector3[], style: StyleDef, isArc: boolean) {
    this.points = points;
    this.style = style;
    this.isArc = isArc;
    this.curve = new THREE.CatmullRomCurve3(points, false, "centripetal");
    const flat = points.flatMap((p) => [p.x, p.y, p.z]);
    const geo = new LineGeometry();
    geo.setPositions(flat);
    this.segs = points.length - 1;
    this.mat = new LineMaterial({
      color: new THREE.Color(style.color),
      linewidth: style.width,
      transparent: true,
      opacity: 0,
      dashed: !!style.dash,
      dashSize: style.dash?.[0] ?? 1,
      gapSize: style.dash?.[1] ?? 1,
      depthWrite: false,
      polygonOffset: true,
      polygonOffsetFactor: -4,
      polygonOffsetUnits: -4,
    });
    this.line = new Line2(geo, this.mat);
    this.line.computeLineDistances();
    this.line.renderOrder = 6;
    this.cmat = new LineMaterial({
      color: CASING,
      linewidth: style.width + 3.2,
      transparent: true,
      opacity: 0,
      depthWrite: false,
      polygonOffset: true,
      polygonOffsetFactor: -3,
      polygonOffsetUnits: -3,
    });
    this.casing = new Line2(geo, this.cmat);
    this.casing.renderOrder = 5;
    const headGeo = isArc ? new THREE.ConeGeometry(0.9, 2.6, 12).rotateX(Math.PI / 2) : new THREE.SphereGeometry(0.7, 16, 12);
    this.head = new THREE.Mesh(headGeo, new THREE.MeshBasicMaterial({ color: style.color, transparent: true, opacity: 0, depthWrite: false }));
    this.head.renderOrder = 7;
    this.group.add(this.casing, this.line, this.head);
    this.group.visible = false;
    for (const l of [this.line, this.casing]) l.frustumCulled = false;
  }

  update(dt: number, camDist: number) {
    const k = 1 - Math.exp(-dt * 5);
    this.opacity += (this.targetOpacity - this.opacity) * k;
    this.draw += (this.targetDraw - this.draw) * (1 - Math.exp(-dt * 8));
    const vis = this.opacity > 0.01 && this.draw > 0.001;
    this.group.visible = vis;
    if (!vis) return;
    this.mat.opacity = this.opacity;
    this.cmat.opacity = this.opacity * 0.6;
    const n = Math.min(this.segs, Math.ceil(this.draw * this.segs));
    (this.line.geometry as LineGeometry).instanceCount = n;
    if (this.style.flow) this.mat.dashOffset -= dt * this.style.flow;
    // the drawing tip: a dot for routes, an arrowhead for arcs
    const drawing = this.draw < 0.995;
    const hm = this.head.material as THREE.MeshBasicMaterial;
    hm.opacity = this.opacity * (this.isArc || drawing ? 1 : 0);
    const t = Math.min(this.draw, 0.999);
    const p = this.curve.getPointAt(t);
    this.head.position.copy(p);
    const s = THREE.MathUtils.clamp(camDist / 180, 0.12, 5);
    this.head.scale.setScalar(s);
    if (this.isArc) {
      const tan = this.curve.getTangentAt(t);
      this.head.lookAt(p.clone().add(tan));
    }
  }
}

/** Builds route lines from geo.json and arcs between places; keeps one instance per (id, style). */
export class Routes {
  group = new THREE.Group();
  lines = new Map<string, RouteLine>();
  proj: Projector;
  heightAt: (x: number, z: number) => number;
  routes: Record<string, [number, number, number][]>;

  constructor(routes: Record<string, [number, number, number][]>, proj: Projector, heightAt: (x: number, z: number) => number) {
    this.routes = routes;
    this.proj = proj;
    this.heightAt = heightAt;
    this.group.name = "routes";
  }

  route(id: string, style: RouteStyle) {
    const key = `r:${id}:${style}`;
    let r = this.lines.get(key);
    if (!r) {
      const pts = this.routes[id].map(([x, , z]) => new THREE.Vector3(x, Math.max(this.heightAt(x, z), 0) + 0.45, z));
      r = new RouteLine(pts, STYLES[style], false);
      this.lines.set(key, r);
      this.group.add(r.group);
    }
    return r;
  }

  arc(a: Arc) {
    const key = `a:${JSON.stringify(a.from)}>${JSON.stringify(a.to)}:${a.style}`;
    let r = this.lines.get(key);
    if (!r) {
      const A = this.proj.place(a.from, 0.4);
      const B = this.proj.place(a.to, 0.4);
      const len = Math.hypot(B.x - A.x, B.z - A.z);
      const lift = (a.lift ?? 0.22) * len;
      const pts: THREE.Vector3[] = [];
      const N = 72;
      for (let i = 0; i <= N; i++) {
        const t = i / N;
        const x = A.x + (B.x - A.x) * t;
        const z = A.z + (B.z - A.z) * t;
        const base = Math.max(this.heightAt(x, z), 0, A.y + (B.y - A.y) * t);
        pts.push(new THREE.Vector3(x, base + Math.sin(Math.PI * t) * lift + 0.4, z));
      }
      r = new RouteLine(pts, STYLES[a.style], true);
      this.lines.set(key, r);
      this.group.add(r.group);
    }
    return r;
  }

  update(dt: number, camDist: number) {
    for (const r of this.lines.values()) r.update(dt, camDist);
  }
}

import * as THREE from "three";
import type { World } from "./world";
import type { Routes } from "./routes";
import type { MoverKind, Step } from "../story/steps";

interface Convoy {
  kind: MoverKind;
  route: string;
  group: THREE.Group;
  units: THREE.Object3D[];
  curve: THREE.CatmullRomCurve3;
  length: number;
  opacity: number;
  t: number; // position along the route (0..1) for the lead unit
}

/** Fleets, junks, caravans and canal barges that travel along the story's routes. */
export class Movers {
  world: World;
  routes: Routes;
  convoys = new Map<string, Convoy>();
  models = new Map<string, THREE.Object3D>();
  group = new THREE.Group();

  constructor(world: World, routes: Routes) {
    this.world = world;
    this.routes = routes;
    this.group.name = "movers";
    world.scene.add(this.group);
  }

  useModels(models: Map<string, THREE.Object3D>) {
    this.models = models;
    // rebuild any convoy created with placeholders
    for (const [key, c] of this.convoys) {
      this.group.remove(c.group);
      this.convoys.delete(key);
    }
  }

  private unit(kind: MoverKind, i: number): THREE.Object3D {
    const name = kind === "fleet" ? (i === 0 ? "treasure" : i % 3 === 0 ? "junk" : "treasure") : kind === "junks" ? "junk" : kind === "caravan" ? "camel" : "barge";
    const tpl = this.models.get(name);
    if (tpl) return tpl.clone(true);
    // placeholder: a simple hull or a small body until the Blender models have loaded
    const color = kind === "caravan" ? "#8a6a44" : kind === "barges" ? "#6d5236" : "#5a3d28";
    const g = new THREE.Group();
    const hull = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.08, kind === "caravan" ? 0.2 : 0.5), new THREE.MeshStandardMaterial({ color }));
    hull.position.y = 0.04;
    g.add(hull);
    if (kind !== "caravan") {
      const sail = new THREE.Mesh(new THREE.PlaneGeometry(0.22, 0.26), new THREE.MeshStandardMaterial({ color: "#b8673a", side: THREE.DoubleSide }));
      sail.position.y = 0.22;
      g.add(sail);
    }
    return g;
  }

  private convoy(kind: MoverKind, route: string): Convoy {
    const key = `${kind}:${route}`;
    let c = this.convoys.get(key);
    if (c) return c;
    const pts = this.world.geo.routes[route].map(([x, , z]) => new THREE.Vector3(x, 0, z));
    const curve = new THREE.CatmullRomCurve3(pts, false, "centripetal");
    const n = kind === "fleet" ? 9 : kind === "junks" ? 7 : kind === "caravan" ? 8 : 6;
    const group = new THREE.Group();
    const units: THREE.Object3D[] = [];
    for (let i = 0; i < n; i++) {
      const u = this.unit(kind, i);
      group.add(u);
      units.push(u);
    }
    group.visible = false;
    this.group.add(group);
    c = { kind, route, group, units, curve, length: curve.getLength(), opacity: 0, t: 0 };
    this.convoys.set(key, c);
    return c;
  }

  update(step: Step, progress: number, dt: number) {
    const cam = this.world.camera;
    const active = new Set<string>();
    for (const m of step.movers ?? []) {
      const c = this.convoy(m.kind, m.route);
      active.add(`${m.kind}:${m.route}`);
      if (m.mode === "scroll") {
        const span = m.span ?? (step.cams.length > 1 ? [0.3, 0.95] : [0.15, 0.9]);
        const f = Math.min(Math.max((progress - span[0]) / (span[1] - span[0]), 0), 1);
        c.t += (f - c.t) * (1 - Math.exp(-dt * 6));
      } else {
        c.t = (c.t + dt * (0.35 / c.length)) % 1;
      }
    }
    for (const [key, c] of this.convoys) {
      const on = active.has(key);
      c.opacity += ((on ? 1 : 0) - c.opacity) * (1 - Math.exp(-dt * 4));
      c.group.visible = c.opacity > 0.02;
      if (!c.group.visible) continue;
      // keep ships and camels readable from far away: they grow with camera distance, like icons on a game map
      const tmp = new THREE.Vector3();
      const unitLen = { fleet: 0.9, junks: 0.5, caravan: 0.12, barges: 0.3 }[c.kind];
      const grow = { fleet: 40, junks: 38, caravan: 9, barges: 30 }[c.kind];
      const lead = c.curve.getPointAt(Math.min(Math.max(c.t, 0.0005), 0.9995));
      const sLead = Math.max(1, tmp.copy(lead).sub(cam.position).length() / grow);
      c.units.forEach((u, i) => {
        const spacing = c.kind === "junks" ? 9 : unitLen * (c.kind === "caravan" ? 1.6 : 1.5) * sLead;
        let t = c.t - (i * spacing) / c.length;
        if (c.kind === "junks") t = (((c.t + i / c.units.length) % 1) + 1) % 1;
        t = Math.min(Math.max(t, 0.0005), 0.9995);
        const p = c.curve.getPointAt(t);
        const tan = c.curve.getTangentAt(t);
        // fleets sail in a loose formation, not single file
        const side = new THREE.Vector3(-tan.z, 0, tan.x);
        const lateral = c.kind === "fleet" ? ((i % 3) - 1) * 1.1 * sLead * 0.9 : c.kind === "junks" ? ((i % 2) - 0.5) * 3 : 0;
        p.addScaledVector(side, lateral);
        const d = tmp.copy(p).sub(cam.position).length();
        const s = Math.max(1, d / grow);
        const ground = this.world.heightAt(p.x, p.z);
        p.y = c.kind === "caravan" ? Math.max(ground, 0.03) : 0.03;
        u.position.copy(p);
        u.scale.setScalar(s * (c.kind === "fleet" && i === 0 ? 1.25 : 1));
        u.rotation.y = Math.atan2(tan.x, tan.z);
        u.visible = c.opacity > 0.02 && (c.kind !== "fleet" || t > 0.001);
      });
    }
  }
}

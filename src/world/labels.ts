import * as THREE from "three";
import type { Label } from "../story/steps";
import type { Projector } from "./geo";

interface Item {
  key: string;
  el: HTMLElement;
  pos: THREE.Vector3;
  kind: string;
  on: boolean;
  x: number;
  y: number;
}

const tmp = new THREE.Vector3();

/** HTML labels pinned to places on the map; they fade in and out as the story moves between steps. */
export class Labels {
  root: HTMLElement;
  items = new Map<string, Item>();
  proj: Projector;

  constructor(root: HTMLElement, proj: Projector) {
    this.root = root;
    this.proj = proj;
  }

  static key(l: Label) {
    return `${typeof l.at === "string" ? l.at : l.at.join(",")}|${l.text}|${l.sub ?? ""}`;
  }

  private make(l: Label): Item {
    const key = Labels.key(l);
    const kind = l.kind ?? "city";
    const el = document.createElement("div");
    el.className = `lbl lbl--${kind}`;
    el.dataset.dir = l.dir ?? (kind === "region" || kind === "sea" ? "c" : "e");
    el.innerHTML =
      kind === "region" || kind === "sea"
        ? `<span class="lbl-t">${l.text}</span>`
        : `<i class="lbl-dot"></i><span class="lbl-box"><span class="lbl-t">${l.text}</span>${l.sub ? `<span class="lbl-s">${l.sub}</span>` : ""}</span>`;
    this.root.appendChild(el);
    // labels float a little above the place so they do not sit on top of its landmark
    const lift = l.lift ?? (kind === "region" || kind === "sea" ? 1.5 : kind === "city" ? 0.9 : 0.6);
    return { key, el, pos: this.proj.place(l.at, lift), kind, on: false, x: -1e4, y: -1e4 };
  }

  /** Show exactly these labels (others fade out). */
  set(labels: Label[]) {
    const want = new Set(labels.map((l) => Labels.key(l)));
    for (const l of labels) {
      const k = Labels.key(l);
      if (!this.items.has(k)) this.items.set(k, this.make(l));
    }
    for (const it of this.items.values()) {
      const on = want.has(it.key);
      if (on !== it.on) {
        it.on = on;
        it.el.classList.toggle("is-on", on);
      }
    }
  }

  update(camera: THREE.PerspectiveCamera, w: number, h: number) {
    for (const it of this.items.values()) {
      if (!it.on && !it.el.classList.contains("is-on") && it.el.style.opacity === "0") continue;
      tmp.copy(it.pos).project(camera);
      const behind = tmp.z > 1 || tmp.z < -1;
      const x = (tmp.x * 0.5 + 0.5) * w;
      const y = (-tmp.y * 0.5 + 0.5) * h;
      const off = behind || x < -200 || x > w + 200 || y < -120 || y > h + 120;
      it.el.classList.toggle("is-off", off);
      if (off) continue;
      if (Math.abs(x - it.x) > 0.05 || Math.abs(y - it.y) > 0.05) {
        it.x = x;
        it.y = y;
        it.el.style.transform = `translate3d(${x.toFixed(1)}px, ${y.toFixed(1)}px, 0)`;
      }
    }
  }
}

import * as THREE from "three";

/* ==========================================================================
   Depth parallax for the Blender renders.
   Each scene ships a colour image + a depth map (from Blender's Mist pass).
   A full-screen shader displaces pixels by depth, so moving the pointer (or
   scrolling) makes near objects slide against far ones — a live 2.5D camera.
   WebGL contexts are created only near the viewport and disposed afterwards.
   ========================================================================== */

const VERT = /* glsl */ `
  varying vec2 vUv;
  void main() { vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }
`;

const FRAG = /* glsl */ `
  precision highp float;
  uniform sampler2D uImage;
  uniform sampler2D uDepth;
  uniform vec2 uMouse;      // -1..1, smoothed
  uniform float uStrength;  // max uv offset for the nearest pixels
  uniform float uFocus;     // depth that stays still
  uniform float uZoom;      // >1 = overscan so edges never show
  uniform vec2 uScale;      // cover-fit scale (uv space)
  uniform vec2 uOffset;     // cover-fit offset (uv space)
  uniform float uFade;      // 0..1 fade-in
  varying vec2 vUv;

  void main() {
    vec2 uv = vUv * uScale + uOffset;
    vec2 c = uOffset + uScale * 0.5;
    uv = c + (uv - c) / uZoom;
    // fixed-point iteration: find the source pixel whose displaced position lands here
    vec2 p = uv;
    for (int i = 0; i < 5; i++) {
      float d = texture2D(uDepth, p).r;
      p = uv - uMouse * (d - uFocus) * uStrength;
    }
    vec3 col = texture2D(uImage, clamp(p, vec2(0.001), vec2(0.999))).rgb;
    gl_FragColor = vec4(col * uFade, 1.0);
  }
`;

export interface SceneMeta {
  w: number;
  h: number;
  focal: [number, number];
  depthMean: number;
}

const pointer = { x: 0, y: 0, t: 0 };
let listening = false;
const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;

function listen() {
  if (listening) return;
  listening = true;
  window.addEventListener(
    "pointermove",
    (e) => {
      pointer.x = (e.clientX / innerWidth) * 2 - 1;
      pointer.y = -((e.clientY / innerHeight) * 2 - 1);
      pointer.t = performance.now();
    },
    { passive: true },
  );
}

function pickImageWidth(): number {
  const px = innerWidth * Math.min(devicePixelRatio || 1, 2);
  if (px <= 1100) return 960;
  if (px <= 1900) return 1600;
  return 2560;
}

const loader = new THREE.TextureLoader();

export class DepthScene {
  el: HTMLElement;
  canvas: HTMLCanvasElement;
  slug: string;
  meta: SceneMeta;
  renderer?: THREE.WebGLRenderer;
  material?: THREE.ShaderMaterial;
  scene?: THREE.Scene;
  camera?: THREE.Camera;
  textures: THREE.Texture[] = [];
  alive = false;
  visible = false;
  progress = 0.5; // scroll progress through the section (0 entering .. 1 leaving)
  mouse = new THREE.Vector2();
  raf = 0;
  strength: number;
  private ro?: ResizeObserver;

  constructor(el: HTMLElement, meta: SceneMeta, opts: { strength?: number } = {}) {
    this.el = el;
    this.canvas = el.querySelector("canvas.scene-gl") as HTMLCanvasElement;
    this.slug = el.dataset.scene!;
    this.meta = meta;
    this.strength = opts.strength ?? 0.03;
    el.style.setProperty("--fx", `${meta.focal[0] * 100}%`);
    el.style.setProperty("--fy", `${meta.focal[1] * 100}%`);
    listen();
  }

  async init() {
    if (this.alive || reduced) return;
    this.alive = true;
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ canvas: this.canvas, antialias: false, alpha: false, powerPreference: "high-performance" });
    } catch {
      this.alive = false;
      return; // WebGL unavailable: the <img> fallback stays visible
    }
    renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 1.75));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer = renderer;
    const w = pickImageWidth();
    const [img, depth] = await Promise.all([
      loader.loadAsync(`scenes/${this.slug}-${w}.webp`),
      loader.loadAsync(`scenes/${this.slug}-depth.webp`),
    ]);
    if (!this.alive) {
      img.dispose();
      depth.dispose();
      return;
    }
    // ShaderMaterial output is not colour-managed: sample the sRGB bytes as-is
    img.colorSpace = THREE.NoColorSpace;
    img.minFilter = THREE.LinearFilter;
    img.generateMipmaps = false;
    depth.colorSpace = THREE.NoColorSpace;
    depth.minFilter = THREE.LinearFilter;
    depth.generateMipmaps = false;
    this.textures = [img, depth];
    this.material = new THREE.ShaderMaterial({
      vertexShader: VERT,
      fragmentShader: FRAG,
      uniforms: {
        uImage: { value: img },
        uDepth: { value: depth },
        uMouse: { value: new THREE.Vector2() },
        uStrength: { value: this.strength },
        uFocus: { value: Math.min(0.75, Math.max(0.2, this.meta.depthMean)) },
        uZoom: { value: 1.08 },
        uScale: { value: new THREE.Vector2(1, 1) },
        uOffset: { value: new THREE.Vector2(0, 0) },
        uFade: { value: 0 },
      },
      depthTest: false,
      depthWrite: false,
    });
    this.scene = new THREE.Scene();
    this.scene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), this.material));
    this.camera = new THREE.Camera();
    this.resize();
    this.ro = new ResizeObserver(() => this.resize());
    this.ro.observe(this.el);
    this.el.classList.add("gl-ready");
    const start = performance.now();
    const tick = (now: number) => {
      if (!this.alive) return;
      this.raf = requestAnimationFrame(tick);
      if (!this.visible) return;
      const u = this.material!.uniforms;
      u.uFade.value = Math.min(1, (now - start) / 900);
      // idle drift when the pointer has been still for a while
      const idle = now - pointer.t > 2500;
      const tx = idle ? Math.sin(now / 5200) * 0.55 : pointer.x;
      const ty = (idle ? Math.cos(now / 6700) * 0.35 : pointer.y) + (this.progress - 0.5) * 0.9;
      this.mouse.x += (tx - this.mouse.x) * 0.045;
      this.mouse.y += (ty - this.mouse.y) * 0.045;
      u.uMouse.value.copy(this.mouse);
      u.uZoom.value = 1.1 - 0.05 * this.progress;
      this.renderer!.render(this.scene!, this.camera!);
    };
    this.raf = requestAnimationFrame(tick);
  }

  resize() {
    if (!this.renderer || !this.material) return;
    const r = this.el.getBoundingClientRect();
    const w = Math.max(1, Math.round(r.width));
    const h = Math.max(1, Math.round(r.height));
    this.renderer.setSize(w, h, false);
    const imgA = this.meta.w / this.meta.h;
    const canA = w / h;
    const [fx, fy] = this.meta.focal;
    const s = new THREE.Vector2(1, 1);
    const o = new THREE.Vector2(0, 0);
    if (canA > imgA) {
      s.y = imgA / canA;
      o.y = Math.min(Math.max(1 - fy - s.y / 2, 0), 1 - s.y);
    } else {
      s.x = canA / imgA;
      o.x = Math.min(Math.max(fx - s.x / 2, 0), 1 - s.x);
    }
    this.material.uniforms.uScale.value.copy(s);
    this.material.uniforms.uOffset.value.copy(o);
    // narrow screens get less displacement (the crop already magnifies)
    this.material.uniforms.uStrength.value = this.strength * (canA < 1 ? 0.6 : 1);
  }

  dispose() {
    if (!this.alive) return;
    this.alive = false;
    cancelAnimationFrame(this.raf);
    this.ro?.disconnect();
    this.textures.forEach((t) => t.dispose());
    this.material?.dispose();
    this.renderer?.dispose();
    this.renderer?.forceContextLoss();
    this.renderer = undefined;
    this.el.classList.remove("gl-ready");
  }
}

/** Manage all scenes: create near the viewport, dispose when far away. */
export function mountScenes(manifest: Record<string, SceneMeta>): DepthScene[] {
  const scenes: DepthScene[] = [];
  document.querySelectorAll<HTMLElement>(".scene[data-scene]").forEach((el) => {
    const meta = manifest[el.dataset.scene!];
    if (!meta) return;
    const s = new DepthScene(el, meta, { strength: el.classList.contains("hero") ? 0.034 : 0.028 });
    scenes.push(s);
  });
  const near = new IntersectionObserver(
    (entries) => {
      for (const e of entries) {
        const s = scenes.find((x) => x.el === e.target);
        if (!s) continue;
        if (e.isIntersecting) s.init();
        else s.dispose();
      }
    },
    { rootMargin: "120% 0px 120% 0px" },
  );
  const vis = new IntersectionObserver(
    (entries) => {
      for (const e of entries) {
        const s = scenes.find((x) => x.el === e.target);
        if (s) s.visible = e.isIntersecting;
      }
    },
    { rootMargin: "0px" },
  );
  scenes.forEach((s) => {
    near.observe(s.el);
    vis.observe(s.el);
  });
  return scenes;
}

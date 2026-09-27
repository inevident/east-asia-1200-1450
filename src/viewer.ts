import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { DRACOLoader } from "three/addons/loaders/DRACOLoader.js";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";

/* ==========================================================================
   Interactive artifacts exported from Blender (.glb, Draco-compressed).
   Empties named "hotspot_*" in each file anchor the annotation markers.
   ========================================================================== */

type Kind = "junk" | "vase" | "compass";

const FILES: Record<Kind, string> = {
  junk: "models/junk_cutaway.glb",
  vase: "models/meiping_vase.glb",
  compass: "models/water_compass.glb",
};

const HOTSPOTS: Record<Kind, Record<string, { title: string; text: string }>> = {
  junk: {
    bulkheads: {
      title: "Watertight bulkheads",
      text: "Transverse walls split the hull into sealed compartments, so a leak floods one hold instead of the whole ship. Song shipwrights used them to improve buoyancy and protect cargo.",
    },
    rudder: {
      title: "Stern-post rudder",
      text: "Mounted on the centerline at the stern and raised or lowered with the depth of the water, it let pilots steer through crowded harbors, narrow channels and river rapids.",
    },
    sails: {
      title: "Battened lug sails",
      text: "Bamboo battens stiffen the matting sails so they hold their shape, can be reefed in moments, and keep working even with a torn panel. They suited long monsoon passages.",
    },
    compass: {
      title: "Compass station",
      text: "By 1119, Chinese pilots were steering by a magnetized needle, holding their course under cloud and far out of sight of land.",
    },
    cargo: {
      title: "Cargo holds",
      text: "Porcelain packed in crates, bolts of silk and iron goods went out. Spices, incense and ivory came back across the Indian Ocean.",
    },
    keel: {
      title: "Keel & V-shaped hull",
      text: "Seagoing Fujian junks had deep, keeled hulls for open-sea swells, unlike the flat-bottomed boats of China’s rivers and canals.",
    },
  },
  vase: {
    cobalt: {
      title: "Persian cobalt",
      text: "The blue is cobalt, much of it imported from Persia along routes the Mongols kept open. Painters applied it to raw porcelain before it was glazed and fired at Jingdezhen.",
    },
    lappets: {
      title: "Cloud-collar lappets",
      text: "Pointed “cloud collar” panels ring the shoulder. The motif also appears on Mongol-era textiles and metalwork across Eurasia.",
    },
    lotus: {
      title: "Lotus panels",
      text: "Tall lotus-petal panels, a Buddhist emblem of purity, circle the lower body of many Yuan blue-and-white wares.",
    },
  },
  compass: {
    needle: {
      title: "The floating needle",
      text: "A magnetized iron needle, pushed through a sliver of reed, floats on water and swings to the north–south line. Its red tip marks south: the Chinese name for the compass means “south-pointer” (指南).",
    },
    directions: {
      title: "Twenty-four directions",
      text: "The outer ring divides the horizon into 24 bearings (12 earthly branches, 8 heavenly stems and 4 trigrams), so a pilot could hold a course to within 15°.",
    },
    trigrams: {
      title: "Eight trigrams",
      text: "The inner rings carry the eight trigrams of the <i>Yijing</i> (Book of Changes). Cosmology and navigation shared a single instrument.",
    },
  },
};

let draco: DRACOLoader | null = null;
function gltfLoader() {
  const l = new GLTFLoader();
  if (!draco) {
    draco = new DRACOLoader();
    draco.setDecoderPath("draco/");
  }
  l.setDRACOLoader(draco);
  return l;
}

export class ArtifactViewer {
  fig: HTMLElement;
  stage: HTMLElement;
  kind: Kind;
  renderer?: THREE.WebGLRenderer;
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(32, 1, 0.01, 200);
  controls?: OrbitControls;
  model?: THREE.Object3D;
  spots: { key: string; obj: THREE.Object3D; btn: HTMLButtonElement }[] = [];
  card?: HTMLElement;
  alive = false;
  visible = false;
  raf = 0;
  ro?: ResizeObserver;
  raycaster = new THREE.Raycaster();
  frame = 0;
  // compass-specific
  board?: THREE.Group;
  needle?: THREE.Group;
  needleAngle = 0;
  needleVel = 0;

  constructor(fig: HTMLElement) {
    this.fig = fig;
    this.stage = fig.querySelector(".artifact-stage") as HTMLElement;
    this.kind = fig.dataset.artifact as Kind;
  }

  async init() {
    if (this.alive) return;
    this.alive = true;
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
    } catch {
      this.stage.querySelector(".artifact-loading")!.textContent = "3D view unavailable on this device";
      this.alive = false;
      return;
    }
    renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = this.kind === "vase" ? 1.05 : 1.15;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFShadowMap;
    this.renderer = renderer;
    this.stage.appendChild(renderer.domElement);
    renderer.domElement.setAttribute("aria-label", `Interactive 3D model: ${this.fig.querySelector("h4")?.textContent ?? ""}`);
    renderer.domElement.setAttribute("role", "img");

    const pmrem = new THREE.PMREMGenerator(renderer);
    this.scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    pmrem.dispose();

    const key = new THREE.DirectionalLight(0xfff1dc, 2.4);
    key.position.set(3, 5, 4);
    key.castShadow = true;
    key.shadow.mapSize.set(1024, 1024);
    key.shadow.radius = 6;
    this.scene.add(key, new THREE.HemisphereLight(0xf4e9d8, 0x2a2118, 0.55));

    const gltf = await gltfLoader().loadAsync(FILES[this.kind]);
    if (!this.alive) return;
    const model = gltf.scene;
    model.traverse((o) => {
      const m = o as THREE.Mesh;
      if (m.isMesh) {
        m.castShadow = true;
        m.receiveShadow = true;
        const mat = m.material as THREE.MeshStandardMaterial;
        if (mat && "envMapIntensity" in mat) mat.envMapIntensity = this.kind === "junk" ? 0.8 : 1.0;
        if (mat) mat.side = THREE.DoubleSide;
      }
    });
    // normalise size and sit the model on y = 0
    const box = new THREE.Box3().setFromObject(model);
    const size = box.getSize(new THREE.Vector3());
    const s = (this.kind === "junk" ? 4.2 : 1.6) / Math.max(size.x, size.y, size.z);
    model.scale.setScalar(s);
    box.setFromObject(model);
    const c = box.getCenter(new THREE.Vector3());
    model.position.sub(new THREE.Vector3(c.x, box.min.y, c.z));
    this.model = model;

    if (this.kind === "compass") this.setupCompass(model);
    else this.scene.add(model);

    // soft ground shadow
    const ground = new THREE.Mesh(new THREE.PlaneGeometry(20, 20), new THREE.ShadowMaterial({ opacity: 0.35 }));
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.001;
    ground.receiveShadow = true;
    this.scene.add(ground);
    key.target.position.set(0, 0, 0);
    const b2 = new THREE.Box3().setFromObject(model);
    const r = b2.getSize(new THREE.Vector3()).length() / 2;
    key.shadow.camera.left = key.shadow.camera.bottom = -r * 1.5;
    key.shadow.camera.right = key.shadow.camera.top = r * 1.5;
    key.shadow.camera.far = 40;

    const target = b2.getCenter(new THREE.Vector3());
    const controls = new OrbitControls(this.camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.enablePan = false;
    controls.target.copy(target);
    // distance at which the model's bounding sphere fits the (narrower) field of view
    const aspect = Math.max(0.5, this.stage.clientWidth / Math.max(1, this.stage.clientHeight));
    const vfov = THREE.MathUtils.degToRad(this.camera.fov);
    const hfov = 2 * Math.atan(Math.tan(vfov / 2) * aspect);
    const fit = r / Math.sin(Math.min(vfov, hfov) / 2);
    const place = (dir: THREE.Vector3, k: number) => this.camera.position.copy(target).addScaledVector(dir.normalize(), fit * k);
    if (this.kind === "junk") {
      // Blender +Y (the cut, open side) exports to -Z in glTF: start on that side
      place(new THREE.Vector3(0.55, 0.28, -1), 0.9);
      controls.minDistance = fit * 0.35;
      controls.maxDistance = fit * 1.6;
      controls.maxPolarAngle = Math.PI * 0.62;
    } else if (this.kind === "vase") {
      place(new THREE.Vector3(0, 0.18, 1), 0.95);
      controls.autoRotate = true;
      controls.autoRotateSpeed = 1.1;
      controls.minDistance = fit * 0.5;
      controls.maxDistance = fit * 1.6;
    } else {
      place(new THREE.Vector3(0, 1.15, 0.8), 0.92);
      controls.enableRotate = false; // dragging turns the board instead
      controls.minDistance = fit * 0.45;
      controls.maxDistance = fit * 1.5;
    }
    this.camera.lookAt(target);
    controls.update();
    this.controls = controls;

    // hotspots
    const defs = HOTSPOTS[this.kind];
    let i = 0;
    model.traverse((o) => {
      const m = o.name.match(/^hotspot_(.+)$/);
      if (!m || !defs[m[1]]) return;
      i++;
      const btn = document.createElement("button");
      btn.className = "hotspot";
      btn.type = "button";
      btn.textContent = String(i);
      btn.setAttribute("aria-label", defs[m[1]].title);
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        this.openCard(m[1], btn);
      });
      this.stage.appendChild(btn);
      this.spots.push({ key: m[1], obj: o, btn });
    });

    this.stage.querySelector(".artifact-loading")?.remove();
    this.resize();
    this.ro = new ResizeObserver(() => this.resize());
    this.ro.observe(this.stage);
    const tick = () => {
      if (!this.alive) return;
      this.raf = requestAnimationFrame(tick);
      if (!this.visible) return;
      this.update();
    };
    this.raf = requestAnimationFrame(tick);
  }

  setupCompass(model: THREE.Object3D) {
    // split the model: the needle floats (keeps pointing N–S), the board turns under it
    this.board = new THREE.Group();
    this.needle = new THREE.Group();
    const needleParts: THREE.Object3D[] = [];
    model.traverse((o) => {
      if (/compass_(needle|reed|south_tip)|hotspot_needle/.test(o.name)) needleParts.push(o);
    });
    this.scene.add(this.board, this.needle);
    this.board.add(model);
    model.updateMatrixWorld(true);
    for (const p of needleParts) this.needle.attach(p);
    const dom = this.renderer!.domElement;
    let dragging = false;
    let lastX = 0;
    dom.addEventListener("pointerdown", (e) => {
      dragging = true;
      lastX = e.clientX;
      dom.setPointerCapture(e.pointerId);
    });
    dom.addEventListener("pointermove", (e) => {
      if (!dragging) return;
      const dx = e.clientX - lastX;
      lastX = e.clientX;
      this.board!.rotation.y += dx * 0.012;
      // the water drags the needle a little with the bowl
      this.needleVel += dx * 0.0035;
    });
    const up = () => (dragging = false);
    dom.addEventListener("pointerup", up);
    dom.addEventListener("pointercancel", up);
  }

  openCard(key: string, btn: HTMLButtonElement) {
    const def = HOTSPOTS[this.kind][key];
    this.spots.forEach((s) => s.btn.classList.toggle("is-open", s.btn === btn));
    if (!this.card) {
      this.card = document.createElement("div");
      this.card.className = "hotspot-card";
      this.stage.appendChild(this.card);
    }
    this.card.innerHTML = `<button type="button" aria-label="Close">×</button><h5>${def.title}</h5><p>${def.text}</p>`;
    this.card.querySelector("button")!.addEventListener("click", () => {
      this.card?.remove();
      this.card = undefined;
      this.spots.forEach((s) => s.btn.classList.remove("is-open"));
    });
  }

  resize() {
    if (!this.renderer) return;
    const w = this.stage.clientWidth;
    const h = this.stage.clientHeight;
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
  }

  update() {
    this.frame++;
    if (this.needle) {
      // damped spring back to north–south (world orientation 0)
      this.needleVel += -this.needleAngle * 0.02;
      this.needleVel *= 0.94;
      this.needleAngle += this.needleVel;
      this.needle.rotation.y = this.needleAngle + Math.sin(performance.now() / 900) * 0.01;
    }
    this.controls?.update();
    this.renderer!.render(this.scene, this.camera);
    // position hotspot buttons
    const w = this.stage.clientWidth;
    const h = this.stage.clientHeight;
    const v = new THREE.Vector3();
    for (const s of this.spots) {
      s.obj.getWorldPosition(v);
      const dist = v.distanceTo(this.camera.position);
      v.project(this.camera);
      const x = (v.x * 0.5 + 0.5) * w;
      const y = (-v.y * 0.5 + 0.5) * h;
      s.btn.style.transform = `translate(${x}px, ${y}px)`;
      if (this.frame % 10 === 0 && this.model) {
        // dim markers hidden behind the model
        const p = new THREE.Vector3();
        s.obj.getWorldPosition(p);
        this.raycaster.set(this.camera.position, p.clone().sub(this.camera.position).normalize());
        const hit = this.raycaster.intersectObject(this.model, true)[0];
        s.btn.classList.toggle("is-hidden", !!hit && hit.distance < dist - 0.05);
      }
    }
  }

  dispose() {
    if (!this.alive) return;
    this.alive = false;
    cancelAnimationFrame(this.raf);
    this.ro?.disconnect();
    this.spots.forEach((s) => s.btn.remove());
    this.spots = [];
    this.card?.remove();
    this.card = undefined;
    this.controls?.dispose();
    this.scene.traverse((o) => {
      const m = o as THREE.Mesh;
      if (m.isMesh) {
        m.geometry.dispose();
        const mats = Array.isArray(m.material) ? m.material : [m.material];
        mats.forEach((mt) => {
          Object.values(mt).forEach((val) => (val instanceof THREE.Texture ? val.dispose() : null));
          mt.dispose();
        });
      }
    });
    this.scene.environment?.dispose();
    this.scene = new THREE.Scene();
    this.renderer?.domElement.remove();
    this.renderer?.dispose();
    this.renderer = undefined;
    this.board = this.needle = undefined;
    if (!this.stage.querySelector(".artifact-loading")) {
      const l = document.createElement("div");
      l.className = "artifact-loading";
      l.textContent = "Loading 3D model…";
      this.stage.prepend(l);
    }
  }
}

export function mountArtifacts() {
  const viewers = [...document.querySelectorAll<HTMLElement>(".artifact[data-artifact]")].map((f) => new ArtifactViewer(f));
  const near = new IntersectionObserver(
    (entries) =>
      entries.forEach((e) => {
        const v = viewers.find((x) => x.fig === e.target);
        if (!v) return;
        if (e.isIntersecting) v.init();
        else v.dispose();
      }),
    { rootMargin: "80% 0px 80% 0px" },
  );
  const vis = new IntersectionObserver((entries) =>
    entries.forEach((e) => {
      const v = viewers.find((x) => x.fig === e.target);
      if (v) v.visible = e.isIntersecting;
    }),
  );
  viewers.forEach((v) => {
    near.observe(v.fig);
    vis.observe(v.fig);
  });
}

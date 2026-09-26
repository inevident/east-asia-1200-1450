import * as THREE from "three";
import { makeTerrain, makeSky, type Geo, type Terrain } from "./terrain";
import type { Landmarks } from "./landmarks";
import { makePost, type Post } from "./post";

export const SKY = new THREE.Color("#e9e0cd");
const SUN_DIR = new THREE.Vector3(-560, 720, 420).normalize(); // from the south-west: lit faces turn toward the (north-looking) camera
const ZENITH = new THREE.Color("#dfe3d8");

export interface World {
  renderer: THREE.WebGLRenderer;
  scene: THREE.Scene;
  camera: THREE.PerspectiveCamera;
  geo: Geo;
  terrain: Terrain;
  heightAt: (x: number, z: number) => number;
  sun: THREE.DirectionalLight;
  clock: THREE.Timer;
  onFrame: ((dt: number, t: number) => void)[];
  quality: "high" | "low";
  render: () => void;
  /** skip drawing while the page's appendix covers the map */
  paused: boolean;
  /** something is moving (scroll, camera, a route drawing): draw every frame; otherwise idle at a low rate */
  busy: boolean;
  /** the opening painting still hides the map: only keep it warm */
  covered: boolean;
  /** frames actually drawn (for checking the idle behaviour) */
  drawn: number;
  /** what the camera is looking at, and from how far (set by the story director) */
  focus: THREE.Vector3;
  focusDist: number;
  landmarks?: Landmarks;
  post?: Post;
}

/** Create the renderer, sky, lights and the painted relief map. */
export async function createWorld(canvas: HTMLCanvasElement, onProgress?: (f: number) => void): Promise<World> {
  const nav = navigator as Navigator & { deviceMemory?: number };
  const small = Math.min(innerWidth, innerHeight) < 700 || (nav.deviceMemory !== undefined && nav.deviceMemory <= 4);
  const quality: "high" | "low" = small ? "low" : "high";
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: "high-performance" });
  renderer.setPixelRatio(Math.min(devicePixelRatio || 1, quality === "high" ? 1.75 : 1.5));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.NeutralToneMapping;
  renderer.toneMappingExposure = 1.05;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFShadowMap;

  const scene = new THREE.Scene();
  scene.background = SKY.clone();
  scene.fog = new THREE.Fog(SKY.clone(), 400, 2200);

  const camera = new THREE.PerspectiveCamera(34, innerWidth / innerHeight, 0.2, 9000);
  camera.position.set(0, 900, 700);
  camera.lookAt(0, 0, 0);

  onProgress?.(0.05);
  const geo: Geo = await fetch("map/geo.json").then((r) => r.json());
  // shift everything so the map is centred on the origin
  const [cx, cy] = geo.center;
  const shift = (p: [number, number, number]) => [p[0] - cx, p[1], p[2] + cy] as [number, number, number];
  for (const k of Object.keys(geo.anchors)) geo.anchors[k] = shift(geo.anchors[k]);
  for (const k of Object.keys(geo.routes)) geo.routes[k] = geo.routes[k].map(shift);
  onProgress?.(0.15);

  const terrain = await makeTerrain(geo, quality, SKY);
  scene.add(terrain.group);
  const sky = makeSky(SKY, ZENITH);
  scene.add(sky);
  onProgress?.(0.8);

  const hemi = new THREE.HemisphereLight("#fff6e8", "#7d6b50", 1.15);
  scene.add(hemi);
  const sun = new THREE.DirectionalLight("#fff0d8", 2.1);
  sun.position.copy(SUN_DIR).multiplyScalar(900); // matches the painted hillshade in the colour map
  sun.castShadow = true;
  sun.shadow.mapSize.set(quality === "high" ? 2048 : 1024, quality === "high" ? 2048 : 1024);
  sun.shadow.bias = -0.0005;
  sun.shadow.normalBias = 0.01;
  scene.add(sun, sun.target);
  // a soft sky-and-ground environment so glazed roofs, gold leaf and water pick up gentle reflections
  const pmrem = new THREE.PMREMGenerator(renderer);
  const envScene = new THREE.Scene();
  const envSphere = new THREE.Mesh(
    new THREE.SphereGeometry(10, 32, 16),
    new THREE.ShaderMaterial({
      side: THREE.BackSide,
      uniforms: { top: { value: new THREE.Color("#f4efe4") }, mid: { value: SKY.clone() }, bot: { value: new THREE.Color("#8f7f62") } },
      vertexShader: "varying vec3 vP; void main(){ vP = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }",
      fragmentShader:
        "uniform vec3 top, mid, bot; varying vec3 vP; void main(){ float y = vP.y; vec3 c = y > 0.0 ? mix(mid, top, smoothstep(0.0, 0.7, y)) : mix(mid, bot, smoothstep(0.0, 0.4, -y)); gl_FragColor = vec4(c, 1.0); }",
    }),
  );
  envScene.add(envSphere);
  scene.environment = pmrem.fromScene(envScene, 0.02).texture;
  scene.environmentIntensity = 0.45;

  // tilt-shift post-processing on capable devices; phones render straight to the screen
  const post = quality === "high" && renderer.capabilities.isWebGL2 ? makePost(renderer, scene, camera) : undefined;
  if (post) {
    // everything is tone-mapped once, at the end, so the water's haze colour stays in linear space
    const sw = (terrain.water.material as THREE.ShaderMaterial).uniforms.uSkyOut.value as THREE.Vector3;
    sw.set(SKY.r, SKY.g, SKY.b);
  }

  const world: World = {
    renderer,
    scene,
    camera,
    geo,
    terrain,
    heightAt: terrain.heightAt,
    sun,
    clock: new THREE.Timer(),
    onFrame: [],
    quality,
    render: () => (post ? post.composer.render() : renderer.render(scene, camera)),
    post,
    paused: false,
    busy: true,
    covered: false,
    drawn: 0,
    focus: new THREE.Vector3(),
    focusDist: 1000,
  };
  const resize = () => {
    const w = canvas.clientWidth || innerWidth;
    const h = canvas.clientHeight || innerHeight;
    renderer.setSize(w, h, false);
    post?.setSize(w, h);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  };
  resize();
  new ResizeObserver(resize).observe(canvas);
  world.onFrame.push(() => sky.position.copy(camera.position));
  return world;
}

/** Advance per-frame state (water, fog, callbacks) and draw one frame. */
export function frame(world: World, dt: number) {
  const { scene, camera } = world;
  const t = world.clock.getElapsed();
  (world.terrain.water.material as THREE.ShaderMaterial).uniforms.uTime.value = t;
  for (const f of world.onFrame) f(dt, t);
  // the sun's shadow box follows whatever the camera is looking at; shadows only matter up close
  const focus = world.focus;
  const span = Math.min(Math.max(world.focusDist * 0.75, 6), 90);
  const sun = world.sun;
  sun.target.position.copy(focus);
  sun.position.copy(focus).add(SUN_DIR.clone().multiplyScalar(300));
  const sc = sun.shadow.camera;
  if (sc.right !== span) {
    sc.left = -span;
    sc.right = span;
    sc.top = span;
    sc.bottom = -span;
    sc.near = 1;
    sc.far = 700;
    sc.updateProjectionMatrix();
  }
  // miniature look: sharp around what the camera looks at, soft above and below, only for close-ups
  if (world.post) {
    const p = focus.clone().project(camera);
    world.post.setFocus(p.y * 0.5 + 0.5, 7 * (1 - THREE.MathUtils.smoothstep(world.focusDist, 12, 90)));
  }
  // fog scales with viewing distance so close-ups stay crisp and overviews fade softly
  const d = Math.max(camera.position.y, 1);
  const fog = scene.fog as THREE.Fog;
  fog.near = d * 1.1 + 30;
  fog.far = d * 4.5 + 500;
  world.render();
  world.drawn++;
}

/**
 * Draw at full rate only while something moves. When the view is still, the water and ships keep drifting at a
 * gentle 12 fps so the GPU can rest; behind the opening painting or the appendix, drawing (nearly) stops.
 */
export function startLoop(world: World) {
  let last = -1e9;
  const tick = (now: number) => {
    requestAnimationFrame(tick);
    if (world.paused) return;
    const gap = world.covered ? 1000 : world.busy ? 0 : 1000 / 12;
    if (now - last < gap - 2) return;
    last = now;
    world.clock.update(now);
    frame(world, Math.min(world.clock.getDelta(), 0.1));
  };
  requestAnimationFrame(tick);
}

import * as THREE from "three";

type Rect = [number, number, number, number];
export interface Tile {
  rect: Rect;
  seg: [number, number];
}
export interface Geo {
  extent: Rect;
  size: [number, number];
  center: [number, number];
  height: { min: number; max: number; exag: number };
  tiles: { global: Tile; ea: Tile };
  border: number;
  projection: Record<string, number>;
  anchors: Record<string, [number, number, number]>;
  routes: Record<string, [number, number, number][]>;
}

/** A decoded height grid (vertex nodes, row 0 = north) that both the GPU and the CPU read. */
interface HeightGrid {
  tile: Tile;
  /** world-space rectangle: x0, z0 (north), x1, z1 (south) */
  box: Rect;
  w: number;
  h: number;
  data: Float32Array;
  tex: THREE.DataTexture;
}

const loader = new THREE.TextureLoader();

/** A colour's components in sRGB output space (what the fog and the clear colour use). */
function srgb(c: THREE.Color) {
  const o = { r: 0, g: 0, b: 0 };
  c.getRGB(o, THREE.SRGBColorSpace);
  return new THREE.Vector3(o.r, o.g, o.b);
}

function tex(url: string, srgb: boolean, aniso = 8) {
  return loader.loadAsync(url).then((t) => {
    t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace;
    t.anisotropy = aniso;
    return t;
  });
}

async function loadHeights(url: string, geo: Geo, tile: Tile): Promise<HeightGrid> {
  const blob = await fetch(url).then((r) => r.blob());
  const bmp = await createImageBitmap(blob, { colorSpaceConversion: "none", premultiplyAlpha: "none" });
  const cv = document.createElement("canvas");
  cv.width = bmp.width;
  cv.height = bmp.height;
  const ctx = cv.getContext("2d", { willReadFrequently: true })!;
  ctx.drawImage(bmp, 0, 0);
  const px = ctx.getImageData(0, 0, bmp.width, bmp.height).data;
  const { min, max } = geo.height;
  const data = new Float32Array(bmp.width * bmp.height);
  for (let i = 0; i < data.length; i++) {
    const v = px[i * 4] * 16 + (px[i * 4 + 1] >> 4);
    data[i] = min + (v / 4095) * (max - min);
  }
  const t = new THREE.DataTexture(data, bmp.width, bmp.height, THREE.RedFormat, THREE.FloatType);
  t.minFilter = t.magFilter = THREE.NearestFilter;
  t.generateMipmaps = false;
  t.needsUpdate = true;
  const [cx, cy] = geo.center;
  const [x0, y0, x1, y1] = tile.rect;
  return { tile, box: [x0 - cx, cy - y1, x1 - cx, cy - y0], w: bmp.width, h: bmp.height, data, tex: t };
}

/** Terrain height under a world-space point, matching the rendered triangles exactly. */
export function makeHeightSampler(grids: HeightGrid[], lowRes: boolean) {
  return (x: number, z: number): number => {
    for (const g of grids) {
      const [x0, z0, x1, z1] = g.box;
      if (x <= x0 + 0.01 || x >= x1 - 0.01 || z <= z0 + 0.01 || z >= z1 - 0.01) continue;
      const step = lowRes ? 2 : 1;
      const sx = g.tile.seg[0] / step;
      const sy = g.tile.seg[1] / step;
      const fx = ((x - x0) / (x1 - x0)) * sx;
      const fy = ((z - z0) / (z1 - z0)) * sy;
      const ix = Math.min(Math.floor(fx), sx - 1);
      const iy = Math.min(Math.floor(fy), sy - 1);
      const tx = fx - ix;
      const ty = fy - iy;
      const at = (i: number, j: number) => g.data[j * step * g.w + i * step];
      const a = at(ix, iy), b = at(ix, iy + 1), c = at(ix + 1, iy + 1), d = at(ix + 1, iy);
      // PlaneGeometry splits each quad into (a, b, d) and (b, c, d)
      return tx + ty <= 1 ? a + (d - a) * tx + (b - a) * ty : c + (b - c) * (1 - tx) + (d - c) * (1 - ty);
    }
    return 0;
  };
}

const DETAIL_GLSL = /* glsl */ `
  float dh(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
  float dn(vec2 p) {
    vec2 i = floor(p), f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(mix(dh(i), dh(i + vec2(1, 0)), u.x), mix(dh(i + vec2(0, 1)), dh(i + vec2(1, 1)), u.x), u.y);
  }
  // stippled tree crowns: one jittered dot per cell
  float crowns(vec2 p) {
    vec2 i = floor(p), f = fract(p);
    float d = 1.0;
    for (int y = -1; y <= 1; y++) for (int x = -1; x <= 1; x++) {
      vec2 o = vec2(float(x), float(y));
      vec2 r = o + vec2(dh(i + o), dh(i + o + 17.3)) * 0.8 + 0.1 - f;
      float sz = 0.6 + 0.6 * dh(i + o + 3.9);
      d = min(d, dot(r, r) / (sz * sz));
    }
    return 1.0 - smoothstep(0.06, 0.2, d);
  }
`;

/**
 * One tile of the painted relief: vertex heights come from a 12-bit height grid sampled exactly at vertex nodes,
 * shading from a world-space normal map, plus hand-painted-looking detail that fades in close to the camera.
 */
function makeTile(grid: HeightGrid, color: THREE.Texture, normal: THREE.Texture, lowRes: boolean, hole?: Rect) {
  const [x0, z0, x1, z1] = grid.box;
  const step = lowRes ? 2 : 1;
  const geom = new THREE.PlaneGeometry(x1 - x0, z1 - z0, grid.tile.seg[0] / step, grid.tile.seg[1] / step);
  geom.rotateX(-Math.PI / 2);
  geom.translate((x0 + x1) / 2, 0, (z0 + z1) / 2);
  // generous bounds so frustum culling never drops a displaced tile
  geom.boundingSphere = new THREE.Sphere(new THREE.Vector3((x0 + x1) / 2, 0, (z0 + z1) / 2), Math.hypot(x1 - x0, z1 - z0) / 2 + 30);
  const mat = new THREE.MeshStandardMaterial({ map: color, normalMap: normal, roughness: 0.95, metalness: 0 });
  const uniforms = {
    uHeight: { value: grid.tex },
    uSeg: { value: new THREE.Vector2(grid.tile.seg[0], grid.tile.seg[1]) },
    uHole: { value: new THREE.Vector4(...(hole ?? [1e9, 1e9, -1e9, -1e9])) },
    uNormalStrength: { value: 1.0 },
    uDetail: { value: 1 },
  };
  mat.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, uniforms);
    sh.vertexShader = sh.vertexShader
      .replace(
        "#include <common>",
        `#include <common>
        uniform sampler2D uHeight; uniform vec2 uSeg; varying vec3 vWPos;`,
      )
      .replace(
        "#include <begin_vertex>",
        `#include <begin_vertex>
        vec2 huv = vec2((uv.x * uSeg.x + 0.5) / (uSeg.x + 1.0), ((1.0 - uv.y) * uSeg.y + 0.5) / (uSeg.y + 1.0));
        transformed.y += texture2D(uHeight, huv).r;
        vWPos = (modelMatrix * vec4(transformed, 1.0)).xyz;`,
      );
    sh.fragmentShader = sh.fragmentShader
      .replace(
        "#include <common>",
        `#include <common>
        uniform vec4 uHole; uniform float uNormalStrength, uDetail; varying vec3 vWPos;
        ${DETAIL_GLSL}`,
      )
      .replace(
        "#include <clipping_planes_fragment>",
        `#include <clipping_planes_fragment>
        if (vWPos.x > uHole.x && vWPos.x < uHole.z && vWPos.z > uHole.y && vWPos.z < uHole.w) discard;`,
      )
      .replace(
        "#include <map_fragment>",
        `#include <map_fragment>
        diffuseColor.a = 1.0;
        {
          vec3 nm = texture2D(normalMap, vNormalMapUv).xyz;
          vec2 nxy = nm.xy * 2.0 - 1.0;
          float slope = 1.0 - sqrt(max(0.0, 1.0 - dot(nxy, nxy)));
          float farm = nm.z;
          float camD = length(cameraPosition - vWPos);
          float near = (1.0 - smoothstep(25.0, 150.0, camD)) * uDetail;
          if (near > 0.001) {
            vec3 c = diffuseColor.rgb;
            vec2 p = vWPos.xz;
            float land = smoothstep(0.03, 0.12, vWPos.y);
            // painterly mottling
            float m = (dn(p * 1.1) - 0.5) * 0.10 + (dn(p * 4.3) - 0.5) * 0.07;
            diffuseColor.rgb *= 1.0 + m * near * land;
            // fields: a soft, irregular patchwork of plots, strongest in the flat farmland
            float zone = dn(p * 0.45 + 3.3);
            float ang = zone < 0.5 ? 0.35 : -0.55;
            mat2 rot = mat2(cos(ang), sin(ang), -sin(ang), cos(ang));
            vec2 w = rot * p * 2.2 + vec2(dn(p * 0.9), dn(p * 0.9 + 7.1)) * 0.9 + vec2(dn(p * 0.3), dn(p * 0.3 + 2.2)) * 2.0;
            vec2 q = w * vec2(1.0, 1.6);
            q.x += step(0.5, fract(q.y * 0.5)) * 0.5;
            vec2 cell = floor(q);
            vec2 f = fract(q);
            float r = dh(cell + floor(zone * 2.0) * 13.0);
            vec3 tint = r < 0.4 ? vec3(0.9, 1.0, 0.84) : (r < 0.78 ? vec3(1.0, 1.0, 0.94) : vec3(1.08, 1.03, 0.86));
            tint = mix(vec3(1.0), tint, 0.55 + 0.45 * dn(p * 1.7));
            float edge = min(min(f.x, 1.0 - f.x), min(f.y, 1.0 - f.y));
            float bund = (1.0 - smoothstep(0.0, 0.05, edge)) * step(0.35, dh(cell + 5.1));
            float fm = smoothstep(0.2, 0.7, farm) * (1.0 - smoothstep(0.03, 0.12, slope)) * land * near;
            diffuseColor.rgb = mix(diffuseColor.rgb, diffuseColor.rgb * tint, fm * 0.6);
            diffuseColor.rgb *= 1.0 - bund * fm * 0.06;
            // woods: clusters of tree crowns on green, unfarmed hills
            float greenness = smoothstep(0.0, 0.06, c.g - max(c.r, c.b) * 0.95);
            float wood = greenness * (1.0 - smoothstep(0.1, 0.5, farm)) * land * (1.0 - smoothstep(0.35, 0.6, slope));
            float dens = smoothstep(0.35, 0.75, dn(p * 0.8 + 4.0));
            float tr = crowns(p * 9.0) * dens;
            diffuseColor.rgb = mix(diffuseColor.rgb, diffuseColor.rgb * vec3(0.66, 0.78, 0.68), tr * wood * near * 0.6);
            diffuseColor.rgb *= 1.0 - wood * dens * near * 0.08;
          }
        }`,
      )
      .replace(
        "#include <normal_fragment_maps>",
        `{
          vec2 nxy = texture2D(normalMap, vNormalMapUv).xy * 2.0 - 1.0;
          float nz = sqrt(max(0.0, 1.0 - dot(nxy, nxy)));
          nxy *= uNormalStrength;
          vec3 nW = normalize(vec3(nxy.x, nz, -nxy.y));
          normal = normalize((viewMatrix * vec4(nW, 0.0)).xyz);
        }`,
      );
  };
  mat.customProgramCacheKey = () => "terrain-tile";
  const mesh = new THREE.Mesh(geom, mat);
  mesh.receiveShadow = true;
  mesh.userData.uniforms = uniforms;
  return mesh;
}

export interface Terrain {
  group: THREE.Group;
  heightAt: (x: number, z: number) => number;
  water: THREE.Mesh;
  tiles: THREE.Mesh[];
}

/** Both tiles (whole map + East Asia detail), their water, and a CPU height sampler. */
export async function makeTerrain(geo: Geo, quality: "high" | "low", sky: THREE.Color): Promise<Terrain> {
  const lowRes = quality === "low";
  const sfx = (big: string, small: string) => (lowRes ? small : big);
  const [gGrid, eGrid, gCol, gNrm, eCol, eNrm, gWat, eWat] = await Promise.all([
    loadHeights("map/global-height.webp", geo, geo.tiles.global),
    loadHeights("map/ea-height.webp", geo, geo.tiles.ea),
    tex(`map/global-color${sfx("", "-2k")}.webp`, true),
    tex(`map/global-normal${sfx("", "-1k")}.webp`, false),
    tex(`map/ea-color${sfx("", "-2k")}.webp`, true),
    tex(`map/ea-normal${sfx("", "-2k")}.webp`, false),
    tex("map/global-water.webp", false, 4),
    tex("map/ea-water.webp", false, 4),
  ]);
  const group = new THREE.Group();
  group.name = "terrain";
  const inset = 0.8;
  const [ex0, ez0, ex1, ez1] = eGrid.box;
  const globalTile = makeTile(gGrid, gCol, gNrm, lowRes, [ex0 + inset, ez0 + inset, ex1 - inset, ez1 - inset]);
  const eaTile = makeTile(eGrid, eCol, eNrm, lowRes);
  group.add(globalTile, eaTile);
  const water = makeWater(geo, gGrid.box, eGrid.box, gWat, eWat, sky);
  group.add(water);
  return { group, heightAt: makeHeightSampler([eGrid, gGrid], lowRes), water, tiles: [globalTile, eaTile] };
}

/** Painted sea: smooth depth tint, drifting wave strokes, surf lines along coasts; dissolves into the haze at the map edge. */
function makeWater(geo: Geo, gBox: Rect, eBox: Rect, gTex: THREE.Texture, eTex: THREE.Texture, sky: THREE.Color) {
  const [W, H] = geo.size;
  const mat = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    fog: true,
    uniforms: THREE.UniformsUtils.merge([
      THREE.UniformsLib.fog,
      {
        uWaterG: { value: null },
        uWaterE: { value: null },
        uBoxG: { value: new THREE.Vector4(...gBox) },
        uBoxE: { value: new THREE.Vector4(...eBox) },
        uBorder: { value: geo.border },
        uTime: { value: 0 },
        uSkyOut: { value: srgb(sky) },
        uShallow: { value: new THREE.Color("#c9ddd2") },
        uDeep: { value: new THREE.Color("#6f9aa0") },
        uFoam: { value: new THREE.Color("#f4f3ea") },
      },
    ]),
    vertexShader: /* glsl */ `
      #include <fog_pars_vertex>
      varying vec3 vWorld;
      void main() {
        vec4 wp = modelMatrix * vec4(position, 1.0);
        vWorld = wp.xyz;
        vec4 mvPosition = viewMatrix * wp;
        gl_Position = projectionMatrix * mvPosition;
        #include <fog_vertex>
      }`,
    fragmentShader: /* glsl */ `
      #include <common>
      #include <fog_pars_fragment>
      uniform sampler2D uWaterG, uWaterE;
      uniform vec4 uBoxG, uBoxE;
      uniform float uBorder, uTime;
      uniform vec3 uSkyOut, uShallow, uDeep, uFoam;
      varying vec3 vWorld;
      float hsh(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
      float vn(vec2 p) {
        vec2 i = floor(p), f = fract(p);
        vec2 u = f * f * (3.0 - 2.0 * f);
        return mix(mix(hsh(i), hsh(i + vec2(1, 0)), u.x), mix(hsh(i + vec2(0, 1)), hsh(i + vec2(1, 1)), u.x), u.y);
      }
      vec2 boxUv(vec4 b, vec2 p) { return vec2((p.x - b.x) / (b.z - b.x), 1.0 - (p.y - b.y) / (b.w - b.y)); }
      void main() {
        vec2 p = vWorld.xz;
        vec4 wg = texture2D(uWaterG, boxUv(uBoxG, p));
        vec4 we = texture2D(uWaterE, boxUv(uBoxE, p));
        float eIn = min(min(p.x - uBoxE.x, uBoxE.z - p.x), min(p.y - uBoxE.y, uBoxE.w - p.y));
        vec4 w = mix(wg, we, smoothstep(2.0, 10.0, eIn));
        float camD = length(cameraPosition - vWorld);
        float near = 1.0 - smoothstep(60.0, 420.0, camD);
        float depth = w.r;
        float coast = w.g;
        vec3 col = mix(uShallow, uDeep, smoothstep(0.0, 0.85, depth));
        // painted wave strokes, like the stylised waves of Song and Yuan painting
        vec2 q = p * 0.55;
        float n = vn(q * 0.3 + uTime * 0.02);
        float band = sin(q.y * 2.6 + sin(q.x * 0.9 + n * 3.0) * 1.6 - uTime * 0.45);
        float stroke = smoothstep(0.955, 0.998, band) * smoothstep(0.45, 0.8, vn(q * 1.3 - uTime * 0.06));
        col = mix(col, uFoam, stroke * 0.22 * (0.3 + 0.7 * depth) * near);
        // fine ripples close up
        float rip = vn(p * 3.0 + vec2(uTime * 0.15, 0.0)) * vn(p * 2.3 - vec2(0.0, uTime * 0.11));
        col *= 1.0 + (0.07 * rip - 0.03) * near;
        // surf lines that roll in toward the shore
        float surfBand = 0.5 + 0.5 * sin(coast * 22.0 - uTime * 1.1 + vn(p * 0.9) * 5.0);
        float breakup = smoothstep(0.3, 0.7, vn(p * 2.2 + uTime * 0.05));
        float surf = smoothstep(0.55, 0.97, coast) * 0.8 + smoothstep(0.85, 1.0, surfBand) * smoothstep(0.25, 0.7, coast) * breakup * 0.6 * near;
        col = mix(col, uFoam, clamp(surf, 0.0, 1.0) * 0.5 * (1.0 - w.b));
        float alpha = mix(0.3, 0.92, smoothstep(0.0, 0.5, depth));
        gl_FragColor = vec4(col, alpha);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
        // dissolve into the mist beyond the (ragged) edge of the map; sky colour is already in output space, like the fog
        vec2 ug = boxUv(uBoxG, p);
        float k = wg.a * step(0.0, ug.x) * step(ug.x, 1.0) * step(0.0, ug.y) * step(ug.y, 1.0);
        gl_FragColor.rgb = mix(uSkyOut, gl_FragColor.rgb, k);
        gl_FragColor.a = mix(1.0, gl_FragColor.a, k);
        #include <fog_fragment>
      }`,
  });
  mat.uniforms.uWaterG.value = gTex;
  mat.uniforms.uWaterE.value = eTex;
  const mesh = new THREE.Mesh(new THREE.PlaneGeometry(W * 3, H * 3, 1, 1), mat);
  mesh.rotation.x = -Math.PI / 2;
  mesh.position.y = 0.03;
  mesh.renderOrder = 2;
  mesh.name = "water";
  return mesh;
}

/** Soft silk-coloured sky dome; like the fog it skips tone mapping, so the horizon matches the fogged distance exactly. */
export function makeSky(horizon: THREE.Color, zenith: THREE.Color) {
  const mat = new THREE.ShaderMaterial({
    side: THREE.BackSide,
    depthWrite: false,
    fog: false,
    uniforms: { uH: { value: horizon.clone() }, uZ: { value: zenith.clone() } },
    vertexShader: /* glsl */ `
      varying vec3 vDir;
      void main() {
        vDir = normalize(position);
        vec4 p = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        gl_Position = p.xyww;
      }`,
    fragmentShader: /* glsl */ `
      uniform vec3 uH, uZ;
      varying vec3 vDir;
      void main() {
        float t = smoothstep(-0.02, 0.55, vDir.y);
        gl_FragColor = vec4(mix(uH, uZ, t), 1.0);
        #include <colorspace_fragment>
      }`,
  });
  const mesh = new THREE.Mesh(new THREE.SphereGeometry(1, 32, 16), mat);
  mesh.scale.setScalar(5000);
  mesh.frustumCulled = false;
  mesh.renderOrder = -1;
  mesh.name = "sky";
  return mesh;
}

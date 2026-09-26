import * as THREE from "three";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { ShaderPass } from "three/addons/postprocessing/ShaderPass.js";
import { OutputPass } from "three/addons/postprocessing/OutputPass.js";

/** Separable blur whose radius grows away from a horizontal band of focus: the "tilt-shift" miniature look. */
const TiltShift = {
  uniforms: {
    tDiffuse: { value: null },
    uDir: { value: new THREE.Vector2(1, 0) },
    uRes: { value: new THREE.Vector2(1, 1) },
    uFocus: { value: 0.5 },
    uBand: { value: 0.14 },
    uAmount: { value: 0 },
  },
  vertexShader: /* glsl */ `
    varying vec2 vUv;
    void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
  fragmentShader: /* glsl */ `
    uniform sampler2D tDiffuse;
    uniform vec2 uDir, uRes;
    uniform float uFocus, uBand, uAmount;
    varying vec2 vUv;
    void main() {
      float d = abs(vUv.y - uFocus);
      float r = smoothstep(uBand, uBand + 0.38, d) * uAmount;
      if (r < 0.05) { gl_FragColor = texture2D(tDiffuse, vUv); return; }
      vec4 sum = vec4(0.0);
      float wsum = 0.0;
      for (int i = -7; i <= 7; i++) {
        float w = exp(-float(i * i) / 24.0);
        sum += texture2D(tDiffuse, vUv + uDir * (float(i) * r) / uRes) * w;
        wsum += w;
      }
      gl_FragColor = sum / wsum;
    }`,
};

export interface Post {
  composer: EffectComposer;
  setFocus: (screenY: number, amount: number) => void;
  setSize: (w: number, h: number) => void;
}

export function makePost(renderer: THREE.WebGLRenderer, scene: THREE.Scene, camera: THREE.Camera): Post {
  const size = renderer.getDrawingBufferSize(new THREE.Vector2());
  const target = new THREE.WebGLRenderTarget(size.x, size.y, { type: THREE.HalfFloatType, samples: 4 });
  const composer = new EffectComposer(renderer, target);
  composer.addPass(new RenderPass(scene, camera));
  const h = new ShaderPass(TiltShift);
  const v = new ShaderPass(TiltShift);
  v.uniforms.uDir.value.set(0, 1);
  composer.addPass(h);
  composer.addPass(v);
  composer.addPass(new OutputPass());
  const setSize = (w: number, hh: number) => {
    composer.setPixelRatio(renderer.getPixelRatio());
    composer.setSize(w, hh);
    const px = renderer.getDrawingBufferSize(new THREE.Vector2());
    for (const p of [h, v]) p.uniforms.uRes.value.set(px.x, px.y);
  };
  return {
    composer,
    setSize,
    setFocus: (y, amount) => {
      for (const p of [h, v]) {
        p.uniforms.uFocus.value = y;
        p.uniforms.uAmount.value = amount * renderer.getPixelRatio();
      }
      h.enabled = v.enabled = amount > 0.05;
    },
  };
}

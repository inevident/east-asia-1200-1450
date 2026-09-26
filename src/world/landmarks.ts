import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { DRACOLoader } from "three/addons/loaders/DRACOLoader.js";
import type { World } from "./world";
import type { Projector } from "./geo";

export interface Landmarks {
  group: THREE.Group;
  byId: Map<string, THREE.Object3D>;
  movers: Map<string, THREE.Object3D>;
}

/**
 * Landmarks modeled in Blender (blender/scenes/map_landmarks.py) arrive as one Draco-compressed glTF.
 * Each node "lm_<anchor>" is modeled around its anchor with vertices at absolute terrain height (the Blender
 * script reads the same height grid as the website), so it only needs moving to its anchor.
 * Nodes named "mv_<kind>" are templates for ships and caravans, bow toward +Z.
 */
export async function loadLandmarks(world: World, proj: Projector): Promise<Landmarks> {
  const group = new THREE.Group();
  group.name = "landmarks";
  const byId = new Map<string, THREE.Object3D>();
  const movers = new Map<string, THREE.Object3D>();
  const draco = new DRACOLoader().setDecoderPath("draco/");
  const loader = new GLTFLoader().setDRACOLoader(draco);
  let gltf;
  try {
    gltf = await loader.loadAsync("models/landmarks.glb");
  } catch {
    return { group, byId, movers };
  }
  for (const node of [...gltf.scene.children]) {
    node.traverse((o) => {
      const m = o as THREE.Mesh;
      if (!m.isMesh) return;
      m.castShadow = true;
      m.receiveShadow = true;
      const mats = Array.isArray(m.material) ? m.material : [m.material];
      for (const mat of mats as THREE.MeshStandardMaterial[]) {
        if (!mat.isMeshStandardMaterial) continue;
        mat.metalness = Math.min(mat.metalness, 0.5);
        mat.side = THREE.DoubleSide;
      }
    });
    if (node.name.startsWith("mv_")) {
      movers.set(node.name.slice(3), node);
      continue;
    }
    if (!node.name.startsWith("lm_")) continue;
    const id = node.name.slice(3);
    if (!world.geo.anchors[id]) continue;
    const at = proj.place(id);
    node.position.set(at.x, 0, at.z);
    node.updateMatrixWorld(true);
    group.add(node);
    byId.set(id, node);
  }
  world.scene.add(group);
  return { group, byId, movers };
}

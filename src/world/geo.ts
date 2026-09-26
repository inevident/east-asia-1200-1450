import * as THREE from "three";
import type { Geo } from "./terrain";

export type Place = string | [number, number];

/**
 * Lambert conformal conic projection, identical to tools/geo.py, so places given as (lon, lat) in the story
 * land exactly where the Python terrain build put them.
 */
export function makeProjector(geo: Geo, heightAt: (x: number, z: number) => number) {
  const p = geo.projection;
  const { R, n, F, rho0, lam0 } = p;
  const [cx, cy] = geo.center;
  const project = (lon: number, lat: number): [number, number] => {
    if (lon < lam0 - 180) lon += 360;
    const phi = THREE.MathUtils.degToRad(lat);
    const rho = (R * F) / Math.pow(Math.tan(Math.PI / 4 + phi / 2), n);
    const th = n * THREE.MathUtils.degToRad(lon - lam0);
    return [rho * Math.sin(th), rho0 - rho * Math.cos(th)];
  };
  /** World position (x, ground height, z) of a lon/lat. */
  const world = (lon: number, lat: number, lift = 0) => {
    const [x, y] = project(lon, lat);
    const X = x - cx;
    const Z = cy - y;
    return new THREE.Vector3(X, Math.max(heightAt(X, Z), 0) + lift, Z);
  };
  /** A named anchor from geo.json or a raw [lon, lat]. */
  const place = (at: Place, lift = 0) => {
    if (typeof at === "string") {
      const a = geo.anchors[at];
      if (!a) throw new Error(`Unknown place "${at}"`);
      return new THREE.Vector3(a[0], Math.max(heightAt(a[0], a[2]), 0) + lift, a[2]);
    }
    return world(at[0], at[1], lift);
  };
  return { project, world, place };
}

export type Projector = ReturnType<typeof makeProjector>;

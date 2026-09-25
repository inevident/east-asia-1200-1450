// Convert Natural Earth land polygons (world-atlas, 1:50m) to GeoJSON for the terrain builder.
import { readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { feature } from "topojson-client";
const require = createRequire(import.meta.url);
const topo = JSON.parse(readFileSync(require.resolve("world-atlas/land-50m.json"), "utf8"));
const land = feature(topo, topo.objects.land);
writeFileSync("blender/data/land50.geojson", JSON.stringify(land));
console.log("polygons:", land.geometry ? land.geometry.coordinates.length : land.features.length);

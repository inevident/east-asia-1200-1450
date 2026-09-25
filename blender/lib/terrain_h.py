"""
Terrain height at any map point, read from the vertex-node grids that tools/build_terrain.py wrote
(the same grids the website displaces its mesh with), interpolated exactly like three.js's PlaneGeometry
triangles. Landmarks built with this sit precisely on the rendered ground.
"""
import json
import numpy as np

DATA = "/Applications/Personal App/AP-WORLD-WEBSITE/blender/data"
META = json.load(open(f"{DATA}/geo_blender.json"))
EXTENT = META["extent"]
EA_RECT = META["ea_rect"]
SEG = META["seg"]
ANCHORS = META["anchors"]  # name -> [x, y, h] in map units
_NG = np.load(f"{DATA}/nodes_global.npy")
_NE = np.load(f"{DATA}/nodes_ea.npy")
_TILES = ((EA_RECT, _NE, SEG["ea"]), (EXTENT, _NG, SEG["global"]))


def H(x, y):
    for (x0, y0, x1, y1), N, (sx, sy) in _TILES:
        if x0 + 1 < x < x1 - 1 and y0 + 1 < y < y1 - 1:
            fx = (x - x0) / (x1 - x0) * sx
            fy = (y1 - y) / (y1 - y0) * sy
            i, j = min(int(fx), sx - 1), min(int(fy), sy - 1)
            tx, ty = fx - i, fy - j
            a, b, c, d = N[j, i], N[j + 1, i], N[j + 1, i + 1], N[j, i + 1]
            v = a + (d - a) * tx + (b - a) * ty if tx + ty <= 1 else c + (b - c) * (1 - tx) + (d - c) * (1 - ty)
            return float(v)
    return 0.0


def ground_fn(anchor):
    """Local ground function g(lx, ly) around an anchor (lx east, ly north, map units)."""
    ax, ay = ANCHORS[anchor][0], ANCHORS[anchor][1]
    return lambda lx, ly: H(ax + lx, ay + ly)


def is_water(g, x, y):
    return g(x, y) < 0.035

"""
Build the 3D map's terrain from Natural Earth coastlines + an authored relief model.

Two consistent tiles (world-space noise, shared smooth fields):
  global  — the whole map (Africa to Japan), 4096 px wide  (~3 km/px)
  ea      — East Asia detail tile, 4096 px                  (~1.2 km/px)
Outputs (public/map/):  {tile}-color.webp, {tile}-normal.webp, {tile}-height.png, geo.json
Also blender/data/heights_{tile}.npy for placing Blender landmarks exactly on the ground.
"""
import json
import math
import os
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw

from geo import EXTENT, PARAMS, RANGES, PLATEAUS, DESERTS, PLAINS, RIVERS, project, LAM0
from anchors import ANCHORS, ROUTES

T0 = time.time()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "public", "map")
DATA = os.path.join(ROOT, "blender", "data")
os.makedirs(OUT, exist_ok=True)

XMIN, YMIN, XMAX, YMAX = EXTENT
EA_RECT = (-60.0, -270.0, 440.0, 290.0)   # East Asia detail tile (projected units)
EXAG = 24.0        # 1 km of land -> 2.4 world units
SEA_EXAG = 4.0
BORDER = 34.0      # world units over which the map dissolves into mist at its edges (edge is roughened by noise)
SEG = {"global": (1024, 612), "ea": (1024, 1148)}   # mesh segments (must stay even so low quality can halve them)
# flatten the ground a little where Blender landmarks stand (radius in world units)
FLATTEN = {"dadu": 2.2, "shangdu": 1.4, "kaifeng": 1.8, "hangzhou": 1.6, "nanjing": 1.6, "quanzhou": 1.2, "jingdezhen": 1.0,
           "kyoto": 1.6, "kamakura": 0.9, "hakata": 1.0, "kaesong": 1.2, "hanseong": 1.2, "haeinsa": 0.8, "thanglong": 1.4,
           "karakorum": 1.6, "samarkand": 1.4, "maragheh": 1.0, "sakya": 1.0, "cheongju": 0.8, "yangzhou": 1.0, "linqing": 0.8,
           "iron": 0.8, "village": 1.0, "xian": 1.4, "champa": 0.8, "calicut": 0.8, "malacca": 0.8, "guangzhou": 1.0,
           "jianyang": 0.8, "bailudong": 0.8, "dunhuang": 1.0, "kashgar": 1.0, "tabriz": 1.0, "hormuz": 0.7}


def log(msg):
    print(f"[{time.time() - T0:5.1f}s] {msg}", flush=True)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return (t * t * (3 - 2 * t)).astype(np.float32)


def densify(pts, step=0.2):
    out = []
    for (a, b) in zip(pts[:-1], pts[1:]):
        n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
        for k in range(n):
            t = k / n
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    out.append(pts[-1])
    return out


class Grid:
    def __init__(self, rect, W):
        self.rect = rect
        x0, y0, x1, y1 = rect
        self.W = W
        self.H = int(round(W * (y1 - y0) / (x1 - x0)))
        self.pu = (x1 - x0) / W           # world units per pixel
        self.km = self.pu * 10.0
        xs = x0 + (np.arange(W, dtype=np.float32) + 0.5) * self.pu
        ys = y1 - (np.arange(self.H, dtype=np.float32) + 0.5) * ((y1 - y0) / self.H)
        self.X, self.Y = np.meshgrid(xs, ys)

    def px(self, x, y):
        x0, y0, x1, y1 = self.rect
        return (x - x0) / (x1 - x0) * self.W, (y1 - y) / (y1 - y0) * self.H

    def ll(self, lon, lat):
        return self.px(*project(lon, lat))

    def lonlat(self):
        n, F, rho0, Rr = PARAMS["n"], PARAMS["F"], PARAMS["rho0"], PARAMS["R"]
        X = self.X.astype(np.float64)
        Y = self.Y.astype(np.float64)
        rho = np.sign(n) * np.hypot(X, rho0 - Y)
        th = np.arctan2(X, rho0 - Y)
        lat = np.degrees(2 * np.arctan((Rr * F / rho) ** (1 / n)) - np.pi / 2)
        lon = LAM0 + np.degrees(th / n)
        return lon.astype(np.float32), lat.astype(np.float32)

    def sample_global(self, G, arr):
        """Resample a field computed on the global grid G onto this grid (bilinear)."""
        gx = (self.X - G.rect[0]) / G.pu - 0.5
        gy = (G.rect[3] - self.Y) / G.pu - 0.5
        return cv2.remap(arr, gx.astype(np.float32), gy.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


# ------------------------------------------------------------------ world-space lattice noise (identical on every grid)
_lattices = {}


def lattice_noise(g, spacing, seed):
    key = (spacing, seed)
    if key not in _lattices:
        r = np.random.default_rng(seed)
        nx = int((XMAX - XMIN) / spacing) + 6
        ny = int((YMAX - YMIN) / spacing) + 6
        _lattices[key] = (r.random((ny, nx)).astype(np.float32) * 2 - 1)
    lat = _lattices[key]
    gx = (g.X - XMIN) / spacing + 2.0
    gy = (YMAX - g.Y) / spacing + 2.0
    return cv2.remap(lat, gx, gy, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)


def fbm(g, spacing, seed, octaves, gain=0.5, min_px=2.5):
    total = np.zeros((g.H, g.W), np.float32)
    amp, norm, s = 1.0, 0.0, spacing
    for o in range(octaves):
        if s < g.pu * min_px:
            break
        total += amp * lattice_noise(g, s, seed * 31 + o)
        norm += amp
        amp *= gain
        s /= 2.03
    return total / max(norm, 1e-6)


def ridged(g, spacing, seed, octaves, gain=0.55, min_px=2.5):
    total = np.zeros((g.H, g.W), np.float32)
    weight = np.ones((g.H, g.W), np.float32)
    amp, norm, s = 1.0, 0.0, spacing
    for o in range(octaves):
        if s < g.pu * min_px:
            break
        sig = (1.0 - np.abs(lattice_noise(g, s, seed * 57 + o))) ** 2
        sig *= weight
        weight = np.clip(sig * 1.7, 0, 1)
        total += amp * sig
        norm += amp
        amp *= gain
        s /= 2.1
    return total / max(norm, 1e-6)


# ------------------------------------------------------------------ land polygons
gj = json.load(open(os.path.join(DATA, "land50.geojson")))
feats = gj["features"] if gj.get("type") == "FeatureCollection" else [gj]
POLYS = []
for f in feats:
    gm = f["geometry"]
    POLYS += gm["coordinates"] if gm["type"] == "MultiPolygon" else [gm["coordinates"]]


def norm_ring(ring):
    out, prev = [], None
    for lon, lat in ring:
        if lon < LAM0 - 180:
            lon += 360
        if prev is not None and abs(lon - prev) > 180:
            return None
        prev = lon
        out.append((lon, max(-80.0, min(84.0, lat))))
    return out


RINGS = []
for poly in POLYS:
    outer = norm_ring(poly[0])
    if outer:
        RINGS.append((outer, [h for h in (norm_ring(r) for r in poly[1:]) if h]))


def land_mask(g, ss=2):
    img = Image.new("L", (g.W * ss, g.H * ss), 0)
    d = ImageDraw.Draw(img)
    for outer, holes in RINGS:
        pts = [g.ll(lon, lat) for lon, lat in outer]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        if max(xs) < 0 or min(xs) > g.W or max(ys) < 0 or min(ys) > g.H:
            continue
        d.polygon([(x * ss, y * ss) for x, y in pts], fill=255)
        for h in holes:
            d.polygon([(x * ss, y * ss) for x, y in (g.ll(lon, lat) for lon, lat in h)], fill=0)
    return np.asarray(img.resize((g.W, g.H), Image.BOX), np.float32) / 255.0


def poly_mask(g, pts, blur_km):
    img = Image.new("L", (g.W, g.H), 0)
    ImageDraw.Draw(img).polygon([g.ll(*p) for p in densify(pts + [pts[0]], 0.5)], fill=255)
    m = np.asarray(img, np.float32) / 255.0
    return cv2.GaussianBlur(m, (0, 0), max(1.0, blur_km / g.km))


def line_dist_km(g, pts):
    img = np.full((g.H, g.W), 255, np.uint8)
    p = np.array([g.ll(*q) for q in densify(pts, 0.1)], np.int32)
    cv2.polylines(img, [p], False, 0, 1, cv2.LINE_8)
    return cv2.distanceTransform(img, cv2.DIST_L2, 5) * g.km


# ------------------------------------------------------------------ smooth fields on the global grid (shared by both tiles)
G = Grid(EXTENT, 4096)
log(f"global grid {G.W}x{G.H} ({G.km:.2f} km/px)")
landG = land_mask(G)
lbin = (landG > 0.5).astype(np.uint8)
d_land = cv2.distanceTransform(lbin, cv2.DIST_L2, 5) * G.km
d_sea = cv2.distanceTransform(1 - lbin, cv2.DIST_L2, 5) * G.km
# domain warp (world units) so ranges wander naturally
wx = fbm(G, 180, 21, 3) * 16
wy = fbm(G, 180, 22, 3) * 16
map_x = ((G.X - XMIN) / G.pu - 0.5 + wx / G.pu).astype(np.float32)
map_y = ((YMAX - G.Y) / G.pu - 0.5 - wy / G.pu).astype(np.float32)


def warped(a):
    return cv2.remap(a, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


plateau = np.zeros((G.H, G.W), np.float32)
for name, pts, elev_p, blur in PLATEAUS:
    plateau = np.maximum(plateau, poly_mask(G, pts, blur) * elev_p)
plateau = warped(plateau)
uplift = np.zeros((G.H, G.W), np.float32)
for name, pts, hw, peak in RANGES:
    uplift = np.maximum(uplift, peak * np.exp(-(warped(line_dist_km(G, pts)) / (hw * 1.9)) ** 2))
desert = np.zeros((G.H, G.W), np.float32)
for name, pts in DESERTS:
    desert = np.maximum(desert, poly_mask(G, pts, 140))
desert = warped(desert)
plain = np.zeros((G.H, G.W), np.float32)
for name, pts in PLAINS:
    plain = np.maximum(plain, poly_mask(G, pts, 30))
plain = warped(plain)
shelf = np.clip(cv2.GaussianBlur(landG, (0, 0), 40) * 1.5 + cv2.GaussianBlur(landG, (0, 0), 9) * 0.7, 0, 1)
lonG, latG = G.lonlat()
inland_dry = smoothstep(900, 1900, d_land) * 0.8
monsoon_east = smoothstep(98, 106, lonG) * smoothstep(44, 31, latG)
monsoon_south = smoothstep(29, 23, latG) * smoothstep(66, 74, lonG)
maritime_ne = smoothstep(123, 127, lonG) * smoothstep(48, 38, latG)
lat_wet = np.maximum.reduce([monsoon_east, monsoon_south, maritime_ne]) * 0.95 + 0.05
FIELDS = {"d_land": d_land, "d_sea": d_sea, "plateau": plateau, "uplift": uplift, "desert": desert, "shelf": shelf, "plain": plain,
          "lat_wet": lat_wet, "inland_dry": inland_dry}
log("global smooth fields ready")

# ------------------------------------------------------------------ palette ('blue-green landscape')


def c(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)], np.float32)


SILK, LOESS, PLAIN_WET, STEPPE = c("dcd0ae"), c("d2bd91"), c("9fbd86"), c("cbc6a2")
PADDY = c("8db77f")
HILL, FOREST = c("6ea487"), c("4a8870")
AZURE, AZURE_DEEP, PLATEAU_C = c("5a8fb2"), c("41749a"), c("b9c09c")
SNOW, SAND = c("f1f4f2"), c("e3d3ab")
SEA_SHALLOW, SEA_DEEP = c("c3d8cc"), c("86abab")
RIVER_C, COAST_C = c("86adac"), c("534c40")
SKY = c("e9e0cd")


def catmull(pts, step):
    """Smooth curve through lon/lat control points, returned in projected units, sampled every `step` units."""
    P = [np.array(project(*q)) for q in pts]
    P = [P[0]] + P + [P[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        n = max(2, int(np.linalg.norm(p2 - p1) / step))
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P[-2])
    return np.array(out)


def meander(path, amp, wavelength, seed):
    """Displace a path sideways with smooth 1-D noise so rivers wind instead of running ruler-straight."""
    d = np.diff(path, axis=0)
    seg = np.hypot(d[:, 0], d[:, 1])
    s = np.concatenate([[0], np.cumsum(seg)])
    tang = np.gradient(path, axis=0)
    tang /= np.maximum(np.hypot(tang[:, 0], tang[:, 1]), 1e-6)[:, None]
    nrm = np.stack([-tang[:, 1], tang[:, 0]], 1)
    r = np.random.default_rng(seed)
    off = np.zeros(len(path))
    for k, (a, w) in enumerate(((1.0, wavelength), (0.45, wavelength / 2.7), (0.2, wavelength / 7.0))):
        knots = r.standard_normal(int(s[-1] / w) + 4)
        x = s / w
        i0 = np.floor(x).astype(int)
        t = (1 - np.cos(np.pi * (x - i0))) / 2
        off += a * (knots[i0] * (1 - t) + knots[i0 + 1] * t)
    taper = np.minimum(1, np.minimum(s, s[-1] - s) / (wavelength * 1.5))
    return path + nrm * (off * amp * taper)[:, None]


RIVER_PATHS = []
for i, (rname, width, pts) in enumerate(RIVERS):
    RIVER_PATHS.append((rname, width, meander(catmull(pts, 0.1), 0.55 + 0.1 * width, 3.2, 100 + i)))
RIVER_PATHS.append(("Grand Canal", 1.0, catmull(ROUTES["canal"], 0.1)))
with open(os.path.join(DATA, "rivers.json"), "w") as f:
    json.dump({n: {"width_km": w, "path": [[round(float(x), 3), round(float(y), 3)] for x, y in pth]} for n, w, pth in RIVER_PATHS}, f)



def flatten(g, Hu):
    """Level the ground under landmark sites so the Blender miniatures sit flat."""
    for key, r in FLATTEN.items():
        ax, ay = project(*ANCHORS[key])
        x0, y0, x1, y1 = g.rect
        if not (x0 < ax < x1 and y0 < ay < y1):
            continue
        px, py = g.px(ax, ay)
        rp = int(r * 1.8 / g.pu) + 2
        i0, i1 = max(0, int(px) - rp), min(g.W, int(px) + rp)
        j0, j1 = max(0, int(py) - rp), min(g.H, int(py) + rp)
        sub = Hu[j0:j1, i0:i1]
        d = np.hypot(g.X[j0:j1, i0:i1] - ax, g.Y[j0:j1, i0:i1] - ay)
        inner = (d < r) & (sub > 0.02)
        if not inner.any():
            continue
        target = max(float(np.median(sub[inner])), 0.12)
        m = smoothstep(r * 1.7, r, d)
        Hu[j0:j1, i0:i1] = np.where(sub > 0.02, sub * (1 - m) + target * m, sub)


def haze(g):
    """1 inside the map, 0 in the mist beyond its (noisy) edge."""
    edge = np.minimum.reduce([g.X - XMIN, XMAX - g.X, g.Y - YMIN, YMAX - g.Y])
    return smoothstep(0, BORDER, edge - 6 + 16 * fbm(g, 45, 9, 3)) * smoothstep(0, 5, edge)


def edge_weight(g, width):
    x0, y0, x1, y1 = g.rect
    e = np.minimum.reduce([g.X - x0, x1 - g.X, g.Y - y0, y1 - g.Y])
    return smoothstep(0, width, e)


def build(name, g, min_px, base=None):
    log(f"--- tile {name}: {g.W}x{g.H} ({g.km:.2f} km/px)")
    F = {k: (v if g is G else g.sample_global(G, v)) for k, v in FIELDS.items()}
    land = landG if g is G else land_mask(g)
    lon, lat = (lonG, latG) if g is G else g.lonlat()
    n_large = fbm(g, 140, 1, 3, min_px=min_px)
    n_mid = fbm(g, 40, 2, 5, min_px=min_px)
    n_fine = fbm(g, 10, 3, 6, min_px=min_px)
    RMF = ridged(g, 17, 11, 8, gain=0.62, min_px=min_px)
    RMF2 = ridged(g, 6.5, 12, 7, gain=0.6, min_px=min_px)
    d_land, d_sea = F["d_land"], F["d_sea"]

    # ---- elevation (km)
    flat = 1 - 0.9 * F["plain"]
    n_hill = fbm(g, 5.0, 4, 5, min_px=min_px)
    base_e = 0.04 + (0.25 * smoothstep(0, 600, d_land) + 0.1 * (n_large * 0.5 + 0.5)) * (1 - 0.75 * F["plain"])
    pl = np.clip(F["plateau"] / 4.5, 0, 1)
    mount = F["uplift"] * (0.16 + 0.84 * RMF) * (0.78 + 0.3 * n_large) * (1 - 0.42 * pl)
    tib = smoothstep(3.0, 4.2, F["plateau"])  # Tibet stays a smooth high plateau; lower plateaus are broken into hills
    plat_rough = F["plateau"] * ((0.93 + 0.1 * (0.5 + 0.5 * n_hill) + 0.06 * RMF2) * tib + (0.8 + 0.45 * RMF2) * (1 - tib))
    elev = np.maximum(base_e, plat_rough) + mount
    hills_amp = smoothstep(0.3, 0.85, n_mid * 0.5 + 0.5) * smoothstep(0, 60, d_land) * (1 - F["desert"] * 0.7) * flat
    elev = elev + hills_amp * (0.45 + 0.35 * F["lat_wet"]) * (0.45 * RMF2 + 0.55 * (0.5 + 0.5 * n_hill)) + 0.04 * n_fine * flat
    elev = np.maximum(elev, 0.02)
    # rivers (and the Grand Canal) painted a little wider than life so they read on the map
    SS = 4  # draw rivers supersampled for clean anti-aliased lines
    river = np.zeros((g.H * SS, g.W * SS), np.uint8)
    bank = np.zeros((g.H * SS, g.W * SS), np.uint8)
    for rname, width, path in RIVER_PATHS:
        p = np.array([g.px(x, y) for x, y in path], np.float64) * SS
        p = np.round(p).astype(np.int32)
        wpx = max(SS, int(round(width * 1.5 / g.km * SS)))
        cv2.polylines(bank, [p], False, 255, wpx + max(SS, int(round(1.6 / g.km * SS))), cv2.LINE_AA)
        cv2.polylines(river, [p], False, 255, wpx, cv2.LINE_AA)
    river = cv2.resize(river, (g.W, g.H), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
    bank = cv2.resize(bank, (g.W, g.H), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
    elev = elev - 0.3 * cv2.GaussianBlur(river, (0, 0), 3) * np.clip(elev, 0, 1.5)
    depth = -(0.05 + 2.8 * (1 - F["shelf"]) ** 1.5) * (1 + 0.1 * n_large)
    land_s = cv2.GaussianBlur(land, (0, 0), 0.7)
    # land rises gently from the shore over ~15 km, so coasts do not look like the cut edge of a cake
    lb_t = (land > 0.5).astype(np.uint8)
    d_in = cv2.distanceTransform(lb_t, cv2.DIST_L2, 5) * g.km
    ramp = smoothstep(0.0, 16.0, d_in) ** 0.8
    E = np.where(land_s > 0.5, 0.012 + (elev - 0.012) * np.maximum(ramp, 0.0), depth * smoothstep(0.5, 0.2, land_s)).astype(np.float32)
    Hu = np.where(E >= 0, E * EXAG / 10.0, E * SEA_EXAG / 10.0).astype(np.float32)
    flatten(g, Hu)
    border = haze(g)
    Hu = Hu * border + (-0.9) * (1 - border)

    # ---- colour
    wet = np.clip(F["lat_wet"] * (1 - F["inland_dry"]) * (1 - F["desert"]) + 0.12 * n_large, 0, 1)
    Ek = np.maximum(E, 0)
    rel = Ek - cv2.GaussianBlur(Ek, (0, 0), max(2.0, 66.0 / g.km))
    ridge_t = smoothstep(0.04, 0.5, rel) * smoothstep(1.2, 2.6, Ek)
    W3 = wet[..., None]
    low = LOESS * (1 - W3) + PLAIN_WET * W3
    low = low * 0.72 + SILK * 0.28
    patch = smoothstep(0.1, 0.25, fbm(g, 3.0, 7, 3, min_px=min_px)) * np.maximum(wet, F["plain"] * 0.8) * smoothstep(0.5, 0.15, Ek)
    low = low * (1 - patch[..., None] * 0.35) + PADDY * (patch[..., None] * 0.35)
    hills_c = HILL * W3 + STEPPE * (1 - W3)
    t1 = smoothstep(0.3, 1.1, Ek)[..., None]
    col = low * (1 - t1) + hills_c * t1
    green_t = (smoothstep(0.8, 1.8, Ek) * (0.35 + 0.65 * wet) * 0.7)[..., None]
    col = col * (1 - green_t) + FOREST * green_t
    blue_t = np.clip(smoothstep(1.9, 3.5, Ek) * 0.72 + ridge_t * 0.3, 0, 0.85)[..., None]
    col = col * (1 - blue_t) + (AZURE * 0.6 + AZURE_DEEP * 0.4) * blue_t
    plat_t = (smoothstep(3.9, 4.5, Ek) * (1 - smoothstep(0.15, 0.6, rel)) * 0.7)[..., None]
    col = col * (1 - plat_t) + PLATEAU_C * plat_t
    snow = smoothstep(6.0, 7.0, Ek + 0.8 * rel + 0.4 * n_fine)[..., None]
    col = col * (1 - snow) + SNOW * snow
    dsa = (F["desert"] * smoothstep(2.0, 0.8, Ek))[..., None]
    col = col * (1 - dsa) + SAND * dsa
    gy, gx = np.gradient(Hu, g.pu)
    Lx, Ly, Lz = -0.6, -0.45, 0.66  # sun from the south-west, matching the website's light
    shade = np.clip(((-gx * Lx) + (gy * Ly) + Lz) / np.sqrt(gx * gx + gy * gy + 1) / math.sqrt(Lx * Lx + Ly * Ly + Lz * Lz), 0, 1)
    ao = np.clip((cv2.GaussianBlur(Hu, (0, 0), max(1.5, 54.0 / g.km)) - Hu) * 0.3, -0.25, 0.4)
    col = col * (0.82 + 0.26 * shade[..., None]) * (1 - np.clip(ao, 0, 0.4)[..., None] * 0.5)
    col = col * (1 + 0.05 * n_mid[..., None] + 0.03 * n_fine[..., None])
    sh = (F["shelf"] ** 1.6)[..., None]
    sea = SEA_DEEP * (1 - sh) + SEA_SHALLOW * sh
    sea = sea * (1 + 0.035 * n_mid[..., None])
    col = np.where((land_s > 0.5)[..., None], col, sea)
    col = col * (1 - bank[..., None] * 0.22) + COAST_C * (bank[..., None] * 0.22)
    col = col * (1 - river[..., None] * 0.85) + RIVER_C * (river[..., None] * 0.85)
    coast_w = max(0.6, 2.2 / g.km)
    coast = np.clip(1.0 - np.abs(cv2.GaussianBlur(land, (0, 0), coast_w) - 0.5) * 5.0, 0, 1) ** 1.6
    col = col * (1 - coast[..., None] * 0.5) + COAST_C * (coast[..., None] * 0.5)
    grain = (np.random.default_rng(5).random((g.H, g.W)).astype(np.float32) - 0.5) * 0.028
    col = col * (1 + grain[..., None])
    col = col * border[..., None] + SKY * (1 - border[..., None])
    col = np.clip(col, 0, 1).astype(np.float32)
    # farmland mask (drives the field patchwork shader close up); stored in the normal map's blue channel
    slope_u = np.hypot(gx, gy)
    farm = ((land_s > 0.5) * smoothstep(0.9, 0.35, Ek) * (1 - F["desert"]) * np.maximum(wet, F["plain"] * 0.9)
            * smoothstep(0.45, 0.12, slope_u) * smoothstep(0.22, 0.02, rel)
            * (1 - smoothstep(0.7, 1.2, F["plateau"])) * (1 - river) * border).astype(np.float32)

    # ---- the detail tile hands over to the global tile near its own edges, so the seam is invisible
    if base is not None:
        HGb, colGb = base
        w = edge_weight(g, 18.0)
        Hu = Hu * w + g.sample_global(G, HGb) * (1 - w)
        cg = np.dstack([g.sample_global(G, np.ascontiguousarray(colGb[..., k])) for k in range(3)])
        col = col * w[..., None] + cg * (1 - w[..., None])

    img = Image.fromarray((col * 255 + 0.5).astype(np.uint8))
    img.save(os.path.join(OUT, f"{name}-color.webp"), "WEBP", quality=86, method=6)
    img.resize((2048, int(round(2048 * g.H / g.W))), Image.LANCZOS).save(os.path.join(OUT, f"{name}-color-2k.webp"), "WEBP", quality=84, method=6)
    img.resize((1400, int(1400 * g.H / g.W)), Image.LANCZOS).save(os.path.join(DATA, f"{name}_preview.png"))
    log(f"{name}: colour saved")

    # ---- normal map (tangent space; +x east, +y north)
    for nW, suffix in ((4096 if name == "ea" else 2048, ""), (2048 if name == "ea" else 1024, "-2k" if name == "ea" else "-1k")):
        nH = int(round(nW * g.H / g.W))
        Hs = cv2.resize(Hu, (nW, nH), interpolation=cv2.INTER_AREA)
        pu = (g.rect[2] - g.rect[0]) / nW
        gy2, gx2 = np.gradient(cv2.GaussianBlur(Hs, (0, 0), 0.6), pu)
        ln = np.sqrt(gx2 * gx2 + gy2 * gy2 + 1)
        fm = cv2.resize(farm, (nW, nH), interpolation=cv2.INTER_AREA)
        # R,G = normal x,y (z is rebuilt in the shader); B = farmland
        nmap = np.stack([-gx2 / ln * 0.5 + 0.5, gy2 / ln * 0.5 + 0.5, fm], -1)
        Image.fromarray((nmap * 255 + 0.5).astype(np.uint8)).save(os.path.join(OUT, f"{name}-normal{suffix}.webp"), "WEBP", quality=90, method=6)
    log(f"{name}: normals saved")

    # ---- water: smooth depth (from the shelf, no contour rings) + closeness to the coast for surf
    wW = 2048
    wH = int(round(wW * g.H / g.W))
    lb = (land > 0.5).astype(np.uint8)
    d_coast = cv2.distanceTransform(1 - lb, cv2.DIST_L2, 5) * g.km
    depth01 = np.clip(1 - F["shelf"], 0, 1) ** 1.2
    surf = np.exp(-d_coast / 9.0) * (1 - lb)
    wimg = np.dstack([depth01, surf, cv2.GaussianBlur(land, (0, 0), 1.0), haze(g)])
    wimg = cv2.resize(wimg, (wW, wH), interpolation=cv2.INTER_AREA)
    Image.fromarray((np.clip(wimg, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA").save(os.path.join(OUT, f"{name}-water.webp"), "WEBP", quality=90, alpha_quality=90, method=6)
    return Hu, col


def nodes(g, Hu, segX, segY):
    """Sample the height field at the mesh's vertex positions (row 0 = north edge)."""
    x0, y0, x1, y1 = g.rect
    xs = x0 + np.arange(segX + 1, dtype=np.float32) * ((x1 - x0) / segX)
    ys = y1 - np.arange(segY + 1, dtype=np.float32) * ((y1 - y0) / segY)
    X, Y = np.meshgrid(xs, ys)
    step_px = (x1 - x0) / segX / g.pu
    Hb = cv2.GaussianBlur(Hu, (0, 0), 0.35 * step_px)
    mx = ((X - x0) / g.pu - 0.5).astype(np.float32)
    my = ((y1 - Y) / ((y1 - y0) / g.H) - 0.5).astype(np.float32)
    return cv2.remap(Hb, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


HG, colG = build("global", G, 2.5)
EA = Grid(EA_RECT, 4096)
HE, _ = build("ea", EA, 2.2, base=(HG, colG))
del colG
NG = nodes(G, HG, *SEG["global"])
NE = nodes(EA, HE, *SEG["ea"])
HMIN = float(min(NG.min(), NE.min())) - 0.01
HMAX = float(max(NG.max(), NE.max())) + 0.01
for name, N in (("global", NG), ("ea", NE)):
    # 12-bit heights: R = top 8 bits, G = low 4 bits in its high nibble (lossless WebP keeps them exact)
    v = np.round(np.clip((N - HMIN) / (HMAX - HMIN), 0, 1) * 4095).astype(np.uint16)
    rgb = np.dstack([(v >> 4).astype(np.uint8), ((v & 15) << 4).astype(np.uint8), np.zeros_like(v, np.uint8)])
    Image.fromarray(rgb).save(os.path.join(OUT, f"{name}-height.webp"), "WEBP", lossless=True, quality=100, method=6)
    np.save(os.path.join(DATA, f"nodes_{name}.npy"), N)
log(f"heights: min {HMIN:.2f} max {HMAX:.2f}")


# ------------------------------------------------------------------ anchors & routes (heights from the rendered vertex grid)
TILES = [(EA, NE, SEG["ea"]), (G, NG, SEG["global"])]


def height_at(x, y):
    for g, N, (sx, sy) in TILES:
        x0, y0, x1, y1 = g.rect
        if x0 + 1 < x < x1 - 1 and y0 + 1 < y < y1 - 1:
            fx = (x - x0) / (x1 - x0) * sx
            fy = (y1 - y) / (y1 - y0) * sy
            i, j = min(int(fx), sx - 1), min(int(fy), sy - 1)
            tx, ty = fx - i, fy - j
            return float((N[j, i] * (1 - tx) + N[j, i + 1] * tx) * (1 - ty) + (N[j + 1, i] * (1 - tx) + N[j + 1, i + 1] * tx) * ty)
    return 0.0


def three(lon, lat, lift=0.0):
    x, y = project(lon, lat)
    return [round(x, 3), round(max(height_at(x, y), 0.0) + lift, 3), round(-y, 3)]


anchors = {k: three(*v) for k, v in ANCHORS.items()}
routes = {k: [three(lon, lat, 0.35) for lon, lat in densify(pts, 0.25)] for k, pts in ROUTES.items()}

geo = {
    "extent": EXTENT,
    "size": [XMAX - XMIN, YMAX - YMIN],
    "center": [(XMIN + XMAX) / 2, (YMIN + YMAX) / 2],
    "height": {"min": round(HMIN, 4), "max": round(HMAX, 4), "exag": EXAG},
    "tiles": {"global": {"rect": EXTENT, "seg": SEG["global"]}, "ea": {"rect": EA_RECT, "seg": SEG["ea"]}},
    "border": BORDER,
    "projection": PARAMS,
    "anchors": anchors,
    "routes": routes,
}
with open(os.path.join(OUT, "geo.json"), "w") as f:
    json.dump(geo, f, separators=(",", ":"))
with open(os.path.join(DATA, "geo_blender.json"), "w") as f:
    json.dump({"extent": EXTENT, "ea_rect": EA_RECT, "seg": SEG, "hmin": HMIN, "hmax": HMAX,
               "anchors": {k: [*project(*v), max(height_at(*project(*v)), 0.0)] for k, v in ANCHORS.items()}}, f)
for fn in sorted(os.listdir(OUT)):
    print(f"  {fn:24s} {os.path.getsize(os.path.join(OUT, fn)) / 1024:8.0f} KB")
log("done")

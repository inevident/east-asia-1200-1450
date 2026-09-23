"""
Map landmarks for the scroll tour, modeled procedurally and exported as one Draco glTF.

    exec(open(".../blender/scenes/map_landmarks.py").read(), {"ONLY": ["hangzhou"], "EXPORT": True})

Each landmark is one mesh "lm_<anchor>" whose vertices are relative to its anchor horizontally and
use absolute terrain heights vertically (see terrain_h.py), so the website only has to move it to
the anchor. "mv_<kind>" meshes are templates for ships and caravans (bow / head toward -Y).
"""
import sys
import importlib
import json
import math
import random
import time
from math import pi, sin, cos, hypot

LIB = "/Applications/Personal App/AP-WORLD-WEBSITE/blender/lib"
if LIB not in sys.path:
    sys.path.insert(0, LIB)
import mini, mini_kit, terrain_h  # noqa: E402

for mod in (mini, mini_kit, terrain_h):
    importlib.reload(mod)
import bpy  # noqa: E402
from mini import Mini, PAL, shade  # noqa: E402
import mini_kit as K  # noqa: E402
from terrain_h import ANCHORS, H, ground_fn  # noqa: E402

ROOT = "/Applications/Personal App/AP-WORLD-WEBSITE"
RIVERS = json.load(open(f"{ROOT}/blender/data/rivers.json"))
ONLY = globals().get("ONLY")
EXPORT = globals().get("EXPORT", True)
LANDMARKS = {}


def landmark(fn):
    LANDMARKS[fn.__name__] = fn
    return fn


def river_local(name, anchor, R=3.0, step=1):
    """Points of a painted river/canal path within R of an anchor, in the anchor's local frame."""
    ax, ay = ANCHORS[anchor][0], ANCHORS[anchor][1]
    pts = [(x - ax, y - ay) for x, y in RIVERS[name]["path"]]
    return [p for p in pts[::step] if hypot(*p) < R]


def water_spots(g, box, n, seed=0, min_depth=0.0, spacing=0.3):
    """Random points on open water inside box (x0, y0, x1, y1), spaced apart."""
    rnd = random.Random(seed)
    out = []
    for _ in range(n * 60):
        if len(out) >= n:
            break
        x = rnd.uniform(box[0], box[2])
        y = rnd.uniform(box[1], box[3])
        ok = all(g(x + dx, y + dy) < 0.025 - min_depth for dx, dy in ((0, 0), (0.25, 0), (-0.25, 0), (0, 0.25), (0, -0.25)))
        if ok and all(hypot(x - a, y - b) > spacing for a, b in out):
            out.append((x, y))
    return out


def rect_poly(cx, cy, w, d):
    return [(cx - w / 2, cy - d / 2), (cx + w / 2, cy - d / 2), (cx + w / 2, cy + d / 2), (cx - w / 2, cy + d / 2)]


def compound(m, g, cx, cy, w, d, wall="red_dark", h=0.035, t=0.03, rot=0.0, court="court", gate_roof="roof"):
    """A walled courtyard with a paved floor and a gate in the south wall."""
    c, s = cos(rot), sin(rot)
    pts = [(cx + c * x - s * y, cy + s * x + c * y) for x, y in ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2))]
    K.slab_on_ground(m, g, pts, court, lift=0.006, n=6)
    K.wall(m, g, pts, h=h, t=t, color=wall)
    K.gate(m, g, cx + s * d / 2, cy - c * d / 2, min(0.16, w * 0.3), 0.07, rot, roof=gate_roof, body=wall, h=h * 1.2)


# ======================================================================================== China
@landmark
def hangzhou(m, g):
    """Lin'an, the Southern Song capital: walled city between West Lake and the Qiantang River."""
    walls = [(-0.55, -1.25), (0.3, -1.35), (0.7, -0.7), (0.8, 0.3), (0.62, 1.25), (-0.4, 1.3), (-0.62, 0.55), (-0.7, -0.35)]
    # Qiantang River sweeping past the south of the city into the bay
    K.ribbon(m, g, [(-3.2, -2.7), (-2.2, -2.3), (-1.2, -2.0), (-0.2, -1.8), (0.7, -1.5), (1.5, -0.85), (2.05, -0.05), (2.5, 0.65), (2.9, 1.1)], 0.34)
    # West Lake with the Su causeway
    lake = [(-1.62, -0.45), (-1.25, -0.62), (-0.85, -0.5), (-0.74, -0.05), (-0.8, 0.45), (-1.0, 0.78), (-1.4, 0.8), (-1.72, 0.4), (-1.78, -0.05)]
    K.pond(m, lake, 0.365, "pond", "stone_dark")
    K.ribbon(m, g, [(-1.45, -0.55), (-1.4, 0.0), (-1.33, 0.72)], 0.035, "grass", lift=0.024, mat=0)
    for k in range(8):
        t = k / 7
        K.tree(m, g, -1.45 + 0.12 * t + 0.03, -0.5 + 1.2 * t, 0.07, "willow", seed=40 + k, z=0.37)
    for x, y in ((-1.1, 0.25), (-1.25, -0.25)):  # islets
        m.lathe(x, y, 0.33, [(0.07, 0), (0.06, 0.04), (0.001, 0.055)], 8, PAL["grass"])
        K.tree(m, g, x, y, 0.06, "broad", seed=int(x * 100), z=0.38)
    for i, (x, y) in enumerate(((-1.0, 0.1), (-1.5, 0.3), (-1.2, -0.35))):
        K.sampan(m, x, y, 0.6 * i, 0.1, z=0.368)
    # pagodas: Leifeng on the south shore, Baochu on the north hill, Liuhe above the river
    K.pagoda(m, g, -1.05, -0.62, r=0.065, tiers=5, body="ochre", roof="roof_dark")
    K.pagoda(m, g, -1.02, 0.95, r=0.03, tiers=7, th=0.07, body="stone_light", roof="stone_dark", taper=0.92)
    K.pagoda(m, g, -0.75, -1.72, r=0.1, tiers=7, body="white", roof="roof_dark", rail="red")
    # walls and gates
    K.wall(m, g, walls, h=0.065, t=0.05, tower_every=0.34)
    for x, y, r in ((0.1, 1.27, 0.0), (-0.12, -1.3, 0.0), (0.77, -0.25, pi / 2), (0.78, 0.55, pi / 2), (-0.66, 0.15, pi / 2), (-0.55, 0.75, pi / 2)):
        K.gate(m, g, x, y, 0.16, 0.08, r)
    # the palace on Phoenix Hill, at the south end of the Imperial Way
    compound(m, g, -0.12, -0.93, 0.62, 0.4, wall="red_dark", h=0.04, gate_roof="roof_green")
    K.hall(m, g, -0.12, -0.98, 0.3, 0.16, 0.0, roof="roof_green", walls="red", double=True)
    K.hall(m, g, -0.33, -0.86, 0.12, 0.09, pi / 2, roof="roof_green")
    K.hall(m, g, 0.09, -0.86, 0.12, 0.09, pi / 2, roof="roof_green")
    K.ribbon(m, g, [(-0.1, -0.7), (-0.02, 0.2), (0.1, 1.24)], 0.07, "road", lift=0.008, mat=0)
    # the examination compound: rows of tiny cells around a watchtower
    ex, ey = 0.36, 0.42
    K.slab_on_ground(m, g, rect_poly(ex, ey, 0.5, 0.46), "court", lift=0.006, n=4)
    K.wall(m, g, rect_poly(ex, ey, 0.5, 0.46), h=0.03, t=0.025, color="brick_grey")
    for r in range(6):
        y = ey - 0.17 + r * 0.055
        for side in (-1, 1):
            x = ex + side * 0.12
            z = g(x, y)
            m.box(x, y, z - 0.1, 0.17, 0.022, 0.12, PAL["plaster"])
            m.roof(x, y, z + 0.02, 0.17, 0.024, 0.012, PAL["roof_dark"], over=0.006, lift=0.002, nu=2, nv=1, ridge_color=False)
    K.hall(m, g, ex, ey, 0.06, 0.06, 0.0, h=0.12, roof="roof", walls="red")
    K.hall(m, g, ex, ey + 0.19, 0.2, 0.07, 0.0, roof="roof", walls="red")
    # neighbourhoods
    avoid = [(-0.45, -1.15, 0.22, -0.72), (ex - 0.28, ey - 0.26, ex + 0.28, ey + 0.26), (-0.08, -0.72, 0.06, 1.3)]
    K.city_blocks(m, g, (0.05, 0.0, 1.5, 2.6), 0.08, seed=3, lot=0.085, street=0.03, fill=0.82, avoid=avoid, within=[(x * 0.93, y * 0.95) for x, y in walls])
    # suburbs along the canal to the north
    K.city_blocks(m, g, (0.2, 1.62, 0.7, 0.4), 0.1, seed=4, lot=0.085, fill=0.6)
    for (x, y) in river_local("Grand Canal", "hangzhou", 3.0, 6)[1:5]:
        K.barge(m, x, y, pi / 2, 0.22, z=max(g(x, y), 0.03) + 0.015)
    # hills west of the lake
    K.grove(m, g, -2.2, 0.3, 1.0, 70, seed=5, kinds=("broad", "pine", "broad"), s=0.09)
    K.grove(m, g, -1.3, -1.35, 0.55, 26, seed=6, kinds=("pine", "broad"), s=0.08)
    # shipping on the river
    for i, (x, y) in enumerate(((-1.6, -2.2), (0.5, -1.62), (1.7, -0.6), (2.3, 0.35))):
        K.junk(m, x, y, 0.35 + 0.4 * i, 0.3, masts=2, z=max(g(x, y), 0.03) + 0.012)


@landmark
def dadu(m, g):
    """Dadu (Khanbaliq), Khubilai's planned capital: grid streets, the Imperial City and its lake, the White Stupa."""
    x0, x1, y0, y1 = -1.2, 1.2, -1.35, 1.5
    outer = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    K.wall(m, g, outer, h=0.075, t=0.06, color="earth", tower_every=0.36, tower=0.1)
    for x, y in outer:
        K.hall(m, g, x, y, 0.16, 0.16, 0.0, h=0.05, roof="roof", walls="red", plat="earth", plat_h=0.1)
    for x in (-0.55, 0.0, 0.55):
        K.gate(m, g, x, y0, 0.2 if x == 0 else 0.16, 0.09, 0.0, body="earth")
    for x in (-0.45, 0.45):
        K.gate(m, g, x, y1, 0.16, 0.09, 0.0, body="earth")
    for y in (-0.75, 0.05, 0.85):
        K.gate(m, g, x1, y, 0.16, 0.09, pi / 2, body="earth")
        K.gate(m, g, x0, y, 0.16, 0.09, pi / 2, body="earth")
    # Imperial City with Taiye Pond, and the Palace City inside it
    imp = rect_poly(-0.15, -0.58, 1.2, 1.25)
    K.slab_on_ground(m, g, imp, "court", lift=0.005, n=8)
    K.wall(m, g, imp, h=0.045, t=0.035, color="red_dark")
    pond = [(-0.48, -1.05), (-0.22, -1.1), (-0.12, -0.62), (-0.2, -0.12), (-0.42, -0.18), (-0.52, -0.62)]
    K.pond(m, pond, g(0, 0) + 0.012)
    m.lathe(-0.33, -0.3, g(-0.33, -0.3) - 0.02, [(0.1, 0), (0.08, 0.05), (0.03, 0.09), (0.001, 0.1)], 10, PAL["grass"])
    K.hall(m, g, -0.33, -0.3, 0.06, 0.06, 0.0, roof="roof_green", z=g(-0.33, -0.3) + 0.08, h=0.03)
    pal = rect_poly(0.15, -0.8, 0.42, 0.62)
    K.wall(m, g, pal, h=0.05, t=0.03, color="red")
    K.gate(m, g, 0.15, -1.11, 0.14, 0.06, 0.0, roof="roof_yellow", body="red")
    K.hall(m, g, 0.15, -0.96, 0.28, 0.15, 0.0, roof="roof_yellow", walls="red", double=True)
    K.hall(m, g, 0.15, -0.62, 0.22, 0.12, 0.0, roof="roof_yellow", walls="red")
    for x in (-0.62, -0.7):
        K.hall(m, g, x, -0.85 if x == -0.62 else -0.35, 0.16, 0.1, pi / 2, roof="roof_green", walls="red")
    # Jishuitan, the harbour at the end of the Grand Canal
    jst = [(-0.78, 0.3), (-0.1, 0.26), (0.05, 0.52), (-0.28, 0.76), (-0.7, 0.66)]
    K.pond(m, jst, g(0, 0) + 0.012)
    for i, (x, y) in enumerate(((-0.55, 0.45), (-0.32, 0.55), (-0.12, 0.42), (-0.6, 0.6))):
        K.barge(m, x, y, 0.3 * i, 0.16, z=g(0, 0) + 0.02)
    K.grove(m, g, -0.42, 0.52, 0.45, 14, seed=9, kinds=("willow",), s=0.06, ring=0.33)
    # the White Stupa of Miaoying Temple (1279)
    compound(m, g, -0.92, -0.05, 0.3, 0.52, wall="red_dark", h=0.03)
    K.stupa(m, g, -0.92, 0.02, s=0.3)
    K.hall(m, g, -0.92, -0.2, 0.14, 0.08, 0.0, roof="roof", walls="red")
    # drum and bell towers at the city's heart
    K.hall(m, g, 0.12, 0.62, 0.16, 0.12, 0.0, roof="roof", walls="red", double=True, plat="earth", plat_h=0.12)
    K.hall(m, g, 0.12, 0.82, 0.11, 0.11, 0.0, roof="roof", walls="red", plat="brick_grey", plat_h=0.12)
    # the observatory: a raised platform with an armillary sphere and a gnomon
    ox, oy = 0.9, -1.02
    K.hall(m, g, ox, oy + 0.12, 0.14, 0.08, 0.0, roof="roof", walls="red")
    zp = g(ox, oy)
    m.box(ox, oy - 0.05, zp - 0.2, 0.22, 0.16, 0.3, PAL["brick_grey"], top=PAL["stone_light"])
    K.armillary(m, ox - 0.04, oy - 0.05, zp + 0.1, 0.045)
    m.box(ox + 0.07, oy - 0.05, zp + 0.1, 0.012, 0.012, 0.1, PAL["bronze"])
    # grid of hutong blocks
    avoid = [(-0.78, -1.24, 0.48, 0.1), (-0.8, 0.24, 0.08, 0.8), (-1.1, -0.34, -0.74, 0.24), (0.0, 0.5, 0.26, 0.92), (0.72, -1.22, 1.08, -0.84)]
    K.city_blocks(m, g, (0.0, 0.07, 2.25, 2.72), 0.0, seed=11, lot=0.09, street=0.04, fill=0.85, avoid=avoid)
    K.ribbon(m, g, [(0.0, y0), (0.0, y1)], 0.06, "road", lift=0.007, mat=0)
    K.ribbon(m, g, [(x0, 0.05), (x1, 0.05)], 0.05, "road", lift=0.007, mat=0)
    K.grove(m, g, -0.15, -0.58, 0.6, 18, seed=12, kinds=("broad", "pine"), s=0.06, avoid=[(0.0, -1.15, 0.4, -0.45)])


@landmark
def quanzhou(m, g):
    """Zayton: walls, the Kaiyuan Temple's twin stone pagodas, the Qingjing Mosque and a harbour full of ships."""
    walls = [(-1.15, -0.45), (-0.2, -0.62), (0.45, -0.35), (0.55, 0.45), (0.1, 0.95), (-0.9, 0.9), (-1.3, 0.3)]
    K.wall(m, g, walls, h=0.06, t=0.045, color="stone", tower_every=0.35)
    for x, y, r in ((-0.3, -0.58, 0.2), (0.5, 0.05, pi / 2), (-0.4, 0.92, 0.0), (-1.22, 0.1, pi / 2)):
        K.gate(m, g, x, y, 0.15, 0.08, r, body="stone")
    # Kaiyuan Temple: the Zhenguo and Renshou pagodas flank the great hall
    compound(m, g, -0.62, 0.42, 0.62, 0.36, wall="red_dark", h=0.03)
    K.pagoda(m, g, -0.84, 0.36, r=0.075, tiers=5, th=0.1, body="stone_light", roof="stone", taper=0.92)
    K.pagoda(m, g, -0.4, 0.36, r=0.075, tiers=5, th=0.1, body="stone_light", roof="stone", taper=0.92)
    K.hall(m, g, -0.62, 0.48, 0.2, 0.12, 0.0, roof="roof", walls="red", double=True)
    # Qingjing Mosque: the tall granite gateway with its pointed arch, and the prayer hall's walls
    mx, my = -0.12, -0.22
    z = g(mx, my)
    m.box(mx, my, z - 0.2, 0.1, 0.08, 0.2 + 0.16, PAL["stone_light"], top=PAL["stone"])
    m.box(mx, my - 0.041, z + 0.02, 0.04, 0.004, 0.1, PAL["black"])
    m.prism(mx, my - 0.041, z + 0.12, 0.02, 0.03, 4, PAL["black"], 0.002, rot=pi / 4)
    for dx, dy, w, d in ((0.12, 0.0, 0.2, 0.02), (0.12, 0.12, 0.2, 0.02), (0.22, 0.06, 0.02, 0.14)):
        m.box(mx + dx, my + dy, z - 0.2, w, d, 0.28, PAL["stone"])
    # neighbourhoods and the waterfront
    avoid = [(-0.95, 0.22, -0.3, 0.62), (-0.2, -0.32, 0.12, -0.08)]
    K.city_blocks(m, g, (-0.35, 0.15, 1.8, 1.6), 0.15, seed=21, lot=0.08, fill=0.82, avoid=avoid, within=walls, walls=("white", "plaster", "brick"))
    K.city_blocks(m, g, (0.7, -0.6, 0.6, 0.8), 0.6, seed=22, lot=0.08, fill=0.7, walls=("wood_light", "plaster"))
    # warehouses on the quay
    for i in range(5):
        x, y = 0.62 + 0.1 * i, -0.95 - 0.12 * i
        if g(x, y) > 0.05:
            K.house(m, g, x, y, 0.16, 0.08, -0.6, "wood", "roof")
    # the Cizao kilns in the hills west of the city
    K.kiln(m, g, -2.1, -0.6, -1.7, -0.4, 0.06, seed=3)
    # a harbour full of junks, with a few dhows from the Indian Ocean
    spots = water_spots(g, (0.9, -3.0, 3.0, 0.3), 16, seed=7, spacing=0.34)
    for i, (x, y) in enumerate(spots):
        hd = -0.9 + (i % 5) * 0.4
        if i % 5 == 4:
            K.dhow(m, x, y, hd, 0.3)
        else:
            K.junk(m, x, y, hd, 0.42 if i % 3 else 0.5, masts=3 if i % 3 else 2, sail="sail" if i % 4 == 1 else "sail_mat")
    K.grove(m, g, -1.9, 0.2, 0.9, 40, seed=23, kinds=("broad", "palm", "broad"), s=0.08)


@landmark
def jingdezhen(m, g):
    """The porcelain town: dragon kilns climbing the eastern hills, workshops, and boats loading wares."""
    K.ribbon(m, g, [(-1.3, -2.6), (-1.15, -1.2), (-1.0, 0.0), (-1.1, 1.3), (-0.95, 2.6)], 0.22)
    K.city_blocks(m, g, (-0.45, 0.0, 0.8, 2.0), 0.05, seed=31, lot=0.08, fill=0.8, walls=("white", "plaster"))
    for i, y in enumerate((-0.95, -0.35, 0.25, 0.85)):
        K.kiln(m, g, 0.25, y, 1.25, y + 0.22, 0.075, seed=30 + i)
        for k in range(3):
            K.house(m, g, 0.12 + 0.12 * k, y - 0.12, 0.11, 0.06, 0.0, "wood", "roof_thatch")
    # the imperial porcelain bureau
    compound(m, g, -0.35, 1.25, 0.34, 0.26, wall="brick_grey")
    K.hall(m, g, -0.35, 1.28, 0.16, 0.09, 0.0, roof="roof", walls="red")
    # stacks of blue-and-white wares on the quay
    for k in range(10):
        x, y = -0.86, -0.6 + 0.12 * k
        z = g(x, y)
        m.prism(x, y, z, 0.02, 0.045, 8, PAL["white"] if k % 2 else PAL["cobalt"], 0.016)
    for i, y in enumerate((-1.1, -0.3, 0.5, 1.4)):
        K.barge(m, -1.08 + 0.02 * i, y, pi / 2 + 0.1, 0.2)
    K.grove(m, g, 1.4, 0.0, 1.3, 70, seed=33, kinds=("pine", "broad", "pine"), s=0.08, avoid=[(0.2, -1.1, 1.3, 1.1)])


@landmark
def nanjing(m, g):
    """Early Ming Nanjing: the great wall, the palace, and the Porcelain Tower of Bao'en Temple."""
    walls = [(-1.1, -1.2), (0.2, -1.25), (1.3, -0.9), (1.35, 0.6), (0.9, 1.3), (-0.2, 1.35), (-1.2, 0.8), (-1.35, -0.3)]
    K.wall(m, g, walls, h=0.085, t=0.06, color="brick_grey", tower_every=0.32)
    K.gate(m, g, -0.3, -1.22, 0.28, 0.14, 0.0, body="brick_grey", h=0.1)  # Jubao Gate
    for x, y, r in ((1.32, -0.1, pi / 2), (0.3, 1.33, 0.0), (-1.28, 0.25, pi / 2)):
        K.gate(m, g, x, y, 0.16, 0.09, r)
    compound(m, g, 0.8, 0.0, 0.6, 0.75, wall="red", h=0.045, gate_roof="roof_yellow")
    K.hall(m, g, 0.8, 0.1, 0.3, 0.16, 0.0, roof="roof_yellow", walls="red", double=True)
    K.hall(m, g, 0.8, -0.2, 0.2, 0.1, 0.0, roof="roof_yellow", walls="red")
    lake = [(0.05, 1.5), (0.6, 1.45), (0.85, 1.75), (0.55, 2.1), (0.05, 2.0)]
    K.pond(m, lake, g(0.4, 1.7) + 0.01)
    K.pagoda(m, g, -0.25, -1.75, r=0.09, tiers=9, th=0.09, body="white", roof="roof_green", rail="roof_yellow")
    compound(m, g, -0.25, -1.9, 0.4, 0.5, wall="red_dark", h=0.03)
    K.city_blocks(m, g, (-0.1, 0.05, 2.5, 2.4), 0.0, seed=41, lot=0.09, fill=0.8, within=walls, avoid=[(0.45, -0.42, 1.15, 0.42)])
    K.grove(m, g, 1.8, 0.8, 0.8, 30, seed=42, kinds=("broad", "pine"), s=0.08)


@landmark
def liujiagang(m, g):
    """Liujiagang, where Zheng He's treasure fleets assembled: the fleet at anchor and the Tianfei temple."""
    compound(m, g, 0.25, -0.35, 0.3, 0.26, wall="red_dark")
    K.hall(m, g, 0.25, -0.32, 0.14, 0.08, 0.0, roof="roof", walls="red")
    K.city_blocks(m, g, (-0.6, -0.9, 1.4, 0.9), 0.3, seed=51, lot=0.08, fill=0.7)
    spots = water_spots(g, (-2.8, 0.5, 2.5, 3.0), 16, seed=5, spacing=0.55)
    for i, (x, y) in enumerate(spots):
        if i < 7:
            K.treasure_ship(m, x, y, -0.4 + 0.15 * i, 0.72)
        else:
            K.junk(m, x, y, -0.3 + 0.2 * i, 0.4, masts=3)


@landmark
def village(m, g):
    """A lineage village in Jiangnan: ancestral hall, half-moon pond, white walls, rice paddies, family graves."""
    # the ancestral hall and its forecourt
    compound(m, g, 0.05, 0.28, 0.34, 0.3, wall="white", h=0.04, gate_roof="roof_dark")
    K.hall(m, g, 0.05, 0.33, 0.2, 0.12, 0.0, roof="roof_dark", walls="red", double=True)
    K.pond(m, [(-0.12, -0.02), (0.22, -0.02), (0.18, -0.12), (0.05, -0.16), (-0.08, -0.12)], g(0.05, -0.08) + 0.012)
    # a memorial archway at the village entrance
    zx = g(0.05, -0.55)
    for dx in (-0.06, 0.06):
        m.box(0.05 + dx, -0.55, zx - 0.1, 0.018, 0.018, 0.2, PAL["stone"])
    m.box(0.05, -0.55, zx + 0.08, 0.16, 0.022, 0.025, PAL["stone"])
    m.roof(0.05, -0.55, zx + 0.105, 0.15, 0.03, 0.025, PAL["roof_dark"], over=0.01, lift=0.008, nu=2, nv=1)
    # houses: whitewashed walls and dark tiles
    rnd = random.Random(61)
    for k in range(34):
        a = rnd.random() * 2 * pi
        r = 0.2 + 0.45 * math.sqrt(rnd.random())
        x, y = 0.05 + cos(a) * r * 1.2, 0.2 + sin(a) * r
        if hypot(x - 0.05, y - 0.28) < 0.24 or (abs(x - 0.05) < 0.2 and -0.2 < y < 0.0):
            continue
        K.house(m, g, x, y, rnd.uniform(0.07, 0.1), rnd.uniform(0.05, 0.065), rnd.choice((0.0, 0.0, pi / 2)), "white", rnd.choice(("roof_house", "roof_house2")), h=0.06)
    # paddies on the valley floor
    K.paddies(m, g, 0.9, 0.35, 0.9, 1.5, 0.1, nx=6, ny=9, seed=62)
    K.paddies(m, g, 0.1, 1.0, 1.1, 0.5, 0.05, nx=7, ny=3, seed=63)
    K.paddies(m, g, 0.2, -1.0, 1.2, 0.5, -0.1, nx=7, ny=3, seed=64)
    # family graves on the hillside to the west
    for k in range(7):
        x, y = -0.95 - 0.08 * (k % 3), 0.1 + 0.12 * k
        z = g(x, y)
        m.lathe(x, y, z - 0.02, [(0.035, 0), (0.028, 0.02), (0.001, 0.03)], 8, PAL["grass"])
        m.box(x + 0.035, y, z - 0.02, 0.008, 0.028, 0.045, PAL["stone"])
    K.grove(m, g, -1.3, 0.0, 0.9, 45, seed=65, kinds=("pine", "broad"), s=0.08)
    K.grove(m, g, 0.2, -1.6, 0.6, 20, seed=66, kinds=("broad", "pine"), s=0.08)
    for x, y in ((-0.25, -0.3), (0.35, -0.35), (-0.35, 0.55)):
        K.tree(m, g, x, y, 0.13, "broad", seed=int(abs(x) * 100 + abs(y) * 10))


@landmark
def terraces(m, g):
    """Rice terraces carved into a hill, where fast-ripening Champa rice could be grown."""
    top = K.terraces(m, g, 0.0, 0.0, r=1.0, levels=9, seed=71, hstep=0.055)
    K.terraces(m, g, 1.25, 0.9, r=0.55, levels=6, seed=72, hstep=0.05)
    for k in range(6):
        K.house(m, g, 1.15 + 0.12 * (k % 3), -0.9 - 0.1 * (k // 3), 0.09, 0.06, 0.2, "white", "roof_thatch")
    K.grove(m, g, 0.0, 0.0, 1.9, 60, seed=73, kinds=("pine", "broad"), s=0.09, ring=1.15)
    m.lathe(0.0, 0.0, top - 0.02, [(0.12, 0), (0.08, 0.06), (0.001, 0.08)], 10, PAL["grass"])


# ======================================================================================== Korea & Japan
@landmark
def haeinsa(m, g):
    """Haeinsa: a mountain monastery on terraces, with the long Janggyeong Panjeon halls that hold the Tripitaka."""
    K.gate(m, g, 0.0, -0.72, 0.1, 0.05, 0.0, body="wood", hall_color="red", h=0.03)
    K.hall(m, g, 0.0, -0.46, 0.16, 0.08, 0.0, roof="roof", walls="red")
    compound(m, g, 0.0, -0.05, 0.5, 0.48, wall="plaster", h=0.03)
    K.hall(m, g, 0.0, 0.05, 0.26, 0.14, 0.0, roof="roof", walls="red", double=True)
    K.pagoda(m, g, 0.0, -0.18, r=0.03, tiers=3, th=0.045, body="stone", roof="stone_dark", sides=4, taper=0.85)
    for x in (-0.18, 0.18):
        K.hall(m, g, x, -0.12, 0.1, 0.07, pi / 2, roof="roof", walls="red")
    # Janggyeong Panjeon: two long, plain storage halls with slatted windows
    for y in (0.4, 0.58):
        z0, z1 = K.footprint_z(g, 0.0, y, 0.72, 0.1)
        m.box(0.0, y, z0 - 0.3, 0.8, 0.13, z1 - z0 + 0.3 + 0.03, PAL["stone"], top=PAL["stone_light"])
        m.box(0.0, y, z1 + 0.03, 0.72, 0.09, 0.07, PAL["wood_light"])
        for k in range(12):
            m.box(-0.33 + 0.06 * k, y - 0.046, z1 + 0.05, 0.03, 0.003, 0.03, PAL["wood_dark"])
        m.roof(0.0, y, z1 + 0.1, 0.74, 0.1, 0.05, PAL["roof"], over=0.02, lift=0.012, nu=4, nv=2)
    K.wall(m, g, rect_poly(0.0, 0.49, 0.88, 0.34), h=0.025, t=0.02, color="plaster")
    K.grove(m, g, 0.0, 0.0, 2.1, 140, seed=81, kinds=("pine", "pine", "broad"), s=0.09, avoid=[(-0.5, -0.8, 0.5, 0.72)])


@landmark
def kyoto(m, g):
    """Kinkaku, the Golden Pavilion (1397), on its Mirror Pond, with the city's grid in the distance."""
    pond = [(-0.5, -0.5), (-0.1, -0.62), (0.4, -0.55), (0.55, -0.15), (0.35, 0.12), (0.1, 0.05), (-0.25, 0.15), (-0.55, -0.1)]
    zp = g(0, 0) + 0.01
    K.pond(m, pond, zp, "pond", "stone_dark")
    for x, y, r in ((-0.15, -0.3, 0.08), (0.2, -0.35, 0.06), (-0.35, -0.2, 0.05)):
        m.lathe(x, y, zp - 0.03, [(r, 0), (r * 0.8, 0.035), (0.001, 0.05)], 8, PAL["grass"])
        K.tree(m, g, x, y, 0.07, "pine", seed=int(r * 1000), z=zp + 0.02)
    K.kinkaku(m, g, 0.1, 0.1, s=0.3, rot=0.0, z=zp - 0.01)
    K.hall(m, g, 0.45, 0.55, 0.3, 0.16, 0.2, roof="roof_brown", walls="wood_light")
    K.hall(m, g, -0.35, 0.6, 0.14, 0.1, -0.1, roof="roof_thatch", walls="wood_light")
    K.grove(m, g, 0.0, 0.0, 2.2, 120, seed=91, kinds=("pine", "broad", "broad"), s=0.09, avoid=[(-0.7, -0.75, 0.8, 0.8), (0.6, -2.6, 2.8, -0.6)])
    # the gridded city to the south-east, with the five-storey pagoda of To-ji
    for i in range(7):
        for j in range(6):
            x, y = 0.8 + i * 0.28, -0.75 - j * 0.3
            if (i + j) % 3 == 0:
                continue
            K.house(m, g, x, y, 0.13, 0.08, 0.0, "plaster", "roof_brown")
    K.pagoda(m, g, 2.3, -2.2, r=0.07, tiers=5, th=0.1, body="red", roof="roof_brown", sides=4, taper=0.88)


# ======================================================================================== second batch
@landmark
def kaifeng(m, g):
    """Kaifeng, the Northern Song capital: nested walls, the Bian canal, the Iron Pagoda (1049)."""
    outer = rect_poly(0.0, 0.0, 2.1, 2.0)
    K.wall(m, g, outer, h=0.07, t=0.055, color="earth", tower_every=0.34)
    inner = rect_poly(0.0, 0.1, 1.1, 1.0)
    K.wall(m, g, inner, h=0.055, t=0.045, color="brick_grey")
    for x, y, r in ((0.0, -1.0, 0.0), (0.0, 1.0, 0.0), (1.05, 0.0, pi / 2), (-1.05, 0.0, pi / 2), (0.0, -0.4, 0.0)):
        K.gate(m, g, x, y, 0.16, 0.09, r, body="earth" if abs(y) > 0.9 or abs(x) > 0.9 else "brick_grey")
    compound(m, g, 0.0, 0.3, 0.46, 0.4, wall="red", h=0.04)
    K.hall(m, g, 0.0, 0.33, 0.26, 0.14, 0.0, roof="roof_green", walls="red", double=True)
    K.ribbon(m, g, [(-1.6, -0.55), (-0.6, -0.62), (0.4, -0.55), (1.6, -0.7)], 0.1)
    for x in (-0.5, 0.35):
        K.bridge(m, x, -0.7, x + 0.02, -0.45, g(x, -0.6) + 0.025, 0.05, piers=2)
    K.pagoda(m, g, 0.62, 0.62, r=0.05, tiers=11, th=0.075, body="brick", roof="wood_dark", taper=0.95)  # the Iron Pagoda
    K.city_blocks(m, g, (0.0, 0.0, 2.0, 1.9), 0.0, seed=101, lot=0.09, fill=0.8, avoid=[(-0.25, 0.08, 0.25, 0.52), (-1.1, -0.72, 1.1, -0.44), (0.5, 0.5, 0.75, 0.75)])
    # the arsenal yard where the Wujing zongyao's weapons were made
    compound(m, g, -0.72, 0.65, 0.34, 0.26, wall="brick_grey", h=0.03)
    for k in range(3):
        K.house(m, g, -0.82 + 0.1 * k, 0.68, 0.08, 0.14, 0.0, "wood", "roof")
    for k in range(4):
        K.pile(m, g, -0.62 + 0.05 * k, 0.56, 0.02, 0.03, "black")


@landmark
def hanseong(m, g):
    """Hanseong (Seoul), capital of Joseon from 1394: Gyeongbokgung palace under the northern peaks, walls and Sungnyemun."""
    loop = [(-1.1, -0.9), (0.0, -1.2), (1.05, -0.95), (1.3, -0.1), (1.15, 0.85), (0.4, 1.35), (-0.45, 1.3), (-1.15, 0.7), (-1.35, -0.1)]
    K.wall(m, g, loop, h=0.05, t=0.04, color="stone", tower_every=0.0)
    K.gate(m, g, 0.0, -1.2, 0.22, 0.1, 0.0, body="stone", h=0.07)  # Sungnyemun, the south gate (1398)
    K.gate(m, g, 1.25, -0.1, 0.16, 0.08, pi / 2, body="stone")
    compound(m, g, 0.0, 0.62, 0.62, 0.62, wall="plaster", h=0.035, gate_roof="roof")
    K.hall(m, g, 0.0, 0.58, 0.3, 0.16, 0.0, roof="roof", walls="red", double=True, plat_h=0.06)
    K.hall(m, g, 0.0, 0.82, 0.22, 0.12, 0.0, roof="roof", walls="red")
    pond = rect_poly(-0.2, 0.84, 0.16, 0.12)
    K.pond(m, pond, g(-0.2, 0.84) + 0.012)
    K.hall(m, g, -0.2, 0.84, 0.12, 0.08, 0.0, roof="roof", walls="red", z=g(-0.2, 0.84) + 0.02)
    K.ribbon(m, g, [(0.0, 0.3), (0.0, -1.15)], 0.06, "road", lift=0.008, mat=0)
    K.city_blocks(m, g, (0.0, -0.3, 2.3, 1.7), 0.0, seed=111, lot=0.085, fill=0.78, within=loop, avoid=[(-0.36, 0.28, 0.36, 0.96), (-0.06, -1.2, 0.06, 0.3)], roofs=("roof_house", "roof_house2", "roof_thatch"))
    K.grove(m, g, 0.2, 1.9, 0.8, 50, seed=112, kinds=("pine", "pine", "broad"), s=0.09)


@landmark
def cheongju(m, g):
    """Heungdeoksa, the temple where the Jikji was printed with metal type in 1377."""
    compound(m, g, 0.0, 0.0, 0.46, 0.4, wall="plaster", h=0.03)
    K.hall(m, g, 0.0, 0.06, 0.24, 0.13, 0.0, roof="roof", walls="red")
    K.pagoda(m, g, 0.0, -0.1, r=0.03, tiers=3, th=0.045, body="stone", roof="stone_dark", sides=4, taper=0.85)
    K.hall(m, g, 0.14, -0.05, 0.08, 0.1, pi / 2, roof="roof", walls="wood_light")  # the print shop
    K.city_blocks(m, g, (0.0, -0.7, 1.4, 0.7), 0.1, seed=121, lot=0.09, fill=0.6, roofs=("roof_house", "roof_thatch"))
    K.grove(m, g, 0.0, 0.3, 1.2, 50, seed=122, kinds=("pine", "broad"), s=0.09, avoid=[(-0.3, -1.1, 0.8, 0.3)])


@landmark
def bailudong(m, g):
    """The White Deer Grotto Academy below Mount Lu, revived by Zhu Xi in 1179."""
    for k, (x, y) in enumerate(((0.0, -0.25), (0.0, 0.05), (0.0, 0.33))):
        compound(m, g, x, y, 0.34, 0.24, wall="plaster", h=0.028, gate_roof="roof_dark")
        K.hall(m, g, x, y + 0.02, 0.2, 0.1, 0.0, roof="roof_dark", walls="red" if k == 1 else "wood_light")
    K.hall(m, g, 0.3, 0.05, 0.12, 0.2, 0.0, roof="roof_dark", walls="wood_light")  # the library
    K.ribbon(m, g, [(-0.6, -0.9), (-0.35, -0.3), (-0.3, 0.3), (-0.45, 0.9)], 0.07, lift=0.01)
    K.bridge(m, -0.42, -0.25, -0.24, -0.25, g(-0.34, -0.25) + 0.03, 0.04, piers=1)
    # the forested shoulder of Mount Lu behind the academy
    base = g(0.0, 0.9)
    m.lathe(0.0, 1.25, base - 0.1, [(1.0, 0), (0.8, 0.12), (0.5, 0.28), (0.2, 0.4), (0.001, 0.44)], 14, PAL["tree"],
            colors=[PAL["grass"], PAL["tree_light"], PAL["tree"], PAL["stone"], PAL["stone"]])
    K.grove(m, g, 0.0, 0.2, 1.4, 70, seed=131, kinds=("pine", "broad", "pine"), s=0.09, avoid=[(-0.25, -0.45, 0.45, 0.5)])
    for k in range(9):
        a = k * 0.7
        K.tree(m, g, 0.6 * cos(a), 1.25 + 0.55 * sin(a), 0.1, "pine", seed=k, z=base + 0.12)


@landmark
def iron(m, g):
    """Northern ironworks: blast furnaces, water-driven bellows, and heaps of ore, coal and charcoal."""
    for k, (x, y) in enumerate(((-0.35, -0.1), (0.05, 0.05), (0.42, -0.15), (0.1, -0.5))):
        K.furnace(m, g, x, y, 0.13, seed=140 + k)
    K.ribbon(m, g, [(-1.0, 0.6), (-0.5, 0.35), (0.2, 0.3), (0.9, 0.5)], 0.08, lift=0.012)
    for x in (-0.45, 0.15):
        K.waterwheel(m, x, 0.26, g(x, 0.3) + 0.01, 0.06, 0.0)
    for k in range(6):
        K.pile(m, g, -0.7 + 0.12 * k, -0.45 - 0.04 * (k % 2), 0.05, 0.05, ("black", "brick", "dirt")[k % 3])
    for k in range(5):
        K.house(m, g, 0.6 + 0.12 * (k % 3), 0.05 + 0.12 * (k // 3), 0.1, 0.06, 0.0, "wood", "roof_thatch")
    # mine adits in the hillside
    for x, y in ((-0.9, -0.6), (-1.0, -0.2)):
        z = g(x, y)
        m.box(x, y, z - 0.05, 0.06, 0.02, 0.09, PAL["black"], 0.3)
        m.box(x, y, z + 0.04, 0.08, 0.03, 0.015, PAL["wood"], 0.3)
    K.grove(m, g, 0.0, 0.0, 1.5, 40, seed=141, kinds=("pine",), s=0.08, ring=0.95)


@landmark
def chengdu(m, g):
    """Chengdu in Sichuan, where the Song first printed government paper money."""
    walls = rect_poly(0.0, 0.0, 1.6, 1.4)
    K.wall(m, g, walls, h=0.06, t=0.05, color="brick_grey", tower_every=0.4)
    for x, y, r in ((0.0, -0.7, 0.0), (0.0, 0.7, 0.0), (0.8, 0.0, pi / 2), (-0.8, 0.0, pi / 2)):
        K.gate(m, g, x, y, 0.15, 0.08, r)
    compound(m, g, 0.0, 0.1, 0.36, 0.3, wall="red_dark", h=0.03)
    K.hall(m, g, 0.0, 0.12, 0.2, 0.1, 0.0, roof="roof", walls="red")  # the paper-money bureau
    K.city_blocks(m, g, (0.0, 0.0, 1.5, 1.3), 0.0, seed=151, lot=0.085, fill=0.8, avoid=[(-0.2, -0.07, 0.2, 0.27)])
    K.ribbon(m, g, [(-1.4, 0.9), (-0.95, 0.0), (-0.6, -0.9), (0.4, -1.1), (1.4, -1.0)], 0.12)
    K.grove(m, g, 0.0, 0.0, 1.8, 50, seed=152, kinds=("broad", "broad", "pine"), s=0.08, ring=1.05)


def canal_town(m, g, anchor, seed, granaries=4, walls=True, locks=0):
    pts = river_local("Grand Canal", anchor, 2.6, 3)
    K.ribbon(m, g, pts, 0.16, lift=0.014)
    rnd = random.Random(seed)
    for k in range(3, len(pts) - 3, 5):
        x, y = pts[k]
        nx, ny = pts[k + 1][0] - x, pts[k + 1][1] - y
        K.barge(m, x, y, math.atan2(ny, nx), 0.2, z=g(x, y) + 0.03)
    if locks:
        for k in range(1, locks + 1):
            x, y = pts[len(pts) * k // (locks + 1)]
            x2, y2 = pts[len(pts) * k // (locks + 1) + 1]
            a = math.atan2(y2 - y, x2 - x) + pi / 2
            z = g(x, y)
            for side in (-1, 1):
                m.box(x + cos(a) * side * 0.09, y + sin(a) * side * 0.09, z - 0.1, 0.05, 0.03, 0.16, PAL["stone"], a)
            m.box(x, y, z + 0.05, 0.22, 0.025, 0.012, PAL["wood"], a)
    if walls:
        wl = [(-0.7, -0.6), (0.7, -0.6), (0.7, 0.6), (-0.7, 0.6)]
        K.wall(m, g, wl, h=0.05, t=0.04, color="brick_grey", tower_every=0.45)
    K.city_blocks(m, g, (0.0, 0.0, 1.3, 1.1), 0.0, seed=seed, lot=0.08, fill=0.75, avoid=[(p[0] - 0.12, p[1] - 0.12, p[0] + 0.12, p[1] + 0.12) for p in pts[::2]])
    for k in range(granaries):
        x, y = 0.9 + 0.14 * (k % 2), -0.3 + 0.2 * (k // 2)
        K.house(m, g, x, y, 0.2, 0.08, 0.0, "plaster", "roof_house")
    return pts


@landmark
def yangzhou(m, g):
    """Yangzhou, where the Grand Canal meets the Yangzi: barges, warehouses and a walled market town."""
    canal_town(m, g, "yangzhou", 161, granaries=6)


@landmark
def linqing(m, g):
    """Linqing, a canal town of locks and granaries on the way north to Dadu."""
    canal_town(m, g, "linqing", 171, granaries=8, walls=False, locks=2)


@landmark
def hakata(m, g):
    """Hakata Bay: the stone wall the samurai built after 1274, and the Mongol fleet of 1281 offshore."""
    line = [(-2.2, -0.85), (-1.6, -0.42), (-1.05, 0.12), (-0.62, 0.78), (-0.32, 1.45), (0.0, 2.1)]
    for (x0, y0), (x1, y1) in zip(line[:-1], line[1:]):
        L = hypot(x1 - x0, y1 - y0)
        n = max(1, int(L / 0.12))
        for k in range(n):
            t0, t1 = k / n, (k + 1) / n
            xa, ya = x0 + (x1 - x0) * (t0 + t1) / 2, y0 + (y1 - y0) * (t0 + t1) / 2
            z = g(xa, ya)
            m.box(xa, ya, z - 0.2, L / n * 1.03, 0.06, 0.2 + 0.05, PAL["stone"], math.atan2(y1 - y0, x1 - x0), top=PAL["stone_light"])
    rnd = random.Random(181)
    for k in range(14):
        t = rnd.random()
        i = min(int(t * (len(line) - 1)), len(line) - 2)
        f = t * (len(line) - 1) - i
        x = line[i][0] + (line[i + 1][0] - line[i][0]) * f + 0.2
        y = line[i][1] + (line[i + 1][1] - line[i][1]) * f - 0.1
        K.tent(m, g, x + rnd.uniform(0, 0.25), y + rnd.uniform(-0.1, 0.1), 0.06, rnd.random(), "white", rnd.choice(("black", "red")))
    K.torii(m, g, 0.2, 0.1, 0.12, 0.6)
    K.hall(m, g, 0.35, 0.3, 0.2, 0.12, 0.6, roof="roof_brown", walls="red")  # Hakozaki shrine
    K.city_blocks(m, g, (0.55, -0.4, 0.8, 0.7), 0.3, seed=182, lot=0.08, fill=0.6, walls=("wood_light", "plaster"), roofs=("roof_brown", "roof_thatch"))
    for i, (x, y) in enumerate(water_spots(g, (-2.6, -0.2, -0.3, 2.6), 14, seed=183, spacing=0.4)):
        K.junk(m, x, y, 0.8 + 0.3 * (i % 4), 0.34, masts=2, sail="sail_mat", hull="hull_dark")
    K.grove(m, g, 1.4, 0.8, 1.0, 50, seed=184, kinds=("pine", "broad"), s=0.09)


@landmark
def bachdang(m, g):
    """The Bach Dang estuary, 1288: iron-tipped stakes hidden at high tide wreck the Mongol fleet on the ebb."""
    rnd = random.Random(191)
    for row, y in enumerate((-0.25, -0.55, -0.85, -1.15)):
        for k in range(26):
            x = -0.3 + 0.085 * k + rnd.uniform(-0.02, 0.02)
            yy = y + rnd.uniform(-0.04, 0.04)
            if g(x, yy) > 0.02:
                continue
            K.stake(m, x, yy, 0.0, 0.1 + rnd.uniform(0, 0.05), 0.012, rnd.random(), "wood_dark")
    for k, (x, y) in enumerate(((0.4, -0.4), (1.0, -0.7), (0.7, -1.0), (1.4, -0.3), (0.2, -0.9))):
        K.junk(m, x, y, 0.9 + 0.5 * k, 0.34, masts=2, sail="sail_mat", hull="hull_dark", z=-0.03 - 0.02 * (k % 2))
    for k, (x, y) in enumerate(((-0.6, -1.6), (-0.3, -1.8), (0.2, -1.9), (-0.9, -1.2))):
        K.sampan(m, x, y, 0.3 * k, 0.14)
    K.city_blocks(m, g, (-1.5, 0.3, 0.8, 0.7), 0.2, seed=192, lot=0.08, fill=0.5, roofs=("roof_thatch", "roof_house"))
    K.grove(m, g, -1.5, -0.4, 1.2, 50, seed=193, kinds=("broad", "palm", "broad"), s=0.08)


@landmark
def ganghwa(m, g):
    """Ganghwa Island, where the Goryeo court held out against the Mongols (1232–1270)."""
    ring = [(-0.4, -0.2), (0.3, -0.35), (0.75, 0.1), (0.7, 0.8), (0.1, 1.0), (-0.45, 0.6)]
    K.wall(m, g, ring, h=0.05, t=0.04, color="earth", tower_every=0.35)
    compound(m, g, 0.15, 0.35, 0.4, 0.3, wall="red_dark", h=0.03)
    K.hall(m, g, 0.15, 0.38, 0.22, 0.12, 0.0, roof="roof", walls="red", double=True)
    K.city_blocks(m, g, (0.15, 0.35, 1.1, 1.2), 0.0, seed=201, lot=0.085, fill=0.6, within=ring, avoid=[(-0.1, 0.18, 0.4, 0.55)], roofs=("roof_house", "roof_thatch"))
    K.grove(m, g, 0.3, 0.8, 1.4, 50, seed=202, kinds=("pine", "broad"), s=0.09, ring=0.9)


@landmark
def kamakura(m, g):
    """Kamakura, the shogun's city: the Great Buddha, the Hachiman shrine and the Zen temples in the hills."""
    K.buddha(m, g, -0.6, 0.25, 0.32, -0.3)
    K.ribbon(m, g, [(0.3, -0.7), (0.3, 0.45)], 0.07, "road", lift=0.008, mat=0)
    for y in (-0.5, -0.1):
        K.torii(m, g, 0.3, y, 0.13)
    compound(m, g, 0.3, 0.62, 0.36, 0.3, wall="red", h=0.03)
    K.hall(m, g, 0.3, 0.66, 0.2, 0.1, 0.0, roof="roof_green", walls="red")
    compound(m, g, 0.7, 1.25, 0.34, 0.4, wall="plaster", h=0.03)  # Kencho-ji, Zen temple (1253)
    K.hall(m, g, 0.7, 1.3, 0.2, 0.12, 0.0, roof="roof_brown", walls="wood_light", double=True)
    K.city_blocks(m, g, (0.2, -0.2, 1.3, 0.9), 0.0, seed=211, lot=0.08, fill=0.6, avoid=[(0.2, -0.75, 0.4, 0.8), (-0.85, 0.0, -0.35, 0.5)], walls=("wood_light", "plaster"), roofs=("roof_brown", "roof_thatch"))
    K.grove(m, g, -0.3, 1.1, 1.2, 70, seed=212, kinds=("pine", "broad", "cypress"), s=0.09, avoid=[(0.45, 1.0, 0.95, 1.5), (0.1, 0.4, 0.5, 0.85)])


@landmark
def kaesong(m, g):
    """Kaesong, the Goryeo capital: the Manwoldae palace terraces below Mount Songak."""
    for k in range(3):
        y = 0.35 + 0.18 * k
        z0, z1 = K.footprint_z(g, 0.0, y, 0.6 - 0.1 * k, 0.16)
        m.box(0.0, y, z0 - 0.2, 0.6 - 0.1 * k, 0.16, z1 - z0 + 0.2 + 0.04 * (k + 1), PAL["stone"], top=PAL["stone_light"])
    K.hall(m, g, 0.0, 0.72, 0.26, 0.13, 0.0, roof="roof", walls="red", double=True, plat_h=0.14)
    loop = [(-1.1, -0.7), (0.9, -0.8), (1.2, 0.3), (0.6, 1.2), (-0.7, 1.1), (-1.3, 0.2)]
    K.wall(m, g, loop, h=0.045, t=0.04, color="earth", tower_every=0.5)
    K.city_blocks(m, g, (0.0, -0.2, 2.0, 1.1), 0.0, seed=221, lot=0.085, fill=0.7, within=loop, roofs=("roof_house", "roof_thatch"))
    K.grove(m, g, 0.0, 1.5, 0.9, 50, seed=222, kinds=("pine",), s=0.09)


@landmark
def thanglong(m, g):
    """Thang Long (Hanoi): the royal citadel, the One Pillar Pagoda and the Temple of Literature."""
    cit = rect_poly(0.0, 0.25, 0.9, 0.8)
    K.wall(m, g, cit, h=0.05, t=0.045, color="brick", tower_every=0.45)
    K.gate(m, g, 0.0, -0.15, 0.16, 0.08, 0.0, body="brick")
    K.hall(m, g, 0.0, 0.35, 0.28, 0.15, 0.0, roof="roof_yellow", walls="red", double=True, plat_h=0.08)
    K.one_pillar(m, g, -0.7, 0.35, 0.12)
    compound(m, g, -0.4, -0.75, 0.28, 0.5, wall="brick", h=0.03)  # Van Mieu, the Temple of Literature (1070)
    K.hall(m, g, -0.4, -0.62, 0.18, 0.09, 0.0, roof="roof_dark", walls="red")
    K.pond(m, rect_poly(-0.4, -0.88, 0.12, 0.08), g(-0.4, -0.88) + 0.012)
    K.city_blocks(m, g, (0.5, -0.8, 1.2, 0.9), 0.0, seed=231, lot=0.08, fill=0.7, roofs=("roof_house", "roof_thatch"))
    K.grove(m, g, 0.0, 0.0, 1.7, 50, seed=232, kinds=("broad", "palm", "broad"), s=0.08, ring=1.1)


@landmark
def karakorum(m, g):
    """Karakorum: a small walled city of palaces and temples inside a sea of felt gers."""
    walls = rect_poly(0.0, 0.0, 0.8, 0.9)
    K.wall(m, g, walls, h=0.04, t=0.035, color="earth")
    for x, y, r in ((0.0, -0.45, 0.0), (0.0, 0.45, 0.0), (0.4, 0.0, pi / 2), (-0.4, 0.0, pi / 2)):
        K.gate(m, g, x, y, 0.12, 0.07, r, body="earth")
    K.hall(m, g, 0.0, 0.2, 0.24, 0.14, 0.0, roof="roof_green", walls="red", plat_h=0.06)  # Tumen Amgalan palace
    z = g(0.0, 0.0)
    m.prism(0.0, 0.0, z, 0.006, 0.12, 6, PAL["gold"], 0.004, mat=3)  # the silver tree fountain
    m.sphere(0.0, 0.0, z + 0.1, 0.035, PAL["gold"], n=7, rings=4, mat=3)
    K.hall(m, g, -0.2, -0.2, 0.12, 0.1, 0.0, roof="roof", walls="red")
    K.city_blocks(m, g, (0.0, -0.1, 0.7, 0.8), 0.0, seed=241, lot=0.085, fill=0.5, avoid=[(-0.15, 0.1, 0.15, 0.3), (-0.3, -0.3, -0.1, -0.1)], roofs=("roof_house", "roof_thatch"))
    rnd = random.Random(242)
    n = 0
    while n < 70:
        a = rnd.random() * 2 * pi
        r = 0.6 + 0.9 * rnd.random()
        K.ger(m, g, cos(a) * r, sin(a) * r * 0.85, 0.035 + 0.01 * rnd.random())
        n += 1


@landmark
def shangdu(m, g):
    """Shangdu (Xanadu), Khubilai's summer capital on the grassland."""
    K.wall(m, g, rect_poly(0.0, 0.0, 1.2, 1.2), h=0.045, t=0.04, color="earth", tower_every=0.4)
    K.wall(m, g, rect_poly(0.1, 0.1, 0.6, 0.6), h=0.04, t=0.035, color="brick_grey")
    K.hall(m, g, 0.1, 0.2, 0.24, 0.14, 0.0, roof="roof_yellow", walls="red", plat_h=0.12)  # Da'an Pavilion
    K.gate(m, g, 0.0, -0.6, 0.14, 0.07, 0.0, body="earth")
    rnd = random.Random(251)
    for k in range(40):
        a = rnd.random() * 2 * pi
        r = 0.85 + 0.6 * rnd.random()
        K.ger(m, g, cos(a) * r, sin(a) * r, 0.035)


@landmark
def champa(m, g):
    """Cham brick temple towers of Vijaya, capital of Champa."""
    for k, (x, y, s) in enumerate(((0.0, 0.0, 0.3), (-0.28, 0.06, 0.2), (0.25, 0.08, 0.22), (0.05, -0.3, 0.16))):
        K.cham_tower(m, g, x, y, s)
    K.city_blocks(m, g, (0.2, -0.9, 1.2, 0.6), 0.2, seed=261, lot=0.08, fill=0.5, roofs=("roof_thatch",), walls=("wood_light",))
    K.grove(m, g, 0.0, 0.0, 1.4, 60, seed=262, kinds=("palm", "broad", "palm"), s=0.09, ring=0.5)


@landmark
def sakya(m, g):
    """Sakya Monastery, seat of the 'Phags-pa Lama, with its grey walls banded red and white."""
    walls = rect_poly(0.0, 0.0, 0.8, 0.8)
    K.striped_wall(m, g, walls, h=0.1, t=0.06)
    for x, y in walls:
        z = g(x, y)
        m.box(x, y, z - 0.2, 0.12, 0.12, 0.34, PAL["stone_dark"])
    z0, z1 = K.footprint_z(g, 0.0, 0.05, 0.4, 0.34)
    m.box(0.0, 0.05, z0 - 0.2, 0.42, 0.36, z1 - z0 + 0.2 + 0.2, PAL["stone_dark"], top=PAL["roof_dark"])
    for k in range(6):
        m.box(-0.18 + 0.072 * k, -0.131, z1 + 0.02, 0.036, 0.004, 0.16, PAL["red" if k % 2 else "white"])
    m.box(0.0, 0.05, z1 + 0.2, 0.16, 0.12, 0.06, PAL["gold"], mat=3)
    for k in range(18):
        a = k * 0.35
        r = 0.6 + 0.12 * (k % 3)
        K.house(m, g, cos(a) * r, sin(a) * r, 0.07, 0.06, a, "white", "stone_dark", h=0.05)


@landmark
def wuyi(m, g):
    """The Wuyi Mountains, where Zhu Xi taught at his own academy."""
    compound(m, g, 0.0, 0.0, 0.3, 0.24, wall="plaster", h=0.025, gate_roof="roof_dark")
    K.hall(m, g, 0.0, 0.03, 0.17, 0.09, 0.0, roof="roof_dark", walls="wood_light")
    K.ribbon(m, g, [(-1.2, -0.8), (-0.5, -0.35), (0.2, -0.5), (0.8, -0.2), (1.3, -0.5)], 0.1, lift=0.012)
    for x, y, r in ((-0.6, 0.5, 0.25), (0.5, 0.55, 0.3), (0.9, -0.9, 0.22), (-0.9, -0.3, 0.2)):
        base = g(x, y)
        m.lathe(x, y, base - 0.1, [(r, 0), (r * 0.9, r * 0.9), (r * 0.6, r * 1.5), (0.001, r * 1.65)], 9, PAL["stone"])
        K.tree(m, g, x, y, 0.07, "pine", seed=int(r * 100), z=base + r * 1.6)
    K.grove(m, g, 0.0, 0.0, 1.5, 60, seed=271, kinds=("pine", "broad"), s=0.08, avoid=[(-0.25, -0.2, 0.25, 0.2)])


@landmark
def guangzhou(m, g):
    """Guangzhou: a walled port on the Pearl River with the smooth white minaret of its mosque."""
    walls = rect_poly(-0.2, 0.35, 1.2, 0.9)
    K.wall(m, g, walls, h=0.055, t=0.045, color="brick_grey", tower_every=0.4)
    K.gate(m, g, -0.2, -0.1, 0.15, 0.08, 0.0)
    z = g(-0.45, 0.45)
    K.minaret(m, -0.45, 0.45, z, 0.045, 0.42, color="white", cap="stone")
    K.city_blocks(m, g, (-0.2, 0.35, 1.1, 0.8), 0.0, seed=281, lot=0.085, fill=0.78, avoid=[(-0.55, 0.35, -0.35, 0.55)])
    for i, (x, y) in enumerate(water_spots(g, (-1.5, -2.0, 1.8, -0.2), 9, seed=282, spacing=0.4)):
        K.junk(m, x, y, 0.2 * i, 0.4, masts=3 if i % 2 else 2)
    K.grove(m, g, -1.6, 0.8, 0.8, 30, seed=283, kinds=("broad", "palm"), s=0.08)


# ======================================================================================== movers (templates)
def movers(coll, mats):
    out = []
    for name, fn in (
        ("treasure", lambda m: K.treasure_ship(m, 0, 0, -pi / 2, 0.9, z=0.0)),
        ("junk", lambda m: K.junk(m, 0, 0, -pi / 2, 0.5, masts=3, z=0.0)),
        ("dhow", lambda m: K.dhow(m, 0, 0, -pi / 2, 0.35, z=0.0)),
        ("barge", lambda m: K.barge(m, 0, 0, -pi / 2, 0.3, z=0.0)),
        ("camel", lambda m: (K.camel(m, 0, 0, 0.0, -pi / 2, 0.08), K.camel(m, 0.0, 0.1, 0.0, -pi / 2, 0.07, pack="cobalt"))),
    ):
        m = Mini()
        fn(m)
        out.append(m.to_object(f"mv_{name}", coll, mats))
    return out


# ======================================================================================== build + export
def build():
    t0 = time.time()
    scn = bpy.data.scenes.get("MapLandmarks") or bpy.data.scenes.new("MapLandmarks")
    bpy.context.window.scene = scn
    coll = bpy.data.collections.get("Landmarks") or bpy.data.collections.new("Landmarks")
    if coll.name not in scn.collection.children:
        scn.collection.children.link(coll)
    mats = mini.materials()
    names = [n for n in LANDMARKS if not ONLY or n in ONLY]
    for ob in list(coll.objects):
        if not ONLY or ob.name[3:] in names or ob.name.startswith("mv_"):
            bpy.data.objects.remove(ob)
    for me in list(bpy.data.meshes):
        if me.users == 0:
            bpy.data.meshes.remove(me)
    stats = {}
    for name in names:
        m = Mini()
        LANDMARKS[name](m, ground_fn(name))
        ob = m.to_object(f"lm_{name}", coll, mats)
        stats[name] = len(ob.data.polygons)
    for ob in movers(coll, mats):
        stats[ob.name] = len(ob.data.polygons)
    # materials: glow gets a constant warm emission so glTF exports it cleanly
    glow = bpy.data.materials["mini_glow"]
    bsdf = glow.node_tree.nodes["Principled BSDF"]
    for link in list(glow.node_tree.links):
        if link.to_socket == bsdf.inputs["Emission Color"]:
            glow.node_tree.links.remove(link)
    bsdf.inputs["Emission Color"].default_value = (1.0, 0.45, 0.12, 1.0)
    bsdf.inputs["Emission Strength"].default_value = 2.0
    out = None
    if EXPORT:
        bpy.ops.object.select_all(action="DESELECT")
        for ob in coll.objects:
            ob.select_set(True)
        out = f"{ROOT}/public/models/landmarks.glb"
        with bpy.context.temp_override(scene=scn):
            bpy.ops.export_scene.gltf(
                filepath=out, export_format="GLB", use_selection=True, use_active_scene=True, export_apply=True,
                export_vertex_color="ACTIVE", export_normals=True, export_materials="EXPORT", export_cameras=False, export_lights=False,
                export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=7,
                export_draco_position_quantization=14, export_draco_color_quantization=8, export_draco_normal_quantization=8,
            )
    bad = [ob.name for ob in coll.objects if "." in ob.name]
    return {"faces": stats, "total_faces": sum(stats.values()), "seconds": round(time.time() - t0, 1), "out": out, "renamed": bad}


result = build()

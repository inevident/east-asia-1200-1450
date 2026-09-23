"""
S0 — HERO: Lin'an (Hangzhou), Southern Song capital, c. 1250.
Dawn mist over the Qiantang River: a Song-style octagonal pagoda on its hill
(after the Liuhe / Six Harmonies Pagoda, rebuilt 1165), seagoing junks,
a riverside town and layered mountains fading into mist, composed like a
Song landscape handscroll with empty misty space for the title inscription.
"""
import sys, importlib, random, math
from math import radians, sin, cos, pi
import bpy
from mathutils import Vector

LIB = "/Applications/Personal App/AP-WORLD-WEBSITE/blender/lib"
if LIB not in sys.path:
    sys.path.insert(0, LIB)
import ealib as E; importlib.reload(E)
import ea_assets as A; importlib.reload(A)

SLUG = "hero"
PREVIEW = globals().get("PREVIEW", True)
scn = E.new_scene("S0_Hero", res=(2560, 1440), samples=160, look="AgX - Medium High Contrast")
E.purge()
P = A.palette()
rnd = random.Random(7)

C_ENV = E.collection("hero_env")
C_ARCH = E.collection("hero_arch")
C_SHIPS = E.collection("hero_ships")
C_TREES = E.collection("hero_trees")
C_TPL = E.collection("hero_templates")

# ---------------------------------------------------------------- terrain
HILL_C = (118.0, 25.0)


def hill_h(x, y):
    """Pagoda hill (right) + rocky spur near the camera for a framing pine."""
    d = math.hypot((x - HILL_C[0]) / 1.0, (y - HILL_C[1]) / 0.8)
    base = 58 * math.exp(-(d / 80) ** 2.3)
    spur_d = math.hypot((x - 40) / 1.0, (y + 190) / 0.6)
    spur = 20 * math.exp(-(spur_d / 30) ** 2.0)
    body = max(base, spur)
    detail = E.fbm(x * 0.018, y * 0.018, octaves=6, seed=2.0) * 9 * min(1.0, body / 15 + 0.15)
    crags = E.ridged(x * 0.03, y * 0.03, octaves=4, seed=5.0) * 5 * min(1.0, body / 25)
    # flatten a terrace for the pagoda platform
    pd = math.hypot(x - 104, y - 18)
    h = body + detail + crags - 7
    if pd < 26:
        h = h * E.smoothstep(12, 26, pd) + 52 * (1 - E.smoothstep(12, 26, pd))
    return h


terr_mat = E.mat_terrain("hero_terrain", grass=(0.035, 0.06, 0.03), rock=(0.2, 0.17, 0.14), scale=0.06, slope_lo=0.55, slope_hi=0.8)
hill = E.heightfield("hero_hill", (300, 420), (250, 350), fn=lambda x, y: hill_h(x + 95, y - 45), loc=(95, -45, 0), coll=C_ENV, mat=terr_mat)


def shore_y(x):
    return 430 + 90 * sin(x / 260.0) + 35 * sin(x / 97.0 + 1.0)


def far_h(x, y):
    t = y - shore_y(x)
    if t < 0:
        return -6 + max(-30.0, t * 0.05)
    rise = E.smoothstep(0, 120, t)
    hills = (E.fbm(x * 0.0035, y * 0.0035, 6, seed=7.0) * 0.5 + 0.5) * 190 * E.smoothstep(160, 900, t)
    bumps = E.fbm(x * 0.02, y * 0.02, 3, seed=3.0) * 3
    return 0.8 + rise * 4 + hills + bumps * rise


far = E.heightfield("hero_farbank", (2600, 1500), (420, 240), fn=lambda x, y: far_h(x - 450, y + 900), loc=(-450, 900, 0), coll=C_ENV, mat=terr_mat)


def mountain_layer(name, yc, height, seed, width=9000, depth=1100, res=(460, 60), x0=-1200, mat=None, sharp=1.0, roundness=0.5):
    def fn(x, y):
        xx = x + x0
        warp = E.fbm(xx * 0.0004, seed, 3, seed=seed + 5) * 900
        r = E.ridged((xx + warp) * 0.0011 * sharp, seed * 1.7, octaves=5, seed=seed)
        f = E.fbm((xx + warp) * 0.0009 * sharp, seed * 0.7, 5, seed=seed + 2) * 0.5 + 0.5
        crest = height * (0.25 + 0.75 * (roundness * f + (1 - roundness) * r))
        prof = math.exp(-((y) / (depth * 0.33)) ** 2)
        det = E.fbm(xx * 0.006, y * 0.006, 5, seed=seed + 1) * height * 0.12
        return crest * prof + det * prof - 20
    ob = E.heightfield(name, (width, depth), res, fn=fn, loc=(x0, yc, 0), coll=C_ENV, mat=mat)
    return ob


mtn_mat = E.mat_terrain("hero_mtn", grass=(0.03, 0.05, 0.035), rock=(0.12, 0.12, 0.12), scale=0.02, slope_lo=0.5, slope_hi=0.75, bump=0.2)
mountain_layer("hero_mtn1", 1700, 300, 11.0, mat=mtn_mat, x0=-1500, roundness=0.8)
mountain_layer("hero_mtn2", 2900, 620, 23.0, width=12000, depth=1600, mat=mtn_mat, x0=-2500, sharp=1.3, roundness=0.45)
mountain_layer("hero_mtn3", 4700, 1050, 37.0, width=16000, depth=2200, mat=mtn_mat, x0=-3500, sharp=1.6, roundness=0.25)

water = E.heightfield("hero_water", (16000, 12000), (2, 2), loc=(0, 3000, 0), coll=C_ENV,
                      mat=E.mat_water("hero_water", color=(0.015, 0.03, 0.035), rough=0.03, wave_scale=900, bump=0.12, stretch=(1, 6, 1), patches=0.85, patch_scale=40.0))

# ---------------------------------------------------------------- pagoda + temple
pg = A.pagoda("hero_pagoda", tiers=7, base_r=7.4, tier_h=6.3, P=P, loc=(104, 18, hill_h(104, 18) - 1.5), coll=C_ARCH)
# small temple hall beside the pagoda
A.house("hero_hall", w=16, d=10, h=5, roof_h=3.6, P=P, wall="red", roof="tiles", ridge=0.55, overhang=1.8, lift=0.9,
        loc=(128, 40, hill_h(128, 40) - 0.8), rot=radians(-15))
for k, (hx, hy, rr) in enumerate([(82, 2, 20), (136, 8, -30), (96, 48, 5)]):
    A.house(f"hero_hut{k}", w=8, d=6, h=3.4, roof_h=2.2, P=P, loc=(hx, hy, hill_h(hx, hy) - 0.6), rot=radians(rr))

# ---------------------------------------------------------------- riverside town (far bank)
house_tpls = []
for k in range(6):
    c = bpy.data.collections.new(f"tpl_house{k}")
    C_TPL.children.link(c)
    w = rnd.uniform(7, 13)
    d = rnd.uniform(6, 9)
    A.house(f"tplh{k}", w=w, d=d, h=rnd.uniform(3, 4.2), roof_h=rnd.uniform(1.8, 2.8), P=P, coll=c,
            wall="plaster" if k % 3 else "plaster_ochre", ridge=rnd.uniform(0.4, 0.7), overhang=0.8, lift=0.35, lit=(k % 2 == 0))
    house_tpls.append(c)
tree_tpls = {}
for kind, n in (("pine", 3), ("leaf", 4), ("willow", 2)):
    tree_tpls[kind] = []
    for k in range(n):
        c = bpy.data.collections.new(f"tpl_{kind}{k}")
        C_TPL.children.link(c)
        if kind == "pine":
            A.pine(f"tpl_{kind}{k}", height=rnd.uniform(11, 16), seed=10 + k, P=P, coll=c, pads=11, spread=1.3)
        elif kind == "leaf":
            A.broadleaf(f"tpl_{kind}{k}", height=rnd.uniform(9, 14), seed=20 + k, P=P, coll=c, mat="leaf", blobs=10)
        else:
            A.willow(f"tpl_{kind}{k}", height=rnd.uniform(8, 10), seed=30 + k, P=P, coll=c, strands=36)
        tree_tpls[kind].append(c)

n_houses = 0
for i in range(900):
    x = rnd.uniform(-900, 180)
    sy = shore_y(x)
    y = sy + rnd.uniform(18, 230) * (rnd.random() ** 0.8)
    z = far_h(x, y)
    if z < 1.0 or z > 40:
        continue
    # keep a clear promenade strip at the waterline
    if y - sy < 16:
        continue
    ang = math.atan2(shore_y(x + 5) - shore_y(x - 5), 10) + (pi / 2 if rnd.random() < 0.15 else 0)
    E.collection_instance(rnd.choice(house_tpls), f"hh{i}", loc=(x, y, z - 0.3), rot=(0, 0, ang), scale=rnd.uniform(0.85, 1.2), coll=C_ARCH)
    n_houses += 1
    if n_houses > 420:
        break

# willows along the far shore
for i in range(140):
    x = rnd.uniform(-900, 200)
    y = shore_y(x) + rnd.uniform(4, 14)
    E.collection_instance(rnd.choice(tree_tpls["willow"]), f"wl{i}", loc=(x, y, far_h(x, y) - 0.3), rot=(0, 0, rnd.uniform(0, 6.28)), scale=rnd.uniform(0.8, 1.2), coll=C_TREES)
# broadleaf forest on far hills
for i in range(2400):
    x = rnd.uniform(-1600, 800)
    y = rnd.uniform(500, 1600)
    t = y - shore_y(x)
    if t < 200 and rnd.random() < 0.8:
        continue
    z = far_h(x, y)
    if z < 2:
        continue
    kind = "pine" if (z > 90 and rnd.random() < 0.5) else "leaf"
    E.collection_instance(rnd.choice(tree_tpls[kind]), f"ft{i}", loc=(x, y, z - 0.5), rot=(0, 0, rnd.uniform(0, 6.28)), scale=rnd.uniform(1.0, 1.8), coll=C_TREES)
# pines + broadleaf on the pagoda hill
for i in range(700):
    x = rnd.uniform(20, 240)
    y = rnd.uniform(-90, 170)
    z = hill_h(x, y)
    if z < 3:
        continue
    if math.hypot(x - 104, y - 18) < 16 or math.hypot(x - 128, y - 40) < 13:
        continue
    kind = "pine" if rnd.random() < 0.55 else "leaf"
    E.collection_instance(rnd.choice(tree_tpls[kind]), f"ht{i}", loc=(x, y, z - 0.4), rot=(0, 0, rnd.uniform(0, 6.28)), scale=rnd.uniform(0.7, 1.25), coll=C_TREES)

# the framing pine on the foreground spur (hand placed, bespoke)
for k, (px, py) in enumerate([(40, -190), (22, -176)]):
    fp = A.pine(f"hero_spurpine{k}", height=20 - 5 * k, seed=4 + k, P=P, coll=C_TREES, lean=0.6, pads=16, spread=1.7)
    fp.location = (px, py, hill_h(px, py) - 1.0)
    fp.rotation_euler.z = radians(160 + 40 * k)

# rocks on the spur and along the pagoda hill shore
rock_mat = E.mat_noisy("hero_rock", (0.16, 0.15, 0.14), (0.3, 0.28, 0.25), scale=1.5, rough=(0.75, 0.95), bump=0.4)
for i in range(70):
    x = rnd.uniform(-10, 240)
    y = rnd.uniform(-230, 150)
    z = hill_h(x, y)
    if z < -1.5 or z > 26:
        continue
    near_spur = math.hypot(x - 40, y + 190) < 50
    if not near_spur and z > 4:
        continue
    A.rock(f"hero_rock{i}", r=rnd.uniform(1.5, 5.5) if near_spur else rnd.uniform(1.5, 4), seed=i, P=P, loc=(x, y, z - 0.6), mat=rock_mat)

# ---------------------------------------------------------------- ships
ships = [
    dict(loc=(-40, 140, 0.2), rot=185, L=34, sail="sail"),
    dict(loc=(-215, 95, 0.2), rot=-12, L=30, sail="sail"),
    dict(loc=(-120, 350, 0.2), rot=170, L=26, sail="sail_light"),
    dict(loc=(-420, 330, 0.2), rot=10, L=26, sail="sail"),
    dict(loc=(20, 360, 0.2), rot=200, L=22, sail="sail_light"),
]
for k, s in enumerate(ships):
    A.junk(f"hero_junk{k}", L=s["L"], B=s["L"] * 0.27, D=s["L"] * 0.11, P=P, coll=C_SHIPS, sail_mat=s["sail"], seed=k + 3,
           loc=s["loc"], rot=radians(s["rot"]), sail_angle=rnd.uniform(4, 14))
for k in range(9):
    x = rnd.uniform(-600, 60)
    y = shore_y(x) - rnd.uniform(8, 40)
    A.sampan(f"hero_sampan{k}", L=rnd.uniform(6, 8), P=P, loc=(x, y, 0.05), rot=rnd.uniform(0, 6.28))

fisher = A.sampan("hero_fisher", L=7.5, P=P, loc=(-62, -112, 0.05), rot=radians(20), canopy=True)
A.person("hero_fisherman", color=(0.12, 0.12, 0.13), hat="cone", loc=(-64.5, -113, 0.35), rot=radians(20), scale=1.0)
pole = E._poly_curve("hero_pole", [(-66, -114, 1.5), (-71, -120, 5.5)], 0.035, C_SHIPS, P["wood_dark"])

# ---------------------------------------------------------------- atmosphere & light
SUN_AZ, SUN_EL = -62.0, 6.0
E.sky_world(scn, sun_elev=SUN_EL, sun_rot=SUN_AZ, strength=0.3, sun_disc=True, aerosol=1.6, air=1.0)
E.sun("hero_sun", elevation=SUN_EL, azimuth=SUN_AZ, strength=4.8, angle=1.0, color=(1.0, 0.6, 0.32), coll=C_ENV)
# overall aerial haze (homogeneous = cheap) + valley mist hugging the water
E.fog_volume("hero_haze", (22000, 16000, 1800), loc=(0, 5000, -20), density=0.00042, color=(0.9, 0.92, 0.96), anisotropy=0.35, falloff_height=260.0, z0=0.0, coll=C_ENV)
E.fog_volume("hero_mist", (8000, 6000, 140), loc=(-600, 2000, -10), density=0.0032, color=(0.97, 0.96, 0.95),
             falloff_height=22.0, z0=0.0, anisotropy=0.35, noise_scale=0.0015, noise_amount=0.7, coll=C_ENV)
scn.cycles.volume_step_rate = 3.0
scn.cycles.volume_max_steps = 256

cam = E.camera("hero_cam", (-60, -330, 42), (-60 + 700 * sin(radians(12.5)), -330 + 700 * cos(radians(12.5)), 42 + 700 * 0.035), lens=35, coll=C_ENV, dof=None)

E.setup_outputs(scn, SLUG, mist_start=20, mist_depth=6000)
A_TPL = C_TPL
E.hide_template(C_TPL)

if PREVIEW:
    scn.render.resolution_percentage = 35
    scn.cycles.samples = 24
result = {"houses": n_houses, "objects": len(scn.objects)}

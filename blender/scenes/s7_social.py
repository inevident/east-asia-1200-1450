"""
S7 — SOCIAL: Terraces of plenty.
Flooded rice terraces at sunset around a farming village. Fast-ripening,
drought-resistant Champa rice (introduced from Vietnam in 1012) and new terraced
fields let southern China feed a population that passed 100 million under the
Song — a society of peasant households organised around patriarchal, filial
family life, with farmers ranked second only to scholars in the Confucian order.
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

SLUG = "social"
PREVIEW = globals().get("PREVIEW", True)
scn = E.new_scene("S7_Social", res=(2560, 1440), samples=192, look="AgX - Medium High Contrast")
E.purge()
P = A.palette()
rnd = random.Random(71)
C = E.collection("soc_land")
C_VIL = E.collection("soc_village")
C_TPL = E.collection("soc_templates")

STEP = 1.25      # terrace height
RISER = 0.13     # fraction of each step used by the riser


def hill(x, y):
    """A broad rounded hill (terraced) rising behind a flat valley floor."""
    wx = x + 38 * E.fbm(x * 0.006, y * 0.006, 3, seed=21.0)
    wy = y + 38 * E.fbm(x * 0.006 + 5, y * 0.006, 3, seed=22.0)
    x, y = wx, wy
    main = 58 * math.exp(-((x - 10) / 150) ** 2 - ((y - 230) / 120) ** 2)
    side = 36 * math.exp(-((x + 170) / 90) ** 2 - ((y - 170) / 90) ** 2)
    far = 0.0
    rid = E.fbm(x * 0.006, y * 0.006, 5, seed=3.0) * 10 * E.smoothstep(0, 25, main + side)
    return max(main + side + rid, 0.0) + far + 2.0


def terraced(x, y):
    b = hill(x, y)
    s = b / STEP
    lvl = math.floor(s)
    f = s - lvl
    # flat paddy for most of the step, steep riser at the end; a small bund lip at the outer edge
    rise = E.smoothstep(1 - RISER, 1.0, f)
    bund = 0.14 * math.exp(-((f - (1 - RISER - 0.02)) / 0.02) ** 2)
    return (lvl + rise) * STEP + bund


def mat_terrace(name):
    """Water on the flat paddies (mirror), green rice/grass on risers & bunds."""
    m, nb, bsdf, out = E.new_material(name)
    tc = nb.texcoord()
    geo = nb.new("ShaderNodeNewGeometry", (-1200, 400))
    sep = nb.sepxyz(geo.outputs["Normal"], loc=(-1000, 400))
    flat = nb.maprange(sep.outputs[2], 0.975, 0.995, 0.0, 1.0, loc=(-800, 400))
    n = nb.noise(tc.outputs["Object"], scale=0.35, detail=6.0, loc=(-900, 100))
    grass = nb.ramp(n.outputs["Fac"], [(0.3, (0.05, 0.1, 0.02)), (0.7, (0.14, 0.2, 0.04))], loc=(-600, 100))
    # young rice seedlings speckled in some paddies
    n2 = nb.noise(tc.outputs["Object"], scale=2.5, detail=2.0, loc=(-900, -200))
    seedl = nb.maprange(n2.outputs["Fac"], 0.6, 0.66, 0.0, 1.0, loc=(-600, -200))
    watercol = nb.mix(nb.math("MULTIPLY", seedl, 0.5, loc=(-450, -200)), (0.01, 0.015, 0.012), (0.08, 0.14, 0.03), loc=(-350, -100))
    col = nb.mix(flat, grass.outputs[0], watercol, loc=(-200, 200))
    rough = nb.maprange(flat, 0, 1, 0.8, 0.02, loc=(-200, 0))
    rough = nb.math("ADD", rough, nb.math("MULTIPLY", seedl, 0.25, loc=(-350, -300)), loc=(-150, -100))
    E.principled(bsdf, color=col, rough=rough, ior=1.33, spec=0.6)
    wn = nb.noise(tc.outputs["Object"], scale=6.0, detail=3.0, loc=(-900, -500))
    E.principled(bsdf, normal=nb.bump(wn.outputs["Fac"], strength=0.1, distance=0.05))
    return m


terr = E.heightfield("soc_terraces", (520, 460), (900, 800), fn=lambda x, y: terraced(x, y + 220), loc=(0, 220, 0), coll=C, mat=mat_terrace("soc_terrace"), smooth=False)

# forested mid-distance ridges to fill the valley
fmat = E.mat_terrain("soc_forest", grass=(0.03, 0.06, 0.025), rock=(0.08, 0.1, 0.06), scale=0.05, slope_lo=0.3, slope_hi=0.5)
E.heightfield("soc_midhills", (2600, 700), (260, 70), fn=lambda x, y: ((E.fbm(x * 0.004, y * 0.004, 5, seed=31.0) * 0.5 + 0.5) * 120 + 20) * math.exp(-(y / 260) ** 2) - 5,
              loc=(0, 760, 0), coll=C, mat=fmat)
# far mountains
mtn = E.mat_terrain("soc_mtn", grass=(0.04, 0.07, 0.03), rock=(0.15, 0.13, 0.11), scale=0.02)
E.heightfield("soc_mtns", (4000, 1400), (300, 90), fn=lambda x, y: (E.ridged(x * 0.0018, y * 0.002, 5, seed=4.0) * 320 + E.fbm(x * 0.004, y * 0.004, 4, seed=2.0) * 60) * math.exp(-(y / 450) ** 2) - 20,
              loc=(0, 1200, 0), coll=C, mat=mtn)
E.heightfield("soc_mtns2", (6000, 1600), (300, 80), fn=lambda x, y: (E.ridged(x * 0.0012, y * 0.002, 5, seed=11.0) * 600) * math.exp(-(y / 500) ** 2) - 20,
              loc=(0, 2600, 0), coll=C, mat=mtn)

# ------------------------------------------------------------ village on a flattened knoll (foreground right)
VX, VY = -30.0, 122.0
tpls = []
for k in range(4):
    c = bpy.data.collections.new(f"tpl_farm{k}")
    C_TPL.children.link(c)
    A.house(f"tpl_farm{k}", w=rnd.uniform(8, 11), d=rnd.uniform(5.5, 7), h=3.0, roof_h=2.3, P=P, coll=c, wall="plaster" if k % 2 else "plaster_ochre",
            ridge=0.7, overhang=0.8, lift=0.3, lit=True)
    tpls.append(c)
vz = terraced(VX, VY + 150 - 150)
spots = [(0, 0, 0), (13, 5, 20), (-12, 8, -12), (5, 17, 8), (-4, -13, 3), (18, -9, 25), (-18, -6, -30)]
village_h = terraced(VX, VY) + 0.05
for k, (dx, dy, rz) in enumerate(spots):
    x, y = VX + dx, VY + dy
    E.collection_instance(tpls[k % 4], f"soc_house{k}", loc=(x, y, terraced(x, y) - 0.2), rot=(0, 0, radians(rz)), coll=C_VIL)
# the knoll itself (flat earthen platform under the houses)
knoll = E.mat_noisy("soc_knoll", (0.16, 0.12, 0.08), (0.24, 0.19, 0.13), scale=0.5, rough=(0.8, 1.0), bump=0.3)

# trees around the village
ttpl = []
for k in range(3):
    c = bpy.data.collections.new(f"tpl_soctree{k}")
    C_TPL.children.link(c)
    A.broadleaf(f"tpl_soctree{k}", height=rnd.uniform(9, 13), seed=90 + k, P=P, coll=c, mat="leaf", blobs=16, crown=0.45)
    ttpl.append(c)
for k in range(3):
    c = bpy.data.collections.new(f"tpl_socbamboo{k}")
    C_TPL.children.link(c)
    A.bamboo_clump(f"tpl_socbamboo{k}", height=9, stalks=16, seed=95 + k, P=P, coll=c)
    ttpl.append(c)
for k in range(22):
    a = rnd.uniform(0, 2 * pi)
    r = rnd.uniform(18, 30)
    tx, ty = VX + cos(a) * r, VY + sin(a) * r * 0.8
    E.collection_instance(rnd.choice(ttpl), f"soc_vtree{k}", loc=(tx, ty, terraced(tx, ty) - 0.5), rot=(0, 0, rnd.uniform(0, 6)), coll=C_VIL)
# chimney smoke (thin volumes rising & drifting)
# (chimney smoke omitted: box volumes read as pillars at this distance)

# ------------------------------------------------------------ farmers transplanting rice + a water buffalo
def buffalo(name, loc, rot):
    hide = E.mat_basic("soc_buffalo", (0.05, 0.045, 0.045), rough=0.6)
    parts = []
    body = E.sphere(name + "_body", r=1.0, coll=C_VIL, mat=hide, scale=(1.35, 0.62, 0.62))
    body.location = (0, 0, 1.25)
    head = E.sphere(name + "_head", r=0.42, coll=C_VIL, mat=hide, scale=(1.3, 0.8, 0.8))
    head.location = (1.55, 0, 1.2)
    parts += [body, head]
    for s in (-1, 1):
        horn = E.bezier_tube(name + f"_horn{s}", [(1.5, s * 0.25, 1.45, 1.0), (1.3, s * 0.75, 1.55, 0.7), (1.0, s * 0.8, 1.75, 0.3)], 0.07, C_VIL, E.mat_basic("soc_horn", (0.12, 0.1, 0.08), rough=0.4))
        parts.append(horn)
    for (lx, ly) in [(0.8, 0.35), (0.8, -0.35), (-0.8, 0.35), (-0.8, -0.35)]:
        parts.append(E.cylinder(name + f"_leg{lx}{ly}", r=0.14, h=1.0, n=8, r2=0.11, loc=(lx, ly, 0), coll=C_VIL, mat=hide))
    ob = E.join(parts, name)
    ob.location = loc
    ob.rotation_euler.z = rot
    return ob


fx, fy = -60.0, 150.0
for k in range(7):
    x = fx + rnd.uniform(-9, 9)
    y = fy + rnd.uniform(-4, 6)
    z = terraced(x, y + 150 - 150)
    p = A.person(f"soc_farmer{k}", color=rnd.choice([(0.12, 0.14, 0.2), (0.3, 0.28, 0.22), (0.08, 0.08, 0.09)]), hat="cone", loc=(x, y, z - 0.25), rot=rnd.uniform(0, 6))
    p.rotation_euler.x = radians(rnd.uniform(18, 32))  # bent over, planting
buffalo("soc_buffalo", (fx - 12, fy + 10, terraced(fx - 12, fy + 10) - 0.3), radians(35))

# ------------------------------------------------------------ light
SUN_AZ, SUN_EL = -48.0, 9.0
E.cloudy_sky_world(scn, sun_elev=SUN_EL, sun_rot=SUN_AZ, strength=0.34, cloud_scale=1.3, coverage=0.46, cloud_height=1.0,
                   warm=(1.0, 0.48, 0.22), shade=(0.3, 0.26, 0.34), sun_disc=True, aerosol=1.6, cloud_strength=1.2)
E.sun("soc_sun", elevation=SUN_EL, azimuth=SUN_AZ, strength=5.0, angle=0.8, color=(1.0, 0.6, 0.32), coll=C)
E.fog_volume("soc_haze", (8000, 8000, 700), loc=(0, 2000, -5), density=0.0003, color=(0.95, 0.9, 0.85), anisotropy=0.55, falloff_height=120.0, z0=0.0, coll=C)
E.fog_volume("soc_valleymist", (900, 700, 30), loc=(0, 200, 0), density=0.004, color=(1.0, 0.97, 0.95), anisotropy=0.5, falloff_height=6.0, z0=2.0, noise_scale=0.02, noise_amount=0.9, coll=C)
scn.cycles.volume_step_rate = 2.0

cam = E.camera("soc_cam", (-95, -70, 96), (20, 250, 44), lens=32, coll=C)
E.setup_outputs(scn, SLUG, mist_start=10, mist_depth=1800)
E.hide_template(C_TPL)
result = {"objects": len(scn.objects), "cam_z": cam.location.z}

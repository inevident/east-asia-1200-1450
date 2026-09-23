"""
S6 — ECONOMIC: Along the Canal (after Zhang Zeduan's 'Along the River During
the Qingming Festival'). A woven-timber 'rainbow bridge' (hongqiao) crowded with
vendors spans a Grand Canal branch; a grain barge lowers its mast to pass
beneath while shops — wine, tea, silk, salt, money-changing, medicine, rice,
porcelain — line both banks. Commercial revolution of the Song economy.
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

SLUG = "economic"
PREVIEW = globals().get("PREVIEW", True)
scn = E.new_scene("S6_Economic", res=(2560, 1440), samples=192, look="AgX - Medium High Contrast")
E.purge()
P = A.palette()
rnd = random.Random(61)
C = E.collection("eco_main")
C_PPL = E.collection("eco_people")
C_ENV = E.collection("eco_env")
C_TPL = E.collection("eco_templates")

# canal runs along +Y; bridge crosses it along X at y=0
CANAL_W = 26.0
water = E.heightfield("eco_water", (CANAL_W + 2, 700), (2, 2), loc=(0, 200, -1.2), coll=C_ENV,
                      mat=E.mat_water("eco_water", color=(0.02, 0.035, 0.03), rough=0.05, wave_scale=120, bump=0.1, stretch=(4, 1, 1)))
bankmat = E.mat_noisy("eco_bank", (0.18, 0.16, 0.13), (0.3, 0.27, 0.22), scale=1.0, rough=(0.8, 0.95), bump=0.3)
street = E.mat_noisy("eco_street", (0.24, 0.21, 0.16), (0.36, 0.32, 0.25), scale=0.6, rough=(0.8, 1.0), bump=0.2)
for side in (-1, 1):
    # stone embankment + street
    E.box(f"eco_emb{side}", (4, 700, 2.4), loc=(side * (CANAL_W / 2 + 2), 200, -2.2), coll=C_ENV, mat=bankmat)
    E.box(f"eco_street{side}", (60, 700, 0.3), loc=(side * (CANAL_W / 2 + 30), 200, -0.3), coll=C_ENV, mat=street)

# ------------------------------------------------------------ rainbow bridge (woven timber arch)
SPAN, RISE, BW = CANAL_W + 6, 7.2, 9.0
bw_mat = E.mat_wood("eco_bridgewood", c1=(0.16, 0.1, 0.06), c2=(0.3, 0.2, 0.12), scale=2.0, rough=0.7)
rail_mat = P["red"]


def arch_z(x):
    # circular-ish segment through (±SPAN/2, 0) with apex RISE
    R = (SPAN ** 2 / 4 + RISE ** 2) / (2 * RISE)
    return math.sqrt(max(0.0, R * R - x * x)) - (R - RISE)


# deck (curved slab)
nxs = 40
dv, df = [], []
for i in range(nxs + 1):
    x = -SPAN / 2 - 3 + (SPAN + 6) * i / nxs
    z = arch_z(max(-SPAN / 2, min(SPAN / 2, x))) + 0.6
    for yy in (-BW / 2, BW / 2):
        dv.append((x, yy, z))
for i in range(nxs):
    a = i * 2
    df.append((a, a + 2, a + 3, a + 1))
deck = E.obj_from_data("eco_deck", dv, df, C, bw_mat)
E.add_mod(deck, "SOLIDIFY", thickness=0.7)
# woven arch: two interleaved polygonal systems of straight timbers, repeated across the width
def polyline_arch(nseg, offset):
    pts = []
    for k in range(nseg + 1):
        x = -SPAN / 2 + SPAN * k / nseg
        pts.append((x, arch_z(x) - offset))
    return pts


for yi in range(11):
    y = -BW / 2 + 0.3 + (BW - 0.6) * yi / 10
    sysA = polyline_arch(4, 0.55) if yi % 2 == 0 else polyline_arch(5, 0.25)
    for (x0, z0), (x1, z1) in zip(sysA[:-1], sysA[1:]):
        E._poly_curve(f"eco_rib{yi}_{x0:.1f}", [(x0, y, z0), (x1, y, z1)], 0.24, C, bw_mat)
# transverse beams tying the systems
for k in range(9):
    x = -SPAN / 2 + SPAN * k / 8
    E.box(f"eco_tie{k}", (0.35, BW, 0.35), loc=(x, 0, arch_z(x) - 0.45), coll=C, mat=bw_mat)
# railings
for side in (-1, 1):
    pts = [(x, side * (BW / 2 - 0.1), arch_z(max(-SPAN / 2, min(SPAN / 2, x))) + 1.75) for x in [(-SPAN / 2 - 3) + (SPAN + 6) * i / 30 for i in range(31)]]
    E._poly_curve(f"eco_rail{side}", pts, 0.08, C, rail_mat)
    for i in range(0, 31, 2):
        x = -SPAN / 2 - 3 + (SPAN + 6) * i / 30
        z = arch_z(max(-SPAN / 2, min(SPAN / 2, x))) + 0.6
        E.box(f"eco_rpost{side}{i}", (0.12, 0.12, 1.2), loc=(x, side * (BW / 2 - 0.1), z), coll=C, mat=rail_mat)
# vendor stalls & parasols on the bridge
canvas = [E.mat_basic(f"eco_canvas{k}", c, rough=0.9) for k, c in enumerate([(0.75, 0.68, 0.52), (0.55, 0.12, 0.06), (0.2, 0.28, 0.4), (0.8, 0.74, 0.6)])]
for k in range(8):
    x = -SPAN / 2 + 3 + k * (SPAN - 6) / 7
    side = 1 if k % 2 else -1
    z = arch_z(x) + 0.6
    y = side * (BW / 2 - 1.1)
    E.box(f"eco_stall{k}", (1.6, 1.0, 0.9), loc=(x, y, z), coll=C, mat=P["wood_raw"])
    pole = E.cylinder(f"eco_ppole{k}", r=0.04, h=2.6, n=6, loc=(x, y, z), coll=C, mat=P["wood_dark"])
    umb = E.cylinder(f"eco_umb{k}", r=1.6, h=0.55, n=16, r2=0.05, loc=(x, y, z + 2.3), coll=C, mat=canvas[k % 4])

# ------------------------------------------------------------ shops along both banks
banner_img = bpy.data.images.load(E.TEX_DIR + "/banners.png", check_existing=True)


def banner(name, idx, loc, rot_z, h=2.6, w=0.95):
    """Hanging cloth shop sign on a pole (uses a cell of the banner atlas)."""
    m = bpy.data.materials.get(f"eco_banner{idx}")
    if m is None:
        m, nb, bsdf, out = E.new_material(f"eco_banner{idx}")
        tc = nb.texcoord()
        mp = nb.mapping(tc.outputs["UV"], scale=(1 / 8, 1, 1), offset=(idx / 8, 0, 0))
        tex = nb.new("ShaderNodeTexImage", (-600, 200))
        tex.image = banner_img
        nb.link(mp.outputs[0], tex.inputs["Vector"])
        E.principled(bsdf, color=tex.outputs["Color"], rough=0.85)
        tr = nb.new("ShaderNodeBsdfTranslucent", (0, -300))
        nb.link(tex.outputs["Color"], tr.inputs["Color"])
        mixs = nb.new("ShaderNodeMixShader", (250, 0))
        mixs.inputs[0].default_value = 0.25
        nb.link(bsdf.outputs[0], mixs.inputs[1])
        nb.link(tr.outputs[0], mixs.inputs[2])
        nb.link(mixs.outputs[0], out.inputs["Surface"])
    verts = [(-w / 2, 0, -h), (w / 2, 0, -h), (w / 2, 0, 0), (-w / 2, 0, 0)]
    ob = E.obj_from_data(name, verts, [(0, 1, 2, 3)], C, m, uvs=[(0, 0), (1, 0), (1, 1), (0, 1)])
    ob.location = loc
    ob.rotation_euler = (0, radians(rnd.uniform(-4, 4)), rot_z)
    return ob


shop_tpls = []
for k in range(6):
    c = bpy.data.collections.new(f"tpl_shop{k}")
    C_TPL.children.link(c)
    two = k % 2 == 0
    A.house(f"tpl_shop{k}", w=rnd.uniform(9, 12), d=rnd.uniform(8, 10), h=6.2 if two else 4.2, roof_h=2.4, P=P, coll=c,
            wall="plaster" if k % 3 else "plaster_ochre", ridge=0.65, overhang=1.2, lift=0.28, lit=(k % 3 == 1))
    shop_tpls.append(c)
bi = 0
for side in (-1, 1):
    y = -70.0
    while y < 420:
        w = rnd.uniform(10, 13)
        x = side * (CANAL_W / 2 + 12.5)
        rot = pi / 2 if side < 0 else -pi / 2
        E.collection_instance(rnd.choice(shop_tpls), f"eco_shop{side}_{y:.0f}", loc=(x, y, 0), rot=(0, 0, rot), coll=C)
        # awning in front of the shop
        aw = E.box(f"eco_awning{side}_{y:.0f}", (2.8, w * 0.8, 0.08), loc=(x - side * 6.5, y, 3.0), rot=(0, side * radians(14), 0), coll=C, mat=canvas[bi % 4])
        # banner on a pole
        if rnd.random() < 0.75:
            px = x - side * 8.5
            E.cylinder(f"eco_bpole{side}_{y:.0f}", r=0.06, h=5.2, n=6, loc=(px, y + w * 0.3, 0), coll=C, mat=P["wood_dark"])
            banner(f"eco_banner{side}_{y:.0f}", bi % 8, (px, y + w * 0.3 - 0.55, 5.0), rot_z=pi / 2)
            bi += 1
        y += w + rnd.uniform(0.5, 2.0)
# willows along the embankment
wtpl = []
for k in range(3):
    c = bpy.data.collections.new(f"tpl_ecowillow{k}")
    C_TPL.children.link(c)
    A.willow(f"tpl_ecowillow{k}", height=rnd.uniform(9, 12), seed=70 + k, P=P, coll=c, strands=50)
    wtpl.append(c)
ltpl = []
for k in range(3):
    c = bpy.data.collections.new(f"tpl_ecoleaf{k}")
    C_TPL.children.link(c)
    A.broadleaf(f"tpl_ecoleaf{k}", height=rnd.uniform(10, 14), seed=75 + k, P=P, coll=c, mat="leaf", blobs=18, crown=0.42)
    ltpl.append(c)
for side in (-1, 1):
    for k in range(26):
        y = -60 + k * 17 + rnd.uniform(-4, 4)
        if abs(y) < 12:
            continue
        pool = wtpl if rnd.random() < 0.45 else ltpl
        E.collection_instance(rnd.choice(pool), f"eco_tree{side}{k}", loc=(side * (CANAL_W / 2 + 3.0), y, 0), rot=(0, 0, rnd.uniform(0, 6.28)), scale=rnd.uniform(0.85, 1.15), coll=C_ENV)
# trees & roofs behind the shop rows, hills and a distant pagoda on the skyline
for i in range(500):
    side = rnd.choice((-1, 1))
    x = side * rnd.uniform(30, 160)
    y = rnd.uniform(-40, 600)
    if rnd.random() < 0.5:
        E.collection_instance(rnd.choice(ltpl), f"eco_bgt{i}", loc=(x, y, 0), rot=(0, 0, rnd.uniform(0, 6.28)), scale=rnd.uniform(0.9, 1.4), coll=C_ENV)
    else:
        E.collection_instance(rnd.choice(shop_tpls), f"eco_bgh{i}", loc=(x, y, 0), rot=(0, 0, rnd.choice((0, pi / 2, pi, -pi / 2))), coll=C_ENV)
hillmat = E.mat_terrain("eco_hills", grass=(0.05, 0.08, 0.035), rock=(0.2, 0.18, 0.15), scale=0.03)
E.heightfield("eco_hillsfar", (3000, 900), (240, 60), fn=lambda x, y: (E.fbm(x * 0.0025, y * 0.003, 5, seed=9.0) * 0.5 + 0.5) * 170 * math.exp(-(y / 320) ** 2) - 10,
              loc=(0, 1250, 0), coll=C_ENV, mat=hillmat)
A.pagoda("eco_farpagoda", tiers=9, base_r=5.5, tier_h=4.8, P=P, loc=(70, 700, 0), coll=C_ENV)

# ------------------------------------------------------------ boats: the famous barge lowering its mast + moored craft
barge_parts = []
bL, bB = 24.0, 6.0
hull = A.sampan("eco_barge_hull", L=bL, B=bB, P=P, canopy=False)
cab = E.box("eco_barge_cabin", (bL * 0.5, bB * 0.8, 1.2), loc=(-bL * 0.05, 0, 0.5), coll=C, mat=P["wood"])
cv, cf = [], []
for i in range(13):
    a = pi * i / 12
    for xx in (-bL * 0.3, bL * 0.2):
        cv.append((xx, bB * 0.45 * cos(a), 1.5 + 1.5 * sin(a)))
for i in range(12):
    a = i * 2
    cf.append((a, a + 2, a + 3, a + 1))
canopy = E.obj_from_data("eco_barge_canopy", cv, cf, C, E.mat_noisy("eco_mat_roof", (0.2, 0.14, 0.07), (0.34, 0.25, 0.13), scale=12, rough=(0.8, 1.0), bump=0.3), smooth=True)
E.add_mod(canopy, "SOLIDIFY", thickness=0.08)
cargo = [E.box(f"eco_cargo{k}", (1.2, 1.0, 0.9), loc=(bL * 0.3 + (k % 2) * 1.4, -1.0 + (k // 2) * 1.1, 0.5), coll=C, mat=P["wood_raw"]) for k in range(4)]
barge = E.join([hull, cab, canopy] + cargo, "eco_barge")
barge.location = (2.5, -40, -1.1)
barge.rotation_euler.z = radians(92)
mast = E.cylinder("eco_barge_mast", r=0.22, h=16, n=8, r2=0.12, loc=(2.5, -34, 2.0), coll=C, mat=P["wood_dark"], rot=(radians(-62), 0, 0))
for k in range(6):
    A.person(f"eco_crew{k}", color=(0.25, 0.22, 0.18), hat="cone", loc=(2.5 + rnd.uniform(-1.8, 1.8), -40 + (rnd.choice((-1, 1)) * rnd.uniform(8.5, 10.5)), -0.5), rot=rnd.uniform(0, 6), coll=C_PPL)
for k in range(10):
    side = 1 if k % 2 else -1
    A.sampan(f"eco_moored{k}", L=rnd.uniform(9, 13), B=2.6, P=P, loc=(side * (CANAL_W / 2 - 2.2), 25 + k * 13 + rnd.uniform(-3, 3), -1.1), rot=radians(90 + rnd.uniform(-4, 4)))

# ------------------------------------------------------------ crowds
robe_cols = [(0.08, 0.12, 0.25), (0.55, 0.45, 0.3), (0.45, 0.08, 0.05), (0.12, 0.25, 0.14), (0.7, 0.62, 0.48), (0.06, 0.06, 0.07), (0.4, 0.28, 0.12), (0.25, 0.15, 0.3)]
ppl_tpls = []
for k, col in enumerate(robe_cols):
    for hat in ("cap", "cone", "scholar"):
        c = bpy.data.collections.new(f"tpl_p{k}{hat}")
        C_TPL.children.link(c)
        A.person(f"tpl_p{k}{hat}", color=col, hat=hat, coll=c)
        ppl_tpls.append(c)
# on the bridge
for i in range(90):
    x = rnd.uniform(-SPAN / 2 - 2, SPAN / 2 + 2)
    y = rnd.uniform(-BW / 2 + 0.6, BW / 2 - 0.6)
    z = arch_z(max(-SPAN / 2, min(SPAN / 2, x))) + 0.6
    E.collection_instance(rnd.choice(ppl_tpls), f"eco_bp{i}", loc=(x, y, z), rot=(0, 0, rnd.uniform(0, 6.28)), coll=C_PPL)
# along the streets
for i in range(260):
    side = rnd.choice((-1, 1))
    x = side * rnd.uniform(CANAL_W / 2 + 1.2, CANAL_W / 2 + 6.5)
    y = rnd.uniform(-60, 120)
    E.collection_instance(rnd.choice(ppl_tpls), f"eco_sp{i}", loc=(x, y, 0), rot=(0, 0, rnd.uniform(0, 6.28)), coll=C_PPL)

# ------------------------------------------------------------ light & camera
E.cloudy_sky_world(scn, sun_elev=13, sun_rot=64, strength=0.32, cloud_scale=1.4, coverage=0.4, warm=(1.0, 0.62, 0.36), shade=(0.45, 0.45, 0.52), sun_disc=False, cloud_strength=1.0)
E.sun("eco_sun", elevation=13, azimuth=64, strength=5.2, angle=1.0, color=(1.0, 0.68, 0.42), coll=C_ENV)
E.fog_volume("eco_haze", (1400, 1400, 160), loc=(0, 300, -2), density=0.0014, color=(0.95, 0.92, 0.88), anisotropy=0.35, falloff_height=45.0, z0=0.0, coll=C_ENV)
cam = E.camera("eco_cam", (-3.0, -78, 11.5), (0.5, 0.0, 4.5), lens=32, coll=C_ENV)
E.setup_outputs(scn, SLUG, mist_start=10, mist_depth=320)
E.hide_template(C_TPL)
result = {"objects": len(scn.objects)}

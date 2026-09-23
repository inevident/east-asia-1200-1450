"""
S3 — RELIGIOUS: The Tripitaka Koreana depository (after Haeinsa's Janggyeong
Panjeon). Goryeo Korea carved the entire Buddhist canon onto 81,000+ woodblocks
(1237–1251) as an act of devotion to win the Buddha's protection against the
Mongol invasions. Shafts of morning light cross racks of lacquered blocks
through the hall's slatted ventilation windows; a monk walks the aisle.
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

SLUG = "religious"
PREVIEW = globals().get("PREVIEW", True)
scn = E.new_scene("S3_Religious", res=(2560, 1440), samples=256, look="AgX - Medium High Contrast")
E.purge()
P = A.palette()
rnd = random.Random(31)
C = E.collection("rel_hall")
C_RACK = E.collection("rel_racks")
C_TPL = E.collection("rel_templates")

HALL_L, HALL_W, WALL_H = 52.0, 9.0, 4.4

# ------------------------------------------------------------ materials
oldwood = E.mat_wood("rel_oldwood", c1=(0.09, 0.07, 0.05), c2=(0.2, 0.16, 0.11), scale=2.5, rough=0.8, bump=0.3)
rackwood = E.mat_wood("rel_rackwood", c1=(0.11, 0.08, 0.05), c2=(0.22, 0.16, 0.1), scale=4.0, rough=0.75, bump=0.2)


def mat_blocks(name):
    """Lacquered woodblock ends with per-block tone variation (object-space stripes)."""
    m, nb, bsdf, out = E.new_material(name)
    tc = nb.texcoord()
    sep = nb.sepxyz(tc.outputs["Object"])
    idx = nb.math("FLOOR", nb.math("DIVIDE", sep.outputs[0], 0.036, loc=(-900, 200)), loc=(-800, 200))
    comb = nb.new("ShaderNodeCombineXYZ", (-700, 200))
    nb.link(idx, comb.inputs[0])
    oi = nb.new("ShaderNodeObjectInfo", (-900, -100))
    nb.link(oi.outputs["Random"], comb.inputs[1])
    wn = nb.new("ShaderNodeTexWhiteNoise", (-550, 200))
    wn.noise_dimensions = "3D"
    nb.link(comb.outputs[0], wn.inputs["Vector"])
    col = nb.ramp(wn.outputs["Value"], [(0.0, (0.03, 0.022, 0.016)), (0.6, (0.07, 0.05, 0.035)), (1.0, (0.16, 0.11, 0.07))], loc=(-350, 200))
    grain = nb.noise(tc.outputs["Object"], scale=120.0, detail=3.0, loc=(-600, -250))
    E.principled(bsdf, color=col.outputs[0], rough=nb.maprange(grain.outputs["Fac"], 0.3, 0.7, 0.35, 0.6), coat=0.25, coat_rough=0.3,
                 normal=nb.bump(grain.outputs["Fac"], strength=0.2, distance=0.01))
    return m


blockmat = mat_blocks("rel_blocks")
labelmat = E.mat_basic("rel_label", (0.2, 0.16, 0.11), rough=0.85)
plaster = E.mat_noisy("rel_plaster", (0.55, 0.5, 0.42), (0.68, 0.63, 0.54), scale=1.5, rough=(0.85, 1.0), bump=0.12)
earth = E.mat_noisy("rel_floor", (0.12, 0.1, 0.08), (0.22, 0.19, 0.15), scale=0.8, rough=(0.8, 1.0), bump=0.35)

# ------------------------------------------------------------ shelf segment template (2 m, one tier, two rows of blocks)
SEG = 2.0
BLK_W, BLK_H, BLK_D = 0.034, 0.27, 0.42


def build_segment(coll):
    parts = []
    parts.append(E.box("seg_plank", (SEG, 0.95, 0.045), loc=(0, 0, -0.045), coll=coll, mat=rackwood))
    n = int(SEG / (BLK_W + 0.002))
    for row, yoff in enumerate((-0.23, 0.23)):
        for i in range(n):
            if rnd.random() < 0.03:
                continue
            x = -SEG / 2 + (i + 0.5) * (BLK_W + 0.002)
            h = BLK_H + rnd.uniform(-0.004, 0.004)
            b = E.box(f"seg_b{row}_{i}", (BLK_W, BLK_D, h), loc=(x, yoff, 0), coll=coll, mat=blockmat)
            b.rotation_euler.z = rnd.uniform(-0.02, 0.02)
            parts.append(b)
            # small paper title label on the aisle-facing end pieces
            if row == 0 and rnd.random() < 0.6:
                parts.append(E.box(f"seg_l{i}", (BLK_W * 0.7, 0.004, 0.05), loc=(x, yoff - BLK_D / 2 - 0.002, h * 0.62), coll=coll, mat=labelmat))
    return E.join(parts, "rel_segment")


seg_coll = bpy.data.collections.new("tpl_rel_segment")
C_TPL.children.link(seg_coll)
build_segment(seg_coll)

TIERS = [0.35, 0.83, 1.31, 1.79, 2.27]


def rack(name, x, y0, y1, facing):
    """Long rack along Y at x; `facing` = +1 if the aisle is at +x."""
    n = int((y1 - y0) / SEG)
    for k in range(n):
        yc = y0 + (k + 0.5) * SEG
        for tz in TIERS:
            E.collection_instance(seg_coll, f"{name}_{k}_{tz}", loc=(x, yc, tz), rot=(0, 0, pi / 2 if facing > 0 else -pi / 2), coll=C_RACK)
    # posts & top rail
    for k in range(n + 1):
        yy = y0 + k * SEG
        for dx in (-0.47, 0.47):
            E.box(f"{name}_post{k}{dx}", (0.09, 0.09, 2.75), loc=(x + dx, yy, 0), coll=C_RACK, mat=rackwood)
    for dx in (-0.47, 0.47):
        E.box(f"{name}_rail{dx}", (0.08, y1 - y0, 0.1), loc=(x + dx, (y0 + y1) / 2, 2.72), coll=C_RACK, mat=rackwood)


rack("rackL", -1.55, 0.0, 50.0, +1)
rack("rackR", 1.55, 0.0, 50.0, +1)
rack("rackLL", -3.55, 0.0, 50.0, -1)

# ------------------------------------------------------------ hall shell
E.box("rel_floor", (HALL_W + 2, HALL_L + 8, 0.2), loc=(0, HALL_L / 2 - 2, -0.2), coll=C, mat=earth)
E.box("rel_wallL", (0.3, HALL_L + 8, WALL_H), loc=(-HALL_W / 2 - 0.15, HALL_L / 2 - 2, 0), coll=C, mat=plaster)
E.box("rel_ceiling", (HALL_W + 1, HALL_L + 8, 0.25), loc=(0, HALL_L / 2 - 2, WALL_H + 0.3), coll=C, mat=oldwood)
E.box("rel_backwall", (HALL_W + 1, 0.3, WALL_H + 0.5), loc=(0, HALL_L + 1.8, 0), coll=C, mat=plaster)
E.box("rel_frontwall", (HALL_W + 1, 0.3, WALL_H + 0.5), loc=(0, -4.5, 0), coll=C, mat=plaster)
# ceiling beams + columns
for k in range(-1, 14):
    y = k * 4.0
    E.box(f"rel_beam{k}", (HALL_W + 0.5, 0.3, 0.35), loc=(0, y, WALL_H - 0.1), coll=C, mat=oldwood)
    for x in (-HALL_W / 2 + 0.2, -2.55, 2.55, HALL_W / 2 - 0.2):
        E.cylinder(f"rel_col{k}{x}", r=0.16, h=WALL_H, n=12, loc=(x, y, 0), coll=C, mat=oldwood)
E.box("rel_purlin", (0.3, HALL_L + 8, 0.3), loc=(0, HALL_L / 2 - 2, WALL_H + 0.05), coll=C, mat=oldwood)

# right wall with slatted windows (upper + lower openings every bay), built from pieces
RW = HALL_W / 2 + 0.15
bay = 4.0
low = (0.45, 1.75)
high = (2.85, 3.75)
for k in range(-1, 14):
    y0 = k * bay
    y1 = y0 + bay
    wy0, wy1 = y0 + 0.9, y1 - 0.9
    # wall pieces around the two window openings
    E.box(f"rel_rw_a{k}", (0.3, wy0 - y0, WALL_H), loc=(RW, (y0 + wy0) / 2, 0), coll=C, mat=plaster)
    E.box(f"rel_rw_b{k}", (0.3, y1 - wy1, WALL_H), loc=(RW, (wy1 + y1) / 2, 0), coll=C, mat=plaster)
    E.box(f"rel_rw_c{k}", (0.3, wy1 - wy0, low[0]), loc=(RW, (wy0 + wy1) / 2, 0), coll=C, mat=plaster)
    E.box(f"rel_rw_d{k}", (0.3, wy1 - wy0, high[0] - low[1]), loc=(RW, (wy0 + wy1) / 2, low[1]), coll=C, mat=plaster)
    E.box(f"rel_rw_e{k}", (0.3, wy1 - wy0, WALL_H - high[1]), loc=(RW, (wy0 + wy1) / 2, high[1]), coll=C, mat=plaster)
    # vertical wooden bars (salchang)
    nb_ = int((wy1 - wy0) / 0.13)
    for i in range(nb_ + 1):
        yy = wy0 + i * (wy1 - wy0) / nb_
        for (z0, z1) in (low, high):
            E.box(f"rel_bar{k}_{i}_{z0}", (0.055, 0.04, z1 - z0), loc=(RW, yy, z0), coll=C, mat=oldwood)

# ------------------------------------------------------------ monk
monk_robe = E.mat_basic("rel_monkrobe", (0.32, 0.31, 0.29), rough=0.9)
monk_sash = E.mat_basic("rel_kasaya", (0.35, 0.16, 0.06), rough=0.85)
mparts = []
body = E.lathe("rel_monk_body", [(0.0, 0.0), (0.3, 0.0), (0.28, 0.4), (0.24, 0.9), (0.22, 1.25), (0.19, 1.38), (0.08, 1.46), (0.0, 1.47)], n=24, coll=C, mat=monk_robe)
body.scale = (1.0, 0.72, 1.0)
head = E.sphere("rel_monk_head", r=0.105, coll=C, mat=bpy.data.materials.get("P_skin") or E.mat_basic("P_skin", (0.55, 0.36, 0.25), rough=0.6))
head.location = (0, 0.02, 1.58)
sash = E.box("rel_monk_sash", (0.5, 0.05, 0.12), loc=(0, -0.2, 1.1), rot=(0, radians(35), 0), coll=C, mat=monk_sash)
monk = E.join([body, head, sash], "rel_monk")
monk.location = (3.0, 10.4, 0.0)
monk.rotation_euler.z = radians(180)

# ------------------------------------------------------------ light & air
E.gradient_world(scn, top=(0.25, 0.35, 0.55), horizon=(0.6, 0.58, 0.5), strength=1.2)
E.sun("rel_sun", elevation=24.0, azimuth=72, strength=16.0, angle=0.4, color=(1.0, 0.78, 0.52), coll=C)
E.fog_volume("rel_dust", (HALL_W, HALL_L + 6, WALL_H + 0.3), loc=(0, HALL_L / 2 - 1.5, 0), density=0.055, color=(1.0, 0.95, 0.88), anisotropy=0.66,
             noise_scale=0.25, noise_amount=0.5, coll=C)
scn.cycles.volume_step_rate = 1.0
scn.cycles.volume_bounces = 1
# faint bounce fill so the shadows aren't black
E.area_light("rel_fill", (3.0, -2.0, 2.6), (2.5, 20, 1.2), size=3.0, energy=40, color=(0.9, 0.85, 0.75), coll=C)

cam = E.camera("rel_cam", (3.25, 0.2, 1.5), (1.75, 30.0, 1.95), lens=22, coll=C)
E.setup_outputs(scn, SLUG, mist_start=0.5, mist_depth=55)
scn.view_settings.exposure = 0.8
E.hide_template(C_TPL)
result = {"objects": len(scn.objects)}

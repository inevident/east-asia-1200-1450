"""
S1 — POLITICAL: The examination compound (gongyuan) at night.
Thousands of candidates, each sealed in a tiny cell with a candle, write
essays on the Confucian classics; a watchtower (after Nanjing's Mingyuan Lou)
lets proctors watch every row. Artist's reconstruction of an imperial
examination compound — the meritocratic heart of the Song bureaucracy.
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

SLUG = "political"
PREVIEW = globals().get("PREVIEW", True)
scn = E.new_scene("S1_Political", res=(2560, 1440), samples=200, look="AgX - Medium High Contrast")
E.purge()
P = A.palette()
rnd = random.Random(11)

C_ENV = E.collection("pol_env")
C_ROWS = E.collection("pol_rows")
C_ARCH = E.collection("pol_arch")
C_TPL = E.collection("pol_templates")

# ------------------------------------------------------------ materials
brick = E.mat_noisy("pol_brick", (0.16, 0.15, 0.14), (0.27, 0.25, 0.23), scale=6, rough=(0.8, 0.95), bump=0.25)
paving = E.mat_noisy("pol_paving", (0.12, 0.11, 0.1), (0.2, 0.19, 0.17), scale=1.2, rough=(0.6, 0.9), bump=0.3)
earth = E.mat_noisy("pol_earth", (0.07, 0.06, 0.05), (0.12, 0.1, 0.08), scale=0.4, rough=(0.8, 1.0), bump=0.2)
flame = E.mat_emit("pol_flame", (1.0, 0.5, 0.15), 260.0)


def mat_cellglow(name):
    """Warm light spilling on the cell's back wall; per-cell random brightness."""
    m, nb, bsdf, out = E.new_material(name)
    tc = nb.texcoord()
    geo = nb.new("ShaderNodeNewGeometry", (-1200, 300))
    sep = nb.sepxyz(tc.outputs["Object"], loc=(-1000, 200))
    cell = nb.math("FLOOR", nb.math("DIVIDE", sep.outputs[0], 1.2, loc=(-900, 200)), loc=(-800, 200))
    oi = nb.new("ShaderNodeObjectInfo", (-1000, -100))
    comb = nb.new("ShaderNodeCombineXYZ", (-650, 100))
    nb.link(cell, comb.inputs[0])
    nb.link(oi.outputs["Random"], comb.inputs[1])
    wn = nb.new("ShaderNodeTexWhiteNoise", (-500, 100))
    wn.noise_dimensions = "3D"
    nb.link(comb.outputs[0], wn.inputs["Vector"])
    # a few cells are dark (candidate asleep / cell empty)
    lit = nb.math("GREATER_THAN", wn.outputs["Value"], 0.06, loc=(-300, 100))
    bright = nb.maprange(wn.outputs["Value"], 0.0, 1.0, 0.8, 2.6, loc=(-300, -50))
    # vertical falloff: brighter near the candle (low), darker toward the roof
    vz = nb.maprange(sep.outputs[2], 0.2, 2.0, 1.0, 0.25, loc=(-300, -200))
    s = nb.math("MULTIPLY", nb.math("MULTIPLY", lit, bright, loc=(-150, 50)), vz, loc=(0, 0))
    em = nb.new("ShaderNodeEmission", (150, -150))
    em.inputs["Color"].default_value = (1.0, 0.5, 0.2, 1)
    nb.link(s, em.inputs["Strength"])
    E.principled(bsdf, color=(0.35, 0.3, 0.25), rough=0.9)
    add = nb.new("ShaderNodeAddShader", (300, 0))
    nb.link(bsdf.outputs[0], add.inputs[0])
    nb.link(em.outputs[0], add.inputs[1])
    nb.link(add.outputs[0], out.inputs["Surface"])
    return m


cellglow = mat_cellglow("pol_cellglow")
robes = [E.mat_basic(f"pol_robe{k}", c, rough=0.85) for k, c in enumerate([(0.12, 0.16, 0.24), (0.3, 0.26, 0.2), (0.14, 0.2, 0.17), (0.36, 0.32, 0.26), (0.24, 0.1, 0.08)])]
skin = E.mat_basic("pol_skin", (0.4, 0.26, 0.18), rough=0.6)
paper = E.mat_basic("pol_paper", (0.8, 0.74, 0.6), rough=0.9)

# ------------------------------------------------------------ one row of cells (template)
N_CELLS, CW, DEPTH, H = 44, 1.2, 1.75, 2.15
ROW_L = N_CELLS * CW


def build_row(coll):
    parts = []
    parts.append(E.box("row_floor", (ROW_L + 0.4, DEPTH + 0.5, 0.25), loc=(0, 0, -0.25), coll=coll, mat=paving))
    parts.append(E.box("row_back", (ROW_L + 0.3, 0.28, H + 0.15), loc=(0, DEPTH / 2, 0), coll=coll, mat=brick))
    parts.append(E.box("row_glow", (ROW_L, 0.02, H * 0.95), loc=(0, DEPTH / 2 - 0.15, 0.02), coll=coll, mat=cellglow))
    for i in range(N_CELLS + 1):
        x = -ROW_L / 2 + i * CW
        parts.append(E.box(f"row_part{i}", (0.14, DEPTH, H), loc=(x, 0, 0), coll=coll, mat=brick))
    # lintel beam across the open front
    parts.append(E.box("row_lintel", (ROW_L + 0.3, 0.22, 0.3), loc=(0, -DEPTH / 2 + 0.05, H - 0.3), coll=coll, mat=P["wood_dark"]))
    for i in range(N_CELLS):
        x = -ROW_L / 2 + (i + 0.5) * CW
        # two boards: the upper one is the desk, the lower one the seat (as in the real haoshe)
        parts.append(E.box(f"row_desk{i}", (CW - 0.16, 0.34, 0.05), loc=(x, -DEPTH / 2 + 0.2, 0.78), coll=coll, mat=P["wood_raw"]))
        parts.append(E.box(f"row_seat{i}", (CW - 0.16, 0.3, 0.05), loc=(x, -0.2, 0.42), coll=coll, mat=P["wood_raw"]))
        parts.append(E.box(f"row_sheet{i}", (0.36, 0.26, 0.004), loc=(x + rnd.uniform(-0.15, 0.15), -DEPTH / 2 + 0.2, 0.832), coll=coll, mat=paper))
        # candle + flame
        cx = x + (0.38 if i % 2 else -0.38)
        parts.append(E.cylinder(f"row_candle{i}", r=0.025, h=0.1, n=6, loc=(cx, -DEPTH / 2 + 0.22, 0.83), coll=coll, mat=paper))
        fl = E.sphere(f"row_flame{i}", r=0.024, seg=6, rings=4, coll=coll, mat=flame, scale=(1, 1, 2.2))
        fl.location = (cx, -DEPTH / 2 + 0.22, 0.96)
        parts.append(fl)
        # candidate (a few cells empty)
        if rnd.random() < 0.9 or i >= N_CELLS - 4:
            rm = rnd.choice(robes)
            body = E.cylinder(f"row_body{i}", r=0.24, h=0.62, n=8, r2=0.15, loc=(x, -0.22, 0.45), coll=coll, mat=rm, rot=(radians(-22), 0, 0))
            head = E.sphere(f"row_head{i}", r=0.1, seg=8, rings=6, coll=coll, mat=skin)
            head.location = (x, -0.47, 1.08)
            cap = E.box(f"row_cap{i}", (0.17, 0.17, 0.12), loc=(x, -0.45, 1.13), coll=coll, mat=P["dark"])
            parts += [body, head, cap]
    ob = E.join(parts, "exam_row_body")
    rf = E.roof_hip("exam_row_roof", ROW_L + 0.3, DEPTH + 0.3, 0.75, overhang=0.55, lift=0.25, ridge_ratio=0.985, coll=coll, mat=P["tiles"], underside_mat=P["wood_dark"], thickness=0.1, res=16)
    rf.location = (0, 0.05, H + 0.02)
    for b in E.ridge_beams("exam_row_rb", ROW_L + 0.3, DEPTH + 0.3, 0.75, 0.55, 0.25, ridge_ratio=0.985, coll=coll, mat=P["tiles"], r=0.07):
        b.location = (0, 0.05, H + 0.02)
    return ob


row_tpl = bpy.data.collections.new("tpl_exam_row")
C_TPL.children.link(row_tpl)
build_row(row_tpl)

# ------------------------------------------------------------ compound layout
AVE = 14.0          # central avenue width (x)
ROW_PITCH = 4.1     # row + alley
N_ROWS = 34
Y0 = -60.0
for side in (-1, 1):
    for r in range(N_ROWS):
        y = Y0 + r * ROW_PITCH
        x = side * (AVE / 2 + ROW_L / 2 + 2.0)
        E.collection_instance(row_tpl, f"row_{side}_{r}", loc=(x, y, 0.25), coll=C_ROWS)
        # a second bank of rows further out for scale
        x2 = side * (AVE / 2 + ROW_L * 1.5 + 6.0)
        E.collection_instance(row_tpl, f"row2_{side}_{r}", loc=(x2, y, 0.25), coll=C_ROWS)

ground = E.heightfield("pol_ground", (900, 900), (2, 2), loc=(0, 120, 0), coll=C_ENV, mat=earth)
avenue = E.box("pol_avenue", (AVE, N_ROWS * ROW_PITCH + 90, 0.12), loc=(0, Y0 + N_ROWS * ROW_PITCH / 2 + 10, 0), coll=C_ENV, mat=paving)
for side in (-1, 1):
    for k in range(3):
        xx = side * (AVE / 2 + ROW_L * (k) + 1.0 + 4.0 * k) if k else side * (AVE / 2 + 1.0)
    # alleys between the two banks
    E.box(f"pol_lane{side}", (3.6, N_ROWS * ROW_PITCH + 10, 0.1), loc=(side * (AVE / 2 + ROW_L + 4.0), Y0 + N_ROWS * ROW_PITCH / 2 - 2, 0), coll=C_ENV, mat=paving)

# ------------------------------------------------------------ Mingyuan-style watchtower
def mat_lattice(name, strength=2.2):
    """Glowing paper window behind a wooden lattice (grid mask)."""
    m, nb, bsdf, out = E.new_material(name)
    tc = nb.texcoord()
    sep = nb.sepxyz(tc.outputs["Generated"])
    gx = nb.math("PINGPONG", nb.math("MULTIPLY", sep.outputs[0], 14, loc=(-800, 300)), 0.5, loc=(-700, 300))
    gz = nb.math("PINGPONG", nb.math("MULTIPLY", sep.outputs[2], 9, loc=(-800, 100)), 0.5, loc=(-700, 100))
    mx = nb.math("GREATER_THAN", gx, 0.07, loc=(-600, 300))
    mz = nb.math("GREATER_THAN", gz, 0.07, loc=(-600, 100))
    paperm = nb.math("MULTIPLY", mx, mz, loc=(-500, 200))
    em = nb.new("ShaderNodeEmission", (0, -200))
    em.inputs["Color"].default_value = (1.0, 0.6, 0.28, 1)
    nb.link(nb.math("MULTIPLY", paperm, strength, loc=(-300, -200)), em.inputs["Strength"])
    E.principled(bsdf, color=(0.05, 0.02, 0.01), rough=0.6)
    add = nb.new("ShaderNodeAddShader", (250, 0))
    nb.link(bsdf.outputs[0], add.inputs[0])
    nb.link(em.outputs[0], add.inputs[1])
    nb.link(add.outputs[0], out.inputs["Surface"])
    return m


LATTICE = mat_lattice("pol_lattice")
TY = Y0 + N_ROWS * ROW_PITCH * 0.55
tz = 0.0
tw = 11.0
lan_mat = P["lantern"]
E.box("tw_plinth", (tw + 4, tw + 4, 1.6), loc=(0, TY, 0), coll=C_ARCH, mat=P["stone"])
tz = 1.6
for lvl, (w, h) in enumerate([(tw, 6.0), (tw * 0.82, 5.0), (tw * 0.66, 4.4)]):
    E.box(f"tw_body{lvl}", (w, w, h), loc=(0, TY, tz), coll=C_ARCH, mat=P["red"])
    # glowing paper lattice windows on all sides
    for ang in (0, 90, 180, 270):
        win = E.box(f"tw_win{lvl}_{ang}", (w * 0.6, 0.1, h * 0.5), loc=(0, 0, 0), coll=C_ARCH, mat=LATTICE)
        a = radians(ang)
        win.location = (sin(a) * (w / 2 + 0.03), TY - cos(a) * (w / 2 + 0.03), tz + h * 0.25)
        win.rotation_euler.z = -a
    for cx in (-1, 1):
        for cy in (-1, 1):
            E.cylinder(f"tw_col{lvl}{cx}{cy}", r=0.32, h=h, n=10, loc=(cx * w / 2, TY + cy * w / 2, tz), coll=C_ARCH, mat=P["red"])
    E.box(f"tw_beam{lvl}", (w + 0.6, w + 0.6, 0.45), loc=(0, TY, tz + h), coll=C_ARCH, mat=P["wood_dark"])
    rh = w * 0.3 if lvl < 2 else w * 0.42
    rf = E.roof_hip(f"tw_roof{lvl}", w, w, rh, overhang=w * 0.2 + 0.8, lift=0.9, ridge_ratio=0.0 if lvl < 2 else 0.35, coll=C_ARCH, mat=P["tiles"], underside_mat=P["wood_dark"], thickness=0.25, res=14)
    rf.location = (0, TY, tz + h + 0.4)
    for b in E.ridge_beams(f"tw_rb{lvl}", w, w, rh, w * 0.2 + 0.8, 0.9, ridge_ratio=0.0 if lvl < 2 else 0.35, coll=C_ARCH, mat=P["tiles"], r=0.14):
        b.location = (0, TY, tz + h + 0.4)
    # lanterns at eave corners
    ov = w / 2 + w * 0.2 + 0.4
    for cx in (-1, 1):
        for cy in (-1, 1):
            A.lantern(f"tw_lan{lvl}{cx}{cy}", r=0.38, P=P, loc=(cx * ov * 0.95, TY + cy * ov * 0.95, tz + h - 0.2), energy=60, coll=C_ARCH)
    tz += h + rh * 0.55

# examiners' halls at the north end + south gate
NY = Y0 + N_ROWS * ROW_PITCH + 22
A.house("pol_hall", w=44, d=16, h=6.5, roof_h=5.0, P=P, wall="red", ridge=0.55, overhang=2.2, lift=1.2, loc=(0, NY, 0), lit=True)
A.house("pol_hall2", w=26, d=12, h=5.5, roof_h=4.0, P=P, wall="red", ridge=0.5, overhang=1.8, lift=1.0, loc=(-60, NY + 8, 0), lit=True)
A.house("pol_hall3", w=26, d=12, h=5.5, roof_h=4.0, P=P, wall="red", ridge=0.5, overhang=1.8, lift=1.0, loc=(60, NY + 8, 0), lit=True)
# perimeter wall
WX = AVE / 2 + ROW_L * 2 + 12
for (sx, sy, lx, ly) in [(0, Y0 - 16, WX * 2 + 2, 2.2), (0, NY + 22, WX * 2 + 2, 2.2), (-WX, (Y0 - 16 + NY + 22) / 2, 2.2, NY + 38 - Y0), (WX, (Y0 - 16 + NY + 22) / 2, 2.2, NY + 38 - Y0)]:
    E.box(f"pol_wall{sx}{sy}", (lx, ly, 5.5), loc=(sx, sy, 0), coll=C_ENV, mat=brick)
A.house("pol_gate", w=18, d=9, h=7.0, roof_h=4.0, P=P, wall="red", ridge=0.5, overhang=1.6, lift=1.0, loc=(0, Y0 - 16, 0))

# avenue lanterns on posts
for k in range(18):
    y = Y0 - 6 + k * 9.5
    for side in (-1, 1):
        post = E.cylinder(f"pol_post{k}{side}", r=0.1, h=3.2, n=6, loc=(side * (AVE / 2 - 0.8), y, 0), coll=C_ENV, mat=P["wood_dark"])
        A.lantern(f"pol_alan{k}{side}", r=0.3, P=P, loc=(side * (AVE / 2 - 0.8), y, 3.5), energy=25, coll=C_ENV)

# proctors walking the alleys with lanterns
for k in range(10):
    r = rnd.randrange(0, N_ROWS - 1)
    side = rnd.choice((-1, 1))
    y = Y0 + r * ROW_PITCH + ROW_PITCH / 2 + 0.2 - 1.0
    x = side * (AVE / 2 + 4 + rnd.uniform(0, ROW_L - 6))
    A.person(f"pol_proctor{k}", color=(0.35, 0.05, 0.03), hat="scholar", loc=(x, y - 1.2, 0.1), rot=radians(90 * side), scale=1.0)
    A.lantern(f"pol_plan{k}", r=0.16, P=P, loc=(x + 0.35, y - 1.0, 1.1), energy=10, coll=C_ENV)

# distant city roofs + trees outside the wall (dark silhouettes)
tpl_tree = bpy.data.collections.new("tpl_poltree")
C_TPL.children.link(tpl_tree)
A.broadleaf("pol_treetpl", height=12, seed=3, P=P, coll=tpl_tree, blobs=9)
for i in range(260):
    ang = rnd.uniform(0, 2 * pi)
    rad = rnd.uniform(WX + 15, 420)
    x, y = cos(ang) * rad, 90 + sin(ang) * rad * 0.9
    if abs(x) < WX + 8 and Y0 - 25 < y < NY + 30:
        continue
    if y < Y0 - 20 and abs(x) < 160:
        continue
    if rnd.random() < 0.5:
        E.collection_instance(tpl_tree, f"pol_tree{i}", loc=(x, y, 0), rot=(0, 0, rnd.uniform(0, 6)), scale=rnd.uniform(0.8, 1.5), coll=C_ENV)
    else:
        A.house(f"pol_city{i}", w=rnd.uniform(8, 14), d=rnd.uniform(6, 9), h=3.5, roof_h=2.4, P=P, loc=(x, y, 0), rot=rnd.uniform(0, 3.14), lit=rnd.random() < 0.4)

# distant hills
def hills(x, y):
    return (E.fbm(x * 0.002, y * 0.002, 5, seed=4.0) * 0.5 + 0.5) * 160 * E.smoothstep(0, 400, y)
E.heightfield("pol_hills", (5000, 1400), (300, 80), fn=lambda x, y: hills(x, y + 700) * 0.6 - 5, loc=(0, 1400, 0), coll=C_ENV, mat=E.mat_basic("pol_hillmat", (0.02, 0.025, 0.03), rough=0.9))

# ------------------------------------------------------------ night sky, moon, fog
def mat_moon(name):
    m, nb, bsdf, out = E.new_material(name)
    tc = nb.texcoord()
    n = nb.noise(tc.outputs["Object"], scale=0.035, detail=6.0, rough=0.6)
    maria = nb.maprange(n.outputs["Fac"], 0.42, 0.62, 0.62, 1.0)
    em = nb.new("ShaderNodeEmission", (0, -200))
    em.inputs["Color"].default_value = (1.0, 0.92, 0.78, 1)
    nb.link(nb.math("MULTIPLY", maria, 9.0, loc=(-200, -200)), em.inputs["Strength"])
    nb.link(em.outputs[0], out.inputs["Surface"])
    return m


MOONMAT = mat_moon("pol_moonmat")
# stars: tiny emissive specks on a far dome
star_mat = E.mat_emit("pol_star", (0.8, 0.85, 1.0), 25.0)
import bmesh as _bm
bm = _bm.new()
srnd = random.Random(99)
for i in range(1400):
    az = srnd.uniform(0, 2 * pi)
    el = math.asin(srnd.uniform(0.04, 1.0))
    d = 4000
    c = (d * cos(el) * cos(az), d * cos(el) * sin(az) + 200, d * sin(el))
    s = srnd.uniform(1.2, 3.8)
    _bm.ops.create_icosphere(bm, subdivisions=1, radius=s, matrix=__import__("mathutils").Matrix.Translation(c))
E.obj_from_bm(bm, "pol_stars", C_ENV, star_mat)
E.gradient_world(scn, top=(0.004, 0.008, 0.022), horizon=(0.03, 0.045, 0.08), strength=1.0, exponent=0.7)
moon = E.sphere("pol_moon", r=72, seg=48, rings=24, coll=C_ENV, mat=MOONMAT)
moon.location = (-2534, 599, 656)
E.sun("pol_moonlight", elevation=15, azimuth=-90, strength=0.22, angle=0.5, color=(0.62, 0.72, 1.0), coll=C_ENV)
E.fog_volume("pol_haze", (3000, 3000, 160), loc=(0, 600, -5), density=0.0022, color=(0.8, 0.85, 1.0), anisotropy=0.4, falloff_height=40.0, z0=0.0, coll=C_ENV)
scn.cycles.volume_step_rate = 2.0

# ------------------------------------------------------------ camera
cam = E.camera("pol_cam", (24, Y0 - 58, 30), (-4, TY + 24, 4), lens=36, coll=C_ENV)
# eye-level camera down an alley of cells with the watchtower at the far end
R_ALLEY = 19
y_alley = Y0 + R_ALLEY * ROW_PITCH - 0.875 - 1.12
cam2 = E.camera("pol_cam_alley", (121.2, y_alley - 0.8, 1.6), (0, y_alley + 8.5, 7.0), lens=24, coll=C_ENV)
# a proctor patrolling this alley with a lantern
A.person("pol_alley_proctor", color=(0.3, 0.04, 0.03), hat="scholar", loc=(92, y_alley - 0.2, 0.12), rot=radians(90), scale=1.0)
A.lantern("pol_alley_lan", r=0.17, P=P, loc=(91.6, y_alley + 0.2, 1.05), energy=18, coll=C_ENV)
A.person("pol_alley_proctor2", color=(0.3, 0.04, 0.03), hat="scholar", loc=(64, y_alley - 0.1, 0.12), rot=radians(-90), scale=1.0)
A.lantern("pol_alley_lan2", r=0.17, P=P, loc=(64.4, y_alley + 0.25, 1.05), energy=18, coll=C_ENV)
cam3 = E.camera("pol_cam_cell", (92.2 + 17.4, y_alley - 0.55, 1.45), (92.2 + 15.2, Y0 + R_ALLEY * ROW_PITCH - 0.2, 1.0), lens=26, coll=C_ENV)
scn.camera = cam2
E.setup_outputs(scn, SLUG, mist_start=10, mist_depth=900)
scn.view_settings.exposure = 0.9
E.hide_template(C_TPL)
result = {"objects": len(scn.objects)}

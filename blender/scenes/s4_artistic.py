"""
S4 — ARTISTIC: Kinkaku (the Golden Pavilion), Kyoto, 1397.
Built for the retired shogun Ashikaga Yoshimitsu, its three storeys stack three
styles — shinden (aristocratic) below, samurai-house in the middle, Chinese Chan
(Zen) hall on top — the upper two sheathed in gold leaf, crowned by a phoenix.
Autumn light across the Kyōko-chi ("Mirror Pond") with its pine islands.
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

SLUG = "artistic"
PREVIEW = globals().get("PREVIEW", True)
scn = E.new_scene("S4_Artistic", res=(2560, 1440), samples=256, look="AgX - Medium High Contrast")
E.purge()
P = A.palette()
rnd = random.Random(41)
C = E.collection("art_pavilion")
C_ENV = E.collection("art_env")
C_TREES = E.collection("art_trees")
C_TPL = E.collection("art_templates")

# ------------------------------------------------------------ materials
gold = E.mat_gold("art_goldleaf", color=(0.95, 0.52, 0.11), rough=0.34)
gold.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 0.62
natwood = E.mat_wood("art_natwood", c1=(0.2, 0.14, 0.08), c2=(0.34, 0.24, 0.14), scale=3.0, rough=0.7)
darkwood = E.mat_wood("art_darkwood", c1=(0.04, 0.03, 0.02), c2=(0.09, 0.06, 0.04), scale=3.0, rough=0.6)
whitewall = E.mat_noisy("art_white", (0.72, 0.69, 0.62), (0.82, 0.8, 0.74), scale=2, rough=(0.8, 0.95), bump=0.05)


def mat_shingle(name, color=(0.12, 0.075, 0.045)):
    """Cypress-bark / shingle roof: fine horizontal courses along the slope."""
    m, nb, bsdf, out = E.new_material(name)
    tc = nb.texcoord()
    sep = nb.sepxyz(tc.outputs["UV"])
    v = nb.math("MULTIPLY", sep.outputs[1], 70.0, loc=(-700, 100))
    course = nb.math("FRACT", v, loc=(-600, 100))
    n = nb.noise(tc.outputs["Object"], scale=6.0, detail=5.0, loc=(-800, -200))
    col = nb.ramp(n.outputs["Fac"], [(0.3, [c * 0.7 for c in color]), (0.7, [c * 1.3 for c in color])], loc=(-400, -150))
    E.principled(bsdf, color=col.outputs[0], rough=0.75, normal=nb.bump(course, strength=0.4, distance=0.03))
    return m


shingle = mat_shingle("art_shingle")
paper = E.mat_basic("art_shoji", (0.85, 0.82, 0.72), rough=0.9)


def mat_goldlattice(name):
    m, nb, bsdf, out = E.new_material(name)
    tc = nb.texcoord()
    sep = nb.sepxyz(tc.outputs["Generated"])
    gx = nb.math("PINGPONG", nb.math("MULTIPLY", sep.outputs[0], 10, loc=(-800, 300)), 0.5, loc=(-700, 300))
    gz = nb.math("PINGPONG", nb.math("MULTIPLY", sep.outputs[2], 14, loc=(-800, 100)), 0.5, loc=(-700, 100))
    bar = nb.math("MAXIMUM", nb.math("LESS_THAN", gx, 0.12, loc=(-600, 300)), nb.math("LESS_THAN", gz, 0.12, loc=(-600, 100)), loc=(-500, 200))
    col = nb.mix(bar, (0.06, 0.035, 0.015), (0.95, 0.52, 0.11), loc=(-300, 200))
    E.principled(bsdf, color=col, metal=nb.math('MULTIPLY', bar, 0.62, loc=(-300, 0)), rough=0.35)
    return m


GOLDLATTICE = mat_goldlattice("art_goldlattice")

# ------------------------------------------------------------ Kinkaku
W1, D1 = 13.0, 10.0
PX, PY = 8.0, 60.0   # pavilion location
parts = []


def at(ob, dx=0, dy=0, z=0):
    ob.location = (PX + dx, PY + dy, z)
    return ob


# stone base and first floor (shinden style: natural wood, white panels, open veranda)
at(E.box("kk_base", (W1 + 1.2, D1 + 1.2, 0.55), coll=C, mat=P["stone"]))
at(E.box("kk_floor1", (W1, D1, 0.2), coll=C, mat=natwood), z=0.55)
H1 = 3.6
at(E.box("kk_core1", (W1 - 3.0, D1 - 2.4, H1), coll=C, mat=whitewall), z=0.75)
# shutters / lattice panels on the core walls (front face)
for i in range(6):
    x = -(W1 - 3.0) / 2 + (i + 0.5) * (W1 - 3.0) / 6
    at(E.box(f"kk_shut{i}", ((W1 - 3.0) / 6 - 0.15, 0.08, H1 * 0.62), coll=C, mat=darkwood), x, -(D1 - 2.4) / 2 - 0.02, 0.9)
    at(E.box(f"kk_shutp{i}", ((W1 - 3.0) / 6 - 0.35, 0.1, H1 * 0.5), coll=C, mat=paper), x, -(D1 - 2.4) / 2 - 0.05, 0.98)
# columns around the veranda
for i in range(7):
    for j in (-1, 1):
        at(E.cylinder(f"kk_c1_{i}{j}", r=0.14, h=H1, n=10, coll=C, mat=natwood), -W1 / 2 + 0.2 + i * (W1 - 0.4) / 6, j * (D1 / 2 - 0.2), 0.75)
for j in range(1, 5):
    for i in (-1, 1):
        at(E.cylinder(f"kk_c1s_{j}{i}", r=0.14, h=H1, n=10, coll=C, mat=natwood), i * (W1 / 2 - 0.2), -D1 / 2 + 0.2 + j * (D1 - 0.4) / 5, 0.75)
# veranda railing (front)
at(E.box("kk_rail1", (W1 - 0.2, 0.08, 0.08), coll=C, mat=natwood), 0, -D1 / 2 + 0.2, 1.35)
at(E.box("kk_beam1", (W1 + 0.2, D1 + 0.2, 0.35), coll=C, mat=natwood), z=0.75 + H1)
# pent roof between floors 1 and 2 (wide, gently curved)
z = 0.75 + H1 + 0.3
r1 = E.roof_hip("kk_roof1", W1, D1, 1.4, overhang=2.0, lift=0.35, ridge_ratio=0.5, coll=C, mat=shingle, underside_mat=darkwood, thickness=0.5, res=16)
at(r1, z=z)
# second floor (buke style) — gold leaf, balcony
W2, D2, H2 = W1 - 1.6, D1 - 1.6, 3.1
z2 = z + 0.8
at(E.box("kk_floor2", (W2 + 1.6, D2 + 1.6, 0.25), coll=C, mat=gold), z=z2)
at(E.box("kk_core2", (W2, D2, H2), coll=C, mat=gold), z=z2 + 0.25)
for i in range(5):
    x = -W2 / 2 + (i + 0.5) * W2 / 5
    at(E.box(f"kk_win2_{i}", (W2 / 5 - 0.4, 0.08, H2 * 0.62), coll=C, mat=GOLDLATTICE), x, -D2 / 2 - 0.03, z2 + 0.75)
# balcony rails
for side in (-1, 1):
    at(E.box(f"kk_bal{side}", (W2 + 1.5, 0.08, 0.1), coll=C, mat=gold), 0, side * (D2 / 2 + 0.72), z2 + 0.95)
    at(E.box(f"kk_balx{side}", (0.08, D2 + 1.5, 0.1), coll=C, mat=gold), side * (W2 / 2 + 0.72), 0, z2 + 0.95)
    for i in range(14):
        at(E.box(f"kk_balp{side}{i}", (0.07, 0.07, 0.7), coll=C, mat=gold), -W2 / 2 - 0.7 + i * (W2 + 1.4) / 13, side * (D2 / 2 + 0.72), z2 + 0.25)
at(E.box("kk_beam2", (W2 + 0.3, D2 + 0.3, 0.35), coll=C, mat=gold), z=z2 + 0.25 + H2)
z3r = z2 + 0.25 + H2 + 0.3
r2 = E.roof_hip("kk_roof2", W2, D2, 1.3, overhang=1.9, lift=0.35, ridge_ratio=0.5, coll=C, mat=shingle, underside_mat=gold, thickness=0.45, res=16)
at(r2, z=z3r)
# third floor: Zen-style hall with bell-shaped (katō) windows, all gold
W3, H3 = 6.2, 2.8
z3 = z3r + 0.9
at(E.box("kk_floor3", (W3 + 1.0, W3 + 1.0, 0.22), coll=C, mat=gold), z=z3)
at(E.box("kk_core3", (W3, W3, H3), coll=C, mat=gold), z=z3 + 0.22)
kato = E.mat_basic("art_kato", (0.03, 0.02, 0.01), rough=0.6)
for i in (-1, 1):
    # bell-shaped window: lathe profile flattened into a panel
    kw = E.lathe(f"kk_kato{i}", [(0.0, 0.0), (0.55, 0.0), (0.58, 0.9), (0.45, 1.3), (0.25, 1.55), (0.0, 1.6)], n=24, coll=C, mat=kato)
    kw.scale = (1, 0.05, 1)
    at(kw, i * 1.5, -W3 / 2 - 0.02, z3 + 0.6)
at(E.box("kk_beam3", (W3 + 0.3, W3 + 0.3, 0.3), coll=C, mat=gold), z=z3 + 0.22 + H3)
ztop = z3 + 0.22 + H3 + 0.25
r3 = E.roof_hip("kk_roof3", W3, W3, 2.9, overhang=1.8, lift=0.5, ridge_ratio=0.0, coll=C, mat=shingle, underside_mat=gold, thickness=0.45, res=18)
at(r3, z=ztop)
for b in E.ridge_beams("kk_rb3", W3, W3, 2.9, 1.8, 0.5, coll=C, mat=gold, r=0.09):
    at(b, z=ztop)
# finial + phoenix
fin = E.lathe("kk_finial", [(0.0, 0), (0.35, 0), (0.35, 0.25), (0.18, 0.4), (0.22, 0.7), (0.1, 0.9), (0.0, 1.0)], n=16, coll=C, mat=gold)
at(fin, z=ztop + 2.8)
ph_parts = []
body = E.sphere("kk_ph_body", r=0.3, coll=C, mat=gold, scale=(1.4, 0.6, 0.8))
body.location = (0, 0, 0.3)
neck = E.bezier_tube("kk_ph_neck", [(0.3, 0, 0.35, 1.0), (0.55, 0, 0.7, 0.8), (0.6, 0, 0.95, 0.6)], 0.09, C, gold)
head = E.sphere("kk_ph_head", r=0.13, coll=C, mat=gold, scale=(1.3, 0.8, 0.9))
head.location = (0.66, 0, 1.0)
tail = E.bezier_tube("kk_ph_tail", [(-0.3, 0, 0.3, 1.0), (-0.8, 0, 0.55, 0.9), (-1.1, 0, 1.1, 0.5), (-0.95, 0, 1.5, 0.2)], 0.1, C, gold)
wings = []
for s in (-1, 1):
    wv = [(0.1, 0, 0.35), (-0.3, s * 0.2, 0.45), (-0.25, s * 0.85, 1.05), (0.15, s * 0.75, 0.95), (0.3, s * 0.15, 0.5)]
    wings.append(E.obj_from_data(f"kk_ph_wing{s}", wv, [(0, 1, 2, 3, 4)], C, gold))
    E.add_mod(wings[-1], "SOLIDIFY", thickness=0.04)
phoenix = E.join([body, neck, head, tail] + wings, "kk_phoenix")
at(phoenix, z=ztop + 3.75)
phoenix.rotation_euler.z = radians(-70)
# fishing pavilion (Sōsei) annex projecting toward the pond on the west side
at(E.box("kk_sosei", (3.2, 3.4, 2.6), coll=C, mat=natwood), -W1 / 2 - 1.6, -D1 / 2 + 2.2, 0.55)
rs = E.roof_hip("kk_sosei_roof", 3.2, 3.4, 1.0, overhang=0.8, lift=0.2, ridge_ratio=0.3, coll=C, mat=shingle, underside_mat=darkwood, thickness=0.18, res=10)
at(rs, -W1 / 2 - 1.6, -D1 / 2 + 2.2, 3.2)

# ------------------------------------------------------------ pond, shores, islands
water = E.heightfield("art_pond", (600, 600), (2, 2), loc=(0, 60, 0.35), coll=C_ENV,
                      mat=E.mat_water("art_water", color=(0.01, 0.02, 0.018), rough=0.015, wave_scale=200, bump=0.03, stretch=(1, 3, 1)))
bank = E.mat_terrain("art_bank", grass=(0.06, 0.09, 0.03), rock=(0.18, 0.16, 0.13), scale=0.1, slope_lo=0.7, slope_hi=0.9)
moss = E.mat_noisy("art_moss", (0.025, 0.05, 0.015), (0.07, 0.11, 0.03), scale=3, rough=(0.8, 1.0), bump=0.5)
gardenrock = E.mat_noisy("art_rock", (0.05, 0.05, 0.045), (0.14, 0.14, 0.12), scale=1.2, rough=(0.7, 0.95), bump=0.5)


def ground_h(x, y):
    # pond basin: water between y ~ -8 and ~ 54 (shore just in front of the pavilion)
    far_bank = E.smoothstep(52, 58, y) * (2.0 + 18 * E.smoothstep(70, 160, y))
    near_bank = E.smoothstep(-6, -20, y) * 3.0
    sides = E.smoothstep(70, 110, abs(x - 5)) * 6
    base = far_bank + near_bank + sides
    h = base + E.fbm(x * 0.03, y * 0.03, 4, seed=5.0) * 1.2 - 0.6
    # keep the pond basin well under the water surface
    if -4 < y < 53 and abs(x - 5) < 75:
        h = min(h, -2.5 + 2.5 * max(E.smoothstep(47, 53, y), E.smoothstep(-2, -4, y), E.smoothstep(68, 75, abs(x - 5))))
    return h


E.heightfield("art_ground", (320, 360), (240, 270), fn=lambda x, y: ground_h(x, y + 60), loc=(0, 60, 0), coll=C_ENV, mat=bank)
# islands with sculpted pines & rocks
islands = [(-27, 24, 3.2), (30, 40, 3.2), (-40, 44, 3.0), (40, 50, 2.5)]
pine_tpls = []
for k in range(4):
    c = bpy.data.collections.new(f"tpl_artpine{k}")
    C_TPL.children.link(c)
    A.pine(f"tpl_artpine{k}", height=rnd.uniform(5.5, 8.0), seed=50 + k, P=P, coll=c, lean=0.7, pads=9, spread=1.5)
    pine_tpls.append(c)
for k, (ix, iy, ir) in enumerate(islands):
    isl = A.foliage_blob(f"art_island{k}", r=ir, coll=C_ENV, mat=moss, flat=0.22, seed=k, subdiv=4, disp=0.45)
    isl.scale = (1.2, 0.9, 0.34)
    isl.location = (ix, iy, 0.15)
    # clipped azalea mounds (karikomi)
    for j in range(2):
        az = A.foliage_blob(f"art_azalea{k}_{j}", r=ir * 0.28, coll=C_ENV, mat=P["leaf"], flat=0.6, seed=k * 3 + j, subdiv=3, disp=0.2)
        az.location = (ix + rnd.uniform(-0.6, 0.6) * ir, iy + rnd.uniform(-0.3, 0.3) * ir, 0.5)
    for j in range(6 + int(ir) * 2):
        a = rnd.uniform(0, 2 * pi)
        rr = rnd.uniform(0.3, 0.95) * ir
        A.rock(f"art_rock{k}_{j}", r=rnd.uniform(0.4, 1.0), seed=k * 10 + j, P=P, loc=(ix + cos(a) * rr * 1.2, iy + sin(a) * rr, 0.25), mat=gardenrock)
    for j in range(1 + int(ir // 2)):
        E.collection_instance(rnd.choice(pine_tpls), f"art_ipine{k}_{j}", loc=(ix + rnd.uniform(-0.5, 0.5) * ir, iy + rnd.uniform(-0.4, 0.4) * ir, 0.6),
                              rot=(0, 0, rnd.uniform(0, 6.28)), scale=rnd.uniform(0.7, 1.1), coll=C_TREES)

# ------------------------------------------------------------ autumn forest
leaf_mats = ["maple", "maple_gold", "leaf", "maple", "leaf"]
tree_tpls = []
for k in range(8):
    c = bpy.data.collections.new(f"tpl_arttree{k}")
    C_TPL.children.link(c)
    A.broadleaf(f"tpl_arttree{k}", height=rnd.uniform(8, 12), seed=60 + k, P=P, coll=c, mat=leaf_mats[k % len(leaf_mats)], blobs=22, crown=0.42, flat=0.7)
    tree_tpls.append(c)
for k in range(5):
    c = bpy.data.collections.new(f"tpl_artcedar{k}")
    C_TPL.children.link(c)
    A.conifer(f"tpl_artcedar{k}", height=rnd.uniform(14, 22), seed=80 + k, P=P, coll=c, width=0.17)
    tree_tpls.append(c)
    tree_tpls.append(c)
c = bpy.data.collections.new("tpl_artbigpine")
C_TPL.children.link(c)
A.pine("tpl_artbigpine", height=15, seed=88, P=P, coll=c, lean=0.3, pads=14, spread=1.0)
tree_tpls.append(c)
n = 0
for i in range(7000):
    x = rnd.uniform(-150, 160)
    y = rnd.uniform(40, 220)
    z = ground_h(x, y)
    if z < 1.0:
        continue
    if abs(x - PX) < 14 and PY - 9 < y < PY + 10:
        continue
    E.collection_instance(rnd.choice(tree_tpls), f"art_t{i}", loc=(x, y, z - 0.3), rot=(0, 0, rnd.uniform(0, 6.28)), scale=rnd.uniform(0.6, 1.0), coll=C_TREES)
    n += 1
    if n > 2200:
        break
# near-shore framing maples (foreground, left & right)
for k, (x, y, s) in enumerate([(-44, -6, 1.3), (-52, 4, 1.2), (30, -8, 1.3)]):
    t = A.broadleaf(f"art_fgmaple{k}", height=12, seed=90 + k, P=P, coll=C_TREES, mat="maple", blobs=16, crown=0.55)
    t.location = (x, y, ground_h(x, y) - 0.3)
    t.scale = (s, s, s)

# ------------------------------------------------------------ light
E.sky_world(scn, sun_elev=14, sun_rot=-105, strength=0.3, sun_disc=False, aerosol=1.0)
E.sun("art_sun", elevation=14, azimuth=-105, strength=6.2, angle=1.0, color=(1.0, 0.7, 0.42), coll=C_ENV)
E.fog_volume("art_haze", (900, 900, 200), loc=(0, 150, -5), density=0.0022, color=(0.95, 0.93, 0.9), anisotropy=0.3, falloff_height=30.0, z0=0.0, coll=C_ENV)
cam = E.camera("art_cam", (-17, 6, 1.9), (9.5, 60, 6.6), lens=46, coll=C_ENV)
E.setup_outputs(scn, SLUG, mist_start=5, mist_depth=260)
E.hide_template(C_TPL)
result = {"trees": n, "objects": len(scn.objects)}

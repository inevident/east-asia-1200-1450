"""
S2 — INTELLECTUAL: Movable type and the Great Learning.
A compositor's forme of wooden movable type (after Wang Zhen's 1313 method,
with Wang's revolving type-case wheel behind), set mirror-reversed with the
opening of the Great Learning (大學) — one of Zhu Xi's Four Books, the core of
the examination curriculum — beside the freshly printed page.
Modeled at real-world scale (metres) so depth of field behaves like macro.
"""
import sys, importlib, random, math
from math import radians, sin, cos, pi
import bpy
from mathutils import Vector, Matrix

LIB = "/Applications/Personal App/AP-WORLD-WEBSITE/blender/lib"
if LIB not in sys.path:
    sys.path.insert(0, LIB)
import ealib as E; importlib.reload(E)
import ea_assets as A; importlib.reload(A)

SLUG = "intellectual"
PREVIEW = globals().get("PREVIEW", True)
scn = E.new_scene("S2_Intellectual", res=(2560, 1440), samples=256, look="AgX - Medium High Contrast")
E.purge()
rnd = random.Random(21)
C = E.collection("int_main")
C_BG = E.collection("int_bg")
C_TPL = E.collection("int_templates")

TEXT = "大學之道在明明德在親民在止於至善知止而後有定定而後能靜靜而後能安安而後能慮慮而後能得"
TW = 0.0125       # type body width (12.5 mm)
TH = 0.022        # type height
GAP = 0.0006

# ------------------------------------------------------------ materials
tabletop = E.mat_wood("int_table", c1=(0.05, 0.028, 0.016), c2=(0.12, 0.07, 0.04), scale=0.9, rough=0.45, bump=0.25)
typewood = E.mat_wood("int_typewood", c1=(0.16, 0.085, 0.04), c2=(0.3, 0.18, 0.09), scale=18.0, rough=0.55, bump=0.1)


def mat_ink_glossy(name):
    m, nb, bsdf, out = E.new_material(name)
    tc = nb.texcoord()
    n = nb.noise(tc.outputs["Object"], scale=900.0, detail=4.0)
    r = nb.maprange(n.outputs["Fac"], 0.35, 0.65, 0.12, 0.35)
    E.principled(bsdf, color=(0.012, 0.011, 0.01), rough=r, coat=0.6, coat_rough=0.12)
    return m


ink = mat_ink_glossy("int_ink")


def mat_inked_wood(name):
    """Type-face wood stained with ink around the relief."""
    m, nb, bsdf, out = E.new_material(name)
    tc = nb.texcoord()
    n = nb.noise(tc.outputs["Object"], scale=300.0, detail=5.0, rough=0.6)
    stain = nb.ramp(n.outputs["Fac"], [(0.35, (0.02, 0.018, 0.016)), (0.65, (0.16, 0.1, 0.06))])
    E.principled(bsdf, color=stain.outputs[0], rough=0.45, coat=0.3, coat_rough=0.2)
    return m


inked_wood = mat_inked_wood("int_inkedwood")
page_img = bpy.data.images.load(E.TEX_DIR + "/printed_page.png", check_existing=True)
paper = E.mat_paper("int_page", color=(0.95, 0.9, 0.78), image=page_img, rough=0.85)
iron = E.mat_noisy("int_iron", (0.03, 0.028, 0.026), (0.09, 0.08, 0.07), scale=120, rough=(0.45, 0.75), bump=0.2)
iron.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 0.8
ceramic = E.mat_basic("int_celadon", (0.32, 0.42, 0.34), rough=0.12, coat=1.0, coat_rough=0.05)
bamboo = E.mat_noisy("int_bamboo", (0.35, 0.26, 0.12), (0.52, 0.4, 0.2), scale=60, rough=(0.3, 0.5), bump=0.05)
hair = E.mat_basic("int_hair", (0.02, 0.018, 0.016), rough=0.4, sheen=0.5)
font = bpy.data.fonts.load(E.FONT_SONG, check_existing=True)


# ------------------------------------------------------------ glyph meshes
_glyph_cache = {}


def glyph_mesh(ch, size=0.0104, depth=0.0011, mirror=True):
    key = (ch, mirror)
    if key in _glyph_cache:
        return _glyph_cache[key]
    cu = bpy.data.curves.new("g_" + ch, "FONT")
    cu.body = ch
    cu.font = font
    cu.size = size
    cu.extrude = depth / 2
    cu.bevel_depth = 0.00008
    cu.bevel_resolution = 1
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    cu.resolution_u = 3
    ob = bpy.data.objects.new("g_" + ch, cu)
    C_TPL.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.curves.remove(cu)
    # glyph baseline centring: font 'CENTER' y alignment is approximate -> recentre bbox
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    zs = [v.co.z for v in me.vertices]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    m = Matrix.Translation((-cx, -cy, -min(zs)))
    if mirror:
        m = Matrix.Scale(-1, 4, (1, 0, 0)) @ m
    me.transform(m)
    if mirror:
        me.flip_normals()
    me.name = f"glyph_{ch}_{int(mirror)}"
    _glyph_cache[key] = me
    return me


def type_block(name, ch, loc, rot=(0, 0, 0), coll=None, mirror=True, inked=True):
    """One piece of movable type: wooden body + raised (mirror-reversed) glyph."""
    body = E.box(name + "_b", (TW, TW, TH - 0.0011), coll=coll, mat=typewood)
    # slightly inked top rim
    top = E.box(name + "_t", (TW * 0.985, TW * 0.985, 0.0004), loc=(0, 0, TH - 0.0011), coll=coll, mat=inked_wood if inked else typewood)
    g = bpy.data.objects.new(name + "_g", glyph_mesh(ch, mirror=mirror))
    E.link(g, coll)
    g.location = (0, 0, TH - 0.0011)
    g.data.materials.clear()
    g.data.materials.append(ink if inked else typewood)
    ob = E.join([body, top, g], name)
    ob.location = loc
    ob.rotation_euler = rot
    return ob


# ------------------------------------------------------------ table
E.box("int_tabletop", (1.6, 0.9, 0.05), loc=(0, 0.1, -0.05), coll=C, mat=tabletop, bevel=0.004)

# ------------------------------------------------------------ the forme (iron chase + wooden type)
COLS, ROWS = 6, 7
inner_w = COLS * (TW + GAP)
inner_h = ROWS * (TW + GAP)
FX, FY = 0.055, 0.035
frame_t = 0.009
for (sx, sy, lx, ly) in [(0, inner_h / 2 + frame_t / 2, inner_w + 2 * frame_t, frame_t), (0, -inner_h / 2 - frame_t / 2, inner_w + 2 * frame_t, frame_t),
                         (inner_w / 2 + frame_t / 2, 0, frame_t, inner_h), (-inner_w / 2 - frame_t / 2, 0, frame_t, inner_h)]:
    E.box(f"int_chase{sx:.3f}{sy:.3f}", (lx, ly, TH * 0.82), loc=(FX + sx, FY + sy, 0), coll=C, mat=iron, bevel=0.0008)
E.box("int_chase_base", (inner_w + 2 * frame_t + 0.01, inner_h + 2 * frame_t + 0.01, 0.004), loc=(FX, FY, -0.004), coll=C, mat=iron, bevel=0.001)
k = 0
for c in range(COLS):
    # mirror of the page: first column of text sits at the LEFT of the forme
    x = FX - inner_w / 2 + (c + 0.5) * (TW + GAP)
    for r in range(ROWS):
        y = FY + inner_h / 2 - (r + 0.5) * (TW + GAP)
        ch = TEXT[k]
        k += 1
        # one gap in the forme: a block lifted out & lying beside it
        if (c, r) == (4, 2):
            continue
        jitter = (rnd.uniform(-0.00015, 0.00015), rnd.uniform(-0.00015, 0.00015), rnd.uniform(-0.0002, 0.0001))
        type_block(f"int_t{c}_{r}", ch, (x + jitter[0], y + jitter[1], jitter[2]), rot=(0, 0, rnd.uniform(-0.01, 0.01)), coll=C)

# loose type: lifted piece + scattered spares (some un-inked, some lying on their sides)
loose = [("靜", (FX + inner_w / 2 + 0.028, FY - 0.012, 0), (0, 0, radians(18)), True),
         ("能", (FX + inner_w / 2 + 0.05, FY + 0.03, TW / 2), (radians(90), 0, radians(-35)), False),
         ("安", (FX - inner_w / 2 - 0.035, FY - 0.045, 0), (0, 0, radians(-12)), False),
         ("德", (FX - inner_w / 2 - 0.02, FY - 0.07, TW / 2), (radians(90), 0, radians(60)), False),
         ("道", (FX + 0.02, FY - inner_h / 2 - 0.04, 0), (0, 0, radians(33)), False),
         ("明", (FX + 0.045, FY - inner_h / 2 - 0.055, TW / 2), (radians(-90), 0, radians(-20)), False),
         ("字", (FX - 0.04, FY - inner_h / 2 - 0.03, 0), (0, 0, radians(5)), False)]
for i, (ch, loc, rot, inked) in enumerate(loose):
    type_block(f"int_loose{i}", ch, loc, rot=rot, coll=C, inked=inked)

# ------------------------------------------------------------ printed page (gently curled)
PW, PH = 0.2, 0.2734
nu, nv = 40, 50
verts, faces, uvs = [], [], []
for j in range(nv + 1):
    v = j / nv
    for i in range(nu + 1):
        u = i / nu
        x = (u - 0.5) * PW
        y = (v - 0.5) * PH
        # lift the right edge and top-left corner
        z = 0.012 * max(0.0, (u - 0.75) / 0.25) ** 2 + 0.006 * max(0.0, (v - 0.85) / 0.15) ** 2 * (1 - u)
        verts.append((x, y, z))
        uvs.append((u, v))
for j in range(nv):
    for i in range(nu):
        a = j * (nu + 1) + i
        faces.append((a, a + 1, a + nu + 2, a + nu + 1))
page = E.obj_from_data("int_page", verts, faces, C, paper, smooth=True, uvs=uvs)
page.location = (-0.135, -0.05, 0.0006)
page.rotation_euler.z = radians(7)
E.add_mod(page, "SOLIDIFY", thickness=0.0002)
# a second, blank sheet under it
blank = E.obj_from_data("int_blank", [(-PW / 2, -PH / 2, 0), (PW / 2, -PH / 2, 0), (PW / 2, PH / 2, 0), (-PW / 2, PH / 2, 0)], [(0, 1, 2, 3)], C, E.mat_paper("int_blankpaper", color=(0.93, 0.88, 0.76)))
blank.location = (-0.15, -0.03, 0.0002)
blank.rotation_euler.z = radians(12)

# ------------------------------------------------------------ inking brush, ink dish, rubbing pad
dish = E.lathe("int_dish", [(0.0, 0.0), (0.035, 0.0), (0.045, 0.004), (0.05, 0.014), (0.048, 0.016), (0.04, 0.008), (0.0, 0.006)], n=48, coll=C, mat=ceramic)
dish.location = (0.2, 0.2, 0)
inkpool = E.cylinder("int_inkpool", r=0.039, h=0.001, n=48, loc=(0.2, 0.2, 0.0065), coll=C, mat=ink)
# round inking brush (bristles + bamboo handle), resting across the dish
brush_parts = []
bh = E.cylinder("int_brushhandle", r=0.006, h=0.16, n=16, coll=C, mat=bamboo)
bb = E.lathe("int_bristle", [(0.0, -0.0), (0.012, 0.004), (0.014, 0.02), (0.009, 0.04), (0.0, 0.05)], n=24, coll=C, mat=hair)
bb.location = (0, 0, -0.045)
br = E.join([bh, bb], "int_brush")
br.location = (0.14, 0.17, 0.018)
br.rotation_euler = (radians(84), 0, radians(58))

# ------------------------------------------------------------ background: Wang Zhen's revolving type wheel
def type_wheel(name, R=1.05, loc=(0, 0, 0)):
    parts = []
    parts.append(E.cylinder(name + "_tray", r=R, h=0.03, n=96, coll=C_BG, mat=E.mat_wood("int_wheelwood", c1=(0.16, 0.09, 0.05), c2=(0.3, 0.18, 0.09), scale=3)))
    parts.append(E.cylinder(name + "_rim", r=R + 0.02, h=0.07, n=96, coll=C_BG, mat=bpy.data.materials["int_wheelwood"]))
    for ring in range(1, 7):
        rr = R * ring / 7
        ringo = E.cylinder(name + f"_ring{ring}", r=rr, h=0.06, n=96, coll=C_BG, mat=bpy.data.materials["int_wheelwood"])
        ringo.scale = (1, 1, 1)
        parts.append(ringo)
    for k in range(24):
        a = 2 * pi * k / 24
        d = E.box(name + f"_div{k}", (R * 0.86, 0.008, 0.06), coll=C_BG, mat=bpy.data.materials["int_wheelwood"])
        d.location = (cos(a) * R * 0.57, sin(a) * R * 0.57, 0)
        d.rotation_euler.z = a
        parts.append(d)
    ob = E.join(parts, name)
    ob.location = loc
    return ob


wheel = type_wheel("int_wheel", R=1.05, loc=(-0.35, 1.45, 0.02))
# type piled in the wheel compartments (instanced blocks)
blk = E.box("int_wblk", (TW, TW, TH), coll=C_TPL, mat=typewood)
for i in range(1500):
    a = rnd.uniform(0, 2 * pi)
    rr = rnd.uniform(0.12, 1.02)
    E.instance(blk, f"int_wt{i}", loc=(-0.35 + cos(a) * rr, 1.45 + sin(a) * rr, 0.052), rot=(0, 0, rnd.uniform(0, 3.14)))
# wheel stand

# back wall with a paper-screen window (light source) and shelves of printed books
wallm = E.mat_noisy("int_wall", (0.16, 0.13, 0.1), (0.24, 0.2, 0.15), scale=3, rough=(0.8, 1.0), bump=0.1)
E.box("int_backwall", (6, 0.1, 3), loc=(0, 2.9, -1), coll=C_BG, mat=wallm)
win = E.box("int_window", (1.3, 0.05, 1.0), loc=(-1.2, 2.84, 0.4), coll=C_BG, mat=E.mat_emit("int_winglow", (1.0, 0.86, 0.66), 4.0))
for sx in range(-4, 5):
    E.box(f"int_mullion{sx}", (0.02, 0.06, 1.0), loc=(-1.2 + sx * 0.14, 2.8, 0.4), coll=C_BG, mat=P_dark if (P_dark := bpy.data.materials.get("P_dark")) else E.mat_basic("P_dark", (0.01, 0.01, 0.01)))
for sz in range(-3, 4):
    E.box(f"int_transom{sz}", (1.3, 0.06, 0.02), loc=(-1.2, 2.8, 0.4 + 0.5 + sz * 0.14), coll=C_BG, mat=bpy.data.materials["P_dark"])
for s in range(4):
    E.box(f"int_shelf{s}", (1.2, 0.3, 0.02), loc=(1.3, 2.7, -0.2 + s * 0.35), coll=C_BG, mat=bpy.data.materials["int_wheelwood"])
    for b in range(14):
        h = rnd.uniform(0.18, 0.26)
        E.box(f"int_book{s}_{b}", (0.07, 0.22, 0.03 * rnd.randint(1, 4)), loc=(0.8 + b * 0.075, 2.7, -0.18 + s * 0.35), coll=C_BG,
              mat=E.mat_basic(f"int_bookc{s}{b}", rnd.choice([(0.5, 0.42, 0.3), (0.14, 0.18, 0.28), (0.4, 0.35, 0.25)]), rough=0.8))

# ------------------------------------------------------------ lighting
E.gradient_world(scn, top=(0.012, 0.012, 0.014), horizon=(0.02, 0.018, 0.016), strength=1.0)
E.area_light("int_key", (-0.9, 0.9, 0.75), (0.0, 0.0, 0.0), size=0.9, energy=90, color=(1.0, 0.82, 0.6), coll=C)
E.area_light("int_fill", (0.8, -0.7, 0.35), (0.0, 0.0, 0.02), size=0.6, energy=6, color=(0.7, 0.8, 1.0), coll=C)
E.area_light("int_rim", (0.4, 0.8, 0.12), (0.0, 0.0, 0.0), size=0.2, energy=10, color=(1.0, 0.7, 0.4), coll=C)
E.point_light("int_lamp", (0.6, 0.9, 0.25), energy=4.0, color=(1.0, 0.55, 0.25), radius=0.02, coll=C_BG)
lampm = E.mat_emit("int_lampflame", (1.0, 0.6, 0.25), 40.0)
for i, (lx, ly) in enumerate([(0.55, 1.1), (0.9, 1.6), (-0.9, 1.9), (0.25, 2.2)]):
    fl = E.sphere(f"int_bokeh{i}", r=0.012, coll=C_BG, mat=lampm, scale=(1, 1, 1.6))
    fl.location = (lx, ly, 0.09 + 0.03 * i)
    E.point_light(f"int_bokehL{i}", (lx, ly, 0.1 + 0.03 * i), energy=1.5, color=(1.0, 0.55, 0.25), radius=0.01, coll=C_BG)

# ------------------------------------------------------------ camera (macro, shallow DOF)
cam = E.camera("int_cam", (0.05, -0.37, 0.205), (0.0, 0.05, 0.0), lens=55, coll=C, dof=(FX, FY - 0.01, 0.022), fstop=2.4)
cam.data.clip_start = 0.005
E.setup_outputs(scn, SLUG, mist_start=0.15, mist_depth=3.2)
E.hide_template(C_TPL)
result = {"objects": len(scn.objects)}

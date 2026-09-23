"""
S6 — ECONOMIC: The merchant's counter.
A Yuan 'Zhiyuan tongxing baochao' paper note (1287 issue; printed warning:
counterfeiters executed, informers rewarded with five silver ingots), strings of
Song & Yuan copper cash, boat-shaped silver ingots, an abacus, bolts of silk and
a Jingdezhen blue-and-white jar painted with Persian cobalt — the paper, metal
and luxury goods of the Song–Yuan commercial revolution.
Real-world scale (metres).
"""
import sys, importlib, random, math
from math import radians, sin, cos, pi
import bpy
import bmesh
from mathutils import Vector, Matrix, Euler

LIB = "/Applications/Personal App/AP-WORLD-WEBSITE/blender/lib"
if LIB not in sys.path:
    sys.path.insert(0, LIB)
import ealib as E; importlib.reload(E)
import ea_assets as A; importlib.reload(A)

SLUG = "economic"
PREVIEW = globals().get("PREVIEW", True)
scn = E.new_scene("S6_Economic", res=(2560, 1440), samples=256, look="AgX - Medium High Contrast")
E.purge()
rnd = random.Random(66)
C = E.collection("eco_counter")
C_BG = E.collection("eco_bg")
C_TPL = E.collection("eco_templates")

# ------------------------------------------------------------ materials
tabletop = E.mat_wood("eco_table", c1=(0.055, 0.03, 0.016), c2=(0.085, 0.048, 0.026), scale=2.5, rough=0.35, bump=0.03)
note_img = bpy.data.images.load(E.TEX_DIR + "/yuan_banknote.png", check_existing=True)
bw_img = bpy.data.images.load(E.TEX_DIR + "/blue_white.png", check_existing=True)


def mat_image_paper(name, img, rough=0.85, trans=0.12):
    m, nb, bsdf, out = E.new_material(name)
    tc = nb.texcoord()
    tex = nb.new("ShaderNodeTexImage", (-700, 200))
    tex.image = img
    nb.link(tc.outputs["UV"], tex.inputs["Vector"])
    n = nb.noise(tc.outputs["Object"], scale=160.0, detail=6.0, loc=(-700, -200))
    E.principled(bsdf, color=tex.outputs["Color"], rough=rough, sheen=0.3, normal=nb.bump(n.outputs["Fac"], strength=0.15, distance=0.002))
    tr = nb.new("ShaderNodeBsdfTranslucent", (0, -300))
    nb.link(tex.outputs["Color"], tr.inputs["Color"])
    mixs = nb.new("ShaderNodeMixShader", (250, 0))
    mixs.inputs[0].default_value = trans
    nb.link(bsdf.outputs[0], mixs.inputs[1])
    nb.link(tr.outputs[0], mixs.inputs[2])
    nb.link(mixs.outputs[0], out.inputs["Surface"])
    return m


note_mat = mat_image_paper("eco_note", note_img)


def mat_coin(name, img_path):
    m, nb, bsdf, out = E.new_material(name)
    img = bpy.data.images.load(img_path, check_existing=True)
    img.colorspace_settings.name = "Non-Color"
    tc = nb.texcoord()
    tex = nb.new("ShaderNodeTexImage", (-800, 200))
    tex.image = img
    nb.link(tc.outputs["UV"], tex.inputs["Vector"])
    n = nb.noise(tc.outputs["Object"], scale=900.0, detail=6.0, rough=0.7, loc=(-800, -200))
    patina = nb.ramp(n.outputs["Fac"], [(0.3, (0.08, 0.04, 0.02)), (0.5, (0.2, 0.09, 0.04)), (0.62, (0.1, 0.13, 0.08)), (0.75, (0.18, 0.08, 0.035))], loc=(-500, -150))
    sep = nb.new("ShaderNodeSeparateColor", (-600, 200))
    nb.link(tex.outputs["Color"], sep.inputs[0])
    relief = sep.outputs[0]
    col = nb.mix(nb.maprange(relief, 0.5, 0.95, 0.0, 0.8, loc=(-500, 150)), patina.outputs[0], (0.55, 0.26, 0.1), loc=(-250, 100))
    metal = nb.maprange(relief, 0.3, 0.95, 0.35, 0.9, loc=(-250, -100))
    E.principled(bsdf, color=col, metal=metal, rough=nb.maprange(n.outputs["Fac"], 0.3, 0.7, 0.3, 0.55, loc=(-250, -250)),
                 normal=nb.bump(relief, strength=0.7, distance=0.0006))
    return m


coin_mats = [mat_coin("eco_coin_a", E.TEX_DIR + "/coin_a.png"), mat_coin("eco_coin_b", E.TEX_DIR + "/coin_b.png")]
silver = E.mat_gold("eco_silver", color=(0.8, 0.8, 0.78), rough=0.24)
cord = E.mat_noisy("eco_cord", (0.35, 0.05, 0.03), (0.5, 0.1, 0.05), scale=400, rough=(0.7, 0.9), bump=0.3)
beadwood = E.mat_wood("eco_bead", c1=(0.05, 0.02, 0.012), c2=(0.12, 0.05, 0.025), scale=40.0, rough=0.3, bump=0.05)
framewood = E.mat_wood("eco_abframe", c1=(0.12, 0.06, 0.03), c2=(0.22, 0.12, 0.06), scale=12.0, rough=0.45)


def mat_silk(name, color):
    m, nb, bsdf, out = E.new_material(name)
    tc = nb.texcoord()
    w = nb.wave(tc.outputs["Object"], scale=900.0, direction="Z", loc=(-800, 0))
    E.principled(bsdf, color=color, rough=0.38, sheen=0.35, aniso=0.5, normal=nb.bump(w.outputs["Fac"], strength=0.05, distance=0.001))
    try:
        bsdf.inputs['Sheen Tint'].default_value = (min(1, color[0] * 2.5), min(1, color[1] * 2.5), min(1, color[2] * 2.5), 1)
    except Exception:
        pass
    return m


silks = [mat_silk("eco_silk_red", (0.2, 0.01, 0.015)), mat_silk("eco_silk_jade", (0.015, 0.08, 0.065)), mat_silk("eco_silk_gold", (0.3, 0.16, 0.025))]


def mat_porcelain(name, img):
    m, nb, bsdf, out = E.new_material(name)
    tc = nb.texcoord()
    tex = nb.new("ShaderNodeTexImage", (-700, 200))
    tex.image = img
    nb.link(tc.outputs["UV"], tex.inputs["Vector"])
    E.principled(bsdf, color=tex.outputs["Color"], rough=0.08, coat=1.0, coat_rough=0.03)
    return m


porcelain = mat_porcelain("eco_porcelain", bw_img)

# ------------------------------------------------------------ table
E.box("eco_tabletop", (1.8, 1.1, 0.05), loc=(0, 0.2, -0.05), coll=C, mat=tabletop, bevel=0.004)


# ------------------------------------------------------------ paper notes (gently curled)
def paper_sheet(name, w, h, mat, loc, rotz, curl=0.01, lift_edge=0.0):
    nu, nv = 30, 40
    verts, faces, uvs = [], [], []
    for j in range(nv + 1):
        v = j / nv
        for i in range(nu + 1):
            u = i / nu
            x, y = (u - 0.5) * w, (v - 0.5) * h
            z = curl * (0.5 - 0.5 * cos(2 * pi * u)) * 0.3 + lift_edge * max(0.0, (v - 0.8) / 0.2) ** 2
            verts.append((x, y, z))
            uvs.append((u, v))
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i
            faces.append((a, a + 1, a + nu + 2, a + nu + 1))
    ob = E.obj_from_data(name, verts, faces, C, mat, smooth=True, uvs=uvs)
    ob.location = loc
    ob.rotation_euler.z = rotz
    E.add_mod(ob, "SOLIDIFY", thickness=0.00025)
    return ob


paper_sheet("eco_note1", 0.22, 0.308, note_mat, (-0.12, 0.02, 0.0012), radians(8), curl=0.006, lift_edge=0.008)
paper_sheet("eco_note2", 0.22, 0.308, note_mat, (-0.26, 0.13, 0.0006), radians(-16), curl=0.004)


# ------------------------------------------------------------ copper cash
def coin_mesh(name, r=0.0125, t=0.0016, hole=0.0034, seg=40):
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    outer_t, outer_b, inner_t, inner_b = [], [], [], []
    for i in range(seg):
        a = 2 * pi * i / seg
        outer_t.append(bm.verts.new((r * cos(a), r * sin(a), t / 2)))
        outer_b.append(bm.verts.new((r * cos(a), r * sin(a), -t / 2)))
    for i in range(seg):
        a = 2 * pi * i / seg
        c, s = cos(a), sin(a)
        k = hole / max(abs(c), abs(s))
        inner_t.append(bm.verts.new((k * c, k * s, t / 2)))
        inner_b.append(bm.verts.new((k * c, k * s, -t / 2)))
    for i in range(seg):
        j = (i + 1) % seg
        bm.faces.new((outer_t[i], outer_t[j], inner_t[j], inner_t[i]))
        bm.faces.new((outer_b[j], outer_b[i], inner_b[i], inner_b[j]))
        bm.faces.new((outer_b[i], outer_b[j], outer_t[j], outer_t[i]))
        bm.faces.new((inner_t[i], inner_t[j], inner_b[j], inner_b[i]))
    for f in bm.faces:
        for loop in f.loops:
            co = loop.vert.co
            loop[uv_layer].uv = (co.x / (2 * r) + 0.5, co.y / (2 * r) + 0.5)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


coin_me = [coin_mesh("coin_a"), coin_mesh("coin_b")]
for k in range(2):
    coin_me[k].materials.append(coin_mats[k])


def coin_string(name, path_pts, n=70, spacing=0.0019):
    """Coins threaded on a cord following a path (a 'string of cash')."""
    pts = [Vector(p) for p in path_pts]
    seg_len = [(pts[i + 1] - pts[i]).length for i in range(len(pts) - 1)]
    total = sum(seg_len)
    cord_pts = []
    for k in range(n):
        s = min(total, k * spacing)
        acc = 0.0
        p, tan = pts[0], (pts[1] - pts[0]).normalized()
        for i, L in enumerate(seg_len):
            if acc + L >= s:
                t = (s - acc) / L
                p = pts[i].lerp(pts[i + 1], t)
                tan = (pts[i + 1] - pts[i]).normalized()
                break
            acc += L
        ob = bpy.data.objects.new(f"{name}_{k}", coin_me[0 if rnd.random() < 0.6 else 1])
        E.link(ob, C)
        q = tan.to_track_quat("Z", "Y")
        m = q.to_matrix().to_4x4() @ Matrix.Rotation(rnd.uniform(0, 6.28), 4, "Z") @ Matrix.Rotation(rnd.uniform(-0.1, 0.1), 4, "X")
        ob.rotation_euler = m.to_euler()
        ob.location = p + Vector((0, 0, 0.0125))
        cord_pts.append(tuple(p + Vector((0, 0, 0.0125))))
    E._poly_curve(name + "_cord", cord_pts, 0.0011, C, cord)


coin_string("eco_cashA", [(0.06, -0.15, 0), (0.12, -0.1, 0), (0.17, -0.02, 0), (0.19, 0.08, 0)], n=100)
coin_string("eco_cashB", [(0.3, -0.19, 0), (0.33, -0.06, 0), (0.31, 0.05, 0), (0.25, 0.13, 0)], n=90)
for k, (x, y) in enumerate([(0.02, -0.17), (-0.02, -0.125), (0.05, -0.22), (-0.06, -0.2), (0.1, -0.215), (0.135, -0.16)]):
    ob = bpy.data.objects.new(f"eco_loose{k}", coin_me[k % 2])
    E.link(ob, C)
    ob.location = (x, y, 0.0008 + (0.0016 if k == 3 else 0))
    ob.rotation_euler = (rnd.uniform(-0.03, 0.03), rnd.uniform(-0.03, 0.03), rnd.uniform(0, 6.28))


# ------------------------------------------------------------ silver ingots (Yuan-style waisted slabs)
def ingot(name, L=0.085, W=0.05, H=0.022, loc=(0, 0, 0), rot=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=6, use_grid_fill=True)
    for v in bm.verts:
        x, y, z = v.co
        v.co.x = x * L * (1.0 if z > 0 else 0.92)
        v.co.y = y * W * (0.78 + 0.22 * (abs(2 * x) ** 1.2)) * (1.0 if z > 0 else 0.9)
        rim = 1.0 if (abs(2 * x) > 0.8 or abs(2 * y) > 0.8) else 0.0
        v.co.z = (z + 0.5) * H + (0.12 * H * rim - 0.1 * H * (1 - rim) if z > 0 else 0)
    ob = E.obj_from_bm(bm, name, C, silver, smooth=True)
    E.add_mod(ob, "SUBSURF", levels=2, render_levels=2)
    ob.location = loc
    ob.rotation_euler.z = rot
    return ob


ingot("eco_ingot1", loc=(0.1, 0.2, 0.0), rot=radians(20))
ingot("eco_ingot2", loc=(0.19, 0.24, 0.0), rot=radians(-30))
ingot("eco_ingot3", loc=(0.15, 0.3, 0.022), rot=radians(5))


# ------------------------------------------------------------ abacus (suanpan)
def abacus(name, loc, rot):
    parts = []
    Wd, Ht, rods = 0.34, 0.16, 13
    for yy in (-Ht / 2, Ht / 2):
        parts.append(E.box(name + f"_fr{yy}", (Wd + 0.02, 0.014, 0.022), loc=(0, yy, 0), coll=C, mat=framewood))
    for xx in (-Wd / 2, Wd / 2):
        parts.append(E.box(name + f"_fs{xx}", (0.014, Ht, 0.022), loc=(xx, 0, 0), coll=C, mat=framewood))
    beam_y = Ht / 2 - 0.045
    parts.append(E.box(name + "_beam", (Wd, 0.008, 0.02), loc=(0, beam_y, 0.001), coll=C, mat=framewood))
    bead_prof = [(0.0, -0.006), (0.006, -0.005), (0.0105, 0.0), (0.006, 0.005), (0.0, 0.006)]
    for i in range(rods):
        x = -Wd / 2 + (i + 0.5) * Wd / rods
        rod = E.cylinder(name + f"_rod{i}", r=0.0012, h=Ht, n=6, coll=C, mat=framewood, rot=(radians(-90), 0, 0))
        rod.location = (x, Ht / 2, 0.011)
        parts.append(rod)
        up = rnd.randint(0, 2)
        lo = rnd.randint(0, 5)
        for b in range(2):
            yb = (Ht / 2 - 0.013 - b * 0.0122) if b < 2 - up else (beam_y + 0.011 + (b - (2 - up)) * 0.0122)
            bb = E.lathe(name + f"_h{i}_{b}", bead_prof, n=16, coll=C, mat=beadwood)
            bb.location = (x, yb, 0.011)
            bb.rotation_euler.x = radians(90)
            parts.append(bb)
        for b in range(5):
            yb = (beam_y - 0.011 - b * 0.0122) if b < lo else (-Ht / 2 + 0.013 + (4 - b) * 0.0122)
            bb = E.lathe(name + f"_e{i}_{b}", bead_prof, n=16, coll=C, mat=beadwood)
            bb.location = (x, yb, 0.011)
            bb.rotation_euler.x = radians(90)
            parts.append(bb)
    ob = E.join(parts, name)
    ob.location = loc
    ob.rotation_euler.z = rot
    return ob


abacus("eco_abacus", loc=(0.37, 0.3, 0.0), rot=radians(-24))

# ------------------------------------------------------------ silk bolts + a flowing length of silk
zc = 0.0
for k in range(5):
    th = rnd.uniform(0.018, 0.026)
    fold = E.box(f"eco_silkfold{k}", (0.26, 0.19, th), loc=(-0.44 + rnd.uniform(-0.01, 0.01), 0.36 + rnd.uniform(-0.01, 0.01), zc), rot=(0, 0, radians(12 + rnd.uniform(-4, 4))), coll=C, mat=silks[k % 3])
    E.add_mod(fold, "BEVEL", width=th * 0.45, segments=4)
    E.add_mod(fold, "SUBSURF", levels=3, render_levels=3, subdivision_type="SIMPLE")
    dmod = fold.modifiers.new("wrinkle", "DISPLACE")
    dmod.texture = A._clouds(0.05, "T_silkwrinkle")
    dmod.strength = 0.012
    dmod.texture_coords = "OBJECT"
    zc += th
sv, sf, su = [], [], []
N = 40
for i in range(N + 1):
    t = i / N
    x = -0.46 + 0.36 * t
    y = 0.3 - 0.12 * t + 0.03 * sin(t * 6)
    z = 0.0015 + 0.012 * max(0, sin(t * 9)) * (1 - t)
    for s in (-1, 1):
        sv.append((x, y + s * 0.07, z + 0.004 * s * sin(t * 12)))
        su.append((t, (s + 1) / 2))
for i in range(N):
    a = i * 2
    sf.append((a, a + 2, a + 3, a + 1))


# ------------------------------------------------------------ blue-and-white jar (guan)
jar_prof = [(0.0, 0.0), (0.055, 0.0), (0.065, 0.005), (0.075, 0.04), (0.11, 0.12), (0.135, 0.2), (0.14, 0.24), (0.13, 0.29), (0.1, 0.33),
            (0.065, 0.35), (0.06, 0.365), (0.062, 0.39), (0.058, 0.395), (0.0, 0.395)]
jar = E.lathe("eco_jar", jar_prof, n=96, coll=C, mat=porcelain)
jar.location = (0.06, 0.4, 0.0)
jar.rotation_euler.z = radians(200)

# ------------------------------------------------------------ background: shelves of wares, lamps
wall = E.mat_noisy("eco_wall", (0.1, 0.075, 0.055), (0.17, 0.13, 0.09), scale=2, rough=(0.8, 1.0), bump=0.1)
E.box("eco_backwall", (5, 0.1, 3), loc=(0, 2.2, -1), coll=C_BG, mat=wall)
celadon = E.mat_basic("eco_celadon", (0.3, 0.42, 0.33), rough=0.1, coat=1.0)
for s in range(3):
    E.box(f"eco_shelf{s}", (1.6, 0.3, 0.025), loc=(0.2, 2.0, 0.15 + s * 0.4), coll=C_BG, mat=framewood)
    for k in range(6):
        pj = E.lathe(f"eco_shelfjar{s}{k}", [(0.0, 0.0), (0.05, 0.0), (0.08, 0.08), (0.07, 0.16), (0.03, 0.2), (0.0, 0.2)], n=24, coll=C_BG,
                     mat=porcelain if (s + k) % 2 else celadon)
        pj.location = (-0.45 + k * 0.26, 2.0, 0.165 + s * 0.4)
E.gradient_world(scn, top=(0.01, 0.01, 0.012), horizon=(0.018, 0.015, 0.012), strength=1.0)
E.area_light("eco_key", (-1.0, 0.5, 0.9), (0.0, 0.05, 0.0), size=1.0, energy=110, color=(1.0, 0.82, 0.6), coll=C)
E.area_light("eco_fill", (0.9, -0.8, 0.5), (0.0, 0.0, 0.0), size=0.8, energy=10, color=(0.75, 0.85, 1.0), coll=C)
E.area_light("eco_rim", (0.3, 1.2, 0.35), (0.0, 0.2, 0.05), size=0.4, energy=25, color=(1.0, 0.7, 0.45), coll=C)
lampm = E.mat_emit("eco_lampflame", (1.0, 0.6, 0.25), 45.0)
for i, (lx, ly, lz) in enumerate([(0.8, 1.6, 0.35), (-0.7, 1.9, 0.6), (1.2, 2.0, 0.9)]):
    fl = E.sphere(f"eco_bokeh{i}", r=0.012, coll=C_BG, mat=lampm, scale=(1, 1, 1.6))
    fl.location = (lx, ly, lz)
    E.point_light(f"eco_bokehL{i}", (lx, ly, lz), energy=2.0, color=(1.0, 0.55, 0.25), radius=0.01, coll=C_BG)

cam = E.camera("eco_cam", (0.3, -0.74, 0.66), (0.0, 0.15, 0.02), lens=46, coll=C, dof=(-0.06, 0.0, 0.0), fstop=4.0)
cam.data.clip_start = 0.005
E.setup_outputs(scn, SLUG, mist_start=0.3, mist_depth=2.2)
E.hide_template(C_TPL)
result = {"objects": len(scn.objects)}

"""
Interactive artifacts for the website's three.js viewer (exported as .glb).
Materials are glTF-friendly (image textures / flat colours) — no procedural nodes.
Empties named 'hotspot_*' mark annotation anchors that the viewer reads by name.

  vase    — Yuan blue-and-white meiping (Jingdezhen, Persian cobalt)
  compass — mariner's water compass with 24-direction board and floating needle
  junk    — cutaway seagoing junk: watertight bulkheads, keel, sternpost rudder,
            battened lug sails, compass station, cargo of porcelain & silk
"""
import sys, importlib, math, random
from math import radians, sin, cos, pi
import bpy
import bmesh
from mathutils import Vector

LIB = "/Applications/Personal App/AP-WORLD-WEBSITE/blender/lib"
if LIB not in sys.path:
    sys.path.insert(0, LIB)
import ealib as E; importlib.reload(E)

ROOT = "/Applications/Personal App/AP-WORLD-WEBSITE"
OUT = ROOT + "/public/models"
TEX = ROOT + "/blender/textures"
WHICH = globals().get("WHICH", ["vase", "compass", "junk"])
rnd = random.Random(5)


def mat_tex(name, path, rough=0.6, metal=0.0, colorspace="sRGB"):
    m = bpy.data.materials.get(name)
    if m:
        bpy.data.materials.remove(m)
    m, nb, bsdf, out = E.new_material(name)
    img = bpy.data.images.load(path, check_existing=True)
    img.colorspace_settings.name = colorspace
    tex = nb.new("ShaderNodeTexImage", (-400, 200))
    tex.image = img
    uv = nb.new("ShaderNodeUVMap", (-700, 200))
    nb.link(uv.outputs[0], tex.inputs["Vector"])
    nb.link(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    return m


def mat_flat(name, color, rough=0.6, metal=0.0, alpha=1.0, emit=None):
    m = bpy.data.materials.get(name)
    if m:
        bpy.data.materials.remove(m)
    m, nb, bsdf, out = E.new_material(name)
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if alpha < 1:
        bsdf.inputs["Alpha"].default_value = alpha
        try:
            m.surface_render_method = "BLENDED"
        except Exception:
            pass
    return m


def hotspot(name, loc, coll):
    e = bpy.data.objects.new("hotspot_" + name, None)
    e.empty_display_size = 0.2
    e.location = loc
    E.link(e, coll)
    return e


def export(scn_name, fname):
    """Export exactly the renderable objects of one scene (deselect everything else first)."""
    scn = bpy.data.scenes[scn_name]
    vl = scn.view_layers[0]
    for s in bpy.data.scenes:
        for v in s.view_layers:
            for o in v.objects:
                try:
                    o.select_set(False, view_layer=v)
                except Exception:
                    pass
    for o in scn.objects:
        if not o.hide_render:
            o.select_set(True, view_layer=vl)
    with bpy.context.temp_override(window=bpy.context.window, scene=scn, view_layer=vl):
        bpy.ops.export_scene.gltf(filepath=f"{OUT}/{fname}", export_format="GLB", use_selection=True, use_active_scene=True,
                                  export_apply=True, export_yup=True, export_texcoords=True, export_normals=True,
                                  export_materials="EXPORT", export_image_format="WEBP", export_image_quality=82,
                                  export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6,
                                  export_cameras=False, export_lights=False)
    return f"{OUT}/{fname}"


import os
os.makedirs(OUT, exist_ok=True)
results = {}

# =====================================================================================
if "vase" in WHICH:
    scn = E.new_scene("GLB_Vase", res=(1024, 1024), samples=64)
    E.purge()
    C = E.collection("vase")
    porcelain = mat_tex("glb_porcelain", TEX + "/blue_white.png", rough=0.12)
    biscuit = mat_flat("glb_biscuit", (0.78, 0.66, 0.5), rough=0.9)
    # meiping profile from the foot ring up to the mouth (v runs foot -> mouth)
    prof = [(0.062, 0.0), (0.066, 0.008), (0.07, 0.04), (0.078, 0.09), (0.092, 0.14), (0.11, 0.2), (0.124, 0.25), (0.128, 0.275),
            (0.122, 0.3), (0.1, 0.322), (0.07, 0.336), (0.04, 0.343), (0.03, 0.348), (0.03, 0.362), (0.036, 0.366), (0.033, 0.372), (0.024, 0.372)]
    vase = E.lathe("meiping", prof, n=128, coll=C, mat=porcelain)
    foot = E.cylinder("meiping_foot", r=0.062, h=0.004, n=64, coll=C, mat=biscuit)
    inner = E.cylinder("meiping_mouth_inner", r=0.024, h=0.001, n=32, loc=(0, 0, 0.36), coll=C, mat=mat_flat("glb_dark", (0.02, 0.02, 0.025), rough=0.8))
    hotspot("cobalt", (0.0, -0.12, 0.2), C)
    hotspot("lappets", (0.0, -0.1, 0.305), C)
    hotspot("lotus", (0.0, -0.085, 0.07), C)
    results["vase"] = export("GLB_Vase", "meiping_vase.glb")

# =====================================================================================
if "compass" in WHICH:
    scn = E.new_scene("GLB_Compass", res=(1024, 1024), samples=64)
    E.purge()
    C = E.collection("compass")
    board_mat = mat_tex("glb_compassboard", TEX + "/compass_board.png", rough=0.35)
    lacquer = mat_flat("glb_lacquer", (0.16, 0.035, 0.02), rough=0.3)
    bronze = mat_flat("glb_bronze", (0.55, 0.38, 0.18), rough=0.35, metal=1.0)
    water = mat_flat("glb_water", (0.12, 0.2, 0.22), rough=0.05, alpha=0.55)
    iron = mat_flat("glb_iron", (0.08, 0.08, 0.09), rough=0.35, metal=0.9)
    reed = mat_flat("glb_reed", (0.6, 0.5, 0.3), rough=0.7)
    R = 0.15
    # board: top disk with planar UVs for the printed rings
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    ret = bmesh.ops.create_circle(bm, cap_ends=True, radius=R, segments=128)
    for f in bm.faces:
        for lp in f.loops:
            lp[uvl].uv = (lp.vert.co.x / (2 * R) + 0.5, lp.vert.co.y / (2 * R) + 0.5)
    top = E.obj_from_bm(bm, "compass_face", C, board_mat)
    top.location.z = 0.025
    body = E.cylinder("compass_body", r=R, h=0.025, n=128, coll=C, mat=lacquer)
    rim = E.lathe("compass_rim", [(R - 0.002, 0.025), (R + 0.004, 0.025), (R + 0.006, 0.033), (R + 0.002, 0.036), (R - 0.004, 0.034), (R - 0.004, 0.026)], n=128, coll=C, mat=lacquer)
    # central water bowl (bronze) sunk into the board, with water and a floating needle
    bowl = E.lathe("compass_bowl", [(0.0, 0.012), (0.045, 0.012), (0.049, 0.02), (0.05, 0.03), (0.047, 0.031), (0.043, 0.02), (0.0, 0.018)], n=96, coll=C, mat=bronze)
    wat = E.cylinder("compass_water", r=0.0445, h=0.001, n=96, loc=(0, 0, 0.027), coll=C, mat=water)
    # magnetised needle threaded through a sliver of reed so it floats (pointing N–S along Y)
    nv = [(0, 0.04, 0.0285), (0.0022, 0, 0.0285), (0, -0.04, 0.0285), (-0.0022, 0, 0.0285)]
    needle = E.obj_from_data("compass_needle", nv, [(0, 1, 2, 3)], C, iron)
    E.add_mod(needle, "SOLIDIFY", thickness=0.0015)
    rd = E.cylinder("compass_reed", r=0.0028, h=0.024, n=12, coll=C, mat=reed, rot=(0, radians(90), 0))
    rd.location = (-0.012, 0, 0.0292)
    red_tip = E.sphere("compass_south_tip", r=0.0024, coll=C, mat=mat_flat("glb_red", (0.6, 0.06, 0.04), rough=0.4))
    red_tip.location = (0, -0.04, 0.0292)
    hotspot("needle", (0.0, 0.0, 0.035), C)
    hotspot("directions", (0.0, -0.13, 0.03), C)
    hotspot("trigrams", (0.08, 0.0, 0.03), C)
    results["compass"] = export("GLB_Compass", "water_compass.glb")

# =====================================================================================
if "junk" in WHICH:
    scn = E.new_scene("GLB_Junk", res=(1024, 1024), samples=64)
    E.purge()
    C = E.collection("junk_cutaway")
    planks = mat_tex("glb_planks", TEX + "/glb_planks.png", rough=0.75)
    sailm = mat_tex("glb_sail", TEX + "/glb_sail.png", rough=0.85)
    porcelain = mat_tex("glb_porcelain_small", TEX + "/blue_white.png", rough=0.15)
    bulk = mat_flat("glb_bulkhead", (0.62, 0.45, 0.27), rough=0.7)
    dark = mat_flat("glb_darkwood", (0.1, 0.06, 0.035), rough=0.6)
    red = mat_flat("glb_redlacquer", (0.45, 0.06, 0.03), rough=0.5)
    white = mat_flat("glb_white", (0.85, 0.82, 0.74), rough=0.5)
    black = mat_flat("glb_black", (0.02, 0.02, 0.02), rough=0.5)
    crate = mat_flat("glb_crate", (0.42, 0.3, 0.16), rough=0.8)
    silk = mat_flat("glb_silk", (0.55, 0.08, 0.06), rough=0.45)
    silk2 = mat_flat("glb_silk2", (0.1, 0.35, 0.28), rough=0.45)
    cutface = mat_flat("glb_cutface", (0.78, 0.6, 0.38), rough=0.8)

    L, B, D = 32.0, 9.0, 4.2
    NX, NS = 48, 14

    def half_beam(u):
        hb = B / 2 * (0.72 + 0.28 * sin(pi * min(1.0, u * 1.15)))
        return hb * (1 - 0.6 * E.smoothstep(0.62, 1.0, u))

    def sheer(u):
        return D * (1.0 + 1.1 * (1 - u) ** 3.5 + 0.5 * u ** 3.2)

    def keel(u):
        return D * 0.6 * (1 - (2 * u - 1) ** 8)

    def section(u, a):
        """a: 0 at keel (centreline) -> 1 at gunwale (port side, y<0)."""
        hb, top, bottom = half_beam(u), sheer(u), -keel(u)
        return (-hb * (a ** 0.7), bottom + (top - bottom) * (a ** 1.35))

    # --- port half hull (cut along the centreline so the interior is visible)
    verts, faces, uvs = [], [], []
    for i in range(NX + 1):
        u = i / NX
        x = -L / 2 + L * u
        for j in range(NS + 1):
            a = j / NS
            y, z = section(u, a)
            verts.append((x, y, z))
            uvs.append((u * 4.0, a * 1.5))
    w = NS + 1
    for i in range(NX):
        for j in range(NS):
            k = i * w + j
            faces.append((k, k + 1, k + w + 1, k + w))
    hull = E.obj_from_data("junk_hull_port", verts, faces, C, planks, smooth=True, uvs=uvs)
    E.add_mod(hull, "SOLIDIFY", thickness=0.25, offset=1.0)
    # red wale band along the top of the hull
    bv, bf = [], []
    for i in range(NX + 1):
        u = i / NX
        x = -L / 2 + L * u
        y, z = section(u, 1.0)
        bv += [(x, y - 0.06, z - 0.9), (x, y - 0.06, z + 0.05)]
    for i in range(NX):
        k = i * 2
        bf.append((k, k + 2, k + 3, k + 1))
    E.obj_from_data("junk_wale", bv, bf, C, red)
    # keel timber
    kv = []
    E.box("junk_keel", (L * 0.84, 0.45, 0.6), loc=(0, 0, -keel(0.5) - 0.2), coll=C, mat=dark)
    # --- watertight bulkheads: 12 walls -> 13 compartments (as in the Quanzhou wreck)
    N_BULK = 12
    deck_z = lambda u: sheer(u) - 0.45
    for b in range(N_BULK):
        u = 0.07 + 0.86 * (b + 0.5) / N_BULK
        x = -L / 2 + L * u
        pts = [(x, 0.0, -keel(u) + 0.05)]
        for j in range(1, NS + 1):
            a = j / NS
            y, z = section(u, a)
            z = min(z, deck_z(u))
            pts.append((x, y * 0.97, z))
        pts.append((x, 0.0, deck_z(u)))
        ob = E.obj_from_data(f"junk_bulkhead{b:02d}", pts, [tuple(range(len(pts)))], C, bulk)
        E.add_mod(ob, "SOLIDIFY", thickness=0.14)
        # cut-face strip along the centreline so the section reads as 'sliced'
        E.box(f"junk_bulkcut{b:02d}", (0.16, 0.05, deck_z(u) + keel(u) - 0.05), loc=(x, 0.0, -keel(u) + 0.05), coll=C, mat=cutface)
    # --- deck (port half only, so the holds stay open to view) + stern castle
    dv, df, du = [], [], []
    for i in range(NX + 1):
        u = i / NX
        x = -L / 2 + L * u
        hb = half_beam(u) * 0.97
        dv += [(x, 0.0, deck_z(u)), (x, -hb, deck_z(u))]
        du += [(u * 5, 0), (u * 5, 1)]
    for i in range(NX):
        k = i * 2
        df.append((k, k + 2, k + 3, k + 1))
    deck = E.obj_from_data("junk_deck_port", dv, df, C, planks, uvs=du)
    E.add_mod(deck, "SOLIDIFY", thickness=0.12)
    cab_u = 0.1
    cab = E.box("junk_sterncabin", (L * 0.17, half_beam(cab_u) * 1.7, 2.2), loc=(-L / 2 + L * 0.13, 0, deck_z(cab_u)), coll=C, mat=red)
    E.box("junk_cabinroof", (L * 0.19, half_beam(cab_u) * 1.9, 0.25), loc=(-L / 2 + L * 0.13, 0, deck_z(cab_u) + 2.2), coll=C, mat=dark)
    # --- sternpost rudder + tiller
    E.box("junk_rudder", (2.4, 0.3, D * 1.7), loc=(-L / 2 - 1.3, 0, -keel(0.02) - D * 0.25), coll=C, mat=dark)
    E.cylinder("junk_rudderpost", r=0.22, h=D * 2.5, n=10, loc=(-L / 2 - 0.35, 0, -D * 0.45), coll=C, mat=dark)
    E.box("junk_tiller", (3.5, 0.18, 0.18), loc=(-L / 2 + 1.0, 0, deck_z(0.02) + 1.9), coll=C, mat=dark)
    # --- compass station on the poop deck
    comp = E.cylinder("junk_compass", r=0.35, h=0.12, n=24, loc=(-L / 2 + L * 0.2, 0.0, deck_z(0.2) + 2.45), coll=C, mat=white)
    # --- masts, battened lug sails, battens
    def sail(name, mx, mz, mh, width, bat):
        sv, sf, su = [], [], []
        nu, nv = 10, bat * 2
        for j in range(nv + 1):
            v = j / nv
            for i in range(nu + 1):
                uu = i / nu
                fwd, aft = width * 0.2, -width * (0.7 + 0.3 * v ** 0.7)
                x = fwd + (aft - fwd) * uu
                z = mh * 0.82 * v + mh * 0.18 * (v ** 1.5) * uu
                y = 0.6 * sin(pi * uu)
                sv.append((mx + x, y + 0.4, mz + mh * 0.15 + z))
                su.append((uu, v))
        for j in range(nv):
            for i in range(nu):
                k = j * (nu + 1) + i
                sf.append((k, k + 1, k + nu + 2, k + nu + 1))
        s = E.obj_from_data(name, sv, sf, C, sailm, smooth=True, uvs=su)
        E.add_mod(s, "SOLIDIFY", thickness=0.05)
        for b in range(bat + 1):
            v = b / bat
            p0 = sv[(b * 2) * (nu + 1)]
            p1 = sv[(b * 2) * (nu + 1) + nu]
            mid = sv[(b * 2) * (nu + 1) + nu // 2]
            E._poly_curve(name + f"_bat{b}", [(p0[0] + 0.2, p0[1] + 0.08, p0[2]), (mid[0], mid[1] + 0.08, mid[2]), (p1[0], p1[1] + 0.08, p1[2])], 0.07, C, dark)
        return s
    for mi, (u, hs, bat) in enumerate([(0.52, 1.0, 9), (0.83, 0.7, 7), (0.2, 0.55, 6)]):
        mx = -L / 2 + L * u
        mh = L * 0.95 * hs
        E.cylinder(f"junk_mast{mi}", r=0.3 * hs, h=mh, n=12, r2=0.16 * hs, loc=(mx, 0.0, -keel(u) + 0.4), coll=C, mat=dark)
        sail(f"junk_sail{mi}", mx, deck_z(u), mh * 0.95, L * 0.38 * hs, bat)
    # --- oculi at the bow
    for s in (-1,):
        u = 0.9
        x = -L / 2 + L * u
        y, z = section(u, 0.75)
        e1 = E.sphere("junk_eye", r=0.5, coll=C, mat=white, scale=(1, 0.2, 0.75))
        e1.location = (x, y - 0.18, z)
        e2 = E.sphere("junk_pupil", r=0.24, coll=C, mat=black, scale=(1, 0.2, 1))
        e2.location = (x + 0.05, y - 0.28, z)
    # --- cargo in the holds: porcelain jars packed in crates, silk bales, crates
    jar_prof = [(0.0, 0.0), (0.16, 0.0), (0.22, 0.12), (0.3, 0.35), (0.3, 0.5), (0.2, 0.68), (0.12, 0.72), (0.12, 0.78), (0.0, 0.78)]
    jar = E.lathe("junk_jar_tpl", jar_prof, n=24, coll=C, mat=porcelain)
    jar.hide_render = True
    jar.hide_viewport = True
    for b in range(N_BULK - 1):
        u0 = 0.07 + 0.86 * (b + 0.5) / N_BULK
        u1 = 0.07 + 0.86 * (b + 1.5) / N_BULK
        um = (u0 + u1) / 2
        x0 = -L / 2 + L * um
        hb = half_beam(um)
        top_, bottom_ = sheer(um), -keel(um)

        def hull_z(yv):
            av = min(1.0, (abs(yv) / hb) ** (1 / 0.7))
            return bottom_ + (top_ - bottom_) * (av ** 1.35)
        kind = b % 3
        for k in range(6):
            yy = -0.45 - (k % 3) * (hb * 0.22)
            floor_z = hull_z(yy - 0.45) + 0.25
            xx = x0 + (-0.55 if k < 3 else 0.55) * (L * 0.86 / N_BULK) * 0.45
            if kind == 0:
                j = bpy.data.objects.new(f"junk_jar{b}_{k}", jar.data)
                E.link(j, C)
                j.location = (xx, yy, floor_z)
                j.scale = (1.2, 1.2, 1.2)
            elif kind == 1:
                E.box(f"junk_crate{b}_{k}", (0.9, 0.9, 0.8), loc=(xx, yy, floor_z), coll=C, mat=crate)
            else:
                bale = E.cylinder(f"junk_bale{b}_{k}", r=0.35, h=0.95, n=12, coll=C, mat=silk if k % 2 else silk2, rot=(radians(90), 0, 0))
                bale.location = (xx, yy + 0.45, floor_z + 0.35)
    # annotation anchors
    hotspot("bulkheads", (-L / 2 + L * 0.47, -0.2, 0.6), C)
    hotspot("rudder", (-L / 2 - 1.3, 0.0, -0.5), C)
    hotspot("sails", (-L / 2 + L * 0.38, 0.6, 18.0), C)
    hotspot("compass", (-L / 2 + L * 0.2, 0.0, deck_z(0.2) + 2.7), C)
    hotspot("cargo", (-L / 2 + L * 0.3, -1.4, -0.4), C)
    hotspot("keel", (0.0, 0.0, -keel(0.5) - 0.4), C)
    results["junk"] = export("GLB_Junk", "junk_cutaway.glb")

result = results

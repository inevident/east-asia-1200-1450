"""
ea_assets — reusable procedural assets (architecture, ships, trees, people)
for the East Asia 1200–1450 scenes. Depends on ealib.
"""
import bpy
import bmesh
import math
import random
from math import sin, cos, pi, radians
from mathutils import Vector, Matrix, noise

import ealib as E


# ---------------------------------------------------------------------------
# Shared material palette (created lazily, cached per blend file)
# ---------------------------------------------------------------------------

def palette():
    def get(name, fn):
        m = bpy.data.materials.get(name)
        return m if m is not None else fn()
    P = {}
    P["tiles"] = get("P_tiles", lambda: E.mat_tiles("P_tiles", color=(0.075, 0.08, 0.09), rows=34, rough=0.4))
    P["tiles_green"] = get("P_tiles_green", lambda: E.mat_tiles("P_tiles_green", color=(0.08, 0.22, 0.14), rows=34, rough=0.25, glaze=0.6))
    P["tiles_gold"] = get("P_tiles_gold", lambda: E.mat_tiles("P_tiles_gold", color=(0.55, 0.36, 0.06), rows=34, rough=0.25, glaze=0.7))
    P["red"] = get("P_red", lambda: E.mat_noisy("P_red", (0.32, 0.035, 0.02), (0.45, 0.06, 0.03), scale=6, rough=(0.45, 0.7), bump=0.05))
    P["wood"] = get("P_wood", lambda: E.mat_wood("P_wood"))
    P["wood_dark"] = get("P_wood_dark", lambda: E.mat_wood("P_wood_dark", c1=(0.07, 0.04, 0.025), c2=(0.16, 0.09, 0.05)))
    P["wood_raw"] = get("P_wood_raw", lambda: E.mat_wood("P_wood_raw", c1=(0.3, 0.2, 0.11), c2=(0.5, 0.36, 0.2), rough=0.7))
    P["plaster"] = get("P_plaster", lambda: E.mat_noisy("P_plaster", (0.62, 0.58, 0.5), (0.74, 0.7, 0.62), scale=3, rough=(0.8, 0.95), bump=0.08))
    P["plaster_ochre"] = get("P_plaster_ochre", lambda: E.mat_noisy("P_plaster_ochre", (0.45, 0.25, 0.1), (0.58, 0.36, 0.16), scale=3, rough=(0.8, 0.95), bump=0.08))
    P["stone"] = get("P_stone", lambda: E.mat_noisy("P_stone", (0.28, 0.27, 0.25), (0.45, 0.43, 0.4), scale=2.5, rough=(0.7, 0.95), bump=0.25))
    P["brick"] = get("P_brick", lambda: E.mat_noisy("P_brick", (0.28, 0.2, 0.15), (0.4, 0.3, 0.22), scale=5, rough=(0.8, 0.95), bump=0.2))
    P["dark"] = get("P_dark", lambda: E.mat_basic("P_dark", (0.01, 0.008, 0.007), rough=0.9))
    P["gold"] = get("P_gold", lambda: E.mat_gold("P_gold"))
    P["bronze"] = get("P_bronze", lambda: E.mat_gold("P_bronze", color=(0.45, 0.3, 0.14), rough=0.4))
    P["sail"] = get("P_sail", lambda: _mat_sail("P_sail", (0.42, 0.2, 0.08)))
    P["sail_light"] = get("P_sail_light", lambda: _mat_sail("P_sail_light", (0.62, 0.48, 0.3)))
    P["hull"] = get("P_hull", lambda: E.mat_wood("P_hull", c1=(0.12, 0.07, 0.035), c2=(0.26, 0.15, 0.07), scale=2.0, rough=0.6))
    P["rope"] = get("P_rope", lambda: E.mat_basic("P_rope", (0.2, 0.15, 0.09), rough=0.9))
    P["bark"] = get("P_bark", lambda: E.mat_noisy("P_bark", (0.06, 0.045, 0.035), (0.16, 0.12, 0.09), scale=14, rough=(0.8, 1.0), bump=0.5))
    P["pine"] = get("P_pine", lambda: E.mat_foliage("P_pine", c1=(0.012, 0.035, 0.018), c2=(0.04, 0.08, 0.03), scale=9, trans=0.15))
    P["leaf"] = get("P_leaf", lambda: E.mat_foliage("P_leaf", c1=(0.03, 0.08, 0.02), c2=(0.09, 0.16, 0.04), scale=7, trans=0.3))
    P["maple"] = get("P_maple", lambda: E.mat_foliage("P_maple", c1=(0.35, 0.03, 0.01), c2=(0.75, 0.2, 0.02), scale=7, trans=0.35))
    P["maple_gold"] = get("P_maple_gold", lambda: E.mat_foliage("P_maple_gold", c1=(0.45, 0.2, 0.02), c2=(0.8, 0.5, 0.05), scale=7, trans=0.35))
    P["willow"] = get("P_willow", lambda: E.mat_foliage("P_willow", c1=(0.1, 0.18, 0.03), c2=(0.22, 0.32, 0.06), scale=12, trans=0.4))
    P["lantern"] = get("P_lantern", lambda: E.mat_lantern("P_lantern"))
    P["window_glow"] = get("P_window_glow", lambda: E.mat_emit("P_window_glow", (1.0, 0.55, 0.2), 6.0))
    P["paper_win"] = get("P_paper_win", lambda: E.mat_basic("P_paper_win", (0.8, 0.72, 0.55), rough=0.9))
    return P


def _mat_sail(name, color):
    """Bamboo-battened matting sail: woven texture + translucency."""
    m, nb, bsdf, out = E.new_material(name)
    tc = nb.texcoord()
    sep = nb.sepxyz(tc.outputs["UV"])
    weave = nb.math("SINE", nb.math("MULTIPLY", sep.outputs[0], 900, loc=(-700, 300)), loc=(-600, 300))
    weave2 = nb.math("SINE", nb.math("MULTIPLY", sep.outputs[1], 900, loc=(-700, 150)), loc=(-600, 150))
    w = nb.math("MULTIPLY", weave, weave2, loc=(-500, 200))
    n = nb.noise(tc.outputs["UV"], scale=6.0, detail=5.0, loc=(-800, -100))
    stain = nb.ramp(n.outputs["Fac"], [(0.3, [c * 0.65 for c in color]), (0.75, [min(1, c * 1.2) for c in color])], loc=(-400, -100))
    E.principled(bsdf, color=stain.outputs[0], rough=0.85, normal=nb.bump(w, strength=0.25, distance=0.01))
    tr = nb.new("ShaderNodeBsdfTranslucent", (0, -300))
    nb.link(stain.outputs[0], tr.inputs["Color"])
    mixs = nb.new("ShaderNodeMixShader", (250, 0))
    mixs.inputs[0].default_value = 0.5
    nb.link(bsdf.outputs[0], mixs.inputs[1])
    nb.link(tr.outputs[0], mixs.inputs[2])
    nb.link(mixs.outputs[0], out.inputs["Surface"])
    return m


# ---------------------------------------------------------------------------
# Architecture
# ---------------------------------------------------------------------------

def octagon_prism(name, r, h, n=8, coll=None, mat=None, r_top=None):
    ob = E.cylinder(name, r=r, h=h, n=n, coll=coll, mat=mat, r2=r_top, smooth=False)
    ob.rotation_euler.z = pi / n
    return ob


def pagoda(name="pagoda", tiers=7, base_r=7.0, tier_h=6.0, taper=0.9, coll=None, P=None, sides=8, loc=(0, 0, 0), wall="plaster_ochre", doors=True):
    """Song-style octagonal pagoda. Returns an Empty parent."""
    P = P or palette()
    coll = coll or E.collection(name)
    root = bpy.data.objects.new(name, None)
    E.link(root, coll)
    root.location = loc
    parts = []
    z = 0.0
    # stepped stone platform
    for k, (rr, hh) in enumerate([(base_r * 1.9, 0.9), (base_r * 1.55, 0.9), (base_r * 1.3, 0.6)]):
        parts.append(octagon_prism(f"{name}_plat{k}", rr, hh, n=sides, coll=coll, mat=P["stone"]))
        parts[-1].location.z = z
        z += hh
    r = base_r
    h = tier_h * 1.25
    for t in range(tiers):
        # body
        body = octagon_prism(f"{name}_body{t}", r, h, n=sides, coll=coll, mat=P[wall], r_top=r * 0.97)
        body.location.z = z
        parts.append(body)
        # corner columns (red)
        for i in range(sides):
            a = 2 * pi * i / sides
            c = E.cylinder(f"{name}_col{t}_{i}", r=0.28 * r / base_r + 0.1, h=h, n=8, coll=coll, mat=P["red"])
            c.location = (r * 1.005 * cos(a), r * 1.005 * sin(a), z)
            parts.append(c)
        # doors on alternating faces
        if doors:
            for i in range(sides):
                if (i + t) % 2:
                    continue
                a = 2 * pi * (i + 0.5) / sides
                apo = r * cos(pi / sides)
                dw, dh = r * 0.42, h * 0.55
                d = E.box(f"{name}_door{t}_{i}", (dw, 0.3, dh), coll=coll, mat=P["dark"])
                d.location = (apo * 0.99 * cos(a), apo * 0.99 * sin(a), z + h * 0.12)
                d.rotation_euler.z = a + pi / 2
                parts.append(d)
        # beam band
        band = octagon_prism(f"{name}_band{t}", r * 1.06, 0.55, n=sides, coll=coll, mat=P["red"])
        band.location.z = z + h - 0.3
        parts.append(band)
        # bracket band (dougong impression)
        brk = octagon_prism(f"{name}_brk{t}", r * 1.14, 0.5, n=sides, coll=coll, mat=P["wood_dark"], r_top=r * 1.3)
        brk.location.z = z + h + 0.2
        parts.append(brk)
        # eave roof
        rh = r * 0.42
        roof = E.roof_hip(f"{name}_roof{t}", 0, 0, rh, overhang=r * 0.55, lift=r * 0.2, n_sides=sides, radius=r * 1.02,
                          coll=coll, mat=P["tiles"], underside_mat=P["wood_dark"], thickness=0.35, res=12)
        roof.location.z = z + h + 0.6
        parts.append(roof)
        for b in E.ridge_beams(f"{name}_rb{t}", 0, 0, rh, r * 0.55, r * 0.2, coll=coll, mat=P["tiles"], r=0.18, n_sides=sides, radius=r * 1.02):
            b.location.z = z + h + 0.6
            parts.append(b)
        # balcony ring above the roof (next tier base)
        z += h + 0.6 + rh * 0.55
        r *= taper
        h = tier_h * (0.96 ** (t + 1))
        if t < tiers - 1:
            rail = octagon_prism(f"{name}_rail{t}", r * 1.12, 0.6, n=sides, coll=coll, mat=P["red"])
            rail.location.z = z - 0.2
            parts.append(rail)
    # finial
    fin_z = z - rh * 0.4
    sp = E.lathe(f"{name}_finial", [(0.0, 0), (1.0, 0), (1.0, 0.6), (0.6, 0.9), (0.9, 1.4), (0.5, 1.8), (0.7, 2.3), (0.35, 2.7), (0.55, 3.2), (0.3, 3.6),
                                     (0.45, 4.1), (0.25, 4.5), (0.4, 5.2), (0.45, 5.6), (0.3, 6.0), (0.12, 6.4), (0.0, 6.5)], n=16, coll=coll, mat=P["bronze"])
    sp.location.z = fin_z
    parts.append(sp)
    for p in parts:
        p.parent = root
    return root


def house(name, w=8, d=6, h=3.2, roof_h=2.2, style="hip", coll=None, P=None, wall="plaster", roof="tiles", ridge=0.5, overhang=0.9, lift=0.35, loc=(0, 0, 0), rot=0.0, lit=False):
    """Simple vernacular house: plaster walls, timber posts, tiled roof."""
    P = P or palette()
    parts = []
    base = E.box(name + "_base", (w + 0.4, d + 0.4, 0.4), coll=coll, mat=P["stone"])
    parts.append(base)
    walls = E.box(name + "_walls", (w, d, h), loc=(0, 0, 0.4), coll=coll, mat=P[wall])
    parts.append(walls)
    # timber posts at corners & mid
    for x in (-w / 2, 0, w / 2):
        for y in (-d / 2, d / 2):
            parts.append(E.box(name + f"_post{x}{y}", (0.3, 0.3, h), loc=(x, y, 0.4), coll=coll, mat=P["wood_dark"]))
    # door/windows on front (-y)
    win_mat = P["window_glow"] if lit else P["dark"]
    parts.append(E.box(name + "_door", (w * 0.18, 0.12, h * 0.7), loc=(0, -d / 2 - 0.02, 0.4), coll=coll, mat=P["dark"]))
    for sx in (-1, 1):
        parts.append(E.box(name + f"_win{sx}", (w * 0.16, 0.12, h * 0.3), loc=(sx * w * 0.3, -d / 2 - 0.02, 0.4 + h * 0.4), coll=coll, mat=win_mat))
    parts.append(E.box(name + "_beam", (w + 0.3, d + 0.3, 0.3), loc=(0, 0, 0.4 + h), coll=coll, mat=P["wood_dark"]))
    rf = E.roof_hip(name + "_roof", w, d, roof_h, overhang=overhang, lift=lift, ridge_ratio=ridge, coll=coll, mat=P[roof], underside_mat=P["wood_dark"], thickness=0.15, res=10)
    rf.location.z = 0.4 + h + 0.25
    parts.append(rf)
    for b in E.ridge_beams(name + "_rb", w, d, roof_h, overhang, lift, ridge_ratio=ridge, coll=coll, mat=P[roof], r=0.1):
        b.location.z = 0.4 + h + 0.25
        parts.append(b)
    ob = E.join(parts, name)
    ob.location = loc
    ob.rotation_euler.z = rot
    return ob


def lantern(name, r=0.35, coll=None, P=None, loc=(0, 0, 0), light=True, energy=15.0, color=(1.0, 0.45, 0.15)):
    P = P or palette()
    body = E.lathe(name, [(0.0, -1.0 * r), (0.45 * r, -0.98 * r), (0.85 * r, -0.6 * r), (1.0 * r, 0), (0.85 * r, 0.6 * r), (0.45 * r, 0.98 * r), (0.0, 1.0 * r)], n=16, coll=coll, mat=P["lantern"])
    body.scale.z = 1.25
    body.location = loc
    if light:
        pl = E.point_light(name + "_L", loc, energy=energy, color=color, radius=r * 0.6, coll=coll)
        return body, pl
    return body, None


# ---------------------------------------------------------------------------
# Ships
# ---------------------------------------------------------------------------

def junk(name="junk", L=30.0, B=8.0, D=4.0, masts=3, coll=None, P=None, sail_mat="sail", furl=0.0, seed=1, eyes=True, loc=(0, 0, 0), rot=0.0, sail_scale=1.0, sail_angle=8.0):
    """
    Seagoing junk (Fujian 'fuchuan' type, cf. the 13th-c. Quanzhou wreck):
    V-bottomed keeled hull, strongly rising sheer to a high square stern,
    small raised bow transom, hanging sternpost rudder and fully battened
    lug sails. Length along +X (bow at +X). Returns an Empty parent.
    """
    P = P or palette()
    rnd = random.Random(seed)
    coll = coll or E.collection(name)
    root = bpy.data.objects.new(name, None)
    E.link(root, coll)
    parts = []
    nx, ns = 36, 12

    def half_beam(u):   # u: 0 stern -> 1 bow
        hb = B / 2 * (0.72 + 0.28 * sin(pi * min(1.0, u * 1.15)))
        return hb * (1 - 0.6 * E.smoothstep(0.62, 1.0, u))

    def sheer(u):
        return D * (1.0 + 1.25 * (1 - u) ** 3.5 + 0.55 * u ** 3.2)

    def keel(u):
        return D * 0.55 * (1 - (2 * u - 1) ** 8)

    verts, faces = [], []
    for i in range(nx + 1):
        u = i / nx
        x = -L / 2 + L * u
        hb = half_beam(u)
        top = sheer(u)
        bottom = -keel(u)
        for j in range(ns + 1):
            s = j / ns * 2 - 1
            a = abs(s)
            y = hb * (a ** 0.7) * (1 if s >= 0 else -1)
            z = bottom + (top - bottom) * (a ** 1.35)
            verts.append((x, y, z))
    w = ns + 1
    for i in range(nx):
        for j in range(ns):
            a = i * w + j
            faces.append((a, a + w, a + w + 1, a + 1))
    faces.append(tuple(range(0, w)))
    faces.append(tuple(reversed(range(nx * w, nx * w + w))))
    hull = E.obj_from_data(name + "_hull", verts, faces, coll, [P["hull"]], smooth=True)
    E._autosmooth(hull, 35)
    E.add_mod(hull, "SOLIDIFY", thickness=0.22, offset=1.0)
    parts.append(hull)
    # painted topside band (black/red) following the sheer
    band_mat = bpy.data.materials.get("P_hullband") or E.mat_noisy("P_hullband", (0.2, 0.025, 0.015), (0.3, 0.05, 0.03), scale=4, rough=(0.5, 0.7), bump=0.05)
    bv, bf = [], []
    for i in range(nx + 1):
        u = i / nx
        x = -L / 2 + L * u
        hb = half_beam(u) + 0.08
        top = sheer(u)
        for side in (-1, 1):
            bv += [(x, side * hb, top - 0.9), (x, side * hb, top + 0.05)]
    for i in range(nx):
        for k in (0, 2):
            a = i * 4 + k
            bf.append((a, a + 4, a + 5, a + 1))
    parts.append(E.obj_from_data(name + "_band", bv, bf, coll, band_mat))
    # stern transom panel (decorated)
    sv = [(-L / 2 - 0.05, y * half_beam(0) * 1.02, z) for (y, z) in ((-1, sheer(0) * 0.35), (1, sheer(0) * 0.35), (1, sheer(0) + 0.1), (-1, sheer(0) + 0.1))]
    parts.append(E.obj_from_data(name + "_transom", sv, [(0, 1, 2, 3)], coll, band_mat))
    # deck
    dverts, dfaces = [], []
    for i in range(nx + 1):
        u = i / nx
        x = -L / 2 + L * u
        hb = half_beam(u) * 0.97
        z = sheer(u) - 0.45
        dverts += [(x, -hb, z), (x, hb, z)]
    for i in range(nx):
        a = i * 2
        dfaces.append((a, a + 2, a + 3, a + 1))
    parts.append(E.obj_from_data(name + "_deck", dverts, dfaces, coll, P["wood_raw"]))
    # stern castle: two stacked cabins with a small tiled roof
    sc_len = L * 0.2
    cx = -L / 2 + sc_len / 2 + 0.6
    hb = half_beam(0.08) * 0.85
    cab = E.box(name + "_cabin", (sc_len, hb * 2, 2.2), loc=(cx, 0, sheer(0.09) - 0.5), coll=coll, mat=P["wood"])
    parts.append(cab)
    rf = E.roof_hip(name + "_cabroof", sc_len * 0.9, hb * 1.8, 1.1, overhang=0.45, lift=0.3, ridge_ratio=0.6, coll=coll, mat=P["tiles"], underside_mat=P["wood_dark"], thickness=0.1, res=6)
    rf.location = (cx, 0, sheer(0.09) + 1.75)
    parts.append(rf)
    # bulwark rails
    for side in (-1, 1):
        rv = []
        for i in range(nx + 1):
            u = i / nx
            rv.append((-L / 2 + L * u, side * half_beam(u) * 0.99, sheer(u) + 0.55))
        E._poly_curve(name + f"_rail{side}", rv, 0.07, coll, P["red"]).parent = root
    # hanging sternpost rudder
    rud = E.box(name + "_rudder", (2.2, 0.28, D * 1.9), loc=(-L / 2 - 1.1, 0, -keel(0.02) - D * 0.35), coll=coll, mat=P["wood_dark"])
    parts.append(rud)
    parts.append(E.cylinder(name + "_rudpost", r=0.25, h=D * 2.6, n=8, loc=(-L / 2 - 0.25, 0, -D * 0.4), coll=coll, mat=P["wood_dark"]))
    # bow oculi
    if eyes:
        eye_w = bpy.data.materials.get("P_eye_white") or E.mat_basic("P_eye_white", (0.8, 0.78, 0.7), rough=0.5)
        for side in (-1, 1):
            u = 0.9
            x = -L / 2 + L * u
            z = sheer(u) - 0.55
            e1 = E.sphere(name + f"_eye{side}", r=0.5, seg=16, rings=8, coll=coll, mat=eye_w, scale=(1, 0.25, 0.75))
            e1.location = (x, side * (half_beam(u) + 0.12), z)
            e2 = E.sphere(name + f"_pupil{side}", r=0.24, seg=12, rings=6, coll=coll, mat=P["dark"], scale=(1, 0.25, 1))
            e2.location = (x + 0.05, side * (half_beam(u) + 0.22), z)
            parts += [e1, e2]
    # masts & battened lug sails (main amidships, raked foremast, mizzen)
    all_masts = [(0.5, 1.0, 0.0), (0.82, 0.72, radians(-10)), (0.16, 0.5, radians(3)), (0.665, 0.86, radians(-4)), (0.33, 0.84, radians(2))]
    mast_specs = all_masts[:masts]
    for mi, (u, hs, rake) in enumerate(mast_specs):
        x = -L / 2 + L * u
        mh = L * 1.0 * hs * sail_scale
        mast = E.cylinder(name + f"_mast{mi}", r=0.34 * hs, h=mh, n=10, r2=0.18 * hs, coll=coll, mat=P["wood_dark"])
        mast.location = (x, 0, sheer(u) - 1.0)
        mast.rotation_euler.y = rake
        parts.append(mast)
        for so in battened_sail(name + f"_sail{mi}", width=L * 0.4 * hs * sail_scale, height=mh * 0.8, battens=10 if hs > 0.8 else 7,
                                coll=coll, P=P, mat=P[sail_mat], furl=furl, seed=seed + mi, billow=0.8 * hs):
            so.parent = mast
            so.location = (L * 0.02 * hs, 0.45, mh * 0.16)
            so.rotation_euler.z = radians(sail_angle + rnd.uniform(-3, 3))
    for p in parts:
        if p.parent is None:
            p.parent = root
    root.location = loc
    root.rotation_euler.z = rot
    return root


def battened_sail(name, width=12, height=18, battens=8, coll=None, P=None, mat=None, furl=0.0, seed=0, billow=1.0):
    """Fan-shaped lug sail: straight luff, curved leech, yard peaking aft, battens fanning out."""
    P = P or palette()
    nu, nv = 16, battens * 3
    eff_h = height * (1 - furl * 0.8)

    def point(u, v):
        fwd = width * 0.2
        aft = -width * (0.7 + 0.3 * v ** 0.7)
        x = fwd + (aft - fwd) * u
        z = eff_h * v + eff_h * 0.22 * (v ** 1.5) * u        # peak rises aft, battens fan
        panel = abs(sin(pi * (v * battens)))
        y = billow * (0.9 * sin(pi * u) + 0.22 * panel * sin(pi * u))
        return (x, y, z)

    verts, faces, uvs = [], [], []
    for j in range(nv + 1):
        v = j / nv
        for i in range(nu + 1):
            u = i / nu
            verts.append(point(u, v))
            uvs.append((u, v))
    w = nu + 1
    for j in range(nv):
        for i in range(nu):
            a = j * w + i
            faces.append((a, a + 1, a + w + 1, a + w))
    sail = E.obj_from_data(name, verts, faces, coll, mat, smooth=True, uvs=uvs)
    objs = [sail]
    for b in range(battens + 1):
        v = b / battens
        pts = []
        for i in range(9):
            u = i / 8
            x, y, z = point(u, v)
            pts.append((x * 1.03 + (0.25 if i == 0 else 0), y + 0.07, z))
        objs.append(E._poly_curve(name + f"_bat{b}", pts, 0.1, coll, P["wood_raw"]))
    # sheets (ropes) fanning from batten ends down to the deck
    for b in range(1, battens + 1, 2):
        x, y, z = point(1.0, b / battens)
        objs.append(E._poly_curve(name + f"_sheet{b}", [(x, y, z), (x * 0.85, 0.2, -eff_h * 0.18)], 0.025, coll, P["rope"]))
    return objs


def sampan(name, L=7.0, B=1.8, coll=None, P=None, loc=(0, 0, 0), rot=0.0, canopy=True):
    P = P or palette()
    parts = []
    nx, ns = 12, 6
    verts, faces = [], []
    for i in range(nx + 1):
        u = i / nx
        x = -L / 2 + L * u
        hb = B / 2 * (0.35 + 0.65 * sin(pi * u) ** 0.6)
        top = 0.5 + 0.35 * (abs(2 * u - 1) ** 3)
        for j in range(ns + 1):
            s = j / ns * 2 - 1
            verts.append((x, hb * s, -0.1 + (top + 0.1) * abs(s) ** 1.4))
    w = ns + 1
    for i in range(nx):
        for j in range(ns):
            a = i * w + j
            faces.append((a, a + w, a + w + 1, a + 1))
    hull = E.obj_from_data(name + "_hull", verts, faces, coll, P["hull"], smooth=True)
    E.add_mod(hull, "SOLIDIFY", thickness=0.06, offset=1.0)
    parts.append(hull)
    if canopy:
        cv, cf = [], []
        for i in range(9):
            a = pi * i / 8
            cv += [(-L * 0.18, B * 0.45 * cos(a), 0.45 + 0.9 * sin(a)), (L * 0.15, B * 0.45 * cos(a), 0.45 + 0.9 * sin(a))]
        for i in range(8):
            a = i * 2
            cf.append((a, a + 2, a + 3, a + 1))
        can = E.obj_from_data(name + "_canopy", cv, cf, coll, P["sail"], smooth=True)
        E.add_mod(can, "SOLIDIFY", thickness=0.04)
        parts.append(can)
    ob = E.join(parts, name)
    ob.location = loc
    ob.rotation_euler.z = rot
    return ob


# ---------------------------------------------------------------------------
# Vegetation
# ---------------------------------------------------------------------------

_cloud_tex = None


def _clouds(scale=0.6, name="T_clouds"):
    t = bpy.data.textures.get(name)
    if t is None:
        t = bpy.data.textures.new(name, "CLOUDS")
        t.noise_scale = scale
        t.noise_depth = 2
    return t


def foliage_blob(name, r=1.0, coll=None, mat=None, flat=0.45, seed=0, subdiv=3, disp=0.45):
    ob = E.ico(name, r=r, subdiv=subdiv, coll=coll, mat=mat)
    ob.scale = (1, 1, flat)
    md = ob.modifiers.new("disp", "DISPLACE")
    md.texture = _clouds(0.35 + 0.1 * (seed % 3), f"T_clouds{seed % 3}")
    md.strength = r * disp
    md.mid_level = 0.5
    md.texture_coords = "OBJECT"
    return ob


def pine(name, height=14.0, seed=0, coll=None, P=None, lean=0.25, pads=7, spread=1.0):
    """Painterly Chinese pine: crooked trunk, horizontal cloud-like foliage pads."""
    P = P or palette()
    rnd = random.Random(seed)
    parts = []
    # trunk polyline
    pts = []
    x = y = 0.0
    lean_dir = rnd.uniform(0, 2 * pi)
    for k in range(7):
        t = k / 6
        x += cos(lean_dir) * lean * height * 0.12 * (1 + rnd.uniform(-0.6, 0.6))
        y += sin(lean_dir) * lean * height * 0.12 * (1 + rnd.uniform(-0.6, 0.6))
        pts.append((x, y, height * t, 1.0 - 0.75 * t))
    trunk = E.bezier_tube(name + "_trunk", pts, height * 0.035, coll, P["bark"], res=6)
    parts.append(trunk)
    # branches + pads
    for b in range(pads):
        t = 0.45 + 0.55 * (b / max(1, pads - 1))
        base = Vector(pts[min(6, int(t * 6))][:3])
        ang = rnd.uniform(0, 2 * pi) if b < pads - 1 else lean_dir
        length = height * (0.42 - 0.25 * t) * spread * rnd.uniform(0.8, 1.2)
        tip = base + Vector((cos(ang) * length, sin(ang) * length, rnd.uniform(-0.05, 0.12) * height))
        mid = (base + tip) / 2 + Vector((0, 0, height * 0.04))
        br = E.bezier_tube(name + f"_br{b}", [tuple(base) + (1.0,), tuple(mid) + (0.7,), tuple(tip) + (0.4,)], height * 0.012, coll, P["bark"], res=4)
        parts.append(br)
        pr = height * (0.16 - 0.06 * t) * spread * rnd.uniform(0.8, 1.2)
        # each pad is a cluster of overlapping flattened blobs -> cloud-like, irregular outline
        for c in range(4):
            cr = pr * rnd.uniform(0.5, 0.85) * (1.0 if c == 0 else 0.8)
            off = Vector((rnd.uniform(-0.7, 0.7) * pr, rnd.uniform(-0.7, 0.7) * pr, rnd.uniform(-0.1, 0.2) * pr)) if c else Vector((0, 0, 0))
            pad = foliage_blob(name + f"_pad{b}_{c}", r=cr, coll=coll, mat=P["pine"], flat=rnd.uniform(0.3, 0.45), seed=seed + b * 5 + c, subdiv=3, disp=0.65)
            pad.location = tip + off + Vector((0, 0, pr * 0.15))
            pad.rotation_euler.z = rnd.uniform(0, 6.28)
            parts.append(pad)
    for c in range(3):
        cr = height * 0.1 * spread * rnd.uniform(0.7, 1.0)
        top = foliage_blob(name + f"_top{c}", r=cr, coll=coll, mat=P["pine"], flat=0.4, seed=seed + 99 + c, disp=0.65)
        top.location = Vector(pts[-1][:3]) + Vector((rnd.uniform(-0.5, 0.5) * cr, rnd.uniform(-0.5, 0.5) * cr, height * 0.03))
        parts.append(top)
    return E.join(parts, name)


def broadleaf(name, height=10.0, seed=0, coll=None, P=None, mat="leaf", blobs=9, crown=0.45, flat=0.75):
    P = P or palette()
    rnd = random.Random(seed)
    parts = []
    trunk_h = height * 0.45
    pts = [(0, 0, 0, 1.0), (rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), trunk_h * 0.5, 0.8), (rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6), trunk_h, 0.6)]
    parts.append(E.bezier_tube(name + "_trunk", pts, height * 0.035, coll, P["bark"], res=4))
    cx, cy, cz = pts[-1][:3]
    R = height * crown
    for b in range(blobs):
        a = rnd.uniform(0, 2 * pi)
        rr = rnd.uniform(0.2, 0.75) * R
        z = cz + rnd.uniform(0.1, 0.85) * height * 0.55
        br = R * rnd.uniform(0.45, 0.7)
        blob = foliage_blob(name + f"_b{b}", r=br, coll=coll, mat=P[mat], flat=flat, seed=seed * 7 + b, subdiv=3, disp=0.55)
        blob.location = (cx + cos(a) * rr, cy + sin(a) * rr, z)
        parts.append(blob)
    return E.join(parts, name)


def willow(name, height=9.0, seed=0, coll=None, P=None, strands=40):
    """Weeping willow: fuzzy layered crown + many thin drooping strands."""
    P = P or palette()
    rnd = random.Random(seed)
    parts = []
    trunk_h = height * 0.5
    pts = [(0, 0, 0, 1.0), (rnd.uniform(-0.5, 0.5), rnd.uniform(-0.5, 0.5), trunk_h * 0.6, 0.8), (rnd.uniform(-0.8, 0.8), rnd.uniform(-0.8, 0.8), trunk_h, 0.6)]
    parts.append(E.bezier_tube(name + "_trunk", pts, height * 0.04, coll, P["bark"], res=4))
    cx, cy, cz = pts[-1][:3]
    for k in range(5):
        a = rnd.uniform(0, 2 * pi)
        rr = rnd.uniform(0.0, 0.2) * height
        cr = height * rnd.uniform(0.18, 0.26)
        crown = foliage_blob(name + f"_crown{k}", r=cr, coll=coll, mat=P["willow"], flat=0.55, seed=seed * 5 + k, disp=0.6)
        crown.location = (cx + cos(a) * rr, cy + sin(a) * rr, cz + height * rnd.uniform(0.12, 0.25))
        parts.append(crown)
    for s in range(strands * 2):
        a = rnd.uniform(0, 2 * pi)
        r0 = rnd.uniform(0.25, 1.0) * height * 0.32
        x0, y0 = cx + cos(a) * r0, cy + sin(a) * r0
        z0 = cz + height * rnd.uniform(0.1, 0.3)
        L = height * rnd.uniform(0.3, 0.62)
        out = rnd.uniform(0.2, 0.6)
        p = [(x0, y0, z0, 1.0), (x0 + cos(a) * out, y0 + sin(a) * out, z0 - L * 0.45, 0.7), (x0 + cos(a) * out * 1.2, y0 + sin(a) * out * 1.2, z0 - L, 0.2)]
        parts.append(E.bezier_tube(name + f"_s{s}", p, height * 0.006, coll, P["willow"], res=3))
    return E.join(parts, name)


def bamboo_clump(name, height=8.0, stalks=14, seed=0, coll=None, P=None, radius=1.2):
    P = P or palette()
    rnd = random.Random(seed)
    stalk_mat = bpy.data.materials.get("P_bamboo") or E.mat_noisy("P_bamboo", (0.22, 0.3, 0.08), (0.35, 0.42, 0.12), scale=30, rough=(0.4, 0.6), bump=0.05)
    parts = []
    for s in range(stalks):
        a = rnd.uniform(0, 2 * pi)
        rr = rnd.uniform(0, radius)
        h = height * rnd.uniform(0.7, 1.1)
        lean = rnd.uniform(0.02, 0.12)
        st = E.cylinder(name + f"_st{s}", r=0.06, h=h, n=6, coll=coll, mat=stalk_mat, smooth=False)
        st.location = (cos(a) * rr, sin(a) * rr, 0)
        st.rotation_euler = (lean * cos(a + 1.3), lean * sin(a + 1.3), 0)
        parts.append(st)
        for k in range(3):
            fb = foliage_blob(name + f"_f{s}{k}", r=h * 0.12, coll=coll, mat=P["leaf"], flat=0.5, seed=seed + s * 3 + k)
            fz = h * (0.6 + 0.15 * k)
            fb.location = (cos(a) * rr + lean * fz * sin(a + 1.3) * 0, sin(a) * rr, fz)
            parts.append(fb)
    return E.join(parts, name)


# ---------------------------------------------------------------------------
# People (tiny stylized figures for scale)
# ---------------------------------------------------------------------------

def person(name, coll=None, color=(0.2, 0.25, 0.35), hat="cap", seated=False, scale=1.0, seed=0, loc=(0, 0, 0), rot=0.0):
    rnd = random.Random(seed)
    mat = bpy.data.materials.get(f"P_robe_{color}") or E.mat_basic(f"P_robe_{color}", color, rough=0.8)
    skin = bpy.data.materials.get("P_skin") or E.mat_basic("P_skin", (0.55, 0.36, 0.25), rough=0.6, sss=0.2)
    dark = bpy.data.materials.get("P_dark") or E.mat_basic("P_dark", (0.01, 0.01, 0.01))
    parts = []
    if seated:
        robe = E.cylinder(name + "_robe", r=0.32, h=0.75, n=10, r2=0.17, coll=coll, mat=mat)
        head_z = 0.9
    else:
        robe = E.cylinder(name + "_robe", r=0.26, h=1.45, n=10, r2=0.16, coll=coll, mat=mat)
        head_z = 1.58
    parts.append(robe)
    head = E.sphere(name + "_head", r=0.11, seg=10, rings=6, coll=coll, mat=skin)
    head.location.z = head_z
    parts.append(head)
    if hat == "cap":
        h = E.cylinder(name + "_hat", r=0.1, h=0.12, n=8, coll=coll, mat=dark)
        h.location.z = head_z + 0.05
        parts.append(h)
    elif hat == "cone":
        straw = bpy.data.materials.get("P_straw") or E.mat_noisy("P_straw", (0.45, 0.35, 0.18), (0.6, 0.5, 0.3), scale=40)
        h = E.cylinder(name + "_hat", r=0.3, h=0.18, n=12, r2=0.0, coll=coll, mat=straw)
        h.location.z = head_z + 0.03
        parts.append(h)
    elif hat == "scholar":
        h = E.box(name + "_hat", (0.2, 0.2, 0.16), coll=coll, mat=dark)
        h.location.z = head_z + 0.06
        wing = E.box(name + "_wing", (0.7, 0.04, 0.03), coll=coll, mat=dark)
        wing.location.z = head_z + 0.12
        parts += [h, wing]
    elif hat == "monk":
        pass
    ob = E.join(parts, name)
    ob.location = loc
    ob.rotation_euler.z = rot
    ob.scale = (scale, scale, scale)
    return ob


def rock(name, r=2.0, seed=0, coll=None, P=None, flat=0.7, loc=(0, 0, 0), mat=None):
    """Weathered boulder: displaced icosphere with a flattened base."""
    P = P or palette()
    ob = E.ico(name, r=r, subdiv=4, coll=coll, mat=mat or P["stone"], smooth=True)
    ob.scale = (1.0, random.Random(seed).uniform(0.7, 1.0), flat)
    t = bpy.data.textures.get(f"T_rock{seed % 4}")
    if t is None:
        t = bpy.data.textures.new(f"T_rock{seed % 4}", "VORONOI")
        t.noise_scale = 0.6 + 0.15 * (seed % 4)
        t.distance_metric = "DISTANCE"
    md = ob.modifiers.new("disp", "DISPLACE")
    md.texture = t
    md.strength = r * 0.45
    md.mid_level = 0.6
    md.texture_coords = "OBJECT"
    t2 = _clouds(0.25, f"T_rockc{seed % 3}")
    md2 = ob.modifiers.new("disp2", "DISPLACE")
    md2.texture = t2
    md2.strength = r * 0.2
    md2.texture_coords = "OBJECT"
    ob.location = loc
    ob.rotation_euler.z = random.Random(seed).uniform(0, 6.28)
    return ob


def conifer(name, height=16.0, seed=0, coll=None, P=None, mat="pine", layers=8, width=0.32):
    """Japanese cedar / cypress: one tall noisy foliage cone (fuzzy edges) on a trunk."""
    P = P or palette()
    rnd = random.Random(seed)
    parts = [E.cylinder(name + "_trunk", r=height * 0.018, h=height * 0.35, n=8, r2=height * 0.012, coll=coll, mat=P["bark"])]
    R = height * width
    prof = [(0.0, height * 0.18)]
    for k in range(1, 12):
        t = k / 11
        r = R * (1 - t) ** 0.85 * (1.0 + 0.08 * sin(t * 9 + seed))
        prof.append((max(r, 0.02), height * (0.18 + 0.82 * t)))
    prof.append((0.0, height * 1.01))
    cone = E.lathe(name + "_crown", prof, n=16, coll=coll, mat=P[mat])
    md = cone.modifiers.new("sub", "SUBSURF")
    md.levels = 2
    md.render_levels = 2
    d = cone.modifiers.new("disp", "DISPLACE")
    d.texture = _clouds(0.22 + 0.04 * (seed % 3), f"T_clouds_c{seed % 3}")
    d.strength = R * 0.55
    d.mid_level = 0.5
    d.texture_coords = "OBJECT"
    cone.rotation_euler.z = rnd.uniform(0, 6.28)
    parts.append(cone)
    return E.join(parts, name)

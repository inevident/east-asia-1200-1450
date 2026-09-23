"""
mini — low-poly, vertex-coloured miniatures for the 3D map tour.

Everything is built into one bmesh per landmark (a `Mini`), with colours stored in a
face-corner colour attribute "Col" (linear floats), so each landmark exports to glTF as
a single mesh and draws in one or two calls. Coordinates: x east, y north, z up, in map
units (1 = 10 km). Buildings are wildly exaggerated so they read at map scale.
"""
import math
import random
from math import sin, cos, pi

import bmesh
import bpy
from mathutils import Matrix, Vector


# ---------------------------------------------------------------------------------- colour
def lin(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple((v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) for v in c) + (1.0,)


def shade(c, k):
    return (min(c[0] * k, 1), min(c[1] * k, 1), min(c[2] * k, 1), 1.0)


def mix(a, b, t):
    return tuple(a[i] * (1 - t) + b[i] * t for i in range(3)) + (1.0,)


PAL = {k: lin(v) for k, v in {
    "roof": "#5d646a", "roof_dark": "#484e54", "roof_house": "#7a8083", "roof_house2": "#6c7378", "roof_green": "#3f7a62", "roof_yellow": "#d29b2f", "roof_brown": "#6b4b37",
    "roof_thatch": "#b39d6c", "roof_blue": "#35679a", "ridge": "#2e3236",
    "red": "#a63a2c", "red_dark": "#7e2a20", "white": "#ece6d8", "ochre": "#d6c19a", "plaster": "#e2d6bd",
    "wood": "#7a5236", "wood_dark": "#4d3322", "wood_light": "#a57b52",
    "stone": "#b5ad9a", "stone_dark": "#8c8574", "stone_light": "#cfc8b5", "brick": "#9b6a4f", "brick_grey": "#8b8a84",
    "earth": "#b9a179", "earth_dark": "#9a8460", "court": "#d8caa7", "road": "#c9b58e",
    "gold": "#d9ab3c", "gold_dark": "#b48624", "bronze": "#6f8b77", "stupa": "#f3efe4",
    "felt": "#efe7d4", "felt_trim": "#8b3b2b",
    "sail": "#b9784a", "sail_mat": "#cfae7e", "sail_white": "#efe9dc", "hull": "#6d4b31", "hull_dark": "#4a3322", "hull_red": "#8e3b2a",
    "water": "#6d9ea6", "pond": "#79a8a8", "paddy_water": "#a3c3b8", "paddy": "#8fb56f", "rice": "#cfbb68", "bund": "#9aa96a",
    "tree": "#4f7f4b", "tree_dark": "#3a6340", "tree_light": "#6f9a57", "pine": "#355a41", "trunk": "#5a4130", "blossom": "#e7c3c9",
    "turquoise": "#3f9d99", "tile_blue": "#2f6fa0", "cham": "#a5593b", "smoke": "#dcd6cc", "fire": "#ff9a3c",
    "black": "#2a2622", "cobalt": "#2c4f93", "sand": "#dccb9c", "grass": "#9db47a", "dirt": "#a88f6a",
}.items()}


# ---------------------------------------------------------------------------------- builder
class Mini:
    """Accumulates geometry with per-face colours; `mat` picks a material slot (0 base, 1 glow, 2 water, 3 gold)."""

    def __init__(self):
        self.bm = bmesh.new()
        self.cl = self.bm.loops.layers.float_color.new("Col")

    # -- low level
    def face(self, pts, color, mat=0):
        vs = [self.bm.verts.new(p) for p in pts]
        f = self.bm.faces.new(vs)
        f.material_index = mat
        for l in f.loops:
            l[self.cl] = color
        return f

    def mesh(self, verts, faces, color, M=None, mat=0, colors=None):
        """verts: list of (x,y,z); faces: index lists. `colors` optionally gives one colour per face."""
        vs = [self.bm.verts.new((M @ Vector(v)) if M else v) for v in verts]
        out = []
        for i, f in enumerate(faces):
            try:
                ff = self.bm.faces.new([vs[j] for j in f])
            except ValueError:
                continue
            ff.material_index = mat
            c = colors[i] if colors else color
            for l in ff.loops:
                l[self.cl] = c
            out.append(ff)
        return out

    @staticmethod
    def M(x=0.0, y=0.0, z=0.0, rot=0.0, s=1.0):
        return Matrix.Translation((x, y, z)) @ Matrix.Rotation(rot, 4, "Z") @ Matrix.Diagonal((s, s, s, 1))

    # -- primitives
    def box(self, x, y, z, sx, sy, sz, color, rot=0.0, top=None, taper=1.0, mat=0, bottom=False, M=None):
        """Box standing on z (centre x,y). `taper` scales the top face; `top` colours it differently."""
        hx, hy = sx / 2, sy / 2
        tx, ty = hx * taper, hy * taper
        v = [(-hx, -hy, 0), (hx, -hy, 0), (hx, hy, 0), (-hx, hy, 0), (-tx, -ty, sz), (tx, -ty, sz), (tx, ty, sz), (-tx, ty, sz)]
        f = [[0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7], [4, 5, 6, 7]]
        cols = [shade(color, 0.92), shade(color, 1.0), shade(color, 0.92), shade(color, 0.86), top or shade(color, 1.06)]
        if bottom:
            f.append([3, 2, 1, 0])
            cols.append(color)
        return self.mesh(v, f, color, (M or Matrix.Identity(4)) @ self.M(x, y, z, rot), mat, cols)

    def prism(self, x, y, z, r, h, n, color, r2=None, rot=0.0, top=None, mat=0, M=None, cap=True):
        r2 = r if r2 is None else r2
        v = []
        for k in range(n):
            a = rot + 2 * pi * k / n
            v.append((r * cos(a), r * sin(a), 0))
        for k in range(n):
            a = rot + 2 * pi * k / n
            v.append((r2 * cos(a), r2 * sin(a), h))
        f = [[k, (k + 1) % n, n + (k + 1) % n, n + k] for k in range(n)]
        cols = [shade(color, 0.86 + 0.14 * abs(cos(rot + 2 * pi * (k + 0.5) / n - 0.8))) for k in range(n)]
        if cap and r2 > 1e-6:
            f.append(list(range(n, 2 * n)))
            cols.append(top or shade(color, 1.05))
        return self.mesh(v, f, color, (M or Matrix.Identity(4)) @ self.M(x, y, z), mat, cols)

    def lathe(self, x, y, z, prof, n, color, mat=0, colors=None, M=None, close_top=True):
        """Surface of revolution from a profile [(r, z), ...] (bottom to top)."""
        v, f, cols = [], [], []
        m = len(prof)
        for (r, h) in prof:
            for k in range(n):
                a = 2 * pi * k / n
                v.append((r * cos(a), r * sin(a), h))
        for j in range(m - 1):
            for k in range(n):
                a, b = j * n + k, j * n + (k + 1) % n
                if prof[j][0] < 1e-6 and prof[j + 1][0] < 1e-6:
                    continue
                f.append([a, b, b + n, a + n])
                c = colors[j] if colors else color
                cols.append(shade(c, 0.88 + 0.14 * abs(cos(2 * pi * (k + 0.5) / n - 0.8))))
        if close_top and prof[-1][0] > 1e-6:
            f.append([(m - 1) * n + k for k in range(n)])
            cols.append(colors[-1] if colors else color)
        return self.mesh(v, f, color, (M or Matrix.Identity(4)) @ self.M(x, y, z), mat, cols)

    def sphere(self, x, y, z, r, color, n=8, rings=5, sz=1.0, mat=0, jitter=0.0, seed=0, M=None):
        rnd = random.Random(seed)
        prof = []
        for i in range(rings + 1):
            t = -pi / 2 + pi * i / rings
            rr = r * cos(t) * (1 + (rnd.uniform(-jitter, jitter) if 0 < i < rings else 0))
            prof.append((max(rr, 0.0), r * sz * (sin(t) + 1)))
        return self.lathe(x, y, z - 0.0, prof, n, color, mat, M=M, close_top=False)

    def slab(self, pts, z, color, mat=0, thick=0.0):
        """Flat polygon (ground patches: courtyards, ponds, fields) at height z."""
        v = [(p[0], p[1], z) for p in pts]
        self.mesh(v, [list(range(len(pts)))], color, mat=mat)
        if thick > 0:
            n = len(pts)
            v2 = v + [(p[0], p[1], z - thick) for p in pts]
            self.mesh(v2, [[k, k + n, (k + 1) % n + n, (k + 1) % n] for k in range(n)], shade(color, 0.8), mat=mat)

    # -- Chinese roofs: concave slopes rising to a ridge, eave corners swept up
    def roof(self, x, y, z, w, d, h, color, rot=0.0, over=0.18, lift=None, ridge=None, nu=4, nv=3, ridge_color=None, M=None):
        """Hip roof over a w x d footprint (x along w). `ridge` = ridge length fraction of w (default from proportions)."""
        lift = h * 0.35 if lift is None else lift
        W, D = w / 2 + over, d / 2 + over
        rl = max(0.0, (W - D)) if ridge is None else ridge * W
        outer = [(-W, -D), (W, -D), (W, D), (-W, D)]
        inner = [(-rl, 0), (rl, 0), (rl, 0), (-rl, 0)]
        verts, faces, cols = [], [], []
        for s in range(4):
            o0, o1 = outer[s], outer[(s + 1) % 4]
            i0, i1 = inner[s], inner[(s + 1) % 4]
            base = len(verts)
            for j in range(nv + 1):
                t = j / nv
                for k in range(nu + 1):
                    u = k / nu
                    ox, oy = o0[0] + (o1[0] - o0[0]) * u, o0[1] + (o1[1] - o0[1]) * u
                    ix, iy = i0[0] + (i1[0] - i0[0]) * u, i0[1] + (i1[1] - i0[1]) * u
                    px, py = ox + (ix - ox) * t, oy + (iy - oy) * t
                    pz = h * t ** 1.45 + lift * (2 * abs(u - 0.5)) ** 3 * (1 - t) ** 2
                    verts.append((px, py, pz))
            for j in range(nv):
                for k in range(nu):
                    a = base + j * (nu + 1) + k
                    faces.append([a, a + 1, a + nu + 2, a + nu + 1])
                    cols.append(shade(color, (0.8, 1.0, 0.9, 0.72)[s] * (0.94 + 0.08 * j / nv)))
        self.mesh(verts, faces, color, (M or Matrix.Identity(4)) @ self.M(x, y, z, rot), 0, cols)
        # underside, so low views never see through the eaves
        self.mesh([(-W, -D, 0), (W, -D, 0), (W, D, 0), (-W, D, 0)], [[3, 2, 1, 0]], shade(color, 0.55), (M or Matrix.Identity(4)) @ self.M(x, y, z, rot))
        if rl > 0 and ridge_color is not False:
            rc = ridge_color or PAL["ridge"]
            self.box(0, 0, h - 0.01, 2 * rl + h * 0.25, h * 0.12, h * 0.1, rc, M=(M or Matrix.Identity(4)) @ self.M(x, y, z, rot))

    def roof_poly(self, x, y, z, r, h, n, color, rot=0.0, lift=None, nv=3, M=None):
        """Pyramidal roof on an n-gon (pagoda eaves, pavilions) with swept-up corners."""
        lift = h * 0.4 if lift is None else lift
        verts, faces, cols = [], [], []
        for s in range(n):
            a0 = rot + 2 * pi * s / n
            a1 = rot + 2 * pi * (s + 1) / n
            base = len(verts)
            for j in range(nv + 1):
                t = j / nv
                for k in range(3):
                    u = k / 2
                    rr = r * (1 - t)
                    px, py = (cos(a0) * (1 - u) + cos(a1) * u) * rr, (sin(a0) * (1 - u) + sin(a1) * u) * rr
                    pz = h * t ** 1.4 + lift * (2 * abs(u - 0.5)) ** 3 * (1 - t) ** 2
                    verts.append((px, py, pz))
            for j in range(nv):
                for k in range(2):
                    a = base + j * 3 + k
                    faces.append([a, a + 1, a + 4, a + 3])
                    cols.append(shade(color, 0.78 + 0.22 * abs(cos((a0 + a1) / 2 - 0.8))))
        self.mesh(verts, faces, color, (M or Matrix.Identity(4)) @ self.M(x, y, z), 0, cols)
        under = [(cos(rot + 2 * pi * s / n) * r, sin(rot + 2 * pi * s / n) * r, 0) for s in range(n)]
        self.mesh(under, [list(range(n))[::-1]], shade(color, 0.5), (M or Matrix.Identity(4)) @ self.M(x, y, z))

    # -- output
    def to_object(self, name, coll, mats):
        me = bpy.data.meshes.new(name)
        self.bm.normal_update()
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        self.bm.to_mesh(me)
        self.bm.free()
        me.color_attributes.active_color_name = "Col"
        me.color_attributes.render_color_index = me.color_attributes.find("Col")
        for m in mats:
            me.materials.append(m)
        ob = bpy.data.objects.new(name, me)
        coll.objects.link(ob)
        for p in me.polygons:
            p.use_smooth = False
        return ob


# ---------------------------------------------------------------------------------- materials
def materials():
    """Base (vertex colour), glow (fire, lanterns), water (glossy), gold (metallic leaf)."""
    out = []
    for name, rough, metal, emit in (("mini", 0.85, 0.0, 0.0), ("mini_glow", 0.6, 0.0, 3.0), ("mini_water", 0.18, 0.0, 0.0), ("mini_gold", 0.32, 0.85, 0.0)):
        m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.clear()
        outn = nt.nodes.new("ShaderNodeOutputMaterial")
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        attr = nt.nodes.new("ShaderNodeVertexColor")
        attr.layer_name = "Col"
        nt.links.new(attr.outputs["Color"], bsdf.inputs["Base Color"])
        nt.links.new(bsdf.outputs["BSDF"], outn.inputs["Surface"])
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
        if emit:
            nt.links.new(attr.outputs["Color"], bsdf.inputs["Emission Color"])
            bsdf.inputs["Emission Strength"].default_value = emit
        m.use_backface_culling = False
        out.append(m)
    return out

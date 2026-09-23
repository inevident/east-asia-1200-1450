"""
ealib — procedural toolkit for the "East Asia 1200–1450" Blender scenes.

Everything here builds geometry/materials from code so each scene script is
reproducible: run the scene script inside Blender and it rebuilds from scratch.
Targets Blender 5.2 (Cycles on Metal).
"""
import bpy
import bmesh
import math
import random
from math import sin, cos, pi, radians
from mathutils import Vector, Matrix, Euler, noise

ROOT = "/Applications/Personal App/AP-WORLD-WEBSITE"
RENDER_DIR = ROOT + "/blender/renders"
TEX_DIR = ROOT + "/blender/textures"

_ASSET = "/System/Library/AssetsV2/PreinstalledAssetsV2/InstallWithOs/com_apple_MobileAsset_Font7/"
FONT_KAI = _ASSET + "66746e61b4dbfa104b24e08fd5cdadcea3816e57.asset/AssetData/BiauKai.ttf"
FONT_SONG = _ASSET + "1f3a029445fcd5c04cb253da881d93774c566101.asset/AssetData/LiSongPro.ttf"


# ---------------------------------------------------------------------------
# Scene / render setup
# ---------------------------------------------------------------------------

def new_scene(name, res=(2560, 1440), samples=256, look="AgX - Medium High Contrast"):
    """Create (or wipe and reuse) a scene and make it the active one."""
    scn = bpy.data.scenes.get(name)
    if scn is None:
        scn = bpy.data.scenes.new(name)
    else:
        for o in list(scn.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        for c in list(scn.collection.children):
            _remove_collection(c)
    bpy.context.window.scene = scn

    r = scn.render
    r.engine = "CYCLES"
    r.resolution_x, r.resolution_y = res
    r.resolution_percentage = 100
    r.film_transparent = False
    r.use_persistent_data = True

    c = scn.cycles
    c.device = "GPU"
    c.samples = samples
    c.preview_samples = 32
    c.use_adaptive_sampling = True
    c.adaptive_threshold = 0.015
    c.use_denoising = True
    c.denoiser = "OPENIMAGEDENOISE"
    try:
        c.denoising_use_gpu = True
    except Exception:
        pass
    c.max_bounces = 8
    c.diffuse_bounces = 3
    c.glossy_bounces = 3
    c.transmission_bounces = 6
    c.volume_bounces = 1
    c.transparent_max_bounces = 12
    c.caustics_reflective = False
    c.caustics_refractive = False
    c.blur_glossy = 1.0
    c.sample_clamp_indirect = 8.0

    vs = scn.view_settings
    vs.view_transform = "AgX"
    try:
        vs.look = look
    except Exception:
        vs.look = "None"
    vs.exposure = 0.0
    vs.gamma = 1.0

    w = bpy.data.worlds.get(name + "_World") or bpy.data.worlds.new(name + "_World")
    scn.world = w
    _use_nodes(w)
    w.node_tree.nodes.clear()
    return scn


def _use_nodes(idblock):
    try:
        idblock.use_nodes = True
    except Exception:
        pass


def _remove_collection(coll):
    for ch in list(coll.children):
        _remove_collection(ch)
    for o in list(coll.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.collections.remove(coll)


def purge():
    try:
        bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
    except Exception:
        pass


def collection(name, parent=None):
    scn = bpy.context.window.scene
    parent = parent or scn.collection
    c = bpy.data.collections.new(name)
    parent.children.link(c)
    return c


def link(obj, coll=None):
    coll = coll or bpy.context.window.scene.collection
    coll.objects.link(obj)
    return obj


# ---------------------------------------------------------------------------
# Node helpers
# ---------------------------------------------------------------------------

class Nodes:
    """Tiny helper for building shader node trees in code."""

    def __init__(self, tree):
        self.tree = tree
        self.nodes = tree.nodes
        self.links = tree.links

    def new(self, kind, loc=(0, 0), **inputs):
        n = self.nodes.new(kind)
        n.location = loc
        for k, v in inputs.items():
            self.set(n, k, v)
        return n

    def set(self, node, key, value):
        # attribute first (e.g. blend_type, noise_type), then socket input
        if hasattr(node, key) and key not in node.inputs.keys():
            setattr(node, key, value)
            return
        sock = node.inputs.get(key)
        if sock is None:
            raise KeyError(f"{node.bl_idname} has no input/attr {key!r}: {[i.name for i in node.inputs]}")
        if isinstance(value, bpy.types.NodeSocket):
            self.links.new(value, sock)
        else:
            sock.default_value = value

    def link(self, a, b):
        self.links.new(a, b)

    # common building blocks ------------------------------------------------
    def texcoord(self, loc=(-1200, 0)):
        return self.new("ShaderNodeTexCoord", loc)

    def mapping(self, vector, scale=(1, 1, 1), loc=(-1000, 0), rot=(0, 0, 0), offset=(0, 0, 0)):
        m = self.new("ShaderNodeMapping", loc)
        self.link(vector, m.inputs["Vector"])
        m.inputs["Scale"].default_value = scale
        m.inputs["Rotation"].default_value = rot
        m.inputs["Location"].default_value = offset
        return m

    def noise(self, vector=None, scale=5.0, detail=4.0, rough=0.5, distortion=0.0, loc=(-800, 0), dims="3D", ntype="FBM", lac=2.0):
        n = self.new("ShaderNodeTexNoise", loc)
        n.noise_dimensions = dims
        try:
            n.noise_type = ntype
        except Exception:
            pass
        if vector is not None:
            self.link(vector, n.inputs["Vector"])
        n.inputs["Scale"].default_value = scale
        n.inputs["Detail"].default_value = detail
        n.inputs["Roughness"].default_value = rough
        n.inputs["Distortion"].default_value = distortion
        if "Lacunarity" in n.inputs:
            n.inputs["Lacunarity"].default_value = lac
        return n

    def voronoi(self, vector=None, scale=5.0, loc=(-800, 0), feature="F1", dist="EUCLIDEAN", rand=1.0):
        n = self.new("ShaderNodeTexVoronoi", loc)
        n.feature = feature
        n.distance = dist
        if vector is not None:
            self.link(vector, n.inputs["Vector"])
        n.inputs["Scale"].default_value = scale
        n.inputs["Randomness"].default_value = rand
        return n

    def wave(self, vector=None, scale=5.0, distortion=0.0, detail=2.0, loc=(-800, 0), wtype="BANDS", direction="X", profile="SIN"):
        n = self.new("ShaderNodeTexWave", loc)
        n.wave_type = wtype
        if wtype == "BANDS":
            n.bands_direction = direction
        else:
            n.rings_direction = direction
        n.wave_profile = profile
        if vector is not None:
            self.link(vector, n.inputs["Vector"])
        n.inputs["Scale"].default_value = scale
        n.inputs["Distortion"].default_value = distortion
        n.inputs["Detail"].default_value = detail
        return n

    def ramp(self, fac, stops, loc=(-500, 0), interp="LINEAR"):
        """stops = [(pos, (r,g,b,a)), ...]"""
        n = self.new("ShaderNodeValToRGB", loc)
        cr = n.color_ramp
        cr.interpolation = interp
        while len(cr.elements) > 1:
            cr.elements.remove(cr.elements[-1])
        cr.elements[0].position = stops[0][0]
        cr.elements[0].color = _rgba(stops[0][1])
        for pos, col in stops[1:]:
            e = cr.elements.new(pos)
            e.color = _rgba(col)
        self.link(fac, n.inputs["Fac"])
        return n

    def math(self, op, a, b=None, loc=(-400, 0), clamp=False):
        n = self.new("ShaderNodeMath", loc)
        n.operation = op
        n.use_clamp = clamp
        if isinstance(a, bpy.types.NodeSocket):
            self.link(a, n.inputs[0])
        else:
            n.inputs[0].default_value = a
        if b is not None:
            if isinstance(b, bpy.types.NodeSocket):
                self.link(b, n.inputs[1])
            else:
                n.inputs[1].default_value = b
        return n.outputs[0]

    def maprange(self, value, fmin, fmax, tmin=0.0, tmax=1.0, loc=(-400, 0), clamp=True, interp="LINEAR"):
        n = self.new("ShaderNodeMapRange", loc)
        n.interpolation_type = interp
        n.clamp = clamp
        self.link(value, n.inputs["Value"])
        n.inputs["From Min"].default_value = fmin
        n.inputs["From Max"].default_value = fmax
        n.inputs["To Min"].default_value = tmin
        n.inputs["To Max"].default_value = tmax
        return n.outputs["Result"]

    def mix(self, fac, a, b, blend="MIX", loc=(-300, 0)):
        n = self.new("ShaderNodeMix", loc)
        n.data_type = "RGBA"
        n.blend_type = blend
        _plug(self, n.inputs["Factor"], fac)
        _plug(self, n.inputs[6], a)  # A (color)
        _plug(self, n.inputs[7], b)  # B (color)
        return n.outputs[2]

    def bump(self, height, strength=0.3, distance=0.1, normal=None, loc=(-200, -400)):
        n = self.new("ShaderNodeBump", loc)
        n.inputs["Strength"].default_value = strength
        n.inputs["Distance"].default_value = distance
        self.link(height, n.inputs["Height"])
        if normal is not None:
            self.link(normal, n.inputs["Normal"])
        return n.outputs["Normal"]

    def sepxyz(self, vector, loc=(-900, 200)):
        n = self.new("ShaderNodeSeparateXYZ", loc)
        self.link(vector, n.inputs[0])
        return n


def _plug(nb, sock, v):
    if isinstance(v, bpy.types.NodeSocket):
        nb.link(v, sock)
    else:
        sock.default_value = _rgba(v) if (isinstance(v, (tuple, list)) and len(v) in (3, 4) and sock.type == "RGBA") else v


def _rgba(c):
    c = tuple(c)
    return c if len(c) == 4 else c + (1.0,)


def new_material(name):
    m = bpy.data.materials.get(name)
    if m is not None:
        bpy.data.materials.remove(m)
    m = bpy.data.materials.new(name)
    _use_nodes(m)
    nt = m.node_tree
    nt.nodes.clear()
    nb = Nodes(nt)
    out = nb.new("ShaderNodeOutputMaterial", (400, 0))
    bsdf = nb.new("ShaderNodeBsdfPrincipled", (0, 0))
    nb.link(bsdf.outputs[0], out.inputs["Surface"])
    return m, nb, bsdf, out


def principled(bsdf, **kw):
    """Set Principled BSDF inputs with friendly names."""
    names = {
        "color": "Base Color", "rough": "Roughness", "metal": "Metallic",
        "spec": "Specular IOR Level", "ior": "IOR", "alpha": "Alpha",
        "coat": "Coat Weight", "coat_rough": "Coat Roughness",
        "sheen": "Sheen Weight", "trans": "Transmission Weight",
        "sss": "Subsurface Weight", "sss_radius": "Subsurface Radius", "sss_scale": "Subsurface Scale",
        "emit": "Emission Color", "emit_strength": "Emission Strength",
        "normal": "Normal", "aniso": "Anisotropic",
    }
    for k, v in kw.items():
        sock = bsdf.inputs[names.get(k, k)]
        if isinstance(v, bpy.types.NodeSocket):
            bsdf.id_data.links.new(v, sock)
        elif sock.type == "RGBA":
            sock.default_value = _rgba(v)
        else:
            sock.default_value = v


# ---------------------------------------------------------------------------
# Material library
# ---------------------------------------------------------------------------

def mat_basic(name, color, rough=0.5, metal=0.0, **kw):
    m, nb, bsdf, out = new_material(name)
    principled(bsdf, color=color, rough=rough, metal=metal, **kw)
    return m


def mat_emit(name, color, strength=5.0):
    m, nb, bsdf, out = new_material(name)
    principled(bsdf, color=(0, 0, 0), emit=color, emit_strength=strength, rough=1.0)
    return m


def mat_noisy(name, c1, c2, scale=8.0, rough=(0.5, 0.8), bump=0.15, detail=6.0, coord="Object", distortion=0.0):
    """Two-tone noise material: plaster, earth, stone, bark..."""
    m, nb, bsdf, out = new_material(name)
    tc = nb.texcoord()
    n = nb.noise(tc.outputs[coord], scale=scale, detail=detail, rough=0.6, distortion=distortion)
    col = nb.ramp(n.outputs["Fac"], [(0.3, c1), (0.7, c2)])
    r = nb.maprange(n.outputs["Fac"], 0.3, 0.7, rough[0], rough[1])
    principled(bsdf, color=col.outputs[0], rough=r)
    if bump:
        principled(bsdf, normal=nb.bump(n.outputs["Fac"], strength=bump, distance=0.05))
    return m


def mat_wood(name, c1=(0.23, 0.12, 0.06), c2=(0.42, 0.25, 0.12), scale=3.0, rough=0.55, direction="X", coord="Object", bump=0.2):
    m, nb, bsdf, out = new_material(name)
    tc = nb.texcoord()
    mp = nb.mapping(tc.outputs[coord], scale=(1, 8, 1) if direction == "X" else (8, 1, 1))
    w = nb.wave(mp.outputs[0], scale=scale, distortion=6.0, detail=3.0, direction=direction)
    n = nb.noise(tc.outputs[coord], scale=40.0, detail=2.0, loc=(-800, -300))
    f = nb.math("MULTIPLY_ADD", w.outputs["Fac"], 0.8, loc=(-600, 0))
    f2 = nb.math("ADD", f, n.outputs["Fac"], loc=(-550, -100))
    f3 = nb.math("MULTIPLY", f2, 0.55, loc=(-520, -100))
    col = nb.ramp(f3, [(0.2, c1), (0.8, c2)])
    principled(bsdf, color=col.outputs[0], rough=rough)
    if bump:
        principled(bsdf, normal=nb.bump(f3, strength=bump, distance=0.02))
    return m


def mat_tiles(name, color=(0.09, 0.09, 0.1), rows=40.0, rough=0.35, glaze=0.0, axis="Y", sheen_color=None):
    """Chinese roof tiles: channels running down the slope (UV v-direction)."""
    m, nb, bsdf, out = new_material(name)
    tc = nb.texcoord()
    sep = nb.sepxyz(tc.outputs["UV"])
    # u across eave -> alternate ridges; v down slope -> overlapping tile courses
    u = nb.math("MULTIPLY", sep.outputs[0], rows, loc=(-700, 300))
    su = nb.math("SINE", nb.math("MULTIPLY", u, 2 * pi, loc=(-650, 300)), loc=(-600, 300))
    ridge = nb.math("POWER", nb.math("ABSOLUTE", su, loc=(-560, 300)), 0.6, loc=(-520, 300))
    v = nb.math("MULTIPLY", sep.outputs[1], rows * 0.55, loc=(-700, 100))
    course = nb.math("FRACT", v, loc=(-600, 100))
    h = nb.math("ADD", ridge, nb.math("MULTIPLY", course, 0.35, loc=(-520, 100)), loc=(-450, 200))
    nz = nb.noise(tc.outputs["Object"], scale=3.0, detail=3.0, loc=(-800, -200))
    tint = nb.ramp(nz.outputs["Fac"], [(0.35, [c * 0.75 for c in color[:3]]), (0.65, [min(1, c * 1.25) for c in color[:3]])], loc=(-400, -150))
    shade = nb.mix(nb.maprange(ridge, 0, 1, 0.55, 1.0), (0, 0, 0), tint.outputs[0], blend="MULTIPLY", loc=(-250, 0))
    principled(bsdf, color=shade, rough=rough, normal=nb.bump(h, strength=0.6, distance=0.08))
    if glaze:
        principled(bsdf, coat=glaze, coat_rough=0.15)
    return m


def mat_water(name, color=(0.02, 0.05, 0.06), rough=0.03, wave_scale=60.0, bump=0.08, stretch=(1, 4, 1), patches=0.0, patch_scale=8.0):
    """Reflective water with directional ripples; `patches` adds calm/rippled wind lanes."""
    m, nb, bsdf, out = new_material(name)
    tc = nb.texcoord()
    mp = nb.mapping(tc.outputs["Generated"], scale=stretch)
    n = nb.noise(mp.outputs[0], scale=wave_scale, detail=4.0, rough=0.55)
    n2 = nb.noise(mp.outputs[0], scale=wave_scale * 0.2, detail=2.0, rough=0.5, loc=(-800, -300))
    h = nb.math("ADD", n.outputs["Fac"], nb.math("MULTIPLY", n2.outputs["Fac"], 1.5, loc=(-600, -300)), loc=(-500, -150))
    strength = bump
    if patches:
        mp2 = nb.mapping(tc.outputs["Generated"], scale=(1, 2.5, 1), loc=(-1000, -600))
        pn = nb.noise(mp2.outputs[0], scale=patch_scale, detail=2.0, rough=0.5, loc=(-800, -600))
        lane = nb.maprange(pn.outputs["Fac"], 0.45, 0.6, 0.0, 1.0, loc=(-600, -600))
        h = nb.math("MULTIPLY", h, nb.maprange(lane, 0, 1, 1 - patches, 1.0, loc=(-450, -600)), loc=(-400, -300))
        r = nb.maprange(lane, 0, 1, rough, rough + 0.12 * patches, loc=(-300, -500))
        principled(bsdf, rough=r)
    else:
        principled(bsdf, rough=rough)
    principled(bsdf, color=color, ior=1.33, spec=0.6, normal=nb.bump(h, strength=strength, distance=0.1))
    return m


def mat_foliage(name, c1=(0.05, 0.12, 0.04), c2=(0.12, 0.2, 0.05), scale=6.0, trans=0.25, rough=0.7, fuzzy=True, fuzz_scale=45.0, fuzz=1.15):
    """Foliage for blob-canopies. fuzzy=True dissolves the silhouette with
    noise at grazing angles so smooth blobs read as leafy clumps."""
    m, nb, bsdf, out = new_material(name)
    tc = nb.texcoord()
    n = nb.noise(tc.outputs["Object"], scale=scale, detail=6.0, rough=0.65)
    col = nb.ramp(n.outputs["Fac"], [(0.35, c1), (0.7, c2)])
    principled(bsdf, color=col.outputs[0], rough=rough)
    tr = nb.new("ShaderNodeBsdfTranslucent", (0, -300))
    nb.link(col.outputs[0], tr.inputs["Color"])
    mixs = nb.new("ShaderNodeMixShader", (250, 0))
    mixs.inputs[0].default_value = trans
    nb.link(bsdf.outputs[0], mixs.inputs[1])
    nb.link(tr.outputs[0], mixs.inputs[2])
    principled(bsdf, normal=nb.bump(n.outputs["Fac"], strength=0.6, distance=0.2))
    final = mixs.outputs[0]
    if fuzzy:
        lw = nb.new("ShaderNodeLayerWeight", (-600, -600))
        lw.inputs["Blend"].default_value = 0.35
        fn = nb.noise(tc.outputs["Object"], scale=fuzz_scale, detail=3.0, rough=0.7, loc=(-800, -700))
        thr = nb.math("MULTIPLY", lw.outputs["Facing"], fuzz, loc=(-400, -600))
        keep = nb.math("GREATER_THAN", fn.outputs["Fac"], thr, loc=(-250, -650))
        transp = nb.new("ShaderNodeBsdfTransparent", (250, -300))
        mix2 = nb.new("ShaderNodeMixShader", (400, -100))
        nb.link(keep, mix2.inputs[0])
        nb.link(transp.outputs[0], mix2.inputs[1])
        nb.link(mixs.outputs[0], mix2.inputs[2])
        final = mix2.outputs[0]
        out.location = (600, 0)
    nb.link(final, out.inputs["Surface"])
    return m


def mat_gold(name, color=(1.0, 0.72, 0.28), rough=0.22):
    m, nb, bsdf, out = new_material(name)
    tc = nb.texcoord()
    n = nb.noise(tc.outputs["Object"], scale=30.0, detail=4.0)
    r = nb.maprange(n.outputs["Fac"], 0.3, 0.7, rough * 0.6, rough * 1.6)
    principled(bsdf, color=color, metal=1.0, rough=r)
    return m


def mat_terrain(name, grass=(0.06, 0.11, 0.035), rock=(0.18, 0.16, 0.13), top=None, scale=0.08, slope_lo=0.62, slope_hi=0.8, bump=0.4):
    """Slope-aware terrain: vegetation on flats, rock on cliffs."""
    m, nb, bsdf, out = new_material(name)
    tc = nb.texcoord()
    geo = nb.new("ShaderNodeNewGeometry", (-1200, 400))
    sep = nb.sepxyz(geo.outputs["Normal"], loc=(-1000, 400))
    n = nb.noise(tc.outputs["Object"], scale=scale * 40, detail=8.0, rough=0.6)
    nz = nb.math("ADD", sep.outputs[2], nb.math("MULTIPLY", nb.math("SUBTRACT", n.outputs["Fac"], 0.5, loc=(-700, 250)), 0.25, loc=(-650, 250)), loc=(-600, 350))
    slope = nb.maprange(nz, slope_lo, slope_hi, 0, 1, loc=(-500, 400))
    rockc = nb.ramp(n.outputs["Fac"], [(0.3, [c * 0.7 for c in rock]), (0.7, [min(1, c * 1.3) for c in rock])], loc=(-500, 100))
    n2 = nb.noise(tc.outputs["Object"], scale=scale * 200, detail=4.0, loc=(-800, -200))
    grassc = nb.ramp(n2.outputs["Fac"], [(0.3, [c * 0.7 for c in grass]), (0.7, [min(1, c * 1.4) for c in grass])], loc=(-500, -100))
    col = nb.mix(slope, rockc.outputs[0], grassc.outputs[0], loc=(-250, 200))
    principled(bsdf, color=col, rough=0.85)
    if bump:
        rv = nb.voronoi(tc.outputs["Object"], scale=scale * 120, loc=(-800, -500), feature="F1")
        h = nb.math("ADD", n.outputs["Fac"], nb.math("MULTIPLY", rv.outputs["Distance"], 0.5, loc=(-600, -500)), loc=(-500, -500))
        principled(bsdf, normal=nb.bump(h, strength=bump, distance=0.5))
    return m


def mat_paper(name, color=(0.86, 0.8, 0.66), image=None, rough=0.8):
    m, nb, bsdf, out = new_material(name)
    tc = nb.texcoord()
    n = nb.noise(tc.outputs["Object"], scale=80.0, detail=8.0, rough=0.7)
    base = nb.ramp(n.outputs["Fac"], [(0.3, [c * 0.92 for c in color]), (0.7, color)])
    col = base.outputs[0]
    if image is not None:
        tex = nb.new("ShaderNodeTexImage", (-800, 300))
        tex.image = image
        nb.link(tc.outputs["UV"], tex.inputs["Vector"])
        col = nb.mix(tex.outputs["Alpha"], col, tex.outputs["Color"], blend="MULTIPLY", loc=(-250, 200))
    principled(bsdf, color=col, rough=rough, sheen=0.2)
    tr = nb.new("ShaderNodeBsdfTranslucent", (0, -300))
    nb.link(base.outputs[0], tr.inputs["Color"])
    mixs = nb.new("ShaderNodeMixShader", (250, 0))
    mixs.inputs[0].default_value = 0.15
    nb.link(bsdf.outputs[0], mixs.inputs[1])
    nb.link(tr.outputs[0], mixs.inputs[2])
    nb.link(mixs.outputs[0], out.inputs["Surface"])
    return m


def mat_lantern(name, color=(1.0, 0.25, 0.08), strength=12.0):
    """Paper lantern: glowing translucent shell."""
    m, nb, bsdf, out = new_material(name)
    tc = nb.texcoord()
    w = nb.wave(tc.outputs["Generated"], scale=12.0, direction="Z", loc=(-800, 0))
    f = nb.maprange(w.outputs["Fac"], 0.0, 1.0, 0.75, 1.0)
    em = nb.new("ShaderNodeEmission", (0, -200))
    em.inputs["Color"].default_value = _rgba(color)
    s = nb.math("MULTIPLY", f, strength, loc=(-200, -300))
    nb.link(s, em.inputs["Strength"])
    principled(bsdf, color=color, rough=0.6)
    add = nb.new("ShaderNodeAddShader", (250, 0))
    nb.link(bsdf.outputs[0], add.inputs[0])
    nb.link(em.outputs[0], add.inputs[1])
    nb.link(add.outputs[0], out.inputs["Surface"])
    return m


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def obj_from_bm(bm, name, coll=None, mat=None, smooth=False):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    link(ob, coll)
    if mat is not None:
        if isinstance(mat, (list, tuple)):
            for mm in mat:
                me.materials.append(mm)
        else:
            me.materials.append(mat)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    return ob


def obj_from_data(name, verts, faces, coll=None, mat=None, smooth=False, uvs=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    if uvs is not None:
        uvl = me.uv_layers.new(name="UVMap")
        for poly in me.polygons:
            for li in poly.loop_indices:
                vi = me.loops[li].vertex_index
                uvl.data[li].uv = uvs[vi]
    me.validate()
    me.update()
    ob = bpy.data.objects.new(name, me)
    link(ob, coll)
    if mat is not None:
        if isinstance(mat, (list, tuple)):
            for mm in mat:
                me.materials.append(mm)
        else:
            me.materials.append(mat)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    return ob


def box(name, size, loc=(0, 0, 0), rot=(0, 0, 0), coll=None, mat=None, bevel=0.0):
    """Axis-aligned box with its base at loc.z (not centered vertically)."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
        v.co.z = (v.co.z + 0.5) * size[2]
    ob = obj_from_bm(bm, name, coll, mat)
    ob.location = loc
    ob.rotation_euler = rot
    if bevel > 0:
        md = ob.modifiers.new("bevel", "BEVEL")
        md.width = bevel
        md.segments = 2
        md.limit_method = "ANGLE"
    return ob


def cylinder(name, r=1.0, h=1.0, n=16, loc=(0, 0, 0), coll=None, mat=None, r2=None, cap=True, smooth=True, rot=(0, 0, 0)):
    """Cylinder/cone from base (z=0) to top (z=h)."""
    r2 = r if r2 is None else r2
    verts, faces = [], []
    for i in range(n):
        a = 2 * pi * i / n
        verts.append((r * cos(a), r * sin(a), 0))
    for i in range(n):
        a = 2 * pi * i / n
        verts.append((r2 * cos(a), r2 * sin(a), h))
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    if cap:
        faces.append(tuple(reversed(range(n))))
        faces.append(tuple(range(n, 2 * n)))
    ob = obj_from_data(name, verts, faces, coll, mat)
    if smooth:
        for p in ob.data.polygons:
            if len(p.vertices) == 4:
                p.use_smooth = True
        _autosmooth(ob)
    ob.location = loc
    ob.rotation_euler = rot
    return ob


def _autosmooth(ob, angle=40):
    try:
        ob.data.set_sharp_from_angle(angle=radians(angle))
    except Exception:
        pass


def sphere(name, r=1.0, loc=(0, 0, 0), coll=None, mat=None, seg=24, rings=12, scale=(1, 1, 1), smooth=True):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r)
    ob = obj_from_bm(bm, name, coll, mat, smooth=smooth)
    ob.location = loc
    ob.scale = scale
    return ob


def ico(name, r=1.0, subdiv=2, loc=(0, 0, 0), coll=None, mat=None, smooth=True):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=r)
    ob = obj_from_bm(bm, name, coll, mat, smooth=smooth)
    ob.location = loc
    return ob


def lathe(name, profile, n=48, coll=None, mat=None, smooth=True, cap_top=False, uv=True):
    """Revolve a profile [(r, z), ...] around Z. UV: u=angle, v=profile length."""
    verts, faces, uvs = [], [], []
    m = len(profile)
    # cumulative length for v
    L = [0.0]
    for i in range(1, m):
        L.append(L[-1] + math.dist(profile[i], profile[i - 1]))
    total = L[-1] or 1.0
    for i in range(n + 1):  # duplicate seam for clean UVs
        a = 2 * pi * i / n
        for k, (r, z) in enumerate(profile):
            verts.append((r * cos(a), r * sin(a), z))
            uvs.append((i / n, L[k] / total))
    for i in range(n):
        for k in range(m - 1):
            a0 = i * m + k
            b0 = (i + 1) * m + k
            faces.append((a0, b0, b0 + 1, a0 + 1))
    ob = obj_from_data(name, verts, faces, coll, mat, smooth=smooth, uvs=uvs if uv else None)
    # weld the seam & poles
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.to_mesh(ob.data)
    bm.free()
    if smooth:
        for p in ob.data.polygons:
            p.use_smooth = True
    return ob


def add_mod(ob, kind, name=None, **props):
    md = ob.modifiers.new(name or kind.lower(), kind)
    for k, v in props.items():
        setattr(md, k, v)
    return md


def apply_mods(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev)
    old = ob.data
    ob.modifiers.clear()
    ob.data = me
    if old.users == 0:
        bpy.data.meshes.remove(old)
    return ob


def join(objs, name=None):
    """Join mesh objects into the first (data API; keeps materials)."""
    objs = [o for o in objs if o is not None]
    if not objs:
        return None
    target = objs[0]
    bm = bmesh.new()
    mats = []
    for o in objs:
        me = o.data
        for mm in me.materials:
            if mm not in mats:
                mats.append(mm)
    for o in objs:
        dg = bpy.context.evaluated_depsgraph_get()
        ev = o.evaluated_get(dg)
        tmp = bpy.data.meshes.new_from_object(ev)
        tmp.transform(o.matrix_world)
        # remap material indices
        remap = [mats.index(mm) if mm in mats else 0 for mm in o.data.materials] or [0]
        for p in tmp.polygons:
            p.material_index = remap[min(p.material_index, len(remap) - 1)]
        bm.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
    me = bpy.data.meshes.new(name or target.name)
    bm.to_mesh(me)
    bm.free()
    for mm in mats:
        me.materials.append(mm)
    coll = target.users_collection[0] if target.users_collection else None
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)
    ob = bpy.data.objects.new(name or "joined", me)
    link(ob, coll)
    return ob


def instance(src, name, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), coll=None):
    """Linked duplicate sharing mesh data (cheap)."""
    ob = bpy.data.objects.new(name, src.data)
    ob.location = loc
    ob.rotation_euler = rot
    ob.scale = scale if hasattr(scale, "__len__") else (scale, scale, scale)
    link(ob, coll)
    return ob


def collection_instance(coll_src, name, loc=(0, 0, 0), rot=(0, 0, 0), scale=1.0, coll=None):
    ob = bpy.data.objects.new(name, None)
    ob.instance_type = "COLLECTION"
    ob.instance_collection = coll_src
    ob.location = loc
    ob.rotation_euler = rot
    ob.scale = (scale, scale, scale) if not hasattr(scale, "__len__") else scale
    link(ob, coll)
    return ob


def hide_template(coll):
    """Exclude a template collection from the view layer (still instancable)."""
    scn = bpy.context.window.scene
    lc = _find_layer_coll(scn.view_layers[0].layer_collection, coll.name)
    if lc:
        lc.exclude = True


def _find_layer_coll(lc, name):
    if lc.collection.name == name:
        return lc
    for ch in lc.children:
        r = _find_layer_coll(ch, name)
        if r:
            return r
    return None


# ---------------------------------------------------------------------------
# Terrain
# ---------------------------------------------------------------------------

def heightfield(name, size=(100, 100), res=(200, 200), fn=None, loc=(0, 0, 0), coll=None, mat=None, smooth=True):
    """Grid whose z = fn(x, y) in local coords. UVs = normalized xy."""
    sx, sy = size
    nx, ny = res
    verts, faces, uvs = [], [], []
    for j in range(ny + 1):
        y = -sy / 2 + sy * j / ny
        for i in range(nx + 1):
            x = -sx / 2 + sx * i / nx
            z = fn(x, y) if fn else 0.0
            verts.append((x, y, z))
            uvs.append((i / nx, j / ny))
    w = nx + 1
    for j in range(ny):
        for i in range(nx):
            a = j * w + i
            faces.append((a, a + 1, a + w + 1, a + w))
    ob = obj_from_data(name, verts, faces, coll, mat, smooth=smooth, uvs=uvs)
    ob.location = loc
    return ob


def fbm(x, y, octaves=6, lac=2.0, gain=0.5, seed=0.0, basis="PERLIN_NEW"):
    amp, freq, s = 1.0, 1.0, 0.0
    norm = 0.0
    for _ in range(octaves):
        s += amp * noise.noise(Vector((x * freq + seed * 17.3, y * freq - seed * 9.1, seed)), noise_basis=basis)
        norm += amp
        amp *= gain
        freq *= lac
    return s / norm


def ridged(x, y, octaves=6, lac=2.0, gain=0.5, seed=0.0, offset=1.0):
    amp, freq, s, norm = 1.0, 1.0, 0.0, 0.0
    prev = 1.0
    for _ in range(octaves):
        n = noise.noise(Vector((x * freq + seed * 13.7, y * freq + seed * 3.3, seed * 0.5)))
        n = offset - abs(n)
        n *= n
        s += n * amp * prev
        norm += amp
        prev = n
        amp *= gain
        freq *= lac
    return s / norm


def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------------------
# Architecture: roofs with upturned eaves
# ---------------------------------------------------------------------------

def roof_hip(name, w, d, h, overhang=0.8, lift=0.6, sag=0.35, ridge_ratio=0.0, res=24, thickness=0.18,
             coll=None, mat=None, underside_mat=None, n_sides=4, radius=None):
    """
    Curved hip roof with upswept corners, the signature silhouette of Chinese
    architecture. Footprint w x d (without overhang). ridge_ratio>0 makes a
    hip-and-ridge (ridge length = ridge_ratio*w). n_sides>4 with radius makes
    a polygonal (pagoda) roof. UV: u along the eave, v from ridge (0) to eave (1).
    """
    verts, faces, uvs = [], [], []
    if n_sides == 4 and radius is None:
        hw, hd = w / 2 + overhang, d / 2 + overhang
        rl = ridge_ratio * w / 2
        # four trapezoid/triangle facets; build each as a grid from ridge line to eave line
        facets = [
            # eave start, eave end, ridge start, ridge end
            ((-hw, -hd), (hw, -hd), (-rl, 0.0), (rl, 0.0)),
            ((hw, -hd), (hw, hd), (rl, 0.0), (rl, 0.0)),
            ((hw, hd), (-hw, hd), (rl, 0.0), (-rl, 0.0)),
            ((-hw, hd), (-hw, -hd), (-rl, 0.0), (-rl, 0.0)),
        ]
        corner_r = math.hypot(hw, hd)
    else:
        R = (radius or w / 2) + overhang
        facets = []
        for i in range(n_sides):
            a0 = 2 * pi * i / n_sides + pi / n_sides
            a1 = 2 * pi * (i + 1) / n_sides + pi / n_sides
            facets.append(((R * cos(a0), R * sin(a0)), (R * cos(a1), R * sin(a1)), (0, 0), (0, 0)))
        corner_r = R
    for (e0, e1, r0, r1) in facets:
        base = len(verts)
        for j in range(res + 1):          # j: ridge(0) -> eave(1)
            t = j / res
            for i in range(res + 1):      # i: along eave
                s = i / res
                ex = e0[0] + (e1[0] - e0[0]) * s
                ey = e0[1] + (e1[1] - e0[1]) * s
                rx = r0[0] + (r1[0] - r0[0]) * s
                ry = r0[1] + (r1[1] - r0[1]) * s
                x = rx + (ex - rx) * t
                y = ry + (ey - ry) * t
                # concave profile: z drops quickly near ridge, flattens at eave
                z = h * (1 - t) - h * sag * sin(pi * t) * 0.5
                z = h * (1 - (t ** (1 - sag * 0.6)))
                # corner lift: strongest at facet ends (s->0/1) near the eave
                edge = abs(s - 0.5) * 2  # 0 at facet middle, 1 at corners
                z += lift * (t ** 2.2) * (edge ** 3.0)
                # slight outward flare at the corners
                flare = 1 + 0.06 * (t ** 3) * (edge ** 4)
                verts.append((x * flare, y * flare, z))
                uvs.append((s * (math.dist(e0, e1) / 4.0), t))
        for j in range(res):
            for i in range(res):
                a = base + j * (res + 1) + i
                faces.append((a, a + 1, a + res + 2, a + res + 1))
    ob = obj_from_data(name, verts, faces, coll, None, smooth=True, uvs=uvs)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    for p in ob.data.polygons:
        p.use_smooth = True
    # make sure normals point up
    if sum(p.normal.z for p in ob.data.polygons) < 0:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
        bm.to_mesh(ob.data)
        bm.free()
    if mat:
        ob.data.materials.append(mat)
    if underside_mat:
        ob.data.materials.append(underside_mat)
    sol = add_mod(ob, "SOLIDIFY", thickness=thickness, offset=-1.0)
    if underside_mat:
        sol.material_offset = 1
        sol.material_offset_rim = 1
    return ob


def ridge_beams(name, w, d, h, overhang, lift, ridge_ratio=0.0, coll=None, mat=None, r=0.09, n_sides=4, radius=None):
    """Thin raised ridges along the hips, following the roof curve."""
    objs = []
    pts_list = []
    if n_sides == 4 and radius is None:
        hw, hd = w / 2 + overhang, d / 2 + overhang
        rl = ridge_ratio * w / 2
        for (cx, cy), (rx, ry) in [((-hw, -hd), (-rl, 0)), ((hw, -hd), (rl, 0)), ((hw, hd), (rl, 0)), ((-hw, hd), (-rl, 0))]:
            pts_list.append(((rx, ry), (cx, cy)))
        if rl > 0:
            pts_list.append(("ridge", (-rl, 0), (rl, 0)))
    else:
        R = (radius or w / 2) + overhang
        for i in range(n_sides):
            a = 2 * pi * i / n_sides + pi / n_sides
            pts_list.append(((0, 0), (R * cos(a), R * sin(a))))
    for k, item in enumerate(pts_list):
        if item[0] == "ridge":
            (x0, y0), (x1, y1) = item[1], item[2]
            cu = _poly_curve(name + f"_r{k}", [(x0, y0, h + r * 0.6), (x1, y1, h + r * 0.6)], r * 1.4, coll, mat)
            objs.append(cu)
            continue
        (rx, ry), (cx, cy) = item
        pts = []
        for j in range(17):
            t = j / 16
            x = rx + (cx - rx) * t
            y = ry + (cy - ry) * t
            z = h * (1 - (t ** (1 - 0.35 * 0.6))) + lift * (t ** 2.2)
            flare = 1 + 0.06 * (t ** 3)
            pts.append((x * flare, y * flare, z + r * 0.6))
        # the tip curls up a little more
        tip = pts[-1]
        pts.append((tip[0] * 1.03, tip[1] * 1.03, tip[2] + lift * 0.35))
        objs.append(_poly_curve(name + f"_h{k}", pts, r, coll, mat))
    return objs


def _poly_curve(name, pts, r, coll, mat):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = r
    cu.bevel_resolution = 2
    cu.use_fill_caps = True
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for p, co in zip(sp.points, pts):
        p.co = (co[0], co[1], co[2], 1)
    ob = bpy.data.objects.new(name, cu)
    link(ob, coll)
    if mat:
        cu.materials.append(mat)
    return ob


def bezier_tube(name, pts, r, coll=None, mat=None, res=12, taper=None):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = r
    cu.bevel_resolution = 3
    cu.resolution_u = res
    cu.use_fill_caps = True
    sp = cu.splines.new("NURBS")
    sp.points.add(len(pts) - 1)
    for p, co in zip(sp.points, pts):
        p.co = (co[0], co[1], co[2], 1)
        if len(co) > 3:
            p.radius = co[3]
    sp.use_endpoint_u = True
    sp.order_u = min(4, len(pts))
    ob = bpy.data.objects.new(name, cu)
    link(ob, coll)
    if mat:
        cu.materials.append(mat)
    return ob


# ---------------------------------------------------------------------------
# Lights, camera, world
# ---------------------------------------------------------------------------

def camera(name, loc, target, lens=35.0, coll=None, dof=None, fstop=4.0, sensor=36.0, shift=(0, 0)):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = sensor
    cd.clip_start = 0.05
    cd.clip_end = 20000
    cd.shift_x, cd.shift_y = shift
    ob = bpy.data.objects.new(name, cd)
    link(ob, coll)
    ob.location = loc
    look_at(ob, target)
    if dof is not None:
        cd.dof.use_dof = True
        cd.dof.focus_distance = dof if isinstance(dof, (int, float)) else (Vector(dof) - Vector(loc)).length
        cd.dof.aperture_fstop = fstop
    bpy.context.window.scene.camera = ob
    return ob


def look_at(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def sun(name, elevation=20.0, azimuth=0.0, strength=3.0, angle=1.0, color=(1.0, 0.9, 0.75), coll=None):
    """azimuth measured from +Y toward +X (degrees); light travels opposite to its direction."""
    ld = bpy.data.lights.new(name, "SUN")
    ld.energy = strength
    ld.angle = radians(angle)
    ld.color = color
    ob = bpy.data.objects.new(name, ld)
    link(ob, coll)
    el, az = radians(elevation), radians(azimuth)
    # direction the light comes FROM
    d = Vector((sin(az) * cos(el), cos(az) * cos(el), sin(el)))
    ob.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    return ob


def point_light(name, loc, energy=100.0, color=(1, 0.6, 0.3), radius=0.1, coll=None):
    ld = bpy.data.lights.new(name, "POINT")
    ld.energy = energy
    ld.color = color
    ld.shadow_soft_size = radius
    ob = bpy.data.objects.new(name, ld)
    ob.location = loc
    link(ob, coll)
    return ob


def area_light(name, loc, target, size=2.0, energy=200.0, color=(1, 1, 1), coll=None, shape="SQUARE", size_y=None):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = energy
    ld.color = color
    ld.shape = shape
    ld.size = size
    if size_y:
        ld.size_y = size_y
    ob = bpy.data.objects.new(name, ld)
    ob.location = loc
    link(ob, coll)
    look_at(ob, target)
    return ob


def sky_world(scn, sun_elev=10.0, sun_rot=0.0, strength=1.0, sky_type="MULTIPLE_SCATTERING", air=1.0, aerosol=1.0, ozone=1.0, sun_disc=True, tint=None, sun_intensity=1.0):
    nt = scn.world.node_tree
    nt.nodes.clear()
    nb = Nodes(nt)
    out = nb.new("ShaderNodeOutputWorld", (400, 0))
    bg = nb.new("ShaderNodeBackground", (200, 0))
    sky = nb.new("ShaderNodeTexSky", (-200, 0))
    sky.sky_type = sky_type
    sky.sun_elevation = radians(sun_elev)
    sky.sun_rotation = radians(sun_rot)
    sky.sun_disc = sun_disc
    for attr, val in (("air_density", air), ("aerosol_density", aerosol), ("ozone_density", ozone), ("sun_intensity", sun_intensity)):
        try:
            setattr(sky, attr, val)
        except Exception:
            pass
    col = sky.outputs[0]
    if tint is not None:
        col = nb.mix(1.0, col, tint, blend="MULTIPLY", loc=(0, 0))
    nb.link(col, bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength
    nb.link(bg.outputs[0], out.inputs["Surface"])
    return nb, out


def gradient_world(scn, top=(0.2, 0.3, 0.5), horizon=(0.8, 0.7, 0.6), bottom=None, strength=1.0, exponent=1.0):
    nt = scn.world.node_tree
    nt.nodes.clear()
    nb = Nodes(nt)
    out = nb.new("ShaderNodeOutputWorld", (400, 0))
    bg = nb.new("ShaderNodeBackground", (200, 0))
    tc = nb.texcoord()
    sep = nb.sepxyz(tc.outputs["Generated"])
    z = nb.maprange(sep.outputs[2], 0.5, 1.0, 0, 1)
    if exponent != 1.0:
        z = nb.math("POWER", z, exponent)
    col = nb.ramp(z, [(0.0, horizon), (1.0, top)])
    nb.link(col.outputs[0], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength
    nb.link(bg.outputs[0], out.inputs["Surface"])
    return nb, out


def fog_volume(name, size, loc, density=0.02, color=(0.9, 0.9, 0.95), falloff_height=None, z0=0.0, anisotropy=0.3, noise_scale=0.0, coll=None, noise_amount=0.6):
    """Box-shaped fog domain; optional exponential height falloff and noise breakup."""
    ob = box(name, size, loc=(loc[0], loc[1], loc[2]), coll=coll)
    m, nb, bsdf, out = new_material(name + "_mat")
    nb.nodes.remove(bsdf)
    vol = nb.new("ShaderNodeVolumePrincipled", (0, 0))
    vol.inputs["Color"].default_value = _rgba(color)
    vol.inputs["Anisotropy"].default_value = anisotropy
    dens = density
    if falloff_height or noise_scale:
        tc = nb.texcoord()
        sep = nb.sepxyz(tc.outputs["Object"])
        d = None
        if falloff_height:
            zrel = nb.math("SUBTRACT", sep.outputs[2], z0 - loc[2], loc=(-700, 200))
            e = nb.math("DIVIDE", zrel, -falloff_height, loc=(-600, 200))
            d = nb.math("EXPONENT", e, loc=(-500, 200))
        if noise_scale:
            n = nb.noise(tc.outputs["Object"], scale=noise_scale, detail=3.0, loc=(-800, -100))
            nf = nb.maprange(n.outputs["Fac"], 0.35, 0.7, 1 - noise_amount, 1.0 + noise_amount * 0.5, loc=(-500, -100))
            d = nf if d is None else nb.math("MULTIPLY", d, nf, loc=(-350, 100))
        dens = nb.math("MULTIPLY", d, density, loc=(-200, 100))
        nb.link(dens, vol.inputs["Density"])
    else:
        vol.inputs["Density"].default_value = density
    nb.link(vol.outputs[0], out.inputs["Volume"])
    ob.data.materials.append(m)
    ob.visible_shadow = True
    return ob


# ---------------------------------------------------------------------------
# Output: beauty + normalized depth (mist) for the web parallax effect
# ---------------------------------------------------------------------------

def setup_outputs(scn, slug, mist_start=1.0, mist_depth=500.0, mist_falloff="LINEAR"):
    vl = scn.view_layers[0]
    vl.use_pass_mist = True
    vl.use_pass_z = False
    w = scn.world
    w.mist_settings.start = mist_start
    w.mist_settings.depth = mist_depth
    w.mist_settings.falloff = mist_falloff
    tree = bpy.data.node_groups.get(slug + "_comp")
    if tree:
        bpy.data.node_groups.remove(tree)
    tree = bpy.data.node_groups.new(slug + "_comp", "CompositorNodeTree")
    scn.compositing_node_group = tree
    tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = tree.nodes.new("CompositorNodeRLayers")
    rl.scene = scn
    rl.location = (-400, 0)
    go = tree.nodes.new("NodeGroupOutput")
    go.location = (300, 100)
    tree.links.new(rl.outputs["Image"], go.inputs[0])
    fo = tree.nodes.new("CompositorNodeOutputFile")
    fo.location = (300, -200)
    fo.directory = RENDER_DIR + "/"
    fo.file_name = slug + "_depth"
    try:
        fo.format.media_type = "IMAGE"
    except Exception:
        pass
    fo.format.file_format = "PNG"
    fo.format.color_mode = "BW"
    fo.format.color_depth = "16"
    fo.file_output_items.clear()
    fo.file_output_items.new("FLOAT", "mist")
    tree.links.new(rl.outputs["Mist"], fo.inputs[0])
    scn.render.filepath = RENDER_DIR + "/" + slug + ".png"
    try:
        scn.render.image_settings.media_type = "IMAGE"
    except Exception:
        pass
    scn.render.image_settings.file_format = "PNG"
    scn.render.image_settings.color_mode = "RGB"
    scn.render.image_settings.color_depth = "8"
    return tree


def save_blend(path=None):
    path = path or ROOT + "/blender/east_asia.blend"
    bpy.ops.wm.save_as_mainfile(filepath=path, compress=True)
    return path


def cloudy_sky_world(scn, sun_elev=5.0, sun_rot=0.0, strength=0.3, cloud_scale=1.2, coverage=0.5, cloud_height=1.0,
                     warm=(1.0, 0.55, 0.3), shade=(0.35, 0.33, 0.38), sun_disc=True, air=1.0, aerosol=1.0, cloud_strength=1.0, stretch=(1.0, 3.0)):
    """Physical sky + cheap painted cloud layer computed from the view direction
    (projected onto a virtual plane), lit warm toward the sun and cool away from it."""
    nt = scn.world.node_tree
    nt.nodes.clear()
    nb = Nodes(nt)
    out = nb.new("ShaderNodeOutputWorld", (900, 0))
    bg = nb.new("ShaderNodeBackground", (700, 0))
    sky = nb.new("ShaderNodeTexSky", (-200, 300))
    sky.sky_type = "MULTIPLE_SCATTERING"
    sky.sun_elevation = radians(sun_elev)
    sky.sun_rotation = radians(sun_rot)
    sky.sun_disc = sun_disc
    for attr, val in (("air_density", air), ("aerosol_density", aerosol)):
        try:
            setattr(sky, attr, val)
        except Exception:
            pass
    tc = nb.new("ShaderNodeTexCoord", (-1400, -200))
    norm = nb.new("ShaderNodeVectorMath", (-1250, -200))
    norm.operation = "NORMALIZE"
    nb.link(tc.outputs["Generated"], norm.inputs[0])
    sep = nb.sepxyz(norm.outputs[0], loc=(-1100, -200))
    zc = nb.math("MAXIMUM", sep.outputs[2], 0.015, loc=(-950, -350))
    u = nb.math("DIVIDE", sep.outputs[0], zc, loc=(-800, -150))
    v = nb.math("DIVIDE", sep.outputs[1], zc, loc=(-800, -250))
    comb = nb.new("ShaderNodeCombineXYZ", (-650, -200))
    nb.link(nb.math("MULTIPLY", u, stretch[0] * cloud_height, loc=(-720, -150)), comb.inputs[0])
    nb.link(nb.math("MULTIPLY", v, stretch[1] * cloud_height, loc=(-720, -250)), comb.inputs[1])
    n = nb.noise(comb.outputs[0], scale=cloud_scale, detail=8.0, rough=0.62, loc=(-500, -200), dims="2D")
    dens = nb.maprange(n.outputs["Fac"], 1.0 - coverage, 1.0 - coverage + 0.22, 0.0, 1.0, loc=(-300, -200))
    horizon = nb.maprange(sep.outputs[2], 0.0, 0.12, 0.0, 1.0, loc=(-300, -350))
    mask = nb.math("MULTIPLY", dens, horizon, loc=(-150, -250))
    # sun proximity for warm lighting of cloud edges
    sd = Vector((-sin(radians(sun_rot)) * 0 + sin(radians(sun_rot)) * cos(radians(sun_elev)), cos(radians(sun_rot)) * cos(radians(sun_elev)), sin(radians(sun_elev))))
    dot = nb.new("ShaderNodeVectorMath", (-900, 150))
    dot.operation = "DOT_PRODUCT"
    nb.link(norm.outputs[0], dot.inputs[0])
    dot.inputs[1].default_value = sd
    near = nb.maprange(dot.outputs["Value"], 0.2, 1.0, 0.0, 1.0, loc=(-600, 150), interp="SMOOTHSTEP")
    thick = nb.maprange(n.outputs["Fac"], 1.0 - coverage + 0.1, 1.0, 0.0, 1.0, loc=(-300, 50))
    litmix = nb.math("MULTIPLY", near, nb.math("SUBTRACT", 1.0, nb.math("MULTIPLY", thick, 0.7, loc=(-250, 100)), loc=(-200, 100)), loc=(-100, 150))
    ccol = nb.mix(litmix, shade, warm, loc=(100, 100))
    cbright = nb.mix(1.0, ccol, (cloud_strength, cloud_strength, cloud_strength), blend="MULTIPLY", loc=(250, 100))
    final = nb.mix(mask, sky.outputs[0], cbright, loc=(450, 0))
    nb.link(final, bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength
    nb.link(bg.outputs[0], out.inputs["Surface"])
    return nb, out

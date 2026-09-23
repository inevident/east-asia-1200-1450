"""
S5 — TECHNOLOGICAL: A treasure fleet at sea (early 1400s).
A five-masted seagoing junk — battened lug sails, sternpost rudder, a hull of
watertight bulkhead compartments, steered by the magnetic compass — leads an
escort fleet across the Indian Ocean at sunset, as in Zheng He's voyages
(1405–1433). The ocean is Blender's FFT ocean simulation.
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

SLUG = "technological"
PREVIEW = globals().get("PREVIEW", True)
scn = E.new_scene("S5_Technological", res=(2560, 1440), samples=192, look="AgX - Medium High Contrast")
E.purge()
P = A.palette()
rnd = random.Random(51)
C = E.collection("tech_fleet")
C_ENV = E.collection("tech_env")

# ------------------------------------------------------------ ocean (FFT)
def mat_ocean(name):
    m, nb, bsdf, out = E.new_material(name)
    attr = nb.new("ShaderNodeAttribute", (-900, -200))
    attr.attribute_name = "foam"
    foam = nb.maprange(attr.outputs["Fac"], 0.25, 0.9, 0.0, 1.0, loc=(-700, -200))
    tc = nb.texcoord()
    fn = nb.noise(tc.outputs["Object"], scale=0.6, detail=6.0, rough=0.7, loc=(-900, -450))
    foamm = nb.math("MULTIPLY", foam, nb.maprange(fn.outputs["Fac"], 0.4, 0.65, 0.2, 1.0, loc=(-700, -450)), loc=(-500, -300))
    col = nb.mix(foamm, (0.006, 0.03, 0.04), (0.75, 0.78, 0.8), loc=(-300, 0))
    rough = nb.maprange(foamm, 0, 1, 0.07, 0.6, loc=(-300, -200))
    E.principled(bsdf, color=col, rough=rough, ior=1.33, spec=0.7)
    # small-scale ripples on top of the simulated swell
    rn = nb.noise(tc.outputs["Object"], scale=3.5, detail=4.0, rough=0.55, loc=(-900, -700))
    E.principled(bsdf, normal=nb.bump(rn.outputs["Fac"], strength=0.25, distance=0.1))
    return m


ocean_mat = mat_ocean("tech_ocean")
for mname in ("P_sail", "P_sail_light"):
    if bpy.data.materials.get(mname):
        bpy.data.materials.remove(bpy.data.materials[mname])
P["sail"] = A._mat_sail("P_sail", (0.36, 0.12, 0.05))
P["sail_light"] = A._mat_sail("P_sail_light", (0.5, 0.3, 0.15))
# darker, tarred hull for seagoing junks
for mname in ("P_hull",):
    if bpy.data.materials.get(mname):
        bpy.data.materials.remove(bpy.data.materials[mname])
P["hull"] = E.mat_wood("P_hull", c1=(0.035, 0.022, 0.014), c2=(0.09, 0.055, 0.03), scale=2.0, rough=0.55)
bpy.ops.mesh.primitive_plane_add(size=2)
ocean = bpy.context.active_object
ocean.name = "tech_ocean"
for c in ocean.users_collection:
    c.objects.unlink(ocean)
C_ENV.objects.link(ocean)
om = ocean.modifiers.new("ocean", "OCEAN")
om.geometry_mode = "GENERATE"
om.spatial_size = 110
om.repeat_x = 11
om.repeat_y = 11
om.resolution = 18 if not PREVIEW else 10
om.viewport_resolution = 6
om.wave_scale = 2.4
om.choppiness = 1.25
om.wind_velocity = 12
om.wave_alignment = 0.6
om.wave_direction = radians(30)
om.random_seed = 7
om.use_normals = True
om.use_foam = True
om.foam_coverage = 0.25
om.foam_layer_name = "foam"
om.time = 12.0
ocean.data.materials.append(ocean_mat)
ocean.location = (-om.spatial_size * om.repeat_x / 2 + 50, -om.spatial_size * om.repeat_y / 2 + 50, 0)
# flat far-field sea to the horizon (same look, no simulation)
far = E.heightfield("tech_farsea", (40000, 40000), (2, 2), loc=(0, 0, -2.6), coll=C_ENV,
                    mat=E.mat_water("tech_farwater", color=(0.006, 0.03, 0.04), rough=0.06, wave_scale=4000, bump=0.08, stretch=(1, 3, 1)))

# ------------------------------------------------------------ the fleet
flag = E.mat_basic("tech_flag", (0.55, 0.05, 0.03), rough=0.7)
main = A.junk("tech_flagship", L=58, B=15, D=6.2, masts=5, P=P, coll=C, sail_mat="sail", seed=5, loc=(0, 0, -1.4), rot=0.0, sail_scale=0.78, sail_angle=14)
main.rotation_euler = (radians(1.2), radians(-1.5), radians(0))
escorts = [((-170, 150, -1.0), 8, 36, 3), ((-360, 60, -1.0), -5, 32, 3), ((-90, 420, -1.0), 10, 40, 5), ((-520, 330, -1.0), 2, 30, 3), ((120, 520, -1.0), 15, 34, 3), ((-700, 620, -1.0), 5, 28, 3)]
for k, (loc, rot, L, masts) in enumerate(escorts):
    A.junk(f"tech_escort{k}", L=L, B=L * 0.26, D=L * 0.11, P=P, coll=C, masts=masts, sail_mat="sail" if k % 2 else "sail_light", seed=20 + k,
           loc=loc, rot=radians(rot), sail_scale=0.85, sail_angle=rnd.uniform(8, 16))
# pennants on the flagship's masts
for o in bpy.data.objects:
    if o.name.startswith("tech_flagship_mast"):
        tip_z = o.data.vertices[-1].co.z if o.type == "MESH" else 20
pn = E.obj_from_data("tech_pennant", [(0, 0, 0), (-6, 0.4, -0.6), (0, 0, -1.6)], [(0, 1, 2)], C, flag)
pn.location = (-L * 0 + 0.5, 0, 48)

# ------------------------------------------------------------ sky & light
SUN_AZ, SUN_EL = -62.0, 3.6
E.cloudy_sky_world(scn, sun_elev=SUN_EL, sun_rot=SUN_AZ, strength=0.35, cloud_scale=1.6, coverage=0.48, cloud_height=1.0,
                   warm=(1.0, 0.46, 0.2), shade=(0.22, 0.2, 0.28), sun_disc=True, aerosol=1.5, cloud_strength=1.2, stretch=(1.0, 3.2))
E.sun("tech_sun", elevation=SUN_EL, azimuth=SUN_AZ, strength=6.0, angle=0.7, color=(1.0, 0.55, 0.28), coll=C_ENV)
E.fog_volume("tech_haze", (20000, 20000, 900), loc=(0, 0, -10), density=0.00016, color=(0.9, 0.9, 0.95), anisotropy=0.4, falloff_height=180.0, z0=0.0, coll=C_ENV)

cam = E.camera("tech_cam", (62, -84, 5.0), (-34, 14, 20.0), lens=30, coll=C_ENV)
E.setup_outputs(scn, SLUG, mist_start=10, mist_depth=1500)
result = {"objects": len(scn.objects)}

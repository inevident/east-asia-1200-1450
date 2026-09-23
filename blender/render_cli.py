"""
Headless final render:
  Blender -b east_asia.blend --python render_cli.py -- <SceneName> <slug> [samples] [percent]
Writes renders/<slug>.png and (via the compositor File Output node) renders/<slug>_depth*.png
"""
import sys
import time
import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
scene_name, slug = argv[0], argv[1]
samples = int(argv[2]) if len(argv) > 2 else None
pct = int(argv[3]) if len(argv) > 3 else 100
cam_name = argv[4] if len(argv) > 4 and argv[4] != "-" else None
mist = (float(argv[5]), float(argv[6])) if len(argv) > 6 else None

ROOT = "/Applications/Personal App/AP-WORLD-WEBSITE/blender"
scn = bpy.data.scenes[scene_name]
bpy.context.window.scene = scn if bpy.context.window else scn
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "METAL"
prefs.get_devices()
for d in prefs.devices:
    d.use = d.type == "METAL"
scn.cycles.device = "GPU"
if samples:
    scn.cycles.samples = samples
if cam_name:
    scn.camera = scn.objects[cam_name]
if mist:
    scn.world.mist_settings.start, scn.world.mist_settings.depth = mist
scn.render.resolution_percentage = pct
if scn.compositing_node_group:
    for n in scn.compositing_node_group.nodes:
        if n.bl_idname == "CompositorNodeOutputFile":
            n.mute = False
            n.directory = ROOT + "/renders/"
            n.file_name = slug + "_depth"
scn.render.filepath = f"{ROOT}/renders/{slug}.png"
t = time.time()
bpy.ops.render.render(write_still=True, scene=scn.name)
print(f"RENDERED {slug} in {time.time() - t:.1f}s")

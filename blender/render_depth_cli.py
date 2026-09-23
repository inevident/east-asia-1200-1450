"""
Clean depth (Mist pass) renders for the web parallax effect.
Volumetric fog makes Cycles' mist pass noisy, so hide every volume domain and
render the mist pass alone at low samples.

  Blender -b east_asia.blend --python render_depth_cli.py -- slug:Scene:camera:start:depth [...]
"""
import sys
import time
import bpy

ROOT = "/Applications/Personal App/AP-WORLD-WEBSITE/blender"
jobs = sys.argv[sys.argv.index("--") + 1:]
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "METAL"
prefs.get_devices()
for d in prefs.devices:
    d.use = d.type == "METAL"


def is_volume(ob):
    if ob.type != "MESH":
        return False
    for slot in ob.material_slots:
        m = slot.material
        if m and m.node_tree:
            out = m.node_tree.nodes.get("Material Output")
            if out and out.inputs["Volume"].is_linked and not out.inputs["Surface"].is_linked:
                return True
    return False


for job in jobs:
    slug, scene_name, cam, start, depth = job.split(":")
    scn = bpy.data.scenes[scene_name]
    hidden = []
    for ob in scn.objects:
        if is_volume(ob) and not ob.hide_render:
            ob.hide_render = True
            hidden.append(ob.name)
    scn.camera = scn.objects[cam]
    scn.world.mist_settings.start = float(start)
    scn.world.mist_settings.depth = float(depth)
    scn.cycles.device = "GPU"
    scn.cycles.samples = 24
    scn.cycles.use_denoising = False
    scn.render.resolution_percentage = 100
    for n in scn.compositing_node_group.nodes:
        if n.bl_idname == "CompositorNodeOutputFile":
            n.mute = False
            n.directory = ROOT + "/renders/"
            n.file_name = slug + "_depth"
    scn.render.filepath = ROOT + f"/renders/_discard_{slug}.png"
    t = time.time()
    bpy.ops.render.render(write_still=True, scene=scn.name)
    print(f"DEPTH {slug} in {time.time() - t:.1f}s (hid {len(hidden)} volumes: {hidden})")

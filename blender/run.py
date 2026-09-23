"""
Runner used from the Blender MCP session:
    exec(open(".../blender/run.py").read(), {"SCENE": "s0_hero", "MODE": "preview", "OUT": "/path.png"})

MODE: "build" (build only), "preview" (build + small render), "final" (build + full render + depth pass).
"""
import time
import bpy

ROOT = "/Applications/Personal App/AP-WORLD-WEBSITE/blender"
_scene = globals().get("SCENE")
_mode = globals().get("MODE", "preview")
_out = globals().get("OUT")
_pct = globals().get("PCT", 35)
_samples = globals().get("SAMPLES", 24)
_rebuild = globals().get("REBUILD", True)

t0 = time.time()
g = {"PREVIEW": _mode != "final", "__name__": "__main__"}
if _rebuild:
    exec(open(f"{ROOT}/scenes/{_scene}.py").read(), g)
scn = bpy.context.window.scene
t1 = time.time()
if _mode in ("preview", "final"):
    if _mode == "preview":
        scn.render.resolution_percentage = _pct
        scn.cycles.samples = _samples
        # don't write the depth pass during previews
        if scn.compositing_node_group:
            for n in scn.compositing_node_group.nodes:
                if n.bl_idname == "CompositorNodeOutputFile":
                    n.mute = True
    else:
        if scn.compositing_node_group:
            for n in scn.compositing_node_group.nodes:
                if n.bl_idname == "CompositorNodeOutputFile":
                    n.mute = False
    if _out:
        scn.render.filepath = _out
    bpy.ops.render.render(write_still=True)
result = {"scene": scn.name, "build_s": round(t1 - t0, 2), "render_s": round(time.time() - t1, 2), "info": g.get("result")}

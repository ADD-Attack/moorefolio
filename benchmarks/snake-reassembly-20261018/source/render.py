"""Staging per REVIEW-STAGING.md + seat rules (P1 ruling): reference-sampled #C1C1BF backdrop,
shadow-catcher contact shadow, shaped neutral key/rim/fill, tight glare on emissives.
blender -b <blend> -P render.py -- <ticket_dir_windows> <mode preview|final> <tag> [views]
final = Cycles 256 adaptive .01 OIDN 1920x1080 (judged); preview = 32 spp 960x540 (ITERATION PREVIEW ONLY).
"""
import bpy, sys, os, json, math
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
a = sys.argv[sys.argv.index("--") + 1:]; T, MODE, TAG = a[0], a[1], a[2]; VIEWS = (a[3] if len(a) > 3 else "full,head").split(",")
OUT = os.path.join(T, "r2", "captures" if MODE == "final" else "previews"); os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
def s2l(c): return ((c + .055) / 1.055) ** 2.4 if c > .04045 else c / 12.92
BG = [s2l(193 / 255), s2l(193 / 255), s2l(191 / 255)]      # #C1C1BF

assets = [o for o in sc.objects if o.type == "MESH" and not o.hide_render]
# ---- stage objects (idempotent)
for n in ["STAGE_catcher", "STAGE_key", "STAGE_rim", "STAGE_fill", "STAGE_cam"]:
    if n in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[n])
mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
for o in assets:
    for c in o.bound_box:
        w = o.matrix_world @ Vector(c); mn = Vector(map(min, mn, w)); mx = Vector(map(max, mx, w))
ctr = (mn + mx) / 2; ext = (mx - mn).length
bpy.ops.mesh.primitive_plane_add(size=ext * 6, location=(ctr.x, ctr.y, mn.z)); pl = bpy.context.object; pl.name = "STAGE_catcher"
pl.is_shadow_catcher = True
def light(name, loc, energy, size, col=(1, 1, 1)):
    ld = bpy.data.lights.new(name, "AREA"); ld.energy = energy; ld.size = size; ld.color = col
    o = bpy.data.objects.new(name, ld); sc.collection.objects.link(o); o.location = loc
    o.rotation_euler = (ctr - Vector(loc)).to_track_quat("-Z", "Y").to_euler(); return o
light("STAGE_key", ctr + Vector((-9, -10, 12)), 2600, 8, (1, .98, .95))
light("STAGE_rim", ctr + Vector((8, 12, 7)), 2200, 6, (.95, .97, 1))
light("STAGE_fill", ctr + Vector((10, -12, 3)), 700, 10)
# world: neutral dim light for reflections (camera never sees it: film transparent + composite #C1C1BF)
w = bpy.data.worlds.get("stage") or bpy.data.worlds.new("stage"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (*BG, 1); w.node_tree.nodes["Background"].inputs["Strength"].default_value = .25
cd = bpy.data.cameras.new("STAGE_cam"); cam = bpy.data.objects.new("STAGE_cam", cd); sc.collection.objects.link(cam); sc.camera = cam
cd.lens = 35; cd.sensor_width = 36
# ---- render settings
sc.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons["cycles"].preferences
try:
    prefs.compute_device_type = "OPTIX"; prefs.get_devices()
    for d in prefs.devices: d.use = d.type == "OPTIX"
    sc.cycles.device = "GPU"
except Exception as e: print("GPU fallback CPU", e); sc.cycles.device = "CPU"
fin = MODE == "final"
sc.cycles.samples = 256 if fin else 32; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = .01 if fin else .05
sc.cycles.use_denoising = True; sc.cycles.denoiser = "OPENIMAGEDENOISE"
sc.render.resolution_x, sc.render.resolution_y = (1920, 1080) if fin else (960, 540); sc.render.resolution_percentage = 100
sc.render.film_transparent = True; sc.view_settings.view_transform = "Standard"; sc.view_settings.look = "None"; sc.view_settings.exposure = 0
sc.render.image_settings.file_format = "PNG"; sc.render.image_settings.color_mode = "RGB"
# ---- compositor: alpha-over onto #C1C1BF, then tight glare
sc.use_nodes = True; nt = sc.node_tree; nt.nodes.clear()
rl = nt.nodes.new("CompositorNodeRLayers"); ao = nt.nodes.new("CompositorNodeAlphaOver"); rgb = nt.nodes.new("CompositorNodeRGB")
rgb.outputs[0].default_value = (*BG, 1); gl = nt.nodes.new("CompositorNodeGlare"); co = nt.nodes.new("CompositorNodeComposite")
gl.glare_type = "FOG_GLOW"
for k, v in (("Threshold", .9), ("Strength", .3), ("Size", .12)):
    if k in gl.inputs: gl.inputs[k].default_value = v
nt.links.new(rgb.outputs[0], ao.inputs[1]); nt.links.new(rl.outputs["Image"], ao.inputs[2])
nt.links.new(ao.outputs[0], gl.inputs[0]); nt.links.new(gl.outputs[0], co.inputs[0])

def frame(objs, d, margin=1.08, look=None):
    pts = []
    for o in objs:
        for c in o.bound_box: pts.append(o.matrix_world @ Vector(c))
    c = look or sum(pts, Vector()) / len(pts); d = Vector(d).normalized(); dist = 10.
    for _ in range(6):
        cam.location = c - d * dist; cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler(); bpy.context.view_layer.update()
        ps = [world_to_camera_view(sc, cam, p) for p in pts]
        xs = [p.x for p in ps]; ys = [p.y for p in ps]
        # recentre then fit
        cx = (min(xs) + max(xs)) / 2 - .5; cy = (min(ys) + max(ys)) / 2 - .5
        mat = cam.matrix_world.to_3x3(); w = 2 * dist * math.tan(cd.angle_x / 2); h = w * sc.render.resolution_y / sc.render.resolution_x
        c = c + mat @ Vector((cx * w, cy * h, 0))
        span = max(max(xs) - min(xs), (max(ys) - min(ys)))
        dist *= span * margin
    return dict(location=list(cam.location), rotation=list(cam.rotation_euler), lens=cd.lens)

head = [o for o in assets if o.name.startswith("Head")]
neck = [o for o in assets if o.name.startswith(("Segment_01", "Segment_02"))]
el = math.radians(22)
VIEWDEF = {"full": (assets, (0.0, math.cos(el), -math.sin(el)), 1.06),
           "head": (head + neck, (0.22, .96, -.17), 1.12),
           "seg": ([o for o in assets if o.name in ("Segment_16", "Segment_17")], (0.0, 1.0, -.12), 1.15)}
frames = {}
for v in VIEWS:
    objs, d, m = VIEWDEF[v]
    frames[v] = frame(objs, d, m)
    sc.render.filepath = os.path.join(OUT, f"{TAG}-{ {'full': 'full-body', 'head': 'head-closeup'}.get(v, v + '-detail') }.png")
    print("RENDER_START", v, MODE, sc.cycles.device, flush=True); bpy.ops.render.render(write_still=True); print("RENDER_DONE", sc.render.filepath, flush=True)
json.dump(dict(mode=MODE, device=sc.cycles.device, samples=sc.cycles.samples, adaptive=sc.cycles.adaptive_threshold,
               denoise="OIDN", res=[sc.render.resolution_x, sc.render.resolution_y], backdrop="#C1C1BF (linear %s)" % BG,
               glare=dict(type="FOG_GLOW", threshold=.9, strength=.3, size=.12), frames=frames,
               lights=[dict(name=o.name, loc=list(o.location), energy=o.data.energy, size=o.data.size) for o in sc.objects if o.type == "LIGHT"]),
          open(os.path.join(OUT, f"{TAG}-render-settings.json"), "w"), indent=1)
print("RENDER_COMPLETE", flush=True)

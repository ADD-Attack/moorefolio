# Round-1 inspection: reference pixel stats + clay GLB topology/bounds + workbench preview renders.
# Run: blender -b -P inspect_r1.py -- <ticket_dir_windows>
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector

T = sys.argv[sys.argv.index("--") + 1]
PACK = os.path.join(T, "pack"); CLAY = os.path.join(T, "clay"); OUT = os.path.join(T, "r1")
os.makedirs(OUT, exist_ok=True)
rep = {}

def img_arr(p):
    im = bpy.data.images.load(p); w, h = im.size
    a = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, im.channels)[::-1, :, :3]
    # 8-bit PNG: Image.pixels already returns stored sRGB values / 255 (no linearization)
    return (a * 255 + .5).astype(int)

# ---- reference stats
for f in ["REFERENCE.png", "head-closeup.png", "segment2-closeup.png", "tail-closeup.png"]:
    im = img_arr(os.path.join(PACK, f)); h, w, _ = im.shape
    c = [im[:40, :40], im[:40, -40:], im[-40:, :40], im[-40:, -40:]]
    rep[f] = {"size": [w, h], "corners": [np.median(x.reshape(-1, 3), 0).astype(int).tolist() for x in c]}
im = img_arr(os.path.join(PACK, "REFERENCE.png")); H, W, _ = im.shape
bg = np.median(im[:80, -400:].reshape(-1, 3), 0)
m = np.abs(im - bg).sum(2) > 40
r, g, b = im[..., 0], im[..., 1], im[..., 2]
gl = (g > 110) & (g - r > 45) & (b > 80)
R = rep["REFERENCE.png"]; R["bg_sample"] = bg.tolist()
ys, xs = np.where(m[:, :]); R["fg_bbox_loose"] = [int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())]
R["glow_px"] = int(gl.sum()); R["glow_median"] = np.median(im[gl], 0).astype(int).tolist()
eg = gl[250:420, 270:430]; ys, xs = np.where(eg)
R["eye_glow_bbox"] = [int(xs.min() + 270), int(xs.max() + 270), int(ys.min() + 250), int(ys.max() + 250)]
mm = m & ~gl; px = im[mm]; lum = px.mean(1)
R["metal_median"] = np.median(px, 0).astype(int).tolist()
R["metal_lum_p5_p50_p95"] = [float(np.percentile(lum, q)) for q in (5, 50, 95)]
R["col_profile"] = {}
for x in range(60, W, 60):
    col = np.where(m[:, x])[0]
    R["col_profile"][x] = [int(col.min()), int(col.max())] if len(col) else None
R["row_profile"] = {}
for y in range(20, H, 40):
    row = np.where(m[y, :])[0]
    R["row_profile"][y] = [int(row.min()), int(row.max())] if len(row) else None

# ---- clay
def clean():
    bpy.ops.wm.read_factory_settings(use_empty=True)

for name in ["hunyuan-head", "hunyuan-segment2", "hunyuan-tail", "hunyuan-test-snake"]:
    clean()
    bpy.ops.import_scene.gltf(filepath=os.path.join(CLAY, name + ".glb"))
    objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    info = {"mesh_objects": len(objs), "materials": len(bpy.data.materials), "images": len(bpy.data.images)}
    tris = verts = 0; mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3); comps = []
    nonman = 0; boundary = 0
    for o in objs:
        me = o.data; me.calc_loop_triangles(); tris += len(me.loop_triangles); verts += len(me.vertices)
        bm = bmesh.new(); bm.from_mesh(me); bm.transform(o.matrix_world)
        for v in bm.verts:
            mn = Vector(map(min, mn, v.co)); mx = Vector(map(max, mx, v.co))
        nonman += sum(1 for e in bm.edges if not e.is_manifold)
        boundary += sum(1 for e in bm.edges if e.is_boundary)
        # connected components
        bm.verts.ensure_lookup_table(); seen = set()
        for v in bm.verts:
            if v.index in seen: continue
            st = [v]; seen.add(v.index); n = 0; cmn = Vector(v.co); cmx = Vector(v.co)
            while st:
                a = st.pop(); n += 1
                cmn = Vector(map(min, cmn, a.co)); cmx = Vector(map(max, cmx, a.co))
                for e in a.link_edges:
                    o2 = e.other_vert(a)
                    if o2.index not in seen: seen.add(o2.index); st.append(o2)
            comps.append((n, [round(x, 3) for x in cmn], [round(x, 3) for x in cmx]))
        bm.free()
    comps.sort(key=lambda c: -c[0])
    info.update(tris=tris, verts=verts, bbox_min=[round(x, 4) for x in mn], bbox_max=[round(x, 4) for x in mx],
                dims=[round(b - a, 4) for a, b in zip(mn, mx)], components=len(comps), top_components=comps[:6],
                nonmanifold_edges=nonman, boundary_edges=boundary)
    rep[name] = info
    # workbench previews (ITERATION PREVIEW ONLY)
    sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"
    sc.render.resolution_x, sc.render.resolution_y = 1024, 768
    sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "SINGLE"
    sc.display.shading.single_color = (0.6, 0.6, 0.6); sc.display.shading.show_cavity = True
    sc.display.shading.cavity_type = "BOTH"; sc.display.shading.show_shadows = False
    sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.53, 0.53, 0.52)
    ctr = (mn + mx) / 2; rad = (mx - mn).length / 2
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.lens = 50
    views = {"front": (0, -1, 0), "side": (1, 0, 0), "top": (0, 0, 1), "3q": (0.7, -0.7, 0.35), "back3q": (-0.7, 0.7, 0.35)}
    for vn, d in views.items():
        d = Vector(d).normalized(); cam.location = ctr + d * rad * 3.0
        cam.rotation_euler = (ctr - cam.location).to_track_quat("-Z", "Y" if vn != "top" else "Y").to_euler()
        if vn == "top": cam.rotation_euler = (0, 0, 0)
        sc.render.filepath = os.path.join(OUT, f"{name}_{vn}.png"); bpy.ops.render.render(write_still=True)

with open(os.path.join(OUT, "inspect.json"), "w") as f: json.dump(rep, f, indent=1)
print("DONE")

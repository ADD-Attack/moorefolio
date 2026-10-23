# Pose tests (straight / S-curve / coil) on the rigged snake + joint-integrity metrics + Workbench preview stills.
# Usage: blender -b forge_snake_rigged.blend --python pose_test.py -- OUTDIR
import bpy, sys, json, math
from mathutils import Vector, Matrix
outdir = sys.argv[sys.argv.index("--")+1]
arm = bpy.data.objects["ForgeSnake_Rig"]; body = bpy.data.objects["ForgeSnake"]
chain = [b.name for b in arm.data.bones if b.name != "root"]   # tail -> head, hierarchy order
L = sum(arm.data.bones[n].length for n in chain)

def straight(s): return Vector((s - L/2, 0, 0.5))
def scurve(s):   # strong S: wavelength 9, amplitude 1.6 (min bend radius ~1.3 for ~1 m barrels)
    return Vector((s * 0.72 - L*0.36, 1.6 * math.sin(2*math.pi*s/9.0), 0.5))
def coil(s):     # tight rising coil: radius 1.8, pitch 1.25/turn, head end on top
    th = s / 1.8; return Vector((1.8*math.cos(th), 1.8*math.sin(th), 0.5 + 1.25*th/(2*math.pi)))
def dense(f, s):  # arclength-correct sampler
    pts=[f(0)]; acc=[0.0]; n=4000
    for i in range(1,n+1):
        p=f(L*1.6*i/n); acc.append(acc[-1]+(p-pts[-1]).length); pts.append(p)
    for i in range(len(acc)-1):
        if acc[i+1] >= s: t=(s-acc[i])/(acc[i+1]-acc[i]); return pts[i].lerp(pts[i+1], t)
    return pts[-1]

def apply_pose(f):
    for pb in arm.pose.bones: pb.matrix_basis = Matrix()
    bpy.context.view_layer.update()
    up = Vector((0,0,1)); s = 0.0
    for n in chain:
        pb = arm.pose.bones[n]; ln = pb.bone.length
        h = pb.head.copy() if pb.bone.use_connect else dense(f, s)
        y = (dense(f, s+ln) - h).normalized()
        up = (up - y*up.dot(y)).normalized(); x = y.cross(up)
        M = Matrix((x, y, up)).transposed().to_4x4(); M.translation = h
        pb.matrix = M; bpy.context.view_layer.update(); s += ln

# rest geometry per source unit, for joint-integrity metrics (edge stretch inside each rigid barrel)
dg = bpy.context.evaluated_depsgraph_get()
def coords():
    e = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); return [v.co.copy() for v in e.data.vertices]
for pb in arm.pose.bones: pb.matrix_basis = Matrix()
bpy.context.view_layer.update(); rest = coords()
edges = [tuple(e.vertices) for e in body.data.edges]
def metrics(cur):
    r = [(cur[a]-cur[b]).length / max((rest[a]-rest[b]).length,1e-6) for a,b in edges]
    r.sort(); n=len(r)
    return dict(edge_stretch_min=round(r[0],3), p01=round(r[n//100],3), p99=round(r[n*99//100],3), max=round(r[-1],3))

scn = bpy.context.scene
scn.render.engine = 'BLENDER_WORKBENCH'; scn.display.shading.light = 'STUDIO'
scn.display.shading.color_type = 'TEXTURE'; scn.display.shading.show_shadows = True
scn.display.shading.show_cavity = True
scn.render.resolution_x, scn.render.resolution_y = 1600, 1000
w = bpy.data.worlds.get("World") or bpy.data.worlds.new("World"); scn.world = w
w.color = (0.533, 0.533, 0.527)  # linear of ~#C1C1BF
scn.display.shading.background_type = 'WORLD'
cam = bpy.data.objects.new("PoseCam", bpy.data.cameras.new("PoseCam")); scn.collection.objects.link(cam); scn.camera = cam
cam.data.lens = 40
res = {}
for name, f in (("straight", straight), ("scurve", scurve), ("coil", coil), ("rest", None)):
    if f: apply_pose(f)
    else:
        for pb in arm.pose.bones: pb.matrix_basis = Matrix()
        bpy.context.view_layer.update()
    cur = coords(); res[name] = metrics(cur)
    mn = Vector([min(v[i] for v in cur) for i in range(3)]); mx = Vector([max(v[i] for v in cur) for i in range(3)])
    c = (mn+mx)/2; ext = max((mx-mn).x, (mx-mn).y, (mx-mn).z)
    d = Vector((0.0, -1.0, 0.85 if name != "coil" else 0.55)).normalized()
    cam.location = c + d * ext * (1.25 if name in ('straight','scurve') else 2.2)
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    scn.render.filepath = f"{outdir}\\pose-{name}.png"
    bpy.ops.render.render(write_still=True)
json.dump(res, open(f"{outdir}\\pose-metrics.json","w"), indent=1)
print("POSE", json.dumps(res))

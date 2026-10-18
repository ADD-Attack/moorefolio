# Round 2 coarse build under the Construction Rule (Decision 35).
# Every sculpted surface below is the Hunyuan clay itself: cut -> logged local refines -> weighted collapse
# decimation of that same surface. Parametric geometry only for machined parts (lens rings, glow bars, port).
# blender -b -P build_r2.py -- <clay_dir> <work_dir>
import bpy, bmesh, sys, os, json, math, numpy as np, mathutils
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
sys.path.append(os.path.dirname(__file__)); from lib import *
A = sys.argv[sys.argv.index("--") + 1:]; CLAY, WORK = A[0], A[1]
LOG = {"refines": [], "deviation": {}, "tris": {}, "scales": {}}
reset(); SC = bpy.context.scene
CLAYM = clay_mat()

def setv(o, V): o.data.vertices.foreach_set("co", V.ravel()); o.data.update()

def normals(o):
    o.data.update(); a = np.empty(len(o.data.vertices) * 3); o.data.vertices.foreach_get("normal", a); return a.reshape(-1, 3)

def bump(t, half):  # smooth 1..0 falloff, |t|<half
    t = np.clip(np.abs(t) / half, 0, 1); return 0.5 * (1 + np.cos(np.pi * t))

def decimate(o, target, weights=None, protect=0.0, vox=0.0):
    """Reduce the formed clay surface itself. Hunyuan shells are not closed: voxel remesh destroyed them (head area
    8 -> 0.7), and deleting non-manifold fans + hole-fill + curvature-weighted collapse shattered them (previews r2/iter).
    Working path (verified visually): merge doubles, SPLIT the >2-face non-manifold edges (no area removed), then
    unweighted quadric collapse with triangulation, iterated to target."""
    bpy.context.view_layer.objects.active = o; o.select_set(True)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bad = [e for e in bm.edges if len(e.link_faces) > 2]; bmesh.ops.split_edges(bm, edges=bad)
    bm.to_mesh(o.data); bm.free(); LOG.setdefault("cleanup", {})[o.name] = {"nonmanifold_edges_split": len(bad)}
    for _ in range(14):
        if tris(o) <= target * 1.03: break
        m = o.modifiers.new("dec", "DECIMATE"); m.ratio = max(0.2, target / tris(o)); m.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=m.name)
    # re-weld the split seams so they do not open as dark cracks (weld radius = 0.15 % of part size)
    V_ = verts(o); r_ = 0.0015 * float(np.linalg.norm(V_.max(0) - V_.min(0)))
    bm = bmesh.new(); bm.from_mesh(o.data); n0 = len(bm.verts); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=r_)
    bmesh.ops.dissolve_degenerate(bm, dist=r_ * 0.1, edges=bm.edges); bmesh.ops.triangulate(bm, faces=bm.faces)
    LOG["cleanup"][o.name]["post_weld_verts_merged"] = n0 - len(bm.verts); bm.to_mesh(o.data); bm.free()
    o.select_set(False); return tris(o)

def curvature_w(o):
    """Feature weight per vertex from normal variation over 1-ring (protects ridges, seams, lips, rims)."""
    bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
    w = np.zeros(len(bm.verts))
    for v in bm.verts:
        n = v.normal; s = 0; k = 0
        for e in v.link_edges:
            s += 1 - n.dot(e.other_vert(v).normal); k += 1
        w[v.index] = s / max(k, 1)
    bm.free(); w = np.clip(w / (np.percentile(w, 90) + 1e-9), 0, 1); return w

def deviation(master, build, length, tag):
    """Hausdorff-style: distance from master verts to build surface, as % of section length."""
    bm = bmesh.new(); bm.from_mesh(build.data); bvh = BVHTree.FromBMesh(bm)
    V = verts(master); idx = np.random.default_rng(0).choice(len(V), min(len(V), 40000), replace=False)
    d = np.array([(bvh.find_nearest(Vector(V[i]))[3] or 0) for i in idx]); bm.free()
    r = {"p50_pct": float(np.percentile(d, 50) / length * 100), "p95_pct": float(np.percentile(d, 95) / length * 100),
         "p99_pct": float(np.percentile(d, 99) / length * 100), "max_pct": float(d.max() / length * 100)}
    LOG["deviation"][tag] = r; print("DEV", tag, r, flush=True); return r

def dup(o, name):
    c = o.copy(); c.data = o.data.copy(); c.name = name; SC.collection.objects.link(c); return c

def lathe_ring(profile, n, M):
    """Machined part: revolve (r, h) profile about local Z, n sides; return bmesh-ready verts/faces in frame M."""
    vs = []; fs = []
    for i in range(n):
        a = 2 * math.pi * i / n
        for (r, h) in profile: vs.append(M @ Vector((r * math.cos(a), r * math.sin(a), h)))
    P = len(profile)
    for i in range(n):
        j = (i + 1) % n
        for k in range(P - 1): fs.append((i * P + k, j * P + k, j * P + k + 1, i * P + k + 1))
    return vs, fs

def mesh_from(name, vs, fs):
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in vs], [], fs); me.update()
    o = bpy.data.objects.new(name, me); SC.collection.objects.link(o); return o

def join(objs, name):
    bm = bmesh.new()
    for o in objs:
        tmp = o.data.copy(); tmp.transform(o.matrix_world); bm.from_mesh(tmp); bpy.data.meshes.remove(tmp)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for o in objs: bpy.data.objects.remove(o)
    o = bpy.data.objects.new(name, me); SC.collection.objects.link(o); return o

t = import_glb(os.path.join(CLAY, "hunyuan-tail.glb")); t.name = "TAIL_master"
V = verts(t)
bm = bmesh.new(); bm.from_mesh(t.data); bm.verts.ensure_lookup_table()
slab = [bm.verts[i] for i in np.where(V[:, 2] < -0.255)[0]]          # D-T1 fused ground slab
bmesh.ops.delete(bm, geom=slab, context="VERTS"); bm.to_mesh(t.data); bm.free()
NOSE = np.array([0.34, -0.945, -0.07]); BASE = np.array([0.555, -0.33, -0.07])
ax = (BASE - NOSE); ax /= np.linalg.norm(ax)
bisect_keep(t, tuple(BASE), tuple(ax), True)
V = verts(t); keep_island_near(t, V[np.argmin(((V - NOSE) ** 2).sum(1))]); V = verts(t)
along = (V - NOSE) @ ax; LT_clay = float(along.max())
base_sec = V[along > along.max() - 0.04]; perp = base_sec - NOSE - np.outer((base_sec - NOSE) @ ax, ax)
bc = base_sec.mean(0)
dia_clay = float(2 * np.percentile(np.linalg.norm((base_sec - bc) - np.outer((base_sec - bc) @ ax, ax), axis=1), 90))
S_TAIL = 0.52 / dia_clay
xa = Vector(ax); za = Vector((0, 0, 1)); za = (za - xa * za.dot(xa)).normalized(); ya = za.cross(xa)
R3 = Matrix((xa, ya, za))  # rows: local axes
Mt = Matrix.Scale(S_TAIL, 4) @ R3.to_4x4() @ Matrix.Translation(-Vector(bc))
t.data.transform(Mt); t.data.update()

V=verts(t);kt=2.7/(LT_clay/dia_clay);V[:,0]*=kt;setv(t,V)
t.data.calc_loop_triangles();np.savez(os.path.join(WORK,'tail-master.npz'),v=verts(t),f=np.array([t.vertices[:] for t in t.data.loop_triangles]))
json.dump({'k':kt,'before':LT_clay/dia_clay,'after':2.7,'base_dia_clay':dia_clay,'scale':S_TAIL,'bc':bc.tolist(),'axis':ax.tolist(),'transform':[list(r) for r in Mt]},open(os.path.join(WORK,'tail-refine.json'),'w'),indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK,'tail-refined-master.blend'))

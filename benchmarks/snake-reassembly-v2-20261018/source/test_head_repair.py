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

# =============================================================== HEAD
h = import_glb(os.path.join(CLAY, "hunyuan-head.glb")); h.name = "HEAD_master"
CUT_X = 0.19
bisect_keep(h, (CUT_X, 0, 0), (1, 0, 0), True)
V = verts(h); keep_island_near(h, V[np.argmin(V[:, 0])])
V = verts(h); N = normals(h); LOG["head_master_tris"] = tris(h)
HL = float(CUT_X - V[:, 0].min())
raw = dup(h, "HEAD_raw_cut")      # untouched cut clay = baseline for sections / deviation

EYE = np.array([-0.667, 0.0, 0.528])
for side in (-1, 1):
    # ---- R1 brow ledge (H11): push the clay brow roll above the eye outward + slightly down so its lip overhangs the socket
    sm = (np.sign(V[:, 1]) == side) & (np.abs(V[:, 1]) > 0.14) & (N[:, 1] * side > 0.2)
    w = bump(V[:, 0] - EYE[0], 0.16) * bump(V[:, 2] - 0.648, 0.045) * sm
    V[:, 1] += side * 0.022 * w; V[:, 2] -= 0.006 * w
    LOG["refines"].append({"id": "R1-brow-ledge", "side": side, "verts": int((w > .05).sum()), "max_out": 0.022, "down": 0.006,
                           "region": "x=-0.667±0.16, z=0.648±0.045, outward-facing side verts"})
# ---- R2 forehead hood (H11 per F2): inflate the forward brow swell along its own normals
w = bump(V[:, 0] + 0.85, 0.08) * bump(V[:, 2] - 0.57, 0.05) * (N[:, 2] > 0.1)
V += N * (0.012 * w)[:, None]
LOG["refines"].append({"id": "R2-forehead-hood", "verts": int((w > .05).sum()), "max_normal_push": 0.012, "region": "x=-0.85±0.08, z=0.57±0.05"})
# ---- R3 snout ridges (H12): sharpen the clay ridge crests by pushing high-curvature upper-flank verts along their normals
setv(h, V); cw = curvature_w(h); N = normals(h)
w = cw * (V[:, 0] < -0.70) * (V[:, 0] > -0.97) * (np.abs(V[:, 1]) > 0.08) * (V[:, 2] > 0.36) * (N[:, 2] > -0.2)
w = w * bump(V[:, 0] + 0.83, 0.15)
V += N * (0.005 * w)[:, None]
LOG["refines"].append({"id": "R3-snout-ridge-crests", "verts": int((w > .05).sum()), "max_normal_push": 0.005})
# ---- R4 mouth seam serration (F6): along-seam smoothing of z only, in the seam band; path + depth kept
band = (V[:, 0] < -0.42) & (np.abs(V[:, 1]) > 0.09) & (V[:, 2] > 0.24) & (V[:, 2] < 0.36)
idx = np.where(band)[0]; kd = KDTree(len(idx))
for k, i in enumerate(idx): kd.insert(Vector(V[i]), k)
kd.balance()
for _ in range(2):
    Z = V[idx, 2].copy()
    for k, i in enumerate(idx):
        nb = [j for (_, j, _) in kd.find_range(Vector(V[i]), 0.028)]
        nbv = [j for j in nb if abs(V[idx[j], 1] - V[i, 1]) < 0.02 and abs(Z[j] - Z[k]) < 0.014]
        if len(nbv) > 3: V[i, 2] = 0.5 * Z[k] + 0.5 * float(np.mean(Z[nbv]))
LOG["refines"].append({"id": "R4-mouth-serration-smooth", "verts": int(len(idx)), "passes": 2, "axis": "z only, along-seam window 0.028, |dz|<0.014"})
setv(h, V)

# ---- R5 snout-only axial stretch (producer ruling on S0-1): minimum stretch landing L:H in 1.45 +/- 3 %.
# Applied AFTER R1-R4 so every local form rides along; only verts forward of the eye ring (x < X0) move,
# along the head's own axis (clay -X); eye ring (centre -0.667, r 0.083) and skull behind it untouched.
L0, H0 = 0.768, 0.78 - 0.19; LH_TARGET = 1.42
X0 = EYE[0] - 0.083 - 0.010; TIP = float(V[:, 0].min())
L_NEW = LH_TARGET * H0; K_SN = 1.0 + (L_NEW - L0) / (X0 - TIP)
def snout_stretch(P):
    m = P[:, 0] < X0; P[m, 0] = X0 + (P[m, 0] - X0) * K_SN; return int(m.sum())
nmov = snout_stretch(V); setv(h, V)
Vr = verts(raw); snout_stretch(Vr); setv(raw, Vr)     # baseline gets the same stretch so deviation measures refine+reduction only
LOG["refines"].append({"id": "R5-snout-axial-stretch", "ruling": "S0-1", "x0_clay": X0, "tip_before": TIP, "tip_after": X0 + (TIP - X0) * K_SN,
                       "k": K_SN, "verts_moved": nmov, "LH_before": L0 / H0, "LH_after": L_NEW / H0, "LH_band": [1.4065, 1.4935]})
print("R5", K_SN, L0 / H0, L_NEW / H0, flush=True)

# ---- Same-scale / pose frame: rear (collar cut) at origin, snout along +X, uniform scale to H = 1.3 D (D = 1.0)
H_CLAY = 0.78 - 0.19; S_HEAD = 1.30 / H_CLAY; ZC = 0.435
LOG["scales"]["head"] = {"H_clay": H_CLAY, "uniform_scale": S_HEAD, "L_to_ventrear_clay_before_R5": 0.768, "LH_before_R5": 0.768 / H_CLAY, "LH_after_R5": L_NEW / H0, "snout_k": K_SN, "snout_x0": X0}
Mh = Matrix.Scale(S_HEAD, 4) @ Matrix(((-1, 0, 0, CUT_X), (0, -1, 0, 0), (0, 0, 1, -ZC), (0, 0, 0, 1)))
for o in (h, raw): o.data.transform(Mh); o.data.update()


for o in list(SC.objects):
 if o != h: bpy.data.objects.remove(o)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK,'head-refined-master.blend'))
for variant,thick,vox in [('weld',0,0),('voxel',0,.008),('solidvox',.012,.008)]:
 c=dup(h,'test_'+variant); bpy.context.view_layer.objects.active=c
 bm=bmesh.new();bm.from_mesh(c.data);bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=.003)
 bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(c.data);bm.free()
 if thick:
  m=c.modifiers.new('close shell','SOLIDIFY');m.thickness=thick;m.offset=0;bpy.ops.object.modifier_apply(modifier=m.name)
 if vox:
  m=c.modifiers.new('clay volume repair','REMESH');m.mode='VOXEL';m.voxel_size=vox;m.use_smooth_shade=False;bpy.ops.object.modifier_apply(modifier=m.name)
  m=c.modifiers.new('reduce repaired clay','DECIMATE');m.ratio=min(1,12000/tris(c));m.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=m.name)
 else: decimate(c,12000)
 print('TEST',variant,tris(c),flush=True)
 c.data.materials.append(CLAYM)
 h.hide_render=True
bpy.data.objects.remove(h)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK,'head-repair-tests.blend'))

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

s = import_glb(os.path.join(CLAY, "hunyuan-segment2.glb")); s.name = "SEG_master"
keep_island_near(s, (0.0, -0.9, 0.0))                       # component A only
bisect_keep(s, (0.20, 0, 0), (1, 0, 0), True)               # cut at the +X housing face (drops fused melt)
V = verts(s)
spike = (V[:, 2] < -0.478) & (V[:, 0] > -0.30) & (V[:, 0] < 0.02)   # D-S2 drip spike (melt artefact)
bm = bmesh.new(); bm.from_mesh(s.data); bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[bm.verts[i] for i in np.where(spike)[0]], context="VERTS"); bm.to_mesh(s.data); bm.free()
V = verts(s); keep_island_near(s, V[np.argmax(V[:, 2])]); V = verts(s)
drum = V[(V[:, 0] > -0.50) & (V[:, 0] < 0.17)]
yc = float((np.percentile(drum[:, 1], 0.5) + np.percentile(drum[:, 1], 99.5)) / 2); zc = float((np.percentile(drum[:, 2], 0.5) + np.percentile(drum[:, 2], 99.5)) / 2)
D_clay = float(max(np.percentile(drum[:, 2], 99.5) - np.percentile(drum[:, 2], 0.5), np.percentile(drum[:, 1], 99.5) - np.percentile(drum[:, 1], 0.5)))
L_plate = float(np.percentile(drum[:, 0], 99.5) - np.percentile(drum[:, 0], 0.5))
S_SEG = 1.0 / D_clay
LOG["scales"]["segment"] = {"D_clay": D_clay, "plate_span_clay": L_plate, "LD_measured": L_plate / D_clay, "uniform_scale": S_SEG, "yc": yc, "zc": zc}
# frame: clay axes kept (no flip), centred on drum axis; housing ring stays at the clay -X end (tail side)
xs = V[:, 0]; Ms = Matrix.Scale(S_SEG, 4) @ Matrix(((1, 0, 0, 0.0), (0, 1, 0, -yc), (0, 0, 1, -zc), (0, 0, 0, 1)))   # detailed shield face -> local -Y (camera side on the front run); clean ring at -X
s.data.transform(Ms); s.data.update()
Vs = verts(s); HX = float(Vs[:, 0].max()); TX = float(Vs[:, 0].min()); PITCH = HX - TX
bm = bmesh.new(); bm.from_mesh(s.data)
inner = [f for f in bm.faces if math.hypot(f.calc_center_median().y, f.calc_center_median().z) < 0.30]
LOG["segment_interior_faces_culled"] = len(inner); bmesh.ops.delete(bm, geom=inner, context="FACES"); bm.to_mesh(s.data); bm.free()
seg_master = dup(s, "SEG_master_keep")
# housing ring radius (clay, measured) for the insert
ringv = Vs[Vs[:, 0] < TX + 0.09]; rads = np.hypot(ringv[:, 1], ringv[:, 2]); R_RING = float(np.percentile(rads, 60))
def drum_retopo(src, name, nu, nv):
    """PRESERVATION-PLAN S.3: cylindrical (u = around, v = axial) retopo of the clay drum. Every vertex is the
    OUTERMOST clay surface point on its radial ray (BVH ray cast from outside toward the axis) - the plate tab,
    notch step, ledge, waist band, brackets, pistons and housing ring heights are the clay's own radii."""
    bmx = bmesh.new(); bmx.from_mesh(src.data); bvh = BVHTree.FromBMesh(bmx)
    xs_ = np.linspace(TX + 0.004, HX - 0.004, nv); R = np.zeros((nv, nu))
    for i, x in enumerate(xs_):
        for j in range(nu):
            a = 2 * math.pi * j / nu; d = Vector((0, math.cos(a), math.sin(a)))
            hit = bvh.ray_cast(Vector((x, 0, 0)) + d * 1.5, -d)
            R[i, j] = (Vector((x, 0, 0)) + d * 1.5 - hit[0]).length if hit[0] is not None else np.nan
            R[i, j] = 1.5 - R[i, j] if hit[0] is not None else np.nan
    bmx.free(); miss = int(np.isnan(R).sum())
    for _ in range(4):
        m = np.isnan(R)
        if not m.any(): break
        Rp = np.where(m, np.nanmean(R), R); nb = (np.roll(Rp, 1, 1) + np.roll(Rp, -1, 1)) / 2; R[m] = nb[m]
    vs = []; fs = []
    for i, x in enumerate(xs_):
        for j in range(nu):
            a = 2 * math.pi * j / nu; vs.append((x, R[i, j] * math.cos(a), R[i, j] * math.sin(a)))
    for i in range(nv - 1):
        for j in range(nu):
            k = i * nu + j; k2 = i * nu + (j + 1) % nu; fs.append((k, k2, k2 + nu, k + nu))
    # end caps (hide the hollow interior at bends): inset ring + centre fan, at both ends
    for i, sgn in ((0, -1), (nv - 1, 1)):
        c = len(vs); vs.append((xs_[i], 0.0, 0.0))
        ring = [i * nu + j for j in range(nu)]
        for j in range(nu):
            a_, b_ = ring[j], ring[(j + 1) % nu]
            fs.append((a_, b_, c) if sgn > 0 else (b_, a_, c))
    o = mesh_from(name, vs, fs); LOG.setdefault("drum_retopo", {})[name] = {"nu": nu, "nv": nv, "ray_misses_filled": miss}
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.triangulate(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    return o


k=.85/LOG['scales']['segment']['LD_measured']
V=verts(seg_master);V[:,0]*=k;setv(seg_master,V);TX*=k;HX*=k;PITCH*=k
LOG['refines'].append({'id':'R6-segment-axial-stretch','k':k,'before':LOG['scales']['segment']['LD_measured'],'after':.85})
bpy.data.objects.remove(s)
exec(compile(open(os.path.join(os.path.dirname(__file__),'body_fix.py')).read(),'body_fix.py','exec'))
bpy.data.objects.remove(seg_master)
s.data.materials.clear();s.data.materials.append(CLAYM)
s.name='SRC_SegmentHero'
json.dump(LOG,open(os.path.join(WORK,'body-log.json'),'w'),indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK,'body-test.blend'))

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

# ---- Decimate the refined clay to budget with feature protection
master_ref = dup(h, "HEAD_refined_master")
exec(compile(open(os.path.join(os.path.dirname(__file__),'head_fix.py')).read(),'head_fix.py','exec'))
deviation(master_ref, h, HL * S_HEAD, "head_build_vs_refined_master")
deviation(raw, h, HL * S_HEAD, "head_build_vs_raw_clay")

# ---- H6 eye lens assemblies (machined, rule 2): seated on the clay eye disc, fitted to the measured clay ring
bmh = bmesh.new(); bmh.from_mesh(h.data); bvh_h = BVHTree.FromBMesh(bmh); lens_parts = []
R = 0.083 * S_HEAD          # clay eye-ring outer radius (probe_negY: 45 px @ 545 px/unit), measured not invented
for side in (-1, 1):
    c0 = Mh @ Vector((EYE[0], 0, EYE[2]))
    hit = bvh_h.ray_cast(Vector((c0.x, 3.0 * side, c0.z)), Vector((0, -side, 0)))
    ctr, nrm = hit[0], hit[1].normalized()
    # disc normal = mean surface normal over the clay disc (radius 0.5R) around the hit
    ns = [];
    for k in range(24):
        a = 2 * math.pi * k / 24; o_ = ctr + Vector((math.cos(a) * 0.5 * R, 0, math.sin(a) * 0.5 * R))
        hh = bvh_h.ray_cast(o_ + Vector((0, 1.0 * side, 0)), Vector((0, -side, 0)))
        if hh[0] is not None: ns.append(hh[1])
    if ns: nrm = sum(ns, Vector()).normalized()
    if nrm.y * side < 0: nrm = -nrm
    rr = R
    M = Matrix.Translation(ctr + nrm * .018) @ nrm.to_track_quat("Z", "Y").to_matrix().to_4x4()
    prof = [(R * 1.00, 0.000), (R * 1.00, 0.012), (R * 0.90, 0.016), (R * 0.84, 0.010),   # outer metal ring
            (R * 0.80, 0.004), (R * 0.76, 0.012), (R * 0.72, 0.012),                    # groove, machined lip
            (R * 0.70, 0.009), (R * 0.68, 0.012),                                      # bezel falling to blades
            (R * 0.60, 0.019), (R * 0.36, 0.027), (R * 0.0, 0.031)]                    # domed optical cover
    vs, fs = lathe_ring(prof, 24, M)
    # recessed aperture blades (P2): 8 thin vanes under the cover
    for b in range(8):
        a = 2 * math.pi * b / 8
        q = [M @ Vector((r * math.cos(a + d), r * math.sin(a + d), 0.004)) for (r, d) in ((R * .52, 0), (R * .52, .5), (R * .2, .35), (R * .2, .05))]
        k = len(vs); vs += q; fs.append((k, k + 1, k + 2, k + 3))
    lens_parts.append(mesh_from(f"EyeLens_{'L' if side==1 else 'R'}", vs, fs))
    LOG["refines"].append({"id": "H6-lens-seat", "side": side, "clay_ring_r": rr, "lens_R": R, "normal": list(nrm)})
lens = join(lens_parts, "HEAD_lens")
head = join([h, lens], "Head")
bmh.free(); bpy.data.objects.remove(master_ref)
LOG["tris"]["Head"] = tris(head)

# =============================================================== HERO SEGMENT
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
Vax=verts(s); KAX=.85/(L_plate/D_clay); Vax[:,0]*=KAX; setv(s,Vax)
LOG['refines'].append({'id':'R6-segment-axial-stretch','ruling':'S0-3','k':KAX,'LD_before':L_plate/D_clay,'LD_after':(L_plate*KAX)/D_clay,'before_projection':True})
Vs = verts(s); HX = float(Vs[:, 0].max()); TX = float(Vs[:, 0].min()); PITCH = HX - TX
bm = bmesh.new(); bm.from_mesh(s.data)
inner = [f for f in bm.faces if math.hypot(f.calc_center_median().y, f.calc_center_median().z) < 0.30]
LOG["segment_interior_faces_culled"] = len(inner); bmesh.ops.delete(bm, geom=inner, context="FACES"); bm.to_mesh(s.data); bm.free()
seg_master = dup(s, "SEG_master_keep")
# housing ring radius (clay, measured) for the insert
ringv = Vs[Vs[:, 0] < TX + 0.09*KAX]; rads = np.hypot(ringv[:, 1], ringv[:, 2]); R_RING = float(np.max(rads))
LOG['housing_measurement']={'method':'outer radial envelope of clean clay housing, original axial span .09; excludes interior-radius percentile choice in R2','radius':R_RING,'old_percentile60':float(np.percentile(rads,60))}
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
bpy.data.objects.remove(s)
exec(compile(open(os.path.join(os.path.dirname(__file__),'body_fix.py')).read(),'body_fix.py','exec'))
deviation(seg_master, s, PITCH, "segment_build_vs_clay")
LOG["scales"]["segment"].update({"pitch": PITCH, "ring_r": R_RING})

def glow_insert(name, nb=20, r=R_RING*1.025, x0=TX + 0.010, x1=TX + 0.090):
    """B9 machined insert: segmented bars around the full circumference (separate mesh; clay at this gate)."""
    vs = []; fs = []
    for i in range(nb):
        a0 = 2 * math.pi * i / nb + 0.05; a1 = 2 * math.pi * (i + 1) / nb - 0.05
        p = [Vector((x0, (r) * math.cos(a), (r) * math.sin(a))) for a in (a0, a1)] + [Vector((x1, (r) * math.cos(a), (r) * math.sin(a))) for a in (a1, a0)]
        q = [Vector((v.x, v.y * 0.94, v.z * 0.94)) for v in p]
        k = len(vs); vs += p + q
        fs += [(k, k + 1, k + 2, k + 3), (k + 4, k, k + 3, k + 7), (k + 1, k + 5, k + 6, k + 2)]
    return mesh_from(name, vs, fs)
glow = glow_insert("GlowInsert")
LOG["tris"]["SegmentHero"] = tris(s); LOG["tris"]["GlowInsert"] = tris(glow)

# ---- Neck variant (B10): derived from the hero build mesh; heavier, overlapping collar plates
nk = dup(s, "SegmentNeck"); Vn = verts(nk); r = np.hypot(Vn[:, 1], Vn[:, 2]); rmax = np.percentile(r, 97)
outer = r > 0.86 * rmax
f = np.where(outer,1.04,1.0)
Vn[:, 1] *= f; Vn[:, 2] *= f
ends = outer & (Vn[:, 0] > HX - 0.25 * PITCH - 0.1)
Vn[ends, 0] += 0.14    # plates lap forward over the next joint -> lit ring reads as partial arc
LOG['refines'].append({'id':'R30-P8-insert-neck','method':'wider separated insert bars and .14 forward overlap of existing neck plates'})
setv(nk, Vn); LOG["tris"]["SegmentNeck"] = tris(nk)
LOG["refines"].append({"id": "B10-neck-variant", "outer_plate_scale": 1.04, "forward_lap": 0.09})

LOG["refines"].append({"id":"R20-neck-plate-lap","method":"extend actual outer neck plates forward .09 and radially 4 percent; housing and core stay unchanged"})

# =============================================================== TAIL
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
Vax=verts(t); KT=2.7/(LT_clay/dia_clay); Vax[:,0]*=KT; setv(t,Vax)
LOG['refines'].append({'id':'R12-tail-axial-stretch','ruling':'S0-4','k':KT,'LD_before':LT_clay/dia_clay,'LD_after':2.7})
tail_master = dup(t, "TAIL_master_keep")
exec(compile(open(os.path.join(os.path.dirname(__file__),'tail_fix.py')).read(),'tail_fix.py','exec'))
deviation(tail_master, t, LT_clay * S_TAIL, "tailtip_build_vs_clay")
t.name = "TailTip"; LTIP = float(-verts(t)[:, 0].min())
LOG["scales"]["tail"] = {"len_clay": LT_clay, "base_dia_clay": dia_clay, "len_over_base_dia_before": LT_clay / dia_clay, "axial_k": KT, "len_over_base_dia": 2.7, "uniform_scale": S_TAIL}
LOG["tris"]["TailTip"] = tris(t)

# ---- T1 taper segments: derived from the hero build mesh (approved ruling), lighter LOD, radial taper
def taper(name, s0, s1, sl, port=False, target=470):
    o = dup(s, name)
    bpy.context.view_layer.objects.active=o
    m=o.modifiers.new('derived hero taper LOD','DECIMATE');m.ratio=(target-4)/tris(o);m.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=m.name)
    if "smooth_hardware_faces" in o.data: del o.data["smooth_hardware_faces"]
    Vt = verts(o); k = (Vt[:, 0] - TX) / PITCH; sc_ = s0 + (s1 - s0) * k
    Vt[:, 1] *= sc_; Vt[:, 2] *= sc_; Vt[:, 0] *= sl; setv(o, Vt)
    if port:   # circular port fitting (machined)
        rr = 0.5 * (s0 + s1) / 2
        M = Matrix.Translation((-0.05 * sl, -rr - 0.005, 0.0)) @ Matrix.Rotation(math.pi / 2, 4, "X")
        vs, fs = lathe_ring([(0.09, 0), (0.09, 0.03), (0.07, 0.035), (0.045, 0.02), (0.0, 0.02)], 10, M)
        o = join([o, mesh_from("port", vs, fs)], name)
    return o
t1 = taper("TailTaper1", 0.70, 0.86, 0.90, port=True, target=480); t2 = taper("TailTaper2", 0.52, 0.70, 0.80, target=480)
LOG["refines"].append({"id":"R17-tail-taper-plate-continuity","method":"decimate actual traced hero module, then radial taper; replaces smooth radial-projection taper; keeps fitted port"})
def scaled_glow(name, sc_, sl):
    g = glow_insert(name, 14); Vg = verts(g); Vg[:, 1] *= sc_; Vg[:, 2] *= sc_; Vg[:, 0] *= sl; setv(g, Vg); return g
g1 = scaled_glow("GlowInsertT1", 0.86, 0.90)
for o in (t1, t2, g1): LOG["tris"][o.name] = tris(o)
LOG["tris"]["tail_section_total"] = tris(t1) + tris(t2) + tris(g1) + tris(t)

for o in [raw, seg_master, tail_master]: bpy.data.objects.remove(o)
for o in SC.objects:
    if o.type == "MESH":
        o.data.materials.clear(); o.data.materials.append(CLAYM)
        bpy.context.view_layer.objects.active = o; o.select_set(True)
        try: bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
        except Exception as e: print("smooth fail", e)
        if 'smooth_hardware_faces' in o.data:
            for i in o.data['smooth_hardware_faces']:
                o.data.polygons[i].use_smooth=True
                for li in o.data.polygons[i].loop_indices:o.data.edges[o.data.loops[li].edge_index].use_edge_sharp=False
        o.select_set(False)

# =============================================================== POSE (spec §1) — master curve from attempt 1, scaled to this pitch
CP = np.array([
    (-0.6, 0.15, 3.35), (0.25, 0.20, 3.62), (0.95, 0.25, 3.30), (1.20, 0.30, 2.45), (1.00, 0.38, 1.55), (0.55, 0.45, 0.85),
    (0.55, 0.55, 0.50), (1.40, 0.70, 0.50), (2.60, 0.10, 0.52), (2.70, -1.30, 0.52), (1.70, -2.20, 0.50),
    (0.00, -2.35, 0.50), (-1.70, -2.20, 0.50), (-3.00, -1.20, 0.50), (-3.00, 0.60, 0.50), (-1.80, 1.75, 0.50),
    (0.30, 3.05, 0.50), (2.70, 3.05, 0.50), (5.50, 1.50, 0.50), (5.90, -1.60, 0.50), (4.70, -3.90, 0.50),
    (3.00, -4.45, 0.50), (1.80, -4.55, 0.50), (0.70, -4.45, 0.50), (-0.40, -4.25, 0.50), (-1.40, -3.95, 0.50)])
G0 = 7; CP[G0:, 0] = .5 + (CP[G0:, 0] - .5) * .85; CP[G0:, 1] = -1.0 + (CP[G0:, 1] + 1.0) * .9
KS = PITCH / 1.03; CP = CP * KS; CP[:,0]*=.85; CP[:,1]*=.85; CP[:,2]*=.90; CP[:, 2] = np.maximum(CP[:, 2], 0.5)   # ground run stays at radius height
LOG["curve_scale"] = KS
LOG["refines"].append({"id":"R14-neck-pose","transport":"fixed lateral axis through upper neck, slerped to upright ground frame","coil_xy_scale":.85,"height_scale":.90,"instance_advance_fraction":.90})
def catmull(P, n=40):
    P = np.vstack([P[0] * 2 - P[1], P, P[-1] * 2 - P[-2]]); out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for tt in np.linspace(0, 1, n, endpoint=False):
            out.append(.5 * ((2 * p1) + (-p0 + p2) * tt + (2 * p0 - 5 * p1 + 4 * p2 - p3) * tt * tt + (-p0 + 3 * p1 - 3 * p2 + p3) * tt ** 3))
    out.append(P[-2]); return np.array(out)
C = catmull(CP); sl_ = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(C, axis=0), axis=1))])
def at(s0): return np.array([np.interp(s0, sl_, C[:, k]) for k in range(3)])
def frame(s0, ln):
    a = at(s0); b = at(s0 + ln); x = Vector(a - b).normalized(); up = Vector((0, 0, 1)); z = up - x * up.dot(x)
    if z.length < 1e-3: z = Vector((0, 1, 0))
    z.normalize(); y = z.cross(x)
    if s0 < 6*PITCH:
        yn=Vector((0,-1,0));yn=(yn-x*yn.dot(x)).normalized();zn=x.cross(yn)
        fac=max(0,min(1,(s0-4*PITCH)/(2*PITCH)))
        q0=Matrix((x,yn,zn)).transposed().to_quaternion();q1=Matrix((x,y,z)).transposed().to_quaternion()
        return q0.slerp(q1,fac).to_matrix().to_4x4(),Vector(a)
    return Matrix((x,y,z)).transposed().to_4x4(),Vector(a)
def node(src, name, M):
    ob = bpy.data.objects.new(name, src.data); SC.collection.objects.link(ob); ob.matrix_world = M; return ob
M, a = frame(0.0, 0.6); node(head, "Head_node", Matrix.Translation(a) @ M)
sp = 0.02; N_NECK, N_BODY = 6, 28
for i in range(N_BODY):
    src = nk if i < N_NECK else s
    M, a = frame(sp, PITCH); ob = node(src, f"Segment_{i+1:02d}", Matrix.Translation(a) @ M @ Matrix.Translation((-HX, 0, 0)))
    g = node(glow, f"Glow_{i+1:02d}", ob.matrix_world.copy()); sp += PITCH*.90
for k, (src, sl) in enumerate([(t1, .90), (t2, .80)]):
    M, a = frame(sp, PITCH * sl); ob = node(src, f"TailTaper_{k+1}", Matrix.Translation(a) @ M @ Matrix.Translation((-HX * sl, 0, 0)))
    if k == 0: node(g1, "Glow_T1", ob.matrix_world.copy())
    sp += PITCH * sl
M, a = frame(sp, LTIP); node(t, "TailTip_node", Matrix.Translation(a) @ M)
for o in [head, s, nk, glow, t1, t2, g1, t]: o.hide_render = o.hide_viewport = True; o.name = "SRC_" + o.name
vis = [o for o in SC.objects if o.type == "MESH" and not o.hide_render]
LOG["instanced_total_tris"] = sum(tris(o) for o in vis); LOG["n_nodes"] = len(vis)
LOG["module_plus_insert"] = LOG["tris"]["SegmentHero"] + LOG["tris"]["GlowInsert"]
print("LOG", json.dumps({k: LOG[k] for k in ("tris", "instanced_total_tris", "scales", "deviation")}), flush=True)
json.dump(LOG, open(os.path.join(WORK, "build-log.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, "snake-v2-r2-fix.blend"))
assert LOG['tris']['Head']<=14000
assert LOG['module_plus_insert']<=1450
assert LOG['tris']['tail_section_total']<=3000
assert 30000<=LOG['instanced_total_tris']<=57600
print('BUILD_DONE',flush=True)

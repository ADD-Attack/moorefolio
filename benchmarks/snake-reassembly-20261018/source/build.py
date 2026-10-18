"""snake-reassembly-20261018 — Round 2 coarse build (clay/simple materials).
blender -b --factory-startup -P build.py -- <ticket_dir_windows>
Units: D = 1.0 = body armour diameter. Blender Z-up; glTF export +Y up.
Module convention: local +X points toward the head; the joint housing + glow insert sit at the +X end.
"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix

T = sys.argv[sys.argv.index("--") + 1]
OUT = os.path.join(T, "r2"); os.makedirs(OUT, exist_ok=True)
CLAY = os.path.join(T, "clay")
LOG = {}
bpy.ops.wm.read_factory_settings(use_empty=True)
SC = bpy.context.scene

# ---------------------------------------------------------------- materials (clay / simple)
def mat(name, col, rough=.55, metal=0., emis=None, estr=0., alpha=1., trans=0.):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emis: b.inputs["Emission Color"].default_value = (*emis, 1); b.inputs["Emission Strength"].default_value = estr
    if trans: b.inputs["Transmission Weight"].default_value = trans
    if alpha < 1: b.inputs["Alpha"].default_value = alpha
    return m
M_CLAY = mat("clay", (.14, .14, .135), .45)
M_DARK = mat("clay_dark", (.10, .10, .10), .6)          # housing ring, recess backs, slot interiors
M_GLOW = mat("glow_teal", (.03, .3, .25), .4, emis=(.14, .62, .5), estr=2.2)
M_CORE = mat("eye_core", (.6, 1, .9), .3, emis=(.55, 1., .85), estr=9.)
M_IRIS = mat("eye_iris", (.0, .25, .18), .3, emis=(.004, .26, .16), estr=6.)
M_GLASS = mat("eye_cover", (1, 1, 1), .03, trans=1.)
MATS = [M_CLAY, M_DARK, M_GLOW, M_CORE, M_IRIS, M_GLASS]

# ---------------------------------------------------------------- mesh helpers
class Acc:
    """Accumulates geometry into one bmesh with per-face material index."""
    def __init__(s): s.bm = bmesh.new()
    def add_bm(s, bm2, mi=0, M=None):
        me = bpy.data.meshes.new("tmp"); bm2.to_mesh(me); bm2.free()
        if M: me.transform(M)
        for p in me.polygons: p.material_index = mi
        s.bm.from_mesh(me); bpy.data.meshes.remove(me)
    def obj(s, name, mats=MATS):
        me = bpy.data.meshes.new(name); s.bm.to_mesh(me); s.bm.free()
        for m in mats: me.materials.append(m)
        ob = bpy.data.objects.new(name, me); SC.collection.objects.link(ob)
        for p in me.polygons: p.use_smooth = False
        return ob

def lathe(prof, n, axis="X", a0=0., a1=2 * math.pi, cap=False):
    """prof: list of (x, r). Revolve around X. Returns bmesh."""
    bm = bmesh.new(); full = abs(a1 - a0 - 2 * math.pi) < 1e-6; cols = n if full else n + 1
    rings = []
    for j in range(cols):
        a = a0 + (a1 - a0) * j / n
        rings.append([bm.verts.new((x, r * math.cos(a), r * math.sin(a))) for x, r in prof])
    for j in range(n):
        A, B = rings[j], rings[(j + 1) % cols]
        for i in range(len(prof) - 1):
            vs = [A[i], A[i + 1], B[i + 1], B[i]]
            if len(set(vs)) == 4: bm.faces.new(vs)
    return bm

def box(c, s, M=None):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.)
    for v in bm.verts: v.co = Vector((v.co.x * s[0] + c[0], v.co.y * s[1] + c[1], v.co.z * s[2] + c[2]))
    if M:
        for v in bm.verts: v.co = M @ v.co
    return bm

def cyl(r, h, n, M=Matrix(), cap1=True, cap2=True):
    """Cylinder along local Z from 0..h."""
    bm = bmesh.new()
    a = [bm.verts.new((r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n), 0)) for i in range(n)]
    b = [bm.verts.new((v.co.x, v.co.y, h)) for v in a]
    for i in range(n): bm.faces.new([a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]])
    if cap1: bm.faces.new(list(reversed(a)))
    if cap2: bm.faces.new(b)
    for v in bm.verts: v.co = M @ v.co
    return bm

def frame_from(p, n, t=None):
    n = Vector(n).normalized(); t = Vector(t or (1, 0, 0)); t = (t - n * t.dot(n)).normalized(); b = n.cross(t)
    M = Matrix((t, b, n)).transposed().to_4x4(); M.translation = Vector(p); return M

def ntri(ob):
    ob.data.calc_loop_triangles(); return len(ob.data.loop_triangles)

# ---------------------------------------------------------------- panel builder in (u,v,h) param space
def panel(surf, u0, u1, v0, v1, t, holes=(), ustep=None, vstep=None, chamfer=.35, cut=None):
    """Raised plate over a param surface. surf(u,v,h)->Vector. Rect [u0,u1]x[v0,v1] minus rect holes.
    cut: optional list of (u,v) corner overrides {('u1v0'): (u,v)} for chamfered corners.
    Bottom faces removed (plate sits on the core). Returns bmesh in world/module coords."""
    us = {u0, u1}; vs = {v0, v1}
    for h in holes: us |= {h[0], h[1]}; vs |= {h[2], h[3]}
    if ustep:
        k = max(1, int(math.ceil((u1 - u0) / ustep))); us |= {u0 + (u1 - u0) * i / k for i in range(k + 1)}
    if vstep:
        k = max(1, int(math.ceil((v1 - v0) / vstep))); vs |= {v0 + (v1 - v0) * i / k for i in range(k + 1)}
    us = sorted(us); vs = sorted(vs)
    bm = bmesh.new(); V = {}
    def gv(i, j):
        if (i, j) not in V: V[(i, j)] = bm.verts.new((us[i], vs[j], 0.))
        return V[(i, j)]
    for i in range(len(us) - 1):
        for j in range(len(vs) - 1):
            cu = (us[i] + us[i + 1]) / 2; cv = (vs[j] + vs[j + 1]) / 2
            if any(h[0] < cu < h[1] and h[2] < cv < h[3] for h in holes): continue
            bm.faces.new([gv(i, j), gv(i + 1, j), gv(i + 1, j + 1), gv(i, j + 1)])
    if cut:
        for (uo, vo), (un, vn) in cut:
            for v in bm.verts:
                if abs(v.co.x - uo) < 1e-6 and abs(v.co.y - vo) < 1e-6: v.co.x, v.co.y = un, vn
    base = list(bm.faces)
    r = bmesh.ops.extrude_face_region(bm, geom=base)
    top_v = [e for e in r["geom"] if isinstance(e, bmesh.types.BMVert)]
    for v in top_v: v.co.z = t * (1 - chamfer)
    top_f = [f for f in bm.faces if f not in base and all(v.co.z > 1e-9 for v in f.verts)]
    bmesh.ops.delete(bm, geom=base, context="FACES_ONLY")
    if chamfer > 0:
        span = min(u1 - u0, v1 - v0)
        ins = bmesh.ops.inset_region(bm, faces=top_f, thickness=min(t * .6, span * .12), depth=0.)
        for f in top_f:
            for v in f.verts: v.co.z = t
    for v in bm.verts: v.co = surf(v.co.x, v.co.y, v.co.z)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def bolt(surf, u, v, h0, r=.022, n=5, hh=.018):
    p = surf(u, v, h0); q = surf(u, v, h0 + .01); nrm = (q - p).normalized()
    tng = (surf(u + .01, v, h0) - p)
    return cyl(r, hh, n, frame_from(p - nrm * .004, nrm, tng), cap1=False)

# ================================================================ BODY MODULE
L_DRUM, GAP = .85, .18; PITCH = L_DRUM + GAP; R_CORE, R_PL = .40, .44   # plates .44 -> .50 (t .06)
def cyl_surf(r):
    def f(x, phi, h):            # phi=0 faces -Y (camera side), +90deg = top; mirrored side via phi'=180-phi
        R = r + h; return Vector((x, -R * math.cos(phi), R * math.sin(phi)))
    return f
D2R = math.radians

def module(lite=False, neck=False, name="seg"):
    VS = 2.0 if lite else (0.95 if neck else 1.45)
    """lite: tail-variant (fewer fasteners/pistons, lower ring res). neck: heavier collar plating (B10)."""
    A = Acc(); S = cyl_surf(R_PL); hx = L_DRUM / 2
    nr = 10 if lite else 12
    # core drum (open tube; ends covered by housing / neighbour housing)
    A.add_bm(lathe([(-hx - .01, R_CORE), (hx + .01, R_CORE)], nr), 1)
    for side in (0, 1):
        def P(x, ph, h, side=side):          # mirror: side 1 = +Y side
            return S(x, ph if side == 0 else math.pi - ph, h)
        def deg(a): return D2R(a)
        T0 = .075
        if not neck:
            # B2 upper stepped shield: full upper plate with lower-right notch, top grille hole (B3)
            hole_top = (-.14, .13, deg(36), deg(47))
            A.add_bm(panel(P, -hx, hx, deg(28), deg(89.5), T0, holes=[hole_top], vstep=deg(13*VS)), 0)
            A.add_bm(panel(P, -hx, .07, deg(1), deg(28), T0, vstep=deg(14*VS),
                           cut=[((.07, deg(28)), (.10, deg(28))), ((.07, deg(1)), (.07, deg(1)))]), 0)
            # notch: lower second level with grille (B3)
            A.add_bm(panel(P, .10, hx, deg(2), deg(26), T0 * .55, holes=[(.14, .38, deg(8), deg(22))], vstep=deg(12*VS)), 0)
            # B2 raised top tab
            A.add_bm(panel(lambda x, p, h: P(x, p, h + T0), -.20, .14, deg(50), deg(77), .035, vstep=deg(14*VS), chamfer=0), 0)
            if not lite:
                for (a, b, c, e), base in [(hole_top, T0), ((.14, .38, deg(8), deg(22)), T0 * .55)]:
                    A.add_bm(panel(lambda x, p, h, base=base: P(x, p, h + base), a - .03, b + .03, c - deg(3.5), e + deg(3.5), .022,
                                   holes=[(a, b, c, e)], chamfer=0), 0)
            # grille backplates (recessed, dark)
            for (a, b, c, d) in [hole_top, (.14, .38, deg(8), deg(22))]:
                A.add_bm(panel(lambda x, p, h: P(x, p, h - .03), a, b, c, d, .005, chamfer=0), 1)
            # B4 waist band strip + B5 bracket blocks + centre grille slot (B3)
            A.add_bm(panel(P, -hx, hx, deg(-4), deg(0.5), .025, chamfer=0), 0)
            if not lite:
                A.add_bm(panel(P, -.16, .26, deg(-34), deg(-9), .045, holes=[(-.06, .17, deg(-30), deg(-14))], vstep=deg(12*VS)), 0)
                A.add_bm(panel(lambda x, p, h: P(x, p, h - .03), -.06, .17, deg(-30), deg(-14), .005, chamfer=0), 1)
                for bx in ((-.13, -.06), (.17, .24)):
                    A.add_bm(panel(lambda x, p, h: P(x, p, h + .045), bx[0], bx[1], deg(-36), deg(-8), .035, chamfer=0), 0)
            # B6 lower plate with inset raised panel
            A.add_bm(panel(P, -hx + .05, hx, deg(-89.5), deg(-36), T0, vstep=deg(13*VS)), 0)
        else:
            # B10 neck variant: heavier overlapping collar bands + big flat side panel
            A.add_bm(panel(P, -hx, hx, deg(40), deg(90), .07, vstep=deg(12*VS)), 0)
            A.add_bm(panel(lambda x, p, h: P(x, p, h + .07), -hx + .04, hx - .25, deg(48), deg(90), .04, vstep=deg(14*VS)), 0)
            A.add_bm(panel(P, -hx, hx - .05, deg(-20), deg(38), .085, holes=[(.12, .34, deg(4), deg(22))], vstep=deg(12*VS)), 0)
            A.add_bm(panel(lambda x, p, h: P(x, p, h - .03), .12, .34, deg(4), deg(22), .005, chamfer=0), 1)
            A.add_bm(panel(P, -hx + .03, hx, deg(-90), deg(-22), .07, vstep=deg(14*VS)), 0)
            A.add_bm(panel(lambda x, p, h: P(x, p, h + .07), -.25, .05, deg(-60), deg(-30), .03), 0)
        # B4 twin pistons (axial, at each end of waist band)
        ph = D2R(-13); pist = [(-hx - .02, -.21), (.21, hx + .02)] if not lite else [(.21, hx + .02)]
        if not neck:
            p = P(0, ph, .045); y, z = p.y, p.z
            ROT = Matrix.Rotation(math.pi / 2, 4, "Y")     # local Z -> +X
            for (xa, xb) in pist:
                # piston barrel on the drum-centre side, rod + end fitting toward the joint
                ln = xb - xa; rod = ln * .45; barrel = ln - rod
                if xa < 0:   # -X end: joint side is xa
                    A.add_bm(cyl(.046, barrel, 5, Matrix.Translation((xa + rod, y, z)) @ ROT), 0)
                    A.add_bm(cyl(.022, rod, 5, Matrix.Translation((xa, y, z)) @ ROT, False, False), 0)
                    A.add_bm(box((xa + .015, y, z), (.03, .075, .075)), 0)
                else:        # +X end: joint side is xb
                    A.add_bm(cyl(.046, barrel, 5, Matrix.Translation((xa, y, z)) @ ROT), 0)
                    A.add_bm(cyl(.022, rod, 5, Matrix.Translation((xa + barrel, y, z)) @ ROT, False, False), 0)
                    A.add_bm(box((xb - .015, y, z), (.03, .075, .075)), 0)
        # B7 fasteners
        if not lite:
            bl = [(-.36, 70), (.33, 70), (.36, -50)] if not neck else \
                 [(-.36, 60), (.3, 64), (-.3, 26), (.0, 10), (-.33, -40), (.33, -40)]
            for (bx, bd) in bl:
                A.add_bm(bolt(P, bx, D2R(bd), .06 if not neck else .075), 0)
    # top & bottom spine plates (bridge between sides)
    if neck:   # B10: heavy overlapping collar bands at both drum ends (reference neck read)
        for (xa, xb) in ((-hx - .02, -hx + .13), (hx - .13, hx + .02)):
            A.add_bm(lathe([(xa, .44), (xa, .545), (xa + .02, .56), (xb - .02, .56), (xb, .545), (xb, .44)], 16), 0)
    # B8 joint housing ring (+X end)
    x0, x1 = hx, hx + GAP
    prof = [(x0, .47), (x0 + .035, .47), (x0 + .045, .418), (x1 - .045, .418), (x1 - .035, .47), (x1, .47)]
    A.add_bm(lathe(prof, 16 if not lite else 14), 1)
    return A.obj(name)

def glow_insert(name="glow", nb=26, scale=1.):
    """B9 segmented emissive bars: separate insert mesh, sits in the housing channel."""
    A = Acc(); x0, x1 = L_DRUM / 2 + .045, L_DRUM / 2 + GAP - .045
    for i in range(nb):
        a0 = 2 * math.pi * i / nb + .006; a1 = 2 * math.pi * (i + 1) / nb - .022
        A.add_bm(lathe([(x0, .428), (x1, .428)], 1, a0=a0, a1=a1), 2)
        # bar side walls (thin) so bars read as raised from the channel
    # dark ribs are the channel floor showing between bars (housing material)
    ob = A.obj(name)
    return ob

# ================================================================ HEAD (clay-driven massing)
def clay_head_profile():
    """Import clay head; cut at collar plane; per-station width / zmin / zmax (excluding crest)."""
    bpy.ops.import_scene.gltf(filepath=os.path.join(CLAY, "hunyuan-head.glb"))
    ob = [o for o in SC.objects if o.type == "MESH"][-1]
    co = np.empty(len(ob.data.vertices) * 3); ob.data.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    co = co @ np.array(ob.matrix_world.to_3x3()).T + np.array(ob.matrix_world.translation)
    bpy.data.objects.remove(ob)
    xs = np.linspace(-.97, -.22, 16); prof = []
    for x in xs:
        m = (np.abs(co[:, 0] - x) < .025) & (co[:, 2] > .05)
        c = co[m]; side = c[np.abs(c[:, 1]) > .08]
        prof.append(dict(x=float(x), w=float(np.percentile(np.abs(c[:, 1]), 99)), z0=float(np.percentile(c[:, 2], 1)),
                         z1=float(np.percentile(side[:, 2], 99)) if len(side) else float(np.percentile(c[:, 2], 99))))
    return prof

HEAD_H = 1.40; HEAD_L = 1.45 * HEAD_H
def build_head():
    prof = clay_head_profile(); LOG["clay_head_profile"] = prof
    # normalise clay stations: u=0 rear (collar) -> u=1 snout; rescale to reference L,H (P3)
    hmax = max(p["z1"] - p["z0"] for p in prof)
    st = []
    for p in reversed(prof):   # clay snout is -X; reverse so u runs rear->snout
        st.append((p["w"] / hmax * HEAD_H, (p["z1"] - p["z0"]) / hmax * HEAD_H, (p["z1"] + p["z0"]) / 2 / hmax * HEAD_H))
    st = np.array(st); us = np.linspace(0, 1, len(st))
    # crown: reference crown slopes ~10deg down to the snout -> take clay top, enforce flat crown
    # reference template (spec §2): near-constant height to u~.55 then taper to .72H at the snout; width .62H -> .46H
    tmpl = np.array([(HEAD_H * (.31 - .09 * u), HEAD_H * (1.0 - .42 * max(0, u - .45) / .55), HEAD_H * (.5 - .05 * u)) for u in us])
    st = .25 * st + .75 * tmpl; LOG["head_station_blend"] = "0.25 clay + 0.75 reference template (clay rear stations carry neck mass, D-H1)"
    st[:, 2] -= st[0, 2]                                  # rear section centre sits on the master curve
    def interp(u, k): return float(np.interp(u, us, st[:, k]))
    def vt(t): return math.copysign(math.asin(min(1, abs(t)) ** 2.5), t)   # relative height t -> superellipse param v
    def sec(u, v, h):
        """superellipse section (boxy). v in [-pi,pi], 0 = -Y side mid, pi/2 = top."""
        hw = interp(u, 0) * .92; hh = interp(u, 1) / 2; zc = interp(u, 2)
        if u > .86:
            k = max(.42, math.sqrt(max(0., 1 - ((u - .86) / .14) ** 2))); hw *= k; hh = hh * (.35 + .65 * k)
        e = 2 / 5.0
        c, s = math.cos(v), math.sin(v)
        y = -(hw + h) * math.copysign(abs(c) ** e, c); z = zc + (hh + h) * math.copysign(abs(s) ** e, s)
        return Vector((u * HEAD_L, y, z))
    A = Acc()
    # core loft
    NU, NV = 30, 44
    bm = bmesh.new(); G = [[bm.verts.new(sec(i / (NU - 1) * .985, -math.pi + 2 * math.pi * j / NV, 0)) for j in range(NV)] for i in range(NU)]
    for i in range(NU - 1):
        for j in range(NV): bm.faces.new([G[i][j], G[i][(j + 1) % NV], G[i + 1][(j + 1) % NV], G[i + 1][j]])
    tip = bm.verts.new(Vector((HEAD_L * .995, 0, interp(1, 2))))
    for j in range(NV): bm.faces.new([G[-1][j], G[-1][(j + 1) % NV], tip])
    A.add_bm(bm, 1)
    S = sec; d = D2R
    # H2 plates: rows (crown, upper cheek, mid cheek, jaw) x columns along u with seams
    seam = .012
    rows = [(d(62), d(118), [(0, .2), (.2, .45), (.45, .7), (.7, .88), (.88, 1.)]),          # crown (centre)
            (d(28), d(62), [(0, .28), (.28, .42), (.6, .78), (.78, .99)]),                     # upper cheek L
            (d(118), d(152), [(0, .28), (.28, .42), (.6, .78), (.78, .99)]),                   # upper cheek R
            (d(-8), d(28), [(0, .04), (.25, .34), (.60, .8), (.8, 1.)]),                        # mid cheek L (eye gap .34-.60, vent .04-.25)
            (d(152), d(188), [(0, .04), (.25, .34), (.60, .8), (.8, 1.)]),                      # mid cheek R
            (d(-40), d(-15), [(0, .3), (.3, .55), (.55, .8), (.8, 1.)]),                       # upper jaw L (mouth line above, H3)
            (d(195), d(220), [(0, .3), (.3, .55), (.55, .8), (.8, 1.)]),                       # upper jaw R
            (d(-80), d(-46), [(.05, .35), (.35, .62), (.62, .85), (.85, .98)]),                # lower jaw L (two-tier, H3)
            (d(226), d(260), [(.05, .35), (.35, .62), (.62, .85), (.85, .98)]),
            (d(-100), d(-80), [(.05, .5), (.5, .97)]), (d(260), d(280), [(.05, .5), (.5, .97)])]
    for (v0, v1, cols) in rows:
        for (a, b) in cols:
            A.add_bm(panel(S, a + seam, min(b, .985) - seam, v0 + seam * 2, v1 - seam * 2, .035, ustep=.09, vstep=d(10)), 0)
    # eye ring frame plates around the eye socket (cheek gap u .38-.66, v -8..28)
    EU, EV = .47, vt(.12)
    for sgn in (1, -1):
        vv = EV if sgn > 0 else math.pi - EV
        A.add_bm(panel(S, .34, .60, (d(-8) if sgn > 0 else math.pi - d(28)) + .02, (d(28) if sgn > 0 else math.pi + d(8)) - .02, .015, ustep=.06, vstep=d(8), chamfer=0), 0)
    # H5 crest fins x3 (swept back, lean ~32deg), on the crown centreline
    for k, (uc, hgt) in enumerate([(.56, .42), (.38, .48), (.20, .43)]):
        top = S(uc, d(90), .035).z - .01
        x = uc * HEAD_L; ln = .34; ft = x + ln / 2 - hgt * math.tan(d(30))
        pts = [(x + ln / 2, top), (x - ln / 2, top), (x - ln / 2 - hgt * .15, top + hgt), (ft, top + hgt * .97)]
        bm = bmesh.new(); th = .045
        th = .075   # plated blade: thick root, thinner tip edge
        L = [bm.verts.new((px, -th / 2 * (1 - .45 * (pz - top) / hgt), pz)) for px, pz in pts]; R = [bm.verts.new((px, th / 2 * (1 - .45 * (pz - top) / hgt), pz)) for px, pz in pts]
        bm.faces.new(L); bm.faces.new(list(reversed(R)))
        for i in range(4): bm.faces.new([L[i], L[(i + 1) % 4], R[(i + 1) % 4], R[i]])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces); A.add_bm(bm, 0)
        A.add_bm(panel(S, uc - .07, uc + .07, d(80), d(100), .025, chamfer=0), 0)   # riveted root plate
        for sg in (-1, 1): A.add_bm(bolt(S, uc + .05 * sg, d(84), .06, r=.016), 0)
    # H6 eye lens assembly x2 (radial profile per spec §2: lit r35 of r60 assembly -> scale)
    R_ASM = .34 * HEAD_H / 2; kpx = R_ASM / 60.
    for sgn in (1, -1):
        vv = EV if sgn > 0 else math.pi - EV
        p = S(EU, vv, .0); q = S(EU, vv, .05); nrm = (q - p).normalized()
        Mf = frame_from(p + nrm * .04, nrm, (1, 0, 0)) @ Matrix.Rotation(-math.pi / 2, 4, "Y")  # lathe X -> normal
        def rk(px): return px * kpx
        # outer metal ring r55-60, dark groove r50-55, light lip r45-50, dark bezel r35-45 (h along normal)
        ring = [(-.02, rk(62)), (.035, rk(61)), (.05, rk(56)), (.03, rk(53)), (.045, rk(50)), (.05, rk(46)), (.025, rk(44)), (.0, rk(36))]
        A.add_bm(lathe(ring, 40), 0, Mf)
        A.add_bm(lathe([(.0, rk(36)), (-.03, rk(34)), (-.03, rk(1))], 40), 1, Mf)     # dark bezel bowl
        # aperture blades (recessed, behind core): 8 slanted thin blades
        for b in range(8):
            a = 2 * math.pi * b / 8
            bm = bmesh.new(); r0, r1 = rk(18), rk(34)
            vs = [bm.verts.new((-.022, r0 * math.cos(a), r0 * math.sin(a))), bm.verts.new((-.022, r1 * math.cos(a + .2), r1 * math.sin(a + .2))),
                  bm.verts.new((-.018, r1 * math.cos(a + .95), r1 * math.sin(a + .95))), bm.verts.new((-.018, r0 * math.cos(a + .75), r0 * math.sin(a + .75)))]
            bm.faces.new(vs); A.add_bm(bm, 1, Mf)
        # iris (saturated rim r25-35), teal r20-25 / mint r10-20, white core r0-10 (emissive discs, layered)
        A.add_bm(lathe([(-.012, rk(35)), (-.012, rk(22))], 40), 4, Mf)
        A.add_bm(lathe([(-.009, rk(22)), (-.009, rk(10))], 40), 3, Mf)
        A.add_bm(lathe([(-.006, rk(10)), (-.006, 0.0005)], 20), 3, Mf)
        # curved optical cover
        cov = [(rk(36) * .0 + .005 + .03 * (1 - (i / 6) ** 2), rk(36) * i / 6) for i in range(7)]
        A.add_bm(lathe(list(reversed(cov)), 40), 5, Mf)
    # H7 cheek vent box + slats, H8 piston rod back into collar
    for sgn in (1, -1):
        vv = vt(.02) if sgn > 0 else math.pi - vt(.02)
        p = S(.15, vv, .035); q = S(.20, vv, .1); nrm = (q - p).normalized(); Mf = frame_from(p, nrm, (1, 0, 0))
        A.add_bm(box((0, 0, .06), (.36, .32, .12), Mf), 0)
        A.add_bm(box((0, 0, .122), (.29, .25, .006), Mf), 1)
        for k in range(6): A.add_bm(box((0, -.105 + k * .042, .13), (.28, .018, .022), Mf), 0)
        A.add_bm(cyl(.03, .32, 6, Mf @ Matrix.Translation((-.12, 0, .05)) @ Matrix.Rotation(-math.pi / 2, 4, "Y")), 0)
    # H4 nostril slot (dark recess) + H3 jaw seam groove (dark strip under the plates)
    for sgn in (1, -1):
        vv = vt(-.18) if sgn > 0 else math.pi - vt(-.18)
        p = S(.88, vv, .04); q = S(.9, vv, .1); nrm = (q - p).normalized(); Mf = frame_from(p, nrm, (1, 0, 0))
        A.add_bm(box((0, 0, .012), (.20, .045, .02), Mf), 1)
    # H9 inset panels: upper-rear window slot, placard, collar-top vent
    for sgn in (1, -1):
        vv = d(48) if sgn > 0 else math.pi - d(48)
        A.add_bm(panel(lambda u, v, h: S(u, v, h + .035), .28, .36, vv - d(4), vv + d(4), .02), 0)
        A.add_bm(panel(lambda u, v, h: S(u, v, h + .035 - .03), .29, .35, vv - d(2.5), vv + d(2.5), .004, chamfer=0), 1)
        vp = d(-22) if sgn > 0 else math.pi + d(22)
        A.add_bm(panel(lambda u, v, h: S(u, v, h + .035), .34, .43, vp - d(5), vp + d(5), .015), 0)
    # H10 head-neck collar (stacked multi-plate bands, boxed top fitting) at the rear (u<0)
    zc0 = interp(0, 2)
    for k, (x0, x1, r) in enumerate([(-.16, .04, .50), (-.30, -.14, .48), (-.42, -.28, .46)]):
        A.add_bm(lathe([(x1, .30), (x1, r), (x1 - .02, r + .02), (x0 + .02, r + .02), (x0, r), (x0, .30)], 32), 0,
                 Matrix.Translation((0, 0, zc0)))
    A.add_bm(lathe([(.06, .0), (.06, .62 * HEAD_H / 2), (.0, .64 * HEAD_H / 2)], 32), 1, Matrix.Translation((0, 0, zc0)))  # rear bulkhead
    A.add_bm(box((-.18, 0, zc0 + .52), (.18, .14, .1)), 0)
    for k in range(3): A.add_bm(box((-.23 + k * .05, 0, zc0 + .572), (.025, .1, .012)), 1)
    ob = A.obj("Head")
    return ob

# ================================================================ TAIL TIP (clay-driven profile)
def clay_tail_tip_profile():
    bpy.ops.import_scene.gltf(filepath=os.path.join(CLAY, "hunyuan-tail.glb"))
    ob = [o for o in SC.objects if o.type == "MESH"][-1]
    co = np.empty(len(ob.data.vertices) * 3); ob.data.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    co = co @ np.array(ob.matrix_world.to_3x3()).T + np.array(ob.matrix_world.translation)
    bpy.data.objects.remove(ob)
    co = co[co[:, 2] > co[:, 2].min() + .04]          # D-T1: drop the fused ground slab
    # finned tip: bottom-right in top view; take points beyond the cone base along its axis (PCA of tip region)
    tipc = co[(co[:, 1] < -.35)]
    c0 = tipc.mean(0); u, s, vt = np.linalg.svd(tipc - c0, full_matrices=False); ax = vt[0]
    t = (tipc - c0) @ ax
    if np.percentile(t, 99) < -np.percentile(t, 1): ax = -ax; t = -t   # point toward the nose (furthest extent)
    rr = np.linalg.norm((tipc - c0) - np.outer(t, ax), axis=1)
    tn = np.linspace(np.percentile(t, 2), t.max(), 12); out = []
    for a, b in zip(tn[:-1], tn[1:]):
        m = (t >= a) & (t < b)
        out.append(float(np.percentile(rr[m], 60)) if m.sum() > 20 else 0.)
    return out

def build_tail_tip(rbase):
    prof = clay_tail_tip_profile(); LOG["clay_tail_tip_radius_profile"] = prof
    A = Acc(); Ltip = 2.75 * 2 * rbase
    # torpedo lathe: base r -> slight swell -> taper -> blunt nose with nozzle hole (T2)
    pr = [(0, R_CORE * .0 + rbase * .82), (.0, rbase), (.18 * Ltip, rbase * 1.04), (.45 * Ltip, rbase * .98), (.70 * Ltip, rbase * .80),
          (.86 * Ltip, rbase * .55), (.95 * Ltip, rbase * .34), (.985 * Ltip, rbase * .22), (.99 * Ltip, rbase * .10), (.96 * Ltip, rbase * .08)]
    pr = [(-x, r) for x, r in pr]   # nose toward -X (away from head)
    A.add_bm(lathe(pr, 18), 0)
    # plate seam bands
    for xs in (.58,):
        A.add_bm(lathe([(-xs * Ltip + .02, rbase * 1.0), (-xs * Ltip + .02, rbase * 1.06), (-xs * Ltip - .04, rbase * 1.06), (-xs * Ltip - .04, rbase * .99)], 20), 0)
    # T3 dorsal swept fin with notched trailing edge; T4 paired lateral/ventral fins
    def fin(M, hgt, ln):
        bm = bmesh.new(); th = .035
        pts = [(0, 0), (-ln, 0), (-ln * .45 - hgt * .5, hgt), (-ln * .2 - hgt * .5, hgt), (-ln * .12, hgt * .55), (.05, hgt * .45)]
        L = [bm.verts.new((x, -th / 2, z)) for x, z in pts]; R = [bm.verts.new((x, th / 2, z)) for x, z in pts]
        bm.faces.new(L); bm.faces.new(list(reversed(R)))
        for i in range(len(pts)): bm.faces.new([L[i], L[(i + 1) % len(pts)], R[(i + 1) % len(pts)], R[i]])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm2 = bm
        for v in bm2.verts: v.co = M @ v.co
        return bm2
    xf = -.22 * Ltip
    A.add_bm(fin(Matrix.Translation((xf, 0, rbase * .95)), rbase * .9, .38), 0)
    for ang in (-140, -40):
        A.add_bm(fin(Matrix.Rotation(D2R(ang - 90), 4, "X") @ Matrix.Translation((xf - .05, 0, rbase * .9)), rbase * .75, .34), 0)
    # T5 grille vents: upper-flank large (7 slats), small near nose
    for (xc, ang, w, h, n) in [(-.45 * Ltip, 35, .30, .16, 7), (-.80 * Ltip, 15, .14, .08, 4)]:
        a = D2R(ang); rr = float(np.interp(-xc, [-x for x, _ in pr[::-1]], [r for _, r in pr[::-1]])) if False else rbase * (1.0 if ang > 20 else .62)
        p = Vector((xc, -rr * math.cos(a), rr * math.sin(a))); nrm = Vector((0, -math.cos(a), math.sin(a)))
        Mf = frame_from(p, nrm, (1, 0, 0))
        A.add_bm(box((0, 0, .0), (w + .04, h + .04, .03), Mf), 0)
        A.add_bm(box((0, 0, .016), (w, h, .004), Mf), 1)
        for k in range(n): A.add_bm(box((0, -h / 2 + (k + .5) * h / n, .024), (w, h / n * .45, .012), Mf), 0)
    # joint housing at the headward (+X) end of the tip
    A.add_bm(lathe([(-.01, rbase * .80), (0, rbase * .98), (.03, rbase * .98), (.04, rbase * .93), (.14, rbase * .93), (.15, rbase * .98), (.18, rbase * .98)], 14), 1)
    ob = A.obj("TailTip")
    g = Acc(); nb = 16
    for i in range(nb):
        a0 = 2 * math.pi * i / nb + .02; a1 = 2 * math.pi * (i + 1) / nb - .07
        g.add_bm(lathe([(.045, rbase * .945), (.135, rbase * .945)], 1, a0=a0, a1=a1), 2)
    gl = g.obj("TailTipGlow")
    return ob, gl, Ltip

def taper(ob, s0, s1, sl, port=False):
    """Tapered hero-module variant: scale YZ linearly along X from s0 (tail end -X) to s1 (head end +X)."""
    me = ob.data; xs = [v.co.x for v in me.vertices]; xa, xb = min(xs), max(xs)
    for v in me.vertices:
        k = (v.co.x - xa) / (xb - xa); s = s0 + (s1 - s0) * k
        v.co.y *= s; v.co.z *= s; v.co.x *= sl
    if port:
        A = Acc(); p = Vector((0, -.5 * (s0 + s1) / 2 - .005, .02)); Mf = frame_from(p, (0, -1, 0), (1, 0, 0))
        A.add_bm(lathe([(0, .09), (.03, .09), (.035, .07), (.02, .05), (.02, .0)], 12), 0, Mf @ Matrix.Rotation(-math.pi / 2, 4, "Y"))
        po = A.obj("tmpport");
        bm = bmesh.new(); bm.from_mesh(me); bm.from_mesh(po.data); bm.to_mesh(me); bm.free(); bpy.data.objects.remove(po)
    return ob

# ================================================================ BUILD SECTIONS
seg = module(name="SegmentHero")
neck = module(neck=True, name="SegmentNeck")
glow = glow_insert("GlowInsert")
t1 = taper(module(lite=True, name="TailTaper1"), .70, .86, .90, port=True)
t2 = taper(module(lite=True, name="TailTaper2"), .52, .70, .80)
g1 = glow_insert("GlowInsertT1", 16); taper(g1, .70, .86, .90)
g2 = glow_insert("GlowInsertT2", 16); taper(g2, .52, .70, .80)
tip, tipglow, LTIP = build_tail_tip(.5 * .52)
head = build_head()
for o in [seg, neck, glow, t1, t2, g1, g2, tip, tipglow, head]: o.hide_render = o.hide_viewport = False
counts = {o.name: ntri(o) for o in [seg, neck, glow, t1, t2, g1, g2, tip, tipglow, head]}
LOG["tris_per_mesh"] = counts; print("COUNTS", counts, flush=True)

# ================================================================ MASTER CURVE (spec §1 pose)
CP = np.array([
    (-0.6, 0.15, 3.35), (0.25, 0.20, 3.62), (0.95, 0.25, 3.30), (1.20, 0.30, 2.45), (1.00, 0.38, 1.55), (0.55, 0.45, 0.85),
    (0.55, 0.55, 0.50),                                   # neck base on the ground at the coil centre
    (1.40, 0.70, 0.50), (2.60, 0.10, 0.52), (2.70, -1.30, 0.52), (1.70, -2.20, 0.50),   # inner right turn (rises slightly)
    (0.00, -2.35, 0.50), (-1.70, -2.20, 0.50),            # front run (-X)
    (-3.00, -1.20, 0.50), (-3.00, 0.60, 0.50), (-1.80, 1.75, 0.50),  # left turn going back
    (0.30, 3.05, 0.50), (2.70, 3.05, 0.50),               # back-left run passes behind the neck base (outer lap)
    (5.50, 1.50, 0.50), (5.90, -1.60, 0.50), (4.70, -3.90, 0.50),     # outer right turn coming forward (lower run)
    (3.00, -4.45, 0.50), (1.80, -4.55, 0.50), (0.70, -4.45, 0.50), (-0.40, -4.25, 0.50), (-1.40, -3.95, 0.50)])  # tail curl, tip pointing -X toward viewer
G0 = 7   # ground control points start; compact the coil toward the reference footprint (spec §1)
CP[G0:, 0] = .5 + (CP[G0:, 0] - .5) * .85; CP[G0:, 1] = -1.0 + (CP[G0:, 1] + 1.0) * .9
def catmull(P, n=40):
    P = np.vstack([P[0] * 2 - P[1], P, P[-1] * 2 - P[-2]]); out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-2]); return np.array(out)
C = catmull(CP); sl = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(C, axis=0), axis=1))])
def at(s): return np.array([np.interp(s, sl, C[:, k]) for k in range(3)])
LOG["curve_length"] = float(sl[-1])

nodes = []
def place(src, glow_src, s0, pitch_len, name, parent=None):
    """Rigid node: local +X toward head along the chord between this module's head end (s0) and tail end."""
    a = at(s0); b = at(s0 + pitch_len); x = Vector(a - b).normalized()
    up = Vector((0, 0, 1)); z = (up - x * up.dot(x))
    if z.length < 1e-3: z = Vector((0, 1, 0))
    z.normalize(); y = z.cross(x)
    M = Matrix((x, y, z)).transposed().to_4x4()
    ob = bpy.data.objects.new(name, src.data); SC.collection.objects.link(ob)
    return ob, M, a

# Head: rear at s=0, snout forward along -T
_, Mh, ah = place(head, None, 0.0, .6, "tmp")
bpy.data.objects.remove(bpy.data.objects["tmp"])
H = bpy.data.objects.new("Head_node", head.data); SC.collection.objects.link(H)
H.matrix_world = Matrix.Translation(Vector(ah)) @ Mh
head.hide_render = True; head.hide_viewport = True

s = 0.30; N_NECK = 6; N_BODY = 28
for i in range(N_BODY):
    src = neck if i < N_NECK else seg
    ob, M, a = place(src, glow, s, PITCH, f"Segment_{i+1:02d}")
    hx = L_DRUM / 2 + GAP          # module head end (ring outer face) sits on curve at s
    ob.matrix_world = Matrix.Translation(Vector(a)) @ M @ Matrix.Translation((-hx, 0, 0))
    gi = bpy.data.objects.new(f"Glow_{i+1:02d}", glow.data); SC.collection.objects.link(gi); gi.parent = ob
    nodes.append(ob); s += PITCH
for k, (src, gsrc, sl_) in enumerate([(t1, g1, .90), (t2, g2, .80)]):
    ob, M, a = place(src, gsrc, s, PITCH * sl_, f"TailTaper_{k+1}")
    ob.matrix_world = Matrix.Translation(Vector(a)) @ M @ Matrix.Translation((-(L_DRUM / 2 + GAP) * sl_, 0, 0))
    gi = bpy.data.objects.new(f"Glow_T{k+1}", gsrc.data); SC.collection.objects.link(gi); gi.parent = ob
    nodes.append(ob); s += PITCH * sl_
ob, M, a = place(tip, tipglow, s, LTIP, "TailTip_node")
ob.matrix_world = Matrix.Translation(Vector(a)) @ M @ Matrix.Translation((-.19, 0, 0))
gi = bpy.data.objects.new("Glow_Tip", tipglow.data); SC.collection.objects.link(gi); gi.parent = ob
nodes.append(ob); s += LTIP + .19
LOG["arc_used"] = s
for o in [seg, neck, glow, t1, t2, g1, g2, tip, tipglow]: o.hide_render = o.hide_viewport = True; o.name = "SRC_" + o.name

inst = sum(ntri(o) for o in SC.objects if o.type == "MESH" and not o.hide_render)
LOG["instanced_total_tris"] = inst; LOG["n_nodes"] = len([o for o in SC.objects if o.type == "MESH" and not o.hide_render])
LOG["tip_world"] = list(bpy.data.objects["TailTip_node"].matrix_world.translation); LOG["head_world"] = list(H.matrix_world.translation)
print("TIP", LOG["tip_world"], "HEAD", LOG["head_world"])
print("INST", inst, "ARC", s, "CURVE", sl[-1], flush=True)
with open(os.path.join(OUT, "build-log.json"), "w") as f: json.dump(LOG, f, indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "snake-r2.blend"))
print("BUILD_DONE", flush=True)

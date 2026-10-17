"""Goblin bake-off build script — Blender 4.5 (headless).

Usage:
  blender -b --factory-startup --python build.py -- [preview|head] [out.png]

Builds the whole scene procedurally (metaball anatomy -> mesh, bmesh props,
node-based PBR materials, three-point studio lighting) and renders with Cycles.
"""
import bpy, bmesh, math, random, sys
import numpy as np
from mathutils import Vector as V, Matrix, Quaternion

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
PREVIEW = 'preview' in argv
HEADCAM = 'head' in argv
OUT = next((a for a in argv if a.endswith('.png')), '//render.png')
rng = random.Random(11)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
COL = scene.collection


def link(ob):
    COL.objects.link(ob)
    return ob


def frame(u, v):
    """Orthonormal frame quaternion: local X->u, local Y->v (orthogonalised), Z=u x v."""
    u = V(u).normalized()
    v = (V(v) - u * u.dot(V(v))).normalized()
    w = u.cross(v)
    return Matrix((u, v, w)).transposed().to_quaternion()


# ----------------------------------------------------------------------------
# Metaball anatomy helper (visible radius = 0.575 * influence radius at stiffness 2)
# ----------------------------------------------------------------------------
K = 1 / 0.575


class Meta:
    def __init__(self, name, res):
        self.mb = bpy.data.metaballs.new(name)
        self.mb.resolution = res
        self.mb.render_resolution = res
        self.mb.threshold = 0.6
        self.obj = link(bpy.data.objects.new(name, self.mb))

    def _el(self, kind, p, R, neg=False, stiff=2.0):
        e = self.mb.elements.new(type=kind)
        e.co = V(p)
        e.radius = R * K
        e.stiffness = stiff
        e.use_negative = neg
        return e

    def ball(self, p, R, **kw):
        return self._el('BALL', p, R, **kw)

    def ell(self, p, axes, rot=None, **kw):
        R = max(axes)
        e = self._el('ELLIPSOID', p, R, **kw)
        e.size_x, e.size_y, e.size_z = (a / R for a in axes)
        if rot is not None:
            e.rotation = rot
        return e

    def cap(self, a, b, R, **kw):
        a, b = V(a), V(b)
        d = b - a
        e = self._el('CAPSULE', (a + b) / 2, R, **kw)
        e.size_x = d.length / 2
        e.rotation = V((1, 0, 0)).rotation_difference(d.normalized())
        return e

    def to_mesh(self, name, smooth_iter=2):
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(self.obj.evaluated_get(dg))
        me.name = name
        bpy.data.objects.remove(self.obj)
        ob = link(bpy.data.objects.new(name, me))
        me.shade_smooth()
        if smooth_iter:
            m = ob.modifiers.new('smooth', 'SMOOTH')
            m.factor = 0.5
            m.iterations = smooth_iter
        return ob


# ----------------------------------------------------------------------------
# bmesh helpers
# ----------------------------------------------------------------------------
def mesh_obj(name, bm, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        me.shade_smooth()
    return link(bpy.data.objects.new(name, me))


def tube(name, rings, close_start=False, close_end=False, closed_ring=True, smooth=True):
    """Skin a list of vertex rings (equal length) into a quad tube."""
    bm = bmesh.new()
    vr = [[bm.verts.new(p) for p in r] for r in rings]
    n = len(rings[0])
    span = n if closed_ring else n - 1
    for a, b in zip(vr[:-1], vr[1:]):
        for i in range(span):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    if close_start and closed_ring:
        bm.faces.new(list(reversed(vr[0])))
    if close_end and closed_ring:
        bm.faces.new(vr[-1])
    bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_obj(name, bm, smooth)


def perp(d):
    d = V(d).normalized()
    a = V((0, 0, 1)) if abs(d.z) < 0.9 else V((1, 0, 0))
    x = d.cross(a).normalized()
    return x, d.cross(x).normalized()


def horn(name, pts, radii, sides=12, flat=1.0, ref=None):
    """Tapered curved spike along a polyline (claws, tusks, nails)."""
    rings = []
    for i, (p, r) in enumerate(zip(pts, radii)):
        d = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        if ref is not None:
            x = d.cross(ref).normalized()
            y = d.cross(x).normalized()
        else:
            x, y = perp(d)
        r = max(r, 0.0002)
        rings.append([p + (x * math.cos(t) * flat + y * math.sin(t)) * r
                      for t in (2 * math.pi * k / sides for k in range(sides))])
    return tube(name, rings, close_start=True, close_end=True)


def bez(p0, p1, p2, n):
    return [p0 * (1 - t) ** 2 + p1 * 2 * t * (1 - t) + p2 * t * t
            for t in (k / (n - 1) for k in range(n))]


# ----------------------------------------------------------------------------
# GOBLIN ANATOMY  (metres, Z up, goblin faces -Y toward camera)
# ----------------------------------------------------------------------------
body = Meta('GobBody', 0.0032 if not PREVIEW else 0.007)

# --- torso: hunched, wiry chest, pot belly
body.ell((0, 0.0, 0.79), (0.145, 0.092, 0.10))                 # rib cage
body.ell((0, 0.045, 0.835), (0.12, 0.07, 0.08))                # upper-back hunch
body.ell((0, -0.035, 0.645), (0.122, 0.118, 0.115))            # pot belly
body.ell((0, 0.005, 0.525), (0.128, 0.092, 0.08))              # pelvis
body.ell((0, 0.055, 0.50), (0.11, 0.06, 0.07))                 # rump
for s in (-1, 1):
    body.ell((s * 0.058, -0.072, 0.805), (0.058, 0.028, 0.04))  # pecs
    body.ell((s * 0.11, -0.02, 0.70), (0.035, 0.06, 0.07), stiff=1.5)  # obliques
    body.ell((s * 0.07, 0.065, 0.74), (0.05, 0.03, 0.09))       # lats
body.ell((0, -0.115, 0.585), (0.045, 0.03, 0.03), neg=True, stiff=0.6)  # belly-under crease
body.ball((0, -0.152, 0.64), 0.006, neg=True, stiff=1.0)       # navel

# --- neck & shoulders
body.cap((0, 0.03, 0.85), (0, -0.035, 0.975), 0.044)
for s in (-1, 1):
    body.cap((0, 0.03, 0.905), (s * 0.17, 0.01, 0.855), 0.036)   # trapezius
    body.cap((s * 0.02, -0.06, 0.87), (s * 0.16, -0.02, 0.86), 0.018)  # clavicle
    body.ball((s * 0.188, 0.0, 0.83), 0.047)                      # deltoid

# --- head: big cranium, long hooked nose, heavy angry brow, underbite jaw
body.ell((0, -0.03, 1.065), (0.118, 0.122, 0.112))             # cranium
body.ell((0, 0.035, 1.085), (0.098, 0.1, 0.098))               # back of skull
body.ell((0, -0.105, 0.995), (0.092, 0.075, 0.058))            # muzzle
body.ell((0, -0.115, 0.952), (0.082, 0.07, 0.04))              # lower jaw
body.ball((0, -0.168, 0.945), 0.026)                           # chin
for s in (-1, 1):
    body.ball((s * 0.074, -0.118, 1.022), 0.034)                # cheekbones
    body.ball((s * 0.083, -0.07, 0.975), 0.035)                 # jaw angle
    body.cap((s * 0.088, -0.142, 1.103), (s * 0.016, -0.174, 1.084), 0.0165)  # angry brow
    body.ball((s * 0.05, -0.172, 1.054), 0.03, neg=True, stiff=4.0)  # eye socket
    body.ell((s * 0.05, -0.158, 1.077), (0.03, 0.02, 0.011),
             rot=frame((1, 0, 0.28 * s), (0, 1, 0)))           # upper lid (heavy, angry)
    body.ell((s * 0.05, -0.152, 1.032), (0.026, 0.016, 0.008))  # lower lid / bag
    body.ball((s * 0.03, -0.177, 1.0), 0.018)                   # nasolabial bulge
# nose
body.cap((0, -0.17, 1.078), (0, -0.228, 1.05), 0.016)
body.cap((0, -0.228, 1.05), (0, -0.268, 1.0), 0.0135)
body.ball((0, -0.262, 0.998), 0.0185)
for s in (-1, 1):
    body.ball((s * 0.021, -0.212, 1.003), 0.016)                # alae
    body.ball((s * 0.011, -0.25, 0.986), 0.006, neg=True)      # nostrils
# mouth: wide sneer slit + lips
mouth = [V((-0.07, -0.158, 0.99)), V((-0.035, -0.186, 0.979)), V((0, -0.194, 0.977)),
         V((0.035, -0.186, 0.979)), V((0.07, -0.158, 0.993))]
for a, b in zip(mouth[:-1], mouth[1:]):
    body.cap(a + V((0, -0.006, 0)), b + V((0, -0.006, 0)), 0.0085, neg=True, stiff=2.5)
body.cap((-0.04, -0.188, 0.968), (0.04, -0.188, 0.968), 0.012)  # lower lip (underbite)
# warts
for p, r in [((0.016, -0.248, 1.03), 0.0055), ((-0.07, -0.135, 1.13), 0.006),
             ((0.08, -0.13, 1.0), 0.005), ((-0.03, -0.12, 1.16), 0.0045)]:
    body.ball(p, r, stiff=3)

# --- ears: huge, swept back, with inner concavity
for s in (-1, 1):
    root, tip = V((s * 0.108, -0.01, 1.075)), V((s * 0.36, 0.085, 1.17))
    L = (tip - root).normalized()
    N = V((s * 0.32, -1, 0.1))
    q = frame(L, (N.cross(L)))
    W = q @ V((0, 1, 0))
    Nn = q @ V((0, 0, 1))
    if Nn.y > 0:
        Nn = -Nn
    w8 = [0.04, 0.056, 0.058, 0.052, 0.043, 0.032, 0.02, 0.01]
    widths = np.interp(np.linspace(0, 7, 22), np.arange(8), w8)
    for i, wv in enumerate(widths):
        t = i / (len(widths) - 1)
        p = root.lerp(tip, t) + V((0, 0, -0.07 * t * t + 0.03 * t))
        body.ell(p + W * 0.012 * math.sin(t * math.pi), (0.03, wv * 0.92, 0.0095 * (1 - 0.45 * t)), rot=q, stiff=1.4)
        if 0.1 < t < 0.8:
            body.ell(p + Nn * 0.011 + W * 0.008, (0.03, wv * 0.6, 0.006), rot=q, neg=True, stiff=0.6)
    body.ell(root + L * 0.015 + V((0, 0, -0.04)), (0.02, 0.018, 0.012), rot=q)  # lobe

# --- limbs (pose) -----------------------------------------------------------
J = {}
for s, name in ((-1, 'R'), (1, 'L')):
    J['hip' + name] = V((s * 0.085, 0.0, 0.50))
    J['knee' + name] = V((s * 0.165, -0.06, 0.285))
    J['ankle' + name] = V((s * 0.185, 0.0, 0.085))
    J['sho' + name] = V((s * 0.19, 0.0, 0.83))
J['elbR'] = V((-0.285, 0.035, 0.645))
J['wriR'] = V((-0.29, -0.115, 0.535))
J['elbL'] = V((0.30, 0.045, 0.65))
J['wriL'] = V((0.345, -0.01, 0.485))

for n in 'RL':
    s = -1 if n == 'R' else 1
    sh, el, wr = J['sho' + n], J['elb' + n], J['wri' + n]
    hp, kn, an = J['hip' + n], J['knee' + n], J['ankle' + n]
    # arm: wiry, knobbly elbow
    body.cap(sh, el, 0.03)
    body.ell(sh.lerp(el, 0.45) + V((0, -0.012, 0)), (0.034, 0.036, 0.06),
             rot=V((0, 0, 1)).rotation_difference(el - sh))     # biceps/triceps
    body.ball(el, 0.03)
    fm = el.lerp(wr, 0.4)
    body.cap(el, fm, 0.034)
    body.cap(fm, wr, 0.024)
    # leg: bony knees, thin shins
    body.cap(hp, kn, 0.05)
    body.ell(hp.lerp(kn, 0.4) + V((0, -0.02, 0)), (0.05, 0.05, 0.085),
             rot=V((0, 0, 1)).rotation_difference(hp - kn))
    body.ball(kn + V((0, -0.012, 0)), 0.04)
    body.cap(kn, an, 0.03)
    body.ell(kn.lerp(an, 0.3) + V((0, 0.03, 0)), (0.036, 0.036, 0.07),
             rot=V((0, 0, 1)).rotation_difference(kn - an))     # calf
    body.ball(an, 0.032)
    # foot: long, splayed, three clawed toes
    a = math.radians(18) * s
    f = V((math.sin(a), -math.cos(a), 0))
    side = V((math.cos(a), math.sin(a), 0))
    base = V((an.x, an.y, 0))
    body.ball(base - f * 0.03 + V((0, 0, 0.038)), 0.038)          # heel
    body.ell(base + f * 0.065 + V((0, 0, 0.034)), (0.08, 0.052, 0.03), rot=frame(f, side))
    for k, o in enumerate((-0.034, 0.0, 0.034)):
        ln = (0.06, 0.075, 0.055)[k]
        tb = base + f * 0.125 + side * o * s + V((0, 0, 0.026))
        tt = tb + f * ln + side * o * s * 0.6 + V((0, 0, -0.008))
        body.cap(tb, tt, 0.0165)
        body.ball(tt, 0.0175)
        J['toe%s%d' % (n, k)] = (tt, f)

# --- hands (separate finer metaball family; wrists hidden by leather wraps)
hands = Meta('GobHands', 0.003 if not PREVIEW else 0.005)
CLAWS = []


def build_hand(n, wrist, u, v, curls, spread, thumb_dirs, mirror):
    u = u.normalized()
    v = (v - u * u.dot(v)).normalized()
    w = (u.cross(v) if not mirror else v.cross(u)).normalized()   # back-of-hand normal
    q = Matrix((u, v, w)).transposed().to_quaternion()
    hands.ball(wrist, 0.026)
    hands.ell(wrist + u * 0.045, (0.048, 0.042, 0.02), rot=q)
    hands.ell(wrist + u * 0.035 + v * 0.03 - w * 0.008, (0.03, 0.02, 0.018), rot=q)  # thenar
    for k, off in enumerate((0.027, 0.0, -0.027)):
        sc = (0.97, 1.06, 0.88)[k]
        p = wrist + u * 0.088 + v * off
        sp = math.radians(spread * (1 - k))
        d0 = (u * math.cos(sp) + v * math.sin(sp)).normalized()
        th = 0.0
        hands.ball(p, 0.0135)
        for seg, (ln, r) in enumerate(((0.042, 0.012), (0.033, 0.0108), (0.025, 0.0092))):
            th += curls[seg]
            d = d0 * math.cos(th) - w * math.sin(th)
            p2 = p + d * ln * sc
            hands.cap(p, p2, r)
            hands.ball(p2, r * 1.12)
            p = p2
        dc = d0 * math.cos(th + 0.5) - w * math.sin(th + 0.5)
        CLAWS.append(bez(p, p + d * 0.018, p + dc * 0.034, 7))
    p = wrist + u * 0.03 + v * 0.036 - w * 0.01
    for ln, r, dd in zip((0.036, 0.03), (0.0135, 0.0115), thumb_dirs):
        d = (u * dd[0] + v * dd[1] - w * dd[2]).normalized()
        p2 = p + d * ln
        hands.cap(p, p2, r)
        hands.ball(p2, r * 1.1)
        p = p2
    CLAWS.append(bez(p, p + d * 0.016, p + d * 0.03 - w * 0.012, 7))
    return u, v, w


# right hand: fist around dagger grip, thumb toward blade
uR = (J['wriR'] - J['elbR']).normalized()
vR = V((-0.25, -0.35, 1.0))
fistR = build_hand('R', J['wriR'], uR, vR, (1.35, 1.45, 1.15), 0, ((0.7, 0.55, 0.45), (0.85, -0.1, 0.55)), False)
# left hand: open, hooked claws, palm facing body
uL = (J['wriL'] - J['elbL']).normalized()
vL = V((0.0, -1.0, 0.15))
build_hand('L', J['wriL'], uL, vL, (0.35, 0.45, 0.4), 12, ((0.45, 0.85, 0.15), (0.8, 0.6, 0.2)), True)

body_ob = body.to_mesh('Goblin_Body', 4)
hands_ob = hands.to_mesh('Goblin_Hands', 2)


def verts_of(ob):
    me = ob.data
    a = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get('co', a)
    return a.reshape(-1, 3)


BV = verts_of(body_ob)
ALLV = np.vstack([BV, verts_of(hands_ob)])


def ring_radius(center, axis, half=0.01, maxr=0.12, verts=ALLV):
    c, a = np.array(center), np.array(V(axis).normalized())
    d = verts - c
    along = d @ a
    rad = np.linalg.norm(d - np.outer(along, a), axis=1)
    m = (np.abs(along) < half) & (rad < maxr)
    return float(rad[m].max()) if m.any() else 0.03


def slice_profile(z, nb, cy=0.0, half=0.008):
    m = (np.abs(BV[:, 2] - z) < half) & (np.abs(BV[:, 0]) < 0.24)
    p = BV[m]
    ang = np.arctan2(p[:, 1] - cy, p[:, 0])
    r = np.hypot(p[:, 0], p[:, 1] - cy)
    bins = ((ang + math.pi) / (2 * math.pi) * nb).astype(int) % nb
    out = np.zeros(nb)
    np.maximum.at(out, bins, r)
    for _ in range(3):  # fill gaps, smooth
        out = np.maximum(out, 0.5 * (np.roll(out, 1) + np.roll(out, -1)))
    return out


# ----------------------------------------------------------------------------
# Eyes, teeth, claws
# ----------------------------------------------------------------------------
EYES = []
for s in (-1, 1):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=32, radius=0.0215)
    ob = mesh_obj('Eye_%s' % ('L' if s > 0 else 'R'), bm)
    ob.location = (s * 0.05, -0.163, 1.054)
    # look slightly toward camera / down, a touch cross-eyed for menace
    ob.rotation_euler = (math.radians(-4), 0, math.radians(-6 * s + 8))
    EYES.append(ob)

TEETH = []
for s in (-1, 1):  # lower tusks over the upper lip
    b = V((s * 0.04, -0.183, 0.968))
    TEETH.append(horn('Tusk', bez(b, b + V((s * 0.002, -0.006, 0.02)), b + V((s * 0.012, -0.004, 0.042)), 8),
                      [0.0085 * (1 - t / 7) ** 0.8 for t in range(8)], sides=14))
for k, x in enumerate((-0.022, -0.008, 0.008, 0.022)):  # small crooked upper teeth
    b = V((x, -0.186 + abs(x) * 0.35, 0.988))
    L = 0.011 + rng.uniform(-0.002, 0.003)
    TEETH.append(horn('Tooth', bez(b, b + V((rng.uniform(-.002, .002), -0.001, -L * 0.5)), b + V((0, 0, -L)), 5),
                      [0.0042, 0.004, 0.0034, 0.0022, 0.0004], sides=10))

for n in 'RL':  # toe claws
    for k in range(3):
        tt, f = J['toe%s%d' % (n, k)]
        p0 = tt + f * 0.006 + V((0, 0, 0.004))
        CLAWS.append(bez(p0, p0 + f * 0.02 + V((0, 0, 0.002)), p0 + f * 0.032 + V((0, 0, -0.016)), 7))
CLAW_OBS = [horn('Claw', pts, [0.0075 * (1 - i / 6) ** 0.9 for i in range(7)], sides=10, flat=0.8)
            for pts in CLAWS]

# ----------------------------------------------------------------------------
# Costume: ragged burlap kilt, leather belt + pouch, wrist/ankle wraps,
#           shoulder pauldron, bone necklace, curved dagger
# ----------------------------------------------------------------------------
NB = 96
ztop, zbot = 0.62, 0.38
profiles = {}
for z in np.linspace(ztop, 0.30, 16):
    profiles[round(float(z), 4)] = slice_profile(float(z), NB, cy=0.005)
hem = np.array([rng.uniform(-1, 1) for _ in range(NB)])
for _ in range(2):
    hem = 0.5 * hem + 0.25 * (np.roll(hem, 1) + np.roll(hem, -1))
rows = 26
rings = []
acc = np.zeros(NB)
zs = sorted(profiles)[::-1]
for i in range(rows):
    t = i / (rows - 1)
    z0 = ztop + (zbot - ztop) * t
    for zz in zs:
        if zz >= z0 - 1e-4:
            acc = np.maximum(acc, profiles[zz])
    ring = []
    for b in range(NB):
        ang = -math.pi + (b + 0.5) / NB * 2 * math.pi
        r = acc[b] + 0.01 + 0.045 * t ** 1.5
        r += 0.006 * t * math.sin(ang * 9 + 1.3) + 0.004 * t * math.sin(ang * 17)  # folds
        z = z0 + (hem[b] * 0.045 + 0.02 * math.cos(ang * 2)) * t ** 4
        ring.append(V((r * math.cos(ang), 0.005 + r * math.sin(ang), z)))
    rings.append(ring)
kilt = tube('Kilt', rings)
m = kilt.modifiers.new('solid', 'SOLIDIFY')
m.thickness = 0.005
m.offset = 1
kilt.modifiers.new('sub', 'SUBSURF').levels = 1

# belt
belt_rings = []
zb = 0.612
prof = np.maximum(slice_profile(zb, NB, 0.005), slice_profile(zb + 0.02, NB, 0.005))
prof = np.maximum(prof, slice_profile(zb - 0.02, NB, 0.005))
for z, off in ((zb - 0.022, 0.0), (zb - 0.018, 0.006), (zb + 0.018, 0.006), (zb + 0.022, 0.0)):
    belt_rings.append([V(((prof[b] + 0.017 + off) * math.cos(a), 0.005 + (prof[b] + 0.017 + off) * math.sin(a), z))
                       for b, a in enumerate(-math.pi + (np.arange(NB) + 0.5) / NB * 2 * math.pi)])
belt = tube('Belt', belt_rings)
m = belt.modifiers.new('solid', 'SOLIDIFY')
m.thickness = 0.008
m.offset = -1
front_r = prof[int(NB * 0.25)] + 0.03
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1.0)
buckle = mesh_obj('Buckle', bm, smooth=False)
buckle.scale = (0.06, 0.012, 0.052)
buckle.location = (0, 0.005 - front_r, zb)
bev = buckle.modifiers.new('bev', 'BEVEL')
bev.width = 0.004
bev.segments = 3
# pouch on left hip
side_r = prof[int(NB * 0.43)] + 0.05
bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=16, radius=1)
pouch = mesh_obj('Pouch', bm)
pouch.scale = (0.04, 0.026, 0.05)
pouch.location = (side_r * math.cos(math.radians(-25)), 0.005 + side_r * math.sin(math.radians(-25)), zb - 0.055)
pouch.rotation_euler = (0, 0.25, -0.4)

# wraps on wrists / ankles
WRAPS = []
for n in 'RL':
    for c, ax, h, lo in ((J['wri' + n], J['wri' + n] - J['elb' + n], 0.05, -0.03),
                         (J['ankle' + n] + V((0, 0, 0.03)), V((0, 0, 1)), 0.065, -0.02)):
        ax = ax.normalized()
        x, y = perp(ax)
        rs = []
        for k in range(9):
            t = k / 8
            pc = c + ax * (lo + h * t)
            r = ring_radius(pc, ax, 0.006, verts=BV) + 0.006 + 0.004 * math.sin(t * math.pi)
            rs.append([pc + (x * math.cos(a) + y * math.sin(a)) * r
                       for a in (2 * math.pi * i / 40 for i in range(40))])
        ob = tube('Wrap', rs)
        mm = ob.modifiers.new('solid', 'SOLIDIFY')
        mm.thickness = 0.004
        WRAPS.append(ob)

# pauldron on left shoulder
bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=20, radius=1)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.15], context='VERTS')
paul = mesh_obj('Pauldron', bm)
paul.scale = (0.07, 0.068, 0.045)
paul.location = J['shoL'] + V((0.012, 0.0, 0.005))
paul.rotation_euler = (0, math.radians(32), 0)
mm = paul.modifiers.new('solid', 'SOLIDIFY')
mm.thickness = 0.12
mm.offset = 1
paul.modifiers.new('sub', 'SUBSURF').levels = 1
RIVETS = []
for k in range(7):
    a = math.radians(-70 + k * 23)
    loc_local = V((math.cos(a) * 0.72, math.sin(a) * 0.72, 0.62))
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.006)
    r = mesh_obj('Rivet', bm)
    mw = paul.matrix_basis if False else (Matrix.Translation(paul.location) @ paul.rotation_euler.to_matrix().to_4x4()
                                          @ Matrix.Diagonal((*paul.scale, 1)))
    r.location = mw @ loc_local
    RIVETS.append(r)
# strap across chest from pauldron
st = [J['shoL'] + V((-0.01, -0.06, 0.03)), V((0.02, -0.11, 0.74)), V((-0.12, -0.085, 0.63))]
strap_pts = bez(*[V(p) for p in st], 14)
srings = []
for i, p in enumerate(strap_pts):
    d = (strap_pts[min(i + 1, 13)] - strap_pts[max(i - 1, 0)]).normalized()
    nrm = V((0, -1, 0))
    wdir = d.cross(nrm).normalized()
    # push out of body
    pc = np.array(p)
    near = ALLV[np.linalg.norm(ALLV - pc, axis=1) < 0.04]
    if len(near):
        front = near[np.argmin(near[:, 1])]
        p = V((p.x, min(p.y, front[1] - 0.006), p.z))
    srings.append([p + wdir * 0.016, p + wdir * 0.016 + V((0, -0.004, 0)),
                   p - wdir * 0.016 + V((0, -0.004, 0)), p - wdir * 0.016])
strap = tube('Strap', srings)

# bone/tooth necklace
NECK = []
for k in range(9):
    t = (k - 4) / 4
    ang = math.radians(-90 + t * 70)
    p = V((0.085 * math.cos(ang) * 1.3, -0.03 + 0.095 * math.sin(ang), 0.87 - 0.03 * (1 - t * t)))
    pc = np.array(p)
    near = BV[np.linalg.norm(BV - pc, axis=1) < 0.05]
    if len(near):
        front = near[np.argmin(near[:, 1])]
        p = V((p.x, front[1] - 0.008, p.z))
    L = 0.032 if k % 2 == 0 else 0.022
    NECK.append(horn('Fang', bez(p, p + V((0, -0.006, -L * 0.5)), p + V((t * 0.006, -0.002, -L)), 6),
                     [0.007, 0.0065, 0.0055, 0.004, 0.0022, 0.0003], sides=10))
cord = [V((0.11 * math.cos(a), -0.03 + 0.1 * math.sin(a), 0.875 - 0.02 * math.sin(a) ** 2)) for a in
        np.linspace(math.radians(-170), math.radians(-10), 30)]
for i, p in enumerate(cord):
    pc = np.array(p)
    near = BV[np.linalg.norm(BV - pc, axis=1) < 0.03]
    if len(near):
        front = near[np.argmin(near[:, 1])]
        cord[i] = V((p.x, min(p.y, front[1] - 0.004), p.z))
cord_ob = horn('Cord', cord, [0.0025] * len(cord), sides=8)

# curved dagger in right fist (blade along thumb direction)
u, v, w = fistR
grip_c = J['wriR'] + u * 0.098 - w * 0.03
grip_c = grip_c + v * 0.005
gr = []
for k in range(10):
    t = k / 9
    pc = grip_c + v * (-0.065 + 0.12 * t)
    r = 0.0125 + 0.0015 * math.sin(t * math.pi * 6)
    x, y = u, w
    gr.append([pc + (x * math.cos(a) + y * math.sin(a)) * r for a in (2 * math.pi * i / 20 for i in range(20))])
grip = tube('Grip', gr, True, True)
guard_c = grip_c + v * 0.06
guard = horn('Guard', bez(guard_c - w * 0.05 - v * 0.012, guard_c, guard_c + w * 0.05 - v * 0.012, 9),
             [0.007, 0.0095, 0.011, 0.012, 0.012, 0.012, 0.011, 0.0095, 0.007], sides=12)
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=3, radius=0.017)
pommel = mesh_obj('Pommel', bm)
pommel.location = grip_c - v * 0.072
blade_rings = []
NBL = 28
for k in range(NBL):
    t = k / (NBL - 1)
    L = 0.30
    c = guard_c + v * (0.008 + L * t) - w * (0.06 * t * t)        # curved spine
    wid = 0.03 * (1 - t ** 2.2) + 0.0006
    if t < 0.06:
        wid *= 0.75
    edge = c + w * wid
    back = c - w * wid * 0.85
    thick = 0.0045 * (1 - t ** 1.5) + 0.0003
    blade_rings.append([edge, c + u * thick, back + u * thick * 0.6, back - u * thick * 0.6, c - u * thick])
blade = tube('Blade', blade_rings, True, True, smooth=False)
blade.data.shade_smooth()
blade.modifiers.new('ws', 'WEIGHTED_NORMAL')

# ground the goblin: lift everything so the lowest skin vertex touches z=0
dz = -float(BV[:, 2].min()) + 0.001
for ob in list(COL.objects):
    ob.location.z += dz

# ----------------------------------------------------------------------------
# MATERIALS
# ----------------------------------------------------------------------------


class NB_:
    def __init__(self, name):
        self.mat = bpy.data.materials.new(name)
        self.mat.use_nodes = True
        self.nt = self.mat.node_tree
        self.nt.nodes.clear()
        self.out = self.n('ShaderNodeOutputMaterial')
        self.bsdf = self.n('ShaderNodeBsdfPrincipled')
        self.l(self.bsdf, 0, self.out, 'Surface')

    def n(self, t, **props):
        nd = self.nt.nodes.new(t)
        for k, val in props.items():
            if k.startswith('in_'):
                key = k[3:].replace('_', ' ')
                nd.inputs[key].default_value = val
            else:
                setattr(nd, k, val)
        return nd

    def l(self, a, ao, b, bi):
        self.nt.links.new(a.outputs[ao], b.inputs[bi])

    def set(self, **kw):
        for k, val in kw.items():
            self.bsdf.inputs[k.replace('_', ' ')].default_value = val

    def coord(self, scale=1.0, space='Object'):
        tc = self.n('ShaderNodeTexCoord')
        if scale == 1.0:
            return tc, space
        mp = self.n('ShaderNodeMapping')
        mp.inputs['Scale'].default_value = (scale,) * 3
        self.l(tc, space, mp, 'Vector')
        return mp, 0

    def noise(self, scale, detail=6.0, rough=0.55, space='Object', dim='3D'):
        src, so = self.coord(space=space)
        nz = self.n('ShaderNodeTexNoise', in_Scale=scale, in_Detail=detail, in_Roughness=rough)
        nz.noise_dimensions = dim
        self.l(src, so, nz, 'Vector')
        return nz

    def ramp(self, src, so, stops):
        r = self.n('ShaderNodeValToRGB')
        cr = r.color_ramp
        cr.elements[0].position, cr.elements[0].color = stops[0][0], (*stops[0][1], 1)
        cr.elements[1].position, cr.elements[1].color = stops[-1][0], (*stops[-1][1], 1)
        for pos, c in stops[1:-1]:
            e = cr.elements.new(pos)
            e.color = (*c, 1)
        self.l(src, so, r, 'Fac')
        return r

    def mix(self, a, ao, b, bo, fac, blend='MIX', facsock=None):
        m = self.n('ShaderNodeMix', data_type='RGBA', blend_type=blend)
        if facsock is not None:
            self.l(facsock[0], facsock[1], m, 0)
        else:
            m.inputs[0].default_value = fac
        ca = a.outputs[2] if a.bl_idname == 'ShaderNodeMix' else a.outputs[0]
        cb = b.outputs[2] if b.bl_idname == 'ShaderNodeMix' else b.outputs[0]
        self.nt.links.new(ca, m.inputs[6])
        self.nt.links.new(cb, m.inputs[7])
        return m

    def bump(self, src, so, strength, dist=0.002, normal_from=None):
        b = self.n('ShaderNodeBump', in_Strength=strength, in_Distance=dist)
        self.l(src, so, b, 'Height')
        if normal_from is not None:
            self.l(normal_from, 'Normal', b, 'Normal')
        return b


def skin_mat():
    M = NB_('GoblinSkin')
    # colour variation: olive/moss greens with yellow undertone
    n1 = M.noise(6.0, 8, 0.6)
    base = M.ramp(n1, 'Fac', [(0.3, (0.04, 0.055, 0.018)), (0.5, (0.07, 0.09, 0.03)), (0.72, (0.13, 0.13, 0.055))])
    # darker mottled spots
    vor = M.n('ShaderNodeTexVoronoi', in_Scale=38.0)
    tc = M.n('ShaderNodeTexCoord')
    M.l(tc, 'Object', vor, 'Vector')
    spots = M.ramp(vor, 'Distance', [(0.0, (0.35, 0.35, 0.35)), (0.22, (1, 1, 1))])
    c1 = M.mix(base, 2, spots, 0, 0.35, 'MULTIPLY')
    # warm, flushed tint on thin/pointy parts (ears, nose, knuckles) via pointiness
    geo = M.n('ShaderNodeNewGeometry')
    pr = M.ramp(geo, 'Pointiness', [(0.52, (0, 0, 0)), (0.6, (1, 1, 1))])
    warm = M.n('ShaderNodeRGB')
    warm.outputs[0].default_value = (0.16, 0.07, 0.03, 1)
    c2 = M.mix(c1, 2, warm, 0, 0, 'MIX', facsock=None)
    mf = M.n('ShaderNodeMath', operation='MULTIPLY', in_Value=0.55)
    M.nt.links.new(pr.outputs[0], mf.inputs[0])
    mf.inputs[1].default_value = 0.35
    M.l(mf, 0, c2, 0)
    # cavity darkening
    ao = M.n('ShaderNodeAmbientOcclusion', in_Distance=0.03, samples=16)
    aor = M.ramp(ao, 'AO', [(0.0, (0.18, 0.12, 0.08)), (0.85, (1, 1, 1))])
    c3 = M.mix(c2, 2, aor, 0, 0.85, 'MULTIPLY')
    M.l(c3, 2, M.bsdf, 'Base Color')
    M.set(Subsurface_Weight=0.1, Subsurface_Scale=0.004, Roughness=0.48, Specular_IOR_Level=0.45,
          Coat_Weight=0.06, Coat_Roughness=0.25)
    M.bsdf.inputs['Subsurface Radius'].default_value = (1.0, 0.38, 0.18)
    M.bsdf.subsurface_method = 'RANDOM_WALK_SKIN'
    # roughness break-up
    rn = M.noise(40.0, 4)
    rr = M.ramp(rn, 'Fac', [(0.35, (0.38, 0.38, 0.38)), (0.7, (0.6, 0.6, 0.6))])
    M.l(rr, 0, M.bsdf, 'Roughness')
    # micro detail: pores + wrinkly cellular skin
    pores = M.noise(420.0, 3, 0.5)
    cells = M.n('ShaderNodeTexVoronoi', in_Scale=140.0, feature='F1')
    M.l(tc, 'Object', cells, 'Vector')
    wr = M.noise(55.0, 10, 0.68)
    b1 = M.bump(pores, 'Fac', 0.18, 0.0006)
    b2 = M.bump(cells, 'Distance', 0.22, 0.0008, normal_from=b1)
    b3 = M.bump(wr, 'Fac', 0.25, 0.0015, normal_from=b2)
    M.l(b3, 'Normal', M.bsdf, 'Normal')
    return M.mat


def eye_mat():
    M = NB_('GoblinEye')
    tc = M.n('ShaderNodeTexCoord')
    sep = M.n('ShaderNodeSeparateXYZ')
    M.l(tc, 'Object', sep, 'Vector')

    def math_(op, a, b=None, val=None):
        nd = M.n('ShaderNodeMath', operation=op)
        if isinstance(a, tuple):
            M.l(a[0], a[1], nd, 0)
        else:
            nd.inputs[0].default_value = a
        if b is not None:
            if isinstance(b, tuple):
                M.l(b[0], b[1], nd, 1)
            else:
                nd.inputs[1].default_value = b
        return nd
    # radial distance from the eye's forward (-Y) axis
    x2 = math_('MULTIPLY', (sep, 'X'), (sep, 'X'))
    z2 = math_('MULTIPLY', (sep, 'Z'), (sep, 'Z'))
    r = math_('SQRT', (math_('ADD', (x2, 0), (z2, 0)), 0))
    front = math_('LESS_THAN', (sep, 'Y'), 0.0)
    rf = math_('ADD', (r, 0), (math_('MULTIPLY', (math_('SUBTRACT', 1.0, (front, 0)), 0), 1.0), 0))
    iris_c = M.n('ShaderNodeTexNoise', in_Scale=900.0, in_Detail=4.0)
    M.l(tc, 'Object', iris_c, 'Vector')
    iris_col = M.ramp(iris_c, 'Fac', [(0.35, (0.35, 0.03, 0.0)), (0.5, (0.8, 0.18, 0.0)), (0.7, (1.0, 0.45, 0.02))])
    sclera = M.n('ShaderNodeRGB')
    sclera.outputs[0].default_value = (0.3, 0.2, 0.045, 1)
    limbal = M.ramp(rf, 0, [(0.0, (1, 1, 1)), (0.0115, (1, 1, 1)), (0.0135, (0, 0, 0)), (1.0, (0, 0, 0))])
    c = M.mix(sclera, 0, iris_col, 0, 0, facsock=(limbal, 0))
    # vertical slit pupil
    px = math_('DIVIDE', (sep, 'X'), 0.0055)
    pz = math_('DIVIDE', (sep, 'Z'), 0.0135)
    q = math_('ADD', (math_('MULTIPLY', (px, 0), (px, 0)), 0), (math_('MULTIPLY', (pz, 0), (pz, 0)), 0))
    q = math_('ADD', (q, 0), (math_('MULTIPLY', (math_('SUBTRACT', 1.0, (front, 0)), 0), 10.0), 0))
    pup = M.ramp(q, 0, [(0.0, (0, 0, 0)), (0.0, (0, 0, 0)), (0.12, (1, 1, 1)), (1.0, (1, 1, 1))])
    pup.color_ramp.elements[1].position = 0.08
    c2 = M.mix(c, 2, pup, 0, 1.0, 'MULTIPLY')
    M.l(c2, 2, M.bsdf, 'Base Color')
    # faint glow in the iris
    em = M.mix(c2, 2, limbal, 0, 1.0, 'MULTIPLY')
    M.l(em, 2, M.bsdf, 'Emission Color')
    M.set(Emission_Strength=0.35, Roughness=0.25, Coat_Weight=1.0, Coat_Roughness=0.02, Subsurface_Weight=0.1)
    return M.mat


def simple_mat(name, color, rough=0.5, metal=0.0, sss=0.0, noise_scale=0.0, noise_amt=0.0,
               bump=0.0, bump_scale=60.0, color2=None, wave=False, coat=0.0):
    M = NB_(name)
    M.set(Roughness=rough, Metallic=metal, Subsurface_Weight=sss, Coat_Weight=coat)
    if sss:
        M.set(Subsurface_Scale=0.005)
    if noise_scale:
        nz = M.noise(noise_scale, 8, 0.6)
        c2 = color2 or tuple(cc * 0.45 for cc in color)
        cr = M.ramp(nz, 'Fac', [(0.3, c2), (0.7, color)])
        if wave:
            wv = M.n('ShaderNodeTexWave', in_Scale=wave, in_Distortion=3.0, in_Detail=4.0)
            tc = M.n('ShaderNodeTexCoord')
            M.l(tc, 'Object', wv, 'Vector')
            wr = M.ramp(wv, 'Fac', [(0.0, (0.55, 0.55, 0.55)), (1.0, (1, 1, 1))])
            cr = M.mix(cr, 0, wr, 0, 0.6, 'MULTIPLY')
            bw = M.bump(wv, 'Fac', bump * 1.5, 0.0015)
        else:
            bw = None
        ao = M.n('ShaderNodeAmbientOcclusion', in_Distance=0.02, samples=8)
        aor = M.ramp(ao, 'AO', [(0.0, (0.25, 0.25, 0.25)), (0.9, (1, 1, 1))])
        cf = M.mix(cr, 0 if not wave else 2, aor, 0, 0.8, 'MULTIPLY')
        M.l(cf, 2, M.bsdf, 'Base Color')
        if bump:
            bn = M.noise(bump_scale, 10, 0.65)
            b = M.bump(bn, 'Fac', bump, 0.001, normal_from=bw)
            M.l(b, 'Normal', M.bsdf, 'Normal')
        rn = M.noise(noise_scale * 3, 4)
        rr = M.ramp(rn, 'Fac', [(0.3, (rough * 0.75,) * 3), (0.7, (min(1, rough * 1.2),) * 3)])
        M.l(rr, 0, M.bsdf, 'Roughness')
    else:
        M.set(Base_Color=(*color, 1))
    return M.mat


def burlap_mat():
    M = NB_('Burlap')
    tc = M.n('ShaderNodeTexCoord')
    w1 = M.n('ShaderNodeTexWave', wave_type='BANDS', bands_direction='X', in_Scale=260.0, in_Distortion=0.6)
    w2 = M.n('ShaderNodeTexWave', wave_type='BANDS', bands_direction='Z', in_Scale=260.0, in_Distortion=0.6)
    for wv in (w1, w2):
        M.l(tc, 'Object', wv, 'Vector')
    weave = M.n('ShaderNodeMath', operation='MULTIPLY')
    M.l(w1, 'Fac', weave, 0)
    M.l(w2, 'Fac', weave, 1)
    dirt = M.noise(9.0, 8, 0.6)
    col = M.ramp(dirt, 'Fac', [(0.25, (0.06, 0.04, 0.02)), (0.55, (0.11, 0.075, 0.04)), (0.8, (0.15, 0.105, 0.06))])
    wr = M.ramp(weave, 0, [(0.0, (0.6, 0.6, 0.6)), (0.5, (1, 1, 1))])
    c = M.mix(col, 0, wr, 0, 1.0, 'MULTIPLY')
    # grime toward the hem
    zsep = M.n('ShaderNodeSeparateXYZ')
    M.l(tc, 'Object', zsep, 'Vector')
    grime = M.ramp(zsep, 'Z', [(0.36, (0.35, 0.3, 0.25)), (0.5, (1, 1, 1))])
    c2 = M.mix(c, 2, grime, 0, 1.0, 'MULTIPLY')
    ao = M.n('ShaderNodeAmbientOcclusion', in_Distance=0.04, samples=8)
    aor = M.ramp(ao, 'AO', [(0.0, (0.2, 0.2, 0.2)), (0.9, (1, 1, 1))])
    c3 = M.mix(c2, 2, aor, 0, 1.0, 'MULTIPLY')
    M.l(c3, 2, M.bsdf, 'Base Color')
    M.set(Roughness=0.92, Sheen_Weight=0.4, Sheen_Roughness=0.6)
    b1 = M.bump(weave, 0, 0.45, 0.0012)
    fz = M.noise(120.0, 12, 0.7)
    b2 = M.bump(fz, 'Fac', 0.25, 0.001, normal_from=b1)
    M.l(b2, 'Normal', M.bsdf, 'Normal')
    return M.mat


def floor_mat():
    M = NB_('Cyclorama')
    M.set(Base_Color=(0.07, 0.07, 0.07, 1), Roughness=0.75, Specular_IOR_Level=0.3)
    return M.mat


MAT = {
    'skin': skin_mat(),
    'eye': eye_mat(),
    'bone': simple_mat('Bone', (0.62, 0.52, 0.32), 0.42, sss=0.15, noise_scale=30, color2=(0.32, 0.24, 0.12),
                       bump=0.15, bump_scale=200, coat=0.2),
    'claw': simple_mat('Claw', (0.13, 0.1, 0.07), 0.3, noise_scale=40, color2=(0.035, 0.025, 0.02),
                       bump=0.1, bump_scale=300, coat=0.4),
    'leather': simple_mat('Leather', (0.1, 0.05, 0.022), 0.5, noise_scale=12, color2=(0.035, 0.018, 0.009),
                          bump=0.35, bump_scale=160),
    'wrap': simple_mat('LeatherWrap', (0.16, 0.1, 0.055), 0.75, noise_scale=10, color2=(0.06, 0.04, 0.025),
                       bump=0.25, bump_scale=120, wave=70.0),
    'iron': simple_mat('Iron', (0.42, 0.4, 0.38), 0.35, metal=1.0, noise_scale=25, color2=(0.16, 0.1, 0.06),
                       bump=0.08, bump_scale=300),
    'steel': simple_mat('BladeSteel', (0.72, 0.71, 0.7), 0.18, metal=1.0, noise_scale=18, color2=(0.3, 0.2, 0.12),
                        bump=0.05, bump_scale=400),
    'burlap': burlap_mat(),
    'floor': floor_mat(),
}


def assign(ob, key):
    ob.data.materials.clear()
    ob.data.materials.append(MAT[key])


assign(body_ob, 'skin')
assign(hands_ob, 'skin')
for ob in EYES:
    assign(ob, 'eye')
    ob.hide_render = 'noeyes' in argv
for ob in TEETH + NECK:
    assign(ob, 'bone')
for ob in CLAW_OBS:
    assign(ob, 'claw')
for ob in (belt, pouch, paul, strap, cord_ob):
    assign(ob, 'leather')
for ob in WRAPS + [grip]:
    assign(ob, 'wrap')
for ob in [buckle, guard, pommel] + RIVETS:
    assign(ob, 'iron')
assign(blade, 'steel')
assign(kilt, 'burlap')

# ----------------------------------------------------------------------------
# STUDIO: cyclorama, three-point lighting, camera
# ----------------------------------------------------------------------------
prof2 = [(-12.0, 0.0), (3.0, 0.0)]
for k in range(1, 13):
    a = k / 12 * math.pi / 2
    prof2.append((3.0 + 2.5 * math.sin(a), 2.5 - 2.5 * math.cos(a)))
prof2.append((5.5, 10.0))
cyc = tube('Cyclorama', [[V((x, y, z)) for (y, z) in prof2] for x in (-14.0, 14.0)], closed_ring=False)
cyc.data.materials.append(MAT['floor'])

TARGET = V((0, 0, 0.62))


def area(name, loc, power, size, color, size_y=None, target=TARGET):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.energy = power
    ld.color = color
    ld.shape = 'RECTANGLE'
    ld.size = size
    ld.size_y = size_y or size
    ob = link(bpy.data.objects.new(name, ld))
    ob.location = loc
    ob.rotation_euler = (V(target) - V(loc)).to_track_quat('-Z', 'Y').to_euler()
    return ob


area('Key', (-2.3, -2.7, 2.6), 720, 1.4, (1.0, 0.93, 0.84))
area('Fill', (2.9, -2.4, 1.3), 160, 2.2, (0.84, 0.9, 1.0))
area('Rim', (1.3, 2.4, 2.3), 650, 0.6, (1.0, 0.97, 0.92), size_y=1.6, target=V((0, 0, 0.9)))

cam_d = bpy.data.cameras.new('Cam')
cam_d.lens = 66 if not HEADCAM else 200
cam_d.sensor_width = 36
cam = link(bpy.data.objects.new('Cam', cam_d))
yaw = math.radians(14)
dist = 4.75
look = TARGET + V((0, 0, 0.0)) if not HEADCAM else V((0, -0.1, 1.06 + dz))
cam.location = look + V((-math.sin(yaw) * dist, -math.cos(yaw) * dist, 0.12))
cam.rotation_euler = (look - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam_d.dof.use_dof = True
cam_d.dof.focus_distance = (V((0, -0.15, 1.05)) - cam.location).length
cam_d.dof.aperture_fstop = 11.0
scene.camera = cam

world = bpy.data.worlds.new('World')
world.use_nodes = True
bg = world.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (0.18, 0.18, 0.18, 1)
bg.inputs['Strength'].default_value = 0.6
scene.world = world

# ----------------------------------------------------------------------------
# RENDER SETTINGS
# ----------------------------------------------------------------------------
r = scene.render
r.engine = 'CYCLES'
r.resolution_x, r.resolution_y = 1920, 1080
r.resolution_percentage = 30 if PREVIEW else 100
r.filepath = OUT
r.image_settings.file_format = 'PNG'
r.image_settings.color_mode = 'RGB'
r.image_settings.color_depth = '8'
r.dither_intensity = 1.0
cy = scene.cycles
cy.samples = 32 if PREVIEW else 1024
cy.use_adaptive_sampling = True
cy.adaptive_threshold = 0.006 if PREVIEW else 0.0025
cy.adaptive_min_samples = 0 if PREVIEW else 256
cy.use_denoising = True
cy.denoiser = 'OPENIMAGEDENOISE'
cy.max_bounces = 12
cy.diffuse_bounces = 4
cy.glossy_bounces = 6
cy.transmission_bounces = 8
cy.caustics_reflective = False
cy.caustics_refractive = False
cy.blur_glossy = 0.5
r.film_transparent = False
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == 'OPTIX'
    cy.device = 'GPU'
except Exception as e:  # CPU fallback
    print('GPU setup failed:', e)
scene.view_settings.view_transform = 'AgX'
try:
    scene.view_settings.look = 'AgX - Medium High Contrast'
except TypeError:
    pass
scene.view_settings.exposure = -0.35

import time; T0 = time.time()
print('POLYCOUNT', sum(len(o.data.polygons) for o in COL.objects if o.type == 'MESH'))
bpy.ops.render.render(write_still=True)
print('WROTE', OUT, 'render secs', round(time.time() - T0, 1))

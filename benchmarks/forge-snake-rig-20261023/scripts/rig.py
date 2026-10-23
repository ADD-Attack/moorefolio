# Rig the M5e forge snake (source m5e-mapped.blend @ 2bdbba4). Rigging only: no geometry/material edits.
# Usage: blender -b m5e-mapped.blend --python rig.py -- OUT.blend OUT.fbx REPORT.json
import bpy, sys, json, math
from mathutils import Vector, Matrix
out_blend, out_fbx, out_json = sys.argv[sys.argv.index("--")+1:][:3]
N_SPINE = 18

def tri_count(objs):
    n = 0
    for o in objs:
        o.data.calc_loop_triangles(); n += len(o.data.loop_triangles)
    return n

def world_verts(o):
    mw = o.matrix_world
    return [mw @ v.co for v in o.data.vertices]

def center(o):
    vs = world_verts(o); return sum(vs, Vector()) / len(vs)

# ---- source set: everything visible (= the GLB delivery set); SRC_* library meshes removed
for o in list(bpy.data.objects):
    if o.name.startswith("SRC_"): bpy.data.objects.remove(o)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
src_tris = tri_count(meshes); src_faces = sum(len(o.data.polygons) for o in meshes)
src_verts = sum(len(o.data.vertices) for o in meshes)
allv = [v for o in meshes for v in world_verts(o)]
bb_min = Vector([min(v[i] for v in allv) for i in range(3)]); bb_max = Vector([max(v[i] for v in allv) for i in range(3)])
src_mats = sorted({s.material.name for o in meshes for s in o.material_slots if s.material})

# ---- unit chain, tail -> head
units = ["TailTip_node", "TailTaper_2", "TailTaper_1"] + [f"Segment_{i:02d}" for i in range(28, 0, -1)]
glow_of = {"TailTaper_1": "Glow_T1", **{f"Segment_{i:02d}": f"Glow_{i:02d}" for i in range(1, 29)}}
C = [center(bpy.data.objects[u]) for u in units]
tip_dir = (C[0] - C[1]).normalized()
tip_end = max(world_verts(bpy.data.objects[units[0]]), key=lambda v: (v - C[1]).dot(tip_dir))
head = bpy.data.objects["Head_node"]
hdir = (center(head) - C[-1]); hdir.z = 0; hdir.normalize()
head_front = max(world_verts(head), key=lambda v: (v - C[-1]).dot(hdir))
head_front = C[-1] + hdir * (head_front - C[-1]).dot(hdir)
P = [tip_end] + C + [head_front]          # polyline; unit k center = P[k+1]
S = [0.0]
for a, b in zip(P, P[1:]): S.append(S[-1] + (b - a).length)

def at(s):
    for i in range(len(P) - 1):
        if s <= S[i+1] or i == len(P) - 2:
            t = (s - S[i]) / max(S[i+1] - S[i], 1e-9); return P[i].lerp(P[i+1], min(max(t, 0), 1))

k07 = units.index("Segment_07") + 1; k04 = units.index("Segment_04") + 1; k01 = units.index("Segment_01") + 1
s_neck0, s_neck1, s_head0, s_end = S[k07], S[k04], S[k01], S[-1]
bone_s = [(s_neck0 * i / N_SPINE, s_neck0 * (i + 1) / N_SPINE, f"spine_{i+1:02d}") for i in range(N_SPINE)]
# neck: one bone per neck segment (Segment_07 -> Segment_01); a coarser neck kept the rest-pose rise baked in
ks = [units.index(f"Segment_{i:02d}") + 1 for i in range(7, 0, -1)]
bone_s += [(S[a], S[b], f"neck_{j+1:02d}") for j, (a, b) in enumerate(zip(ks, ks[1:]))]
bone_s += [(s_head0, s_end, "head")]

# ---- armature (bone Z = parallel-transported world up, so twist is consistent)
arm_data = bpy.data.armatures.new("ForgeSnake_Skeleton")
arm = bpy.data.objects.new("ForgeSnake_Rig", arm_data)
bpy.context.scene.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
eb = arm_data.edit_bones
root = eb.new("root"); root.head = (0, 0, 0); root.tail = (0, 0.5, 0); root.roll = 0
up = Vector((0, 0, 1)); prev = root
for s0, s1, name in bone_s:
    b = eb.new(name); b.head = at(s0); b.tail = at(s1)
    y = (b.tail - b.head).normalized()
    up = (up - y * up.dot(y)).normalized()
    b.align_roll(up)
    b.parent = prev; b.use_connect = (prev is not root)
    prev = b
rest_info = {b.name: {"head": list(b.head), "tail": list(b.tail), "parent": b.parent.name if b.parent else None} for b in eb}
bpy.ops.object.mode_set(mode='OBJECT')

# ---- weights: per-vertex arclength along the chain, hat-function blend between adjacent bone midpoints
mids = [((s0 + s1) / 2, n) for s0, s1, n in bone_s]
def weights_at(s):
    if s <= mids[0][0]: return {mids[0][1]: 1.0}
    if s >= mids[-1][0]: return {mids[-1][1]: 1.0}
    for (a, na), (b, nb) in zip(mids, mids[1:]):
        if a <= s <= b:
            t = (s - a) / (b - a); t = t * t * (3 - 2 * t)   # smoothstep across the joint
            return {k: v for k, v in ((na, 1 - t), (nb, t)) if v > 1e-4}

def arclen_param(v, k):
    best = None
    for i in range(max(0, k - 2), min(len(P) - 1, k + 2)):
        a, b = P[i], P[i+1]; d = b - a
        t = min(max((v - a).dot(d) / d.length_squared, 0), 1)
        dist = (v - (a + d * t)).length
        if best is None or dist < best[0]: best = (dist, S[i] + t * d.length)
    return best[1]

names = [n for _, _, n in bone_s]
for o in meshes: o.data = o.data.copy()   # instanced segment meshes: vertex groups live on mesh data
for o in meshes:
    for n in names: o.vertex_groups.new(name=n)
    allidx = list(range(len(o.data.vertices)))
    for g in o.vertex_groups: g.remove(allidx)   # source meshes carry stale unnamed deform data at index 0
    gi = {g.name: g for g in o.vertex_groups}
    if o.name == "Head_node":
        gi["head"].add(list(range(len(o.data.vertices))), 1.0, 'REPLACE'); continue
    unit = o.name if o.name in units else next(u for u, g in glow_of.items() if g == o.name)
    k = units.index(unit) + 1
    for v, wv in zip(o.data.vertices, world_verts(o)):
        for n, w in weights_at(arclen_param(wv, k)).items(): gi[n].add([v.index], w, 'REPLACE')

# ---- join into one skinned mesh (transforms applied by join; world geometry unchanged)
bpy.ops.object.select_all(action='DESELECT')
for o in meshes: o.select_set(True)
body = bpy.data.objects["Segment_14"]; bpy.context.view_layer.objects.active = body
bpy.ops.object.join(); body.name = "ForgeSnake"; body.data.name = "ForgeSnake_Mesh"
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
body.parent = arm
mod = body.modifiers.new("Armature", 'ARMATURE'); mod.object = arm

# ---- verification
bpy.ops.object.select_all(action='DESELECT'); body.select_set(True); bpy.context.view_layer.objects.active = body
bpy.ops.object.vertex_group_normalize_all(lock_active=False)
gnames = {g.index: g.name for g in body.vertex_groups}
unweighted = 0; over4 = 0; maxinf = 0; badsum = 0
for v in body.data.vertices:
    ws = [g.weight for g in v.groups if g.weight > 0]
    maxinf = max(maxinf, len(ws)); unweighted += (len(ws) == 0); over4 += (len(ws) > 4)
    badsum += abs(sum(ws) - 1) > 1e-3
rig_tris = tri_count([body])
allv2 = [body.matrix_world @ v.co for v in body.data.vertices]
bb2_min = [min(v[i] for v in allv2) for i in range(3)]; bb2_max = [max(v[i] for v in allv2) for i in range(3)]
rig_mats = sorted({s.material.name for s in body.material_slots if s.material})
report = dict(source="m5e-mapped.blend @ 2bdbba4", src_objects=len(meshes), src_verts=src_verts, src_faces=src_faces,
    src_tris=src_tris, rig_verts=len(body.data.vertices), rig_faces=len(body.data.polygons), rig_tris=rig_tris,
    tris_identical=src_tris == rig_tris, mats_identical=src_mats == rig_mats, materials=rig_mats,
    bounds_src=[list(bb_min), list(bb_max)], bounds_rig=[bb2_min, bb2_max],
    bones=len(arm_data.bones), bone_names=[b.name for b in arm_data.bones],
    unweighted=unweighted, over4=over4, max_influences=maxinf, weight_sum_off=badsum, rest=rest_info)
json.dump(report, open(out_json, "w"), indent=1)
print("REPORT", json.dumps({k: v for k, v in report.items() if k not in ("rest", "bone_names")}))
bpy.ops.wm.save_as_mainfile(filepath=out_blend, compress=True)
bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); body.select_set(True)
bpy.ops.export_scene.fbx(filepath=out_fbx, use_selection=True, object_types={'ARMATURE', 'MESH'},
    add_leaf_bones=False, bake_anim=False, mesh_smooth_type='FACE', path_mode='COPY', embed_textures=True,
    apply_scale_options='FBX_SCALE_NONE', axis_forward='-Z', axis_up='Y')
print("DONE")

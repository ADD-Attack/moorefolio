# Stage 1: strip slab, close+clean (solidify→voxel remesh→drop inner wall), save clean.blend
import bpy,sys,bmesh
from mathutils.bvhtree import BVHTree
a=sys.argv[sys.argv.index('--')+1:]; glb,out=a[0],a[1]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=glb)
o=[o for o in bpy.context.scene.objects if o.type=='MESH'][0]
for x in list(bpy.context.scene.objects):
    if x!=o: bpy.data.objects.remove(x)
o.parent=None
bm=bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world); o.matrix_world.identity()
bmesh.ops.delete(bm,geom=[f for f in bm.faces if max(v.co.z for v in f.verts)< -0.516],context='FACES')
bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-5)
# drop tiny loose islands
bm.verts.ensure_lookup_table(); seen=set(); kill=[]
for v in bm.verts:
    if v in seen: continue
    st=[v]; comp=[]; seen.add(v)
    while st:
        u=st.pop(); comp.append(u)
        for e in u.link_edges:
            w=e.other_vert(u)
            if w not in seen: seen.add(w); st.append(w)
    if len(comp)<2000: kill+=comp
bmesh.ops.delete(bm,geom=kill,context='VERTS'); print('KILLED',len(kill))
z0=min(v.co.z for v in bm.verts)
for v in bm.verts: v.co.z-=z0
bm.to_mesh(o.data); orig=BVHTree.FromBMesh(bm)
bpy.context.view_layer.objects.active=o; o.select_set(True)
m=o.modifiers.new('s','SOLIDIFY'); m.thickness=0.008; m.offset=-1
r=o.modifiers.new('r','REMESH'); r.mode='VOXEL'; r.voxel_size=0.005
bpy.ops.object.modifier_apply(modifier='s'); bpy.ops.object.modifier_apply(modifier='r')
bm=bmesh.new(); bm.from_mesh(o.data)
far=[f for f in bm.faces if orig.find_nearest(f.calc_center_median())[3]>0.0035]
bmesh.ops.delete(bm,geom=far,context='FACES'); bm.to_mesh(o.data)
print('CLEAN FACES',len(o.data.polygons))
o.name='clean'; bpy.ops.wm.save_as_mainfile(filepath=out)

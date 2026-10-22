# GATE-RETRY stitch: replace ONLY tail_01..03 in the bace685 clay with a Hunyuan-generated tail element.
# blender -b base.blend -P stitch.py -- <tail.glb> <outdir> <root_sign(+1: root at +x of element, -1: at -x)> <length_m> <zc> <yaw_deg>
import bpy,bmesh,sys,math,mathutils
a=sys.argv[sys.argv.index('--')+1:]; glb,out=a[0],a[1]; RS=float(a[2]); LEN=float(a[3]); ZC=float(a[4]); YAW=float(a[5]) if len(a)>5 else 0.0
THICK=float(a[6]) if len(a)>6 else 1.0
XT=-0.56; EMBED=0.03
body=bpy.data.objects['aliens_b_body']; clay=body.data.materials[0]
for n in ('tail_03','tail_02','tail_01'): bpy.data.objects.remove(bpy.data.objects[n])
before=set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=glb)
el=[o for o in bpy.data.objects if o not in before and o.type=='MESH'][0]
el.data.transform(el.matrix_world); el.matrix_world=mathutils.Matrix()
bm=bmesh.new(); bm.from_mesh(el.data); bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-5)
# largest island only
bm.verts.ensure_lookup_table(); seen=set(); isl=[]
for v in bm.verts:
    if v in seen: continue
    st=[v]; comp=[]; seen.add(v)
    while st:
        x=st.pop(); comp.append(x)
        for e in x.link_edges:
            y=e.other_vert(x)
            if y not in seen: seen.add(y); st.append(y)
    isl.append(comp)
isl.sort(key=len); bmesh.ops.delete(bm,geom=[v for c in isl[:-1] for v in c],context='VERTS')
bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=200)
bmesh.ops.triangulate(bm,faces=bm.faces); bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
# orient: root -> +x end, tail runs toward -x; optional yaw about z
R=mathutils.Matrix.Rotation(math.radians(YAW),4,'Z')
if RS<0: R=mathutils.Matrix.Rotation(math.pi,4,'Z')@R
bmesh.ops.transform(bm,matrix=R,verts=bm.verts)
xs=[v.co.x for v in bm.verts]; s=LEN/(max(xs)-min(xs))
bmesh.ops.scale(bm,vec=(s,s,s),verts=bm.verts)
mx=max(v.co.x for v in bm.verts); root=[v.co for v in bm.verts if v.co.x>mx-0.02]
cy=sum(c.y for c in root)/len(root); cz=sum(c.z for c in root)/len(root)
bmesh.ops.translate(bm,vec=(XT+EMBED-mx,-cy,ZC-cz),verts=bm.verts)
for v in bm.verts: v.co.y*=THICK; v.co.z=ZC+(v.co.z-ZC)*THICK
# clean manifold before decimation (surface-net shell shatters under collapse): voxel remesh the closed element
bm.to_mesh(el.data); bm.free()
rm=el.modifiers.new('rm','REMESH'); rm.mode='VOXEL'; rm.voxel_size=0.0025
bpy.context.view_layer.objects.active=el; bpy.ops.object.modifier_apply(modifier='rm')
bm=bmesh.new(); bm.from_mesh(el.data); bmesh.ops.triangulate(bm,faces=bm.faces)
print('ELEMENT_REMESH boundary',sum(1 for e in bm.edges if e.is_boundary),'nonman',sum(1 for e in bm.edges if not e.is_manifold))
print('ELEMENT tris',len(bm.faces),'bounds x',round(min(v.co.x for v in bm.verts),3),round(max(v.co.x for v in bm.verts),3),'z',round(min(v.co.z for v in bm.verts),3),round(max(v.co.z for v in bm.verts),3))
# 3 segments by length thirds measured from the socket plane
tip=min(v.co.x for v in bm.verts); seg=(XT-tip)/3.0; T1,T2=XT-seg,XT-2*seg
for q in (T1,T2): bmesh.ops.bisect_plane(bm,geom=bm.verts[:]+bm.edges[:]+bm.faces[:],plane_co=(q,0,0),plane_no=(1,0,0),dist=1e-6)
def reg(c): return 'tail_01' if c.x>T1 else ('tail_02' if c.x>T2 else 'tail_03')
groups={}
for f in bm.faces: groups.setdefault(reg(f.calc_center_median()),[]).append(f.index)
budget={'tail_01':2400,'tail_02':1900,'tail_03':1400}; objs={}
for name,idx in groups.items():
    b2=bm.copy(); b2.faces.ensure_lookup_table(); keep=set(idx)
    bmesh.ops.delete(b2,geom=[f for f in b2.faces if f.index not in keep],context='FACES')
    bmesh.ops.delete(b2,geom=[v for v in b2.verts if not v.link_faces],context='VERTS')
    ce=[e for e in b2.edges if e.is_boundary and all(abs(v.co.x-T1)<1e-4 or abs(v.co.x-T2)<1e-4 for v in e.verts)]
    if ce: bmesh.ops.holes_fill(b2,edges=ce,sides=0)
    bmesh.ops.triangulate(b2,faces=b2.faces)
    me=bpy.data.meshes.new(name); b2.to_mesh(me); b2.free()
    o=bpy.data.objects.new(name,me); bpy.context.scene.collection.objects.link(o); objs[name]=o; me.materials.append(clay)
    r=min(1.0,budget[name]/len(me.polygons)); m=o.modifiers.new('d','DECIMATE'); m.ratio=r
    bpy.context.view_layer.objects.active=o; bpy.ops.object.modifier_apply(modifier='d')
    for p in me.polygons: p.use_smooth=True
    print('NODE',name,len(me.polygons))
bpy.data.objects.remove(el)
for name,px in (('tail_01',XT),('tail_02',T1),('tail_03',T2)):
    o=objs[name]; vs=[v.co for v in o.data.vertices]; pt=mathutils.Vector((px,sum(c.y for c in vs)/len(vs),sum(c.z for c in vs)/len(vs)))
    o.data.transform(mathutils.Matrix.Translation(-pt)); o.location=pt
bpy.context.view_layer.update()
def parent(c,p): w=c.matrix_world.copy(); c.parent=p; c.matrix_world=w
parent(objs['tail_01'],body); parent(objs['tail_02'],objs['tail_01']); parent(objs['tail_03'],objs['tail_02'])
for o in objs.values():
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=0.003); bpy.ops.object.mode_set(mode='OBJECT')
print('TOTAL_TRIS',sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH'))
bpy.ops.wm.save_as_mainfile(filepath=out+'\\\\aliens_b_clay.blend')
bpy.ops.export_scene.gltf(filepath=out+'\\\\aliens_b_clay.glb',export_format='GLB',export_yup=True,export_apply=True,export_tangents=True,export_draco_mesh_compression_enable=False)

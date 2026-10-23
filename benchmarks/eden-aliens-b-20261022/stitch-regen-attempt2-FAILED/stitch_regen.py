# STITCH-REGEN: seat a Hunyuan tail-WITH-root element (transition formed in the element) into the bace685 body. Seat + cut only: no flare, no skirt.
# args: <glb> <outdir> <S> <anchor_ex> <anchor_ez> <XS> <ZS> <cut_ex> <c1_ex> <c2_ex>
import bpy,bmesh,sys,mathutils
a=sys.argv[sys.argv.index('--')+1:]; glb,out=a[0],a[1]; S,AX,AZ,XS,ZS,CUT,C1,C2=[float(x) for x in a[2:10]]
body=bpy.data.objects['aliens_b_body']; clay=body.data.materials[0]
for n in ('tail_03','tail_02','tail_01'): bpy.data.objects.remove(bpy.data.objects[n])
before=set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=glb)
el=[o for o in bpy.data.objects if o not in before and o.type=='MESH'][0]; el.data.transform(el.matrix_world); el.matrix_world=mathutils.Matrix()
# clean manifold first (surface-net shells shatter under decimation)
rm=el.modifiers.new('rm','REMESH'); rm.mode='VOXEL'; rm.voxel_size=0.006
bpy.context.view_layer.objects.active=el; bpy.ops.object.modifier_apply(modifier='rm')
bm=bmesh.new(); bm.from_mesh(el.data)
# discard the element's body-margin blob beyond CUT (that region lands inside our body)
bmesh.ops.bisect_plane(bm,geom=bm.verts[:]+bm.edges[:]+bm.faces[:],plane_co=(CUT,0,0),plane_no=(1,0,0),dist=1e-6,clear_outer=True)
# chain cuts in element space
for q in (C1,C2): bmesh.ops.bisect_plane(bm,geom=bm.verts[:]+bm.edges[:]+bm.faces[:],plane_co=(q,0,0),plane_no=(1,0,0),dist=1e-6)
cy=sum(v.co.y for v in bm.verts)/len(bm.verts)
M=mathutils.Matrix.Translation((XS,0,ZS))@mathutils.Matrix.Scale(S,4)@mathutils.Matrix.Translation((-AX,-cy,-AZ))
def tx(x): return XS+(x-AX)*S
groups={}
for f in bm.faces:
    x=f.calc_center_median().x; groups.setdefault('tail_01' if x>C1 else ('tail_02' if x>C2 else 'tail_03'),[]).append(f.index)
budget={'tail_01':2600,'tail_02':1900,'tail_03':1400}; objs={}
bm.faces.ensure_lookup_table()
for name,idx in groups.items():
    b2=bm.copy(); b2.faces.ensure_lookup_table(); keep=set(idx)
    bmesh.ops.delete(b2,geom=[f for f in b2.faces if f.index not in keep],context='FACES')
    bmesh.ops.delete(b2,geom=[v for v in b2.verts if not v.link_faces],context='VERTS')
    ce=[e for e in b2.edges if e.is_boundary and all(min(abs(v.co.x-q) for q in (C1,C2))<1e-4 for v in e.verts)]
    if ce: bmesh.ops.holes_fill(b2,edges=ce,sides=0)
    bmesh.ops.triangulate(b2,faces=b2.faces); b2.transform(M)
    me=bpy.data.meshes.new(name); b2.to_mesh(me); b2.free()
    o=bpy.data.objects.new(name,me); bpy.context.scene.collection.objects.link(o); objs[name]=o; me.materials.append(clay)
    m=o.modifiers.new('d','DECIMATE'); m.ratio=min(1.0,budget[name]/len(me.polygons)); bpy.context.view_layer.objects.active=o; bpy.ops.object.modifier_apply(modifier='d')
    for p in me.polygons: p.use_smooth=True
    print('NODE',name,len(me.polygons))
bpy.data.objects.remove(el)
for name,px in (('tail_01',tx(CUT)),('tail_02',tx(C1)),('tail_03',tx(C2))):
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

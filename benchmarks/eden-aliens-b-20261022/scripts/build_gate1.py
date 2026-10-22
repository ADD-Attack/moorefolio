# EDEN-3D-01 build: segment the approved Hunyuan c1-wholebody-s42 formed mesh into animatable nodes (Decision 35: from the formed mesh, no primitives)
import bpy,bmesh,sys,mathutils
args=sys.argv[sys.argv.index('--')+1:]; glb,outdir=args[0],args[1]
BB,BM=(int(args[2]),int(args[3])) if len(args)>3 else (20000,12000)
VOX=float(args[4]) if len(args)>4 else 0.004
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
src=[o for o in bpy.context.scene.objects if o.type=='MESH'][0]
src.data.transform(src.matrix_world); src.matrix_world=mathutils.Matrix()
bm=bmesh.new(); bm.from_mesh(src.data)
bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-5)
# 1 strip baked ground slab (z<-0.505); feet get capped later
bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.co.z<-0.505],context='VERTS')
# keep largest connected island only (drop stray slab fragments)
bm.verts.ensure_lookup_table(); seen=set(); isl=[]
for v in bm.verts:
    if v in seen: continue
    st=[v]; comp=[]; seen.add(v)
    while st:
        a=st.pop(); comp.append(a)
        for e in a.link_edges:
            b=e.other_vert(a)
            if b not in seen: seen.add(b); st.append(b)
    isl.append(comp)
isl.sort(key=len); print('ISLANDS',[len(i) for i in isl[-5:]])
bmesh.ops.delete(bm,geom=[v for c in isl[:-1] for v in c],context='VERTS')
# fill native Hunyuan seam pinholes + slab-strip foot holes (loops <=120 edges); large natural openings untouched
bd=[e for e in bm.edges if e.is_boundary]; print('RAW_BOUNDARY',len(bd))
bmesh.ops.holes_fill(bm,edges=bd,sides=120); print('RAW_BOUNDARY_AFTER',sum(1 for e in bm.edges if e.is_boundary))
bmesh.ops.triangulate(bm,faces=bm.faces)
# voxel remesh the formed mesh into a clean manifold surface (shell is near-closed here); same form, no double walls
if VOX>0:
    bm.to_mesh(src.data); bm.free()
    rm=src.modifiers.new('rm','REMESH'); rm.mode='VOXEL'; rm.voxel_size=VOX; rm.use_smooth_shade=True
    bpy.context.view_layer.objects.active=src; bpy.ops.object.modifier_apply(modifier='rm')
    bm=bmesh.new(); bm.from_mesh(src.data); bmesh.ops.triangulate(bm,faces=bm.faces)
print('REMESH tris',len(bm.faces),'boundary',sum(1 for e in bm.edges if e.is_boundary),'nonman',sum(1 for e in bm.edges if not e.is_manifold))
XT,XM,ZL,XC=-0.56,0.40,-0.34,0.05
T1,T2=-0.625,-0.675
def cut(co,no):
    g=bm.verts[:]+bm.edges[:]+bm.faces[:]
    bmesh.ops.bisect_plane(bm,geom=g,plane_co=co,plane_no=no,dist=1e-6)
cut((XT,0,0),(1,0,0)); cut((T1,0,0),(1,0,0)); cut((T2,0,0),(1,0,0)); cut((XM,0,0),(1,0,0))
# leg cut plane only within leg columns: bisect globally, region test restricts
cut((0,0,ZL),(0,0,1))
def region(c):
    if c.x<XT: return 'tail_01' if c.x>T1 else ('tail_02' if c.x>T2 else 'tail_03')
    if c.x>XM: return 'mouth'
    if c.z<ZL: return 'leg_'+('F' if c.x>XC else 'B')+('L' if c.y>0 else 'R')
    return 'body'
groups={}
for f in bm.faces: groups.setdefault(region(f.calc_center_median()),[]).append(f.index)
budget={'body':BB,'mouth':BM,'leg_FL':1500,'leg_FR':1500,'leg_BL':1500,'leg_BR':1500,'tail_01':1200,'tail_02':1000,'tail_03':800}
bm.faces.ensure_lookup_table()
clay=bpy.data.materials.new('clay'); clay.diffuse_color=(0.62,0.6,0.57,1)
objs={}
for name,idx in groups.items():
    b2=bm.copy(); b2.faces.ensure_lookup_table(); keep=set(idx)
    bmesh.ops.delete(b2,geom=[f for f in b2.faces if f.index not in keep],context='FACES')
    bmesh.ops.delete(b2,geom=[v for v in b2.verts if not v.link_faces],context='VERTS')
    def oncut(v): return any(abs(v.co.x-q)<1e-4 for q in (XT,T1,T2,XM)) or abs(v.co.z-ZL)<1e-4
    ce=[e for e in b2.edges if e.is_boundary and oncut(e.verts[0]) and oncut(e.verts[1])]
    if ce: bmesh.ops.holes_fill(b2,edges=ce,sides=0)
    bmesh.ops.triangulate(b2,faces=b2.faces)
    bmesh.ops.split_edges(b2,edges=[e for e in b2.edges if len(e.link_faces)>2])
    me=bpy.data.meshes.new(name); b2.to_mesh(me); b2.free()
    o=bpy.data.objects.new(name,me); bpy.context.scene.collection.objects.link(o); objs[name]=o
    o.data.materials.append(clay)
    n=len(me.polygons); r=min(1.0,budget[name]/n)
    m=o.modifiers.new('dec','DECIMATE'); m.ratio=r; m.use_collapse_triangulate=True; m.use_symmetry=False
    bpy.context.view_layer.objects.active=o; bpy.ops.object.modifier_apply(modifier='dec')
    b3=bmesh.new(); b3.from_mesh(o.data)
    bmesh.ops.remove_doubles(b3,verts=b3.verts,dist=0.001)
    bmesh.ops.holes_fill(b3,edges=[e for e in b3.edges if e.is_boundary],sides=40)
    bmesh.ops.triangulate(b3,faces=b3.faces)
    b3.to_mesh(o.data); b3.free()
    for p in o.data.polygons: p.use_smooth=True
    print('NODE',name,'raw',n,'->',len(o.data.polygons))
# pivots: legs at hip-cut centre, tail segs at root, mouth at cut centre
def set_origin(o,pt):
    o.data.transform(mathutils.Matrix.Translation(-pt)); o.location=pt
for name,o in objs.items():
    vs=[v.co for v in o.data.vertices]
    if name.startswith('leg'): pt=mathutils.Vector((sum(v.x for v in vs)/len(vs),sum(v.y for v in vs)/len(vs),ZL))
    elif name=='mouth': pt=mathutils.Vector((XM,0,sum(v.z for v in vs)/len(vs)))
    elif name.startswith('tail'): pt=mathutils.Vector(({'tail_01':XT,'tail_02':T1,'tail_03':T2}[name],0,sum(v.z for v in vs)/len(vs)))
    else: pt=mathutils.Vector((0,0,0))
    set_origin(o,pt)
bpy.context.view_layer.update()
def parent(c,p):
    w=c.matrix_world.copy(); c.parent=p; c.matrix_world=w
for n in objs:
    if n!='body' and not n.startswith('tail_0') or n=='tail_01': parent(objs[n],objs['body'])
parent(objs['tail_02'],objs['tail_01']); parent(objs['tail_03'],objs['tail_02'])
bpy.data.objects.remove(src)
objs['body'].name='aliens_b_body'
# provisional UVs so glTF tangents export (contract: tangents ON); material phase re-UVs
for o in objs.values():
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=0.003); bpy.ops.object.mode_set(mode='OBJECT')
print('TOTAL_TRIS',sum(len(o.data.polygons) for o in objs.values()))
bpy.ops.wm.save_as_mainfile(filepath=outdir+'\\aliens_b_clay.blend')
bpy.ops.export_scene.gltf(filepath=outdir+'\\aliens_b_clay.glb',export_format='GLB',export_yup=True,export_apply=True,export_tangents=True,export_draco_mesh_compression_enable=False)

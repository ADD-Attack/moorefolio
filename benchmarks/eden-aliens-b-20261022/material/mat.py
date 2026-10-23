# EDEN-3D-01 material phase: geometry FROZEN (positions untouched). Shared UV atlas, procedural geometry-driven shader -> baked maps -> image Principled + ORM.
import bpy,bmesh,sys,math,mathutils,os
a=sys.argv[sys.argv.index('--')+1:]; out=a[0]; RES=int(a[1]); SPP=int(a[2]); EMIT=float(a[3]); GI=int(a[7]) if len(a)>7 else 6; SMI2=int(a[8]) if len(a)>8 else 12; PT0=float(a[4]) if len(a)>4 else 0.47; PT1=float(a[5]) if len(a)>5 else 0.40; BS=float(a[6]) if len(a)>6 else 0.6
s=bpy.context.scene; objs=[o for o in s.objects if o.type=='MESH']
pos_hash=hash(tuple(round(c,6) for o in objs for v in o.data.vertices for c in (o.matrix_world@v.co)))
# 1 shared atlas (UV only)
bpy.ops.object.select_all(action='DESELECT')
for o in objs: o.select_set(True)
bpy.context.view_layer.objects.active=objs[0]
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=0.004,scale_to_bounds=False)
bpy.ops.uv.pack_islands(margin=0.004); bpy.ops.object.mode_set(mode='OBJECT')
# 2 mouth-interior mask as a color attribute (geometric: inward-facing cavity surfaces + throat cup)
mo=bpy.data.objects['mouth']; M=mo.matrix_world; ws=[M@v.co for v in mo.data.vertices]
cy=sum(p.y for p in ws)/len(ws); cz=sum(p.z for p in ws)/len(ws)
GCS={}
for o in objs:
    me=o.data; R=o.matrix_world.to_3x3()
    # smooth concavity: laplacian depth along normal / mean edge length, diffused GI iterations
    bmc=bmesh.new(); bmc.from_mesh(me); bmc.verts.ensure_lookup_table(); bmc.normal_update()
    d=[0.0]*len(bmc.verts)
    for v in bmc.verts:
        nb=[e.other_vert(v) for e in v.link_edges]
        if not nb: continue
        avg=sum((u.co for u in nb),mathutils.Vector())/len(nb); el=sum((u.co-v.co).length for u in nb)/len(nb)
        d[v.index]=max(0.0,(avg-v.co).dot(v.normal)/max(el,1e-6))
    for _ in range(GI):
        d=[ (d[v.index]+sum(d[e.other_vert(v).index] for e in v.link_edges))/(1+len(v.link_edges)) for v in bmc.verts]
    GC=d; GCS[o.name]=d; bmc.free(); sd=sorted(d); print('GSTAT',o.name,[round(sd[int(len(sd)*q)],3) for q in (0.5,0.8,0.9,0.95,0.98,0.995)])
    ca=me.color_attributes.new('mmask','FLOAT_COLOR','POINT')
    for v in me.vertices:
        p=o.matrix_world@v.co; n=(R@v.normal).normalized(); r=mathutils.Vector((0,p.y-cy,p.z-cz))
        m=0.0
        if p.x>0.12 and r.length>1e-4:
            inward=-n.dot(r.normalized()); facing=n.x
            if inward>0.25 and p.x<0.58: m=min(1,(inward-0.25)/0.4)
            if facing>0.45 and r.length<0.22 and p.x<0.47: m=max(m,1.0)
        deep=max(0.0,min(1.0,(0.55-p.x)/0.35))
        ca.data[v.index].color=(m,deep,GC[v.index],1)
# 3 procedural material
mat=bpy.data.materials.new('aliens_b_proc'); mat.use_nodes=True; nt=mat.node_tree; N=nt.nodes; L=nt.links
for n in list(N): N.remove(n)
outn=N.new('ShaderNodeOutputMaterial'); bsdf=N.new('ShaderNodeBsdfPrincipled')
def lin(c): return tuple((x/255)**2.2 for x in c)+(1,)
def mix(a,b,f,op='MIX'):
    m=N.new('ShaderNodeMix'); m.data_type='RGBA'; m.blend_type=op
    for src,sock in ((f,0),(a,6),(b,7)):
        if isinstance(src,(int,float)): m.inputs[sock].default_value=src
        elif isinstance(src,tuple): m.inputs[sock].default_value=src
        else: L.new(src,m.inputs[sock])
    return m.outputs[2]
def mr(x,fa,fb,ta=0,tb=1):
    m=N.new('ShaderNodeMapRange'); m.inputs[1].default_value=fa; m.inputs[2].default_value=fb; m.inputs[3].default_value=ta; m.inputs[4].default_value=tb; m.clamp=True; L.new(x,m.inputs[0]); return m.outputs[0]
geo=N.new('ShaderNodeNewGeometry'); sep=N.new('ShaderNodeSeparateXYZ'); L.new(geo.outputs['Normal'],sep.inputs[0])
ao=N.new('ShaderNodeAmbientOcclusion'); ao.samples=32; ao.inputs['Distance'].default_value=0.12
noise=N.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=7.0; noise.inputs['Detail'].default_value=4.0
noise2=N.new('ShaderNodeTexNoise'); noise2.inputs['Scale'].default_value=28.0; noise2.inputs['Detail'].default_value=2.0
attr=N.new('ShaderNodeAttribute'); attr.attribute_name='mmask'; asep=N.new('ShaderNodeSeparateColor'); L.new(attr.outputs['Color'],asep.inputs[0])
base=lin((240,96,10)); dark=lin((196,50,14)); hi=lin((250,150,40)); under=lin((190,52,28)); seam=lin((62,16,6))
c=mix(base,dark,mr(noise.outputs['Fac'],0.0,1.0,0,0)) if False else base
c=mix(c,hi,mr(sep.outputs['Z'],0.55,0.95,0,0.35))                    # lit tops a touch warmer/lighter (master highlight band)
c=mix(c,under,mr(sep.outputs['Z'],0.15,-0.6,0,0.95))               # red-orange underside (master)
pt=geo.outputs['Pointiness']
groove=mr(asep.outputs['Blue'],PT0,PT1)                                                  # 0 flat/convex -> 1 deep concave (smooth, vertex-interpolated)
c=mix(c,seam,groove)
mouthc=mix(lin((10,2,1)),lin((88,16,6)),mr(asep.outputs['Green'],0.75,0.15)) # interior: maroon at rim -> near-black deep
c=mix(c,mouthc,asep.outputs['Red'])
L.new(c,bsdf.inputs['Base Color'])
rough=mr(groove,0,1,0.6,0.75); rough=mix((0.5,0.5,0.5,1),(0.8,0.8,0.8,1),mr(ao.outputs['AO'],0.8,0.3)) if False else rough
L.new(rough,bsdf.inputs['Roughness']); bsdf.inputs['Metallic'].default_value=0.0
em=N.new('ShaderNodeMath'); em.operation='MULTIPLY'; L.new(asep.outputs['Red'],em.inputs[0])
em2=N.new('ShaderNodeMath'); em2.operation='POWER'; em2.inputs[1].default_value=4.0; L.new(asep.outputs['Green'],em2.inputs[0]); L.new(em2.outputs[0],em.inputs[1])
L.new(em.outputs[0],bsdf.inputs['Emission Strength']); bsdf.inputs['Emission Color'].default_value=lin((255,120,30))
bp=N.new('ShaderNodeBump'); bp.inputs['Strength'].default_value=BS; bp.inputs['Distance'].default_value=0.01; bp.invert=True
gm=N.new('ShaderNodeMath'); gm.operation='MULTIPLY'; gm.inputs[1].default_value=1.0; L.new(groove,gm.inputs[0]); L.new(gm.outputs[0],bp.inputs['Height']); L.new(bp.outputs['Normal'],bsdf.inputs['Normal'])
L.new(bsdf.outputs[0],outn.inputs[0])
for o in objs: o.data.materials.clear(); o.data.materials.append(mat)
# 4 bake
s.render.engine='CYCLES'; s.cycles.samples=SPP; s.cycles.device='GPU'
try:
    pr=bpy.context.preferences.addons['cycles'].preferences; pr.compute_device_type='CUDA'; pr.get_devices(); [setattr(d,'use',True) for d in pr.devices]
except Exception as e: print('GPU',e)
def img(n,col=True):
    i=bpy.data.images.new(n,RES,RES,alpha=False,float_buffer=False); i.colorspace_settings.name='sRGB' if col else 'Non-Color'; return i
imgs={'normal':img('normal',False),'basecolor':img('basecolor'),'ao':img('ao',False),'rough':img('rough',False),'emission':img('emission')}
tn=N.new('ShaderNodeTexImage'); N.active=tn
bk=s.render.bake; bk.margin=6; bk.use_clear=True
bpy.ops.object.select_all(action='DESELECT')
for o in objs: o.select_set(True)
def bake(key,typ,**kw):
    tn.image=imgs[key]; N.active=tn
    bpy.ops.object.bake(type=typ,**kw); imgs[key].filepath_raw=os.path.join(out,key+'.png'); imgs[key].file_format='PNG'; imgs[key].save(); print('BAKED',key)
bake('basecolor','DIFFUSE',pass_filter={'COLOR'})
bake('ao','AO')
# normal map: bake from a groove-weighted SMOOTHED copy onto the real mesh (selected-to-active). Real geometry untouched.
tn.image=imgs['normal']; N.active=tn; first=True
for o in objs:
    hi=o.copy(); hi.data=o.data.copy(); bpy.context.scene.collection.objects.link(hi)
    vg=hi.vertex_groups.new(name='gw'); g=GCS[o.name]; mx=max(PT1,1e-6)
    for i,val in enumerate(g): vg.add([i],min(1.0,val/mx)*0.9+0.1,'REPLACE')
    sm=hi.modifiers.new('sm','SMOOTH'); sm.factor=0.8; sm.iterations=SMI2; sm.vertex_group='gw'
    bpy.context.view_layer.objects.active=hi; bpy.ops.object.modifier_apply(modifier='sm')
    bpy.ops.object.select_all(action='DESELECT'); hi.select_set(True); o.select_set(True); bpy.context.view_layer.objects.active=o
    bk.use_selected_to_active=True; bk.cage_extrusion=0.01; bk.max_ray_distance=0.03; bk.use_clear=first
    bpy.ops.object.bake(type='NORMAL',normal_space='TANGENT'); first=False
    bpy.data.objects.remove(hi)
bk.use_selected_to_active=False; bk.use_clear=True
imgs['normal'].filepath_raw=os.path.join(out,'normal.png'); imgs['normal'].file_format='PNG'; imgs['normal'].save(); print('BAKED normal (smoothed hi->lo)')
bpy.ops.object.select_all(action='DESELECT')
for o in objs: o.select_set(True)
bake('rough','ROUGHNESS')
bake('emission','EMIT')
# 5 pack ORM: R=AO, G=rough, B=metal(0)
A=list(imgs['ao'].pixels); Rg=list(imgs['rough'].pixels); orm=bpy.data.images.new('orm',RES,RES,alpha=False); orm.colorspace_settings.name='Non-Color'
px=[0.0]*(RES*RES*4)
for i in range(0,len(px),4): px[i]=A[i]; px[i+1]=Rg[i]; px[i+2]=0.0; px[i+3]=1.0
orm.pixels=px; orm.filepath_raw=os.path.join(out,'orm.png'); orm.file_format='PNG'; orm.save(); print('PACKED orm')
# 6 export material: image Principled + glTF occlusion
fm=bpy.data.materials.new('aliens_b'); fm.use_nodes=True; ft=fm.node_tree; FN=ft.nodes; FL=ft.links; fb=FN['Principled BSDF']
def tex(path,col):
    t=FN.new('ShaderNodeTexImage'); t.image=bpy.data.images.load(path); t.image.colorspace_settings.name='sRGB' if col else 'Non-Color'; return t
tb=tex(os.path.join(out,'basecolor.png'),True); to=tex(os.path.join(out,'orm.png'),False); te=tex(os.path.join(out,'emission.png'),True)
FL.new(tb.outputs['Color'],fb.inputs['Base Color'])
so=FN.new('ShaderNodeSeparateColor'); FL.new(to.outputs['Color'],so.inputs[0]); FL.new(so.outputs['Green'],fb.inputs['Roughness']); FL.new(so.outputs['Blue'],fb.inputs['Metallic'])
FL.new(te.outputs['Color'],fb.inputs['Emission Color'])
tn2=tex(os.path.join(out,'normal.png'),False); nm=FN.new('ShaderNodeNormalMap'); FL.new(tn2.outputs['Color'],nm.inputs['Color']); FL.new(nm.outputs['Normal'],fb.inputs['Normal']); fb.inputs['Emission Strength'].default_value=EMIT; fb.inputs['Specular IOR Level'].default_value=0.3
g=bpy.data.node_groups.get('glTF Material Output') or bpy.data.node_groups.new('glTF Material Output','ShaderNodeTree')
if not g.interface.items_tree: g.interface.new_socket('Occlusion',in_out='INPUT',socket_type='NodeSocketFloat')
gn=FN.new('ShaderNodeGroup'); gn.node_tree=g; FL.new(so.outputs['Red'],gn.inputs['Occlusion'])
for o in objs:
    o.data.materials.clear(); o.data.materials.append(fm)
    if 'mmask' in o.data.color_attributes: o.data.color_attributes.remove(o.data.color_attributes['mmask'])
pos_hash2=hash(tuple(round(c,6) for o in objs for v in o.data.vertices for c in (o.matrix_world@v.co)))
print('GEOMETRY_FROZEN',pos_hash==pos_hash2,'TRIS',sum(len(o.data.polygons) for o in objs))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out,'aliens_b_mat.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(out,'aliens_b.glb'),export_format='GLB',export_yup=True,export_apply=True,export_tangents=True,export_draco_mesh_compression_enable=False,export_image_format='AUTO')

# MATERIALS-FINAL-2 micro-surface: procedural height (flesh pits+grain / bark fissures on feet+horns / smooth pods),
# region-gated by the rasterized region map, CPU-baked to a tangent normal map + height map; height folded into colour/roughness.
import bpy,sys,numpy as np
a=sys.argv[sys.argv.index('--')+1:]; OUT=a[0]; RES=2048; BSTR=float(a[1]); BDIST=float(a[2])
s=bpy.context.scene; s.render.engine='CYCLES'; s.cycles.device='CPU'; s.cycles.samples=1; s.render.bake.use_selected_to_active=False; s.render.bake.margin=16
ms=[o for o in bpy.data.objects if o.type=='MESH']
reg=bpy.data.images.load(OUT+'\\aliens_node_region.png'); reg.colorspace_settings.name='Non-Color'
mat=bpy.data.materials.new('bake'); mat.use_nodes=True; nt=mat.node_tree; N=nt.nodes; L=nt.links
for n in list(N): N.remove(n)
def node(t,**kw):
    n=N.new(t)
    for k,v in kw.items(): setattr(n,k,v)
    return n
def math_(op,a_,b_=None):
    m=node('ShaderNodeMath',operation=op)
    for i,v in enumerate([a_,b_]):
        if v is None: continue
        if isinstance(v,(int,float)): m.inputs[i].default_value=v
        else: L.new(v,m.inputs[i])
    return m.outputs[0]
def mrange(v,a0,a1,b0=0,b1=1):
    m=node('ShaderNodeMapRange'); m.clamp=True; L.new(v,m.inputs['Value']); m.inputs['From Min'].default_value=a0; m.inputs['From Max'].default_value=a1; m.inputs['To Min'].default_value=b0; m.inputs['To Max'].default_value=b1; return m.outputs['Result']
geo=node('ShaderNodeNewGeometry'); pos=geo.outputs['Position']
# flesh: sparse round pits (voronoi F1) + fine grain
vor=node('ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value=95; vor.inputs['Randomness'].default_value=0.9; L.new(pos,vor.inputs['Vector'])
pits=mrange(vor.outputs['Distance'],0.04,0.20)          # 0 in pit centre -> 1 on flesh
vor2=node('ShaderNodeTexVoronoi'); vor2.inputs['Scale'].default_value=300; L.new(pos,vor2.inputs['Vector'])
pits2=mrange(vor2.outputs['Distance'],0.02,0.09)
grain=node('ShaderNodeTexNoise'); grain.inputs['Scale'].default_value=650; grain.inputs['Detail'].default_value=2; L.new(pos,grain.inputs['Vector'])
flesh=math_('ADD',math_('MULTIPLY',math_('MULTIPLY',pits,pits2),0.85),math_('MULTIPLY',grain.outputs['Fac'],0.15))
# bark: anisotropic noise, fissures along the length. horns: stretched along Z. feet: along the radial direction (vary with angle and height).
sep=node('ShaderNodeSeparateXYZ'); L.new(pos,sep.inputs[0])
ang=math_('ARCTAN2',sep.outputs['Y'],sep.outputs['X']); rad=math_('SQRT',math_('ADD',math_('MULTIPLY',sep.outputs['X'],sep.outputs['X']),math_('MULTIPLY',sep.outputs['Y'],sep.outputs['Y'])))
cf=node('ShaderNodeCombineXYZ'); L.new(math_('MULTIPLY',ang,7.0),cf.inputs[0]); L.new(math_('MULTIPLY',sep.outputs['Z'],11.0),cf.inputs[1]); L.new(math_('MULTIPLY',rad,0.6),cf.inputs[2])
nf=node('ShaderNodeTexNoise'); nf.inputs['Scale'].default_value=6; nf.inputs['Detail'].default_value=1.5; nf.inputs['Roughness'].default_value=0.55; L.new(cf.outputs[0],nf.inputs['Vector'])
ch=node('ShaderNodeCombineXYZ'); L.new(math_('MULTIPLY',sep.outputs['X'],70),ch.inputs[0]); L.new(math_('MULTIPLY',sep.outputs['Y'],70),ch.inputs[1]); L.new(math_('MULTIPLY',sep.outputs['Z'],9),ch.inputs[2])
nh=node('ShaderNodeTexNoise'); nh.inputs['Scale'].default_value=1; nh.inputs['Detail'].default_value=1.5; nh.inputs['Roughness'].default_value=0.55; L.new(ch.outputs[0],nh.inputs['Vector'])
barkF=mrange(math_('ABSOLUTE',math_('SUBTRACT',nf.outputs['Fac'],0.5)),0.0,0.05); barkH=mrange(math_('ABSOLUTE',math_('SUBTRACT',nh.outputs['Fac'],0.5)),0.0,0.05)
# region gate
ti=node('ShaderNodeTexImage'); ti.image=reg; uvn=node('ShaderNodeUVMap'); L.new(uvn.outputs[0],ti.inputs['Vector'])
rs=node('ShaderNodeSeparateColor'); L.new(ti.outputs['Color'],rs.inputs[0])
podm,hornm,footm=rs.outputs['Red'],rs.outputs['Green'],rs.outputs['Blue']
def mix(f,x,y):
    m=node('ShaderNodeMix'); m.data_type='FLOAT'; L.new(f,m.inputs['Factor']); 
    for i,v in ((2,x),(3,y)):
        if isinstance(v,(int,float)): m.inputs[i].default_value=v
        else: L.new(v,m.inputs[i])
    return m.outputs[0]
h=mix(footm,flesh,barkF); h=mix(hornm,h,barkH); h=mix(podm,h,1.0)
bump=node('ShaderNodeBump'); bump.inputs['Strength'].default_value=BSTR; bump.inputs['Distance'].default_value=BDIST; L.new(h,bump.inputs['Height'])
bs=node('ShaderNodeBsdfPrincipled'); L.new(bump.outputs['Normal'],bs.inputs['Normal'])
em=node('ShaderNodeEmission'); L.new(h,em.inputs['Color'])
out=node('ShaderNodeOutputMaterial')
tgt=node('ShaderNodeTexImage'); N.active=tgt; tgt.select=True
def bake(kind,name):
    im=bpy.data.images.new(name,RES,RES,alpha=False,float_buffer=False); im.colorspace_settings.name='Non-Color'; tgt.image=im; N.active=tgt
    for l in list(out.inputs['Surface'].links): L.remove(l)
    L.new((bs if kind=='NORMAL' else em).outputs[0],out.inputs['Surface'])
    if kind=='NORMAL': bpy.ops.object.bake(type='NORMAL',normal_space='TANGENT',margin=16,use_clear=True)
    else: bpy.ops.object.bake(type='EMIT',margin=16,use_clear=True)
    im.filepath_raw=OUT+'\\'+name+'.png'; im.file_format='PNG'; im.save(); print('BAKED',name); return im
keep={o.name:list(o.data.materials) for o in ms}
for o in ms: o.data.materials.clear(); o.data.materials.append(mat)
bpy.ops.object.select_all(action='DESELECT')
for o in ms: o.select_set(True)
bpy.context.view_layer.objects.active=ms[0]
I_N=bake('NORMAL','aliens_node_normal'); I_H=bake('EMIT','aliens_node_height')
for o in ms: o.data.materials.clear(); o.data.materials.append(bpy.data.materials['aliens_node'])
# fold height into base colour (pits/fissures a touch darker) and roughness (pits rougher)
H=np.array(I_H.pixels[:]).reshape(RES,RES,4)[...,0]
def load(nm):
    im=bpy.data.images[nm]; return im,np.array(im.pixels[:]).reshape(RES,RES,4)
ib,Bp=load('aliens_node_basecolor'); io,Op=load('aliens_node_orm')
dark=(1-H)
Bp[...,:3]*= (1-0.14*dark)[...,None]     # sRGB-space multiply, deliberate not mottled (single clean pattern)
Op[...,1]=np.clip(Op[...,1]+0.10*dark,0,1)
ib.pixels.foreach_set(Bp.ravel().astype(np.float32)); ib.save(); io.pixels.foreach_set(Op.ravel().astype(np.float32)); io.save()
# wire normal map into the export material
m2=bpy.data.materials['aliens_node']; nt2=m2.node_tree; P=nt2.nodes['Principled BSDF']
tn=nt2.nodes.new('ShaderNodeTexImage'); tn.image=I_N; I_N.colorspace_settings.name='Non-Color'; nm=nt2.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value=1.0
nt2.links.new(tn.outputs['Color'],nm.inputs['Color']); nt2.links.new(nm.outputs['Normal'],P.inputs['Normal'])
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=OUT+'\\aliens-node.glb',export_format='GLB',export_yup=True,export_apply=True,export_tangents=True,export_draco_mesh_compression_enable=False)
bpy.ops.wm.save_as_mainfile(filepath=OUT+'\\aliens-node-mat.blend'); print('DONE')

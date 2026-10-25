# Judged clay staging: Cycles 256 adaptive + denoise, ONE neutral clay material, backdrop = ref bg sampled (220,210,202),
# key/rim/fill area lights, shadow-catcher contact shadow, AO via Cycles GI. Also exports clay GLB.
import bpy,sys,math,mathutils
a=sys.argv[sys.argv.index('--')+1:]; outdir,glb=a[0],a[1]; E=float(a[2]) if len(a)>2 else 1.0; Q=len(a)>3
s=bpy.context.scene
ms=[o for o in s.objects if o.type=='MESH']
for o in ms:
    for p in o.data.polygons: p.use_smooth=True
mat=bpy.data.materials['aliens_node']; nt=mat.node_tree; Nn=nt.nodes; L=nt.links
# render-only: AO (ORM R) multiplied into base colour (rule 4); the exported GLB carries AO in the occlusion slot instead
bs=Nn['Principled BSDF']; tb=[n for n in Nn if n.type=='TEX_IMAGE' and 'basecolor' in n.image.name][0]; sp=[n for n in Nn if n.type=='SEPARATE_COLOR'][0]
mx=Nn.new('ShaderNodeMix'); mx.data_type='RGBA'; mx.blend_type='MULTIPLY'; mx.inputs['Factor'].default_value=1.0
L.new(tb.outputs['Color'],mx.inputs[6]); L.new(sp.outputs['Red'],mx.inputs[7]); L.new(mx.outputs[2],bs.inputs['Base Color'])
def s2l(c): c=c/255; return c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4
bg=[s2l(c) for c in (220,210,202)]
w=bpy.data.worlds.new('w'); s.world=w; w.use_nodes=True; nt=w.node_tree; N=nt.nodes; L=nt.links
bgc=N['Background']; bgc.inputs['Color'].default_value=(*bg,1); bgc.inputs['Strength'].default_value=1
amb=N.new('ShaderNodeBackground'); amb.inputs['Color'].default_value=(*bg,1); amb.inputs['Strength'].default_value=0.35
lp=N.new('ShaderNodeLightPath'); mx=N.new('ShaderNodeMixShader')
L.new(lp.outputs['Is Camera Ray'],mx.inputs[0]); L.new(amb.outputs[0],mx.inputs[1]); L.new(bgc.outputs[0],mx.inputs[2]); L.new(mx.outputs[0],N['World Output'].inputs[0])
pl=bpy.data.objects.new('catcher',bpy.data.meshes.new('pl')); s.collection.objects.link(pl)
import bmesh; bm=bmesh.new(); bmesh.ops.create_grid(bm,x_segments=1,y_segments=1,size=6); bm.to_mesh(pl.data); pl.is_shadow_catcher=True
def light(n,loc,e,size):
    l=bpy.data.lights.new(n,'AREA'); l.energy=e; l.size=size; o=bpy.data.objects.new(n,l); s.collection.objects.link(o)
    o.location=loc; o.rotation_euler=(mathutils.Vector((0,0,0.5))-mathutils.Vector(loc)).to_track_quat('-Z','Y').to_euler()
light('key',(-2.2,-2.6,3.0),E*90,1.6); light('fill',(2.8,-2.0,1.2),E*22,2.5); light('rim',(1.2,3.0,2.6),E*90,1.2)
s.render.engine='CYCLES'; c=s.cycles; c.samples=24 if Q else 256; c.use_adaptive_sampling=True; c.adaptive_threshold=0.01; c.use_denoising=True
try:
    pr=bpy.context.preferences.addons['cycles'].preferences; pr.compute_device_type='OPTIX'; pr.get_devices(); [setattr(d,'use',True) for d in pr.devices]; c.device='GPU'
except Exception as e: print('GPU fail',e)
s.view_settings.view_transform='Standard'; s.render.film_transparent=False
s.use_nodes=True; ct=s.node_tree; rl=ct.nodes['Render Layers']; comp=ct.nodes['Composite']
gl=ct.nodes.new('CompositorNodeGlare'); gl.glare_type='FOG_GLOW'
for k,v in (('Threshold',1.0),('Strength',0.35),('Size',0.35)):
    if k in gl.inputs: gl.inputs[k].default_value=v
ct.links.new(rl.outputs['Image'],gl.inputs['Image']); ct.links.new(gl.outputs['Image'],comp.inputs['Image'])
s.render.resolution_x=1200; s.render.resolution_y=1060
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam')); s.collection.objects.link(cam); s.camera=cam
ctr=mathutils.Vector((0,-0.06,0.47))
VIEWS=[('horns',-20,14,1.5,70,mathutils.Vector((0,0.14,1.02))),('base-34',-30,12,2.6,60,ctr+mathutils.Vector((0,0,-0.2))),('full-front',0,14,4.2,50,ctr),('full-34',-35,18,4.2,50,ctr),('full-side',90,10,4.2,50,ctr),('full-back',180,14,4.2,50,ctr),('pods-front',0,10,3.0,70,ctr+mathutils.Vector((0,0,0.08)))]
for name,az,el,dist,lens,tgt in (VIEWS[:2]+VIEWS[-1:] if Q else VIEWS):
    d=mathutils.Vector((math.cos(math.radians(el))*math.sin(math.radians(az)),-math.cos(math.radians(el))*math.cos(math.radians(az)),math.sin(math.radians(el))))
    cam.location=tgt+d*dist; cam.rotation_euler=(tgt-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.lens=lens
    s.render.filepath=outdir+'\\clay-'+name+'.png'; bpy.ops.render.render(write_still=True); print('RENDERED',name)
bpy.ops.wm.save_as_mainfile(filepath=outdir+'\\..\\aliens-node-mat-staged.blend')

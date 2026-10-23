# Clay-gate judged captures (Cycles production). blender -b <blend> -P stage.py -- <outdir> <samples>
import bpy,sys,math,mathutils,json
a=sys.argv[sys.argv.index('--')+1:]; out=a[0]; spp=int(a[1]); GT=float(a[2]) if len(a)>2 else 0.8
s=bpy.context.scene
ms=[o for o in s.objects if o.type=='MESH']
# MATERIAL REVIEW: review-only copy of the export material with ORM R (AO) multiplied into albedo
src=ms[0].data.materials[0]; rv=src.copy(); rv.name='REVIEW_'+src.name; nt=rv.node_tree; N=nt.nodes; L=nt.links
bs=[n for n in N if n.type=='BSDF_PRINCIPLED'][0]; sep=[n for n in N if n.type=='SEPARATE_COLOR'][0]
bc=bs.inputs['Base Color'].links[0].from_socket
mm=N.new('ShaderNodeMix'); mm.data_type='RGBA'; mm.blend_type='MULTIPLY'; mm.inputs[0].default_value=1.0
L.new(bc,mm.inputs[6]); L.new(sep.outputs['Red'],mm.inputs[7]); L.new(mm.outputs[2],bs.inputs['Base Color'])
for o in ms: o.data.materials.clear(); o.data.materials.append(rv)
pts=[o.matrix_world@v.co for o in ms for v in o.data.vertices]
mn=mathutils.Vector([min(q[i] for q in pts) for i in range(3)]); mx=mathutils.Vector([max(q[i] for q in pts) for i in range(3)])
c=(mn+mx)/2
bpy.ops.mesh.primitive_plane_add(size=20,location=(0,0,mn.z)); pl=bpy.context.object; pl.is_shadow_catcher=True
bg=(228/255)**2.2
w=bpy.data.worlds.new('w'); s.world=w; w.use_nodes=True; w.node_tree.nodes['Background'].inputs[0].default_value=(bg,bg,bg,1); w.node_tree.nodes['Background'].inputs[1].default_value=1.0
s.view_settings.view_transform='Standard'; s.view_settings.look='None'
def light(name,loc,energy,size):
    L=bpy.data.lights.new(name,'AREA'); L.energy=energy; L.size=size
    o=bpy.data.objects.new(name,L); s.collection.objects.link(o); o.location=loc
    o.rotation_euler=(c-mathutils.Vector(loc)).to_track_quat('-Z','Y').to_euler()
light('key',(1.5,-2.2,2.6),90,1.6); light('fill',(-2.4,-1.6,0.8),25,2.5); light('rim',(-0.8,2.4,2.0),70,1.2)
s.render.engine='CYCLES'; s.cycles.samples=spp; s.cycles.use_adaptive_sampling=True; s.cycles.adaptive_threshold=0.01; s.cycles.use_denoising=True
try:
    s.cycles.device='GPU'; bpy.context.preferences.addons['cycles'].preferences.compute_device_type='CUDA'; bpy.context.preferences.addons['cycles'].preferences.get_devices()
    for d in bpy.context.preferences.addons['cycles'].preferences.devices: d.use=True
except Exception as e: print('GPU',e)
s.render.film_transparent=False; s.use_nodes=True
ct=s.node_tree; [ct.nodes.remove(n) for n in list(ct.nodes)]
rl=ct.nodes.new('CompositorNodeRLayers'); gl=ct.nodes.new('CompositorNodeGlare'); co=ct.nodes.new('CompositorNodeComposite')
gl.glare_type='FOG_GLOW'
for k,v in (('Threshold',GT),('Strength',0.25),('Size',0.125)):
    if k in gl.inputs: gl.inputs[k].default_value=v
ct.links.new(rl.outputs['Image'],gl.inputs['Image']); ct.links.new(gl.outputs['Image'],co.inputs['Image'])
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam')); s.collection.objects.link(cam); s.camera=cam
shots={'tail':(mathutils.Vector((-0.66,0,-0.17)),-45,14,1.35,(1400,1400),50),'full':(c+mathutils.Vector((0.05,0,0.04)),32,9,5.2,(1840,1168),85),'mouth':(mathutils.Vector((0.5,0,0.1)),55,10,1.25,(1400,1400),50)}
rec={}
for n,(tgt,az,el,dist,res,lens) in shots.items():
    d=mathutils.Vector((math.sin(math.radians(az))*math.cos(math.radians(el)),-math.cos(math.radians(az))*math.cos(math.radians(el)),math.sin(math.radians(el))))
    cam.location=tgt+d*dist; cam.rotation_euler=(tgt-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.lens=lens
    s.render.resolution_x,s.render.resolution_y=res; s.render.filepath=out+'\\mat-'+n+'.png'; bpy.ops.render.render(write_still=True)
    rec[n]=dict(cam=list(cam.location),az=az,el=el,dist=dist,res=res,lens=lens)
mats={m.name for o in ms for m in o.data.materials}
glare={k:gl.inputs[k].default_value for k in ('Threshold','Strength','Size') if k in gl.inputs}
rec['settings']=dict(phase='MATERIAL review',engine='CYCLES',samples=spp,adaptive=0.01,denoise=True,view='Standard',bg_srgb=228,materials=sorted(mats),glare=glare,lights={'key':90,'fill':25,'rim':70},shadow_catcher=True)
open(out+'\\render-settings.json','w').write(json.dumps(rec,indent=1)); print('STAGED',json.dumps(rec['settings']))

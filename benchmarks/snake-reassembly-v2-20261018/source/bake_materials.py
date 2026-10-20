"""Bake existing UV'd P8 geometry to portable maps; resumable from per-map PNGs."""
import bpy,sys,json,hashlib,os,numpy as np
if "--" in sys.argv: os.chdir(sys.argv[sys.argv.index("--")+1])
from pathlib import Path
OUT=Path('material');TEX=OUT/'textures';TEX.mkdir(exist_ok=True)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=16
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='OPTIX'
sc.cycles.device='GPU';sc.render.bake.margin=8;sc.render.bake.use_clear=True;sc.render.bake.use_selected_to_active=False
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8'
baseline=json.load(open(OUT/'inventory.json'))
def fingerprint(me):
 v=np.array([v.co[:] for v in me.vertices],np.float32);f=[tuple(p.vertices) for p in me.polygons]
 return hashlib.sha256(v.tobytes()+repr(f).encode()).hexdigest()
sources=sorted([o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('SRC_')],key=lambda o:('Glow' in o.name,o.name))
state={o.name:(o.hide_render,o.hide_viewport) for o in bpy.data.objects}
for o in bpy.data.objects:
 if o.type=='MESH':o.hide_render=True
progress={}
def canonical(ob,images):
 me=ob.data;m=bpy.data.materials.new('PBR_'+ob.name.removeprefix('SRC_'));m.use_nodes=True;nt=m.node_tree;nt.nodes.clear();p=nt.nodes.new('ShaderNodeBsdfPrincipled');p.name='Surface';out=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(p.outputs[0],out.inputs[0])
 nodes={}
 for key,im in images.items():
  n=nt.nodes.new('ShaderNodeTexImage');n.name=key;n.image=im;nodes[key]=n
 nt.links.new(nodes['BaseColor'].outputs['Color'],p.inputs['Base Color'])
 sep=nt.nodes.new('ShaderNodeSeparateColor');sep.name='PackedORM';sep.mode='RGB';nt.links.new(nodes['ORM'].outputs['Color'],sep.inputs[0]);nt.links.new(sep.outputs['Green'],p.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],p.inputs['Metallic'])
 ao=nt.nodes.new('NodeReroute');ao.name='ORM_AO';nt.links.new(sep.outputs['Red'],ao.inputs[0])
 group=bpy.data.node_groups.get('glTF Material Output')
 if group is None:
  group=bpy.data.node_groups.new('glTF Material Output','ShaderNodeTree');group.interface.new_socket(name='Occlusion',in_out='INPUT',socket_type='NodeSocketFloat')
 g=nt.nodes.new('ShaderNodeGroup');g.node_tree=group;nt.links.new(sep.outputs['Red'],g.inputs['Occlusion'])
 normal=nt.nodes.new('ShaderNodeNormalMap');normal.uv_map=me.uv_layers.active.name;nt.links.new(nodes['Normal'].outputs['Color'],normal.inputs['Color']);nt.links.new(normal.outputs[0],p.inputs['Normal'])
 strength=1.8 if ob.name=='SRC_Head' else 1.2 if 'Glow' in ob.name else 0.
 nt.links.new(nodes['Emission'].outputs['Color'],p.inputs['Emission Color']);p.inputs['Emission Strength'].default_value=strength
 me.materials.clear();me.materials.append(m)
 for poly in me.polygons:poly.material_index=0
 for im in images.values():im.pack()
 return m
for ob in sources:
 print('BAKE_OBJECT',ob.name,flush=True);me=ob.data;assert fingerprint(me)==baseline[ob.name]['mesh_hash']
 bpy.ops.object.select_all(action='DESELECT');ob.hide_render=False;ob.hide_viewport=False;ob.hide_set(False);ob.select_set(True);bpy.context.view_layer.objects.active=ob
 size=4096 if ob.name=='SRC_Head' else 256 if 'Glow' in ob.name else 2048
 used=set(p.material_index for p in me.polygons);mats=[me.materials[i] for i in used];ims={}
 for channel in ['BaseColor','ORM','Normal','Emission']:
  path=TEX/(ob.name.removeprefix('SRC_')+'_'+channel+'.png')
  # Always rebake. Reusing an existing PNG shipped the stale M1d maps once.
  if False and path.exists():im=bpy.data.images.load(str(path.resolve()),check_existing=True);print('REUSE',path,flush=True)
  else:
   im=bpy.data.images.new(path.stem,width=size,height=size,alpha=False);im.colorspace_settings.name='sRGB' if channel in ('BaseColor','Emission') else 'Non-Color'
   restore=[]
   for m in mats:
    nt=m.node_tree;n=nt.nodes.new('ShaderNodeTexImage');n.name='BakeTarget';n.image=im
    for old in nt.nodes:old.select=False
    n.select=True;nt.nodes.active=n
    out=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL');link=out.inputs['Surface'].links[0];original=link.from_socket
    temp=[]
    if channel!='Normal':
     e=nt.nodes.new('ShaderNodeEmission');temp.append(e)
     if channel=='ORM':
      c=nt.nodes.new('ShaderNodeCombineColor');c.mode='RGB';temp.append(c)
      for key,inp in [('BAKE_AO','Red'),('BAKE_ROUGH','Green'),('BAKE_METAL','Blue')]:nt.links.new(nt.nodes[key].outputs[0],c.inputs[inp])
      socket=c.outputs[0]
     else:socket=nt.nodes['BAKE_COLOR' if channel=='BaseColor' else 'BAKE_EMISSION'].outputs[0]
     nt.links.new(socket,e.inputs['Color']);e.inputs['Strength'].default_value=1;nt.links.new(e.outputs[0],out.inputs['Surface'])
    restore.append((nt,out,original,temp,n))
   print('BAKE_START',ob.name,channel,size,flush=True)
   bpy.ops.object.bake(type='NORMAL' if channel=='Normal' else 'EMIT',normal_space='TANGENT')
   im.filepath_raw=str(path.resolve());im.file_format='PNG';im.save()
   for nt,out,original,temp,target in restore:
    nt.links.new(original,out.inputs['Surface'])
    for n in temp+[target]:nt.nodes.remove(n)
   print('BAKE_DONE',path,flush=True)
  im.colorspace_settings.name='sRGB' if channel in ('BaseColor','Emission') else 'Non-Color';ims[channel]=im
 canonical(ob,ims);assert fingerprint(me)==baseline[ob.name]['mesh_hash'];ob.hide_render=True;ob.hide_viewport=True
 progress[ob.name]={'size':size,'maps':{k:str(Path(i.filepath).name) for k,i in ims.items()},'mesh_hash_unchanged':True}
 (OUT/'bake-progress.json').write_text(json.dumps(progress,indent=2))
for o in bpy.data.objects:
 if o.name in state:o.hide_render,o.hide_viewport=state[o.name]
for o in bpy.data.objects:o.select_set(False)
for o in bpy.data.objects:
 if o.type=='MESH' and not o.hide_render:o.hide_viewport=False;o.hide_set(False);o.select_set(True)
bpy.ops.wm.save_as_mainfile(filepath=str((OUT/'m4-mapped.blend').resolve()))
bpy.ops.export_scene.gltf(filepath=str((OUT/'snake-p8-material.glb').resolve()),export_format='GLB',use_selection=True,export_apply=False,export_materials='EXPORT',export_image_format='AUTO',export_yup=True)
print('MAPS_AND_EXPORT_COMPLETE',flush=True)

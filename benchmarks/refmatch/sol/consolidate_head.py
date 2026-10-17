"""Consolidate mechanical head into one opaque PBR atlas + one optical cover.
All maps use one UV0 in the final game mesh. AO is a real Cycles contact bake.
"""
import bpy,os,numpy as np

def consolidate_head(low,root):
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24
 scene.render.bake.use_selected_to_active=False;scene.render.bake.use_clear=True;scene.render.bake.margin=16
 low.data.uv_layers.active_index=1;low.data.uv_layers['BakeUV'].active_render=True
 original=list(low.data.materials);original_indices=[p.material_index for p in low.data.polygons]
 bpy.ops.object.select_all(action='DESELECT');low.select_set(True);bpy.context.view_layer.objects.active=low
 images={}
 def image(name,space):
  im=bpy.data.images.new('Head_Atlas_'+name,width=2048,height=2048,alpha=False);im.colorspace_settings.name=space;images[name]=im;return im
 def assign_targets(im,channel=None):
  for i,old in enumerate(original):
   m=old.copy();low.data.materials[i]=m;n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
   if channel:
    if channel=='emission':
     inp=p.inputs['Emission Color'];factor=p.inputs['Emission Strength'].default_value/3.5
    else:inp=p.inputs[channel];factor=1
    socket=inp.links[0].from_socket if inp.is_linked else None
    value=tuple(inp.default_value) if hasattr(inp.default_value,'__len__') else (inp.default_value,)*4
    for key in ['Base Color','Metallic','Emission Color','Emission Strength','Alpha']:
     for link in list(p.inputs[key].links):l.remove(link)
    p.inputs['Base Color'].default_value=(0,0,0,1);p.inputs['Metallic'].default_value=0;p.inputs['Alpha'].default_value=1;p.inputs['Emission Strength'].default_value=1
    if socket and factor>0:l.new(socket,p.inputs['Emission Color'])
    else:p.inputs['Emission Color'].default_value=tuple(float(v)*factor for v in value[:3])+(1,)
   t=n.new('ShaderNodeTexImage');t.image=im;n.active=t
 def bake(name,space,kind,channel=None):
  im=image(name,space);assign_targets(im,channel);bpy.ops.object.bake(type=kind);return im
 bake('normal','Non-Color','NORMAL')
 bake('albedo','sRGB','EMIT','Base Color')
 bake('roughness','Non-Color','EMIT','Roughness')
 bake('metallic','Non-Color','EMIT','Metallic')
 bake('emission','sRGB','EMIT','emission')
 bake('ao','Non-Color','AO')
 count=2048*2048*4
 def pixels(name):
  values=np.empty(count,dtype=np.float32);images[name].pixels.foreach_get(values);return values.reshape(-1,4)
 orm=image('orm','Non-Color');arr=np.ones((2048*2048,4),dtype=np.float32)
 arr[:,0]=pixels('ao')[:,0];arr[:,1]=pixels('roughness')[:,0];arr[:,2]=pixels('metallic')[:,0];orm.pixels.foreach_set(arr.ravel());orm.update()
 for name in ['albedo','normal','orm','emission']:
  im=images[name];im.filepath_raw=os.path.join(root,'textures','head_atlas_'+name+'.png');im.file_format='PNG';im.save()
 # All texture coordinates are now the same. No normal-on-UV2 engine dependency.
 low.data.uv_layers.remove(low.data.uv_layers['UVMap']);low.data.uv_layers['BakeUV'].name='UVMap';low.data.uv_layers.active_index=0
 m=bpy.data.materials.new('Head_Atlas_Principled');m.use_nodes=True;m.use_backface_culling=True;n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
 def tex(name):
  t=n.new('ShaderNodeTexImage');t.image=images[name];return t
 l.new(tex('albedo').outputs['Color'],p.inputs['Base Color'])
 normal=n.new('ShaderNodeNormalMap');normal.uv_map='UVMap';l.new(tex('normal').outputs['Color'],normal.inputs['Color']);l.new(normal.outputs['Normal'],p.inputs['Normal'])
 sep=n.new('ShaderNodeSeparateColor');l.new(tex('orm').outputs['Color'],sep.inputs[0]);l.new(sep.outputs['Green'],p.inputs['Roughness']);l.new(sep.outputs['Blue'],p.inputs['Metallic'])
 group=n.new('ShaderNodeGroup');group.node_tree=bpy.data.node_groups['glTF Material Output'];l.new(sep.outputs['Red'],group.inputs['Occlusion'])
 l.new(tex('emission').outputs['Color'],p.inputs['Emission Color']);p.inputs['Emission Color'].default_value=(1,1,1,1);p.inputs['Emission Strength'].default_value=3.5
 glass=next(old for old in original if 'Optical_Lens_Cover' in old.name)
 # The optical cover has scalar properties only, so its old UV nodes are irrelevant.
 low.data.materials.clear();low.data.materials.append(m);low.data.materials.append(glass)
 for poly,old_index in zip(low.data.polygons,original_indices):poly.material_index=1 if 'Optical_Lens_Cover' in original[old_index].name else 0
 bpy.ops.object.select_all(action='DESELECT')
 print('HEAD_UNIFIED_ATLAS_COMPLETE: all PBR maps UV0, contact AO in ORM.R')

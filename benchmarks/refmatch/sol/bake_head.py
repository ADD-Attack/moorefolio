"""High-to-low head normal bake. Called by build_snake.py inside Blender.
Original trim UV retained for albedo/ORM. A unique padded second UV set carries
MikkTSpace selected-to-active normals from a beveled and micro-displaced high.
"""
import bpy,os,math

def bake_head(low,root):
 scene=bpy.context.scene
 bpy.ops.object.select_all(action='DESELECT');low.select_set(True);bpy.context.view_layer.objects.active=low
 # Freeze exact delivery triangles before unwrapping and baking.
 mod=low.modifiers.new('Bake_Triangulate','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=mod.name)
 high=low.copy();high.data=low.data.copy();high.name='Bake_High_Head';bpy.context.collection.objects.link(high)
 bevel=high.modifiers.new('High_Machined_Radii','BEVEL');bevel.width=.0018;bevel.segments=3;bevel.limit_method='ANGLE';bevel.angle_limit=.38
 # Fine high-only dents, not subdivision inflation of the delivery geometry.
 noise=bpy.data.textures.new('High_Head_Micro_Dents',type='CLOUDS');noise.noise_scale=.024;noise.noise_depth=2
 disp=high.modifiers.new('High_Surface_Wear','DISPLACE');disp.texture=noise;disp.strength=.00045;disp.mid_level=.5
 low.data.uv_layers.new(name='BakeUV');low.data.uv_layers.active_index=1;low.data.uv_layers['BakeUV'].active_render=True
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(65),island_margin=.008,area_weight=.3,scale_to_bounds=True);bpy.ops.object.mode_set(mode='OBJECT')
 image=bpy.data.images.new('Head_Selected_To_Active_Normal',width=2048,height=2048,alpha=False);image.generated_color=(.5,.5,1,1);image.colorspace_settings.name='Non-Color'
 # Low-only material copies preserve the original shader normal sources on high.
 for i,m in enumerate(list(low.data.materials)):
  cp=m.copy();cp.name='HeadBake_'+m.name;low.data.materials[i]=cp
  target=cp.node_tree.nodes.new('ShaderNodeTexImage');target.name='BAKE_TARGET';target.image=image;cp.node_tree.nodes.active=target
 scene.render.engine='CYCLES';scene.cycles.samples=16
 try:
  prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='CUDA';prefs.get_devices()
  for d in prefs.devices:d.use=d.type=='CUDA'
  scene.cycles.device='GPU' if any(d.type=='CUDA' for d in prefs.devices) else 'CPU'
 except:pass
 scene.render.bake.use_selected_to_active=True;scene.render.bake.use_cage=False;scene.render.bake.cage_extrusion=.0025;scene.render.bake.max_ray_distance=.006;scene.render.bake.margin=16
 scene.render.bake.normal_space='TANGENT';scene.render.bake.use_clear=True
 bpy.ops.object.select_all(action='DESELECT');high.select_set(True);low.select_set(True);bpy.context.view_layer.objects.active=low
 bpy.ops.object.bake(type='NORMAL')
 image.filepath_raw=os.path.join(root,'textures','head_baked_normal.png');image.file_format='PNG';image.save()
 # The exporter calculates one tangent basis per mesh. BakeUV is the active
 # render UV, so tangents and every head normal texture use the SAME basis.
 # Original trim color/ORM/emission samplers explicitly keep UVMap (UV0).
 for mat in low.data.materials:
  nt=mat.node_tree;target=nt.nodes.get('BAKE_TARGET');original_uv=nt.nodes.new('ShaderNodeUVMap');original_uv.uv_map='UVMap'
  for tex in [node for node in nt.nodes if node.type=='TEX_IMAGE' and node!=target]:nt.links.new(original_uv.outputs['UV'],tex.inputs['Vector'])
  if not ('Head_Worn_Gunmetal' in mat.name or 'Woven_Steel' in mat.name):continue
  uv=nt.nodes.new('ShaderNodeUVMap');uv.uv_map='BakeUV';nt.links.new(uv.outputs['UV'],target.inputs['Vector'])
  p=nt.nodes.get('Principled BSDF');nm=nt.nodes.new('ShaderNodeNormalMap');nm.uv_map='BakeUV';nm.inputs['Strength'].default_value=1;nt.links.new(target.outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],p.inputs['Normal'])
 low.data.uv_layers.active_index=1;low.data.uv_layers['BakeUV'].active_render=True
 bpy.data.objects.remove(high,do_unlink=True)
 bpy.ops.object.select_all(action='DESELECT')
 print('HEAD_HIGH_LOW_BAKE',image.filepath_raw)

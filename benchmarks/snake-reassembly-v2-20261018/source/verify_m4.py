"""Independent M4 geometry/UV, active-stage and baked-map checks. Run after final renders."""
import bpy,sys,os,json,hashlib,numpy as np
from pathlib import Path
T=Path(sys.argv[sys.argv.index('--')+1]);os.chdir(T);O=T/'material'
def imagehash(im):
 return hashlib.sha256(bytes(im.packed_file.data)).hexdigest() if im.packed_file else None
def stage(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));s=bpy.context.scene;w=s.world.node_tree.nodes['Background'];cam=s.camera
 result={'engine':s.render.engine,'device':s.cycles.device,'samples':s.cycles.samples,'adaptive':s.cycles.use_adaptive_sampling,'threshold':s.cycles.adaptive_threshold,'denoise':s.cycles.use_denoising,'denoiser':s.cycles.denoiser,'resolution':[s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage],'film_transparent':s.render.film_transparent,'view':[s.view_settings.view_transform,s.view_settings.look,s.view_settings.exposure,s.view_settings.gamma],'world':[list(w.inputs['Color'].default_value),w.inputs['Strength'].default_value],'camera':{'matrix':[list(r) for r in cam.matrix_world],'lens':cam.data.lens,'sensor_width':cam.data.sensor_width,'clip':[cam.data.clip_start,cam.data.clip_end],'dof':cam.data.dof.use_dof},'lights':[]}
 for ob in sorted(s.objects,key=lambda o:o.name):
  if ob.type=='LIGHT':result['lights'].append({'name':ob.name,'matrix':[list(r) for r in ob.matrix_world],'type':ob.data.type,'energy':ob.data.energy,'size':ob.data.size,'color':list(ob.data.color)})
 catch=bpy.data.objects['STAGE_catcher'];result['catcher']={'matrix':[list(r) for r in catch.matrix_world],'dimensions':list(catch.dimensions),'is_shadow_catcher':catch.is_shadow_catcher}
 gl=s.node_tree.nodes['MaterialBloom'];bg=next(n for n in s.node_tree.nodes if n.type=='RGB');result['compositor']={'background':list(bg.outputs[0].default_value),'glare_type':gl.glare_type,'quality':gl.quality,'sockets':{k:gl.inputs[k].default_value for k in ['Threshold','Strength','Size']},'links':sorted((l.from_node.bl_idname,l.from_socket.name,l.to_node.bl_idname,l.to_socket.name) for l in s.node_tree.links)}
 return result
baseline=stage(O/'m3-staged.blend');current=stage(O/'m4-staged.blend')
assert baseline==current,{k:(baseline[k],current[k]) for k in baseline if baseline[k]!=current[k]}
assert current['engine']=='CYCLES' and current['device']=='GPU' and current['samples']==256 and current['denoiser']=='OPENIMAGEDENOISE'
assert current['resolution']==[1920,1080,100]
review=[]
for m in {m for ob in bpy.context.scene.objects if ob.type=='MESH' and not ob.hide_render and not ob.name.startswith('STAGE_') for m in ob.data.materials if m}:
 nt=m.node_tree;ao=nt.nodes.get('REVIEW_AO');assert ao and ao.blend_type=='MULTIPLY';assert ao.inputs[2].links[0].from_node.name=='ORM_AO';r=nt.nodes['ORM_AO'];assert r.inputs[0].links[0].from_socket.name=='Red';sep=r.inputs[0].links[0].from_node;assert sep.inputs[0].links[0].from_node.name=='ORM';assert nt.nodes['Surface'].inputs['Base Color'].links[0].from_node==ao
 review.append({'material':m.name,'ao_applied':True,'packed_images':{n.name:imagehash(n.image) for n in nt.nodes if n.type=='TEX_IMAGE'}})
# Separate check: no UV changes except the authorized optical assembly allocation.
bpy.ops.wm.open_mainfile(filepath=str(O/'m3-procedural.blend'));uvbase={};non_eye={}
for ob in bpy.data.objects:
 if ob.name.startswith('SRC_') and ob.type=='MESH':
  uvbase[ob.name]=np.array([u.uv[:] for u in ob.data.uv_layers.active.data],np.float32)
  non_eye[ob.name]=[li for p in ob.data.polygons if not ob.data.materials[p.material_index].name.startswith('Optic_') for li in p.loop_indices]
bpy.ops.wm.open_mainfile(filepath=str(O/'m4-procedural.blend'));uvreport={}
for ob in bpy.data.objects:
 if ob.name in uvbase:
  uv=np.array([u.uv[:] for u in ob.data.uv_layers.active.data],np.float32);indices=non_eye[ob.name];assert np.array_equal(uv[indices],uvbase[ob.name][indices]);uvreport[ob.name]={'all_non_optic_uv_exactly_unchanged':True,'all_uv_unchanged':bool(np.array_equal(uv,uvbase[ob.name]))}
a=json.load(open(O/'captures/m3-render-settings.json'));b=json.load(open(O/'captures/m4-render-settings.json'));assert a==b
(O/'m4-verification.json').write_text(json.dumps({'active_staging_identical':True,'baseline':baseline,'m4':current,'review_material_checks':review,'uv_checks':uvreport,'frozen_camera_records_identical':True},indent=2))
print('M4_ACTIVE_STAGE_UV_AO_PASS',flush=True)

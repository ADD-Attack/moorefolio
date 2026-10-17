import bpy, os,json
from mathutils import Vector
D=os.environ.get('ASSEMBLY_WORKDIR','D:/OpenClaw/assembly-sol-op-20261017')
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene
sc.render.engine='BLENDER_WORKBENCH';sc.render.resolution_x=1000;sc.render.resolution_y=1000;sc.render.resolution_percentage=100
sc.world.color=(.3,.3,.3);sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_shadows=True;sc.display.shading.show_cavity=True
for name in ['head','segment2','tail']:
 bpy.ops.import_scene.gltf(filepath=f'{D}/hunyuan-{name}.glb')
 obs=[o for o in sc.objects if o.type=='MESH']
 print('SOURCE',name,[(o.name,len(o.data.vertices),len(o.data.polygons),[list(v) for v in o.bound_box]) for o in obs],flush=True)
 for o in obs:o.hide_render=False
 pts=[o.matrix_world@Vector(c) for o in obs for c in o.bound_box];mi=Vector([min(v[i] for v in pts) for i in range(3)]);ma=Vector([max(v[i] for v in pts) for i in range(3)]);center=(mi+ma)/2;size=max(ma-mi)
 for label,vec in [('front',(0,-1,0)),('side',(1,0,0)),('top',(0,0,1))]:
  bpy.ops.object.camera_add(location=center+Vector(vec)*size*3);cam=bpy.context.object;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=size*1.15;sc.camera=cam;sc.render.filepath=f'{D}/{name}-{label}.png';bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
 for o in list(sc.objects):bpy.data.objects.remove(o,do_unlink=True)

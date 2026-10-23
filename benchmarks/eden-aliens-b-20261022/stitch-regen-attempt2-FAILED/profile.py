# print radius profile of a Hunyuan element along its long axis (to locate body-margin -> transition -> tail)
import bpy,sys,mathutils
glb=sys.argv[sys.argv.index('--')+1]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=glb)
o=[o for o in bpy.context.scene.objects if o.type=='MESH'][0]; V=[o.matrix_world@v.co for v in o.data.vertices]
mn=mathutils.Vector([min(v[i] for v in V) for i in range(3)]); mx=mathutils.Vector([max(v[i] for v in V) for i in range(3)]); print('BOUNDS',[round(x,3) for x in mn],[round(x,3) for x in mx])
for k in range(-20,21):
    x=k/20; s=[v for v in V if abs(v.x-x)<0.025]
    if s: print('X %+.2f n %6d  y %+.2f..%+.2f  z %+.2f..%+.2f'%(x,len(s),min(v.y for v in s),max(v.y for v in s),min(v.z for v in s),max(v.z for v in s)))

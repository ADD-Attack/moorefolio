import bpy,sys
from collections import Counter
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=sys.argv[sys.argv.index('--')+1])
o=[o for o in bpy.context.scene.objects if o.type=='MESH'][0]; M=o.matrix_world
V=[M@v.co for v in o.data.vertices]
zs=Counter(round(v.z,2) for v in V); print('ZHIST',sorted(zs.items())[:14])
for z0 in [-0.5,-0.45,-0.4,-0.35,-0.3,-0.25,-0.2,-0.15,-0.1]:
    s=[v for v in V if abs(v.z-z0)<0.01]
    if s: print('Z',z0,'n',len(s),'x',round(min(v.x for v in s),2),round(max(v.x for v in s),2),'y',round(min(v.y for v in s),2),round(max(v.y for v in s),2))
for x0 in [-0.98,-0.9,-0.8,-0.7,-0.6,0.5,0.6,0.7,0.8,0.9]:
    s=[v for v in V if abs(v.x-x0)<0.01 and v.z>-0.45]
    if s: print('X',x0,'n',len(s),'y',round(min(v.y for v in s),2),round(max(v.y for v in s),2),'z',round(min(v.z for v in s),2),round(max(v.z for v in s),2))

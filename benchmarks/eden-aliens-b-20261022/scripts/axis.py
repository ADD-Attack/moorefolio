import bpy,sys,math,mathutils
glb=sys.argv[sys.argv.index('--')+1]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=glb)
o=[o for o in bpy.context.scene.objects if o.type=='MESH'][0]; V=[o.matrix_world@v.co for v in o.data.vertices]
# tail = verts far from the blob: x < -0.3
T=[v for v in V if v.x<-0.3]; cx=sum(v.x for v in T)/len(T); cy=sum(v.y for v in T)/len(T)
sxx=sum((v.x-cx)**2 for v in T); syy=sum((v.y-cy)**2 for v in T); sxy=sum((v.x-cx)*(v.y-cy) for v in T)
ang=0.5*math.atan2(2*sxy,sxx-syy); print('TAIL_YAW_DEG',round(math.degrees(ang),1),'centroid',round(cx,2),round(cy,2))
R=mathutils.Matrix.Rotation(-ang,3,'Z'); W=[R@v for v in V]
for k in range(-20,21):
    x=k/20; s=[v for v in W if abs(v.x-x)<0.025]
    if s: print('X %+.2f n %6d y %+.2f..%+.2f z %+.2f..%+.2f'%(x,len(s),min(v.y for v in s),max(v.y for v in s),min(v.z for v in s),max(v.z for v in s)))

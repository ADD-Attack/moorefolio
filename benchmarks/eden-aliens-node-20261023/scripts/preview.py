# blender -b -P preview.py -- <glb> <outprefix> : Workbench two-angle ITERATION PREVIEW (not judged)
import bpy,sys,math,mathutils
a=sys.argv[sys.argv.index('--')+1:]; glb,out=a[0],a[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
ms=[o for o in bpy.context.scene.objects if o.type=='MESH']
pts=[o.matrix_world@v.co for o in ms for v in o.data.vertices]
mn=mathutils.Vector([min(p[i] for p in pts) for i in range(3)]); mx=mathutils.Vector([max(p[i] for p in pts) for i in range(3)])
c=(mn+mx)/2; r=(mx-mn).length/2
print('BOUNDS',tuple(round(x,3) for x in mn),tuple(round(x,3) for x in mx),'TRIS',sum(len(o.data.polygons) for o in ms))
s=bpy.context.scene; s.render.engine='BLENDER_WORKBENCH'; s.display.shading.light='STUDIO'; s.display.shading.color_type='SINGLE'
s.display.shading.single_color=(0.8,0.75,0.7); s.display.shading.show_cavity=True
s.render.resolution_x=s.render.resolution_y=768
w=bpy.data.worlds.new('w'); s.world=w; w.color=(0.78,0.78,0.78)
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam')); s.collection.objects.link(cam); s.camera=cam
for name,az,el in [('a',0,8),('b',-35,20)]:
    d=mathutils.Vector((math.cos(math.radians(el))*math.sin(math.radians(az)),-math.cos(math.radians(el))*math.cos(math.radians(az)),math.sin(math.radians(el))))
    cam.location=c+d*r*3.2; cam.rotation_euler=(c-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.lens=50
    s.render.filepath=out+'-'+name+'.png'; bpy.ops.render.render(write_still=True)

# Flat captures: Workbench, FLAT light, texture colour, no AO/cavity/shadow/raytrace. Same cameras as stage_mat.py.
import bpy,sys,math,mathutils
out=sys.argv[sys.argv.index('--')+1]
s=bpy.context.scene; ms=[o for o in s.objects if o.type=='MESH']
pts=[o.matrix_world@v.co for o in ms for v in o.data.vertices]
mn=mathutils.Vector([min(q[i] for q in pts) for i in range(3)]); mx=mathutils.Vector([max(q[i] for q in pts) for i in range(3)]); c=(mn+mx)/2
s.render.engine='BLENDER_WORKBENCH'; sh=s.display.shading
sh.light='FLAT'; sh.color_type='TEXTURE'; sh.show_cavity=False; sh.show_shadows=False; sh.show_specular_highlight=False; sh.show_object_outline=False
s.display.shading.background_type='VIEWPORT' if hasattr(sh,'background_type') else None
s.view_settings.view_transform='Standard'
w=s.world or bpy.data.worlds.new('w'); s.world=w; bg=(228/255)**2.2; w.color=(bg,bg,bg)
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam')); s.collection.objects.link(cam); s.camera=cam
shots={'full':(c+mathutils.Vector((0.05,0,0.04)),32,9,5.2,(1840,1168),85),'mouth':(mathutils.Vector((0.5,0,0.1)),55,10,1.25,(1400,1400),50)}
for n,(tgt,az,el,dist,res,lens) in shots.items():
    d=mathutils.Vector((math.sin(math.radians(az))*math.cos(math.radians(el)),-math.cos(math.radians(az))*math.cos(math.radians(el)),math.sin(math.radians(el))))
    cam.location=tgt+d*dist; cam.rotation_euler=(tgt-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.lens=lens
    s.render.resolution_x,s.render.resolution_y=res; s.render.filepath=out+'\\flat-mat-'+n+'.png'; bpy.ops.render.render(write_still=True)
print('FLAT_DONE',sh.light,sh.color_type,sh.show_cavity,sh.show_shadows)

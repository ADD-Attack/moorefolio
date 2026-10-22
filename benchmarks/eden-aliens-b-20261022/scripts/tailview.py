import bpy,sys,math,mathutils
out=sys.argv[sys.argv.index('--')+1]
s=bpy.context.scene; s.render.engine='BLENDER_WORKBENCH'; s.display.shading.light='STUDIO'; s.display.shading.show_cavity=True
s.render.resolution_x=s.render.resolution_y=700
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); s.collection.objects.link(cam); s.camera=cam
t=mathutils.Vector((-0.66,0,-0.2))
for n,az in (('side',0),('back',-60)):
    d=mathutils.Vector((math.sin(math.radians(az)),-math.cos(math.radians(az)),0.25)).normalized()
    cam.location=t+d*0.9; cam.rotation_euler=(t-cam.location).to_track_quat('-Z','Y').to_euler()
    s.render.filepath=out+'-'+n+'.png'; bpy.ops.render.render(write_still=True)

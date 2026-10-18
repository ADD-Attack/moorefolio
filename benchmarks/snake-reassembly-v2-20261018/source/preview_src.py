# Workbench iteration previews of the SRC meshes (NOT judged captures).
import bpy, sys, os, math, mathutils
A=sys.argv[sys.argv.index("--")+1:]; OUT=A[0]; names=A[1].split(",")
sc=bpy.context.scene; sc.render.engine="BLENDER_WORKBENCH"; sc.render.resolution_x=900; sc.render.resolution_y=700
sc.display.shading.light="STUDIO"; sc.display.shading.show_cavity=True; sc.display.shading.color_type="SINGLE"; sc.display.shading.single_color=(0.55,0.55,0.53); sc.display.shading.background_type="VIEWPORT"; sc.display.shading.background_color=(0.3,0.3,0.3); sc.view_settings.view_transform="Standard"
for o in sc.objects: o.hide_render=True
cd=bpy.data.cameras.new("pc"); cam=bpy.data.objects.new("pc",cd); sc.collection.objects.link(cam); sc.camera=cam; cd.lens=60
for n in names:
    o=bpy.data.objects[n]; o.hide_render=False
    bb=[o.matrix_world@mathutils.Vector(c) for c in o.bound_box]; c=sum(bb,mathutils.Vector())/8; r=max((b-c).length for b in bb)
    for tag,d in [("3q",(0.45,-1,0.35)),("side",(0,-1,0.05)),("top",(0.01,-0.2,1))]:
        d=mathutils.Vector(d).normalized(); cam.location=c+d*r*3.6; cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler()
        sc.render.filepath=os.path.join(OUT,"pv_%s_%s.png"%(n,tag)); bpy.ops.render.render(write_still=True)
    o.hide_render=True

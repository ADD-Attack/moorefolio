# Step 0 probe: raw head clay orientation + profile stats + ortho workbench views (iteration previews only).
import bpy, bmesh, sys, os, json
import numpy as np
A=sys.argv[sys.argv.index("--")+1:]; CLAY,OUT=A[0],A[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=CLAY)
o=[o for o in bpy.context.scene.objects if o.type=="MESH"][0]
me=o.data; M=np.array(o.matrix_world)
V=np.array([v.co for v in me.vertices]); V=V@M[:3,:3].T+M[:3,3]
print("BOUNDS",V.min(0),V.max(0))
# histogram along X of z-extent and y-extent for upper part
for x in np.linspace(V[:,0].min(),V[:,0].max(),25):
    s=V[np.abs(V[:,0]-x)<0.03]
    if len(s): print("X %.3f n%6d z[%.3f %.3f] y[%.3f %.3f]"%(x,len(s),s[:,2].min(),s[:,2].max(),s[:,1].min(),s[:,1].max()))
sc=bpy.context.scene; sc.render.engine="BLENDER_WORKBENCH"; sc.render.resolution_x=1200; sc.render.resolution_y=900
sc.display.shading.light="STUDIO"; sc.display.shading.color_type="SINGLE"
cam=bpy.data.cameras.new("c"); cam.type="ORTHO"; cam.ortho_scale=2.2
co=bpy.data.objects.new("c",cam); sc.collection.objects.link(co); sc.camera=co
c=(V.min(0)+V.max(0))/2
import mathutils
for name,d in [("negY",(0,-1,0)),("posZ",(0,0,1)),("negX",(-1,0,0))]:
    d=mathutils.Vector(d); co.location=mathutils.Vector(c)+d*5
    co.rotation_euler=(-d).to_track_quat('-Z','Y' if name=="posZ" else 'Z').to_euler()
    sc.render.filepath=os.path.join(OUT,"probe_"+name+".png"); bpy.ops.render.render(write_still=True)

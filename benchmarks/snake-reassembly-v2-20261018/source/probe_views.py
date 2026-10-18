# Labeled ortho previews of the largest clay island: front(-Y, right=+X up=+Z), top(+Z, right=+X up=+Y), side(+X, right=+Y up=+Z).
import bpy, sys, os, math, numpy as np, mathutils
sys.path.append(os.path.dirname(__file__)); from lib import *
A=sys.argv[sys.argv.index("--")+1:]; CLAY,OUT,TAG,SEED=A[0],A[1],A[2],[float(x) for x in A[3].split(",")]
reset(); o=import_glb(CLAY); keep_island_near(o,SEED)
V=verts(o); print("BB",V.min(0).round(3),V.max(0).round(3))
sc=bpy.context.scene; sc.render.engine="BLENDER_WORKBENCH"; sc.render.resolution_x=800; sc.render.resolution_y=800
sc.display.shading.light="STUDIO"; sc.display.shading.show_cavity=True
cam=bpy.data.cameras.new("c"); cam.type="ORTHO"; cam.ortho_scale=2.1
co=bpy.data.objects.new("c",cam); sc.collection.objects.link(co); sc.camera=co
E=mathutils.Euler
for name,loc,rot in [("front",(0,-5,0),(math.pi/2,0,0)),("top",(0,0,5),(0,0,0)),("side",(5,0,0),(math.pi/2,0,math.pi/2))]:
    co.location=loc; co.rotation_euler=rot
    sc.render.filepath=os.path.join(OUT,TAG+"_"+name+".png"); bpy.ops.render.render(write_still=True)

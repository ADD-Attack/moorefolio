# Probe a clay part: islands, bounds, ortho Workbench previews along -Y, +Z, -X (iteration previews only).
import bpy, sys, os, numpy as np, mathutils, bmesh
sys.path.append(os.path.dirname(__file__)); from lib import *
A=sys.argv[sys.argv.index("--")+1:]; CLAY,OUT,TAG=A
reset(); o=import_glb(CLAY)
bm=bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
lab=[-1]*len(bm.verts); k=0; sizes=[]
for v0 in bm.verts:
    if lab[v0.index]>=0: continue
    st=[v0]; lab[v0.index]=k; n=0; P=[]
    while st:
        v=st.pop(); n+=1; P.append(v.co[:])
        for e in v.link_edges:
            w=e.other_vert(v)
            if lab[w.index]<0: lab[w.index]=k; st.append(w)
    P=np.array(P); sizes.append((n,k,P.min(0).round(3).tolist(),P.max(0).round(3).tolist())); k+=1
for s in sorted(sizes,reverse=True)[:7]: print("ISLAND",s)
V=verts(o)
for ax in range(3):
    print("AXIS",ax,np.percentile(V[:,ax],[0,1,50,99,100]).round(3))
sc=bpy.context.scene; sc.render.engine="BLENDER_WORKBENCH"; sc.render.resolution_x=1000; sc.render.resolution_y=1000
sc.display.shading.light="STUDIO"; sc.display.shading.show_cavity=True
cam=bpy.data.cameras.new("c"); cam.type="ORTHO"; cam.ortho_scale=2.1
co=bpy.data.objects.new("c",cam); sc.collection.objects.link(co); sc.camera=co
for name,d,up in [("negY",(0,-1,0),'Y'),("posZ",(0,0,1),'Y'),("negX",(-1,0,0),'Y'),("posX",(1,0,0),'Y')]:
    d=mathutils.Vector(d); co.location=d*5; co.rotation_euler=(-d).to_track_quat('-Z',up).to_euler()
    sc.render.filepath=os.path.join(OUT,TAG+"_"+name+".png"); bpy.ops.render.render(write_still=True)

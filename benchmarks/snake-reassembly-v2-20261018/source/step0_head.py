# Step 0: cut the raw head clay at the collar plane, keep the skull island, measure profiles. No edits to form.
import bpy, sys, os, json, numpy as np
sys.path.append(os.path.dirname(__file__)); from lib import *
A=sys.argv[sys.argv.index("--")+1:]; CLAY,WORK=A[0],A[1]
CUT_X=float(A[2]) if len(A)>2 else 0.19
reset(); o=import_glb(CLAY); o.name="head_clay_cut"
raw=len(o.data.vertices)
bisect_keep(o,(CUT_X,0,0),(1,0,0),True)
V=verts(o); tip=V[np.argmin(V[:,0])]
n=keep_island_near(o,tip)
V=verts(o)
rep={"cut_x":CUT_X,"raw_verts":raw,"kept_verts":len(V),"tris":tris(o),"bounds":[V.min(0).tolist(),V.max(0).tolist()]}
prof=[]
for x in np.arange(V[:,0].min(),V[:,0].max(),0.025):
    s=V[np.abs(V[:,0]-x)<0.0125]
    if len(s)<10: continue
    side=s[np.abs(s[:,1])>0.12]
    prof.append([round(float(x),3),round(float(s[:,2].min()),3),(round(float(side[:,2].max()),3) if len(side) else None),round(float(s[:,2].max()),3),round(float(s[:,1].min()),3),round(float(s[:,1].max()),3)])
rep["profile_x_zmin_zmaxSide_zmaxAll_ymin_ymax"]=prof
json.dump(rep,open(os.path.join(WORK,"step0_head.json"),"w"),indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK,"head_cut.blend"))
print("DONE",rep["kept_verts"],rep["tris"])

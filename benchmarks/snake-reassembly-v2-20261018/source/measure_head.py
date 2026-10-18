# Measure skull L:H on the delivered head mesh (back in clay frame): L = snout tip -> vent-box rear (x=-0.21), H = fin-root crown 0.78 -> jaw underside.
import bpy, sys, os, json, numpy as np, mathutils
sys.path.append(os.path.dirname(__file__)); from lib import *
A=sys.argv[sys.argv.index("--")+1:]; L=json.load(open(A[0])); S=L["scales"]["head"]["uniform_scale"]
Mh=mathutils.Matrix.Scale(S,4)@mathutils.Matrix(((-1,0,0,0.19),(0,-1,0,0),(0,0,1,-0.435),(0,0,0,1)))
o=bpy.data.objects["SRC_Head"]; me=o.data.copy(); me.transform(Mh.inverted())
V=np.array([v.co[:] for v in me.vertices])
skull=V[V[:,0]<-0.30]; tip=float(skull[:,0].min()); jaw=float(np.percentile(skull[:,2],0.2))
Lm=-0.21-tip; Hm=0.78-jaw
r={"tip_x":tip,"jaw_z":jaw,"L":Lm,"H":Hm,"LH":Lm/Hm,"band":[1.4065,1.4935]}; print("MEASURE",r); json.dump(r,open(A[1],"w"),indent=1)

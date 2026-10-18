# Section-profile survival test (PRESERVATION-PLAN H.4): raw cut clay (grey) vs head build (red), same frame.
# blender -b snake-v2-r2.blend -P sections.py -- <clay head glb> <build-log.json> <out_prefix>
import bpy, bmesh, sys, os, json, numpy as np, mathutils
sys.path.append(os.path.dirname(__file__)); from lib import *
A=sys.argv[sys.argv.index("--")+1:]; GLB,LOGP,OUT=A
L=json.load(open(LOGP)); S=L["scales"]["head"]["uniform_scale"]
Mh=mathutils.Matrix.Scale(S,4)@mathutils.Matrix(((-1,0,0,0.19),(0,-1,0,0),(0,0,1,-0.435),(0,0,0,1)))
build=bpy.data.objects["SRC_Head"]
before=set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=GLB)
raw=[o for o in bpy.data.objects if o not in before and o.type=="MESH"][0]
raw.data.transform(raw.matrix_world); raw.matrix_world=mathutils.Matrix(); raw.data.transform(Mh)
def cut(o,co,no):
    bm=bmesh.new(); bm.from_mesh(o.data)
    r=bmesh.ops.bisect_plane(bm,geom=bm.verts[:]+bm.edges[:]+bm.faces[:],plane_co=co,plane_no=no)
    E=[e for e in r["geom_cut"] if isinstance(e,bmesh.types.BMEdge)]
    segs=[(e.verts[0].co.copy(),e.verts[1].co.copy()) for e in E]; bm.free(); return segs
ex=1.895  # eye-centre station (clay x=-0.67) in build frame
planes={"a_eye_station_x":((ex,0,0),(1,0,0),(1,2)),"b_midsnout_x":((2.29,0,0),(1,0,0),(1,2)),
        "c_profile_y_nearside":((0,0.36,0),(0,1,0),(0,2)),"d_plan_z_nostril":((0,0,-0.12),(0,0,1),(0,1))}
rep={}
for name,(co,no,ax) in planes.items():
    W,H=900,700; img=np.ones((H,W,4),np.float32); img[...,:3]=0.96
    sr=cut(raw,co,no); sb=cut(build,co,no)
    P=np.array([[p[ax[0]],p[ax[1]]] for s in sr for p in s]+[[p[ax[0]],p[ax[1]]] for s in sb for p in s])
    if len(P)==0: continue
    mn,mx=P.min(0),P.max(0); sc=0.85*min(W/(mx[0]-mn[0]+1e-6),H/(mx[1]-mn[1]+1e-6)); c=(mn+mx)/2
    f=lambda p:((p[ax[0]]-c[0])*sc+W/2, H/2-(p[ax[1]]-c[1])*sc)
    for a,b in sr: draw_poly(img,[f(a),f(b)],[0.55,0.55,0.55],1)
    for a,b in sb: draw_poly(img,[f(a),f(b)],[0.85,0.1,0.1],0)
    save_img(img,OUT+"_"+name+".png"); rep[name]={"raw_segments":len(sr),"build_segments":len(sb)}
json.dump(rep,open(OUT+"_sections.json","w"),indent=1); print("SECTIONS",rep)

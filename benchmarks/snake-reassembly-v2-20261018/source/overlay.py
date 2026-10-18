# Same-angle comparison (Construction Rule 4): solve a camera from landmarks, render the mesh in Workbench clay,
# warp into the reference frame by a 2D similarity fit, and write overlay + side-by-side.
# Args: blend obj_name ref.png out_prefix landmarks.json   (landmarks: [[x,y,z],[u,v]] pairs)
import bpy, sys, os, json, numpy as np, mathutils, math
sys.path.append(os.path.dirname(__file__)); from lib import *
A=sys.argv[sys.argv.index("--")+1:]; OBJ,REF,OUT,LM=A[0],A[1],A[2],json.loads(open(A[3]).read())
o=bpy.data.objects[OBJ]
for x in bpy.data.objects:
    if x.type=="MESH" and x.name!=OBJ and not x.name.startswith(OBJ.split("_")[0]): x.hide_render=True
sc=bpy.context.scene; ref=load_img(REF); H,W=ref.shape[:2]
sc.render.resolution_x=W*2; sc.render.resolution_y=H*2; sc.render.film_transparent=True
sc.render.engine="BLENDER_WORKBENCH"; sc.display.shading.light="STUDIO"; sc.display.shading.color_type="SINGLE"
sc.display.shading.single_color=(0.6,0.6,0.58); sc.display.shading.show_cavity=True
cd=bpy.data.cameras.new("cam"); cd.lens=85; cam=bpy.data.objects.new("cam",cd); sc.collection.objects.link(cam); sc.camera=cam
P3=np.array([l[0] for l in LM]); P2=np.array([l[1] for l in LM],float)
ctr=P3.mean(0); rad=6.0
def place(yaw,el):
    d=mathutils.Vector((math.sin(math.radians(yaw))*-1*math.cos(math.radians(el)),-math.cos(math.radians(yaw))*math.cos(math.radians(el)),math.sin(math.radians(el))))
    cam.location=mathutils.Vector(ctr)+d*rad; cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler(); bpy.context.view_layer.update()
def fit(src,dst):
    # similarity: dst = s R src + t
    ms,md=src.mean(0),dst.mean(0); a,b=src-ms,dst-md
    U,S,Vt=np.linalg.svd(b.T@a); R=U@Vt
    if np.linalg.det(R)<0: U[:,-1]*=-1; R=U@Vt
    s=S.sum()/ (a**2).sum(); t=md-s*(R@ms)
    res=np.sqrt((((s*(R@src.T)).T+t-dst)**2).sum(1)).mean(); return s,R,t,res
best=None
for yaw in range(-30,46,3):
    for el in range(-6,34,3):
        place(yaw,el); p=project(cam,P3)/2.0
        s,R,t,res=fit(p,P2)
        if best is None or res<best[0]: best=(res,yaw,el,s,R,t)
res,yaw,el,s,R,t=best; place(yaw,el)
print("SOLVE yaw %d el %d resid %.1fpx scale %.3f"%(yaw,el,res,s))
sc.render.filepath=OUT+"_render.png"; bpy.ops.render.render(write_still=True)
rd=load_img(OUT+"_render.png"); rh,rw=rd.shape[:2]
# inverse warp render (in half-res units) into ref frame
yy,xx=np.mgrid[0:H,0:W].astype(np.float32); q=np.stack([xx.ravel(),yy.ravel()],1)
src=((np.linalg.inv(R)@((q-t).T)).T/s)*2.0
sx=np.clip(src[:,0].round().astype(int),0,rw-1); sy=np.clip(src[:,1].round().astype(int),0,rh-1)
ok=(src[:,0]>=0)&(src[:,0]<rw)&(src[:,1]>=0)&(src[:,1]<rh)
warp=rd[sy,sx].reshape(H,W,4); warp[~ok.reshape(H,W)]=0
alpha=warp[...,3]>0.5
sil=np.zeros_like(alpha); sil[1:-1,1:-1]=alpha[1:-1,1:-1]&~(alpha[:-2,1:-1]&alpha[2:,1:-1]&alpha[1:-1,:-2]&alpha[1:-1,2:])
ov=ref.copy(); ov[...,:3]=ov[...,:3]*0.55+0.2
m=alpha; ov[m,:3]=ov[m,:3]*0.5+warp[m,:3]*0.5
e=edges(ref,0.18); ov[e,:3]=[0.05,0.25,0.9]
k=sil.copy()
for dy in(-1,0,1):
    for dx in(-1,0,1): k|=np.roll(np.roll(sil,dy,0),dx,1)
ov[k,:3]=[0.95,0.1,0.1]
for (u,v) in P2: ov[int(v)-3:int(v)+4,int(u)-3:int(u)+4,:3]=[1,1,0]
save_img(ov,OUT+"_overlay.png")
sbs=np.concatenate([ref, np.where(alpha[...,None], warp, np.concatenate([np.full((H,W,3),0.757),np.ones((H,W,1))],2))],1)
save_img(sbs.astype(np.float32),OUT+"_sbs.png")
json.dump({"yaw":yaw,"el":el,"resid_px":float(res),"scale":float(s)},open(OUT+"_solve.json","w"))

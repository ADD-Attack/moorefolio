# Shared helpers (Blender 4.5). Image I/O via bpy (no PIL on host). 8-bit PNG pixels are sRGB/255 already.
import bpy, bmesh, numpy as np, mathutils, os, math
from bpy_extras.object_utils import world_to_camera_view

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def import_glb(p):
    before=set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=p)
    obs=[o for o in bpy.data.objects if o not in before and o.type=="MESH"]
    o=obs[0]
    # bake transform
    o.data.transform(o.matrix_world); o.parent=None; o.matrix_world=mathutils.Matrix()
    for x in [x for x in bpy.data.objects if x.type!="MESH"]: bpy.data.objects.remove(x)
    o.data.materials.clear()
    return o

def verts(o):
    a=np.empty(len(o.data.vertices)*3); o.data.vertices.foreach_get("co",a); return a.reshape(-1,3)

def bisect_keep(o, co, no, keep_neg=True):
    """Plane cut: keep the side where dot(v-co,no)<0 (keep_neg) and fill the cap."""
    bm=bmesh.new(); bm.from_mesh(o.data)
    g=bm.verts[:]+bm.edges[:]+bm.faces[:]
    r=bmesh.ops.bisect_plane(bm,geom=g,plane_co=co,plane_no=no,clear_outer=keep_neg,clear_inner=not keep_neg)
    bm.to_mesh(o.data); bm.free()

def keep_island_near(o, point):
    bm=bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
    P=np.array([v.co for v in bm.verts]); seed=int(np.argmin(((P-np.array(point))**2).sum(1)))
    seen={seed}; st=[bm.verts[seed]]
    while st:
        v=st.pop()
        for e in v.link_edges:
            w=e.other_vert(v)
            if w.index not in seen: seen.add(w.index); st.append(w)
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.index not in seen],context="VERTS")
    bm.to_mesh(o.data); bm.free(); return len(seen)

def tris(o):
    o.data.calc_loop_triangles(); return len(o.data.loop_triangles)

def load_img(p):
    im=bpy.data.images.load(p); w,h=im.size
    a=np.array(im.pixels[:],np.float32).reshape(h,w,im.channels)[::-1]
    if a.shape[2]==3: a=np.concatenate([a,np.ones((h,w,1),np.float32)],2)
    return a

def save_img(a,p):
    h,w=a.shape[:2]
    if a.shape[2]==3: a=np.concatenate([a,np.ones((h,w,1),np.float32)],2)
    im=bpy.data.images.new(os.path.basename(p),w,h,alpha=True); im.pixels=a[::-1].ravel()
    im.filepath_raw=p; im.file_format="PNG"; im.save()

def edges(a, thr=0.12):
    l=a[...,:3].mean(2); gx=np.zeros_like(l); gy=np.zeros_like(l)
    gx[:,1:-1]=l[:,2:]-l[:,:-2]; gy[1:-1]=l[2:]-l[:-2]
    return np.hypot(gx,gy)>thr

def clay_mat(name="clay", col=(0.22,0.22,0.21,1)):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes=True
    b=m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value=col
    b.inputs["Roughness"].default_value=0.55; b.inputs["Metallic"].default_value=0.0
    return m

def project(cam, P):
    sc=bpy.context.scene; W,H=sc.render.resolution_x,sc.render.resolution_y
    out=[]
    for p in P:
        v=world_to_camera_view(sc,cam,mathutils.Vector(p)); out.append((v.x*W,(1-v.y)*H))
    return np.array(out)

def draw_poly(a, pts, col, w=1):
    h,W=a.shape[:2]
    for (x0,y0),(x1,y1) in zip(pts[:-1],pts[1:]):
        n=int(max(abs(x1-x0),abs(y1-y0)))+1
        for t in np.linspace(0,1,n):
            x=int(round(x0+(x1-x0)*t)); y=int(round(y0+(y1-y0)*t))
            a[max(0,y-w):y+w+1, max(0,x-w):x+w+1, :3]=col

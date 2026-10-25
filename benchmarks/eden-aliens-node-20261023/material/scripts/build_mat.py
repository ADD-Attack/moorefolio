# MATERIALS: one shared UV atlas (smart project), per-vertex material fields from geometry masks,
# rasterized to 2K maps (basecolor sRGB, ORM linear, emissive sRGB), Principled material, GLB (tangents ON).
import bpy,sys,math,numpy as np
from collections import deque
a=sys.argv[sys.argv.index('--')+1:]; OUT=a[0]; RES=int(a[1]); EMS=float(a[2])
pod_v=np.load(OUT+'\\pod.npy')
def s2l(c): c=np.asarray(c,float)/255; return np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4)
C_BODY=s2l((186,84,32)); C_TOP=s2l((224,118,48)); C_TROUGH=s2l((92,26,12)); C_UNDER=s2l((124,40,18))
C_HORN=s2l((44,27,21)); C_HORN_HI=s2l((78,50,38)); C_POD=s2l((250,150,26)); C_POD_EDGE=s2l((196,78,10)); C_EM=s2l((255,118,12))
def lap(V,E,deg,it):
    S=V.copy()
    for _ in range(it):
        acc=np.zeros_like(S); np.add.at(acc,E[:,0],S[E[:,1]]); np.add.at(acc,E[:,1],S[E[:,0]]); S=0.5*S+0.5*acc/np.maximum(deg,1)[:,None]
    return S
HAX=[(-0.203,0.20),(0.187,0.196)]
fields={}
for o in [x for x in bpy.data.objects if x.type=='MESH']:
    me=o.data; nv=len(me.vertices); mw=o.matrix_world
    E=np.empty(len(me.edges)*2,np.int32); me.edges.foreach_get('vertices',E); E=E.reshape(-1,2); deg=np.bincount(E.ravel(),minlength=nv).astype(float)
    P=np.empty(nv*3); me.vertices.foreach_get('co',P); P=P.reshape(-1,3); N=np.empty(nv*3); me.vertices.foreach_get('normal',N); N=N.reshape(-1,3)
    W=np.array([mw@__import__('mathutils').Vector(p) for p in P]); R3=np.array(mw.to_3x3()); Nw=N@R3.T
    el=np.linalg.norm(P[E[:,0]]-P[E[:,1]],axis=1).mean()
    hF=np.einsum('ij,ij->i',P-lap(P,E,deg,6),N)
    cav=np.clip(-hF/(0.8*el),0,1); cav=lap(cav[:,None],E,deg,8)[:,0]; cav=np.clip(cav*2.6,0,1)**0.8     # smoothed concavity (no AO speckle)
    hL=np.einsum('ij,ij->i',P-lap(P,E,deg,30),N); cvx=np.clip(hL/0.02,0,1)
    up=np.clip(Nw[:,2],-1,1); top=np.clip(0.55*cvx+0.45*np.clip(up,0,1),0,1); under=np.clip(-up*0.8+np.clip((0.25-W[:,2])/0.25,0,1)*0.5,0,1)
    horn=np.zeros(nv); pod=np.zeros(nv); podc=np.zeros(nv)
    if o.name.startswith('foot'): cav=np.clip(cav*1.4,0,1); under=np.clip(under+0.35*np.clip(-up,0,1)+0.25,0,1)
    if o.name=='body':
        for hx,hy in HAX:
            d=np.hypot(W[:,0]-hx,W[:,1]-hy); horn=np.maximum(horn,np.clip((W[:,2]-0.875)/0.04,0,1)*np.clip((0.14-d)/0.03,0,1))
        pod=pod_v.astype(float)
        # distance-into-pod (BFS from pod border) for a bright centre / darker edge
        adj=[[] for _ in range(nv)]
        for i,j in E: adj[i].append(j); adj[j].append(i)
        dist=np.full(nv,1e9); q=deque()
        for i in np.where(pod_v)[0]:
            if any(not pod_v[j] for j in adj[i]): dist[i]=0; q.append(i)
        while q:
            u=q.popleft()
            for w in adj[u]:
                if pod_v[w] and dist[w]>dist[u]+1: dist[w]=dist[u]+1; q.append(w)
        for _ in range(2):   # erode 2 rings so rims never glow
            b=[i for i in np.where(pod_v)[0] if any(not pod_v[j] for j in adj[i])]; pod_v=pod_v.copy(); pod_v[b]=False
        podc=np.where(pod_v,np.clip(dist/7,0,1),0); podc=lap(podc[:,None],E,deg,6)[:,0]*pod_v
        pod=lap(pod_v.astype(float)[:,None],E,deg,2)[:,0]; horn=horn*(1-pod)
    base=C_BODY[None]*(1-top[:,None])+C_TOP[None]*top[:,None]
    base=base*(1-under[:,None]*0.6)+C_UNDER[None]*under[:,None]*0.6
    base=base*(1-cav[:,None])+C_TROUGH[None]*cav[:,None]
    hcol=C_HORN[None]*(1-cvx[:,None]*0.6)+C_HORN_HI[None]*cvx[:,None]*0.6
    base=base*(1-horn[:,None])+hcol*horn[:,None]
    pcol=C_POD_EDGE[None]*(1-podc[:,None])+C_POD[None]*podc[:,None]
    base=base*(1-pod[:,None])+pcol*pod[:,None]
    rough=(0.55-0.12*top+0.15*cav)*(1-horn)+0.42*horn; rough=rough*(1-pod)+0.10*pod
    ao=1-0.45*cav; ao=ao*(1-pod)+1.0*pod
    em=C_EM[None]*(pod*(0.15+0.85*podc**1.3))[:,None]
    fields[o.name]=dict(base=base,orm=np.stack([ao,rough,np.zeros(nv)],1),em=em)
    print('FIELDS',o.name,nv,'pod',int(pod_v.sum()) if o.name=='body' else 0,'horn>0.5',int((horn>0.5).sum()))
# ---- UVs: one shared atlas
bpy.ops.object.select_all(action='DESELECT')
ms=[x for x in bpy.data.objects if x.type=='MESH']
for x in ms: x.select_set(True)
bpy.context.view_layer.objects.active=ms[0]
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(60),island_margin=0.004,area_weight=0.0,scale_to_bounds=False)
bpy.ops.uv.pack_islands(margin=0.004)
bpy.ops.object.mode_set(mode='OBJECT')
# ---- raster per-vertex fields into UV space
img={k:np.zeros((RES,RES,3)) for k in ('base','orm','em')}; cov=np.zeros((RES,RES),bool)
for o in ms:
    me=o.data; uvl=me.uv_layers.active.data; F=fields[o.name]
    loops=np.empty(len(me.loops),np.int32); me.loops.foreach_get('vertex_index',loops)
    UV=np.empty(len(me.loops)*2); uvl.foreach_get('uv',UV); UV=UV.reshape(-1,2)*RES
    ls=np.empty(len(me.polygons)*1,np.int32); me.polygons.foreach_get('loop_start',ls)
    for st in ls:
        l=[st,st+1,st+2]; t=UV[l]; vi=loops[l]
        x0,y0=np.floor(t.min(0)).astype(int); x1,y1=np.ceil(t.max(0)).astype(int)
        x0=max(x0,0); y0=max(y0,0); x1=min(x1,RES-1); y1=min(y1,RES-1)
        if x1<x0 or y1<y0: continue
        xs,ys=np.meshgrid(np.arange(x0,x1+1)+0.5,np.arange(y0,y1+1)+0.5)
        d=(t[1,1]-t[2,1])*(t[0,0]-t[2,0])+(t[2,0]-t[1,0])*(t[0,1]-t[2,1])
        if abs(d)<1e-12: continue
        w0=((t[1,1]-t[2,1])*(xs-t[2,0])+(t[2,0]-t[1,0])*(ys-t[2,1]))/d; w1=((t[2,1]-t[0,1])*(xs-t[2,0])+(t[0,0]-t[2,0])*(ys-t[2,1]))/d; w2=1-w0-w1
        m=(w0>=-0.02)&(w1>=-0.02)&(w2>=-0.02)
        if not m.any(): continue
        yy=(ys[m]-0.5).astype(int); xx=(xs[m]-0.5).astype(int)
        for k in img: img[k][yy,xx]=w0[m,None]*F[k][vi[0]]+w1[m,None]*F[k][vi[1]]+w2[m,None]*F[k][vi[2]]
        cov[yy,xx]=True
print('COVERAGE',round(cov.mean(),3))
for _ in range(12):   # edge padding
    for k in img:
        im=img[k]; acc=np.zeros_like(im); n=np.zeros(cov.shape)
        for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
            sh=np.roll(np.roll(im,dy,0),dx,1); sc=np.roll(np.roll(cov,dy,0),dx,1); acc+=sh*sc[...,None]; n+=sc
        fill=(~cov)&(n>0); im[fill]=acc[fill]/n[fill,None]
    cov=cov|fill
def l2s(x): x=np.clip(x,0,1); return np.where(x<=0.0031308,x*12.92,1.055*x**(1/2.4)-0.055)
def save(name,arr,srgb):
    im=bpy.data.images.new(name,RES,RES,alpha=False,float_buffer=False)
    px=np.concatenate([l2s(arr) if srgb else np.clip(arr,0,1),np.ones((RES,RES,1))],2)
    im.pixels.foreach_set(px.ravel().astype(np.float32)); im.filepath_raw=OUT+'\\'+name+'.png'; im.file_format='PNG'; im.save()
    im.colorspace_settings.name='sRGB' if srgb else 'Non-Color'; return im
I_B=save('aliens_node_basecolor',img['base'],True); I_O=save('aliens_node_orm',img['orm'],False); I_E=save('aliens_node_emissive',img['em'],True)
# ---- Principled material + glTF occlusion output
mat=bpy.data.materials.new('aliens_node'); mat.use_nodes=True; nt=mat.node_tree; Nn=nt.nodes; L=nt.links
bs=Nn['Principled BSDF']
def tex(im,x,y): t=Nn.new('ShaderNodeTexImage'); t.image=im; t.location=(x,y); return t
tb=tex(I_B,-700,300); to=tex(I_O,-700,0); te=tex(I_E,-700,-300)
sp=Nn.new('ShaderNodeSeparateColor'); sp.location=(-400,0)
L.new(tb.outputs['Color'],bs.inputs['Base Color']); L.new(to.outputs['Color'],sp.inputs['Color'])
L.new(sp.outputs['Green'],bs.inputs['Roughness']); L.new(sp.outputs['Blue'],bs.inputs['Metallic'])
L.new(te.outputs['Color'],bs.inputs['Emission Color']); bs.inputs['Emission Strength'].default_value=EMS
g=bpy.data.node_groups.get('glTF Material Output') or bpy.data.node_groups.new('glTF Material Output','ShaderNodeTree')
if 'Occlusion' not in [i.name for i in g.interface.items_tree]: g.interface.new_socket('Occlusion',in_out='INPUT',socket_type='NodeSocketFloat')
gn=Nn.new('ShaderNodeGroup'); gn.node_tree=g; gn.location=(-100,-400); L.new(sp.outputs['Red'],gn.inputs['Occlusion'])
for o in ms: o.data.materials.clear(); o.data.materials.append(mat)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=OUT+'\\aliens-node.glb',export_format='GLB',export_yup=True,export_apply=True,export_tangents=True,export_draco_mesh_compression_enable=False,export_image_format='AUTO')
bpy.ops.wm.save_as_mainfile(filepath=OUT+'\\aliens-node-mat.blend')
print('DONE')

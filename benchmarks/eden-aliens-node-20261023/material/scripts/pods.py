# Pod mask: seed by raycast at pod centres picked from the diag views, flood over non-concave verts (stops at the dome/rim groove).
import bpy,sys,math,mathutils,numpy as np
from collections import deque
a=sys.argv[sys.argv.index('--')+1:]; TH=float(a[0]); RMAX=float(a[1])
SEEDS={'f':[(343,245),(228,290),(460,290),(195,395),(268,400),(390,465),(490,400)],'b':[(350,355),(360,455)]}
s=bpy.context.scene; o=bpy.data.objects['body']; me=o.data; nv=len(me.vertices)
hF=np.load(a[2])[:,1]
E=np.empty(len(me.edges)*2,np.int32); me.edges.foreach_get('vertices',E); E=E.reshape(-1,2)
adj=[[] for _ in range(nv)]
for i,j in E: adj[i].append(j); adj[j].append(i)
P=np.empty(nv*3); me.vertices.foreach_get('co',P); P=P.reshape(-1,3)
for f in [x for x in s.objects if x.name.startswith('foot')]: f.hide_set(True); f.hide_render=True
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); s.collection.objects.link(cam); s.render.resolution_x=s.render.resolution_y=700; cam.data.lens=60
dg=bpy.context.evaluated_depsgraph_get()
pod=np.zeros(nv,bool); seedsv=[]
for nm,az in [('f',0),('b',180)]:
    d=mathutils.Vector((math.sin(math.radians(az))*0.95,-math.cos(math.radians(az))*0.95,0.3)); t=mathutils.Vector((0,-0.06,0.55))
    cam.location=t+d*4; cam.rotation_euler=(t-cam.location).to_track_quat('-Z','Y').to_euler(); s.camera=cam; bpy.context.view_layer.update()
    fr=cam.data.view_frame(scene=s); tr,bl=fr[0],fr[2]
    for px,py in SEEDS[nm]:
        x=px/700; y=1-py/700
        loc=mathutils.Vector((bl.x+(tr.x-bl.x)*x, bl.y+(tr.y-bl.y)*y, tr.z))
        dirw=(cam.matrix_world.to_3x3()@loc).normalized()
        hit,p,n,fi,ob,_=s.ray_cast(dg,cam.location,dirw)
        if not hit or ob.name!='body': print('MISS',nm,px,py,ob.name if ob else None); continue
        fv=list(me.polygons[fi].vertices); sv=fv[0]; seedsv.append(sv)
        q=deque([sv]); seen={sv}; c0=P[sv]
        while q:
            u=q.popleft(); pod[u]=True
            for w in adj[u]:
                if w not in seen and hF[w]>TH and np.linalg.norm(P[w]-c0)<RMAX: seen.add(w); q.append(w)
        print('SEED',nm,px,py,'verts',len(seen))
np.save(a[3],pod)
col=me.color_attributes.new('pod','FLOAT_COLOR','POINT'); c=np.zeros((nv,4)); c[:,3]=1; c[:,2]=0.6; c[pod]=[1,0.2,0.0,1]; col.data.foreach_set('color',c.ravel())
me.color_attributes.active_color=col
s.render.engine='BLENDER_WORKBENCH'; s.display.shading.color_type='VERTEX'; s.display.shading.light='STUDIO'
for nm,az in [('f',0),('b',180),('l',-90),('r',90)]:
    d=mathutils.Vector((math.sin(math.radians(az))*0.95,-math.cos(math.radians(az))*0.95,0.3)); t=mathutils.Vector((0,-0.06,0.55))
    cam.location=t+d*4; cam.rotation_euler=(t-cam.location).to_track_quat('-Z','Y').to_euler()
    s.render.filepath=a[4]+'-'+nm+'.png'; bpy.ops.render.render(write_still=True)

# Diagnostic: per-vertex large-scale height (pods/lobes protrusion) and fine concavity, shown as vertex colors.
import bpy,sys,numpy as np
a=sys.argv[sys.argv.index('--')+1:]
def lap(P,E,deg,it):
    S=P.copy()
    for _ in range(it):
        acc=np.zeros_like(S); np.add.at(acc,E[:,0],S[E[:,1]]); np.add.at(acc,E[:,1],S[E[:,0]]); S=0.5*S+0.5*acc/np.maximum(deg,1)[:,None]
    return S
o=bpy.data.objects['body']; me=o.data; nv=len(me.vertices)
E=np.empty(len(me.edges)*2,np.int32); me.edges.foreach_get('vertices',E); E=E.reshape(-1,2); deg=np.bincount(E.ravel(),minlength=nv).astype(float)
P=np.empty(nv*3); me.vertices.foreach_get('co',P); P=P.reshape(-1,3); N=np.empty(nv*3); me.vertices.foreach_get('normal',N); N=N.reshape(-1,3)
hL=np.einsum('ij,ij->i',P-lap(P,E,deg,int(a[0])),N); hF=np.einsum('ij,ij->i',P-lap(P,E,deg,6),N)
print('hL pct',np.percentile(hL,[5,50,90,97]).round(4),'hF pct',np.percentile(hF,[3,10,50,90]).round(4))
x=np.clip((hL-np.percentile(hL,50))/(np.percentile(hL,98)-np.percentile(hL,50)),0,1)
c=np.clip(-hF/abs(np.percentile(hF,3)),0,1)
col=me.color_attributes.new('diag','FLOAT_COLOR','POINT')
cols=np.stack([x,0.3+0*x,c,np.ones(nv)],1); col.data.foreach_set('color',cols.ravel())
np.save(a[1],np.stack([hL,hF],1))
s=bpy.context.scene; s.render.engine='BLENDER_WORKBENCH'; s.display.shading.color_type='VERTEX'; s.display.shading.light='FLAT'
for f in [x for x in s.objects if x.name.startswith('foot')]: f.hide_render=True
import math,mathutils
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); s.collection.objects.link(cam); s.camera=cam; s.render.resolution_x=s.render.resolution_y=700
for nm,az in [('f',0),('b',180),('l',-90),('r',90)]:
    d=mathutils.Vector((math.sin(math.radians(az))*0.95,-math.cos(math.radians(az))*0.95,0.3)); t=mathutils.Vector((0,-0.06,0.55))
    cam.location=t+d*4; cam.rotation_euler=(t-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.lens=60
    s.render.filepath=a[2]+'-'+nm+'.png'; bpy.ops.render.render(write_still=True)

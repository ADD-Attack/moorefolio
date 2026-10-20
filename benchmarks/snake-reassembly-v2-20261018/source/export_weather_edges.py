"""Read-only extraction of frozen geometry and UVs for fitted weathering masks."""
import bpy,sys,os,numpy as np
from pathlib import Path
T=Path(sys.argv[sys.argv.index('--')+1]);O=T/'material/mask-input';O.mkdir(exist_ok=True)
for ob in bpy.data.objects:
 if ob.type!='MESH' or not ob.name.startswith('SRC_') or 'Glow' in ob.name:continue
 me=ob.data;me.calc_loop_triangles();V=np.array([v.co[:] for v in me.vertices]);UV=np.array([u.uv[:] for u in me.uv_layers.active.data]);F=np.array([t.vertices[:] for t in me.loop_triangles]);U=np.array([UV[list(t.loops)] for t in me.loop_triangles]);adj={}
 for p in me.polygons:
  for a,b in p.edge_keys:adj.setdefault(tuple(sorted((a,b))),[]).append(p.index)
 convex=[];cavity=[]
 for (a,b),faces in adj.items():
  if len(faces)==1:convex.append([V[a],V[b]]);continue
  if len(faces)!=2:continue
  p,q=[me.polygons[i] for i in faces];n1=np.array(p.normal);n2=np.array(q.normal)
  if n1@n2>np.cos(np.deg2rad(28)):continue
  sign=(n1-n2)@(np.array(p.center)-np.array(q.center))
  (convex if sign>=0 else cavity).append([V[a],V[b]])
 np.savez_compressed(O/(ob.name+'.npz'),V=V,F=F,U=U,convex=np.array(convex),cavity=np.array(cavity))
 print('WEATHER_EDGE_SOURCE',ob.name,len(convex),len(cavity),flush=True)

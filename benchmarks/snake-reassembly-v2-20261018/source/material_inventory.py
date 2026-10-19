import bpy,json,hashlib,numpy as np
from pathlib import Path
out={}
for o in bpy.data.objects:
 if o.type!='MESH' or not o.name.startswith('SRC_'):continue
 me=o.data;me.calc_loop_triangles();v=np.array([v.co[:] for v in me.vertices],dtype=np.float32);f=[tuple(p.vertices) for p in me.polygons]
 parent=list(range(len(v)))
 def root(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for p in me.polygons:
  a=root(p.vertices[0])
  for j in p.vertices[1:]:parent[root(j)]=a
 groups={}
 for i in range(len(v)):groups.setdefault(root(i),[]).append(i)
 comps=[]
 for ids in groups.values():
  if len(ids)<16:continue
  q=v[ids];comps.append({'vertices':len(ids),'center':q.mean(0).tolist(),'min':q.min(0).tolist(),'max':q.max(0).tolist()})
 out[o.name]={'verts':len(v),'polygons':len(f),'tris':len(me.loop_triangles),'uv_layers':list(me.uv_layers.keys()),'mesh_hash':hashlib.sha256(v.tobytes()+repr(f).encode()).hexdigest(),'components':sorted(comps,key=lambda x:-x['vertices'])[:25]}
Path('material/inventory.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=1))

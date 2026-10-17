import json,struct,os,math
from pathlib import Path
D=Path(os.environ.get('ASSEMBLY_OUTPUT',str(Path(__file__).parent/'delivery')))
def read(p):
 b=p.read_bytes();magic,version,length=struct.unpack_from('<III',b);assert magic==0x46546c67 and version==2 and length==len(b);n,t=struct.unpack_from('<II',b,12);return json.loads(b[20:20+n])
def validate(p):
 g=read(p);access=g['accessors'];meshes=g['meshes'];nodes=g['nodes'];errors=[]
 def tris(i):return sum(access[q['indices']]['count']//3 for q in meshes[i]['primitives'])
 counts={n.get('name',str(i)):tris(n['mesh']) for i,n in enumerate(nodes) if 'mesh'in n}
 for m in meshes:
  for q in m['primitives']:
   if not {'POSITION','NORMAL','TEXCOORD_0','TANGENT'}.issubset(q['attributes']):errors.append('Attributes missing '+m.get('name',''))
   if 'KHR_draco_mesh_compression' in q.get('extensions',{}):errors.append('Draco forbidden')
 for n in nodes:
  if 'skin'in n:errors.append('Skin forbidden')
  if any(abs(s-1)>1e-5 for s in n.get('scale',[1,1,1])):errors.append('Nonunit scale '+n.get('name',''))
 for m in g['materials']:
  if 'normalTexture'in m:
   orm=m.get('pbrMetallicRoughness',{}).get('metallicRoughnessTexture',{}).get('index');ao=m.get('occlusionTexture',{}).get('index')
   if ao is None or ao!=orm:errors.append('ORM/AO mismatch '+m.get('name',''))
 assert not any('uri'in i for i in g.get('images',[])), 'GLB must embed images'
 result={'file':p.name,'triangles':sum(counts.values()),'meshes':len(meshes),'mesh_nodes':len(counts),'counts':counts,'errors':errors}
 if p.name=='snake-sectional.glb':
  body=[n for n in nodes if n.get('name','').startswith('Segment_')]
  result['rigid_segments']=len(body);result['body_unique_meshes']=len(set(n['mesh'] for n in body));result['joint_insert_nodes']=len([n for n in nodes if 'GlowBars'in n.get('name','')]);result['segment_with_joint']=counts['Segment_00']+counts['Joint_00_Housing']+counts['Joint_00_GlowBars'];result['tail_with_joint']=counts['Tail']+counts['TailJoint_Housing']+counts['TailJoint_GlowBars']
  assert len(body)==28 and result['body_unique_meshes']==1
  assert result['joint_insert_nodes']==29
  assert result['segment_with_joint']<=1600 and result['tail_with_joint']<=3000
  assert 30000<=result['triangles']<=60000
 else:assert 10000<=result['triangles']<=18000
 assert not errors,errors
 return result
out=[validate(D/p) for p in ['snake-sectional.glb','head.glb']];(D/'glb-validation.json').write_text(json.dumps(out,indent=2));print(json.dumps([{k:v for k,v in o.items() if k!='counts'} for o in out],indent=2))

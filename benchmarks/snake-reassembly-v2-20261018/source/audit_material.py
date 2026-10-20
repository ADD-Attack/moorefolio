import bpy,json,hashlib,sys,struct,os,numpy as np
if "--" in sys.argv: os.chdir(sys.argv[sys.argv.index("--")+1])
from pathlib import Path

def snapshot(path):
 bpy.ops.wm.open_mainfile(filepath=str(Path(path).resolve()));meshes={};nodes={}
 for ob in bpy.data.objects:
  if ob.type!='MESH' or ob.name.startswith('STAGE_'):continue
  me=ob.data;me.calc_loop_triangles();v=np.array([v.co[:] for v in me.vertices],np.float32);f=[tuple(p.vertices) for p in me.polygons]
  meshes[ob.name]=hashlib.sha256(v.tobytes()+repr(f).encode()).hexdigest()
  if not ob.hide_render:nodes[ob.name]={'tris':len(me.loop_triangles),'matrix':np.array(ob.matrix_world).tolist()}
 return meshes,nodes
base,base_nodes=snapshot('fix/snake-v2-r2-fix.blend');cur,nodes=snapshot('material/m4-mapped.blend')
assert base==cur,'P8 mesh fingerprint drift';assert base_nodes==nodes,'instance or count drift'
counts={'head':nodes['Head_node']['tris'],'module_insert':nodes['Segment_07']['tris']+nodes['Glow_07']['tris'],'tail':sum(v['tris'] for k,v in nodes.items() if k.startswith(('Tail','Glow_T'))),'assembly':sum(v['tris'] for v in nodes.values())}
assert counts['head']<=14000 and counts['module_insert']<=1450 and counts['tail']<=3000 and counts['assembly']<=57600
raw=Path('material/snake-p8-material.glb').read_bytes();n,typ=struct.unpack_from('<II',raw,12);assert typ==0x4e4f534a;g=json.loads(raw[20:20+n]);maps=[]
for m in g['materials']:
 p=m['pbrMetallicRoughness'];ao=m['occlusionTexture']['index'];mr=p['metallicRoughnessTexture']['index'];ai=g['textures'][ao]['source'];mi=g['textures'][mr]['source'];assert ai==mi,('ORM not packed',m['name']);assert 'normalTexture' in m and 'baseColorTexture' in p
 em=m.get('emissiveFactor',[0,0,0]);allowed=('Head' in m['name'] or 'Glow' in m['name']);assert allowed or max(em)==0,('unapproved emission',m['name'])
 maps.append({'material':m['name'],'ao_and_mr_image':ai,'normal':m['normalTexture']['index'],'emissive':em,'extensions':m.get('extensions',{})})
export_counts={}
for nd in g['nodes']:
 if 'mesh' not in nd:continue
 tr=0
 for pr in g['meshes'][nd['mesh']]['primitives']:
  assert pr.get('mode',4)==4;tr+=g['accessors'][pr['indices']]['count']//3
 export_counts[nd['name']]=tr
assert export_counts=={k:v['tris'] for k,v in nodes.items()},'GLB node/tri drift'
report={'geometry_fingerprints_unchanged':True,'instance_transforms_unchanged':True,'counts':counts,'glb_node_counts_match':True,'maps':maps,'glb_sha256':hashlib.sha256(raw).hexdigest(),'acceptance':'not inferred from technical checks'}
Path('material/audit-material.json').write_text(json.dumps(report,indent=2));print('MATERIAL_TECHNICAL_PASS',counts)

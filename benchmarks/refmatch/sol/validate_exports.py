"""Standard-library structural glTF checks; counts assembled instances, not just unique meshes."""
import json,struct,os,math,sys
ROOT=os.path.dirname(os.path.abspath(__file__))
def load(path):
 data=open(path,'rb').read();magic,version,length=struct.unpack_from('<4sII',data);assert magic==b'glTF' and version==2 and length==len(data)
 n,kind=struct.unpack_from('<II',data,12);assert kind==0x4e4f534a
 return json.loads(data[20:20+n])
def validate(name):
 g=load(os.path.join(ROOT,name));assert 'KHR_draco_mesh_compression' not in g.get('extensionsUsed',[])
 for node in g['nodes']:
  assert all(abs(x-1)<1e-5 for x in node.get('scale',[1,1,1])),(name,node.get('name'),node.get('scale'))
  if 'matrix' in node:
   m=node['matrix'];det=m[0]*(m[5]*m[10]-m[9]*m[6])-m[4]*(m[1]*m[10]-m[9]*m[2])+m[8]*(m[1]*m[6]-m[5]*m[2]);assert det>0,(name,node.get('name'),'negative determinant')
 total=0;prims=0
 for node in g['nodes']:
  if 'mesh' not in node:continue
  for p in g['meshes'][node['mesh']]['primitives']:
   assert p.get('mode',4)==4
   total+=g['accessors'][p['indices']]['count']//3;prims+=1
   assert 'TANGENT' in p['attributes'],(name,node.get('name'),'no tangent')
   assert 'TEXCOORD_0' in p['attributes']
   assert 'material' in p
 for mat in g['materials']:
  orm=mat.get('pbrMetallicRoughness',{}).get('metallicRoughnessTexture')
  occ=mat.get('occlusionTexture')
  if occ and orm:assert occ['index']==orm['index'],(mat['name'],'AO not packed with MR')
  if 'normalTexture' in mat: assert mat['normalTexture'].get('texCoord',0) in [0,1]
 assert not g.get('skins'), 'Rigid route must not accidentally acquire a skin'
 return {'triangles':total,'mesh_nodes':sum('mesh'in n for n in g['nodes']),'material_surfaces':prims,'materials':len(g['materials']),'embedded_images':len(g.get('images',[])),'all_tangents':True,'unit_scale_positive_frames':True,'draco':False}
results={n:validate(n) for n in ['snake_head.glb','snake_segment.glb','snake_full.glb']}
assert 10000<=results['snake_head.glb']['triangles']<=18000
assert results['snake_full.glb']['triangles']<=60000
json.dump(results,open(os.path.join(ROOT,'validation.json'),'w'),indent=2)
print(json.dumps(results,indent=2))

"""Fix-order regression checks against the authorized original commit only."""
import hashlib, json, math, struct, subprocess
from pathlib import Path

D=Path(__file__).resolve().parent
prefix='benchmarks/snake-sectional-v1/'
def original(path):
    return subprocess.check_output(['git','show','45cb5d8:'+prefix+path],cwd=D)
def glb(data):
    n=struct.unpack_from('<I',data,12)[0]
    g=json.loads(data[20:20+n]);p=20+n
    length=struct.unpack_from('<I',data,p)[0]
    return g,data[p+8:p+8+length]
def accessor(g,b,i):
    a=g['accessors'][i];v=g['bufferViews'][a['bufferView']]
    code={5120:'b',5121:'B',5122:'h',5123:'H',5125:'I',5126:'f'}[a['componentType']]
    width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
    fmt='<'+code*width;step=v.get('byteStride',struct.calcsize(fmt))
    offset=v.get('byteOffset',0)+a.get('byteOffset',0)
    return [struct.unpack_from(fmt,b,offset+j*step) for j in range(a['count'])]
old,ob=glb(original('head.glb'))
new,nb=glb((D/'head.glb').read_bytes())
def lens(g):return {n['name']:n for n in g['nodes'] if 'mesh' in n and n.get('name')!='Head'}
ol,nl=lens(old),lens(new)
assert ol.keys()==nl.keys(), 'Lens node set changed'
lens_results=[]
for name in ol:
    a,b=ol[name],nl[name]
    for key,default in [('translation',[0,0,0]),('rotation',[0,0,0,1]),('scale',[1,1,1])]:
        assert max(abs(x-y) for x,y in zip(a.get(key,default),b.get(key,default)))<1e-6,(name,key)
    ap=old['meshes'][a['mesh']]['primitives'];bp=new['meshes'][b['mesh']]['primitives']
    assert len(ap)==len(bp)
    max_error=0
    for p,q in zip(ap,bp):
        assert p['attributes'].keys()==q['attributes'].keys()
        for key in p['attributes']:
            aa=accessor(old,ob,p['attributes'][key]);bb=accessor(new,nb,q['attributes'][key])
            assert len(aa)==len(bb),(name,key,'count')
            err=max(abs(x-y) for av,bv in zip(aa,bb) for x,y in zip(av,bv))
            max_error=max(max_error,err)
            assert err<2e-5,(name,key,err)
        assert accessor(old,ob,p['indices'])==accessor(new,nb,q['indices']),(name,'topology')
        om=old['materials'][p['material']];nm=new['materials'][q['material']]
        assert om==nm,(name,'lens material changed')
    lens_results.append({'node':name,'unchanged_material':True,'max_attribute_error':max_error})
protected=[]
for path in sorted((D/'captures').glob('wip-*.png')):
    before=hashlib.sha256(original('captures/'+path.name)).hexdigest()
    after=hashlib.sha256(path.read_bytes()).hexdigest()
    assert before==after,path
    protected.append({'file':'captures/'+path.name,'sha256':after,'unchanged':True})
for name in ['snake-sectional.glb','head.glb']:
    assert (D/name).read_bytes()==(D/'godot'/name).read_bytes(),'Godot asset copy differs'
report={'baseline':'45cb5d8','lens_nodes_unchanged':lens_results,'protected_wip':protected,
        'godot_assets_identical':True,'pass':True}
(D/'fix-validation.json').write_text(json.dumps(report,indent=2))
print('FIX_VALIDATION_PASS lens_nodes=',len(lens_results),' protected_wip=',len(protected))

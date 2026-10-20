"""M5e owner tweak from M5d: slightly lighter plate value, slightly lower roughness. Shader-only; mesh/UV frozen."""
import bpy,sys,os,json,hashlib,numpy as np
from pathlib import Path
T=Path(sys.argv[sys.argv.index('--')+1]);os.chdir(T)
exec((T/'source/material_m5.py').read_text().split('before=')[0])
def uvh(o):return hashlib.sha256(np.array([u.uv[:] for u in o.data.uv_layers.active.data],np.float32).tobytes()).hexdigest()
meshes=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('SRC_')]
before={o.name:(fingerprint(o.data),uvh(o)) for o in meshes}
for m in {m for o in meshes for m in o.data.materials if m}:
 nt=m.node_tree;p=nt.nodes.get('Surface')
 if not p or 'M5dValueDrop' not in nt.nodes:continue
 nt.nodes['M5dValueDrop'].inputs[2].default_value=(.93,.94,.95,1)
 rr=nt.nodes['BAKE_ROUGH'].inputs[0].links[0].from_socket
 rr=mathn(nt,'MAXIMUM',mathn(nt,'SUBTRACT',rr,.04),.15)
 route(nt,rr,'BAKE_ROUGH');nt.links.new(rr,p.inputs['Roughness'])
assert before=={o.name:(fingerprint(o.data),uvh(o)) for o in meshes}
(T/'material/m5e-shader-audit.json').write_text(json.dumps({'geometry_and_uv_exactly_unchanged':True},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(T/'material/m5e-procedural.blend'));print('M5E_SHADER_COMPLETE')

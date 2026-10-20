"""M5c removes uniform brushing; retain topology-local wear and explicit real-part tones."""
import bpy,sys,os,json,hashlib,numpy as np
from pathlib import Path
T=Path(sys.argv[sys.argv.index('--')+1]);os.chdir(T)
exec((T/'source/material_m5.py').read_text().split('before=')[0])
for m in {m for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('SRC_') for m in o.data.materials if m}:
 nt=m.node_tree
 if 'M5bScuffedSteel' not in nt.nodes:continue
 edge=nt.nodes['ConvexConcaveMask'].outputs['Red'] if 'ConvexConcaveMask' in nt.nodes else nt.nodes['PhysicalEdgeMask'].outputs[0]
 scratch=nt.nodes['M5bScuffedSteel'].inputs[0].links[0].from_socket
 local=mathn(nt,'MULTIPLY',scratch,mathn(nt,'ADD',.08,mathn(nt,'MULTIPLY',edge,1.5)))
 nt.links.new(local,nt.nodes['M5bScuffedSteel'].inputs[0])
 # Earlier M5 global hairlines also confined to physical edges.
 for name in ['M5HairlineColor','SilverHairlines']:
  if name in nt.nodes:
   n=nt.nodes[name];s=n.inputs[0].links[0].from_socket
   nt.links.new(mathn(nt,'MULTIPLY',s,mathn(nt,'ADD',.12,edge)),n.inputs[0])
 r=nt.nodes['ComponentTint'].color_ramp
 tones=('7F8C8C','A5A397')
 if 'Gunmetal_00' in m.name:tones=('626B65','857965')
 if 'FinInset' in m.name:tones=('555D56','736653')
 if 'MachinedSteel' in m.name:tones=('A0AAA7','B6B3A4')
 for e,h in zip(r.elements,tones):e.color=(*rgb(h),1)
 # More mottled oxide only in the existing narrow seam/recess shoulder, never whole panels.
 n=nt.nodes['M5bWarmStreaks'];s=n.inputs[0].links[0].from_socket
 nt.links.new(mathn(nt,'MULTIPLY',s,1.35),n.inputs[0])
bpy.ops.wm.save_as_mainfile(filepath=str(T/'material/m5c-procedural.blend'));print('M5C_SHADER_COMPLETE')

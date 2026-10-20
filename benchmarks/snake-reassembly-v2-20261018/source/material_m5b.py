"""M5b: material-only tonal/wear refinement from M5, no mesh or UV changes."""
import bpy,sys,os,json,hashlib,numpy as np
from pathlib import Path
T=Path(sys.argv[sys.argv.index('--')+1]);os.chdir(T)
exec((T/'source/material_m5.py').read_text().split('before=')[0])
before={o.name:fingerprint(o.data) for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('SRC_')}
for m in {m for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('SRC_') for m in o.data.materials if m}:
 if not any(x in m.name for x in ['Gunmetal','FinInset','MachinedSteel']):continue
 nt=m.node_tree;p=nt.nodes['Surface'];co=nt.nodes['Coordinates'].outputs['Object']
 # Reference: distinct restrained alloy tones on real parts, not procedural color cells.
 tones=('929A98','A19D8D')
 if 'Gunmetal_00' in m.name:tones=('777D79','928571')
 if 'FinInset' in m.name:tones=('62685F','81745F')
 if 'MachinedSteel' in m.name:tones=('9DA4A1','B1AC9C')
 r=nt.nodes['ComponentTint'].color_ramp
 for e,h in zip(r.elements,tones):e.color=(*rgb(h),1)
 old=nt.nodes['BAKE_COLOR'].inputs[0].links[0].from_socket
 streak=noise(nt,co,(16,52,8),'M5bWearStreaks');streak=mask(nt,streak,.40,.68,'M5bStreakContrast')
 patch=noise(nt,co,(9,13,18),'M5bLocalBreakup')
 stain=mathn(nt,'MULTIPLY',streak,mask(nt,patch,.32,.67,'M5bInterruptedStain'))
 cavity=nt.nodes['CAVITY_MASK'].outputs[0]
 stain=mathn(nt,'MULTIPLY',stain,mathn(nt,'ADD',.32,mathn(nt,'MULTIPLY',cavity,.55)))
 col=mix(nt,old,rgb('524E42'),stain,'M5bWarmStreaks')
 # Narrow scratches with sparse breakup; no connected cell boundaries.
 scratches=noise(nt,co,(5,230,170),'M5bScratchField');scratch=mask(nt,scratches,.60,.67,'M5bScratchThreshold')
 scratch=mathn(nt,'MULTIPLY',scratch,mask(nt,patch,.43,.65,'M5bScratchBreak'))
 col=mix(nt,col,rgb('C1BFB3'),mathn(nt,'MULTIPLY',scratch,.50),'M5bScuffedSteel')
 # Do not wash over precisely confined tail vent shading.
 if 'M5ConfinedTailVent' in nt.nodes:
  vent=nt.nodes['M5ConfinedTailVent'].inputs[0].links[0].from_socket
  col=mix(nt,col,rgb('303732'),vent,'M5bPreserveTailVent')
 route(nt,col,'BAKE_COLOR');nt.links.new(col,p.inputs['Base Color'])
 rr=nt.nodes['BAKE_ROUGH'].inputs[0].links[0].from_socket
 rr=mathn(nt,'ADD',rr,mathn(nt,'MULTIPLY',stain,.14));rr=mathn(nt,'SUBTRACT',rr,mathn(nt,'MULTIPLY',scratch,.15));route(nt,rr,'BAKE_ROUGH');nt.links.new(rr,p.inputs['Roughness'])
after={o.name:fingerprint(o.data) for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('SRC_')};assert before==after
bpy.ops.wm.save_as_mainfile(filepath=str(T/'material/m5b-procedural.blend'));print('M5B_SHADER_PASS')

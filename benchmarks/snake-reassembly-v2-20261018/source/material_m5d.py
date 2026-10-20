"""M5d plate response from M5c: gunmetal value, recess grime, thin joint arc. Shader-only; mesh/UV frozen."""
import bpy,sys,os,json,hashlib,numpy as np
from pathlib import Path
T=Path(sys.argv[sys.argv.index('--')+1]);os.chdir(T)
exec((T/'source/material_m5.py').read_text().split('before=')[0])
def uvh(o):return hashlib.sha256(np.array([u.uv[:] for u in o.data.uv_layers.active.data],np.float32).tobytes()).hexdigest()
meshes=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('SRC_')]
before={o.name:(fingerprint(o.data),uvh(o)) for o in meshes}
for m in {m for o in meshes for m in o.data.materials if m}:
 nt=m.node_tree;p=nt.nodes.get('Surface')
 if not p or 'Optic_' in m.name:continue
 co=nt.nodes['Coordinates']
 if 'TealInsert' in m.name:
  # Reference joints: dark collar with one thin continuous emissive arc at the centre.
  x=nt.nodes['M5InsertAxes'].outputs['X']
  band=mathn(nt,'MULTIPLY',mask(nt,x,.36,.42,'M5dArcL'),mathn(nt,'SUBTRACT',1,mask(nt,x,.58,.64,'M5dArcR')))
  col=mix(nt,rgb('2B302E'),rgb('5FD9B8'),band,'M5dInsertColor')
  em=mix(nt,(0,0,0),rgb('4FD8B2'),mathn(nt,'MULTIPLY',band,1.6),'M5dInsertEmission')
  route(nt,col,'BAKE_COLOR');route(nt,em,'BAKE_EMISSION');nt.links.new(col,p.inputs['Base Color']);nt.links.new(em,p.inputs['Emission Color'])
  continue
 if 'DarkHousing' in m.name or 'RecessedGrille' in m.name:continue
 if 'ComponentTint' in nt.nodes:
  r=nt.nodes['ComponentTint'].color_ramp
  tones=('4A504E','5E5850')
  if 'Gunmetal_00' in m.name:tones=('3D433F','524A40')
  if 'FinInset' in m.name:tones=('343A36','463F35')
  if 'MachinedSteel' in m.name:tones=('6A706E','7A756A')
  for e,h in zip(r.elements,tones):e.color=(*rgb(h),1)
 old=nt.nodes['BAKE_COLOR'].inputs[0].links[0].from_socket
 # Global value drop toward the reference gunmetal, keeping existing variation.
 dark=node(nt,'ShaderNodeMixRGB','M5dValueDrop');dark.blend_type='MULTIPLY';dark.inputs[0].default_value=1
 nt.links.new(old,dark.inputs[1]);dark.inputs[2].default_value=(.68,.69,.70,1);col=dark.outputs[0]
 # Dark recess grime from the existing cavity mask, broken by noise.
 cav=nt.nodes['CAVITY_MASK'].outputs[0]
 brk=mask(nt,noise(nt,co.outputs['Object'],(14,14,14),'M5dGrimeNoise'),.35,.7,'M5dGrimeBreak')
 grime=mathn(nt,'MINIMUM',mathn(nt,'MULTIPLY',cav,mathn(nt,'ADD',.45,mathn(nt,'MULTIPLY',brk,.55))),1)
 col=mix(nt,col,rgb('1E1D1A'),grime,'M5dRecessGrime')
 # Faint oxide in recesses only (reference shows small rust spots, not patches).
 rust=mathn(nt,'MULTIPLY',grime,mask(nt,noise(nt,co.outputs['Object'],(30,30,30),'M5dRustNoise'),.62,.75,'M5dRustMask'))
 col=mix(nt,col,rgb('5A3A26'),mathn(nt,'MULTIPLY',rust,.7),'M5dOxide')
 rr=nt.nodes['BAKE_ROUGH'].inputs[0].links[0].from_socket
 rr=mathn(nt,'ADD',rr,mathn(nt,'MULTIPLY',grime,.15))
 route(nt,col,'BAKE_COLOR');route(nt,rr,'BAKE_ROUGH');nt.links.new(col,p.inputs['Base Color']);nt.links.new(rr,p.inputs['Roughness'])
after={o.name:(fingerprint(o.data),uvh(o)) for o in meshes}
assert before==after
(T/'material/m5d-shader-audit.json').write_text(json.dumps({'geometry_and_uv_exactly_unchanged':True},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(T/'material/m5d-procedural.blend'));print('M5D_SHADER_COMPLETE')
